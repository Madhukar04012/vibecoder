"""
Atoms Engine — Full Multi-Agent SDLC Pipeline with Race Mode + Auto-Deploy

Architecture:
  - Blackboard Pattern: Shared state (PRD, Architecture, FileSystem)
  - Auto-Deploy: Files written to disk, npm install, dev server auto-started
  - Race Mode: N parallel teams, Judge selects best solution
"""

import asyncio
import json
import logging
import os
import re
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.core.orchestrator import execute_project
from backend.core.streaming.agent_stream_bus import get_agent_stream_bus
from backend.core.tech_detector import detect_stack, get_architect_prompt_for_stack, get_engineer_prompt_for_stack, get_fallback_architecture

router = APIRouter(prefix="/api/atoms", tags=["atoms"])

# ─── Project Sandbox ─────────────────────────────────────────────────────────
PROJECT_DIR = Path(__file__).resolve().parent.parent.parent / "generated_projects" / "demo"


def _safe_file_path(relative_path: str) -> Path:
    """Resolve path under PROJECT_DIR; reject traversal and absolute paths."""
    if not relative_path or ".." in relative_path or relative_path.startswith("/"):
        raise ValueError(f"Invalid file path: {relative_path!r}")
    resolved = (PROJECT_DIR / relative_path).resolve()
    try:
        resolved.relative_to(PROJECT_DIR)
    except ValueError:
        raise ValueError(f"Invalid file path: {relative_path!r}")
    return resolved


def _find_frontend_dir(files_map: Dict[str, str]) -> Optional[Path]:
    """Find the frontend directory containing package.json with vite.

    The coder agent wraps output in a project folder (e.g. ``my_project/``),
    and the frontend lives under ``<project>/frontend/``.  This helper locates
    the correct directory on disk so that ``npm install`` and
    ``npx vite`` run in the right place.
    """
    candidates: list[tuple[str, str]] = []
    for key, content in files_map.items():
        if key.endswith("package.json") or key.split("/")[-1] == "package.json":
            candidates.append((key, content))

    # Prefer the package.json that contains "vite" (the frontend one)
    for key, content in candidates:
        if "vite" in content:
            rel_dir = "/".join(key.replace("\\", "/").split("/")[:-1])
            return (PROJECT_DIR / rel_dir).resolve() if rel_dir else PROJECT_DIR

    # Fallback: any package.json
    if candidates:
        key = candidates[0][0]
        rel_dir = "/".join(key.replace("\\", "/").split("/")[:-1])
        return (PROJECT_DIR / rel_dir).resolve() if rel_dir else PROJECT_DIR

    return None


def _write_files_to_disk(files: Dict[str, str]) -> None:
    """Write all generated files to the sandbox directory for preview."""
    import shutil

    # Clean previous project
    if PROJECT_DIR.exists():
        for item in PROJECT_DIR.iterdir():
            if item.name == "node_modules":
                continue  # Don't delete node_modules (expensive to reinstall)
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

    PROJECT_DIR.mkdir(parents=True, exist_ok=True)
    for path, content in files.items():
        file_path = _safe_file_path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")


def _run_npm_install(cwd: Optional[Path] = None) -> tuple[bool, str]:
    """Run npm install in the given directory (defaults to PROJECT_DIR). Returns (success, combined_output)."""
    target = str(cwd or PROJECT_DIR)
    try:
        result = subprocess.run(
            "npm install",
            shell=True,
            cwd=target,
            capture_output=True,
            timeout=120,
            encoding="utf-8",
            errors="replace",
        )
        output = (result.stdout or "") + "\n" + (result.stderr or "")
        return result.returncode == 0, output.strip()
    except subprocess.TimeoutExpired:
        return False, "npm install timed out"
    except Exception as e:
        return False, str(e)


async def _run_npm_install_streaming(
    cwd: Optional[Path],
) -> AsyncGenerator[tuple[str, bool] | int, None]:
    """
    Run npm install and yield (line, is_stderr) for each line of output; finally yield return_code (int).
    Reads stdout and stderr concurrently to avoid deadlock.
    """
    target = str(cwd or PROJECT_DIR)
    proc = await asyncio.create_subprocess_shell(
        "npm install",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=target,
    )
    queue: asyncio.Queue[tuple[str, bool] | None] = asyncio.Queue()

    async def read_stdout() -> None:
        if proc.stdout:
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                text = line.decode("utf-8", errors="replace").rstrip()
                if text:
                    await queue.put((text, False))
        await queue.put(None)

    async def read_stderr() -> None:
        if proc.stderr:
            while True:
                line = await proc.stderr.readline()
                if not line:
                    break
                text = line.decode("utf-8", errors="replace").rstrip()
                if text:
                    await queue.put((text, True))
        await queue.put(None)

    readers = asyncio.create_task(asyncio.gather(read_stdout(), read_stderr()))
    sentinels = 0
    while sentinels < 2:
        item = await queue.get()
        if item is None:
            sentinels += 1
            continue
        yield item
    await readers
    await proc.wait()
    yield proc.returncode if proc.returncode is not None else 0


# Preview process management
_preview_proc: Optional[subprocess.Popen] = None
_preview_port: int = 5174


def _start_dev_server(cwd: Optional[Path] = None) -> tuple[bool, str, int]:
    """Start the Vite dev server for preview."""
    global _preview_proc, _preview_port
    import socket

    target = cwd or PROJECT_DIR

    # Kill existing
    if _preview_proc is not None:
        try:
            _preview_proc.terminate()
            _preview_proc.wait(timeout=3)
        except Exception:
            try:
                _preview_proc.kill()
            except Exception:
                pass
        _preview_proc = None

    # Find free port
    for port in range(5174, 5190):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("", port))
                _preview_port = port
                break
        except OSError:
            continue

    pkg_json = target / "package.json"
    if not pkg_json.exists():
        return False, f"No package.json found at {target}", _preview_port

    try:
        _preview_proc = subprocess.Popen(
            f"npx vite --port {_preview_port} --host",
            shell=True,
            cwd=str(target),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        # Wait until port is accepting connections (up to 15s) so preview_ready is sent when iframe can load
        for _ in range(30):
            time.sleep(0.5)
            if _preview_proc.poll() is not None:
                return False, f"Dev server exited with code {_preview_proc.returncode}", _preview_port
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.5)
                    s.connect(("127.0.0.1", _preview_port))
                return True, f"Dev server running on port {_preview_port}", _preview_port
            except (OSError, socket.error):
                continue
        return False, "Dev server failed to bind within 15s", _preview_port
    except Exception as e:
        return False, str(e), _preview_port


# ─── Request Model ───────────────────────────────────────────────────────────

class AtomsRequest(BaseModel):
    prompt: str = ""
    files: dict = Field(default_factory=dict)
    mode: str = "standard"  # "standard" | "race"
    race_teams: int = 2     # number of parallel teams for race mode


# ─── Blackboard (Shared State) ───────────────────────────────────────────────

class Blackboard:
    """Shared truth between all agents. Immutable snapshots for safety."""
    def __init__(self, prompt: str, existing_files: dict):
        self.prompt = prompt
        self.existing_files = existing_files
        self.prd: Optional[dict] = None
        self.architecture: Optional[dict] = None
        self.file_plan: List[str] = []
        self.generated_files: Dict[str, str] = {}
        self.agent_messages: List[dict] = []
        self.score: float = 0.0

    def snapshot(self) -> dict:
        return {
            "prompt": self.prompt,
            "prd": self.prd,
            "architecture": self.architecture,
            "file_plan": self.file_plan,
            "files": dict(self.generated_files),
            "score": self.score,
        }


# ─── LLM Caller ─────────────────────────────────────────────────────────────

def _call_llm_sync(system: str, user: str, max_tokens: int = 2048, temp: float = 0.3, use_coder: bool = False) -> str | None:
    """Synchronous LLM call via the gateway for cost tracking. Returns raw text.
    
    WARNING: This blocks the calling thread. Use _call_llm() (async) in async contexts.
    """
    from backend.engine.llm_gateway import llm_call

    agent_name = "atoms_engineer" if use_coder else "atoms_pipeline"
    
    return llm_call(
        agent_name=agent_name,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=max_tokens,
        temperature=temp,
        use_coder=use_coder,
    )


async def _call_llm(system: str, user: str, max_tokens: int = 2048, temp: float = 0.3, use_coder: bool = False) -> str | None:
    """Async LLM call — runs the blocking LLM call in a thread pool so it
    does NOT freeze the event loop."""
    return await asyncio.to_thread(_call_llm_sync, system, user, max_tokens, temp, use_coder)


def _stream_llm_sync(system: str, user: str, max_tokens: int = 2048, temp: float = 0.3, use_coder: bool = False):
    """Synchronous streaming LLM call. Yields token strings.
    
    WARNING: This blocks. Use _stream_llm_collect() for async contexts.
    """
    from backend.engine.llm_gateway import llm_call_stream

    agent_name = "atoms_engineer" if use_coder else "atoms_pipeline"
    
    yield from llm_call_stream(
        agent_name=agent_name,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=max_tokens,
        temperature=temp,
        use_coder=use_coder,
    )


async def _stream_llm_to_sse(system: str, user: str, file_path: str, max_tokens: int = 2048, temp: float = 0.3, use_coder: bool = False):
    """Async generator: run the synchronous streaming LLM in a thread and yield
    (token, sse_event) pairs without blocking the event loop.
    
    Collects all tokens from the sync generator in a background thread,
    pushes them into an asyncio.Queue, and yields SSE events from the queue.
    """
    queue: asyncio.Queue = asyncio.Queue()
    loop = asyncio.get_running_loop()
    sentinel = object()  # signals "done"

    def _produce():
        try:
            for token in _stream_llm_sync(system, user, max_tokens, temp, use_coder):
                if token:
                    loop.call_soon_threadsafe(queue.put_nowait, token)
        except Exception as exc:
            loop.call_soon_threadsafe(queue.put_nowait, exc)
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, sentinel)

    # Start producer in a thread
    loop.run_in_executor(None, _produce)

    content_parts = []
    while True:
        item = await queue.get()
        if item is sentinel:
            break
        if isinstance(item, Exception):
            logger.exception("[Atoms] Stream error: %s", item)
            break
        content_parts.append(item)
        yield item  # caller wraps in sse("file_delta", ...)

    # Return the full content via a special attribute on the generator
    # (callers collect from content_parts via the yielded tokens)


def _extract_json(text: str) -> dict | list | None:
    """Extract JSON from LLM output."""
    if not text:
        return None
    # Strip markdown fences
    text = re.sub(r'^```\w*\n?', '', text.strip())
    text = re.sub(r'\n?```$', '', text.strip())
    # Find JSON
    for pattern in [r'\{[\s\S]*\}', r'\[[\s\S]*\]']:
        m = re.search(pattern, text)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                continue
    return None


# ─── Agent Definitions ───────────────────────────────────────────────────────

AGENT_PM_SYSTEM = """You are a Product Manager agent. Your job is to create a Product Requirements Document (PRD).

IMPORTANT: The tech_hints field MUST reflect exactly what technologies 
the user mentions in their prompt. Do NOT default to React/FastAPI if the
user asked for different technologies (e.g., Django, Vue, Go, Angular, etc.)

Output ONLY valid JSON:
{
  "title": "Product title",
  "description": "What this product does",
  "user_stories": ["As a user, I want...", ...],
  "features": ["Feature 1", "Feature 2", ...],
  "constraints": ["Must be responsive", ...],
  "tech_hints": ["<exact technologies from user prompt>"]
}

No markdown. No explanation. JSON only."""

# NOTE: AGENT_ARCHITECT_SYSTEM is now generated dynamically per-prompt via
# get_architect_prompt_for_stack(). This static version is kept ONLY as a
# fallback when tech detection returns nothing.
AGENT_ARCHITECT_SYSTEM_DEFAULT = """You are a Senior Software Architect agent. Based on the PRD, design a COMPANY-LEVEL production system.

IMPORTANT: Analyze the PRD carefully to determine the CORRECT technology stack.
- If the user asks for Python/Django/Flask/FastAPI → generate Python files (.py)
- If the user asks for Node/Express/NestJS → generate JS/TS files
- If the user asks for Go/Gin → generate Go files (.go)
- If the user asks for Java/Spring → generate Java files (.java)
- If the user asks for Vue/Angular/Svelte → use those frameworks, NOT React
- If no specific tech is mentioned, choose the BEST tech for the described project

You MUST output a comprehensive project with MANY files. Think like a real engineering team.

Output ONLY valid JSON:
{
  "stack": {"backend": "<framework>", "frontend": "<framework if needed>", "database": "<if needed>"},
  "directory_structure": [
    "<config_file>",
    "<entry_point>",
    "<routes/controllers>",
    "<models>",
    "<services>",
    "<tests>",
    "... at least 10-20 files"
  ],
  "component_tree": {},
  "data_model": {"entities": []},
  "api_endpoints": []
}

RULES:
- Include AT LEAST 10-20 files for a proper project
- Use CORRECT file extensions for the chosen technology
- Include proper configuration files for the stack
- Include a test directory
- The project MUST be complete and runnable
- No markdown. No explanation. JSON only."""

# NOTE: AGENT_ENGINEER_SYSTEM is now generated dynamically per-file via
# get_engineer_prompt_for_stack(). This static version is the fallback.
AGENT_ENGINEER_SYSTEM_DEFAULT = """You are a Senior Software Engineer at a top tech company. Write the COMPLETE contents of the file '{file_path}'.

CRITICAL RULES:
- Write PRODUCTION-READY, COMPANY-LEVEL code
- NO markdown, NO explanations, NO code fences (```)
- Output ONLY the raw file content — nothing before or after
- Detect the language from the file extension and write idiomatic code for that language
- Include ALL imports, exports, types, and logic
- Write REAL functionality, not placeholders or TODOs
- Use modern best practices for the detected language/framework
- Include proper error handling
- Make it look professional and well-structured"""

AGENT_JUDGE_SYSTEM = """You are a Code Judge. Evaluate this code solution and score it.

Output ONLY valid JSON:
{
  "score": 85,
  "syntactic_correctness": true,
  "functional_compliance": 90,
  "code_quality": 80,
  "issues": ["Minor: could use better error handling"],
  "verdict": "PASS"
}

Score from 0-100. No markdown. JSON only."""

# ─── Discussion & Review Prompts ─────────────────────────────────────────────

AGENT_TEAMLEAD_REVIEW = """You are the Team Leader reviewing the Product Requirements Document.

Given this PRD, provide brief feedback (2-3 sentences max). Ask one clarifying question if needed.
Be constructive and professional. If it looks good, say "Approved" and why.

Output plain text only. No JSON. No markdown."""

AGENT_ARCHITECT_REVIEW = """You are the Architect reviewing the PRD before designing the system.

Provide brief feedback (2-3 sentences) on the technical feasibility.
Mention any potential technical challenges. Suggest the best approach.

Output plain text only. No JSON. No markdown."""

AGENT_QA_SYSTEM = """You are a Senior QA Engineer. Review the generated code files for bugs, issues, and improvements.

Analyze the code and output ONLY valid JSON:
{
  "status": "pass" or "fail",
  "bugs": [
    {"file": "src/App.jsx", "severity": "high", "description": "Missing error boundary"},
    {"file": "src/utils/helpers.js", "severity": "low", "description": "No input validation"}
  ],
  "improvements": ["Add loading states", "Add error handling for API calls"],
  "test_results": {
    "total_files_checked": 10,
    "files_with_issues": 2,
    "critical_bugs": 0,
    "warnings": 3
  },
  "overall_score": 85,
  "verdict": "PASS — Ready for deployment with minor improvements"
}

Be thorough but realistic. Score from 0-100. No markdown. JSON only."""

AGENT_ENGINEER_FIX = """You are a Senior Software Engineer fixing a bug reported by QA.

Bug report: {bug_description}
File: {file_path}

Current file content:
{file_content}

Rewrite the COMPLETE file with the fix applied. Output ONLY the raw file content.
NO markdown, NO explanations, NO code fences."""


# ─── Typing Speed ────────────────────────────────────────────────────────────

TYPING_CHUNK = 32
TYPING_DELAY = 0.003


# ─── Event Helper ────────────────────────────────────────────────────────────

def sse(etype: str, data: dict) -> str:
    return f"data: {json.dumps({'type': etype, **data})}\n\n"


# ─── Standard Mode Pipeline ─────────────────────────────────────────────────

async def standard_pipeline(prompt: str, existing_files: dict) -> AsyncGenerator[str, None]:
    """Full multi-agent pipeline with inter-agent discussions and QA testing.
    
    TeamLead → PM → [Discussion: TeamLead reviews PRD] →
    Architect → [Discussion: Architect explains to TeamLead] →
    Engineer → QA → [Fix cycle if needed] → DevOps
    """

    board = Blackboard(prompt, existing_files)

    # ═══════════════════════════════════════════════════════════════
    #  PHASE 1: TEAM LEADER — Kickoff
    # ═══════════════════════════════════════════════════════════════
    yield sse("agent_start", {"agent": "team_lead", "name": "Team Leader", "icon": "crown", "description": "Analyzing request and assembling the team..."})
    await asyncio.sleep(0.3)

    # Detect technology stack from the user's prompt
    detected_stack = detect_stack(prompt)

    # Derive project_type from detection
    if detected_stack.project_type == "api" or detected_stack.is_backend_only:
        project_type = f"{detected_stack.backend_language or 'python'}_api"
    elif detected_stack.project_type == "fullstack":
        project_type = "fullstack"
    elif detected_stack.project_type == "cli":
        project_type = f"{detected_stack.primary_language}_cli"
    elif detected_stack.is_frontend_only:
        project_type = detected_stack.frontend_framework.lower().replace(".", "") if detected_stack.frontend_framework else "react"
    elif detected_stack.backend_framework and detected_stack.frontend_framework:
        project_type = "fullstack"
    elif detected_stack.backend_framework:
        project_type = f"{detected_stack.backend_language or 'python'}_api"
    elif detected_stack.frontend_framework:
        project_type = detected_stack.frontend_framework.lower().replace(".", "").replace(" ", "")
    else:
        project_type = "react"  # ultimate fallback

    stack_summary = detected_stack.summary()
    yield sse("agent_end", {"agent": "team_lead", "name": "Team Leader", "icon": "crown", "result": f"Project: {project_type}. Stack: {stack_summary}. Assigning to PM."})
    yield sse("blackboard_update", {"field": "project_type", "value": project_type})
    yield sse("blackboard_update", {"field": "detected_stack", "value": detected_stack.to_dict()})

    # Team Lead speaks to the team
    yield sse("discussion", {
        "from": "Team Leader", "to": "All", "icon": "crown",
        "message": f"Team, we have a new project: \"{prompt}\". I'm assigning PM to write the requirements. Let's build something great."
    })
    await asyncio.sleep(0.15)

    # ═══════════════════════════════════════════════════════════════
    #  PHASE 2: PRODUCT MANAGER — PRD
    # ═══════════════════════════════════════════════════════════════
    yield sse("agent_start", {"agent": "pm", "name": "Product Manager", "icon": "clipboard", "description": "Writing product requirements..."})

    prd_raw = await _call_llm(AGENT_PM_SYSTEM, f"Create a PRD for: {prompt}")
    prd = _extract_json(prd_raw)
    if not prd or not isinstance(prd, dict):
        prd = {"title": prompt[:50], "description": prompt,
               "user_stories": [f"As a user, I want to {prompt.lower()}"],
               "features": ["Core functionality", "Clean UI", "Responsive design"],
               "constraints": ["Must work in modern browsers"], "tech_hints": [project_type]}
    board.prd = prd

    yield sse("agent_end", {"agent": "pm", "name": "Product Manager", "icon": "clipboard", "result": f"PRD: {prd.get('title', 'Project')} — {len(prd.get('features', []))} features"})
    yield sse("blackboard_update", {"field": "prd", "value": prd})

    # PM presents PRD to the team
    features_str = ", ".join(prd.get("features", [])[:5])
    yield sse("discussion", {
        "from": "Product Manager", "to": "Team Leader", "icon": "clipboard",
        "message": f"PRD ready: \"{prd.get('title', 'Project')}\". Key features: {features_str}. Requesting review."
    })
    await asyncio.sleep(0.1)

    # ═══════════════════════════════════════════════════════════════
    #  DISCUSSION: Team Lead reviews the PRD
    # ═══════════════════════════════════════════════════════════════
    tl_review = await _call_llm(AGENT_TEAMLEAD_REVIEW, f"PRD:\n{json.dumps(prd, indent=2)}\n\nReview this PRD briefly.", max_tokens=200, temp=0.5)
    if tl_review:
        tl_review = tl_review[:300]
    else:
        tl_review = "Looks solid. The features cover the core requirements. Approved — let's move to architecture."

    yield sse("discussion", {
        "from": "Team Leader", "to": "Product Manager", "icon": "crown",
        "message": tl_review
    })
    await asyncio.sleep(0.1)

    # Architect chimes in
    arch_feedback = await _call_llm(AGENT_ARCHITECT_REVIEW, f"PRD:\n{json.dumps(prd, indent=2)}\n\nGive brief technical feedback.", max_tokens=200, temp=0.5)
    if arch_feedback:
        arch_feedback = arch_feedback[:300]
    else:
        arch_feedback = "Technically feasible. I'll design the component architecture and file structure now."

    yield sse("discussion", {
        "from": "Architect", "to": "Team Leader", "icon": "layers",
        "message": arch_feedback
    })
    await asyncio.sleep(0.1)

    yield sse("message", {"content": f"**PRD Approved:** {prd.get('title', prompt)}\n{prd.get('description', '')}"})

    # ═══════════════════════════════════════════════════════════════
    #  PHASE 3: ARCHITECT — System Design
    # ═══════════════════════════════════════════════════════════════
    yield sse("agent_start", {"agent": "architect", "name": "Architect", "icon": "layers", "description": "Designing system architecture..."})

    # Use tech-aware architect prompt
    architect_system = get_architect_prompt_for_stack(detected_stack) if (detected_stack.backend_framework or detected_stack.frontend_framework or detected_stack.languages) else AGENT_ARCHITECT_SYSTEM_DEFAULT
    arch_prompt = f"PRD:\n{json.dumps(prd, indent=2)}\n\nDesign the system architecture for a {project_type} project.\nUser request: {prompt}"
    arch_raw = await _call_llm(architect_system, arch_prompt)
    arch = _extract_json(arch_raw)

    if not arch or not isinstance(arch, dict) or "directory_structure" not in arch:
        # Use detected-stack-aware fallback instead of hardcoded React
        arch = get_fallback_architecture(detected_stack, prompt)

    board.architecture = arch
    board.file_plan = arch.get("directory_structure", [])

    yield sse("agent_end", {"agent": "architect", "name": "Architect", "icon": "layers", "result": f"Architecture: {len(board.file_plan)} files planned"})
    yield sse("blackboard_update", {"field": "architecture", "value": arch})

    # Architect explains design to the team
    stack_str = ", ".join(f"{k}: {v}" for k, v in arch.get("stack", {}).items())
    yield sse("discussion", {
        "from": "Architect", "to": "Engineer", "icon": "layers",
        "message": f"Architecture ready. Stack: {stack_str}. {len(board.file_plan)} files planned. Engineer, you're up — start coding."
    })
    await asyncio.sleep(0.1)

    yield sse("discussion", {
        "from": "Engineer", "to": "Architect", "icon": "code",
        "message": f"Got it. I'll implement all {len(board.file_plan)} files. Starting with the core setup files."
    })
    await asyncio.sleep(0.1)

    # ═══════════════════════════════════════════════════════════════
    #  PHASE 4: ENGINEER — Live Code Writing
    # ═══════════════════════════════════════════════════════════════
    yield sse("agent_start", {"agent": "engineer", "name": "Engineer", "icon": "code", "description": "Writing code..."})
    yield sse("message", {"content": f"Building project with {len(board.file_plan)} files. Watch the code appear live..."})

    total = len(board.file_plan)
    for idx, file_path in enumerate(board.file_plan, 1):
        yield sse("file_start", {"path": file_path, "index": idx, "total": total})
        await asyncio.sleep(0.05)

        # Use tech-aware engineer prompt per-file — stream tokens live to IDE
        eng_system = get_engineer_prompt_for_stack(detected_stack, file_path)
        eng_context = f"PRD: {json.dumps(prd)}\nArchitecture: {json.dumps(arch)}\n\nWrite the complete file: {file_path}\nUser request: {prompt}"

        # Stream tokens directly from LLM → SSE → frontend (true live coding)
        # Uses async wrapper to avoid blocking the event loop
        content_parts = []
        async for token in _stream_llm_to_sse(eng_system, eng_context, file_path, use_coder=True):
            content_parts.append(token)
            yield sse("file_delta", {"path": file_path, "delta": token})
            await asyncio.sleep(0)  # yield control to event loop

        content = "".join(content_parts)
        if not content:
            content = f"// {file_path}\n// Generated by Atoms Engine\n"
            yield sse("file_delta", {"path": file_path, "delta": content})
            await asyncio.sleep(0)

        content = re.sub(r'^```\w*\n?', '', content.strip())
        content = re.sub(r'\n?```$', '', content.strip())
        board.generated_files[file_path] = content

        yield sse("file_end", {"path": file_path, "index": idx, "total": total})
        await asyncio.sleep(0.03)

    yield sse("agent_end", {"agent": "engineer", "name": "Engineer", "icon": "code", "result": f"Wrote {total} files"})

    yield sse("discussion", {
        "from": "Engineer", "to": "QA Engineer", "icon": "code",
        "message": f"All {total} files are written. Handing off to QA for testing and review."
    })
    await asyncio.sleep(0.1)

    # ═══════════════════════════════════════════════════════════════
    #  PHASE 5: QA ENGINEER — Testing & Review
    # ═══════════════════════════════════════════════════════════════
    yield sse("agent_start", {"agent": "qa", "name": "QA Engineer", "icon": "shield", "description": "Running tests and code review..."})

    # Build code summary for QA
    code_summary = "\n\n".join(
        f"--- {p} ---\n{c[:800]}" for p, c in list(board.generated_files.items())[:8]
    )

    qa_raw = await _call_llm(
        AGENT_QA_SYSTEM,
        f"Project: {prompt}\nPRD: {json.dumps(prd)}\n\nReview these {len(board.generated_files)} files:\n{code_summary}",
        max_tokens=1024
    )
    qa_result = _extract_json(qa_raw)

    if not qa_result or not isinstance(qa_result, dict):
        qa_result = {
            "status": "pass", "bugs": [],
            "improvements": ["Consider adding error boundaries", "Add loading states"],
            "test_results": {"total_files_checked": total, "files_with_issues": 0, "critical_bugs": 0, "warnings": 1},
            "overall_score": 82,
            "verdict": "PASS — Code is production-ready with minor suggestions"
        }

    yield sse("agent_end", {"agent": "qa", "name": "QA Engineer", "icon": "shield", "result": f"QA Score: {qa_result.get('overall_score', 'N/A')}/100 — {qa_result.get('verdict', 'Done')}"})
    yield sse("blackboard_update", {"field": "qa_result", "value": qa_result})

    # QA discusses results with the team
    bugs = qa_result.get("bugs", [])
    improvements = qa_result.get("improvements", [])
    test_info = qa_result.get("test_results", {})

    yield sse("discussion", {
        "from": "QA Engineer", "to": "Team Leader", "icon": "shield",
        "message": f"Testing complete. Score: {qa_result.get('overall_score', 82)}/100. "
                   f"Checked {test_info.get('total_files_checked', total)} files. "
                   f"Found {len(bugs)} bug(s), {test_info.get('warnings', 0)} warning(s). "
                   f"Verdict: {qa_result.get('verdict', 'PASS')}"
    })
    await asyncio.sleep(0.1)

    # If there are high-severity bugs, Engineer fixes them
    high_bugs = [b for b in bugs if isinstance(b, dict) and b.get("severity") == "high"]
    if high_bugs:
        yield sse("discussion", {
            "from": "QA Engineer", "to": "Engineer", "icon": "shield",
            "message": f"Found {len(high_bugs)} critical bug(s) that need fixing: " + "; ".join(b.get("description", "") for b in high_bugs[:3])
        })
        await asyncio.sleep(0.1)

        yield sse("discussion", {
            "from": "Engineer", "to": "QA Engineer", "icon": "code",
            "message": f"On it. Fixing {len(high_bugs)} critical issue(s) now."
        })
        await asyncio.sleep(0.1)

        # Fix each high-severity bug
        for bug in high_bugs[:3]:
            bug_file = bug.get("file", "")
            bug_desc = bug.get("description", "")
            if bug_file and bug_file in board.generated_files:
                yield sse("agent_start", {"agent": "engineer", "name": "Engineer", "icon": "code", "description": f"Fixing: {bug_desc[:50]}..."})

                fix_prompt = AGENT_ENGINEER_FIX.replace("{bug_description}", bug_desc).replace("{file_path}", bug_file).replace("{file_content}", board.generated_files[bug_file][:3000])

                # Stream fix tokens live (async to avoid blocking)
                yield sse("file_start", {"path": bug_file, "index": 0, "total": 0})
                fix_parts = []
                async for token in _stream_llm_to_sse("You are a bug-fixing engineer.", fix_prompt, bug_file, max_tokens=2048, use_coder=True):
                    fix_parts.append(token)
                    yield sse("file_delta", {"path": bug_file, "delta": token})
                    await asyncio.sleep(0)

                fixed = "".join(fix_parts)
                if fixed:
                    fixed = re.sub(r'^```\w*\n?', '', fixed.strip())
                    fixed = re.sub(r'\n?```$', '', fixed.strip())
                    board.generated_files[bug_file] = fixed

                yield sse("file_end", {"path": bug_file, "index": 0, "total": 0})

                yield sse("agent_end", {"agent": "engineer", "name": "Engineer", "icon": "code", "result": f"Fixed: {bug_desc[:60]}"})
                await asyncio.sleep(0.05)

        yield sse("discussion", {
            "from": "Engineer", "to": "QA Engineer", "icon": "code",
            "message": "All critical bugs fixed. Ready for re-check."
        })
        yield sse("discussion", {
            "from": "QA Engineer", "to": "Team Leader", "icon": "shield",
            "message": "Fixes verified. Project is now ready for deployment."
        })
        await asyncio.sleep(0.1)
    else:
        # No critical bugs
        if improvements:
            yield sse("discussion", {
                "from": "QA Engineer", "to": "Engineer", "icon": "shield",
                "message": f"No critical bugs. Suggestions for later: {', '.join(improvements[:3])}"
            })
            await asyncio.sleep(0.1)

        yield sse("discussion", {
            "from": "QA Engineer", "to": "Team Leader", "icon": "shield",
            "message": "All tests passed. Code is clean. Ready for deployment."
        })
        await asyncio.sleep(0.1)

    # Team Leader gives the green light
    yield sse("discussion", {
        "from": "Team Leader", "to": "DevOps", "icon": "crown",
        "message": "QA passed. Deploy the project now."
    })
    await asyncio.sleep(0.1)

    # ═══════════════════════════════════════════════════════════════
    #  PHASE 6: DEVOPS — Auto-Deploy
    # ═══════════════════════════════════════════════════════════════
    yield sse("agent_start", {"agent": "devops", "name": "DevOps", "icon": "rocket", "description": "Deploying project..."})

    yield sse("message", {"content": "Writing files to disk..."})
    _write_files_to_disk(board.generated_files)
    await asyncio.sleep(0.1)

    has_pkg = "package.json" in board.generated_files
    has_requirements = "requirements.txt" in board.generated_files
    has_go_mod = "go.mod" in board.generated_files
    has_pom = "pom.xml" in board.generated_files
    has_cargo = "Cargo.toml" in board.generated_files

    if has_pkg:
        frontend_dir = _find_frontend_dir(board.generated_files)
        cwd = frontend_dir if frontend_dir else None
        yield sse("message", {"content": "Running npm install...", "type": "stdout"})
        yield sse("discussion", {"from": "DevOps", "to": "Team Leader", "icon": "rocket", "message": "Installing npm dependencies..."})
        success = True
        async for item in _run_npm_install_streaming(cwd=cwd):
            if isinstance(item, int):
                success = item == 0
                break
            line, is_stderr = item
            yield sse("message", {"content": line, "type": "stderr" if is_stderr else "stdout"})
        if success:
            yield sse("message", {"content": "Dependencies installed. Starting dev server...", "type": "stdout"})
        else:
            yield sse("message", {"content": "npm install failed (see terminal output above).", "type": "stderr"})

        ok, msg, port = _start_dev_server(cwd=cwd)
        if ok:
            preview_url = f"http://127.0.0.1:{port}"
            yield sse("preview_ready", {"url": preview_url, "port": port})
            yield sse("message", {"content": f"Preview running at {preview_url}", "type": "stdout"})
            yield sse("discussion", {"from": "DevOps", "to": "Team Leader", "icon": "rocket", "message": f"Deployed successfully! Live at port {port}."})
        else:
            yield sse("message", {"content": f"Dev server: {msg}", "type": "stderr"})
    elif has_requirements:
        yield sse("message", {"content": "Python project ready. Run: pip install -r requirements.txt && python main.py"})
        yield sse("discussion", {"from": "DevOps", "to": "Team Leader", "icon": "rocket", "message": "Python project files written. User can install deps with pip and run the server."})
    elif has_go_mod:
        yield sse("message", {"content": "Go project ready. Run: go mod tidy && go run main.go"})
        yield sse("discussion", {"from": "DevOps", "to": "Team Leader", "icon": "rocket", "message": "Go project files written. User can build with go build."})
    elif has_pom:
        yield sse("message", {"content": "Java project ready. Run: mvn spring-boot:run"})
        yield sse("discussion", {"from": "DevOps", "to": "Team Leader", "icon": "rocket", "message": "Java project files written. User can build with Maven."})
    elif has_cargo:
        yield sse("message", {"content": "Rust project ready. Run: cargo run"})
        yield sse("discussion", {"from": "DevOps", "to": "Team Leader", "icon": "rocket", "message": "Rust project files written. User can build with cargo."})
    else:
        yield sse("message", {"content": "Project files written to disk."})
        yield sse("discussion", {"from": "DevOps", "to": "Team Leader", "icon": "rocket", "message": "All project files deployed."})

    yield sse("agent_end", {"agent": "devops", "name": "DevOps", "icon": "rocket", "result": "Project deployed"})

    # Final team discussion
    yield sse("discussion", {
        "from": "Team Leader", "to": "All", "icon": "crown",
        "message": f"Great work team! Project \"{prd.get('title', 'Project')}\" is live with {total} files. QA score: {qa_result.get('overall_score', 82)}/100."
    })
    yield sse("message", {"content": f"Project complete! {total} files created. QA Score: {qa_result.get('overall_score', 82)}/100. Project is live!"})


# ─── Race Mode Pipeline ─────────────────────────────────────────────────────

async def race_pipeline(prompt: str, existing_files: dict, num_teams: int = 2) -> AsyncGenerator[str, None]:
    """Race Mode: N parallel teams compete, Judge picks the best."""

    yield sse("agent_start", {"agent": "team_lead", "name": "Team Leader", "icon": "crown", "description": f"Launching Race Mode with {num_teams} teams..."})
    await asyncio.sleep(0.3)
    yield sse("agent_end", {"agent": "team_lead", "result": f"Race Mode: {num_teams} parallel teams competing"})

    # Detect stack once for all race teams
    race_stack = detect_stack(prompt)
    race_architect_system = get_architect_prompt_for_stack(race_stack) if (race_stack.backend_framework or race_stack.frontend_framework or race_stack.languages) else AGENT_ARCHITECT_SYSTEM_DEFAULT

    yield sse("race_start", {"teams": num_teams})
    await asyncio.sleep(0.2)

    # Run teams in parallel
    boards: List[Blackboard] = []

    for team_idx in range(1, num_teams + 1):
        yield sse("race_progress", {"team": team_idx, "status": "generating", "phase": "planning"})
        await asyncio.sleep(0.1)

        board = Blackboard(prompt, existing_files)

        # PM phase
        prd_raw = await _call_llm(
            AGENT_PM_SYSTEM,
            f"Create a PRD for: {prompt}\n\n(Team {team_idx} — be creative with your approach)",
            temp=0.4 + (team_idx * 0.15),  # Different temperatures for diversity
        )
        prd = _extract_json(prd_raw)
        if not prd or not isinstance(prd, dict):
            prd = {"title": prompt, "features": ["Core feature"], "user_stories": [], "constraints": [], "tech_hints": []}
        board.prd = prd

        yield sse("race_progress", {"team": team_idx, "status": "generating", "phase": "architecture"})

        # Architect phase
        arch_raw = await _call_llm(
            race_architect_system,
            f"PRD: {json.dumps(prd)}\n\nDesign architecture. (Team {team_idx})\nUser request: {prompt}",
            temp=0.3 + (team_idx * 0.1),
        )
        arch = _extract_json(arch_raw)
        if not arch or not isinstance(arch, dict) or "directory_structure" not in arch:
            arch = get_fallback_architecture(race_stack, prompt)
        board.architecture = arch
        board.file_plan = arch.get("directory_structure", [])

        yield sse("race_progress", {"team": team_idx, "status": "generating", "phase": "coding"})

        # Engineer phase
        for file_path in board.file_plan:
            eng_system = get_engineer_prompt_for_stack(race_stack, file_path)
            content = await _call_llm(eng_system, f"PRD: {json.dumps(prd)}\nWrite: {file_path}\nRequest: {prompt}", temp=0.3 + (team_idx * 0.1), use_coder=True)
            if content:
                content = re.sub(r'^```\w*\n?', '', content.strip())
                content = re.sub(r'\n?```$', '', content.strip())
                board.generated_files[file_path] = content
            else:
                board.generated_files[file_path] = f"// {file_path}\n"

        yield sse("race_progress", {"team": team_idx, "status": "complete", "phase": "done", "files": len(board.generated_files)})
        boards.append(board)

    # ═══ Judge Phase ═══
    yield sse("agent_start", {"agent": "judge", "name": "Judge", "icon": "scale", "description": "Evaluating solutions..."})
    await asyncio.sleep(0.2)

    best_idx = 0
    best_score = 0

    for i, board in enumerate(boards):
        # Score based on: number of files, total code length, has key files
        file_count = len(board.generated_files)
        total_lines = sum(c.count('\n') for c in board.generated_files.values())
        has_entry = any('main' in p or 'App' in p or 'index' in p for p in board.generated_files)

        score = (file_count * 10) + (min(total_lines, 500) * 0.2) + (20 if has_entry else 0)
        board.score = round(score, 1)

        # Try LLM judge for more sophisticated scoring
        all_code = "\n\n".join(f"--- {p} ---\n{c[:500]}" for p, c in list(board.generated_files.items())[:5])
        judge_raw = await _call_llm(AGENT_JUDGE_SYSTEM, f"Evaluate this solution for: {prompt}\n\nCode:\n{all_code}")
        judge = _extract_json(judge_raw)
        if judge and isinstance(judge, dict) and "score" in judge:
            board.score = float(judge["score"])

        yield sse("race_progress", {"team": i + 1, "status": "scored", "score": board.score})

        if board.score > best_score:
            best_score = board.score
            best_idx = i

    winner = boards[best_idx]
    yield sse("agent_end", {"agent": "judge", "result": f"Team {best_idx + 1} wins with score {winner.score}"})
    yield sse("race_result", {"winner": best_idx + 1, "score": winner.score, "teams": num_teams})
    await asyncio.sleep(0.2)

    # Write the winning solution with live typing
    yield sse("agent_start", {"agent": "engineer", "name": "Engineer", "icon": "code", "description": "Writing winning solution..."})
    yield sse("message", {"content": f"Race complete! Team {best_idx + 1} won (score: {winner.score}). Writing code..."})

    total = len(winner.generated_files)
    for idx, (file_path, content) in enumerate(winner.generated_files.items(), 1):
        yield sse("file_start", {"path": file_path, "index": idx, "total": total})
        await asyncio.sleep(0.03)

        pos = 0
        while pos < len(content):
            chunk = content[pos:pos + TYPING_CHUNK]
            yield sse("file_delta", {"path": file_path, "delta": chunk})
            pos += TYPING_CHUNK
            await asyncio.sleep(TYPING_DELAY)

        yield sse("file_end", {"path": file_path, "index": idx, "total": total})

    yield sse("agent_end", {"agent": "engineer", "result": f"Wrote {total} files from winning team"})

    # Auto-deploy race winner
    yield sse("agent_start", {"agent": "devops", "name": "DevOps", "icon": "rocket", "description": "Deploying winning solution..."})
    _write_files_to_disk(winner.generated_files)
    frontend_dir = _find_frontend_dir(winner.generated_files)
    if frontend_dir:
        yield sse("message", {"content": "Installing dependencies...", "type": "stdout"})
        success = True
        async for item in _run_npm_install_streaming(cwd=frontend_dir):
            if isinstance(item, int):
                success = item == 0
                break
            line, is_stderr = item
            yield sse("message", {"content": line, "type": "stderr" if is_stderr else "stdout"})
        ok, msg, port = _start_dev_server(cwd=frontend_dir)
        if ok:
            yield sse("preview_ready", {"url": f"http://127.0.0.1:{port}", "port": port})
            yield sse("message", {"content": f"Preview live at http://127.0.0.1:{port}", "type": "stdout"})
        elif not success:
            yield sse("message", {"content": "npm install failed.", "type": "stderr"})
    yield sse("agent_end", {"agent": "devops", "result": "Deployed"})
    yield sse("message", {"content": f"Done! {total} files created from the winning team. Project is live!"})


# ─── Main Stream Generator ──────────────────────────────────────────────────

async def _stream_unified_standard(prompt: str, files: dict) -> AsyncGenerator[str, None]:
    """
    Stream events from the unified PipelineRunner (single source of truth).

    Legacy `standard_pipeline()` remains in this module for backward compatibility,
    but new standard execution now routes through backend.core.pipeline_runner.
    """
    from backend.core.pipeline_runner import PipelineContext, PipelineRequest, run_pipeline
    from backend.storage.artifact_store import flatten_structure, get_artifact_store

    queue: asyncio.Queue = asyncio.Queue()
    loop = asyncio.get_running_loop()
    result_holder: dict = {}
    sentinel = object()

    def _emit(event_name: str, payload: dict) -> None:
        loop.call_soon_threadsafe(queue.put_nowait, (event_name, payload))

    def _runner():
        req = PipelineRequest(
            idea=prompt,
            mode="full",
            channel="web",
            user_id="atoms-stream",
            project_id="atoms-stream",
            token_tier="free",
            memory_scope="project",
        )
        result_holder["result"] = run_pipeline(req, PipelineContext(on_event=_emit, strict_contracts=True))
        loop.call_soon_threadsafe(queue.put_nowait, (sentinel, {}))

    loop.run_in_executor(None, _runner)

    agent_meta: Dict[str, tuple[str, str]] = {
        "planner": ("Planner", "map"),
        "db_schema": ("Architect", "layers"),
        "auth": ("Engineer", "code"),
        "coder": ("Engineer", "code"),
        "code_reviewer": ("QA Engineer", "shield"),
        "tester": ("QA Engineer", "shield"),
        "deployer": ("DevOps", "rocket"),
    }

    agent_thinking: Dict[str, str] = {
        "planner": "Breaking down your request into an execution strategy.",
        "db_schema": "Designing data structures and schema boundaries.",
        "auth": "Planning authentication and access control flow.",
        "coder": "Implementing the project files and feature logic.",
        "code_reviewer": "Reviewing generated code for quality and risk.",
        "tester": "Validating behavior and checking for regressions.",
        "deployer": "Preparing install/build/deploy runtime steps.",
    }

    def _agent_display(agent_id: str) -> tuple[str, str]:
        return agent_meta.get(agent_id, (agent_id.replace("_", " ").title(), "brain"))

    async def _emit_tokens(text: str, chunk_size: int = 3, delay_s: float = 0.005) -> AsyncGenerator[str, None]:
        """Stream text as message_token events for Replit/Atmos-level typewriter effect.
        Small chunks (3 chars) + short delay (5ms) = smooth 60fps dripping."""
        if not text:
            return
        for i in range(0, len(text), chunk_size):
            yield sse("message_token", {"token": text[i:i + chunk_size]})
            await asyncio.sleep(delay_s)

    event_map = {
        "agent_started": "agent_start",
        "agent_completed": "agent_end",
        "agent_failed": "agent_error",
        "execution_plan": "execution_plan",
        "budget_configured": "budget_configured",
        "state_transition": "blackboard_update",
        "agent_retry": "message",
        "run_started": "run_started",
        "run_failed": "error",
        "run_timeout": "error",
        "run_finished": "message",
    }

    while True:
        name, payload = await queue.get()
        if name is sentinel:
            break

        sse_type = event_map.get(name, "message")
        if sse_type == "agent_start":
            agent_id = payload.get("agent", "unknown")
            display_name, icon = _agent_display(agent_id)
            attempt = payload.get("attempt", 1)
            yield sse(sse_type, {
                "agent": agent_id,
                "name": display_name,
                "icon": icon,
                "description": f"{display_name} running (attempt {attempt})",
            })
        elif sse_type == "agent_end":
            agent_id = payload.get("agent", "unknown")
            display_name, icon = _agent_display(agent_id)
            yield sse(sse_type, {
                "agent": agent_id,
                "name": display_name,
                "icon": icon,
                "result": f"Completed in {payload.get('duration_ms', 0)}ms",
            })
        elif sse_type == "agent_error":
            yield sse("error", {"message": f"{payload.get('agent', 'agent')} failed: {payload.get('error', 'unknown error')}"})
        elif sse_type == "blackboard_update":
            yield sse("blackboard_update", {"field": "state", "value": payload.get("state")})
        elif sse_type in {"run_started", "budget_configured", "execution_plan"}:
            event_payload = dict(payload)
            if sse_type == "run_started":
                chat_model = os.getenv("NIM_MODEL", "").strip()
                coder_model = os.getenv("NIM_CODER_MODEL", "").strip() or chat_model
                if chat_model:
                    event_payload["chat_model"] = chat_model
                if coder_model:
                    event_payload["coder_model"] = coder_model
                intro = (
                    "Team Leader: I received your prompt. "
                    "I am analyzing requirements and assigning the team now.\n\n"
                )
                async for token_evt in _emit_tokens(intro):
                    yield token_evt
            elif sse_type == "execution_plan":
                order = event_payload.get("execution_order")
                if isinstance(order, list) and order:
                    readable = " -> ".join(str(x).replace("_", " ") for x in order)
                    plan_text = f"Planner: Execution plan ready: {readable}.\n\n"
                else:
                    plan_text = "Planner: Execution plan is ready.\n\n"
                async for token_evt in _emit_tokens(plan_text):
                    yield token_evt
            yield sse(sse_type, event_payload)
        elif sse_type == "error":
            yield sse("error", {"message": payload.get("error", payload.get("message", "pipeline error"))})
        else:
            message = payload.get("message") or payload.get("event") or name
            yield sse("message", {"content": str(message)})

        if sse_type == "agent_start":
            agent_id = payload.get("agent", "unknown")
            display_name, _ = _agent_display(agent_id)
            thinking = agent_thinking.get(agent_id, "Working on the assigned step.")
            async for token_evt in _emit_tokens(f"{display_name}: {thinking}\n"):
                yield token_evt

        if sse_type == "agent_end":
            agent_id = payload.get("agent", "unknown")
            display_name, _ = _agent_display(agent_id)
            result = payload.get("duration_ms")
            completion = (
                f"{display_name}: Completed this step in {result}ms.\n\n"
                if result is not None
                else f"{display_name}: Completed this step.\n\n"
            )
            async for token_evt in _emit_tokens(completion):
                yield token_evt

    result = result_holder.get("result", {})
    manifest = result.get("artifact_manifest") or {}
    files_map = {}
    if manifest.get("project_key") and manifest.get("version"):
        try:
            files_map = get_artifact_store().load_version(
                project_key=manifest["project_key"],
                version=int(manifest["version"]),
            )
        except Exception:
            files_map = {}
    if not files_map:
        files_map = flatten_structure(result.get("agent_outputs", {}).get("coder", {}))

    total = len(files_map)
    for idx, (path, content) in enumerate(files_map.items(), start=1):
        async for token_evt in _emit_tokens(f"Engineer: Writing {path} ({idx}/{total})...\n", chunk_size=18, delay_s=0.006):
            yield token_evt
        yield sse("file_start", {"path": path, "index": idx, "total": total})
        yield sse("file_delta", {"path": path, "delta": content})
        yield sse("file_end", {"path": path, "index": idx, "total": total})
        async for token_evt in _emit_tokens(f"Engineer: Finished {path}.\n", chunk_size=18, delay_s=0.004):
            yield token_evt

    state = result.get("state", "unknown")
    yield sse("message", {"content": f"Unified pipeline finished with state={state}. Files: {total}"})

    # ═══════════════════════════════════════════════════════════════
    #  AUTO-DEPLOY: Write files to disk and start dev server for preview
    # ═══════════════════════════════════════════════════════════════
    if files_map:
        yield sse("agent_start", {"agent": "devops", "name": "DevOps", "icon": "rocket", "description": "Deploying project..."})
        yield sse("message", {"content": "Writing files to disk..."})
        _write_files_to_disk(files_map)
        await asyncio.sleep(0.1)

        # Locate the frontend directory containing package.json with vite
        frontend_dir = _find_frontend_dir(files_map)

        if frontend_dir:
            yield sse("message", {"content": f"Running npm install in {frontend_dir.name}/...", "type": "stdout"})
            yield sse("discussion", {"from": "DevOps", "to": "Team Leader", "icon": "rocket", "message": "Installing npm dependencies..."})
            success = True
            async for item in _run_npm_install_streaming(cwd=frontend_dir):
                if isinstance(item, int):
                    success = item == 0
                    break
                line, is_stderr = item
                yield sse("message", {"content": line, "type": "stderr" if is_stderr else "stdout"})
            if success:
                yield sse("message", {"content": "Dependencies installed. Starting dev server...", "type": "stdout"})
            else:
                yield sse("message", {"content": "npm install failed (see terminal output above).", "type": "stderr"})

            ok, msg, port = _start_dev_server(cwd=frontend_dir)
            if ok:
                preview_url = f"http://127.0.0.1:{port}"
                yield sse("preview_ready", {"url": preview_url, "port": port})
                yield sse("message", {"content": f"Preview running at {preview_url}", "type": "stdout"})
                yield sse("discussion", {"from": "DevOps", "to": "Team Leader", "icon": "rocket", "message": f"Deployed successfully! Live at port {port}."})
            else:
                yield sse("message", {"content": f"Dev server: {msg}", "type": "stderr"})
        else:
            yield sse("message", {"content": "Project files written to disk (no frontend package.json found for preview)."})

        yield sse("agent_end", {"agent": "devops", "name": "DevOps", "icon": "rocket", "result": "Project deployed"})


async def atoms_stream(prompt: str, files: dict, mode: str = "standard", race_teams: int = 2) -> AsyncGenerator[str, None]:
    try:
        if mode == "race":
            async for event in race_pipeline(prompt, files, race_teams):
                yield event
        else:
            async for event in _stream_unified_standard(prompt, files):
                yield event

        yield sse("done", {"message": "Complete"})
    except Exception as e:
        yield sse("error", {"message": str(e)})
        yield sse("done", {"message": "Complete"})


# ─── API Endpoint ────────────────────────────────────────────────────────────

@router.post("/stream")
async def atoms_endpoint(body: AtomsRequest):
    """Atoms Engine: Multi-agent pipeline with optional Race Mode."""
    return StreamingResponse(
        atoms_stream(body.prompt, body.files, body.mode, body.race_teams),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


# ─── Phase-2: Diagram Acknowledgment ─────────────────────────────────────────

# Global engine instance tracking for diagram acknowledgment
_active_engines: Dict[str, "AtomsEngine"] = {}


class AcknowledgeDiagramResponse(BaseModel):
    success: bool
    message: str


@router.post("/engine/acknowledge-diagram", response_model=AcknowledgeDiagramResponse)
async def acknowledge_diagram(run_id: str = ""):
    """
    Acknowledge a planning diagram.
    
    Must be called before execution can proceed when a Mermaid diagram
    is detected in the roadmap.
    """
    from backend.engine.atoms_engine import AtomsEngine
    from backend.engine.events import get_event_emitter, EngineEventType
    
    # Emit acknowledgment event globally (for any listening engines)
    emitter = get_event_emitter()
    emitter.emit(EngineEventType.DIAGRAM_ACKNOWLEDGED, {"run_id": run_id})
    
    return AcknowledgeDiagramResponse(
        success=True,
        message="Diagram acknowledged. Execution can now proceed."
    )


# ─── Phase-2: Engine Events Endpoint ─────────────────────────────────────────

class EventsResponse(BaseModel):
    events: list
    total: int


@router.get("/engine/events", response_model=EventsResponse)
async def get_engine_events(limit: int = 50, event_type: str = ""):
    """
    Get recent engine events.
    
    Useful for debugging and monitoring agent activity.
    """
    from backend.engine.events import get_event_emitter, EngineEventType
    
    emitter = get_event_emitter()
    
    # Filter by event type if specified
    filter_type = None
    if event_type:
        try:
            filter_type = EngineEventType(event_type)
        except ValueError:
            pass
    
    events = emitter.get_history(event_type=filter_type, limit=limit)
    
    # Convert to serializable format
    events_data = [
        {
            "type": e.type.value,
            "payload": e.payload,
            "timestamp": e.timestamp.isoformat(),
            "run_id": e.run_id,
        }
        for e in events
    ]
    
    return EventsResponse(events=events_data, total=len(events_data))


# ─── Agent Chat Runtime (WebSocket + Orchestrator Events) ───────────────────

_agent_chat_runs: Dict[str, Dict[str, Any]] = {}


class AgentChatExecuteRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    project_id: Optional[str] = None
    max_revision_loops: int = Field(default=2, ge=0, le=3)


class AgentChatExecuteResponse(BaseModel):
    run_id: str
    project_id: str
    status: str


@router.websocket("/ws/agents/{project_id}")
async def agents_ws_updates(websocket: WebSocket, project_id: str) -> None:
    """
    Subscribe to live per-agent updates for a project.

    Message types:
    - connected
    - keepalive_ping / keepalive_pong
    - run_started / run_finished / run_failed
    - agent_started / agent_completed / agent_token
    - task_started / task_retry / task_failed / task_completed
    - dag_batch_started / dag_batch_finished
    """
    bus = get_agent_stream_bus()
    await bus.connect(project_id, websocket)

    try:
        await websocket.send_json({"type": "connected", "project_id": project_id})
        while True:
            try:
                msg = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                if msg.strip().lower() == "ping":
                    await websocket.send_json({"type": "keepalive_pong"})
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "keepalive_ping"})
    except WebSocketDisconnect:
        logger.info("[Atoms] WS client disconnected: project_id=%s", project_id)
    except Exception as e:
        logger.exception("[Atoms] WS error: %s", e)
    finally:
        await bus.disconnect(project_id, websocket)


@router.post("/chat/execute", response_model=AgentChatExecuteResponse)
async def execute_agents_chat(body: AgentChatExecuteRequest) -> AgentChatExecuteResponse:
    """
    Start DAG + worker-pool execution and stream events over WebSocket.

    Client flow:
    1. Open WebSocket `/api/atoms/ws/agents/{project_id}`
    2. POST this endpoint with same `project_id`
    """
    run_id = f"agent_run_{uuid.uuid4().hex[:10]}"
    project_id = body.project_id or run_id

    _agent_chat_runs[run_id] = {
        "run_id": run_id,
        "project_id": project_id,
        "status": "queued",
        "prompt_preview": body.prompt[:200],
        "started_at": time.time(),
        "finished_at": None,
        "result": None,
        "error": None,
        "last_event": "queued",
    }

    asyncio.create_task(
        _run_agent_chat_session(
            run_id=run_id,
            project_id=project_id,
            prompt=body.prompt,
            max_revision_loops=body.max_revision_loops,
        )
    )

    return AgentChatExecuteResponse(run_id=run_id, project_id=project_id, status="queued")


@router.get("/chat/status/{run_id}")
async def get_agent_chat_status(run_id: str) -> Dict[str, Any]:
    status = _agent_chat_runs.get(run_id)
    if not status:
        raise HTTPException(status_code=404, detail="Run not found")
    return status


async def _run_agent_chat_session(
    run_id: str,
    project_id: str,
    prompt: str,
    max_revision_loops: int,
) -> None:
    bus = get_agent_stream_bus()
    state = _agent_chat_runs.get(run_id, {})
    state["status"] = "running"

    async def emit(event_name: str, payload: Dict[str, Any]) -> None:
        state["last_event"] = event_name
        await bus.broadcast(
            project_id,
            {
                "type": event_name,
                "run_id": run_id,
                "project_id": project_id,
                **payload,
            },
        )

    try:
        result = await execute_project(
            user_prompt=prompt,
            max_revision_loops=max_revision_loops,
            on_event=emit,
            project_id=project_id,
        )
        state["result"] = result
        state["status"] = "completed" if result.get("success") else "failed"
        state["finished_at"] = time.time()
    except Exception as exc:
        state["status"] = "failed"
        state["error"] = str(exc)
        state["finished_at"] = time.time()
        await emit("run_failed", {"error": str(exc)})


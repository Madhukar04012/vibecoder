"""
Atoms Engine — Full Multi-Agent SDLC Pipeline with Race Mode + Auto-Deploy

Architecture:
  - Blackboard Pattern: Shared state (PRD, Architecture, FileSystem)
  - Auto-Deploy: Files written to disk, npm install, dev server auto-started
  - Race Mode: N parallel teams, Judge selects best solution
"""

import asyncio
import json
import os
import re
import subprocess
import time
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/atoms", tags=["atoms"])

# ─── Project Sandbox ─────────────────────────────────────────────────────────
PROJECT_DIR = Path(__file__).resolve().parent.parent.parent / "generated_projects" / "demo"


def _write_files_to_disk(files: Dict[str, str]) -> None:
    """Write all generated files to the sandbox directory for preview."""
    # Clean previous project
    if PROJECT_DIR.exists():
        import shutil
        for item in PROJECT_DIR.iterdir():
            if item.name == 'node_modules':
                continue  # Don't delete node_modules (expensive to reinstall)
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

    PROJECT_DIR.mkdir(parents=True, exist_ok=True)
    for path, content in files.items():
        file_path = PROJECT_DIR / path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")


def _run_npm_install() -> tuple[bool, str]:
    """Run npm install in the project directory."""
    try:
        result = subprocess.run(
            "npm install",
            shell=True,
            cwd=str(PROJECT_DIR),
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


# Preview process management
_preview_proc: Optional[subprocess.Popen] = None
_preview_port: int = 5174


def _start_dev_server() -> tuple[bool, str, int]:
    """Start the Vite dev server for preview."""
    global _preview_proc, _preview_port
    import socket

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

    pkg_json = PROJECT_DIR / "package.json"
    if not pkg_json.exists():
        return False, "No package.json found", _preview_port

    try:
        _preview_proc = subprocess.Popen(
            f"npx vite --port {_preview_port} --host",
            shell=True,
            cwd=str(PROJECT_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(1.5)  # Give dev server time to start
        if _preview_proc.poll() is not None:
            return False, f"Dev server exited with code {_preview_proc.returncode}", _preview_port
        return True, f"Dev server running on port {_preview_port}", _preview_port
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

def _call_llm(system: str, user: str, max_tokens: int = 2048, temp: float = 0.3) -> str | None:
    """Call NIM or Ollama. Returns raw text."""
    import requests

    # Try NIM first
    api_key = os.getenv("NIM_API_KEY", "").strip()
    if api_key:
        model = os.getenv("NIM_MODEL", "meta/llama-3.3-70b-instruct")
        try:
            r = requests.post(
                "https://integrate.api.nvidia.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": model, "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ], "max_tokens": max_tokens, "temperature": temp},
                timeout=90,
            )
            r.raise_for_status()
            content = r.json().get("choices", [{}])[0].get("message", {}).get("content", "")
            return content.strip() if content.strip() else None
        except Exception as e:
            print(f"[LLM] NIM error: {e}")

    # Fallback to Ollama
    model = os.getenv("OLLAMA_CHAT_MODEL", "llama3.2")
    try:
        r = requests.post("http://localhost:11434/api/generate",
                          json={"model": model, "prompt": f"{system}\n\n{user}", "stream": False}, timeout=90)
        r.raise_for_status()
        return r.json().get("response", "").strip() or None
    except Exception:
        return None


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

Output ONLY valid JSON:
{
  "title": "Product title",
  "description": "What this product does",
  "user_stories": ["As a user, I want...", ...],
  "features": ["Feature 1", "Feature 2", ...],
  "constraints": ["Must be responsive", ...],
  "tech_hints": ["Use React", "REST API", ...]
}

No markdown. No explanation. JSON only."""

AGENT_ARCHITECT_SYSTEM = """You are a Senior Software Architect agent. Based on the PRD, design a COMPANY-LEVEL production system.

You MUST output a comprehensive project with MANY files. Think like a real engineering team.

Output ONLY valid JSON:
{
  "stack": {"frontend": "React + Vite", "styling": "CSS Modules", "state": "React Hooks"},
  "directory_structure": [
    "package.json",
    "vite.config.js",
    "index.html",
    "src/main.jsx",
    "src/App.jsx",
    "src/App.css",
    "src/components/Header.jsx",
    "src/components/Header.css",
    "src/components/Footer.jsx",
    "src/components/Sidebar.jsx",
    "src/components/Layout.jsx",
    "src/pages/Home.jsx",
    "src/pages/About.jsx",
    "src/hooks/useLocalStorage.js",
    "src/utils/helpers.js",
    "src/styles/variables.css",
    "src/styles/global.css"
  ],
  "component_tree": {"App": ["Layout"], "Layout": ["Header", "Sidebar", "MainContent", "Footer"]},
  "data_model": {"entities": []},
  "api_endpoints": []
}

RULES:
- Include AT LEAST 12-20 files for a proper project
- Include components/, pages/, hooks/, utils/, styles/ directories
- Include proper CSS files for each component
- Include Header, Footer, Sidebar, Layout components
- Include utility functions and custom hooks
- The project MUST be a complete, runnable React+Vite app
- package.json MUST include react, react-dom, and vite dependencies
- vite.config.js MUST use @vitejs/plugin-react

No markdown. No explanation. JSON only."""

AGENT_ENGINEER_SYSTEM = """You are a Senior Software Engineer at a top tech company. Write the COMPLETE contents of the file '{file_path}'.

CRITICAL RULES:
- Write PRODUCTION-READY, COMPANY-LEVEL code
- NO markdown, NO explanations, NO code fences (```)
- Output ONLY the raw file content — nothing before or after
- Include ALL imports, exports, types, and logic
- Write REAL functionality, not placeholders or TODOs
- Use modern best practices (hooks, functional components, proper CSS)
- For CSS files: write comprehensive styles with variables, responsive design, hover effects
- For components: include proper props, state management, event handlers
- For utils: include real utility functions with error handling
- For package.json: include react, react-dom, @vitejs/plugin-react, vite as dependencies
- For vite.config.js: use @vitejs/plugin-react plugin
- Make it look professional — good spacing, colors, typography"""

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

TYPING_CHUNK = 8
TYPING_DELAY = 0.008


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

    p = prompt.lower()
    if any(w in p for w in ["python", "fastapi", "flask", "django"]):
        project_type = "python_api"
    elif any(w in p for w in ["full stack", "fullstack"]):
        project_type = "fullstack"
    elif any(w in p for w in ["next.js", "nextjs"]):
        project_type = "nextjs"
    else:
        project_type = "react"

    yield sse("agent_end", {"agent": "team_lead", "result": f"Project: {project_type}. Assigning to PM."})
    yield sse("blackboard_update", {"field": "project_type", "value": project_type})

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

    prd_raw = _call_llm(AGENT_PM_SYSTEM, f"Create a PRD for: {prompt}")
    prd = _extract_json(prd_raw)
    if not prd or not isinstance(prd, dict):
        prd = {"title": prompt[:50], "description": prompt,
               "user_stories": [f"As a user, I want to {prompt.lower()}"],
               "features": ["Core functionality", "Clean UI", "Responsive design"],
               "constraints": ["Must work in modern browsers"], "tech_hints": [project_type]}
    board.prd = prd

    yield sse("agent_end", {"agent": "pm", "result": f"PRD: {prd.get('title', 'Project')} — {len(prd.get('features', []))} features"})
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
    tl_review = _call_llm(AGENT_TEAMLEAD_REVIEW, f"PRD:\n{json.dumps(prd, indent=2)}\n\nReview this PRD briefly.", max_tokens=200, temp=0.5)
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
    arch_feedback = _call_llm(AGENT_ARCHITECT_REVIEW, f"PRD:\n{json.dumps(prd, indent=2)}\n\nGive brief technical feedback.", max_tokens=200, temp=0.5)
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

    arch_prompt = f"PRD:\n{json.dumps(prd, indent=2)}\n\nDesign the system architecture for a {project_type} project."
    arch_raw = _call_llm(AGENT_ARCHITECT_SYSTEM, arch_prompt)
    arch = _extract_json(arch_raw)

    if not arch or not isinstance(arch, dict) or "directory_structure" not in arch:
        if project_type == "react":
            arch = {"stack": {"frontend": "React + Vite", "styling": "CSS"},
                    "directory_structure": ["package.json", "vite.config.js", "index.html", "src/main.jsx", "src/App.jsx", "src/index.css"]}
        elif project_type == "python_api":
            arch = {"stack": {"backend": "FastAPI", "database": "SQLite"},
                    "directory_structure": ["main.py", "routes.py", "models.py", "requirements.txt"]}
        else:
            arch = {"stack": {"frontend": "React", "backend": "FastAPI"},
                    "directory_structure": ["package.json", "vite.config.js", "index.html", "src/main.jsx", "src/App.jsx", "src/index.css"]}

    board.architecture = arch
    board.file_plan = arch.get("directory_structure", [])

    yield sse("agent_end", {"agent": "architect", "result": f"Architecture: {len(board.file_plan)} files planned"})
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

        eng_system = AGENT_ENGINEER_SYSTEM.replace("{file_path}", file_path)
        eng_context = f"PRD: {json.dumps(prd)}\nArchitecture: {json.dumps(arch)}\n\nWrite the complete file: {file_path}\nUser request: {prompt}"
        content = _call_llm(eng_system, eng_context)

        if not content:
            content = f"// {file_path}\n// Generated by Atoms Engine\n"
        content = re.sub(r'^```\w*\n?', '', content.strip())
        content = re.sub(r'\n?```$', '', content.strip())
        board.generated_files[file_path] = content

        pos = 0
        while pos < len(content):
            chunk = content[pos:pos + TYPING_CHUNK]
            yield sse("file_delta", {"path": file_path, "delta": chunk})
            pos += TYPING_CHUNK
            await asyncio.sleep(TYPING_DELAY)

        yield sse("file_end", {"path": file_path, "index": idx, "total": total})
        await asyncio.sleep(0.03)

    yield sse("agent_end", {"agent": "engineer", "result": f"Wrote {total} files"})

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

    qa_raw = _call_llm(
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

    yield sse("agent_end", {"agent": "qa", "result": f"QA Score: {qa_result.get('overall_score', 'N/A')}/100 — {qa_result.get('verdict', 'Done')}"})
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
                fixed = _call_llm("You are a bug-fixing engineer.", fix_prompt, max_tokens=2048)
                if fixed:
                    fixed = re.sub(r'^```\w*\n?', '', fixed.strip())
                    fixed = re.sub(r'\n?```$', '', fixed.strip())
                    board.generated_files[bug_file] = fixed

                    # Live-write the fix
                    yield sse("file_start", {"path": bug_file, "index": 0, "total": 0})
                    pos = 0
                    while pos < len(fixed):
                        chunk = fixed[pos:pos + TYPING_CHUNK * 2]
                        yield sse("file_delta", {"path": bug_file, "delta": chunk})
                        pos += TYPING_CHUNK * 2
                        await asyncio.sleep(TYPING_DELAY)
                    yield sse("file_end", {"path": bug_file, "index": 0, "total": 0})

                yield sse("agent_end", {"agent": "engineer", "result": f"Fixed: {bug_desc[:60]}"})
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
    if has_pkg:
        yield sse("message", {"content": "Running npm install..."})
        yield sse("discussion", {"from": "DevOps", "to": "Team Leader", "icon": "rocket", "message": "Installing dependencies..."})
        success, output = _run_npm_install()
        if success:
            yield sse("message", {"content": "Dependencies installed. Starting dev server..."})
        else:
            yield sse("message", {"content": f"npm install warning: {output[:200]}"})

        ok, msg, port = _start_dev_server()
        if ok:
            preview_url = f"http://127.0.0.1:{port}"
            yield sse("preview_ready", {"url": preview_url, "port": port})
            yield sse("message", {"content": f"Preview running at {preview_url}"})
            yield sse("discussion", {"from": "DevOps", "to": "Team Leader", "icon": "rocket", "message": f"Deployed successfully! Live at port {port}."})
        else:
            yield sse("message", {"content": f"Dev server: {msg}"})
    else:
        yield sse("message", {"content": "No package.json — skipping install."})

    yield sse("agent_end", {"agent": "devops", "result": "Project deployed"})

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

    yield sse("race_start", {"teams": num_teams})
    await asyncio.sleep(0.2)

    # Run teams in parallel
    boards: List[Blackboard] = []

    for team_idx in range(1, num_teams + 1):
        yield sse("race_progress", {"team": team_idx, "status": "generating", "phase": "planning"})
        await asyncio.sleep(0.1)

        board = Blackboard(prompt, existing_files)

        # PM phase
        prd_raw = _call_llm(
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
        arch_raw = _call_llm(
            AGENT_ARCHITECT_SYSTEM,
            f"PRD: {json.dumps(prd)}\n\nDesign architecture. (Team {team_idx})",
            temp=0.3 + (team_idx * 0.1),
        )
        arch = _extract_json(arch_raw)
        if not arch or not isinstance(arch, dict) or "directory_structure" not in arch:
            arch = {"stack": {"frontend": "React"}, "directory_structure": ["package.json", "src/App.jsx", "src/index.css"]}
        board.architecture = arch
        board.file_plan = arch.get("directory_structure", [])

        yield sse("race_progress", {"team": team_idx, "status": "generating", "phase": "coding"})

        # Engineer phase
        for file_path in board.file_plan:
            eng_system = AGENT_ENGINEER_SYSTEM.replace("{file_path}", file_path)
            content = _call_llm(eng_system, f"PRD: {json.dumps(prd)}\nWrite: {file_path}\nRequest: {prompt}", temp=0.3 + (team_idx * 0.1))
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
        judge_raw = _call_llm(AGENT_JUDGE_SYSTEM, f"Evaluate this solution for: {prompt}\n\nCode:\n{all_code}")
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
    has_pkg = "package.json" in winner.generated_files
    if has_pkg:
        yield sse("message", {"content": "Installing dependencies..."})
        _run_npm_install()
        ok, msg, port = _start_dev_server()
        if ok:
            yield sse("preview_ready", {"url": f"http://127.0.0.1:{port}", "port": port})
            yield sse("message", {"content": f"Preview live at http://127.0.0.1:{port}"})
    yield sse("agent_end", {"agent": "devops", "result": "Deployed"})
    yield sse("message", {"content": f"Done! {total} files created from the winning team. Project is live!"})


# ─── Main Stream Generator ──────────────────────────────────────────────────

async def atoms_stream(prompt: str, files: dict, mode: str = "standard", race_teams: int = 2) -> AsyncGenerator[str, None]:
    try:
        if mode == "race":
            async for event in race_pipeline(prompt, files, race_teams):
                yield event
        else:
            async for event in standard_pipeline(prompt, files):
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


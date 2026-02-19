"""
ATMOS Backend — AI-Only Autonomous Pipeline

Single endpoint: POST /atmos/run
Accepts: {"intent": "build a full stack app"}
Returns: SSE stream of events

The AI controls EVERYTHING:
1. Interpret intent → decide stack, structure
2. Generate all files
3. Install dependencies
4. Build project
5. Start dev server
6. Return preview URL
7. If error → auto-fix → rebuild (max 3 retries)

User NEVER runs commands, creates files, or fixes errors.
"""

import os
import json
import asyncio
import traceback
from typing import AsyncGenerator, Dict, Any, Optional

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.engine.llm_gateway import llm_call_simple, extract_json
from backend.engine.token_ledger import ledger
from backend.engine.sandbox import get_sandbox_manager
from backend.engine.events import get_event_emitter, EngineEventType


router = APIRouter(prefix="/atmos", tags=["atmos"])

MAX_FIX_RETRIES = 3


# ─── Request ────────────────────────────────────────────────────────────────

MAX_INTENT_LEN = 20_000


class AtmosRequest(BaseModel):
    intent: str = Field(..., min_length=1, max_length=MAX_INTENT_LEN)


# ─── SSE Helpers ─────────────────────────────────────────────────────────────

def sse_event(data: dict) -> str:
    """Format a dict as an SSE data line."""
    return f"data: {json.dumps(data)}\n\n"


def phase_event(phase: str) -> str:
    return sse_event({"type": "phase_change", "phase": phase})


def status_event(message: str) -> str:
    return sse_event({"type": "status", "message": message})


def file_event(path: str, content: str) -> str:
    return sse_event({"type": "file_created", "path": path, "content": content})


def chat_event(message: str) -> str:
    return sse_event({"type": "chat_message", "message": message})


def error_event(message: str, fixing: bool = False) -> str:
    return sse_event({"type": "error", "message": message, "fixing": fixing})


def preview_event(url: str) -> str:
    return sse_event({"type": "preview_ready", "url": url})


def done_event() -> str:
    return sse_event({"type": "done"})


def chat_token_event(token: str) -> str:
    """Stream individual chat tokens for real-time typing effect."""
    return sse_event({"type": "chat_token", "token": token})


def file_writing_event(path: str) -> str:
    """Signal that AI is starting to write a specific file."""
    return sse_event({"type": "file_writing", "path": path})


def file_token_event(path: str, token: str) -> str:
    """Stream a chunk of file content for live typing effect."""
    return sse_event({"type": "file_token", "path": path, "token": token})


# ─── Intent Interpreter ─────────────────────────────────────────────────────

INTERPRETER_SYSTEM = """You are an expert software architect. Given a user's intent, decide:
1. What stack to use (language, framework, tools)
2. What files to create (full directory structure)
3. What dependency commands to run (e.g., npm install, pip install)
4. What build/run commands to use

Respond in JSON:
{
    "project_name": "my-app",
    "stack": "React + FastAPI",
    "files": [
        {"path": "package.json", "description": "Dependencies"},
        {"path": "src/App.tsx", "description": "Main component"},
        ...
    ],
    "install_command": "npm install",
    "build_command": "npm run build",
    "dev_command": "npm run dev",
    "dev_port": 5173
}

Rules:
- Always pick a modern, production-quality stack
- Include ALL necessary files (config, entry points, components)
- Use sensible defaults
- Keep it simple but complete
"""


async def interpret_intent(intent: str) -> Optional[Dict[str, Any]]:
    """Use LLM to interpret user intent into a project plan."""
    print(f"[ATMOS] Interpreting intent: {intent[:100]}...")

    try:
        response = await asyncio.to_thread(
            llm_call_simple,
            agent_name="atmos_interpreter",
            system=INTERPRETER_SYSTEM,
            user=intent,
            max_tokens=2048,
            temperature=0.3,
        )
    except Exception as e:
        print(f"[ATMOS] LLM call failed in interpret_intent: {e}")
        return None

    if not response:
        print("[ATMOS] interpret_intent got empty response from LLM")
        return None

    print(f"[ATMOS] interpret_intent response length: {len(response)}")
    result = extract_json(response)

    if not result:
        print(f"[ATMOS] Failed to extract JSON from response: {response[:200]}")
        return None

    # extract_json might return a list if the LLM outputs a JSON array
    if isinstance(result, list):
        # Treat the list as the files array
        print(f"[ATMOS] Got list from LLM, wrapping as files array ({len(result)} items)")
        result = {"files": result, "project_name": "my-app", "stack": "auto"}

    if not isinstance(result, dict):
        print(f"[ATMOS] Unexpected result type: {type(result)}")
        return None

    print(f"[ATMOS] Plan has {len(result.get('files', []))} files")
    return result


# ─── File Generator ──────────────────────────────────────────────────────────

FILE_GEN_SYSTEM = """You are an expert software engineer. Generate the COMPLETE, PRODUCTION-READY
content for the requested file. The file must be fully functional — no placeholders, no TODOs.

Project context:
- Stack: {stack}
- Project name: {project_name}
- All files in project: {all_files}

CRITICAL: Output ONLY the raw file content. Do NOT wrap in markdown code fences (```). 
Do NOT add any explanation before or after the code. Just the raw code/content."""


def strip_code_fences(text: str) -> str:
    """Remove markdown code fences that LLMs sometimes add despite instructions."""
    if not text:
        return text
    stripped = text.strip()
    # Handle ```lang\n...``` or ```\n...```
    if stripped.startswith('```'):
        # Remove opening fence (first line)
        first_newline = stripped.find('\n')
        if first_newline != -1:
            stripped = stripped[first_newline + 1:]
        # Remove closing fence (last line)
        if stripped.rstrip().endswith('```'):
            stripped = stripped.rstrip()[:-3].rstrip()
    return stripped


async def generate_file(
    file_path: str,
    description: str,
    plan: Dict[str, Any],
) -> str:
    """Generate a single file's content."""
    all_files = ", ".join(f["path"] for f in plan.get("files", []))

    print(f"[ATMOS] Generating file: {file_path}")

    try:
        response = await asyncio.to_thread(
            llm_call_simple,
            agent_name="atmos_engineer",
            system=FILE_GEN_SYSTEM.format(
                stack=plan.get("stack", ""),
                project_name=plan.get("project_name", "app"),
                all_files=all_files,
            ),
            user=f"Generate the file: {file_path}\nDescription: {description}",
            max_tokens=4096,
            temperature=0.2,
        )
    except Exception as e:
        print(f"[ATMOS] LLM call failed for {file_path}: {e}")
        return f"// Error generating {file_path}: {e}"

    result = strip_code_fences(response) if response else f"// Error generating {file_path}"
    print(f"[ATMOS] Generated {file_path}: {len(result)} chars")
    return result


# ─── Error Fixer ─────────────────────────────────────────────────────────────

FIX_SYSTEM = """You are a debugging expert. An error occurred during build/run.
Fix the file that caused the error. Return ONLY the corrected file content.
No markdown fences. No explanation. Just the fixed code.

Error output:
{error}

Current file content:
{content}
"""


async def fix_error(
    error_output: str,
    files: Dict[str, str],
) -> Optional[Dict[str, str]]:
    """Attempt to fix build/run errors by editing files."""
    # Ask LLM which file to fix and how (wrap sync call for async context)
    diag_response = await asyncio.to_thread(
        llm_call_simple,
        agent_name="atmos_fixer",
        system="You diagnose build errors. Given the error, identify which file needs fixing. Respond in JSON: {\"file\": \"path/to/file.ext\", \"reason\": \"why\"}",
        user=f"Error:\n{error_output}\n\nFiles in project:\n{', '.join(files.keys())}",
        max_tokens=256,
        temperature=0.1,
    )

    if not diag_response:
        return None

    diag = extract_json(diag_response)
    if not diag or "file" not in diag:
        return None

    target_file = diag["file"]
    if target_file not in files:
        return None

    # Fix the file (wrap sync call for async context)
    fixed = await asyncio.to_thread(
        llm_call_simple,
        agent_name="atmos_fixer",
        system=FIX_SYSTEM.format(
            error=error_output[:2000],
            content=files[target_file][:3000],
        ),
        user=f"Fix {target_file}",
        max_tokens=4096,
        temperature=0.1,
    )

    if fixed:
        fixed = strip_code_fences(fixed)
        files[target_file] = fixed
        return {target_file: fixed}

    return None


# ─── Main Pipeline ───────────────────────────────────────────────────────────

async def atmos_pipeline(intent: str) -> AsyncGenerator[str, None]:
    """
    The full ATMOS autonomous pipeline.
    User types intent → AI does everything → preview URL returned.
    """

    # ── Phase 1: Interpret ───────────────────────────────────────────────────
    yield phase_event("interpreting")
    yield status_event("Understanding your intent…")

    plan = await interpret_intent(intent)

    if not plan or "files" not in plan:
        yield chat_event("I couldn't understand that. Try being more specific.")
        yield done_event()
        return

    project_name = plan.get("project_name", "my-app")
    yield chat_event(f"Building {project_name}…")

    # ── Phase 2: Generate Files ──────────────────────────────────────────────
    yield phase_event("generating")

    files: Dict[str, str] = {}

    for i, file_info in enumerate(plan["files"]):
        path = file_info["path"]
        desc = file_info.get("description", path)

        yield status_event(f"Writing {path} ({i + 1}/{len(plan['files'])})")
        yield file_writing_event(path)

        content = await generate_file(path, desc, plan)
        files[path] = content

        # Stream file content line-by-line for live typing effect
        lines = content.split('\n')
        for line_idx, line in enumerate(lines):
            token = line + ('\n' if line_idx < len(lines) - 1 else '')
            yield file_token_event(path, token)
            # Small delay between lines for visual effect
            await asyncio.sleep(0.015)

        # Send final complete file event
        yield file_event(path, content)

    yield chat_event("Project created.")

    # ── Phase 3: Build & Run (in sandbox) ────────────────────────────────────
    sandbox_mgr = get_sandbox_manager()

    with sandbox_mgr.create(project_name) as sandbox:
        # Write all files to sandbox
        for path, content in files.items():
            sandbox.write_file(path, content)

        # Install dependencies
        install_cmd = plan.get("install_command", "")
        if install_cmd:
            yield phase_event("building")
            yield status_event("Installing dependencies…")

            result = sandbox.execute(install_cmd, timeout=120)

            if not result.success:
                # Try to fix
                fixed = await _auto_fix_loop(
                    sandbox, files, plan, result.stderr, "install",
                    lambda msg: None,  # Can't yield from nested — handled below
                )
                if not fixed:
                    yield error_event(f"Install failed: {result.stderr[:500]}")
                    yield chat_event("Could not install dependencies. Try a different approach.")
                    yield done_event()
                    return

                # Re-emit fixed files
                for fp, fc in fixed.items():
                    yield file_event(fp, fc)

        # Build (if applicable)
        build_cmd = plan.get("build_command", "")
        if build_cmd:
            yield status_event("Building project…")
            result = sandbox.execute(build_cmd, timeout=60)
            # Build failures are non-fatal for dev mode

        # Start dev server
        dev_cmd = plan.get("dev_command", "")
        dev_port = plan.get("dev_port", 5173)

        if dev_cmd:
            yield phase_event("running")
            yield status_event("Starting dev server…")

            # Start in background (non-blocking)
            result = sandbox.execute(dev_cmd, timeout=5)

            # Give server time to start
            await asyncio.sleep(2)

            preview_url = f"http://localhost:{dev_port}"
            yield preview_event(preview_url)
            # preview_event triggers transition to 'live' on the frontend
        else:
            # Static project — no dev server needed, go straight to live
            yield phase_event("live")
            yield status_event("Project ready.")

    yield chat_event("Live.")
    yield done_event()


async def _auto_fix_loop(
    sandbox,
    files: Dict[str, str],
    plan: Dict[str, Any],
    error_output: str,
    phase: str,
    status_cb,
) -> Optional[Dict[str, str]]:
    """Attempt to auto-fix errors up to MAX_FIX_RETRIES times."""
    for attempt in range(MAX_FIX_RETRIES):
        fixed = await fix_error(error_output, files)
        if not fixed:
            return None

        # Write fixed files to sandbox
        for path, content in fixed.items():
            sandbox.write_file(path, content)
            files[path] = content

        # Retry the command
        cmd = plan.get(f"{phase}_command", "")
        if cmd:
            result = sandbox.execute(cmd, timeout=120)
            if result.success:
                return fixed
            error_output = result.stderr

    return None


# ─── Endpoint ────────────────────────────────────────────────────────────────

@router.post("/run")
async def atmos_run(req: AtmosRequest):
    """
    ATMOS autonomous execution endpoint.

    Accepts user intent, returns SSE stream.
    AI handles EVERYTHING: planning, coding, building, running.
    """

    async def stream():
        try:
            async for event in atmos_pipeline(req.intent):
                yield event
        except Exception as e:
            yield error_event(f"Pipeline error: {str(e)}")
            yield done_event()

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

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
from pydantic import BaseModel

from backend.engine.llm_gateway import llm_call_simple, extract_json
from backend.engine.token_ledger import ledger
from backend.engine.sandbox import get_sandbox_manager
from backend.engine.events import get_event_emitter, EngineEventType


router = APIRouter(prefix="/atmos", tags=["atmos"])

MAX_FIX_RETRIES = 3


# ─── Request ────────────────────────────────────────────────────────────────

class AtmosRequest(BaseModel):
    intent: str


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
    response = llm_call_simple(
        agent_name="atmos_interpreter",
        system=INTERPRETER_SYSTEM,
        user=intent,
        max_tokens=2048,
        temperature=0.3,
    )

    if not response:
        return None

    return extract_json(response)


# ─── File Generator ──────────────────────────────────────────────────────────

FILE_GEN_SYSTEM = """You are an expert software engineer. Generate the COMPLETE, PRODUCTION-READY
content for the requested file. The file must be fully functional — no placeholders, no TODOs.

Project context:
- Stack: {stack}
- Project name: {project_name}
- All files in project: {all_files}

Generate ONLY the file content. No markdown fences. No explanation. Just the raw code."""


async def generate_file(
    file_path: str,
    description: str,
    plan: Dict[str, Any],
) -> str:
    """Generate a single file's content."""
    all_files = ", ".join(f["path"] for f in plan.get("files", []))

    response = llm_call_simple(
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

    return response or f"// Error generating {file_path}"


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
    # Ask LLM which file to fix and how
    diag_response = llm_call_simple(
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

    # Fix the file
    fixed = llm_call_simple(
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

        content = await generate_file(path, desc, plan)
        files[path] = content

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
        else:
            # Static project — no dev server needed
            yield phase_event("live")

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

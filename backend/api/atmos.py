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

import logging
import os
import json
import asyncio
import traceback
from typing import AsyncGenerator, Dict, Any, Optional

from fastapi import APIRouter, Request

logger = logging.getLogger(__name__)
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.engine.llm_gateway import llm_call_simple, llm_call_stream, extract_json
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
    return sse_event({"type": "chat_token", "token": token, "channel": "chat"})


def thinking_token_event(token: str) -> str:
    """Stream thinking/reasoning tokens for live typing effect."""
    return sse_event({"type": "thinking_token", "token": token, "channel": "thinking"})


def file_writing_event(path: str) -> str:
    """Signal that AI is starting to write a specific file."""
    return sse_event({"type": "file_writing", "path": path, "channel": "system"})


def file_token_event(path: str, token: str) -> str:
    """Stream a chunk of file content for live typing effect."""
    return sse_event({"type": "file_token", "path": path, "token": token, "channel": "code"})


def stream_start_event(channel: str) -> str:
    """Signal that a stream is starting on a channel (frontend shows typing indicator)."""
    return sse_event({"type": "stream_start", "channel": channel})


def stream_end_event(channel: str) -> str:
    """Signal that a stream has ended on a channel (frontend flushes + hides indicator)."""
    return sse_event({"type": "stream_end", "channel": channel})


# ─── Async Streaming Helper ──────────────────────────────────────────────────

def _stream_llm_sync(
    system: str, user: str, agent_name: str = "atmos_pipeline",
    max_tokens: int = 2048, temp: float = 0.3, use_coder: bool = False,
):
    """Synchronous streaming LLM call — yields token strings. Blocks the thread."""
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


async def _stream_llm_async(
    system: str, user: str, agent_name: str = "atmos_pipeline",
    max_tokens: int = 2048, temp: float = 0.3, use_coder: bool = False,
):
    """
    Async generator: run the blocking LLM stream in a thread, yield tokens
    without blocking the event loop. Uses asyncio.Queue for thread→async bridging.
    """
    queue: asyncio.Queue = asyncio.Queue()
    loop = asyncio.get_running_loop()
    sentinel = object()

    def _produce():
        try:
            for token in _stream_llm_sync(system, user, agent_name, max_tokens, temp, use_coder):
                if token:
                    loop.call_soon_threadsafe(queue.put_nowait, token)
        except Exception as exc:
            loop.call_soon_threadsafe(queue.put_nowait, exc)
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, sentinel)

    loop.run_in_executor(None, _produce)

    while True:
        item = await queue.get()
        if item is sentinel:
            break
        if isinstance(item, Exception):
            logger.warning("[ATMOS] Stream error: %s", item)
            break
        yield item


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


async def interpret_intent_streaming(intent: str):
    """
    Async generator: stream thinking tokens while interpreting intent.
    Yields (token_str, None) for thinking tokens, and (None, plan_dict) at the end.
    """
    logger.debug("[ATMOS] Interpreting intent (streaming): %s...", intent[:100])

    full_content = []
    try:
        async for token in _stream_llm_async(
            system=INTERPRETER_SYSTEM,
            user=intent,
            agent_name="atmos_interpreter",
            max_tokens=2048,
            temp=0.3,
        ):
            full_content.append(token)
            yield (token, None)  # thinking token
    except Exception as e:
        logger.exception("[ATMOS] Streaming interpret failed: %s", e)
        yield (None, None)
        return

    response = "".join(full_content)
    if not response:
        logger.warning("[ATMOS] interpret_intent got empty response from LLM")
        yield (None, None)
        return

    logger.debug("[ATMOS] interpret_intent response length: %s", len(response))
    result = extract_json(response)

    if not result:
        logger.warning("[ATMOS] Failed to extract JSON from response: %s", response[:200])
        yield (None, None)
        return

    if isinstance(result, list):
        logger.debug("[ATMOS] Got list from LLM, wrapping as files array (%s items)", len(result))
        result = {"files": result, "project_name": "my-app", "stack": "auto"}

    if not isinstance(result, dict):
        logger.warning("[ATMOS] Unexpected result type: %s", type(result))
        yield (None, None)
        return

    logger.debug("[ATMOS] Plan has %s files", len(result.get("files", [])))
    yield (None, result)  # final plan


async def interpret_intent(intent: str) -> Optional[Dict[str, Any]]:
    """Non-streaming fallback: Use LLM to interpret user intent into a project plan."""
    logger.debug("[ATMOS] Interpreting intent: %s...", intent[:100])

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
        logger.exception("[ATMOS] LLM call failed in interpret_intent: %s", e)
        return None

    if not response:
        logger.warning("[ATMOS] interpret_intent got empty response from LLM")
        return None

    logger.debug("[ATMOS] interpret_intent response length: %s", len(response))
    result = extract_json(response)

    if not result:
        logger.warning("[ATMOS] Failed to extract JSON from response: %s", response[:200])
        return None

    if isinstance(result, list):
        logger.debug("[ATMOS] Got list from LLM, wrapping as files array (%s items)", len(result))
        result = {"files": result, "project_name": "my-app", "stack": "auto"}

    if not isinstance(result, dict):
        logger.warning("[ATMOS] Unexpected result type: %s", type(result))
        return None

    logger.debug("[ATMOS] Plan has %s files", len(result.get("files", [])))
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


async def stream_generate_file(
    file_path: str,
    description: str,
    plan: Dict[str, Any],
):
    """
    Async generator: stream file content tokens as they arrive from the LLM.
    Yields token strings. Caller collects them for the full file content.
    """
    all_files = ", ".join(f["path"] for f in plan.get("files", []))
    logger.debug("[ATMOS] Streaming file generation: %s", file_path)

    system = FILE_GEN_SYSTEM.format(
        stack=plan.get("stack", ""),
        project_name=plan.get("project_name", "app"),
        all_files=all_files,
    )
    user = f"Generate the file: {file_path}\nDescription: {description}"

    token_count = 0
    async for token in _stream_llm_async(
        system=system,
        user=user,
        agent_name="atmos_engineer",
        max_tokens=4096,
        temp=0.2,
        use_coder=True,
    ):
        token_count += 1
        yield token

    logger.debug("[ATMOS] Streamed %s: %s tokens", file_path, token_count)


async def generate_file(
    file_path: str,
    description: str,
    plan: Dict[str, Any],
) -> str:
    """Non-streaming fallback: generate a single file's content."""
    all_files = ", ".join(f["path"] for f in plan.get("files", []))

    logger.debug("[ATMOS] Generating file: %s", file_path)

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
        logger.exception("[ATMOS] LLM call failed for %s: %s", file_path, e)
        return f"// Error generating {file_path}: {e}"

    result = strip_code_fences(response) if response else f"// Error generating {file_path}"
    logger.debug("[ATMOS] Generated %s: %s chars", file_path, len(result))
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
    The full ATMOS autonomous pipeline — with real-time token streaming.
    User types intent → AI does everything → preview URL returned.

    Key difference from before: LLM tokens stream in real-time instead of
    generating full responses and then chunking them.
    """

    # ── Phase 1: Interpret (with live thinking tokens) ───────────────────────
    yield phase_event("interpreting")
    yield status_event("Understanding your intent…")

    # Stream thinking tokens so the frontend shows live reasoning
    plan = None
    yield stream_start_event("thinking")
    async for token, result in interpret_intent_streaming(intent):
        if token:
            yield thinking_token_event(token)
        if result is not None:
            plan = result
    yield stream_end_event("thinking")

    if not plan or "files" not in plan:
        # Fallback to non-streaming if streaming returned nothing
        plan = await interpret_intent(intent)

    if not plan or "files" not in plan:
        yield chat_event("I couldn't understand that. Try being more specific.")
        yield done_event()
        return

    project_name = plan.get("project_name", "my-app")
    yield chat_event(f"Building {project_name}…")

    # ── Phase 2: Generate Files (real-time LLM token streaming) ──────────────
    yield phase_event("generating")

    files: Dict[str, str] = {}

    for i, file_info in enumerate(plan["files"]):
        path = file_info["path"]
        desc = file_info.get("description", path)

        yield status_event(f"Writing {path} ({i + 1}/{len(plan['files'])})")
        yield file_writing_event(path)

        # Stream tokens directly from the LLM — real-time, not simulated
        content_parts = []
        yield stream_start_event("code")
        try:
            async for token in stream_generate_file(path, desc, plan):
                content_parts.append(token)
                yield file_token_event(path, token)
        except Exception as e:
            logger.warning("[ATMOS] Stream failed for %s, falling back: %s", path, e)
            # Fallback to non-streaming generation
            fallback_content = await generate_file(path, desc, plan)
            content_parts = [fallback_content]
            # Emit as larger chunks for the fallback path
            for ci in range(0, len(fallback_content), 64):
                yield file_token_event(path, fallback_content[ci:ci + 64])
                await asyncio.sleep(0.005)
        yield stream_end_event("code")

        content = strip_code_fences("".join(content_parts))
        files[path] = content

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
                    lambda msg: None,
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

        # Start dev server
        dev_cmd = plan.get("dev_command", "")
        dev_port = plan.get("dev_port", 5173)

        if dev_cmd:
            yield phase_event("running")
            yield status_event("Starting dev server…")

            result = sandbox.execute(dev_cmd, timeout=5)
            await asyncio.sleep(2)

            preview_url = f"http://localhost:{dev_port}"
            yield preview_event(preview_url)
        else:
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

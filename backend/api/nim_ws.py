"""
NIM WebSocket Streaming — Phase 4

Endpoint:  /ws/nim/{session_id}

Flow:
  1. Client connects → receives {"type": "connected", "session_id": "..."}
  2. Client sends   → {"type": "start", "prompt": "Build a blog API"}
  3. Server runs TEAM_LEAD → sends dag_ready event
  4. Server dispatches tasks → each agent generates silently, then streams
     files into the editor and streams the human-readable summary to chat
  5. All complete → writes files to disk, attempts preview, sends dag_complete

Typed event schema (all events are JSON):
  {"agent": "team_lead",       "task_id": "t0",  "type": "agent_start",      "content": ""}
  {"agent": "backend_engineer","task_id": "t2",  "type": "token",            "content": "Built the API…"}
  {"agent": "backend_engineer","task_id": "t2",  "type": "file_writing",     "path": "backend/main.py",  "content": "backend/main.py"}
  {"agent": "backend_engineer","task_id": "t2",  "type": "file_delta",       "path": "backend/main.py",  "content": "from fastapi"}
  {"agent": "backend_engineer","task_id": "t2",  "type": "file_complete",    "path": "backend/main.py",  "content": "...full content..."}
  {"agent": "team_lead",       "task_id": "t2",  "type": "agent_discussion", "from": "Team Leader",  "to": "Backend Engineer", "icon": "crown", "content": "Starting on: ..."}
  {"agent": "backend_engineer","task_id": "t2",  "type": "agent_complete",   "content": ""}
  {"agent": "backend_engineer","task_id": "t2",  "type": "task_error",       "content": "timeout after 3 retries"}
  {"agent": "",                "task_id": "",    "type": "dag_complete",     "content": ""}
  {"agent": "",                "task_id": "",    "type": "dag_ready",        "content": "<dag json string>"}
  {"agent": "",                "task_id": "",    "type": "preview_ready",    "content": "http://localhost:5174"}

Session isolation: each session_id has its own queue. Agents push events; the
sender coroutine drains the queue to the WebSocket. Reconnecting clients receive
the last N buffered events.
"""

from __future__ import annotations

import asyncio
import json
import logging
import socket
import uuid
from collections import deque
from pathlib import Path
from typing import Any, Deque, Dict, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.agents.nim_agents import (
    TeamLeadAgent,
    QAEngineerAgent,
    get_agent,
)
from backend.engine.dag_executor import DAGParser, DAGTask, TaskDispatcher, TaskStatus
from backend.engine.nim_client import get_nim_client
from backend.engine.model_config import get_model_for_role, get_profile

logger = logging.getLogger("nim_ws")

router = APIRouter(prefix="/ws/nim", tags=["nim-websocket"])

# Root for writing generated project files to disk
GENERATED_ROOT = Path(__file__).resolve().parent.parent.parent / "generated_projects"

# ── Streaming Bus ──────────────────────────────────────────────────────────────

_EVENT_BUFFER_SIZE = 200  # max buffered events per session for reconnect support


class SessionBus:
    """
    Per-session event queue.

    Agents push events; the WebSocket sender task drains the queue.
    A bounded deque holds recent events so reconnecting clients don't miss history.
    """

    def __init__(self) -> None:
        self._queue: asyncio.Queue[Optional[dict]] = asyncio.Queue()
        self._history: Deque[dict] = deque(maxlen=_EVENT_BUFFER_SIZE)
        self._closed = False

    async def push(self, event: dict) -> None:
        """Push an event. No-op if the session is already closed."""
        if self._closed:
            return
        self._history.append(event)
        await self._queue.put(event)

    async def get(self) -> Optional[dict]:
        """Block until next event. Returns None when the session is closed."""
        return await self._queue.get()

    def close(self) -> None:
        """Signal the sender coroutine to stop."""
        self._closed = True
        self._queue.put_nowait(None)  # sentinel

    def replay_events(self) -> list[dict]:
        """Return all buffered events for a reconnecting client."""
        return list(self._history)


class StreamingBus:
    """Registry of all active SessionBus objects, keyed by session_id."""

    def __init__(self) -> None:
        self._sessions: Dict[str, SessionBus] = {}

    def create(self, session_id: str) -> SessionBus:
        bus = SessionBus()
        self._sessions[session_id] = bus
        return bus

    def get(self, session_id: str) -> Optional[SessionBus]:
        return self._sessions.get(session_id)

    def remove(self, session_id: str) -> None:
        bus = self._sessions.pop(session_id, None)
        if bus:
            bus.close()

    def active_sessions(self) -> list[str]:
        return list(self._sessions.keys())


_bus = StreamingBus()


# ── Helpers ────────────────────────────────────────────────────────────────────

def _event(
    event_type: str,
    agent: str = "",
    task_id: str = "",
    content: str = "",
    **extra: Any,
) -> dict:
    """Build a typed event dict. Extra kwargs (e.g. path, from, to, icon) are merged in."""
    evt = {
        "type":    event_type,
        "agent":   agent,
        "task_id": task_id,
        "content": content,
    }
    evt.update(extra)
    return evt


# ── Preview Generation ─────────────────────────────────────────────────────────

def _find_free_port(start: int = 5174, end: int = 5200) -> Optional[int]:
    """Return the first available TCP port in [start, end), or None if all taken."""
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return None


async def _generate_preview(
    session_id: str,
    files: Dict[str, str],
    bus: SessionBus,
) -> None:
    """
    Write generated project files to disk, then attempt npm install + npm run dev.
    Emits preview_ready on success. All errors are logged and swallowed.
    """
    root = GENERATED_ROOT / session_id
    root.mkdir(parents=True, exist_ok=True)

    # Write every file to disk
    written = 0
    for rel_path, content in files.items():
        target = root / rel_path
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            written += 1
        except Exception as exc:
            logger.warning("[Preview] Could not write %s: %s", rel_path, exc)

    logger.info("[Preview] Wrote %d/%d files to %s", written, len(files), root)

    # Locate a frontend package.json
    frontend_dir: Optional[Path] = None
    for candidate in [root / "frontend", root]:
        if (candidate / "package.json").exists():
            frontend_dir = candidate
            break

    if not frontend_dir:
        logger.info("[Preview] No package.json found — skipping dev server")
        bus.close()
        return

    port = _find_free_port()
    if port is None:
        logger.warning("[Preview] No free port found in range 5174-5200")
        bus.close()
        return

    try:
        # npm install
        install_proc = await asyncio.create_subprocess_exec(
            "npm", "install",
            cwd=str(frontend_dir),
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            _, stderr_bytes = await asyncio.wait_for(install_proc.communicate(), timeout=120)
        except asyncio.TimeoutError:
            logger.warning("[Preview] npm install timed out")
            bus.close()
            return

        if install_proc.returncode != 0:
            logger.warning("[Preview] npm install failed: %s",
                           stderr_bytes.decode(errors="replace")[:400])
            bus.close()
            return

        # npm run dev — fire and forget, no await
        await asyncio.create_subprocess_exec(
            "npm", "run", "dev", "--", f"--port={port}", "--host",
            cwd=str(frontend_dir),
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )

        # Give Vite a moment to bind the port
        await asyncio.sleep(4)

        preview_url = f"http://localhost:{port}"
        await bus.push(_event("preview_ready", content=preview_url))
        logger.info("[Preview] Dev server at %s", preview_url)

    except Exception as exc:
        logger.error("[Preview] Failed to start preview server: %s", exc)
    finally:
        bus.close()


# ── DAG Runner ─────────────────────────────────────────────────────────────────

async def _run_dag(
    session_id: str,
    bus: SessionBus,
    prompt: str,
    db_session: Any = None,
) -> None:
    """
    Orchestrate the full DAG pipeline for one user request.
    Streams all events to the SessionBus.
    """
    nim = get_nim_client()
    context: Dict[str, str] = {}

    # ── Step 1: TEAM_LEAD generates the DAG ───────────────────────────────────
    tl_model = get_model_for_role("team_lead")
    await bus.push(_event("agent_start", agent="team_lead", task_id="dag", model=tl_model))
    try:
        team_lead = TeamLeadAgent(client=nim)
        dag_json = await team_lead.generate_dag(prompt)
    except Exception as exc:
        logger.error("[NIM-WS] TEAM_LEAD failed: %s", exc)
        await bus.push(_event("task_error", agent="team_lead", task_id="dag", content=str(exc)))
        await bus.push(_event("dag_complete"))
        bus.close()
        return

    await bus.push(_event("agent_complete", agent="team_lead", task_id="dag"))
    await bus.push(_event("dag_ready", content=json.dumps(dag_json)))

    # ── Step 2: Parse DAG ─────────────────────────────────────────────────────
    try:
        tasks = DAGParser.parse(dag_json)
    except ValueError as exc:
        logger.error("[NIM-WS] DAG parse failed: %s", exc)
        await bus.push(_event("task_error", task_id="dag", content=f"DAG validation error: {exc}"))
        await bus.push(_event("dag_complete"))
        bus.close()
        return

    # ── Step 3: Dispatch tasks ────────────────────────────────────────────────
    # max_workers=3 enables parallel agent execution (e.g. backend + frontend simultaneously)
    dispatcher = TaskDispatcher(tasks, max_workers=3, max_retries=3)

    async def task_event_callback(task: DAGTask) -> None:
        event_type = {
            TaskStatus.RUNNING:  "agent_start",
            TaskStatus.COMPLETE: "agent_complete",
            TaskStatus.FAILED:   "task_error",
            TaskStatus.BLOCKED:  "task_error",
        }.get(task.status, "token")
        extra = {}
        if event_type == "agent_start":
            extra["model"] = get_model_for_role(task.role)
        await bus.push(
            _event(
                event_type,
                agent=task.role,
                task_id=task.id,
                content=task.error or "",
                **extra,
            )
        )

    async def execute_task(task: DAGTask, ctx: Dict[str, str]) -> str:
        """
        Execute one task:
          1. Emit a discussion message from Team Leader assigning the task.
          2. Stream a short "thinking" narrative from NIM API concurrently
             while code is generated — users see text immediately.
          3. Generate code via non-streaming complete_json() / validate().
          4. Stream each generated file into the editor (file_writing / file_delta / file_complete).
          5. Stream the human-readable summary to the chat speech bubble as token events.
          6. Emit an agent_discussion completion message back to the team.

        Returns the full JSON string (stored in context for subsequent agents).
        """
        agent = get_agent(task.role, client=nim)

        # ── Emit task assignment discussion ───────────────────────────────────
        brief = task.description[:200].rstrip()
        if len(task.description) > 200:
            brief += "…"
        agent_display = task.role.replace("_", " ").title()
        await bus.push(_event(
            "agent_discussion",
            agent="team_lead",
            task_id=task.id,
            content=f"Starting on: {brief}",
            **{"from": "Team Leader", "to": agent_display, "icon": "crown"},
        ))

        # ── Fast status message (no extra LLM call) ─────────────────────────
        # Instead of streaming a "thinking" narrative via a separate LLM call,
        # emit a single instant status token — saves ~5s per agent.
        status_msg = f"Generating {agent_display.lower()} code…"
        await bus.push(_event(
            "token", agent=task.role, task_id=task.id, content=status_msg,
        ))

        # ── Generate code ─────────────────────────────────────────────────────
        if isinstance(agent, QAEngineerAgent):
            result_json = await agent.validate(task, ctx)
        else:
            result_json = await agent.execute(task, ctx)

        # ── Parse result ──────────────────────────────────────────────────────
        try:
            result: dict = json.loads(result_json)
        except (json.JSONDecodeError, TypeError):
            result = {}

        files: Dict[str, str] = result.get("files", {})
        summary: str = result.get("summary", "")

        # ── Stream files to the editor ────────────────────────────────────────
        CHUNK_SIZE = 500   # chars per delta event — maximum speed
        for file_path, file_content in files.items():
            # Signal that we're starting this file
            await bus.push(_event(
                "file_writing",
                agent=task.role,
                task_id=task.id,
                path=file_path,
                content=file_path,
            ))
            # Stream content in chunks for typewriter effect
            for i in range(0, len(file_content), CHUNK_SIZE):
                chunk = file_content[i:i + CHUNK_SIZE]
                await bus.push(_event(
                    "file_delta",
                    agent=task.role,
                    task_id=task.id,
                    path=file_path,
                    content=chunk,
                ))
                await asyncio.sleep(0)  # yield to event loop, zero delay
            # Signal file is complete (with full content for IDE to finalize)
            await bus.push(_event(
                "file_complete",
                agent=task.role,
                task_id=task.id,
                path=file_path,
                content=file_content,
            ))

        # ── Build summary text for QA if not present ──────────────────────────
        if not summary and isinstance(agent, QAEngineerAgent):
            passed = result.get("passed", False)
            score = result.get("score", 0)
            issues = result.get("issues", [])
            verdict = "✓ PASSED" if passed else "✗ FAILED"
            summary = f"{verdict} — Score: {score}/100."
            if issues:
                top = issues[:3]
                details = "; ".join(
                    f"{i.get('severity', 'info')}: {i.get('description', '')[:60]}"
                    for i in top
                )
                summary += f" Issues: {details}"

        # ── Stream summary text to the chat speech bubble ─────────────────────
        # Only stream summary if it adds new info beyond what was shown in thinking
        if summary:
            TOKEN_CHUNK = 20  # chars per token event — fast summary
            for i in range(0, len(summary), TOKEN_CHUNK):
                await bus.push(_event(
                    "token",
                    agent=task.role,
                    task_id=task.id,
                    content=summary[i:i + TOKEN_CHUNK],
                ))
                await asyncio.sleep(0)  # yield to event loop, zero delay

        # ── Completion discussion ─────────────────────────────────────────────
        if files:
            done_msg = f"Done — {len(files)} file(s) written."
        elif isinstance(agent, QAEngineerAgent):
            done_msg = "Validation complete."
        else:
            done_msg = "Task complete."

        await bus.push(_event(
            "agent_discussion",
            agent=task.role,
            task_id=task.id,
            content=done_msg,
            **{"from": agent_display, "to": "Team Leader", "icon": "check-circle"},
        ))

        return result_json

    try:
        await dispatcher.run(
            executor=execute_task,
            on_event=task_event_callback,
            context=context,
        )
    except Exception as exc:
        logger.error("[NIM-WS] DAG execution error: %s", exc)
        await bus.push(_event("task_error", content=f"Execution error: {exc}"))

    # ── Step 4: Collect files and attempt preview ─────────────────────────────
    all_files: Dict[str, str] = {}
    for task in tasks:
        if task.output and task.status == TaskStatus.COMPLETE:
            try:
                out = json.loads(task.output)
                if isinstance(out, dict) and "files" in out:
                    all_files.update(out["files"])
            except Exception as e:
                logger.warning("[NIM-WS] Failed to parse task output for files: %s", e)

    await bus.push(_event("dag_complete"))

    if all_files:
        # Preview runs in background — bus stays open so preview_ready can be sent.
        # _generate_preview closes the bus when done.
        asyncio.create_task(_generate_preview(session_id, all_files, bus))
    else:
        # No files to preview — close bus immediately
        bus.close()


# ── WebSocket Endpoint ─────────────────────────────────────────────────────────

@router.websocket("/{session_id}")
async def nim_websocket(websocket: WebSocket, session_id: str) -> None:
    """
    WebSocket endpoint for NIM multi-agent streaming.

    Protocol (client → server):
      {"type": "start", "prompt": "<user requirement>"}

    Protocol (server → client):
      <typed event JSON objects — see module docstring>
    """
    await websocket.accept()
    logger.info("[NIM-WS] Client connected: session=%s", session_id)

    # Create session bus
    bus = _bus.create(session_id)

    # Send connected confirmation
    await websocket.send_json({"type": "connected", "session_id": session_id})

    # Sender coroutine: drains bus → WebSocket
    async def sender() -> None:
        while True:
            event = await bus.get()
            if event is None:
                break
            try:
                await websocket.send_json(event)
            except Exception as e:
                logger.debug("[NIM-WS] Sender stopped: %s", e)
                break

    sender_task = asyncio.create_task(sender())

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json(
                    {"type": "error", "content": "Invalid JSON message."}
                )
                continue

            msg_type = msg.get("type", "")

            if msg_type == "start":
                prompt = msg.get("prompt", "").strip()
                if not prompt:
                    await websocket.send_json(
                        {"type": "error", "content": "Missing 'prompt' field."}
                    )
                    continue
                logger.info("[NIM-WS] session=%s START prompt=%r", session_id, prompt[:80])
                asyncio.create_task(_run_dag(session_id, bus, prompt))

            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})

            else:
                await websocket.send_json(
                    {"type": "error", "content": f"Unknown message type: {msg_type!r}"}
                )

    except WebSocketDisconnect:
        logger.info("[NIM-WS] Client disconnected: session=%s", session_id)
    finally:
        bus.close()
        sender_task.cancel()
        _bus.remove(session_id)
        logger.info("[NIM-WS] Session cleaned up: %s", session_id)

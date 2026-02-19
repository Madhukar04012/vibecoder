"""
Terminal WebSocket — Phase 2

WebSocket endpoint for real-time terminal interaction.
Connects xterm.js frontend to PTY shell sessions.

Endpoints:
- GET /ws/terminal/{session_id} — WebSocket connection
- POST /api/terminal/create — Create new session
- DELETE /api/terminal/{session_id} — Close session

Usage:
    1. Create session: POST /api/terminal/create
    2. Connect WebSocket: ws://localhost:8000/ws/terminal/{session_id}
    3. Send/receive data over WebSocket
    4. Close session: DELETE /api/terminal/{session_id}
"""

import asyncio
from typing import Dict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel

from backend.tools.shell_executor import get_shell_manager, ShellSessionManager


router = APIRouter(tags=["terminal"])


# ─── REST Endpoints ──────────────────────────────────────────────────────────

class CreateSessionRequest(BaseModel):
    cwd: str = ""


class CreateSessionResponse(BaseModel):
    session_id: str
    success: bool


class SessionStatusResponse(BaseModel):
    session_id: str
    is_active: bool
    output: str


@router.post("/api/terminal/create", response_model=CreateSessionResponse)
def create_terminal_session(body: CreateSessionRequest):
    """Create a new terminal session."""
    manager = get_shell_manager()
    
    cwd = body.cwd if body.cwd else None
    session_id = manager.create_session(cwd=cwd)
    
    return CreateSessionResponse(session_id=session_id, success=True)


@router.delete("/api/terminal/{session_id}")
def close_terminal_session(session_id: str):
    """Close a terminal session."""
    manager = get_shell_manager()
    
    if not manager.get_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    manager.close_session(session_id)
    return {"success": True}


@router.get("/api/terminal/{session_id}/status", response_model=SessionStatusResponse)
def get_session_status(session_id: str):
    """Get terminal session status and buffered output."""
    manager = get_shell_manager()
    session = manager.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionStatusResponse(
        session_id=session_id,
        is_active=session.is_active,
        output=manager.get_output(session_id),
    )


# ─── WebSocket Endpoint ──────────────────────────────────────────────────────

# Track active WebSocket connections
_active_connections: Dict[str, WebSocket] = {}


@router.websocket("/ws/terminal/{session_id}")
async def terminal_websocket(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for terminal interaction.
    
    Bidirectional streaming:
    - Client sends: command input
    - Server sends: command output
    """
    manager = get_shell_manager()
    session = manager.get_session(session_id)
    
    if not session:
        await websocket.close(code=4004, reason="Session not found")
        return
    
    await websocket.accept()
    _active_connections[session_id] = websocket
    
    # Register output callback for streaming
    async def output_callback(data: str):
        try:
            await websocket.send_text(data)
        except Exception:
            pass
    
    manager.register_output_callback(session_id, output_callback)
    
    try:
        # Send initial prompt
        await websocket.send_text("$ ")
        
        while True:
            # Receive command from client
            data = await websocket.receive_text()
            
            if not data.strip():
                await websocket.send_text("$ ")
                continue
            
            # Execute command
            result = await manager.execute(session_id, data.strip())
            
            # Send output
            if result["stdout"]:
                await websocket.send_text(result["stdout"])
            if result["stderr"]:
                await websocket.send_text(f"\033[31m{result['stderr']}\033[0m")  # Red for stderr
            
            # Send prompt for next command
            await websocket.send_text("\n$ ")
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_text(f"\033[31mError: {e}\033[0m\n")
        except Exception:
            pass
    finally:
        # Cleanup
        _active_connections.pop(session_id, None)
        manager.close_session(session_id)


# ─── Execute Single Command ──────────────────────────────────────────────────

class ExecuteRequest(BaseModel):
    session_id: str
    command: str


class ExecuteResponse(BaseModel):
    stdout: str
    stderr: str
    exit_code: int


@router.post("/api/terminal/execute", response_model=ExecuteResponse)
async def execute_command(body: ExecuteRequest):
    """Execute a single command in a session (non-WebSocket)."""
    manager = get_shell_manager()
    session = manager.get_session(body.session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    result = await manager.execute(body.session_id, body.command)
    
    return ExecuteResponse(
        stdout=result["stdout"],
        stderr=result["stderr"],
        exit_code=result["exit_code"],
    )

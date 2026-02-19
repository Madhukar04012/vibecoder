"""
Shell Executor — Phase 2

Cross-platform shell session manager for real terminal experience.
- Windows: subprocess with pipes
- Linux/Mac: PTY for true terminal behavior

Each session is isolated. Fresh session per run.

Usage:
    manager = ShellSessionManager()
    session_id = manager.create_session(cwd="/path/to/project")
    output = await manager.execute(session_id, "echo hello")
    manager.close_session(session_id)
"""

import asyncio
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Optional, Dict, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime

# Platform detection
IS_WINDOWS = sys.platform == "win32"

# Try to import PTY for Unix systems
if not IS_WINDOWS:
    try:
        import pty
        import os
        import select
        HAS_PTY = True
    except ImportError:
        HAS_PTY = False
else:
    HAS_PTY = False


@dataclass
class ShellSession:
    """Represents an active shell session."""
    id: str
    cwd: str
    created_at: datetime = field(default_factory=datetime.now)
    process: Optional[subprocess.Popen] = None
    pty_fd: Optional[int] = None
    pty_pid: Optional[int] = None
    output_buffer: str = ""
    is_active: bool = True


class ShellSessionManager:
    """
    Manages multiple shell sessions.
    
    Thread-safe session creation and management.
    Each session runs in isolation.
    """
    
    def __init__(self, default_cwd: Optional[str] = None):
        """
        Initialize the session manager.
        
        Args:
            default_cwd: Default working directory for new sessions
        """
        self.sessions: Dict[str, ShellSession] = {}
        self.default_cwd = default_cwd or str(Path.cwd())
        self._output_callbacks: Dict[str, Callable[[str], Awaitable[None]]] = {}
    
    def create_session(self, cwd: Optional[str] = None) -> str:
        """
        Create a new isolated shell session.
        
        Args:
            cwd: Working directory for the session
            
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        session_cwd = cwd or self.default_cwd
        
        # Ensure directory exists
        Path(session_cwd).mkdir(parents=True, exist_ok=True)
        
        session = ShellSession(
            id=session_id,
            cwd=session_cwd,
        )
        
        self.sessions[session_id] = session
        return session_id
    
    def get_session(self, session_id: str) -> Optional[ShellSession]:
        """Get a session by ID."""
        return self.sessions.get(session_id)
    
    def register_output_callback(
        self, 
        session_id: str, 
        callback: Callable[[str], Awaitable[None]]
    ) -> None:
        """Register a callback for session output (for WebSocket streaming)."""
        self._output_callbacks[session_id] = callback
    
    async def execute(
        self, 
        session_id: str, 
        command: str,
        timeout: float = 30.0
    ) -> Dict[str, any]:
        """
        Execute a command in a session.
        
        Args:
            session_id: Session to execute in
            command: Command to run
            timeout: Maximum execution time in seconds
            
        Returns:
            Dict with stdout, stderr, exit_code
        """
        session = self.sessions.get(session_id)
        if not session:
            return {
                "stdout": "",
                "stderr": f"Session {session_id} not found",
                "exit_code": 1,
            }
        
        if not session.is_active:
            return {
                "stdout": "",
                "stderr": "Session is closed",
                "exit_code": 1,
            }
        
        # Use subprocess for cross-platform compatibility
        return await self._execute_subprocess(session, command, timeout)
    
    async def _cleanup_previous_process(self, session: ShellSession) -> None:
        """Clean up any previously running process in the session."""
        if session.process is not None:
            try:
                if session.process.returncode is None:
                    # Process is still running, terminate it
                    session.process.terminate()
                    try:
                        await asyncio.wait_for(session.process.wait(), timeout=2.0)
                    except asyncio.TimeoutError:
                        # Force kill if graceful termination fails
                        session.process.kill()
                        await session.process.wait()
            except Exception:
                # Ignore errors during cleanup
                pass
            finally:
                session.process = None
    
    async def _execute_subprocess(
        self, 
        session: ShellSession, 
        command: str,
        timeout: float
    ) -> Dict[str, any]:
        """Execute command using subprocess (cross-platform)."""
        try:
            # Clean up any previous process to prevent resource leaks
            await self._cleanup_previous_process(session)
            
            # Determine shell based on platform
            if IS_WINDOWS:
                shell_cmd = ["cmd", "/c", command]
            else:
                shell_cmd = ["bash", "-c", command]
            
            process = await asyncio.create_subprocess_exec(
                *shell_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=session.cwd,
            )
            
            session.process = process
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
                
                stdout_str = stdout.decode("utf-8", errors="replace")
                stderr_str = stderr.decode("utf-8", errors="replace")
                
                # Stream output if callback registered
                callback = self._output_callbacks.get(session.id)
                if callback:
                    if stdout_str:
                        await callback(stdout_str)
                    if stderr_str:
                        await callback(stderr_str)
                
                # Buffer output
                session.output_buffer += stdout_str + stderr_str
                
                return {
                    "stdout": stdout_str,
                    "stderr": stderr_str,
                    "exit_code": process.returncode or 0,
                }
                
            except asyncio.TimeoutError:
                process.kill()
                return {
                    "stdout": "",
                    "stderr": f"Command timed out after {timeout}s",
                    "exit_code": 124,
                }
                
        except Exception as e:
            return {
                "stdout": "",
                "stderr": str(e),
                "exit_code": 1,
            }
    
    async def write_input(self, session_id: str, data: str) -> bool:
        """
        Write input to a running session (for interactive commands).
        
        Args:
            session_id: Session ID
            data: Input data to write
            
        Returns:
            True if successful
        """
        session = self.sessions.get(session_id)
        if not session or not session.process:
            return False
        
        try:
            if session.process.stdin:
                session.process.stdin.write(data.encode())
                await session.process.stdin.drain()
                return True
        except Exception:
            pass
        
        return False
    
    def close_session(self, session_id: str) -> bool:
        """
        Close a session and clean up resources.
        
        Args:
            session_id: Session to close
            
        Returns:
            True if session was closed
        """
        session = self.sessions.get(session_id)
        if not session:
            return False
        
        session.is_active = False
        
        # Kill any running process
        if session.process:
            try:
                session.process.kill()
            except Exception:
                pass
        
        # Remove callback
        self._output_callbacks.pop(session_id, None)
        
        # Remove session
        del self.sessions[session_id]
        return True
    
    def close_all(self) -> int:
        """
        Close all sessions.
        
        Returns:
            Number of sessions closed
        """
        session_ids = list(self.sessions.keys())
        for sid in session_ids:
            self.close_session(sid)
        return len(session_ids)
    
    def get_output(self, session_id: str) -> str:
        """Get buffered output for a session."""
        session = self.sessions.get(session_id)
        return session.output_buffer if session else ""
    
    def clear_output(self, session_id: str) -> None:
        """Clear buffered output for a session."""
        session = self.sessions.get(session_id)
        if session:
            session.output_buffer = ""


# ─── Global Instance ─────────────────────────────────────────────────────────

_manager: Optional[ShellSessionManager] = None


def get_shell_manager() -> ShellSessionManager:
    """Get the global shell session manager."""
    global _manager
    if _manager is None:
        _manager = ShellSessionManager()
    return _manager

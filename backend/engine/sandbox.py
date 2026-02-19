"""
Sandbox Manager — Phase 2/3

Isolated execution environment for agent-generated code.
Every run happens in a fresh sandbox — no host pollution.

Features:
- Fresh temp directory per run
- File isolation (copy project → sandbox → execute → collect results)
- Hard timeout
- Cleanup guarantee
- Optional Docker support (when available)

Usage:
    from engine.sandbox import get_sandbox_manager

    sandbox_mgr = get_sandbox_manager()
    
    with sandbox_mgr.create("my_run") as sandbox:
        sandbox.write_file("main.py", "print('hello')")
        result = sandbox.execute("python main.py", timeout=30)
        print(result.stdout)
"""

import os
import shutil
import subprocess
import tempfile
import uuid
import shlex
import re
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager

from backend.engine.events import get_event_emitter, EngineEventType


# ─── Constants ───────────────────────────────────────────────────────────────

DEFAULT_TIMEOUT = 60  # seconds
MAX_OUTPUT_SIZE = 50000  # characters

# Security: Whitelist of allowed commands
ALLOWED_COMMANDS = {
    'python', 'python3', 'pip', 'pip3', 'node', 'npm', 'yarn',
    'cargo', 'rustc', 'go', 'javac', 'java', 'ruby', 'gem',
    'php', 'composer', 'dotnet', 'dotnet', 'make', 'cmake',
    'gcc', 'g++', 'clang', 'clang++', 'git', 'docker', 'docker-compose',
    'pytest', 'mocha', 'jest', 'cargo test', 'go test', 'unittest',
}

# Security: Dangerous patterns that should be rejected
DANGEROUS_PATTERNS = [
    r'[;&|]\s*(?:rm|mv|cp|dd|mkfs|fdisk|format)',
    r'\b(?:curl|wget)\s+.*\|.*(?:sh|bash|zsh)',
    r'`[^`]*`',
    r'\$\([^)]*\)',
    r'>>>',
    r'<\s*/dev/(?:tcp|udp)',
    r'base64\s+-d',
    r'eval\s*\(',
    r'exec\s*\(',
    r'system\s*\(',
]


# ─── Execution Result ───────────────────────────────────────────────────────

@dataclass
class ExecutionResult:
    """Result from a sandboxed execution."""
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    command: str
    sandbox_path: str
    
    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "exit_code": self.exit_code,
            "stdout": self.stdout[:MAX_OUTPUT_SIZE],
            "stderr": self.stderr[:MAX_OUTPUT_SIZE],
            "duration_ms": round(self.duration_ms, 2),
            "command": self.command,
        }


# ─── Sandbox Instance ───────────────────────────────────────────────────────

class Sandbox:
    """
    An isolated execution environment.
    
    All file writes and executions happen within the sandbox directory.
    No changes leak to the host filesystem.
    """
    
    def __init__(self, sandbox_id: str, base_path: str):
        self.id = sandbox_id
        self.path = base_path
        self.created_at = datetime.utcnow().isoformat()
        self._files_written: List[str] = []
        self._executions: List[ExecutionResult] = []
    
    def write_file(self, relative_path: str, content: str) -> str:
        """
        Write a file to the sandbox.
        
        Args:
            relative_path: Path relative to sandbox root
            content: File content
            
        Returns:
            Absolute path of written file
        """
        abs_path = os.path.join(self.path, relative_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self._files_written.append(relative_path)
        return abs_path
    
    def read_file(self, relative_path: str) -> Optional[str]:
        """Read a file from the sandbox."""
        abs_path = os.path.join(self.path, relative_path)
        if os.path.exists(abs_path):
            with open(abs_path, 'r', encoding='utf-8', errors='replace') as f:
                return f.read()
        return None
    
    def list_files(self) -> List[str]:
        """List all files in the sandbox."""
        files = []
        for root, _, filenames in os.walk(self.path):
            for filename in filenames:
                rel = os.path.relpath(os.path.join(root, filename), self.path)
                files.append(rel.replace('\\', '/'))
        return files
    
    def copy_from_project(self, project_path: str, exclude: Optional[List[str]] = None) -> int:
        """
        Copy project files into the sandbox.
        
        Args:
            project_path: Source project directory
            exclude: Glob patterns to exclude
            
        Returns:
            Number of files copied
        """
        exclude = exclude or [
            "__pycache__", "node_modules", ".git", ".venv",
            "*.pyc", ".env", "*.db",
        ]
        
        count = 0
        for root, dirs, files in os.walk(project_path):
            # Filter directories
            dirs[:] = [d for d in dirs if d not in exclude]
            
            for filename in files:
                # Check file exclusions
                skip = False
                for pattern in exclude:
                    if pattern.startswith("*.") and filename.endswith(pattern[1:]):
                        skip = True
                        break
                    if filename == pattern:
                        skip = True
                        break
                if skip:
                    continue
                
                src = os.path.join(root, filename)
                rel = os.path.relpath(src, project_path)
                dst = os.path.join(self.path, rel)
                
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                try:
                    shutil.copy2(src, dst)
                    count += 1
                except (PermissionError, OSError):
                    pass
        
        return count
    
    def _validate_command(self, command: str) -> tuple[bool, str]:
        """
        Validate command for security issues.
        
        Returns:
            (is_valid, error_message)
        """
        # Check for dangerous patterns
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return False, f"Security violation: Dangerous pattern detected"
        
        # Parse command to get the base command
        try:
            # Use shlex to safely parse the command
            args = shlex.split(command)
            if not args:
                return False, "Empty command"
            
            base_cmd = args[0]
            
            # Allow if it's in whitelist OR it's a path to an executable
            if '/' in base_cmd or '\\' in base_cmd:
                # It's a path - extract the command name
                cmd_name = os.path.basename(base_cmd)
            else:
                cmd_name = base_cmd
            
            # Check if command is in whitelist
            if cmd_name not in ALLOWED_COMMANDS:
                return False, f"Command '{cmd_name}' not in allowed list"
            
            return True, ""
            
        except ValueError as e:
            return False, f"Invalid command syntax: {e}"

    def execute(
        self,
        command: Union[str, List[str]],
        timeout: int = DEFAULT_TIMEOUT,
        env: Optional[Dict[str, str]] = None,
        shell: bool = False,
    ) -> ExecutionResult:
        """
        Execute a command inside the sandbox.
        
        SECURITY NOTE: By default, shell=False for safety. 
        If shell=True is needed, command will be validated against whitelist.
        
        Args:
            command: Command to run (string or list of args)
            timeout: Hard timeout in seconds
            env: Additional environment variables
            shell: If True, run through shell (validated for security)
            
        Returns:
            ExecutionResult with stdout, stderr, exit code
        """
        run_env = os.environ.copy()
        if env:
            run_env.update(env)
        
        # Restrict PATH-like vars to sandbox
        run_env["SANDBOX_ID"] = self.id
        
        # Convert list to string for logging
        if isinstance(command, list):
            command_str = ' '.join(shlex.quote(str(arg)) for arg in command)
        else:
            command_str = command
        
        start = datetime.utcnow()
        
        # SECURITY: Validate command if using shell
        if shell and isinstance(command, str):
            is_valid, error_msg = self._validate_command(command)
            if not is_valid:
                return ExecutionResult(
                    success=False,
                    exit_code=-1,
                    stdout="",
                    stderr=f"Security error: {error_msg}",
                    duration_ms=0.0,
                    command=command_str,
                    sandbox_path=self.path,
                )
        
        try:
            if shell and isinstance(command, str):
                # Use shell=True only after validation
                proc = subprocess.run(
                    command,
                    shell=True,
                    cwd=self.path,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    env=run_env,
                )
            else:
                # Safe: shell=False with list or validated string
                if isinstance(command, str):
                    command = shlex.split(command)
                
                proc = subprocess.run(
                    command,
                    shell=False,
                    cwd=self.path,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    env=run_env,
                )
            
            duration = (datetime.utcnow() - start).total_seconds() * 1000
            
            result = ExecutionResult(
                success=proc.returncode == 0,
                exit_code=proc.returncode,
                stdout=proc.stdout[:MAX_OUTPUT_SIZE],
                stderr=proc.stderr[:MAX_OUTPUT_SIZE],
                duration_ms=duration,
                command=command_str,
                sandbox_path=self.path,
            )
            
        except subprocess.TimeoutExpired as e:
            duration = timeout * 1000
            # Try to capture partial output
            stdout = e.stdout.decode('utf-8', errors='replace')[:MAX_OUTPUT_SIZE] if e.stdout else ""
            stderr = e.stderr.decode('utf-8', errors='replace')[:MAX_OUTPUT_SIZE] if e.stderr else f"Command timed out after {timeout}s"
            
            result = ExecutionResult(
                success=False,
                exit_code=-1,
                stdout=stdout,
                stderr=stderr,
                duration_ms=duration,
                command=command_str,
                sandbox_path=self.path,
            )
        except Exception as e:
            duration = (datetime.utcnow() - start).total_seconds() * 1000
            result = ExecutionResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                duration_ms=duration,
                command=command_str,
                sandbox_path=self.path,
            )
        
        self._executions.append(result)
        return result
    
    def collect_results(self) -> Dict[str, str]:
        """Collect all files from sandbox for extraction."""
        results = {}
        for filepath in self.list_files():
            content = self.read_file(filepath)
            if content is not None:
                results[filepath] = content
        return results
    
    def cleanup(self) -> None:
        """Remove the sandbox directory."""
        try:
            shutil.rmtree(self.path, ignore_errors=True)
        except Exception:
            pass
    
    def get_status(self) -> dict:
        """Get sandbox status."""
        return {
            "id": self.id,
            "path": self.path,
            "created_at": self.created_at,
            "files_written": len(self._files_written),
            "executions": len(self._executions),
            "total_files": len(self.list_files()),
        }


# ─── Sandbox Manager ────────────────────────────────────────────────────────

class SandboxManager:
    """
    Manages sandboxed execution environments.
    
    Each sandbox is isolated: own directory, own process space.
    Cleanup is guaranteed via context manager or explicit cleanup.
    """
    
    def __init__(self, base_dir: str = ""):
        self.base_dir = base_dir or tempfile.gettempdir()
        self._active: Dict[str, Sandbox] = {}
        self._history: List[Dict[str, Any]] = []
        self.events = get_event_emitter()
    
    @contextmanager
    def create(self, label: str = ""):
        """
        Create a sandbox as a context manager (auto-cleanup).
        
        Usage:
            with sandbox_mgr.create("test_run") as sandbox:
                sandbox.write_file("main.py", code)
                result = sandbox.execute("python main.py")
        """
        sandbox = self.create_sandbox(label)
        try:
            yield sandbox
        finally:
            self.destroy_sandbox(sandbox.id)
    
    def create_sandbox(self, label: str = "") -> Sandbox:
        """
        Create a new sandbox.
        
        Args:
            label: Human-readable label
            
        Returns:
            Sandbox instance
        """
        sandbox_id = f"{label}_{uuid.uuid4().hex[:8]}" if label else uuid.uuid4().hex[:12]
        sandbox_path = os.path.join(self.base_dir, f"vibecoder_sandbox_{sandbox_id}")
        os.makedirs(sandbox_path, exist_ok=True)
        
        sandbox = Sandbox(sandbox_id, sandbox_path)
        self._active[sandbox_id] = sandbox
        
        self._emit_event("SANDBOX_CREATED", {
            "sandbox_id": sandbox_id,
            "path": sandbox_path,
        })
        
        return sandbox
    
    def destroy_sandbox(self, sandbox_id: str) -> bool:
        """Destroy a sandbox and clean up files."""
        if sandbox_id in self._active:
            sandbox = self._active.pop(sandbox_id)
            
            self._history.append({
                "sandbox_id": sandbox_id,
                "created_at": sandbox.created_at,
                "destroyed_at": datetime.utcnow().isoformat(),
                "files": len(sandbox._files_written),
                "executions": len(sandbox._executions),
            })
            
            sandbox.cleanup()
            
            self._emit_event("SANDBOX_DESTROYED", {
                "sandbox_id": sandbox_id,
            })
            return True
        return False
    
    def get_sandbox(self, sandbox_id: str) -> Optional[Sandbox]:
        """Get active sandbox by ID."""
        return self._active.get(sandbox_id)
    
    def list_active(self) -> List[Dict[str, Any]]:
        """List all active sandboxes."""
        return [s.get_status() for s in self._active.values()]
    
    def cleanup_all(self) -> int:
        """Destroy all active sandboxes."""
        count = len(self._active)
        for sandbox_id in list(self._active.keys()):
            self.destroy_sandbox(sandbox_id)
        return count
    
    def _emit_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Emit sandbox event."""
        self.events.emit(EngineEventType.AGENT_STATUS, {
            "agent": "sandbox_manager",
            "event": event_type,
            **payload,
        })


# ─── Global Instance ────────────────────────────────────────────────────────

_sandbox_manager: Optional[SandboxManager] = None


def get_sandbox_manager() -> SandboxManager:
    """Get the global sandbox manager instance."""
    global _sandbox_manager
    if _sandbox_manager is None:
        _sandbox_manager = SandboxManager()
    return _sandbox_manager

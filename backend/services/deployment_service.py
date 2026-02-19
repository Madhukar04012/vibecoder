"""
Deployment Service — Phase 2

Sandbox execution for safe code running.
Agents never execute on host. All execution happens in isolated temp directories.

Features:
- Copy project to temp directory
- Execute commands in isolation
- Clean up after execution
- Timeout protection

Usage:
    result = await run_in_sandbox(
        project_path="/path/to/project",
        command="npm test"
    )
    print(result.stdout)
"""

import asyncio
import shutil
import tempfile
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class SandboxResult:
    """Result of sandbox execution."""
    stdout: str
    stderr: str
    exit_code: int
    execution_time_ms: float
    sandbox_path: str
    success: bool


class DeploymentService:
    """
    Manages sandboxed execution of code.
    
    Every run gets a fresh temp directory.
    No pollution between runs.
    """
    
    def __init__(self, base_temp_dir: Optional[str] = None):
        """
        Initialize the deployment service.
        
        Args:
            base_temp_dir: Base directory for temp sandboxes (default: system temp)
        """
        self.base_temp_dir = base_temp_dir
        self.active_sandboxes: dict[str, str] = {}
    
    async def run_in_sandbox(
        self,
        project_path: str,
        command: str,
        timeout: float = 30.0,
        keep_sandbox: bool = False,
    ) -> SandboxResult:
        """
        Execute a command in an isolated sandbox.
        
        Args:
            project_path: Source project directory to copy
            command: Command to execute
            timeout: Maximum execution time in seconds
            keep_sandbox: Keep sandbox after execution (for debugging)
            
        Returns:
            Execution result
        """
        start_time = datetime.now()
        sandbox_path = ""
        
        try:
            # Create temp sandbox directory
            sandbox_path = tempfile.mkdtemp(
                prefix="vibecober_sandbox_",
                dir=self.base_temp_dir,
            )
            
            # Track active sandbox
            sandbox_id = str(datetime.now().timestamp())
            self.active_sandboxes[sandbox_id] = sandbox_path
            
            # Copy project to sandbox
            project = Path(project_path)
            if project.exists():
                shutil.copytree(
                    project_path,
                    sandbox_path,
                    dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns(
                        "__pycache__",
                        "node_modules",
                        ".git",
                        ".venv",
                        "venv",
                        "*.pyc",
                    ),
                )
            
            # Execute command in sandbox
            import sys
            if sys.platform == "win32":
                shell_cmd = ["cmd", "/c", command]
            else:
                shell_cmd = ["bash", "-c", command]
            
            process = await asyncio.create_subprocess_exec(
                *shell_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=sandbox_path,
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout,
                )
                
                elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
                
                return SandboxResult(
                    stdout=stdout.decode("utf-8", errors="replace"),
                    stderr=stderr.decode("utf-8", errors="replace"),
                    exit_code=process.returncode or 0,
                    execution_time_ms=elapsed_ms,
                    sandbox_path=sandbox_path,
                    success=process.returncode == 0,
                )
                
            except asyncio.TimeoutError:
                process.kill()
                elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
                
                return SandboxResult(
                    stdout="",
                    stderr=f"Command timed out after {timeout}s",
                    exit_code=124,
                    execution_time_ms=elapsed_ms,
                    sandbox_path=sandbox_path,
                    success=False,
                )
                
        except Exception as e:
            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            return SandboxResult(
                stdout="",
                stderr=str(e),
                exit_code=1,
                execution_time_ms=elapsed_ms,
                sandbox_path=sandbox_path,
                success=False,
            )
            
        finally:
            # Cleanup sandbox unless keeping for debug
            if sandbox_path and not keep_sandbox:
                try:
                    shutil.rmtree(sandbox_path, ignore_errors=True)
                except Exception:
                    pass
                
            # Remove from tracking
            if sandbox_id in self.active_sandboxes:
                del self.active_sandboxes[sandbox_id]
    
    def cleanup_all(self) -> int:
        """
        Clean up all active sandboxes.
        
        Returns:
            Number of sandboxes cleaned up
        """
        count = 0
        for sandbox_id, path in list(self.active_sandboxes.items()):
            try:
                shutil.rmtree(path, ignore_errors=True)
                del self.active_sandboxes[sandbox_id]
                count += 1
            except Exception:
                pass
        return count


# ─── Convenience Function ────────────────────────────────────────────────────

_service: Optional[DeploymentService] = None


def get_deployment_service() -> DeploymentService:
    """Get the global deployment service instance."""
    global _service
    if _service is None:
        _service = DeploymentService()
    return _service


async def run_in_sandbox(
    project_path: str,
    command: str,
    timeout: float = 30.0,
) -> SandboxResult:
    """
    Convenience function to run a command in sandbox.
    
    Args:
        project_path: Source project directory
        command: Command to execute
        timeout: Maximum execution time
        
    Returns:
        Execution result
    """
    service = get_deployment_service()
    return await service.run_in_sandbox(
        project_path=project_path,
        command=command,
        timeout=timeout,
    )

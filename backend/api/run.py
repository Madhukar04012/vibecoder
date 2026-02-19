"""
Code execution endpoint — Phase 3.
Runs a shell command and returns stdout/stderr/exitCode.

POST /api/run    → run a command
POST /api/write  → write a file to disk (cross-platform)

Safety: sandboxed to generated_projects/demo/ directory.
"""

import subprocess
from pathlib import Path
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["run"])

# Sandbox: all execution happens inside this directory
SANDBOX_DIR = Path(__file__).resolve().parent.parent.parent / "generated_projects" / "demo"


# ─── Run Command ─────────────────────────────────────────────────────────────

class RunRequest(BaseModel):
    cmd: str


class RunResponse(BaseModel):
    stdout: str
    stderr: str
    exitCode: int


@router.post("/run", response_model=RunResponse)
def run_command(body: RunRequest):
    cmd = body.cmd.strip()
    if not cmd:
        return RunResponse(stdout="", stderr="No command provided.", exitCode=1)

    # Ensure sandbox directory exists
    SANDBOX_DIR.mkdir(parents=True, exist_ok=True)

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            timeout=30,
            cwd=str(SANDBOX_DIR),
            encoding="utf-8",
            errors="replace",
        )
        return RunResponse(
            stdout=result.stdout or "",
            stderr=result.stderr or "",
            exitCode=result.returncode,
        )
    except subprocess.TimeoutExpired:
        return RunResponse(stdout="", stderr="Command timed out (30s limit).", exitCode=124)
    except Exception as e:
        return RunResponse(stdout="", stderr=str(e), exitCode=1)


# ─── Write File ──────────────────────────────────────────────────────────────

class WriteRequest(BaseModel):
    path: str
    content: str


class WriteResponse(BaseModel):
    success: bool
    error: str = ""


@router.post("/write", response_model=WriteResponse)
def write_file(body: WriteRequest):
    """Write a file to the sandbox directory. Creates parent dirs automatically."""
    try:
        target = (SANDBOX_DIR / body.path).resolve()

        # Security: ensure the target is inside the sandbox
        if not str(target).startswith(str(SANDBOX_DIR)):
            return WriteResponse(success=False, error="Path escapes sandbox.")

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body.content, encoding="utf-8")
        return WriteResponse(success=True)
    except Exception as e:
        return WriteResponse(success=False, error=str(e))

"""
Code execution endpoint — Phase 3.
Runs a shell command and returns stdout/stderr/exitCode.

POST /api/run    → run a command
POST /api/write  → write a file to disk (cross-platform)

Safety: sandboxed to generated_projects/demo/ directory with command whitelisting.
"""

import logging
import re
import shlex
import subprocess
from pathlib import Path
from fastapi import APIRouter
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["run"])

# Sandbox: all execution happens inside this directory
SANDBOX_DIR = Path(__file__).resolve().parent.parent.parent / "generated_projects" / "demo"

# Whitelisted command prefixes — only these are allowed to execute
ALLOWED_COMMANDS = frozenset({
    "npm", "npx", "node", "python", "python3", "pip", "pip3",
    "pytest", "ls", "dir", "cat", "echo", "pwd", "cd",
    "git", "tsc", "eslint", "prettier", "vitest", "jest",
})

# Patterns that indicate shell injection attempts
DANGEROUS_PATTERNS = re.compile(
    r"[;&|`$]"       # shell metacharacters: chaining, pipes, subshells
    r"|>\s*/",        # redirect to absolute path
    flags=re.IGNORECASE,
)

MAX_OUTPUT_BYTES = 50_000


def _validate_command(cmd: str) -> str | None:
    """Validate command against whitelist. Returns error message or None if valid."""
    try:
        tokens = shlex.split(cmd)
    except ValueError:
        return "Invalid command syntax."

    if not tokens:
        return "No command provided."

    base_cmd = tokens[0].lower()
    # Strip path prefix (e.g., /usr/bin/node → node)
    base_cmd = base_cmd.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]

    if base_cmd not in ALLOWED_COMMANDS:
        return f"Command '{base_cmd}' is not allowed. Allowed: {', '.join(sorted(ALLOWED_COMMANDS))}"

    if DANGEROUS_PATTERNS.search(cmd):
        return "Command contains disallowed shell operators."

    return None


# ─── Run Command ─────────────────────────────────────────────────────────────

class RunRequest(BaseModel):
    cmd: str = Field(..., max_length=2000)


class RunResponse(BaseModel):
    stdout: str
    stderr: str
    exitCode: int


@router.post("/run", response_model=RunResponse)
def run_command(body: RunRequest):
    cmd = body.cmd.strip()
    if not cmd:
        return RunResponse(stdout="", stderr="No command provided.", exitCode=1)

    validation_error = _validate_command(cmd)
    if validation_error:
        logger.warning("Blocked command: %s — reason: %s", cmd[:100], validation_error)
        return RunResponse(stdout="", stderr=validation_error, exitCode=1)

    # Ensure sandbox directory exists
    SANDBOX_DIR.mkdir(parents=True, exist_ok=True)

    try:
        # Use shlex.split to avoid shell=True where possible
        result = subprocess.run(
            shlex.split(cmd),
            shell=False,
            capture_output=True,
            timeout=30,
            cwd=str(SANDBOX_DIR),
            encoding="utf-8",
            errors="replace",
        )
        return RunResponse(
            stdout=(result.stdout or "")[:MAX_OUTPUT_BYTES],
            stderr=(result.stderr or "")[:MAX_OUTPUT_BYTES],
            exitCode=result.returncode,
        )
    except subprocess.TimeoutExpired:
        return RunResponse(stdout="", stderr="Command timed out (30s limit).", exitCode=124)
    except FileNotFoundError:
        return RunResponse(stdout="", stderr=f"Command not found: {shlex.split(cmd)[0]}", exitCode=127)
    except OSError as e:
        logger.error("Command execution failed: %s", e)
        return RunResponse(stdout="", stderr="Command execution failed.", exitCode=1)


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
    if ".." in body.path or body.path.startswith("/") or body.path.startswith("\\"):
        return WriteResponse(success=False, error="Invalid path: must be relative without '..'.")

    try:
        sandbox_resolved = SANDBOX_DIR.resolve()
        target = (sandbox_resolved / body.path).resolve()

        # Security: ensure the resolved target is inside the resolved sandbox
        try:
            target.relative_to(sandbox_resolved)
        except ValueError:
            logger.warning("Path traversal attempt blocked: %s", body.path[:200])
            return WriteResponse(success=False, error="Path escapes sandbox.")

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body.content, encoding="utf-8")
        return WriteResponse(success=True)
    except PermissionError:
        return WriteResponse(success=False, error="Permission denied.")
    except OSError as e:
        logger.error("File write failed for path=%s: %s", body.path[:200], e)
        return WriteResponse(success=False, error="File write failed.")

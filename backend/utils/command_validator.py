"""
Command Validator - Sanitize and validate shell commands for security
Prevents command injection attacks by using allowlist-based validation
"""

import re
from typing import Tuple, Optional
import shlex


# Allowlist of safe command patterns (command name + optional safe args)
SAFE_COMMANDS = {
    # Package managers
    "npm": ["install", "run", "start", "build", "test", "ci", "audit", "outdated", "list", "version"],
    "yarn": ["install", "build", "start", "test", "add", "remove", "upgrade"],
    "pnpm": ["install", "build", "start", "test", "add", "remove", "update"],
    "pip": ["install", "list", "show", "freeze"],
    "poetry": ["install", "add", "remove", "update", "build", "run"],

    # Build tools
    "vite": ["build", "preview", "dev"],
    "webpack": ["build"],
    "tsc": [],
    "eslint": [],
    "prettier": [],

    # Testing
    "pytest": [],
    "vitest": ["run", "watch"],
    "jest": [],

    # Python tools
    "python": ["-m", "-c"],
    "python3": ["-m", "-c"],
    "uvicorn": [],

    # Version control (read-only operations)
    "git": ["status", "log", "diff", "show", "branch", "remote", "fetch", "pull", "clone"],

    # File operations (safe subset)
    "ls": [],
    "cat": [],
    "echo": [],
    "pwd": [],
    "which": [],
    "tree": [],

    # Docker (read-only)
    "docker": ["ps", "images", "logs", "inspect"],
    "docker-compose": ["ps", "logs", "config"],
}

# Dangerous patterns that should never be allowed
DANGEROUS_PATTERNS = [
    r"rm\s+-rf",        # Recursive force delete
    r";\s*rm",          # Chained delete
    r"&&\s*rm",         # Conditional delete
    r"\|\s*rm",         # Piped delete
    r">\s*/dev",        # Writing to devices
    r"curl.*\|\s*sh",   # Piping downloads to shell
    r"wget.*\|\s*sh",   # Piping downloads to shell
    r"eval",            # Code evaluation
    r"exec",            # Code execution
    r"shutdown",        # System shutdown
    r"reboot",          # System reboot
    r"mkfs",            # Format filesystem
    r"dd\s+if=",        # Disk operations
    r"chmod\s+777",     # Dangerous permissions
    r"chown\s+root",    # Ownership changes
    r"sudo",            # Privilege escalation
    r"su\s",            # User switching
    r"`.*`",            # Command substitution
    r"\$\(",            # Command substitution
    r">\s*~/\.",        # Writing to user config
    r">\s*/etc",        # Writing to system config
]


def validate_command(command: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a shell command against security rules.

    Returns:
        (is_valid, error_message)
        - (True, None) if command is safe
        - (False, error_message) if command is dangerous
    """
    if not command or not command.strip():
        return False, "Empty command"

    command = command.strip()

    # Check for dangerous patterns first
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return False, f"Command contains dangerous pattern: {pattern}"

    # Check for command chaining (allow only &&, but inspect each part)
    if ";" in command or "|" in command:
        return False, "Command chaining with ';' or '|' is not allowed. Use '&&' for sequential commands."

    # Split by && for sequential commands
    parts = command.split("&&")

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # Try to parse command safely
        try:
            tokens = shlex.split(part)
        except ValueError:
            return False, f"Invalid command syntax: {part}"

        if not tokens:
            continue

        base_command = tokens[0]

        # Remove path prefixes (./node_modules/.bin/vite -> vite)
        if "/" in base_command:
            base_command = base_command.split("/")[-1]

        # Check if base command is in allowlist
        if base_command not in SAFE_COMMANDS:
            return False, f"Command '{base_command}' is not in the allowlist. Allowed commands: {', '.join(sorted(SAFE_COMMANDS.keys()))}"

        # Check subcommands if applicable
        allowed_subcommands = SAFE_COMMANDS[base_command]
        if allowed_subcommands and len(tokens) > 1:
            # Verify first argument is in allowed subcommands
            first_arg = tokens[1]

            # Skip flags (start with -)
            if first_arg.startswith("-"):
                continue

            # For git, allow branch names, remotes, etc.
            if base_command == "git" and first_arg not in allowed_subcommands:
                return False, f"Git subcommand '{first_arg}' is not allowed. Allowed: {', '.join(allowed_subcommands)}"

            # For npm/yarn/pnpm, validate subcommands
            if base_command in ["npm", "yarn", "pnpm"] and first_arg not in allowed_subcommands:
                # Allow script names after 'run'
                if len(tokens) > 2 and tokens[1] == "run":
                    continue
                return False, f"{base_command} subcommand '{first_arg}' is not allowed. Allowed: {', '.join(allowed_subcommands)}"

    return True, None


def sanitize_command(command: str) -> str:
    """
    Sanitize a command by removing dangerous characters.
    Note: This is defense-in-depth. Validation should be the primary security control.
    """
    # Remove null bytes
    command = command.replace("\x00", "")

    # Remove newlines (prevent multi-line injection)
    command = command.replace("\n", " ").replace("\r", " ")

    # Collapse multiple spaces
    command = " ".join(command.split())

    return command


def get_safe_command_help() -> str:
    """Return help text listing all allowed commands"""
    commands = sorted(SAFE_COMMANDS.keys())
    return f"""
Allowed commands for security:
- Package managers: npm, yarn, pnpm, pip, poetry
- Build tools: vite, webpack, tsc, eslint, prettier
- Testing: pytest, vitest, jest
- Python: python, python3, uvicorn
- Git (read-only): git status, log, diff, etc.
- File ops: ls, cat, echo, pwd, which, tree
- Docker (read-only): docker ps, images, logs

Full list: {', '.join(commands)}

For safety, destructive commands (rm, sudo, etc.) are blocked.
    """.strip()

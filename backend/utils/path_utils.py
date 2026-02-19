"""
Path Utilities - Cross-platform path normalization and validation
"""

import os
from pathlib import Path
from typing import Optional


def normalize_path(path: str, base: Optional[str] = None) -> str:
    """
    Normalize file path to use forward slashes and remove workspace prefix.

    Args:
        path: Raw path string
        base: Optional base directory to resolve against

    Returns:
        Normalized path string
    """
    if not path:
        return ""

    # Remove workspace prefix
    path = path.replace("/workspace/", "").replace("\\workspace\\", "")
    path = path.lstrip("/\\")

    # Convert to forward slashes
    path = path.replace("\\", "/")

    # Resolve against base if provided
    if base:
        base_path = Path(base)
        full_path = (base_path / path).resolve()
        # Make relative to base
        try:
            return str(full_path.relative_to(base_path)).replace("\\", "/")
        except ValueError:
            # Path is outside base
            return path

    return path


def safe_join(*paths: str) -> str:
    """
    Safely join path components, preventing directory traversal attacks.

    Args:
        *paths: Path components to join

    Returns:
        Joined path string

    Raises:
        ValueError: If path traversal detected
    """
    base = Path(paths[0]) if paths else Path(".")
    result = base

    for part in paths[1:]:
        # Remove any ../ attempts
        if ".." in part:
            raise ValueError(f"Path traversal detected: {part}")

        result = result / part

    return str(result).replace("\\", "/")


def is_safe_path(path: str, allowed_base: str) -> bool:
    """
    Check if a path is safe (doesn't escape allowed base directory).

    Args:
        path: Path to check
        allowed_base: Base directory that should contain the path

    Returns:
        True if path is safe, False otherwise
    """
    try:
        base = Path(allowed_base).resolve()
        target = (base / path).resolve()
        # Check if target is under base
        target.relative_to(base)
        return True
    except (ValueError, RuntimeError):
        return False

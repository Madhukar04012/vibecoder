"""
Shared password hashing utilities.
Single source of truth — imported by API routes and agents alike.
"""

import bcrypt


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    password_bytes = password.encode("utf-8")[:72]  # bcrypt 72-byte limit
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against bcrypt hash."""
    try:
        password_bytes = password.encode("utf-8")[:72]
        return bcrypt.checkpw(password_bytes, hashed.encode("utf-8"))
    except Exception:
        return False

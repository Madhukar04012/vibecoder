"""Utility modules for VibeCober backend"""

from .command_validator import validate_command, sanitize_command, get_safe_command_help
from .json_parser import extract_json_from_text, safe_json_dumps, safe_json_loads
from .path_utils import normalize_path, safe_join, is_safe_path
from .error_formatter import format_error, format_validation_error, format_api_error
from .logger import get_logger, configure_logging, StructuredLogger

__all__ = [
    # Command validation
    "validate_command",
    "sanitize_command",
    "get_safe_command_help",
    # JSON utilities
    "extract_json_from_text",
    "safe_json_dumps",
    "safe_json_loads",
    # Path utilities
    "normalize_path",
    "safe_join",
    "is_safe_path",
    # Error formatting
    "format_error",
    "format_validation_error",
    "format_api_error",
    # Logging
    "get_logger",
    "configure_logging",
    "StructuredLogger",
]

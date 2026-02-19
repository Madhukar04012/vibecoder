"""
Error Formatter - Consistent error message formatting
"""

from typing import Any, Dict, Optional
import traceback


def format_error(
    error: Exception,
    context: Optional[str] = None,
    include_traceback: bool = False
) -> Dict[str, Any]:
    """
    Format exception into consistent error response.

    Args:
        error: The exception to format
        context: Optional context description
        include_traceback: Whether to include full traceback

    Returns:
        Dict with error details
    """
    error_dict = {
        "error": type(error).__name__,
        "message": str(error),
    }

    if context:
        error_dict["context"] = context

    if include_traceback:
        error_dict["traceback"] = traceback.format_exc()

    return error_dict


def format_validation_error(field: str, message: str, value: Any = None) -> Dict[str, Any]:
    """
    Format validation error with field information.

    Args:
        field: Field name that failed validation
        message: Validation error message
        value: Optional invalid value

    Returns:
        Dict with validation error details
    """
    error_dict = {
        "error": "ValidationError",
        "field": field,
        "message": message,
    }

    if value is not None:
        error_dict["invalid_value"] = str(value)

    return error_dict


def format_api_error(status_code: int, detail: str, **kwargs) -> Dict[str, Any]:
    """
    Format API error response.

    Args:
        status_code: HTTP status code
        detail: Error detail message
        **kwargs: Additional error context

    Returns:
        Dict with API error details
    """
    return {
        "status_code": status_code,
        "detail": detail,
        **kwargs
    }

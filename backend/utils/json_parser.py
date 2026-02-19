"""
JSON Parser Utility - Robust JSON extraction from LLM responses
"""

import json
import re
from typing import Any, Optional


def extract_json_from_text(text: str) -> Optional[Any]:
    """
    Extract and parse JSON from mixed text content (e.g., LLM responses).
    Handles markdown code blocks, fenced JSON, and embedded JSON.

    Args:
        text: Raw text that may contain JSON

    Returns:
        Parsed JSON (dict/list) or None if no valid JSON found
    """
    if not text or not isinstance(text, str):
        return None

    text = text.strip()

    # Try 1: Strip markdown code blocks
    if "```json" in text:
        start = text.find("```json") + 7
        end = text.find("```", start)
        if end != -1:
            text = text[start:end].strip()
    elif "```" in text:
        start = text.find("```") + 3
        end = text.find("```", start)
        if end != -1:
            text = text[start:end].strip()

    # Try 2: Find JSON by brace matching
    for open_char, close_char in [("{", "}"), ("[", "]")]:
        idx = text.find(open_char)
        if idx == -1:
            continue

        depth = 0
        for i in range(idx, len(text)):
            if text[i] == open_char:
                depth += 1
            elif text[i] == close_char:
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[idx : i + 1])
                    except json.JSONDecodeError:
                        break

    # Try 3: Parse entire text as JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def safe_json_dumps(obj: Any, indent: int = 2) -> str:
    """
    Safely serialize object to JSON string with error handling.

    Args:
        obj: Object to serialize
        indent: Indentation level (default: 2)

    Returns:
        JSON string or error message
    """
    try:
        return json.dumps(obj, indent=indent, ensure_ascii=False)
    except (TypeError, ValueError) as e:
        return f"{{\"error\": \"JSON serialization failed: {str(e)}\"}}"


def safe_json_loads(text: str) -> Optional[Any]:
    """
    Safely parse JSON string with error handling.

    Args:
        text: JSON string to parse

    Returns:
        Parsed object or None on error
    """
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError, ValueError):
        return None

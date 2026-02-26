"""
Agent Chat API - Secure backend proxy for Anthropic API
Prevents client-side API key exposure by routing through backend
"""

import os
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address
import logging

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/api/agent-chat", tags=["agent-chat"])


class ChatMessage(BaseModel):
    role: str
    content: str | List[Dict[str, Any]]


class ChatRequest(BaseModel):
    agent_name: str
    messages: List[ChatMessage]
    system_prompt: str
    can_use_tools: bool = False
    max_tokens: int = Field(default=8192, le=16384)


class ChatResponse(BaseModel):
    content: List[Dict[str, Any]]
    usage: Optional[Dict[str, int]] = None
    stop_reason: Optional[str] = None


# Tool definitions for IDE integration
IDE_TOOLS = [
    {
        "name": "read_file",
        "description": "Read content of a file from the workspace",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path relative to workspace root"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "write_file",
        "description": "Write or update a file in the workspace",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path relative to workspace root"},
                "content": {"type": "string", "description": "File content to write"}
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "list_files",
        "description": "List all files in the workspace or a specific directory",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path (optional)"}
            }
        }
    },
    {
        "name": "run_command",
        "description": "Execute a whitelisted shell command in the workspace (npm, node, python, git, ls only)",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Shell command to execute. Only npm, node, python, git, ls, cat, echo are allowed.",
                    "maxLength": 2000,
                }
            },
            "required": ["command"]
        }
    },
    {
        "name": "open_file",
        "description": "Open a file in the editor",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to open"}
            },
            "required": ["path"]
        }
    }
]


@router.post("/chat", response_model=ChatResponse)
@limiter.limit("20/minute")  # Stricter limit for AI API calls
async def agent_chat(request: ChatRequest, http_request: Request):
    """
    Proxy Anthropic API calls through backend to keep API key secure.
    Supports tool use for IDE integration.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="ANTHROPIC_API_KEY not configured on server. Please set environment variable."
        )

    try:
        from anthropic import AsyncAnthropic
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Anthropic SDK not installed. Run: pip install anthropic"
        )

    try:
        client = AsyncAnthropic(
            api_key=api_key,
            timeout=30.0,
        )

        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        tools = IDE_TOOLS if request.can_use_tools else None

        response = await client.messages.create(
            model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
            max_tokens=request.max_tokens,
            system=request.system_prompt,
            messages=messages,
            tools=tools,
        )

        usage = None
        if hasattr(response, 'usage'):
            usage = {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            }

        return ChatResponse(
            content=response.content,
            usage=usage,
            stop_reason=response.stop_reason if hasattr(response, 'stop_reason') else None
        )

    except Exception as e:
        logger.exception("Agent chat error: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Error calling AI service. Please try again or contact support.",
        )


@router.get("/health")
async def agent_chat_health():
    """Check if Anthropic API is configured"""
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    return {
        "configured": bool(api_key),
        "message": "Agent chat ready" if api_key else "ANTHROPIC_API_KEY not set"
    }

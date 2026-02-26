"""
MetaGPT Engine API - Atmos Mode

This endpoint wraps MetaGPT as a reasoning engine.
Returns ONLY file changes as JSON array.

Rules:
- No plans, roles, messages returned
- Single run, no rounds
- Strict output format: [{ path, content }]

LLM: Uses NVIDIA NIM API when NIM_API_KEY is set in .env
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
import sys
import os
import json
import logging

logger = logging.getLogger("metagpt_engine")

# NVIDIA NIM — Kimi K2 Thinking (moonshotai/kimi-k2-thinking)
NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"
KIMI_BASE_URL = NIM_BASE_URL  # alias
KIMI_MODEL = "moonshotai/kimi-k2-thinking"
NIM_CODE_MODEL = KIMI_MODEL  # backward-compat alias

router = APIRouter(prefix="/api/agent", tags=["metagpt"])


# ─── Request/Response Schemas ────────────────────────────────────────────────

class WorkspaceContext(BaseModel):
    active: List[str] = []
    opened: List[str] = []
    modified: List[str] = []


class AgentRequest(BaseModel):
    systemPrompt: str
    userPrompt: str
    files: Dict[str, str] = {}


class FileChange(BaseModel):
    path: str
    content: str


# ─── MetaGPT Integration ─────────────────────────────────────────────────────

# Bulletproof prompt header - forces JSON-only output
STRICT_JSON_HEADER = """You are a code generation assistant. You MUST follow these rules EXACTLY:

CRITICAL RULES:
1. Output ONLY valid JSON - nothing else
2. The JSON MUST be an array of objects
3. Each object MUST have exactly two keys: "path" and "content"
4. "path" = relative file path (e.g., "src/utils.ts")
5. "content" = complete file content as a string

FORBIDDEN - DO NOT OUTPUT:
- Explanations or comments
- Markdown or code fences (no ```)
- Plans, roles, or messages
- Anything before or after the JSON array

EXAMPLE OUTPUT:
[{"path": "src/utils.ts", "content": "export function sum(a: number, b: number): number {\\n  return a + b;\\n}"}]

If you cannot generate code, output: []
"""


async def run_metagpt_once(system_prompt: str, user_prompt: str, files: Dict[str, str]) -> List[FileChange]:
    """
    Run MetaGPT as a single-shot code generator.
    Returns only file changes, no plans/roles/messages.
    """
    try:
        # Add MetaGPT to path if needed
        metagpt_path = os.path.join(os.path.dirname(__file__), "..", "..", "project", "MetaGPT")
        if metagpt_path not in sys.path:
            sys.path.insert(0, metagpt_path)
        
        # Import MetaGPT components
        from metagpt.actions.write_code import WriteCode
        from metagpt.schema import Message
        from metagpt.context import Context
        
        # Build context with existing files
        file_context = "\n\n".join([
            f"File: {path}\n{content}"
            for path, content in files.items()
        ]) if files else "No existing files."
        
        # Build the full prompt with strict JSON requirement
        full_prompt = f"""{STRICT_JSON_HEADER}

{system_prompt}

EXISTING FILES:
{file_context}

USER REQUEST:
{user_prompt}

RESPOND WITH JSON ARRAY ONLY:"""
        
        # Create context and action
        # Use NVIDIA NIM when NIM_API_KEY is set; else fall back to config2.yaml
        api_key = (
            os.getenv("NIM_API_KEY", "").strip()
            or os.getenv("NVIDIA_API_KEY", "").strip()
        )
        logger.debug("NIM_API_KEY set: %s", bool(api_key))
        if api_key:
            from metagpt.config2 import Config
            llm_config = {
                "api_type": "openai",
                "base_url": KIMI_BASE_URL,
                "api_key": api_key,
                "model": os.getenv("NIM_MODEL", os.getenv("KIMI_MODEL", KIMI_MODEL)),
                "temperature": 0.2,
                "top_p": 0.7,
            }
            config = Config.from_llm_config(llm_config)
        else:
            from metagpt.config2 import config
        ctx = Context(config=config)
        action = WriteCode(context=ctx)

        model_name = os.getenv("NIM_MODEL", os.getenv("KIMI_MODEL", KIMI_MODEL))
        logger.debug("Calling Kimi model=%s", model_name)

        async def generate():
            result = await action.run(Message(content=full_prompt))
            return result

        # Run the async action (await, not asyncio.run - we're already in an event loop)
        result = await generate()
        raw_output = str(result)

        logger.debug("Raw model output length: %s", len(raw_output))

        # Try to extract JSON from the response
        import re

        patterns = [
            r'\[[\s\S]*?\]',
            r'\[\s*\{[\s\S]*\}\s*\]',
        ]

        for pattern in patterns:
            json_match = re.search(pattern, raw_output)
            if json_match:
                try:
                    changes_data = json.loads(json_match.group())
                    if isinstance(changes_data, list):
                        valid_changes = [
                            FileChange(path=c["path"], content=c["content"])
                            for c in changes_data
                            if isinstance(c, dict) and "path" in c and "content" in c
                        ]
                        if valid_changes:
                            logger.debug("Parsed %s file changes", len(valid_changes))
                            return valid_changes
                except json.JSONDecodeError:
                    continue

        logger.error("Model output JSON parse failed; output length=%s", len(raw_output))
        raise RuntimeError("JSON parse failed")

    except Exception as e:
        logger.exception("MetaGPT run failed: %s", e)
        raise


# ─── API Endpoint ────────────────────────────────────────────────────────────

@router.post("/metagpt", response_model=List[FileChange])
async def run_metagpt_endpoint(request: AgentRequest) -> List[FileChange]:
    """
    Run MetaGPT and return file changes only.
    
    Input:
    - systemPrompt: Instructions for the agent
    - userPrompt: User's request
    - files: Current workspace files
    
    Output:
    - Array of { path, content } changes
    """
    logger.debug("Endpoint /api/agent/metagpt called")
    try:
        changes = await run_metagpt_once(
            system_prompt=request.systemPrompt,
            user_prompt=request.userPrompt,
            files=request.files
        )
        
        # Return normalized output
        return changes
        
    except Exception as e:
        logger.exception("MetaGPT endpoint error")
        raise HTTPException(status_code=500, detail=str(e))

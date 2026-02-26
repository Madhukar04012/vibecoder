"""
LLM Gateway — Multi-Model High-Performance Stack (OpenAI SDK + auto-loads .env)

Centralized LLM caller with token tracking and cost accounting.
ALL agent LLM calls MUST go through this gateway.

Routes each call to the optimal model for its role via model_config.py.

Usage:
    from engine.llm_gateway import llm_call
    
    response = llm_call(
        agent_name="product_manager",
        messages=[
            {"role": "system", "content": "You are a PM."},
            {"role": "user", "content": "Write a PRD."}
        ]
    )
"""

import logging
import os
import re
import json
from typing import List, Dict, Optional, AsyncGenerator
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

# Ensure .env is loaded (belt-and-suspenders: database.py also loads it)
try:
    from dotenv import load_dotenv
    _project_root = Path(__file__).resolve().parent.parent.parent
    _env_file = _project_root / ".env"
    if _env_file.exists():
        load_dotenv(_env_file, override=True)
        logger.debug("Loaded .env from %s", _env_file)
    else:
        load_dotenv(override=True)
except ImportError:
    logger.debug("dotenv not available, using process env")
except Exception as e:
    logger.warning("Failed to load .env: %s", e)

from backend.engine.token_ledger import ledger
from backend.models.pricing import get_model_pricing, estimate_cost
from backend.engine.model_config import (
    get_model_for_role,
    get_profile,
    get_profile_for_role,
    get_chat_model,
    get_coder_model,
    supports_thinking as model_supports_thinking,
)


_nim_key = os.getenv("NIM_API_KEY", "").strip()
_nim_model = os.getenv("NIM_MODEL", "nvidia/llama-3.3-nemotron-super-49b-v1")
_nim_coder_model = os.getenv("NIM_CODER_MODEL", "mistralai/devstral-2-123b-instruct-2512")
_nim_reasoning = os.getenv("NIM_ENABLE_THINKING", "true").lower() == "true"

NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"

logger.info(
    "LLM Gateway: NIM_API_KEY set=%s, model=%s, coder=%s, thinking=%s",
    bool(_nim_key), _nim_model, _nim_coder_model, _nim_reasoning,
)
if not _nim_key:
    logger.warning("No NIM_API_KEY found; agents will fail. Set NIM_API_KEY in .env (nvapi-* from build.nvidia.com)")


def count_tokens(messages: List[Dict[str, str]]) -> int:
    """
    Estimate token count from messages.
    
    Rough estimation: ~4 chars per token for English text.
    For accurate counting, use tiktoken library.
    
    Args:
        messages: List of message dicts with "content" key
        
    Returns:
        Estimated token count
    """
    total_chars = sum(len(m.get("content", "")) for m in messages)
    # Add overhead for role markers, formatting (~10 tokens per message)
    overhead = len(messages) * 10
    return (total_chars // 4) + overhead


def count_output_tokens(text: str) -> int:
    """Estimate output token count from response text."""
    return len(text) // 4 + 5  # +5 for overhead


def _call_nvidia_nim(
    messages: List[Dict[str, str]],
    model: str,
    max_tokens: int,
    temperature: float,
    api_key: str,
    enable_reasoning: bool = True,
    top_p: Optional[float] = None,
) -> tuple[Optional[str], dict]:
    """Call NVIDIA NIM API via OpenAI SDK with per-model optimal parameters. Returns (content, usage_dict)."""
    try:
        from openai import OpenAI

        client = OpenAI(
            base_url=NIM_BASE_URL,
            api_key=api_key,
        )

        # Get model profile for optimal parameters
        profile = get_profile(model)
        has_thinking = profile.supports_thinking and enable_reasoning

        logger.debug(
            "Calling NIM: model=%s, max_tokens=%s, thinking=%s, temp=%.2f, top_p=%.2f",
            model, max_tokens, has_thinking, temperature, top_p or profile.top_p,
        )

        kwargs = dict(
            model=model,
            messages=messages,
            temperature=temperature,
            top_p=top_p if top_p is not None else profile.top_p,
            max_tokens=max_tokens,
            stream=False,
        )

        completion = client.chat.completions.create(**kwargs)
        if not completion.choices:
            return None, {}

        message = completion.choices[0].message
        content = getattr(message, "content", "") or ""
        usage = completion.usage

        logger.debug("NIM response: model=%s, %s chars", model, len(content))

        return content.strip() if content else None, {
            "input_tokens": usage.prompt_tokens if usage else 0,
            "output_tokens": usage.completion_tokens if usage else 0,
        }
    except Exception as e:
        logger.exception("NIM call failed: model=%s error=%s", model, e)
        return None, {}


def llm_call(
    agent_name: str,
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    max_tokens: int = 2048,
    temperature: float = 0.3,
    use_coder: bool = False,
    top_p: Optional[float] = None,
    enable_reasoning: Optional[bool] = None,
    role: Optional[str] = None,
) -> Optional[str]:
    """
    Make an LLM call with automatic token tracking and cost accounting.
    
    This is the ONLY way agents should call LLMs.
    
    Args:
        agent_name: Name of the calling agent (for cost attribution)
        messages: List of message dicts with "role" and "content"
        model: Model to use (auto-detected from role/env if None)
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature (overridden by model profile if role is set)
        use_coder: If True, use the dedicated coder model for code generation
        top_p: Optional nucleus sampling value (defaults to model profile)
        enable_reasoning: Optional reasoning toggle override
        role: Agent role for model routing (e.g., "backend_engineer")
        
    Returns:
        Response content as string, or None if call failed
    """
    if enable_reasoning is None:
        enable_reasoning = os.getenv("NIM_ENABLE_THINKING", "true").lower() == "true"

    nim_key = os.getenv("NIM_API_KEY", "").strip()

    # Model selection priority: explicit model > role-based > coder > default
    if model:
        pass  # use the explicit model
    elif role:
        model = get_model_for_role(role)
        # Use role-specific optimal parameters unless explicitly overridden
        profile = get_profile(model)
        if temperature == 0.3:  # default wasn't overridden
            temperature = profile.temperature
        if top_p is None:
            top_p = profile.top_p
    elif use_coder:
        model = get_coder_model()
    else:
        model = get_chat_model()

    key = nim_key
    
    if not key:
        logger.error("No API key available for model %s", model)
        return None
        
    content, usage = _call_nvidia_nim(
        messages=messages,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        api_key=key,
        enable_reasoning=enable_reasoning,
        top_p=top_p,
    )
    
    # Calculate cost
    input_tokens = usage.get("input_tokens", count_tokens(messages))
    output_tokens = usage.get("output_tokens", count_output_tokens(content or ""))
    cost = estimate_cost(model, input_tokens, output_tokens)
    
    # Record in ledger
    ledger.record(agent_name, input_tokens, output_tokens, cost)
    
    return content


def llm_call_simple(
    agent_name: str,
    system: str,
    user: str,
    max_tokens: int = 2048,
    temperature: float = 0.3,
) -> Optional[str]:
    """
    Simplified LLM call with system/user strings.
    
    Args:
        agent_name: Name of the calling agent
        system: System message content
        user: User message content
        max_tokens: Maximum tokens
        temperature: Sampling temperature
        
    Returns:
        Response content or None
    """
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    return llm_call(agent_name, messages, max_tokens=max_tokens, temperature=temperature)


def extract_json(text: str) -> dict | list | None:
    """
    Extract JSON from LLM output (handles markdown fences).
    
    Args:
        text: Raw LLM output
        
    Returns:
        Parsed JSON or None
    """
    if not text:
        return None
    
    # Strip markdown fences
    text = re.sub(r'^```\w*\n?', '', text.strip())
    text = re.sub(r'\n?```$', '', text.strip())
    
    # Find JSON object or array
    for pattern in [r'\{[\s\S]*\}', r'\[[\s\S]*\]']:
        match = re.search(pattern, text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                continue
    
    return None


# ─── Streaming LLM Calls ─────────────────────────────────────────────────────

def _stream_nvidia_nim(
    messages: List[Dict[str, str]],
    model: str,
    max_tokens: int,
    temperature: float,
    api_key: str,
    enable_reasoning: bool = True,
    top_p: Optional[float] = None,
):
    """Stream tokens from NVIDIA NIM API with per-model parameters. Yields token strings."""
    try:
        from openai import OpenAI

        client = OpenAI(
            base_url=NIM_BASE_URL,
            api_key=api_key,
        )

        # Get model profile
        profile = get_profile(model)
        has_thinking = profile.supports_thinking and enable_reasoning

        logger.debug(
            "Streaming NIM: model=%s, max_tokens=%s, thinking=%s, temp=%.2f",
            model, max_tokens, has_thinking, temperature,
        )

        kwargs = dict(
            model=model,
            messages=messages,
            temperature=temperature,
            top_p=top_p if top_p is not None else profile.top_p,
            max_tokens=max_tokens,
            stream=True,
        )

        stream = client.chat.completions.create(**kwargs)

        for chunk in stream:
            if not getattr(chunk, "choices", None):
                continue
            delta = chunk.choices[0].delta
            # Yield reasoning tokens for models that support thinking
            reasoning = getattr(delta, "reasoning_content", None)
            if reasoning and has_thinking:
                yield reasoning
            if delta.content is not None:
                yield delta.content
    except Exception as e:
        logger.exception("NIM stream error: model=%s error=%s", model, e)


def llm_call_stream(
    agent_name: str,
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    max_tokens: int = 2048,
    temperature: float = 0.3,
    use_coder: bool = False,
    role: Optional[str] = None,
    top_p: Optional[float] = None,
):
    """
    Streaming LLM call — yields tokens as they arrive.
    Routes to the optimal model based on role.

    Args:
        agent_name: Name of the calling agent (for cost attribution)
        messages: List of message dicts
        model: Model override
        max_tokens: Max output tokens
        temperature: Sampling temperature
        use_coder: Use coder model
        role: Agent role for model routing
        top_p: Nucleus sampling override

    Yields:
        Token strings as they arrive from the LLM
    """
    nim_key = os.getenv("NIM_API_KEY", "").strip()

    # Model selection: explicit > role-based > coder > default
    if model:
        pass
    elif role:
        model = get_model_for_role(role)
        profile = get_profile(model)
        if temperature == 0.3:
            temperature = profile.temperature
        if top_p is None:
            top_p = profile.top_p
    elif use_coder:
        model = get_coder_model()
    else:
        model = get_chat_model()

    if nim_key:
        gen = _stream_nvidia_nim(
            messages, model, max_tokens, temperature, nim_key,
            top_p=top_p,
        )
    else:
        logger.error("No NIM_API_KEY available for streaming")
        return

    full_content = []
    for token in gen:
        full_content.append(token)
        yield token

    # Record cost after streaming completes
    full_text = "".join(full_content)
    input_tokens = count_tokens(messages)
    output_tokens = count_output_tokens(full_text)
    cost = estimate_cost(model, input_tokens, output_tokens)
    ledger.record(agent_name, input_tokens, output_tokens, cost)

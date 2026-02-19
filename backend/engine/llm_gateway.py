"""
LLM Gateway — Phase-1 (OpenAI SDK + auto-loads .env)

Centralized LLM caller with token tracking and cost accounting.
ALL agent LLM calls MUST go through this gateway.

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

import os
import re
import json
from typing import List, Dict, Optional, AsyncGenerator
from pathlib import Path

import requests

# Ensure .env is loaded (belt-and-suspenders: database.py also loads it)
try:
    from dotenv import load_dotenv
    # Try project root .env first, then fallback
    _project_root = Path(__file__).resolve().parent.parent.parent
    _env_file = _project_root / ".env"
    if _env_file.exists():
        load_dotenv(_env_file, override=True)
        print(f"[LLM Gateway] Loaded .env from {_env_file}")
    else:
        load_dotenv(override=True)  # fallback to cwd
except ImportError:
    pass

from backend.engine.token_ledger import ledger
from backend.models.pricing import get_model_pricing, estimate_cost


# Log which provider will be used
_nim_key = os.getenv("NIM_API_KEY", "").strip()
_nim_model = os.getenv("NIM_MODEL", "deepseek-ai/deepseek-v3.2")
_nim_coder_model = os.getenv("NIM_CODER_MODEL", "")
_nim_reasoning = os.getenv("NIM_REASONING", "true").lower() == "true"

print(f"[LLM Gateway] NIM_API_KEY set: {bool(_nim_key)} (len={len(_nim_key)})")
print(f"[LLM Gateway] Analysis Model: {_nim_model}")
print(f"[LLM Gateway] Reasoning Mode: {_nim_reasoning}")
if _nim_coder_model:
    print(f"[LLM Gateway] Coder Model: {_nim_coder_model}")

if not _nim_key:
    print("[LLM Gateway] WARNING: No NIM_API_KEY found.")


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
) -> tuple[Optional[str], dict]:
    """Call NVIDIA NIM API via OpenAI SDK with optional reasoning. Returns (content, usage_dict)."""
    try:
        from openai import OpenAI

        client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=api_key,
        )

        is_deepseek = "deepseek" in model.lower()
        use_reasoning = enable_reasoning and is_deepseek

        print(f"[LLM Gateway] Calling NIM: model={model}, max_tokens={max_tokens}, reasoning={use_reasoning}")

        # Build request kwargs
        kwargs = dict(
            model=model,
            messages=messages,
            temperature=temperature if not use_reasoning else 1,  # DeepSeek reasoning requires temp=1
            top_p=0.95 if use_reasoning else 0.7,
            max_tokens=max_tokens,
            stream=use_reasoning,  # Reasoning mode requires streaming
        )

        # Add reasoning support for DeepSeek models
        if use_reasoning:
            kwargs["extra_body"] = {"chat_template_kwargs": {"thinking": True}}

        if use_reasoning:
            # Streaming mode for reasoning — collect full response
            stream = client.chat.completions.create(**kwargs)
            content_parts = []
            reasoning_parts = []
            for chunk in stream:
                if not getattr(chunk, "choices", None):
                    continue
                delta = chunk.choices[0].delta
                # Collect reasoning tokens (internal chain-of-thought)
                reasoning = getattr(delta, "reasoning_content", None)
                if reasoning:
                    reasoning_parts.append(reasoning)
                # Collect content tokens (actual answer)
                if delta.content is not None:
                    content_parts.append(delta.content)

            content = "".join(content_parts)
            reasoning_text = "".join(reasoning_parts)

            if reasoning_text:
                print(f"[LLM Gateway] DeepSeek reasoning: {len(reasoning_text)} chars")
            print(f"[LLM Gateway] NIM response: {len(content)} chars")

            # Estimate tokens from char counts
            return content.strip() if content else None, {
                "input_tokens": sum(len(m.get('content', '')) for m in messages) // 4,
                "output_tokens": (len(content) + len(reasoning_text)) // 4,
            }
        else:
            # Standard non-streaming call
            completion = client.chat.completions.create(**kwargs)
            content = completion.choices[0].message.content if completion.choices else None
            usage = completion.usage

            print(f"[LLM Gateway] NIM response: {len(content or '')} chars")

            return content.strip() if content else None, {
                "input_tokens": usage.prompt_tokens if usage else 0,
                "output_tokens": usage.completion_tokens if usage else 0,
            }
    except Exception as e:
        print(f"[LLM Gateway] NIM error: {e}")
        return None, {}


def llm_call(
    agent_name: str,
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    max_tokens: int = 2048,
    temperature: float = 0.3,
    use_coder: bool = False,
) -> Optional[str]:
    """
    Make an LLM call with automatic token tracking and cost accounting.
    
    This is the ONLY way agents should call LLMs.
    
    Args:
        agent_name: Name of the calling agent (for cost attribution)
        messages: List of message dicts with "role" and "content"
        model: Model to use (auto-detected from env if None)
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature
        use_coder: If True, use the dedicated coder model for code generation
        
    Returns:
        Response content as string, or None if call failed
    """
    nim_key = os.getenv("NIM_API_KEY", "").strip()
    nim_coder_key = os.getenv("NIM_CODER_API_KEY", "").strip()

    enable_reasoning = os.getenv("NIM_REASONING", "true").lower() == "true"

    if use_coder:
        nim_default_model = os.getenv("NIM_CODER_MODEL", "") or os.getenv("NIM_MODEL", "deepseek-ai/deepseek-v3.2")
    else:
        nim_default_model = os.getenv("NIM_MODEL", "deepseek-ai/deepseek-v3.2")

    model = model or nim_default_model
    key = nim_coder_key if use_coder else nim_key
    
    if not key:
        print(f"[LLM Gateway] ERROR: No API key available for {'coder' if use_coder else 'standard'} model")
        return None
        
    content, usage = _call_nvidia_nim(messages, model, max_tokens, temperature, key, enable_reasoning)
    
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
):
    """Stream tokens from NVIDIA NIM API with reasoning support. Yields token strings."""
    try:
        from openai import OpenAI

        client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=api_key,
        )

        is_deepseek = "deepseek" in model.lower()
        use_reasoning = enable_reasoning and is_deepseek

        print(f"[LLM Gateway] Streaming NIM: model={model}, max_tokens={max_tokens}, reasoning={use_reasoning}")

        kwargs = dict(
            model=model,
            messages=messages,
            temperature=1 if use_reasoning else temperature,
            top_p=0.95 if use_reasoning else 0.7,
            max_tokens=max_tokens,
            stream=True,
        )

        if use_reasoning:
            kwargs["extra_body"] = {"chat_template_kwargs": {"thinking": True}}

        stream = client.chat.completions.create(**kwargs)

        for chunk in stream:
            if not getattr(chunk, "choices", None):
                continue
            delta = chunk.choices[0].delta
            # Skip reasoning tokens in streaming output (internal thinking)
            # They're used by the model but we don't stream them to the user
            if delta.content is not None:
                yield delta.content
    except Exception as e:
        print(f"[LLM Gateway] NIM stream error: {e}")


def llm_call_stream(
    agent_name: str,
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    max_tokens: int = 2048,
    temperature: float = 0.3,
    use_coder: bool = False,
):
    """
    Streaming LLM call — yields tokens as they arrive.

    Args:
        agent_name: Name of the calling agent (for cost attribution)
        messages: List of message dicts
        model: Model override
        max_tokens: Max output tokens
        temperature: Sampling temperature
        use_coder: Use coder model

    Yields:
        Token strings as they arrive from the LLM
    """
    if use_coder:
        nim_key = os.getenv("NIM_CODER_API_KEY", "").strip() or os.getenv("NIM_API_KEY", "").strip()
        default_model = os.getenv("NIM_CODER_MODEL", "") or os.getenv("NIM_MODEL", "deepseek-ai/deepseek-v3.2")
    else:
        nim_key = os.getenv("NIM_API_KEY", "").strip()
        default_model = os.getenv("NIM_MODEL", "deepseek-ai/deepseek-v3.2")

    enable_reasoning = os.getenv("NIM_REASONING", "true").lower() == "true"

    if nim_key:
        model = model or default_model
        gen = _stream_nvidia_nim(messages, model, max_tokens, temperature, nim_key, enable_reasoning)
    else:
        print("[LLM Gateway] ERROR: No NIM_API_KEY available for streaming")
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

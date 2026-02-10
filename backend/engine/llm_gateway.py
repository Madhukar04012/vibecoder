"""
LLM Gateway — Phase-1

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
from typing import List, Dict, Optional

import requests

from backend.engine.token_ledger import ledger
from backend.models.pricing import get_model_pricing, estimate_cost


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
) -> tuple[Optional[str], dict]:
    """Call NVIDIA NIM API. Returns (content, usage_dict)."""
    try:
        response = requests.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
            timeout=90,
        )
        response.raise_for_status()
        data = response.json()
        
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        usage = data.get("usage", {})
        
        return content.strip() if content else None, {
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
        }
    except Exception as e:
        print(f"[LLM Gateway] NIM error: {e}")
        return None, {}


def _call_ollama(
    messages: List[Dict[str, str]],
    model: str,
    temperature: float,
) -> tuple[Optional[str], dict]:
    """Call local Ollama. Returns (content, usage_dict)."""
    # Combine messages into single prompt for generate endpoint
    prompt_parts = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "system":
            prompt_parts.append(f"[System]: {content}")
        else:
            prompt_parts.append(content)
    
    prompt = "\n\n".join(prompt_parts)
    
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": temperature},
            },
            timeout=90,
        )
        response.raise_for_status()
        data = response.json()
        
        content = data.get("response", "").strip()
        
        # Ollama provides token counts
        usage = {
            "input_tokens": data.get("prompt_eval_count", count_tokens(messages)),
            "output_tokens": data.get("eval_count", count_output_tokens(content)),
        }
        
        return content if content else None, usage
    except Exception as e:
        print(f"[LLM Gateway] Ollama error: {e}")
        return None, {}


def llm_call(
    agent_name: str,
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    max_tokens: int = 2048,
    temperature: float = 0.3,
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
        
    Returns:
        Response content as string, or None if call failed
    """
    # Determine model and provider
    nim_key = os.getenv("NIM_API_KEY", "").strip()
    
    if nim_key:
        model = model or os.getenv("NIM_MODEL", "meta/llama-3.3-70b-instruct")
        content, usage = _call_nvidia_nim(messages, model, max_tokens, temperature, nim_key)
    else:
        model = model or os.getenv("OLLAMA_CHAT_MODEL", "llama3.2")
        content, usage = _call_ollama(messages, model, temperature)
    
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

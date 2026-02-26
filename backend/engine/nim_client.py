"""
NIMClient — Async LLM Client for NVIDIA NIM High-Performance Multi-Model Stack

Features:
  - Per-role model routing (each agent uses its optimal model)
  - Async streaming via AsyncGenerator[str, None]
  - Retry with exponential backoff, max 3 retries
  - Rate limit (429) detection and graceful retry
  - Token usage tracking per call
  - JSON response validation with retry on parse failure
  - Per-model optimal parameters (temperature, top_p, thinking mode)

Model Stack:
  team_lead         → nvidia/llama-3.3-nemotron-super-49b-v1              (planning)
  backend_engineer  → mistralai/devstral-2-123b-instruct-2512             (backend code)
  frontend_engineer → qwen/qwen2.5-coder-32b-instruct                    (frontend code)
  database_engineer → meta/llama-3.3-70b-instruct                         (schema design)
  qa_engineer       → qwen/qwq-32b                                        (validation)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import random
import re
import time
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Optional

from dotenv import load_dotenv

# Load .env from project root
_root = Path(__file__).resolve().parent.parent.parent
_env = _root / ".env"
if _env.exists():
    load_dotenv(_env, override=True)

logger = logging.getLogger("nim_client")

# ── Import centralized model config ───────────────────────────────────────────
from backend.engine.model_config import (
    ROLE_MODEL_DEFAULTS,
    MODEL_PROFILES,
    get_model_for_role,
    get_profile_for_role,
    get_profile,
    get_temperature_for_role,
    get_top_p_for_role,
    get_max_tokens_for_role,
    supports_thinking,
)

# ── Constants ──────────────────────────────────────────────────────────────────

NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"
MAX_RETRIES = 3
BASE_BACKOFF = 0.5  # seconds (fast retry for NIM)

# Re-export AGENT_MODEL_MAP for backward compatibility (nim_test.py imports it)
AGENT_MODEL_MAP = ROLE_MODEL_DEFAULTS

# Agent temperatures — dynamic from model_config
AGENT_TEMPERATURES: Dict[str, float] = {
    role: get_temperature_for_role(role)
    for role in ROLE_MODEL_DEFAULTS
}


# ── Key Routing ────────────────────────────────────────────────────────────────

def _resolve_api_key(model: str) -> str:
    """Select the correct NIM API key for the given model."""
    key = (
        os.getenv("NIM_API_KEY", "").strip()
        or os.getenv("NVIDIA_API_KEY", "").strip()
    )
    if not key:
        raise EnvironmentError(
            f"No NIM API key found for model '{model}'. "
            "Set NIM_API_KEY (get it at build.nvidia.com) in .env"
        )
    return key


# ── Usage Tracking ─────────────────────────────────────────────────────────────

class UsageLedger:
    """In-memory per-call usage tracker (synchronous, thread-safe via GIL)."""

    def __init__(self) -> None:
        self._records: list[dict] = []

    def record(
        self,
        role: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: float,
    ) -> None:
        rec = {
            "role": role,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "latency_ms": round(latency_ms, 1),
        }
        self._records.append(rec)
        logger.info(
            "[Usage] role=%s model=%s in=%d out=%d %.0fms",
            role, model, input_tokens, output_tokens, latency_ms,
        )

    def totals(self) -> dict:
        return {
            "call_count":          len(self._records),
            "total_input_tokens":  sum(r["input_tokens"]  for r in self._records),
            "total_output_tokens": sum(r["output_tokens"] for r in self._records),
        }

    def records(self) -> list[dict]:
        return list(self._records)


usage_ledger = UsageLedger()


# ── NIMClient ──────────────────────────────────────────────────────────────────

class NIMClient:
    """
    Async LLM client for NVIDIA NIM Cloud (OpenAI-compatible API).
    Routes each agent role to its optimal model with tuned parameters.

    Usage::

        client = NIMClient()

        # Non-streaming
        text = await client.complete(role="team_lead", messages=[...])

        # Streaming
        async for token in client.stream(role="backend_engineer", messages=[...]):
            print(token, end="", flush=True)

        # JSON-validated (retries on parse failure)
        data = await client.complete_json(role="team_lead", messages=[...])
    """

    def __init__(self) -> None:
        self._clients: Dict[str, object] = {}  # api_key → AsyncOpenAI

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _get_async_client(self, api_key: str):
        if api_key not in self._clients:
            from openai import AsyncOpenAI  # lazy import — avoids import-time overhead
            self._clients[api_key] = AsyncOpenAI(
                base_url=NIM_BASE_URL,
                api_key=api_key,
                timeout=float(os.getenv("LLM_TIMEOUT_SECONDS", "300")),
            )
        return self._clients[api_key]

    async def _call_with_retry(
        self,
        role: str,
        model: str,
        api_key: str,
        messages: List[Dict[str, str]],
        temperature: float,
        top_p: float,
        max_tokens: int,
        stream: bool,
    ):
        """Execute one LLM call with exponential-backoff retry on rate limits and transient errors."""
        from openai import RateLimitError, APIStatusError, APIConnectionError

        client = self._get_async_client(api_key)
        last_exc: Exception | None = None

        for attempt in range(MAX_RETRIES):
            try:
                kwargs = dict(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    top_p=top_p,
                    max_tokens=max_tokens,
                    stream=stream,
                )
                logger.debug(
                    "[NIMClient] %s role=%s model=%s temp=%.2f top_p=%.2f max_tok=%d",
                    "stream" if stream else "complete", role, model,
                    temperature, top_p, max_tokens,
                )
                return await client.chat.completions.create(**kwargs)
            except RateLimitError as exc:
                last_exc = exc
                wait = BASE_BACKOFF * (2 ** attempt) + random.uniform(0, 0.5)
                logger.warning(
                    "[NIMClient] 429 rate-limited (attempt %d/%d) role=%s model=%s — retry in %.1fs",
                    attempt + 1, MAX_RETRIES, role, model, wait,
                )
                await asyncio.sleep(wait)
            except (APIStatusError, APIConnectionError) as exc:
                last_exc = exc
                if attempt < MAX_RETRIES - 1:
                    wait = BASE_BACKOFF * (2 ** attempt) + random.uniform(0, 0.5)
                    logger.warning(
                        "[NIMClient] API error (attempt %d/%d) role=%s model=%s: %s — retry in %.1fs",
                        attempt + 1, MAX_RETRIES, role, model, exc, wait,
                    )
                    await asyncio.sleep(wait)
                else:
                    raise

        raise last_exc or RuntimeError(
            f"NIMClient: all {MAX_RETRIES} retries exhausted for role={role} model={model}"
        )

    # ── Public API ─────────────────────────────────────────────────────────────

    async def complete(
        self,
        role: str,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
    ) -> str:
        """Non-streaming completion. Uses per-role optimal parameters."""
        model = model or get_model_for_role(role)
        profile = get_profile(model)
        temperature = temperature if temperature is not None else profile.temperature
        top_p = top_p if top_p is not None else profile.top_p
        max_tokens = max_tokens or profile.max_tokens
        api_key = _resolve_api_key(model)

        t0 = time.monotonic()
        completion = await self._call_with_retry(
            role=role, model=model, api_key=api_key,
            messages=messages, temperature=temperature, top_p=top_p,
            max_tokens=max_tokens, stream=False,
        )
        latency_ms = (time.monotonic() - t0) * 1000

        content: str = completion.choices[0].message.content or ""
        usage = completion.usage
        usage_ledger.record(
            role=role, model=model,
            input_tokens=usage.prompt_tokens if usage else _estimate_tokens(messages),
            output_tokens=usage.completion_tokens if usage else len(content) // 4,
            latency_ms=latency_ms,
        )
        return content.strip()

    async def stream(
        self,
        role: str,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Async generator — yields token strings as they arrive from the NIM API.
        Handles models with reasoning_content (thinking tokens) transparently.
        """
        model = model or get_model_for_role(role)
        profile = get_profile(model)
        temperature = temperature if temperature is not None else profile.temperature
        top_p = top_p if top_p is not None else profile.top_p
        max_tokens = max_tokens or profile.max_tokens
        api_key = _resolve_api_key(model)

        t0 = time.monotonic()
        stream_obj = await self._call_with_retry(
            role=role, model=model, api_key=api_key,
            messages=messages, temperature=temperature, top_p=top_p,
            max_tokens=max_tokens, stream=True,
        )

        full_content: list[str] = []
        async for chunk in stream_obj:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            # Yield reasoning tokens for models that support thinking
            reasoning = getattr(delta, "reasoning_content", None)
            if reasoning and profile.supports_thinking:
                full_content.append(reasoning)
                yield reasoning
            if delta.content:
                full_content.append(delta.content)
                yield delta.content

        latency_ms = (time.monotonic() - t0) * 1000
        full_text = "".join(full_content)
        usage_ledger.record(
            role=role, model=model,
            input_tokens=_estimate_tokens(messages),
            output_tokens=len(full_text) // 4,
            latency_ms=latency_ms,
        )

    async def complete_json(
        self,
        role: str,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
    ) -> dict | list:
        """
        Non-streaming completion that validates and returns parsed JSON.
        Retries up to MAX_RETRIES times on JSON parse failure.
        """
        msgs = list(messages)  # don't mutate caller's list
        last_error: str = ""

        for attempt in range(MAX_RETRIES):
            text = await self.complete(
                role=role, messages=msgs, model=model,
                max_tokens=max_tokens, temperature=temperature, top_p=top_p,
            )
            parsed = _extract_json(text)
            if parsed is not None:
                return parsed

            last_error = f"attempt {attempt + 1}: got {text[:200]!r}"
            logger.warning("[NIMClient] JSON parse failed for role=%s model=%s — %s",
                           role, get_model_for_role(role), last_error)

            # Inject correction turn so the model self-corrects on retry
            msgs = msgs + [
                {"role": "assistant", "content": text},
                {
                    "role": "user",
                    "content": (
                        "Your response was not valid JSON. "
                        "Return ONLY a valid JSON object or array. "
                        "No markdown fences, no explanations."
                    ),
                },
            ]

        raise ValueError(
            f"NIMClient.complete_json: all {MAX_RETRIES} attempts produced invalid JSON "
            f"for role={role}. Last error: {last_error}"
        )

    def get_model_info(self, role: str) -> dict:
        """Return model info for a role (useful for frontend display)."""
        model = get_model_for_role(role)
        profile = get_profile(model)
        return {
            "model": model,
            "temperature": profile.temperature,
            "top_p": profile.top_p,
            "max_tokens": profile.max_tokens,
            "supports_thinking": profile.supports_thinking,
            "description": profile.description,
        }


# ── Helpers ────────────────────────────────────────────────────────────────────

def _estimate_tokens(messages: List[Dict[str, str]]) -> int:
    """Rough token estimate: 4 chars/token + 10 tokens overhead per message."""
    total_chars = sum(len(m.get("content", "")) for m in messages)
    return (total_chars // 4) + len(messages) * 10


def _extract_json(text: str) -> dict | list | None:
    """Extract and parse JSON from LLM output, stripping markdown fences if present."""
    if not text:
        return None

    # Strip ```json ... ``` fences
    clean = re.sub(r"^```\w*\n?", "", text.strip())
    clean = re.sub(r"\n?```$", "", clean.strip())

    # Try direct parse
    try:
        return json.loads(clean)
    except json.JSONDecodeError as e:
        logger.debug("parse_json_from_llm direct parse failed: %s", e)

    # Try to extract the first JSON object or array embedded in prose
    for pattern in [r"\{[\s\S]*\}", r"\[[\s\S]*\]"]:
        m = re.search(pattern, clean)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                continue

    return None


# ── Singleton ──────────────────────────────────────────────────────────────────

_singleton: NIMClient | None = None


def get_nim_client() -> NIMClient:
    """Return (or create) the module-level NIMClient singleton."""
    global _singleton
    if _singleton is None:
        _singleton = NIMClient()
    return _singleton

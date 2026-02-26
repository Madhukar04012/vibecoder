"""
Centralized LLM client (NVIDIA NIM + OpenAI SDK).

Responsibilities:
- Single provider integration path for streamed chat completions
- API key isolation (no keys in agents/routers)
- Retry + rate-limit handling with circuit breaker
- Token/cost tracking via shared ledger

Legacy helpers (`nim_chat`, `call_llm`, `call_ollama`) are preserved for older
code paths.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
from typing import Any, AsyncGenerator, Callable

from backend.engine.token_ledger import ledger
from backend.models.pricing import estimate_cost

logger_llm = logging.getLogger(__name__)

# ── Circuit Breaker ──────────────────────────────────────────────────────────

CIRCUIT_FAILURE_THRESHOLD = int(os.getenv("LLM_CIRCUIT_FAILURE_THRESHOLD", "5"))
CIRCUIT_RECOVERY_SECONDS = float(os.getenv("LLM_CIRCUIT_RECOVERY_SECONDS", "30"))


class CircuitOpenError(RuntimeError):
    """Raised when the circuit breaker is open and calls are rejected."""


class _CircuitBreaker:
    """Per-provider circuit breaker: CLOSED → OPEN → HALF_OPEN → CLOSED."""

    def __init__(self, threshold: int = CIRCUIT_FAILURE_THRESHOLD, recovery_s: float = CIRCUIT_RECOVERY_SECONDS):
        self._threshold = threshold
        self._recovery_s = recovery_s
        self._failures: int = 0
        self._opened_at: float = 0.0
        self._state: str = "closed"  # closed | open | half_open

    @property
    def state(self) -> str:
        if self._state == "open" and (time.monotonic() - self._opened_at) >= self._recovery_s:
            self._state = "half_open"
        return self._state

    def record_success(self) -> None:
        self._failures = 0
        self._state = "closed"

    def record_failure(self) -> None:
        self._failures += 1
        if self._failures >= self._threshold:
            self._state = "open"
            self._opened_at = time.monotonic()
            logger_llm.warning("Circuit breaker OPEN after %d failures (recovery in %ds)", self._failures, self._recovery_s)

    def check(self, provider: str) -> None:
        state = self.state
        if state == "open":
            raise CircuitOpenError(f"Circuit breaker open for provider '{provider}'. Retry after {self._recovery_s}s.")


# Global per-provider breakers
_breakers: dict[str, _CircuitBreaker] = {}


def _get_breaker(provider: str) -> _CircuitBreaker:
    if provider not in _breakers:
        _breakers[provider] = _CircuitBreaker()
    return _breakers[provider]

# Ensure .env is loaded
try:
    from dotenv import load_dotenv
    _root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    load_dotenv(os.path.join(_root, ".env"))
except Exception as e:
    logger_llm.debug("llm_client: could not load .env: %s", e)


class LLMClientError(RuntimeError):
    """Raised when the LLM client cannot complete a request."""


def extract_json_from_text(raw: str) -> dict | list | None:
    """Extract JSON object/array from raw text (handles markdown fences)."""
    if not raw or not isinstance(raw, str):
        return None

    text = raw.strip()
    text = re.sub(r"^```json\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    for pattern in [r"\{[\s\S]*\}", r"\[[\s\S]*\]"]:
        match = re.search(pattern, text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                continue

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


class LLMClient:
    """Universal async LLM caller — Kimi K2 Thinking via NVIDIA NIM."""

    MODEL_ALIASES = {
        # Short aliases → full NIM model ID
        "kimi-k2": "moonshotai/kimi-k2-thinking",
        "kimi": "moonshotai/kimi-k2-thinking",
        "kimi-k2.5": "moonshotai/kimi-k2-thinking",
        "kimi-k2-thinking": "moonshotai/kimi-k2-thinking",
        # Legacy model aliases — all map to Kimi K2 Thinking
        "deepseek-v3.2": "moonshotai/kimi-k2-thinking",
        "deepseek-ai/deepseek-v3.2": "moonshotai/kimi-k2-thinking",
        "deepseek-v3.1-terminus": "moonshotai/kimi-k2-thinking",
        "qwen3-coder-480b-a35b-instruct": "moonshotai/kimi-k2-thinking",
        "qwen/qwen3-coder-480b-a35b-instruct": "moonshotai/kimi-k2-thinking",
        "qwen3-next-80b-thinking": "moonshotai/kimi-k2-thinking",
    }

    def __init__(self, timeout_seconds: float | None = None, max_retries: int = 3):
        timeout_default = os.getenv("LLM_TIMEOUT_SECONDS", "180")
        self.timeout_seconds = float(timeout_seconds if timeout_seconds is not None else timeout_default)
        self.max_retries = max(1, min(int(max_retries), 3))

        self.nim_base_url = os.getenv("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
        # NIM API key (nvapi-* from build.nvidia.com)
        self.kimi_key = (
            os.getenv("NIM_API_KEY", "").strip()
            or os.getenv("NVIDIA_API_KEY", "").strip()
        )
        # Legacy aliases — all route to the same NIM key
        self.deepseek_key = self.kimi_key
        self.qwen_key = self.kimi_key
        self.glm_key = self.kimi_key

    def _get_key(self, provider: str) -> str:
        return self.kimi_key

    def _normalize_model(self, model: str, provider: str) -> str:
        model_name = (model or "").strip()
        if not model_name:
            model_name = os.getenv("NIM_MODEL", "moonshotai/kimi-k2-thinking")
        return self.MODEL_ALIASES.get(model_name, model_name)

    @staticmethod
    def _env_truthy(value: str | None) -> bool:
        if value is None:
            return False
        return value.strip().lower() in {"1", "true", "yes", "on"}

    def _thinking_enabled_for_model(self, model_id: str) -> bool:
        # kimi-k2-thinking has built-in reasoning — no chat_template_kwargs needed
        # reasoning arrives via delta.reasoning_content, final answer via delta.content
        if not self._env_truthy(os.getenv("NIM_ENABLE_THINKING", "true")):
            return False
        return "kimi" in model_id.lower()

    @staticmethod
    def _is_retryable(status_code: int | None, message: str) -> bool:
        if status_code in {429, 500, 502, 503, 504}:
            return True
        text = (message or "").lower()
        return any(token in text for token in ["timeout", "connection", "temporarily", "rate limit"])

    async def call(
        self,
        provider: str,
        model: str,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
        top_p: float = 0.85,
        stream: bool = True,
    ) -> AsyncGenerator[str, None]:
        """Low-level model call with circuit breaker and retry."""
        api_key = self._get_key(provider)
        if not api_key:
            raise LLMClientError(f"missing API key for provider: {provider}")

        model_id = self._normalize_model(model, provider)
        thinking_enabled = self._thinking_enabled_for_model(model_id)
        breaker = _get_breaker(provider)

        # Fail fast if circuit is open
        breaker.check(provider)

        for attempt in range(1, self.max_retries + 1):
            client = None
            try:
                from openai import AsyncOpenAI

                client = AsyncOpenAI(
                    base_url=self.nim_base_url,
                    api_key=api_key,
                    timeout=self.timeout_seconds,
                )

                kwargs: dict[str, Any] = {
                    "model": model_id,
                    "messages": messages,
                    "temperature": 1.0 if thinking_enabled else temperature,
                    "top_p": 0.9 if thinking_enabled else top_p,
                    "max_tokens": max_tokens,
                    "stream": stream,
                }

                # kimi-k2-thinking: NO chat_template_kwargs — reasoning is built-in.
                # Reasoning tokens arrive in delta.reasoning_content, final answer in delta.content.

                if stream:
                    completion_stream = await client.chat.completions.create(**kwargs)
                    async for chunk in completion_stream:
                        if not getattr(chunk, "choices", None):
                            continue
                        delta = chunk.choices[0].delta
                        # kimi-k2-thinking: reasoning_content first, then content
                        reasoning = getattr(delta, "reasoning_content", None)
                        if reasoning is not None:
                            yield reasoning
                        content = getattr(delta, "content", None)
                        if content is not None:
                            yield content
                else:
                    completion = await client.chat.completions.create(**kwargs)
                    content = completion.choices[0].message.content if completion.choices else ""
                    if content:
                        yield content

                breaker.record_success()
                return

            except CircuitOpenError:
                raise
            except asyncio.TimeoutError as exc:
                breaker.record_failure()
                logger_llm.warning("LLM timeout provider=%s model=%s attempt=%d/%d", provider, model_id, attempt, self.max_retries)
                if attempt >= self.max_retries:
                    raise LLMClientError(f"{provider} timed out after {self.timeout_seconds}s") from exc
                await asyncio.sleep(min(2 ** (attempt - 1), 8))
            except Exception as exc:
                status_code = getattr(exc, "status_code", None)
                message = str(exc)
                retryable = self._is_retryable(status_code, message)

                if retryable:
                    breaker.record_failure()
                    logger_llm.warning(
                        "LLM retryable error provider=%s model=%s attempt=%d/%d status=%s: %s",
                        provider, model_id, attempt, self.max_retries, status_code, message[:200],
                    )
                else:
                    # Non-retryable (400, 401, 404) — fail immediately, don't trip breaker
                    raise LLMClientError(f"{provider} non-retryable error (status={status_code}): {message[:200]}") from exc

                if attempt >= self.max_retries:
                    raise LLMClientError(f"{provider} failed after {self.max_retries} attempts: {message[:200]}") from exc
                await asyncio.sleep(min(2 ** (attempt - 1), 8))
            finally:
                if client is not None:
                    try:
                        await client.close()
                    except Exception:
                        pass  # Close errors are non-actionable

        raise LLMClientError(f"{provider} call failed after {self.max_retries} attempts")

    async def stream_tokens(
        self,
        provider: str,
        model: str,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
        top_p: float = 0.85,
        agent_name: str | None = None,
        on_token: Callable[[str], Any] | None = None,
    ) -> AsyncGenerator[str, None]:
        """Yield decoded content tokens and record usage/cost after completion."""
        chunks: list[str] = []
        async for token in self.call(
            provider=provider,
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            stream=True,
        ):
            if not token:
                continue
            chunks.append(token)
            if on_token:
                maybe = on_token(token)
                if asyncio.iscoroutine(maybe):
                    await maybe
            yield token

        final_text = "".join(chunks)
        self._record_usage(
            agent_name=agent_name,
            model=self._normalize_model(model, provider),
            messages=messages,
            output_text=final_text,
        )

    async def complete(
        self,
        provider: str,
        model: str,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
        top_p: float = 0.85,
        agent_name: str | None = None,
        on_token: Callable[[str], Any] | None = None,
    ) -> str:
        """Return full content text while optionally streaming tokens to callback."""
        parts: list[str] = []
        async for token in self.stream_tokens(
            provider=provider,
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            agent_name=agent_name,
            on_token=on_token,
        ):
            parts.append(token)
        result = "".join(parts).strip()
        if not result:
            model_id = self._normalize_model(model, provider)
            raise LLMClientError(f"{provider} model '{model_id}' returned empty content")
        return result

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        if not text:
            return 0
        return max(1, len(text) // 4)

    def _record_usage(
        self,
        agent_name: str | None,
        model: str,
        messages: list[dict[str, str]],
        output_text: str,
    ) -> None:
        if not agent_name:
            return

        input_text = "\n".join(str(m.get("content", "")) for m in messages)
        input_tokens = self._estimate_tokens(input_text)
        output_tokens = self._estimate_tokens(output_text)
        cost = estimate_cost(model, input_tokens, output_tokens)
        ledger.record(agent_name, input_tokens=input_tokens, output_tokens=output_tokens, cost=cost)


# ---------------------------------------------------------------------------
# Legacy compatibility wrappers
# ---------------------------------------------------------------------------

_DEFAULT_LEGACY_MODEL = os.getenv("NIM_MODEL", "moonshotai/kimi-k2-thinking")


def nim_chat(prompt: str, max_retries: int = 3, timeout: float = 30.0) -> str | None:
    """
    Legacy NIM-compatible sync helper.

    Uses the existing llm_gateway path for older modules.
    """
    from backend.engine.llm_gateway import llm_call

    _ = max_retries
    _ = timeout
    return llm_call(
        agent_name="legacy_llm_client",
        model=_DEFAULT_LEGACY_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=8192,
        temperature=0.3,
    )


def call_llm(prompt: str):
    """
    Legacy sync helper that returns parsed JSON when possible.
    """
    raw = nim_chat(prompt)
    if raw is None:
        return None
    parsed = extract_json_from_text(raw)
    return parsed if parsed is not None else raw


def call_ollama(prompt: str):
    """Backward-compat alias."""
    return call_llm(prompt)


__all__ = [
    "LLMClient",
    "LLMClientError",
    "extract_json_from_text",
    "nim_chat",
    "call_llm",
    "call_ollama",
]

"""
Central model router for role-bound agent calls.

Agents must never call LLM providers directly. All model calls go through this
router so model binding, retries, JSON parsing, and token-usage logging stay
consistent.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import os
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict

from backend.core.llm_client import LLMClient, extract_json_from_text
from backend.engine.token_ledger import ledger


logger = logging.getLogger(__name__)


class ModelRouterError(RuntimeError):
    """Raised when a model call fails or returns invalid output."""


@dataclass(frozen=True)
class ModelCallConfig:
    """Model call config for one role."""

    provider: str
    model: str
    temperature: float
    top_p: float
    max_tokens: int


class ModelRouter:
    """Role-based model router with retry, JSON enforcement, and usage logs."""

    def __init__(
        self,
        max_retries: int = 3,
        retry_backoff_seconds: float = 0.75,
        llm_client: LLMClient | None = None,
        on_token: Callable[[str, str], Awaitable[None] | None] | None = None,
    ):
        # Hard-cap retries to 3 per requirements.
        self.max_retries = max(1, min(int(max_retries), 3))
        self.retry_backoff_seconds = max(0.0, float(retry_backoff_seconds))
        self.client = llm_client or LLMClient(max_retries=3)
        self.on_token = on_token
        default_model = os.getenv("NIM_MODEL", "moonshotai/kimi-k2-thinking")

        self.team_lead = ModelCallConfig(
            provider="kimi",
            model=os.getenv("TEAM_LEAD_MODEL", default_model),
            temperature=0.2,
            top_p=0.85,
            max_tokens=8000,
        )
        self.backend_engineer = ModelCallConfig(
            provider="kimi",
            model=os.getenv("BACKEND_ENGINEER_MODEL", default_model),
            temperature=0.2,
            top_p=0.85,
            max_tokens=16000,
        )
        self.frontend_engineer = ModelCallConfig(
            provider="kimi",
            model=os.getenv("FRONTEND_ENGINEER_MODEL", default_model),
            temperature=0.2,
            top_p=0.85,
            max_tokens=16000,
        )
        self.database_engineer = ModelCallConfig(
            provider="kimi",
            model=os.getenv("DATABASE_ENGINEER_MODEL", default_model),
            temperature=0.2,
            top_p=0.85,
            max_tokens=8000,
        )
        self.qa_engineer = ModelCallConfig(
            provider="kimi",
            model=os.getenv("QA_ENGINEER_MODEL", default_model),
            temperature=0.1,
            top_p=0.8,
            max_tokens=6000,
        )

    async def call_team_lead(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        return await self._call_json("team_lead", self.team_lead, prompt, system_prompt)

    async def call_backend_engineer(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        return await self._call_json("backend_engineer", self.backend_engineer, prompt, system_prompt)

    async def call_frontend_engineer(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        return await self._call_json("frontend_engineer", self.frontend_engineer, prompt, system_prompt)

    async def call_database_engineer(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        return await self._call_json("database_engineer", self.database_engineer, prompt, system_prompt)

    async def call_qa_engineer(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        return await self._call_json("qa_engineer", self.qa_engineer, prompt, system_prompt)

    async def _call_json(
        self,
        agent_name: str,
        config: ModelCallConfig,
        prompt: str,
        system_prompt: str,
    ) -> Dict[str, Any]:
        last_error: Exception | None = None
        messages = [
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": prompt},
        ]

        for attempt in range(1, self.max_retries + 1):
            try:
                response = await self.client.complete(
                    provider=config.provider,
                    model=config.model,
                    messages=messages,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                    top_p=config.top_p,
                    agent_name=agent_name,
                    on_token=lambda token: self._emit_token(agent_name, token),
                )
                if not response:
                    raise ModelRouterError(f"empty response from model '{config.model}'")

                payload = self._parse_json_object(response)
                self._log_token_usage(agent_name)
                return payload
            except ModelRouterError:
                # JSON parse failures — retry with backoff (model may produce valid JSON on next attempt)
                last_error = ModelRouterError(f"JSON parse failed on attempt {attempt}")
                logger.warning("model_router JSON parse error agent=%s attempt=%d/%d", agent_name, attempt, self.max_retries)
                if attempt >= self.max_retries:
                    break
                await asyncio.sleep(self.retry_backoff_seconds * (2 ** (attempt - 1)))
            except (ConnectionError, TimeoutError, OSError) as exc:
                last_error = exc
                logger.warning("model_router network error agent=%s attempt=%d/%d: %s", agent_name, attempt, self.max_retries, exc)
                if attempt >= self.max_retries:
                    break
                await asyncio.sleep(self.retry_backoff_seconds * (2 ** (attempt - 1)))
            except Exception as exc:
                # Non-retryable errors (auth, missing key, circuit open) — fail immediately
                raise ModelRouterError(f"{agent_name} failed: {exc}") from exc

        detail = str(last_error) if last_error else "unknown model router failure"
        raise ModelRouterError(f"{agent_name} failed after {self.max_retries} attempts: {detail}")

    @staticmethod
    def _parse_json_object(response: Any) -> Dict[str, Any]:
        if isinstance(response, dict):
            return response

        if isinstance(response, str):
            parsed = extract_json_from_text(response)
            if isinstance(parsed, dict):
                return parsed

        raise ModelRouterError("model response is not a valid JSON object")

    async def _emit_token(self, agent_name: str, token: str) -> None:
        if not self.on_token:
            return
        maybe = self.on_token(agent_name, token)
        if inspect.isawaitable(maybe):
            await maybe

    @staticmethod
    def _log_token_usage(agent_name: str) -> None:
        usage = ledger.by_agent.get(agent_name, {})
        logger.info(
            "model_router usage agent=%s calls=%s input=%s output=%s total=%s cost=%s",
            agent_name,
            usage.get("call_count", 0),
            usage.get("input_tokens", 0),
            usage.get("output_tokens", 0),
            usage.get("total_tokens", 0),
            usage.get("cost_usd", 0.0),
        )

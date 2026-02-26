"""
/api/nim/test — NIM model connectivity probe

Tests all 5 agent roles sequentially with a minimal prompt.
Returns per-role pass/fail status, latency, and the model name used.

Usage:
    GET /api/nim/test              — test all roles
    GET /api/nim/test?role=team_lead  — test a single role
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from backend.engine.nim_client import get_nim_client, get_model_for_role, AGENT_MODEL_MAP
from backend.engine.model_config import get_all_role_configs

logger = logging.getLogger("nim_test")

router = APIRouter(prefix="/api/nim", tags=["NIM"])

# Minimal test prompt — we just want a 1-token reply to confirm connectivity
_PROBE_MESSAGES = [
    {"role": "system", "content": "You are a test assistant. Reply with only the word OK."},
    {"role": "user",   "content": "Are you connected?"},
]


async def _probe_role(role: str) -> dict:
    """
    Fire a minimal completion for one role.
    Returns a result dict regardless of success or failure.
    """
    model = get_model_for_role(role)
    client = get_nim_client()
    t0 = time.monotonic()

    try:
        reply = await client.complete(
            role=role,
            messages=_PROBE_MESSAGES,
            max_tokens=10,   # we only need 1-3 tokens — keep it cheap
        )
        latency_ms = round((time.monotonic() - t0) * 1000)
        return {
            "role":       role,
            "model":      model,
            "status":     "ok",
            "reply":      reply[:100],   # truncate — we don't need more
            "latency_ms": latency_ms,
        }
    except Exception as exc:
        latency_ms = round((time.monotonic() - t0) * 1000)
        logger.warning("[nim_test] role=%s FAILED: %s", role, exc)
        return {
            "role":       role,
            "model":      model,
            "status":     "error",
            "error":      str(exc)[:300],
            "latency_ms": latency_ms,
        }


@router.get("/test")
async def nim_test(
    role: Optional[str] = Query(
        default=None,
        description="Specific role to test. If omitted, all 5 roles are tested.",
    )
):
    """
    Probe NIM model connectivity for all agent roles (or one specific role).

    Response shape:
    ```json
    {
        "summary": { "total": 5, "ok": 4, "failed": 1 },
        "results": [
            { "role": "team_lead", "model": "moonshotai/kimi-k2-thinking",
              "status": "ok", "reply": "OK", "latency_ms": 823 },
            ...
        ]
    }
    ```
    """
    roles_to_test: list[str]

    if role:
        if role not in AGENT_MODEL_MAP:
            return JSONResponse(
                status_code=400,
                content={
                    "error": f"Unknown role '{role}'.",
                    "valid_roles": list(AGENT_MODEL_MAP.keys()),
                },
            )
        roles_to_test = [role]
    else:
        roles_to_test = list(AGENT_MODEL_MAP.keys())

    # Run probes concurrently — all models share the same key for now
    tasks = [_probe_role(r) for r in roles_to_test]
    results = await asyncio.gather(*tasks)

    ok_count    = sum(1 for r in results if r["status"] == "ok")
    failed_count = len(results) - ok_count

    return {
        "summary": {
            "total":  len(results),
            "ok":     ok_count,
            "failed": failed_count,
        },
        "results": results,
    }


@router.get("/config")
async def nim_config():
    """
    Return the current NIM model configuration (no secrets — models and params only).
    Useful for verifying .env settings and seeing optimal parameters per role.
    """
    return {
        "base_url": "https://integrate.api.nvidia.com/v1",
        "roles": get_all_role_configs(),
    }

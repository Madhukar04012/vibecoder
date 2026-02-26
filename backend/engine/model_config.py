"""
Model Configuration — Centralized per-model optimal parameters for NVIDIA NIM.

Each model in the high-performance stack has its own optimal temperature,
top_p, max_tokens, and feature flags (thinking, streaming, etc.).

This file is the SINGLE SOURCE OF TRUTH for model parameters.
Both nim_client.py and llm_gateway.py import from here.

Stack:
  TEAM_LEAD        → nvidia/llama-3.3-nemotron-super-49b-v1               (planning & orchestration)
  BACKEND_ENGINEER → mistralai/devstral-2-123b-instruct-2512              (FastAPI code generation)
  FRONTEND_ENGINEER→ qwen/qwen2.5-coder-32b-instruct                     (React/TS code generation)
  DATABASE_ENGINEER→ meta/llama-3.3-70b-instruct                          (schema & SQL reasoning)
  QA_ENGINEER      → qwen/qwq-32b                                         (validation & reasoning)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

from dotenv import load_dotenv

# Ensure .env is loaded
_root = Path(__file__).resolve().parent.parent.parent
_env = _root / ".env"
if _env.exists():
    load_dotenv(_env, override=True)


# ── Model Profile ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ModelProfile:
    """Optimal parameters for a specific NIM model."""
    model_id: str                     # NIM model identifier (org/name)
    temperature: float = 0.3          # Sampling temperature
    top_p: float = 0.9                # Nucleus sampling
    max_tokens: int = 4096            # Default max output tokens
    supports_thinking: bool = False   # Has reasoning_content in delta
    supports_streaming: bool = True   # Supports stream=True
    context_window: int = 32768       # Max context length
    description: str = ""             # Human-readable description


# ── Model Profiles Database ───────────────────────────────────────────────────
# Optimal parameters tuned for each model's architecture and strengths.

MODEL_PROFILES: Dict[str, ModelProfile] = {
    # Nemotron Super 49B — excellent at structured planning, instruction following
    "nvidia/llama-3.3-nemotron-super-49b-v1": ModelProfile(
        model_id="nvidia/llama-3.3-nemotron-super-49b-v1",
        temperature=0.5,
        top_p=0.92,
        max_tokens=4096,
        supports_thinking=False,
        context_window=131072,
        description="Nemotron Super 49B — planning & orchestration specialist",
    ),
    # Devstral 2 123B — Mistral's developer model, precise code generation (0.27s latency)
    "mistralai/devstral-2-123b-instruct-2512": ModelProfile(
        model_id="mistralai/devstral-2-123b-instruct-2512",
        temperature=0.15,
        top_p=0.9,
        max_tokens=16384,
        supports_thinking=False,
        context_window=131072,
        description="Devstral 2 123B — backend code generation specialist",
    ),
    # Qwen 2.5 Coder 32B — fast, high-quality code model for frontend (0.21s latency)
    "qwen/qwen2.5-coder-32b-instruct": ModelProfile(
        model_id="qwen/qwen2.5-coder-32b-instruct",
        temperature=0.15,
        top_p=0.9,
        max_tokens=16384,
        supports_thinking=False,
        context_window=131072,
        description="Qwen 2.5 Coder 32B — frontend/UI code generation specialist",
    ),
    # Llama 3.3 70B — fast, reliable instruction-following for schema design (0.77s latency)
    "meta/llama-3.3-70b-instruct": ModelProfile(
        model_id="meta/llama-3.3-70b-instruct",
        temperature=0.2,
        top_p=0.9,
        max_tokens=8192,
        supports_thinking=False,
        context_window=131072,
        description="Llama 3.3 70B — database schema & SQL specialist",
    ),
    # QWQ 32B — Qwen's reasoning model, excellent for QA validation
    "qwen/qwq-32b": ModelProfile(
        model_id="qwen/qwq-32b",
        temperature=0.3,
        top_p=0.95,
        max_tokens=2048,          # Reduced for faster validation responses
        supports_thinking=True,   # QWQ has built-in reasoning
        context_window=131072,
        description="QWQ 32B — QA validation & reasoning specialist",
    ),
    # Fallback: Kimi K2 Thinking (previous default)
    "moonshotai/kimi-k2-thinking": ModelProfile(
        model_id="moonshotai/kimi-k2-thinking",
        temperature=1.0,
        top_p=0.9,
        max_tokens=8192,
        supports_thinking=True,
        context_window=131072,
        description="Kimi K2 Thinking — general-purpose reasoning model",
    ),
}


# ── Role → Model Mapping ──────────────────────────────────────────────────────
# Maps each agent role to: (env_var_name, default_model_id)

ROLE_MODEL_DEFAULTS: Dict[str, tuple[str, str]] = {
    "team_lead":         ("TEAM_LEAD_MODEL",         "nvidia/llama-3.3-nemotron-super-49b-v1"),
    "backend_engineer":  ("BACKEND_ENGINEER_MODEL",  "mistralai/devstral-2-123b-instruct-2512"),
    "frontend_engineer": ("FRONTEND_ENGINEER_MODEL", "qwen/qwen2.5-coder-32b-instruct"),
    "database_engineer": ("DATABASE_ENGINEER_MODEL", "meta/llama-3.3-70b-instruct"),
    "qa_engineer":       ("QA_ENGINEER_MODEL",       "qwen/qwq-32b"),
}

# Chat mode uses the team_lead model for general conversation
CHAT_MODEL_ENV = "NIM_MODEL"
CHAT_MODEL_DEFAULT = "nvidia/llama-3.3-nemotron-super-49b-v1"

# Code generation mode uses the backend model for file generation
CODER_MODEL_ENV = "NIM_CODER_MODEL"
CODER_MODEL_DEFAULT = "mistralai/devstral-2-123b-instruct-2512"


# ── Public API ─────────────────────────────────────────────────────────────────

def get_model_for_role(role: str) -> str:
    """Return the configured model name for an agent role (reads from .env)."""
    if role not in ROLE_MODEL_DEFAULTS:
        # Fallback for unknown roles
        return os.getenv("NIM_MODEL", CHAT_MODEL_DEFAULT)
    env_var, fallback = ROLE_MODEL_DEFAULTS[role]
    return os.getenv(env_var, fallback)


def get_profile_for_role(role: str) -> ModelProfile:
    """Return the full ModelProfile for an agent role."""
    model_id = get_model_for_role(role)
    return get_profile(model_id)


def get_profile(model_id: str) -> ModelProfile:
    """Return the ModelProfile for a specific model ID. Falls back to sensible defaults."""
    if model_id in MODEL_PROFILES:
        return MODEL_PROFILES[model_id]

    # Partial match (e.g., model ID variants)
    for key, profile in MODEL_PROFILES.items():
        if key in model_id or model_id in key:
            return profile

    # Unknown model — return conservative defaults
    return ModelProfile(
        model_id=model_id,
        temperature=0.3,
        top_p=0.9,
        max_tokens=4096,
        supports_thinking=False,
        description=f"Unknown model: {model_id}",
    )


def get_temperature_for_role(role: str) -> float:
    """Return the optimal temperature for an agent role's model."""
    return get_profile_for_role(role).temperature


def get_top_p_for_role(role: str) -> float:
    """Return the optimal top_p for an agent role's model."""
    return get_profile_for_role(role).top_p


def get_max_tokens_for_role(role: str) -> int:
    """Return the default max_tokens for an agent role's model."""
    return get_profile_for_role(role).max_tokens


def supports_thinking(role: str) -> bool:
    """Return whether the model for this role supports reasoning_content."""
    return get_profile_for_role(role).supports_thinking


def get_chat_model() -> str:
    """Return the model used for general chat (non-code) conversations."""
    return os.getenv(CHAT_MODEL_ENV, CHAT_MODEL_DEFAULT)


def get_coder_model() -> str:
    """Return the model used for code generation in SSE chat_stream."""
    return os.getenv(CODER_MODEL_ENV, CODER_MODEL_DEFAULT)


def get_all_role_configs() -> Dict[str, dict]:
    """Return a summary of all role → model configurations (no secrets)."""
    configs = {}
    for role, (env_var, _) in ROLE_MODEL_DEFAULTS.items():
        model_id = get_model_for_role(role)
        profile = get_profile(model_id)
        configs[role] = {
            "env_var": env_var,
            "model": model_id,
            "temperature": profile.temperature,
            "top_p": profile.top_p,
            "max_tokens": profile.max_tokens,
            "supports_thinking": profile.supports_thinking,
            "description": profile.description,
        }
    return configs

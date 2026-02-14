"""
Structured observability for pipeline runs.

Writes JSON lines run logs and aggregates per-agent reliability metrics.
"""

from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


LOG_DIR = Path("run_logs")
AGENT_STATS_FILE = LOG_DIR / "agent_stats.json"
_LOCK = threading.Lock()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_log_dir() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class AgentMetrics:
    agent: str
    status: str
    attempt: int
    retries: int
    duration_ms: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    error: str | None = None


class RunLogger:
    """JSONL run logger used by PipelineRunner."""

    def __init__(self, run_id: str, project_id: str | None = None, user_id: str | None = None):
        _ensure_log_dir()
        self.run_id = run_id
        self.project_id = project_id
        self.user_id = user_id
        self.path = LOG_DIR / f"{run_id}.jsonl"

    def log(self, event: str, payload: Dict[str, Any]) -> None:
        record = {
            "ts": _utc_now(),
            "run_id": self.run_id,
            "project_id": self.project_id,
            "user_id": self.user_id,
            "event": event,
            "payload": payload,
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")

    def log_agent_metrics(self, metrics: AgentMetrics) -> None:
        self.log("agent_metrics", asdict(metrics))
        _update_agent_stats(metrics)


def _load_agent_stats() -> Dict[str, Any]:
    if not AGENT_STATS_FILE.exists():
        return {"updated_at": _utc_now(), "agents": {}}

    try:
        return json.loads(AGENT_STATS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"updated_at": _utc_now(), "agents": {}}


def _update_agent_stats(metrics: AgentMetrics) -> None:
    with _LOCK:
        _ensure_log_dir()
        stats = _load_agent_stats()
        agents = stats.setdefault("agents", {})
        agent = agents.setdefault(
            metrics.agent,
            {
                "runs": 0,
                "failures": 0,
                "total_duration_ms": 0.0,
                "avg_duration_ms": 0.0,
                "last_status": None,
                "failure_rate": 0.0,
                "last_error": None,
                "last_updated": None,
            },
        )

        agent["runs"] += 1
        if metrics.status != "success":
            agent["failures"] += 1
            agent["last_error"] = metrics.error

        agent["total_duration_ms"] += metrics.duration_ms
        agent["avg_duration_ms"] = round(
            agent["total_duration_ms"] / max(agent["runs"], 1), 3
        )
        agent["failure_rate"] = round(
            agent["failures"] / max(agent["runs"], 1), 4
        )
        agent["last_status"] = metrics.status
        agent["last_updated"] = _utc_now()

        stats["updated_at"] = _utc_now()
        AGENT_STATS_FILE.write_text(json.dumps(stats, indent=2), encoding="utf-8")


def get_agent_stats() -> Dict[str, Any]:
    """Return aggregate agent observability stats."""
    with _LOCK:
        return _load_agent_stats()

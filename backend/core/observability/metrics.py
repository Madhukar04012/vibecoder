"""
Metrics collector — agent executions, duration, tokens, costs (Plan Phase 3.4).

Lightweight in-process metrics. No external dependencies (Prometheus optional).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class ExecutionRecord:
    agent: str
    status: str
    duration_sec: float
    tokens: int = 0
    cost_usd: float = 0.0
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class MetricsCollector:
    """Collect system metrics for all agent executions."""

    _records: List[ExecutionRecord] = field(default_factory=list)

    def record_execution(
        self,
        agent_name: str,
        status: str = "ok",
        duration_sec: float = 0.0,
        tokens: int = 0,
        cost_usd: float = 0.0,
    ) -> None:
        self._records.append(
            ExecutionRecord(
                agent=agent_name,
                status=status,
                duration_sec=duration_sec,
                tokens=tokens,
                cost_usd=cost_usd,
            )
        )

    def get_stats(self) -> Dict[str, Any]:
        by_agent: Dict[str, List[ExecutionRecord]] = {}
        for r in self._records:
            by_agent.setdefault(r.agent, []).append(r)

        executions: Dict[str, int] = {}
        avg_duration: Dict[str, float] = {}
        success_rate: Dict[str, float] = {}
        tokens_by_agent: Dict[str, int] = {}
        cost_by_agent: Dict[str, float] = {}

        for agent, records in by_agent.items():
            executions[agent] = len(records)
            durations = [r.duration_sec for r in records]
            avg_duration[agent] = round(sum(durations) / len(durations), 2) if durations else 0
            ok_count = sum(1 for r in records if r.status == "ok")
            success_rate[agent] = round(ok_count / len(records), 2) if records else 0
            tokens_by_agent[agent] = sum(r.tokens for r in records)
            cost_by_agent[agent] = round(sum(r.cost_usd for r in records), 4)

        return {
            "total_executions": len(self._records),
            "executions_by_agent": executions,
            "avg_duration_by_agent": avg_duration,
            "success_rate_by_agent": success_rate,
            "tokens_by_agent": tokens_by_agent,
            "cost_by_agent": cost_by_agent,
            "total_cost": round(sum(r.cost_usd for r in self._records), 4),
        }

    def get_recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        return [
            {
                "agent": r.agent,
                "status": r.status,
                "duration_sec": round(r.duration_sec, 2),
                "tokens": r.tokens,
                "cost_usd": r.cost_usd,
                "timestamp": r.timestamp,
            }
            for r in self._records[-limit:]
        ]

    def clear(self) -> None:
        self._records.clear()

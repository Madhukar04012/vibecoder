"""
Workflow tracer — span-based tracing for agent executions (Plan Phase 3.4).

Provides lightweight tracing without requiring OpenTelemetry.
Each agent execution is a span with timing, status, and metadata.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, Generator, List, Optional


class Span:
    """A single trace span representing an agent execution."""

    __slots__ = ("agent", "task", "status", "error", "start_time", "end_time", "metadata")

    def __init__(self, agent: str, task: str) -> None:
        self.agent = agent
        self.task = task
        self.status = "running"
        self.error: Optional[str] = None
        self.start_time = datetime.now(timezone.utc)
        self.end_time: Optional[datetime] = None
        self.metadata: Dict[str, Any] = {}

    @property
    def duration_ms(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent": self.agent,
            "task": self.task,
            "status": self.status,
            "error": self.error,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": round(self.duration_ms, 1),
            "metadata": self.metadata,
        }


class WorkflowTracer:
    """Distributed tracing for multi-agent workflows."""

    def __init__(self) -> None:
        self._spans: List[Span] = []

    @contextmanager
    def trace_agent_execution(self, agent_name: str, task: str) -> Generator[Span, None, None]:
        """Trace an agent execution as a span."""
        span = Span(agent_name, task)
        self._spans.append(span)
        try:
            yield span
        except Exception as e:
            span.status = "error"
            span.error = str(e)
            raise
        else:
            span.status = "ok"
        finally:
            span.end_time = datetime.now(timezone.utc)

    def trace_document_flow(self, doc_id: str, doc_type: str, agent: str) -> None:
        """Record a document creation event."""
        span = Span(agent, f"document:{doc_type}")
        span.metadata = {"doc_id": doc_id, "doc_type": doc_type}
        span.status = "ok"
        span.end_time = datetime.now(timezone.utc)
        self._spans.append(span)

    def get_spans(self) -> List[Dict[str, Any]]:
        return [s.to_dict() for s in self._spans]

    def get_spans_for_agent(self, agent_name: str) -> List[Dict[str, Any]]:
        return [s.to_dict() for s in self._spans if s.agent == agent_name]

    def get_error_spans(self) -> List[Dict[str, Any]]:
        return [s.to_dict() for s in self._spans if s.status == "error"]

    def clear(self) -> None:
        self._spans.clear()

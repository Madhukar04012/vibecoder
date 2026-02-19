"""
Prometheus Metrics - Production observability (Phase 3.2)

Exports metrics for Prometheus monitoring including:
- Agent execution metrics
- Token usage and costs
- Pipeline performance
- Error rates
- Document flow metrics
"""

from __future__ import annotations

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timezone
import time

# Try to import prometheus_client, fallback to mock if not available
try:
    from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Mock classes for when prometheus_client is not installed
    class Counter:
        def __init__(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
    class Histogram:
        def __init__(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
    class Gauge:
        def __init__(self, *args, **kwargs): pass
        def set(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass
        def dec(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
    class Info:
        def __init__(self, *args, **kwargs): pass
        def info(self, *args, **kwargs): pass
    def generate_latest(*args): return b""
    CONTENT_TYPE_LATEST = "text/plain"


@dataclass
class MetricSnapshot:
    """Snapshot of metrics at a point in time."""
    timestamp: datetime
    agent_executions: Dict[str, int]
    total_cost: float
    total_tokens: int
    active_runs: int
    success_rate: float
    avg_duration: float


class PrometheusMetrics:
    """
    Prometheus metrics exporter for VibeCober.
    
    Tracks:
    - Agent performance
    - Pipeline execution
    - Token usage and costs
    - Document flow
    - Error rates
    """

    def __init__(self):
        self._initialized = False
        self._initialize_metrics()

    def _initialize_metrics(self):
        """Initialize all Prometheus metrics."""
        if self._initialized:
            return

        # Agent execution metrics
        self.agent_executions_total = Counter(
            'vibecober_agent_executions_total',
            'Total agent executions',
            ['agent_name', 'status']
        )

        self.agent_execution_duration = Histogram(
            'vibecober_agent_execution_duration_seconds',
            'Agent execution duration in seconds',
            ['agent_name'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0]
        )

        self.agent_execution_errors = Counter(
            'vibecober_agent_execution_errors_total',
            'Total agent execution errors',
            ['agent_name', 'error_type']
        )

        # Pipeline metrics
        self.pipeline_executions_total = Counter(
            'vibecober_pipeline_executions_total',
            'Total pipeline executions',
            ['mode', 'status']
        )

        self.pipeline_duration = Histogram(
            'vibecober_pipeline_duration_seconds',
            'Pipeline execution duration',
            ['mode'],
            buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0]
        )

        self.active_runs = Gauge(
            'vibecober_active_runs',
            'Number of currently active runs'
        )

        # Token and cost metrics
        self.tokens_used_total = Counter(
            'vibecober_tokens_used_total',
            'Total tokens used',
            ['agent_name', 'model', 'token_type']
        )

        self.cost_usd_total = Counter(
            'vibecober_cost_usd_total',
            'Total cost in USD',
            ['agent_name', 'model']
        )

        self.daily_budget_remaining = Gauge(
            'vibecober_daily_budget_remaining_usd',
            'Remaining daily budget in USD',
            ['tier']
        )

        # Document metrics
        self.documents_created_total = Counter(
            'vibecober_documents_created_total',
            'Total documents created',
            ['doc_type', 'agent_name']
        )

        self.documents_by_status = Gauge(
            'vibecober_documents_by_status',
            'Number of documents by status',
            ['status']
        )

        # API metrics
        self.api_requests_total = Counter(
            'vibecober_api_requests_total',
            'Total API requests',
            ['endpoint', 'method', 'status_code']
        )

        self.api_request_duration = Histogram(
            'vibecober_api_request_duration_seconds',
            'API request duration',
            ['endpoint'],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]
        )

        # Memory metrics
        self.memory_operations_total = Counter(
            'vibecober_memory_operations_total',
            'Total memory operations',
            ['operation_type']
        )

        self.memory_size_bytes = Gauge(
            'vibecober_memory_size_bytes',
            'Memory usage in bytes',
            ['scope']
        )

        # Build info
        self.build_info = Info(
            'vibecober_build',
            'VibeCober build information'
        )
        self.build_info.info({
            'version': '0.7.0',
            'python_version': '3.11',
        })

        self._initialized = True

    def record_agent_execution(
        self,
        agent_name: str,
        status: str,
        duration_seconds: float,
    ) -> None:
        """Record an agent execution."""
        self.agent_executions_total.labels(
            agent_name=agent_name,
            status=status
        ).inc()

        self.agent_execution_duration.labels(
            agent_name=agent_name
        ).observe(duration_seconds)

    def record_agent_error(
        self,
        agent_name: str,
        error_type: str,
    ) -> None:
        """Record an agent error."""
        self.agent_execution_errors.labels(
            agent_name=agent_name,
            error_type=error_type
        ).inc()

    def record_pipeline_execution(
        self,
        mode: str,
        status: str,
        duration_seconds: float,
    ) -> None:
        """Record a pipeline execution."""
        self.pipeline_executions_total.labels(
            mode=mode,
            status=status
        ).inc()

        self.pipeline_duration.labels(
            mode=mode
        ).observe(duration_seconds)

    def update_active_runs(self, count: int) -> None:
        """Update the number of active runs."""
        self.active_runs.set(count)

    def record_token_usage(
        self,
        agent_name: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        """Record token usage."""
        self.tokens_used_total.labels(
            agent_name=agent_name,
            model=model,
            token_type='input'
        ).inc(input_tokens)

        self.tokens_used_total.labels(
            agent_name=agent_name,
            model=model,
            token_type='output'
        ).inc(output_tokens)

    def record_cost(
        self,
        agent_name: str,
        model: str,
        cost_usd: float,
    ) -> None:
        """Record cost in USD."""
        self.cost_usd_total.labels(
            agent_name=agent_name,
            model=model
        ).inc(cost_usd)

    def update_budget_remaining(self, tier: str, amount_usd: float) -> None:
        """Update remaining budget."""
        self.daily_budget_remaining.labels(tier=tier).set(amount_usd)

    def record_document_created(
        self,
        doc_type: str,
        agent_name: str,
    ) -> None:
        """Record document creation."""
        self.documents_created_total.labels(
            doc_type=doc_type,
            agent_name=agent_name
        ).inc()

    def update_document_status(self, status: str, count: int) -> None:
        """Update document count by status."""
        self.documents_by_status.labels(status=status).set(count)

    def record_api_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        duration_seconds: float,
    ) -> None:
        """Record an API request."""
        self.api_requests_total.labels(
            endpoint=endpoint,
            method=method,
            status_code=str(status_code)
        ).inc()

        self.api_request_duration.labels(
            endpoint=endpoint
        ).observe(duration_seconds)

    def record_memory_operation(self, operation_type: str) -> None:
        """Record a memory operation."""
        self.memory_operations_total.labels(
            operation_type=operation_type
        ).inc()

    def update_memory_size(self, scope: str, size_bytes: int) -> None:
        """Update memory size."""
        self.memory_size_bytes.labels(scope=scope).set(size_bytes)

    def get_metrics(self) -> bytes:
        """Get all metrics in Prometheus format."""
        return generate_latest()

    def get_snapshot(self) -> MetricSnapshot:
        """Get a snapshot of current metrics."""
        # This is a simplified snapshot - in production you'd track these values
        return MetricSnapshot(
            timestamp=datetime.now(timezone.utc),
            agent_executions={},
            total_cost=0.0,
            total_tokens=0,
            active_runs=0,
            success_rate=0.0,
            avg_duration=0.0,
        )


# Global metrics instance
_metrics: Optional[PrometheusMetrics] = None


def get_metrics() -> PrometheusMetrics:
    """Get or create the global metrics instance."""
    global _metrics
    if _metrics is None:
        _metrics = PrometheusMetrics()
    return _metrics

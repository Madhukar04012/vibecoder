"""Learning module for self-improvement and failure analysis."""

from .failure_analyzer import (
    FailureAnalyzer,
    ExecutionFailure,
    FailureAnalysis,
    FailureCategory,
    FailureSeverity,
    FailurePattern,
)
from .improvement_engine import (
    ContinuousImprovementEngine,
    Improvement,
    ImprovementStatus,
    ImprovementRisk,
    PerformanceMetrics,
)

__all__ = [
    # Failure Analysis (enhanced)
    "FailureAnalyzer",
    "ExecutionFailure",
    "FailureAnalysis",
    "FailureCategory",
    "FailureSeverity",
    "FailurePattern",
    # Improvement Engine (enhanced)
    "ContinuousImprovementEngine",
    "Improvement",
    "ImprovementStatus",
    "ImprovementRisk",
    "PerformanceMetrics",
]
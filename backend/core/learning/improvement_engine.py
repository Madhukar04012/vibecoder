"""
Continuous Improvement Engine - Advanced self-improvement system (Phase 2.4)

Analyzes system performance, identifies improvement opportunities, and 
automatically applies safe optimizations.
"""

from __future__ import annotations

import json
import asyncio
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from collections import defaultdict

from backend.engine.llm_gateway import llm_call_simple


class ImprovementStatus(str, Enum):
    """Status of an improvement."""
    PENDING = "pending"
    APPROVED = "approved"
    APPLIED = "applied"
    REJECTED = "rejected"
    FAILED = "failed"


class ImprovementRisk(str, Enum):
    """Risk level of an improvement."""
    LOW = "low"       # Safe to auto-apply
    MEDIUM = "medium" # Needs review
    HIGH = "high"     # Manual approval required


@dataclass
class Improvement:
    """A suggested system improvement."""
    improvement_id: str
    description: str
    category: str  # "prompt", "workflow", "configuration", "architecture"
    target_agent: Optional[str]
    current_value: str
    proposed_value: str
    expected_impact: Dict[str, Any]  # {"success_rate": +0.05, "cost": -0.10}
    auto_apply: bool
    confidence: float  # 0.0 - 1.0
    risk: ImprovementRisk
    status: ImprovementStatus = ImprovementStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    applied_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "improvement_id": self.improvement_id,
            "description": self.description,
            "category": self.category,
            "target_agent": self.target_agent,
            "current_value": self.current_value,
            "proposed_value": self.proposed_value,
            "expected_impact": self.expected_impact,
            "auto_apply": self.auto_apply,
            "confidence": self.confidence,
            "risk": self.risk.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "applied_at": self.applied_at.isoformat() if self.applied_at else None,
            "result": self.result,
        }


@dataclass
class PerformanceMetrics:
    """Performance metrics for a time period."""
    period_start: datetime
    period_end: datetime
    total_runs: int
    success_count: int
    failure_count: int
    avg_duration: float
    total_cost: float
    by_agent: Dict[str, Dict[str, Any]]
    common_failures: List[Dict[str, Any]]
    bottlenecks: List[str]


class ContinuousImprovementEngine:
    """
    Advanced continuous improvement system.
    
    Features:
    - Comprehensive performance analysis
    - LLM-powered improvement generation
    - Automatic application of safe improvements
    - A/B testing framework
    - Rollback capability
    """

    IMPROVEMENT_PROMPT = """Analyze this system performance data and suggest concrete improvements.

PERFORMANCE DATA:
{metrics_json}

FAILURE PATTERNS:
{failure_patterns}

Generate improvements as JSON:
{{
  "improvements": [
    {{
      "description": "Clear description of what to change",
      "category": "prompt|workflow|configuration|architecture",
      "target_agent": "agent_name or null",
      "current_value": "Current state",
      "proposed_value": "Proposed change",
      "expected_impact": {{"success_rate": 0.05, "cost": -0.10}},
      "confidence": 0.85,
      "risk": "low|medium|high",
      "reasoning": "Why this will help"
    }}
  ]
}}

Focus on:
1. Prompt engineering improvements for low-performing agents
2. Workflow optimizations for bottlenecks
3. Cost reduction opportunities
4. Quality improvements

Only suggest high-confidence improvements with clear expected impact."""

    def __init__(
        self,
        auto_apply_threshold: float = 0.8,
        min_confidence: float = 0.7,
        max_improvements_per_cycle: int = 5,
    ):
        self.auto_apply_threshold = auto_apply_threshold
        self.min_confidence = min_confidence
        self.max_improvements_per_cycle = max_improvements_per_cycle
        
        # Storage
        self._metrics: List[Dict[str, Any]] = []
        self._improvements: List[Improvement] = []
        self._applied_improvements: List[Improvement] = []
        
        # Analysis history
        self._analysis_history: List[Dict[str, Any]] = []
        
        # Callbacks for applying improvements
        self._improvement_callbacks: Dict[str, Callable] = {}

    def register_improvement_callback(
        self, 
        category: str, 
        callback: Callable[[Improvement], bool]
    ) -> None:
        """Register a callback to apply improvements of a specific category."""
        self._improvement_callbacks[category] = callback

    def record_metric(
        self,
        agent: str,
        success: bool,
        duration_sec: float,
        cost_usd: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a performance metric."""
        self._metrics.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent": agent,
            "success": success,
            "duration_sec": duration_sec,
            "cost_usd": cost_usd,
            "metadata": metadata or {},
        })

    def get_metrics_for_period(
        self,
        days: int = 7,
    ) -> PerformanceMetrics:
        """Get aggregated metrics for a time period."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Filter recent metrics
        recent = [
            m for m in self._metrics
            if datetime.fromisoformat(m["timestamp"]) > cutoff
        ]
        
        if not recent:
            return PerformanceMetrics(
                period_start=cutoff,
                period_end=datetime.now(timezone.utc),
                total_runs=0,
                success_count=0,
                failure_count=0,
                avg_duration=0.0,
                total_cost=0.0,
                by_agent={},
                common_failures=[],
                bottlenecks=[],
            )

        # Aggregate by agent
        by_agent: Dict[str, List[Dict]] = defaultdict(list)
        for m in recent:
            by_agent[m["agent"]].append(m)

        # Calculate agent stats
        agent_stats = {}
        for agent, runs in by_agent.items():
            success_count = sum(1 for r in runs if r["success"])
            total_duration = sum(r["duration_sec"] for r in runs)
            total_cost = sum(r.get("cost_usd", 0.0) for r in runs)
            
            agent_stats[agent] = {
                "runs": len(runs),
                "success_rate": success_count / len(runs),
                "avg_duration": total_duration / len(runs),
                "total_cost": total_cost,
            }

        # Identify bottlenecks (agents with high duration)
        bottlenecks = [
            agent for agent, stats in agent_stats.items()
            if stats["avg_duration"] > 30.0  # > 30 seconds
        ]

        # Find common failures
        failures = [m for m in recent if not m["success"]]
        failure_types = defaultdict(int)
        for f in failures:
            error_type = f.get("metadata", {}).get("error_type", "unknown")
            failure_types[error_type] += 1

        common_failures = [
            {"type": ft, "count": count}
            for ft, count in sorted(failure_types.items(), key=lambda x: x[1], reverse=True)
        ][:5]

        return PerformanceMetrics(
            period_start=cutoff,
            period_end=datetime.now(timezone.utc),
            total_runs=len(recent),
            success_count=sum(1 for m in recent if m["success"]),
            failure_count=len(failures),
            avg_duration=sum(m["duration_sec"] for m in recent) / len(recent),
            total_cost=sum(m.get("cost_usd", 0.0) for m in recent),
            by_agent=agent_stats,
            common_failures=common_failures,
            bottlenecks=bottlenecks,
        )

    async def analyze_week(self) -> Dict[str, Any]:
        """Analyze the past week and generate insights."""
        metrics = self.get_metrics_for_period(days=7)
        
        analysis = {
            "period": "7_days",
            "total_runs": metrics.total_runs,
            "success_rate": metrics.success_count / max(metrics.total_runs, 1),
            "avg_duration": metrics.avg_duration,
            "total_cost": metrics.total_cost,
            "by_agent": metrics.by_agent,
            "bottlenecks": metrics.bottlenecks,
            "common_failures": metrics.common_failures,
            "low_performing_agents": [
                agent for agent, stats in metrics.by_agent.items()
                if stats["success_rate"] < 0.8
            ],
        }
        
        self._analysis_history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "analysis": analysis,
        })
        
        return analysis

    async def generate_improvements(
        self,
        analysis: Optional[Dict[str, Any]] = None,
    ) -> List[Improvement]:
        """Generate improvement suggestions using LLM."""
        if analysis is None:
            analysis = await self.analyze_week()

        # Skip if not enough data
        if analysis["total_runs"] < 10:
            return []

        # Get failure patterns
        from backend.core.learning.failure_analyzer import FailureAnalyzer
        failure_analyzer = FailureAnalyzer()
        failure_stats = failure_analyzer.get_failure_stats()

        # Build prompt
        prompt = self.IMPROVEMENT_PROMPT.format(
            metrics_json=json.dumps(analysis, indent=2),
            failure_patterns=json.dumps(failure_stats.get("top_patterns", []), indent=2),
        )

        # Call LLM
        def _call_llm():
            return llm_call_simple(
                agent_name="improvement_engine",
                system="You are an expert at optimizing multi-agent AI systems.",
                user=prompt,
                max_tokens=2000,
                temperature=0.3,
            )

        try:
            response = await asyncio.get_running_loop().run_in_executor(None, _call_llm)
            if not response:
                return []

            # Parse response
            data = self._parse_llm_response(response)
            improvements_data = data.get("improvements", [])

            # Create Improvement objects
            improvements = []
            for idx, imp_data in enumerate(improvements_data[:self.max_improvements_per_cycle]):
                confidence = imp_data.get("confidence", 0.5)
                risk_str = imp_data.get("risk", "medium")
                
                # Skip low confidence
                if confidence < self.min_confidence:
                    continue

                # Determine if auto-apply is safe
                auto_apply = (
                    confidence >= self.auto_apply_threshold and
                    risk_str == "low" and
                    imp_data.get("category") in ["prompt", "configuration"]
                )

                improvement = Improvement(
                    improvement_id=f"imp_{datetime.now(timezone.utc).strftime('%Y%m%d')}_{idx:03d}",
                    description=imp_data["description"],
                    category=imp_data["category"],
                    target_agent=imp_data.get("target_agent"),
                    current_value=imp_data.get("current_value", ""),
                    proposed_value=imp_data.get("proposed_value", ""),
                    expected_impact=imp_data.get("expected_impact", {}),
                    auto_apply=auto_apply,
                    confidence=confidence,
                    risk=ImprovementRisk(risk_str),
                )
                
                improvements.append(improvement)
                self._improvements.append(improvement)

            return improvements

        except Exception as e:
            print(f"Error generating improvements: {e}")
            return []

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response to extract improvements."""
        try:
            text = response.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            return json.loads(text.strip())
        except (json.JSONDecodeError, IndexError):
            return {}

    async def apply_improvement(self, improvement_id: str) -> bool:
        """Apply a specific improvement."""
        improvement = next(
            (imp for imp in self._improvements if imp.improvement_id == improvement_id),
            None
        )
        
        if not improvement or improvement.status != ImprovementStatus.PENDING:
            return False

        # Get callback for this category
        callback = self._improvement_callbacks.get(improvement.category)
        if not callback:
            improvement.status = ImprovementStatus.FAILED
            improvement.result = {"error": "No callback registered for category"}
            return False

        # Apply the improvement
        try:
            success = callback(improvement)
            
            if success:
                improvement.status = ImprovementStatus.APPLIED
                improvement.applied_at = datetime.now(timezone.utc)
                improvement.result = {"success": True}
                self._applied_improvements.append(improvement)
            else:
                improvement.status = ImprovementStatus.FAILED
                improvement.result = {"success": False}
            
            return success
            
        except Exception as e:
            improvement.status = ImprovementStatus.FAILED
            improvement.result = {"error": str(e)}
            return False

    async def run_improvement_cycle(self) -> Dict[str, Any]:
        """Run a full improvement cycle: analyze → generate → apply safe improvements."""
        # Analyze performance
        analysis = await self.analyze_week()
        
        # Generate improvements
        improvements = await self.generate_improvements(analysis)
        
        # Auto-apply safe improvements
        applied = []
        for imp in improvements:
            if imp.auto_apply:
                success = await self.apply_improvement(imp.improvement_id)
                if success:
                    applied.append(imp.improvement_id)

        return {
            "analysis": analysis,
            "improvements_generated": len(improvements),
            "improvements_auto_applied": len(applied),
            "applied_ids": applied,
            "pending_review": [
                imp.improvement_id for imp in improvements
                if not imp.auto_apply and imp.status == ImprovementStatus.PENDING
            ],
        }

    def get_improvement_history(
        self,
        status: Optional[ImprovementStatus] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get history of improvements."""
        improvements = self._improvements + self._applied_improvements
        
        if status:
            improvements = [imp for imp in improvements if imp.status == status]
        
        # Sort by creation date (newest first)
        improvements.sort(key=lambda x: x.created_at, reverse=True)
        
        return [imp.to_dict() for imp in improvements[:limit]]

    def get_performance_trends(self, days: int = 30) -> Dict[str, Any]:
        """Get performance trends over time."""
        if len(self._analysis_history) < 2:
            return {"trend": "insufficient_data"}

        # Compare recent vs older performance
        recent = self._analysis_history[-1]["analysis"] if self._analysis_history else {}
        older = self._analysis_history[0]["analysis"] if len(self._analysis_history) > 1 else {}

        return {
            "success_rate_trend": recent.get("success_rate", 0) - older.get("success_rate", 0),
            "duration_trend": recent.get("avg_duration", 0) - older.get("avg_duration", 0),
            "cost_trend": recent.get("total_cost", 0) - older.get("total_cost", 0),
            "analysis_count": len(self._analysis_history),
        }

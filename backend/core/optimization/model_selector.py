"""
Smart Model Selector - Cost optimization through intelligent model selection (Phase 3.1)

Automatically selects the most cost-effective model for each task while
maintaining quality standards.
"""

from __future__ import annotations

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import asyncio

from backend.engine.llm_gateway import llm_call_simple


class ModelTier(str, Enum):
    """Model quality tiers."""
    PREMIUM = "premium"      # Best quality, highest cost
    STANDARD = "standard"    # Good balance
    ECONOMY = "economy"      # Cost-effective
    BUDGET = "budget"        # Cheapest option


@dataclass
class ModelInfo:
    """Information about an LLM model."""
    name: str
    tier: ModelTier
    input_cost_per_1k: float  # USD per 1K input tokens
    output_cost_per_1k: float  # USD per 1K output tokens
    max_tokens: int
    capabilities: List[str]
    average_quality_score: float  # 0.0 - 1.0


class SmartModelSelector:
    """
    Intelligently selects the best model for a task based on:
    - Task complexity
    - Budget constraints
    - Quality requirements
    - Historical performance
    """

    # Model pricing (approximate, update as needed)
    AVAILABLE_MODELS = {
        "claude-3-opus": ModelInfo(
            name="claude-3-opus",
            tier=ModelTier.PREMIUM,
            input_cost_per_1k=0.015,
            output_cost_per_1k=0.075,
            max_tokens=4096,
            capabilities=["complex_reasoning", "code_generation", "architecture", "debugging"],
            average_quality_score=0.95,
        ),
        "claude-3-sonnet": ModelInfo(
            name="claude-3-sonnet",
            tier=ModelTier.STANDARD,
            input_cost_per_1k=0.003,
            output_cost_per_1k=0.015,
            max_tokens=4096,
            capabilities=["code_generation", "documentation", "testing"],
            average_quality_score=0.88,
        ),
        "claude-3-haiku": ModelInfo(
            name="claude-3-haiku",
            tier=ModelTier.ECONOMY,
            input_cost_per_1k=0.00025,
            output_cost_per_1k=0.00125,
            max_tokens=4096,
            capabilities=["simple_tasks", "summarization", "formatting"],
            average_quality_score=0.75,
        ),
        "gpt-4": ModelInfo(
            name="gpt-4",
            tier=ModelTier.PREMIUM,
            input_cost_per_1k=0.03,
            output_cost_per_1k=0.06,
            max_tokens=8192,
            capabilities=["complex_reasoning", "code_generation", "architecture"],
            average_quality_score=0.93,
        ),
        "gpt-3.5-turbo": ModelInfo(
            name="gpt-3.5-turbo",
            tier=ModelTier.ECONOMY,
            input_cost_per_1k=0.0015,
            output_cost_per_1k=0.002,
            max_tokens=4096,
            capabilities=["simple_tasks", "formatting", "summarization"],
            average_quality_score=0.78,
        ),
    }

    # Task complexity indicators
    COMPLEXITY_INDICATORS = {
        "simple": [
            "format", "convert", "summarize", "extract", "rename",
            "reformat", "clean", "organize", "list", "count",
        ],
        "moderate": [
            "implement", "create", "build", "generate", "write",
            "develop", "design", "construct", "make", "produce",
        ],
        "complex": [
            "architect", "optimize", "refactor", "analyze", "debug",
            "troubleshoot", "solve", "complex", "advanced", "sophisticated",
        ],
    }

    def __init__(self):
        self.usage_stats: Dict[str, Dict[str, Any]] = {}
        self.cost_tracking: Dict[str, float] = {}
        self.quality_scores: Dict[str, List[float]] = {}

    async def select_model(
        self,
        task_description: str,
        budget_constraint: Optional[float] = None,
        min_quality_score: float = 0.7,
        expected_input_tokens: int = 1000,
        expected_output_tokens: int = 500,
    ) -> str:
        """
        Select the optimal model for a task.
        
        Args:
            task_description: Description of the task
            budget_constraint: Max cost willing to pay (USD)
            min_quality_score: Minimum acceptable quality (0.0-1.0)
            expected_input_tokens: Estimated input size
            expected_output_tokens: Estimated output size
            
        Returns:
            Name of selected model
        """
        # Analyze task complexity
        complexity = self._analyze_complexity(task_description)
        
        # Filter models by quality requirement
        eligible_models = [
            name for name, info in self.AVAILABLE_MODELS.items()
            if info.average_quality_score >= min_quality_score
        ]
        
        if not eligible_models:
            # Fallback to best available
            return "claude-3-opus"

        # Calculate expected costs
        model_costs = {}
        for model_name in eligible_models:
            info = self.AVAILABLE_MODELS[model_name]
            input_cost = (expected_input_tokens / 1000) * info.input_cost_per_1k
            output_cost = (expected_output_tokens / 1000) * info.output_cost_per_1k
            total_cost = input_cost + output_cost
            model_costs[model_name] = total_cost

        # Apply budget constraint
        if budget_constraint:
            affordable_models = [
                name for name, cost in model_costs.items()
                if cost <= budget_constraint
            ]
            if affordable_models:
                eligible_models = affordable_models
            else:
                # No model meets budget - use cheapest
                return min(model_costs.keys(), key=lambda x: model_costs[x])

        # Select based on complexity and cost
        if complexity == "simple":
            # For simple tasks, prefer cheaper models
            return self._select_cheapest(eligible_models, model_costs)
        elif complexity == "moderate":
            # For moderate tasks, balance cost and quality
            return self._select_balanced(eligible_models, model_costs)
        else:  # complex
            # For complex tasks, prefer quality
            return self._select_best_quality(eligible_models)

    def _analyze_complexity(self, task_description: str) -> str:
        """Analyze task complexity based on keywords."""
        task_lower = task_description.lower()
        
        # Count complexity indicators
        simple_count = sum(1 for word in self.COMPLEXITY_INDICATORS["simple"] if word in task_lower)
        moderate_count = sum(1 for word in self.COMPLEXITY_INDICATORS["moderate"] if word in task_lower)
        complex_count = sum(1 for word in self.COMPLEXITY_INDICATORS["complex"] if word in task_lower)

        # Determine complexity
        if complex_count > 0 or moderate_count >= 2:
            return "complex"
        elif moderate_count > 0 or simple_count >= 2:
            return "moderate"
        else:
            return "simple"

    def _select_cheapest(self, models: List[str], costs: Dict[str, float]) -> str:
        """Select the cheapest model from the list."""
        return min(models, key=lambda x: costs.get(x, float('inf')))

    def _select_balanced(self, models: List[str], costs: Dict[str, float]) -> str:
        """Select a balanced model (good quality, reasonable cost)."""
        # Score each model on quality per dollar
        scores = {}
        for model in models:
            info = self.AVAILABLE_MODELS[model]
            cost = costs.get(model, 0.01)
            quality_per_dollar = info.average_quality_score / cost
            scores[model] = quality_per_dollar

        return max(scores.keys(), key=lambda x: scores[x])

    def _select_best_quality(self, models: List[str]) -> str:
        """Select the highest quality model."""
        return max(
            models,
            key=lambda x: self.AVAILABLE_MODELS[x].average_quality_score
        )

    def record_usage(
        self,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        quality_score: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Record model usage for tracking."""
        if model_name not in self.usage_stats:
            self.usage_stats[model_name] = {
                "calls": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_cost": 0.0,
            }

        info = self.AVAILABLE_MODELS.get(model_name)
        if not info:
            return {}

        # Calculate cost
        input_cost = (input_tokens / 1000) * info.input_cost_per_1k
        output_cost = (output_tokens / 1000) * info.output_cost_per_1k
        total_cost = input_cost + output_cost

        # Update stats
        self.usage_stats[model_name]["calls"] += 1
        self.usage_stats[model_name]["input_tokens"] += input_tokens
        self.usage_stats[model_name]["output_tokens"] += output_tokens
        self.usage_stats[model_name]["total_cost"] += total_cost

        # Track quality
        if quality_score is not None:
            if model_name not in self.quality_scores:
                self.quality_scores[model_name] = []
            self.quality_scores[model_name].append(quality_score)

        return {
            "model": model_name,
            "cost": total_cost,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        }

    def get_cost_report(self) -> Dict[str, Any]:
        """Get comprehensive cost and usage report."""
        total_cost = sum(s["total_cost"] for s in self.usage_stats.values())
        total_calls = sum(s["calls"] for s in self.usage_stats.values())
        
        model_breakdown = {}
        for model, stats in self.usage_stats.items():
            avg_quality = 0.0
            if model in self.quality_scores and self.quality_scores[model]:
                avg_quality = sum(self.quality_scores[model]) / len(self.quality_scores[model])
            
            model_breakdown[model] = {
                "calls": stats["calls"],
                "cost": round(stats["total_cost"], 4),
                "percentage": round((stats["total_cost"] / total_cost * 100), 2) if total_cost > 0 else 0,
                "avg_quality": round(avg_quality, 2),
            }

        return {
            "total_cost_usd": round(total_cost, 4),
            "total_calls": total_calls,
            "average_cost_per_call": round(total_cost / total_calls, 4) if total_calls > 0 else 0,
            "by_model": model_breakdown,
            "savings_vs_premium": self._calculate_savings(),
        }

    def _calculate_savings(self) -> Dict[str, float]:
        """Calculate savings compared to using premium model for everything."""
        premium_cost = 0.0
        actual_cost = 0.0
        
        for model, stats in self.usage_stats.items():
            info = self.AVAILABLE_MODELS.get(model)
            if not info:
                continue
            
            actual_cost += stats["total_cost"]
            
            # Calculate what it would cost with premium (opus)
            premium_info = self.AVAILABLE_MODELS.get("claude-3-opus")
            if premium_info:
                input_cost = (stats["input_tokens"] / 1000) * premium_info.input_cost_per_1k
                output_cost = (stats["output_tokens"] / 1000) * premium_info.output_cost_per_1k
                premium_cost += input_cost + output_cost

        savings = premium_cost - actual_cost
        savings_percent = (savings / premium_cost * 100) if premium_cost > 0 else 0

        return {
            "premium_would_cost": round(premium_cost, 4),
            "actual_cost": round(actual_cost, 4),
            "savings_usd": round(savings, 4),
            "savings_percent": round(savings_percent, 2),
        }

    def get_recommendations(self) -> List[str]:
        """Get recommendations for optimizing model selection."""
        recommendations = []
        
        # Check if using expensive models for simple tasks
        opus_usage = self.usage_stats.get("claude-3-opus", {})
        if opus_usage.get("calls", 0) > 10:
            recommendations.append(
                "Consider using cheaper models (sonnet/haiku) for simple tasks to reduce costs"
            )

        # Check quality scores
        for model, scores in self.quality_scores.items():
            if scores:
                avg = sum(scores) / len(scores)
                if avg < 0.7:
                    recommendations.append(
                        f"Model {model} has low quality score ({avg:.2f}) - consider upgrading"
                    )

        return recommendations


# Global selector instance
_selector: Optional[SmartModelSelector] = None


def get_model_selector() -> SmartModelSelector:
    """Get or create the global model selector."""
    global _selector
    if _selector is None:
        _selector = SmartModelSelector()
    return _selector

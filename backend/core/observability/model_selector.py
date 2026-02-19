"""Smart model selection by task complexity (plan Phase 3.5)."""
from __future__ import annotations
from typing import Optional, Dict, Any

COSTS = {"haiku": 0.001, "sonnet": 0.015, "opus": 0.075}

class SmartModelSelector:
    def __init__(self) -> None:
        self.model_costs = COSTS

    async def select_model(self, task: Dict[str, Any], budget_constraint: Optional[float] = None) -> str:
        complexity = task.get("complexity", "moderate")
        if complexity == "simple":
            return "haiku"
        if complexity == "moderate":
            return "sonnet"
        if budget_constraint and budget_constraint < 0.5:
            return "sonnet"
        return "opus"

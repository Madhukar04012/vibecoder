"""
Token Ledger — Phase-1 + Budget Enforcement

Tracks token usage and cost per agent.
Enforces hard budget ceiling — raises BudgetExceededError on breach.
Uses Decimal for precise financial calculations.

Usage:
    from engine.token_ledger import ledger

    ledger.set_budget(1.00)  # $1.00 max
    ledger.record("product_manager", tokens=500, cost=0.015)
    ledger.record("engineer", tokens=1200, cost=0.036)

    print(ledger.total_cost)       # Decimal('0.051')
    print(ledger.budget_remaining)  # Decimal('0.949')
    print(ledger.by_agent)          # {"product_manager": {...}, "engineer": {...}}
"""

import threading
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Optional, Union
from decimal import Decimal, ROUND_HALF_UP


class BudgetExceededError(Exception):
    """Raised when an LLM call would exceed the configured budget."""
    def __init__(self, budget: Decimal, current_cost: Decimal, attempted_cost: Decimal):
        self.budget = budget
        self.current_cost = current_cost
        self.attempted_cost = attempted_cost
        total = current_cost + attempted_cost
        super().__init__(
            f"Budget exceeded: ${total:.4f} > ${budget:.4f} limit. "
            f"Current: ${current_cost:.4f}, Attempted: ${attempted_cost:.4f}"
        )


@dataclass
class AgentUsage:
    """Token usage stats for a single agent."""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost_usd: Decimal = field(default_factory=lambda: Decimal("0"))
    call_count: int = 0

    def add(self, input_tokens: int, output_tokens: int, cost: Union[float, Decimal]) -> None:
        """Add usage from a single LLM call."""
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.total_tokens += input_tokens + output_tokens
        # Convert float to Decimal if needed
        if isinstance(cost, float):
            cost = Decimal(str(cost))  # str() avoids float precision issues
        self.cost_usd += cost
        self.call_count += 1

    def to_dict(self) -> dict:
        """Convert to serializable dict."""
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "cost_usd": float(self.cost_usd.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)),
            "call_count": self.call_count,
        }


class TokenLedger:
    """
    Central ledger for tracking token usage and costs.

    Thread-safe singleton pattern for use across all agents.
    Uses Decimal for precise financial calculations.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._agents: Dict[str, AgentUsage] = defaultdict(AgentUsage)
        self._run_id: str | None = None
        self._budget: Optional[Decimal] = None  # None = unlimited

    def set_budget(self, max_usd: Union[float, Decimal]) -> None:
        """
        Set a hard budget ceiling.

        Args:
            max_usd: Maximum allowed cost in USD. Set to 0 or None to disable.
        """
        if max_usd is None or max_usd == 0:
            self._budget = None
        else:
            # Convert to Decimal for precision
            if isinstance(max_usd, float):
                max_usd = Decimal(str(max_usd))
            self._budget = max_usd if max_usd > 0 else None

    @property
    def budget(self) -> Optional[Decimal]:
        """Current budget limit (None = unlimited)."""
        return self._budget

    @property
    def budget_remaining(self) -> Optional[Decimal]:
        """Remaining budget in USD (None if no budget set)."""
        if self._budget is None:
            return None
        return max(Decimal("0"), self._budget - self.total_cost)

    @property
    def is_over_budget(self) -> bool:
        """Check if current spending exceeds budget."""
        if self._budget is None:
            return False
        return self.total_cost >= self._budget

    @property
    def budget_utilization(self) -> Optional[float]:
        """Budget utilization as percentage (0.0 to 1.0+). None if no budget."""
        if self._budget is None or self._budget == 0:
            return None
        return float(self.total_cost / self._budget)
    
    def start_run(self, run_id: str | None = None) -> None:
        """Start a new run, optionally with an ID for tracking."""
        self.reset()
        self._run_id = run_id
    
    def record(
        self,
        agent_name: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost: Union[float, Decimal] = 0.0
    ) -> None:
        """
        Record token usage from an LLM call.

        Args:
            agent_name: Name of the agent making the call
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cost: Cost in USD (float or Decimal)

        Raises:
            BudgetExceededError: If recording would exceed the budget
        """
        # Convert cost to Decimal
        if isinstance(cost, float):
            cost = Decimal(str(cost))
        elif not isinstance(cost, Decimal):
            cost = Decimal("0")

        with self._lock:
            # CRITICAL FIX: Calculate total_cost INSIDE the lock to prevent race conditions
            # The race condition occurred because total_cost was calculated outside the lock
            # in some contexts, allowing other threads to modify costs between check and record
            current_total = sum((a.cost_usd for a in self._agents.values()), Decimal("0"))
            
            # Check budget before recording
            if self._budget is not None and cost > 0:
                projected = current_total + cost
                if projected > self._budget:
                    raise BudgetExceededError(self._budget, current_total, cost)

            self._agents[agent_name].add(input_tokens, output_tokens, cost)

    def record_simple(self, agent_name: str, tokens: int, cost: Union[float, Decimal]) -> None:
        """
        Simplified recording with just total tokens and cost.

        Args:
            agent_name: Name of the agent
            tokens: Total tokens (counted as output for simplicity)
            cost: Cost in USD (float or Decimal)
            
        Raises:
            BudgetExceededError: If recording would exceed the budget
        """
        with self._lock:
            # Check budget before recording (same enforcement as record())
            if self._budget is not None and cost > 0:
                projected = self.total_cost + cost
                if projected > self._budget:
                    raise BudgetExceededError(self._budget, self.total_cost, cost)
            
            self._agents[agent_name].add(0, tokens, cost)
    
    @property
    def total_tokens(self) -> int:
        """Total tokens across all agents."""
        return sum(a.total_tokens for a in self._agents.values())

    @property
    def total_cost(self) -> Decimal:
        """Total cost in USD across all agents (as Decimal for precision)."""
        return sum((a.cost_usd for a in self._agents.values()), Decimal("0"))

    @property
    def by_agent(self) -> Dict[str, dict]:
        """Usage breakdown by agent."""
        return {name: usage.to_dict() for name, usage in self._agents.items()}

    @property
    def run_id(self) -> str | None:
        """Current run ID."""
        return self._run_id

    def get_agent_cost(self, agent_name: str) -> Decimal:
        """Get cost for a specific agent (as Decimal for precision)."""
        return self._agents[agent_name].cost_usd
    
    def get_summary(self) -> dict:
        """Get full summary for API response. Converts Decimal to float for JSON serialization."""
        summary = {
            "run_id": self._run_id,
            "total_tokens": self.total_tokens,
            "total_cost_usd": float(self.total_cost.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)),
            "by_agent": self.by_agent,
        }
        if self._budget is not None:
            summary["budget_usd"] = float(self._budget.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP))
            budget_remaining = self.budget_remaining or Decimal("0")
            summary["budget_remaining_usd"] = float(budget_remaining.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP))
            summary["budget_utilization"] = round(self.budget_utilization or 0, 4)
            summary["is_over_budget"] = self.is_over_budget
        return summary
    
    def reset(self) -> None:
        """Reset all tracking for a new run. Budget is preserved."""
        self._agents.clear()
        self._run_id = None
        # Note: budget is intentionally NOT reset here
    
    def __repr__(self) -> str:
        return f"TokenLedger(agents={list(self._agents.keys())}, total_cost=${self.total_cost:.4f})"


# Global singleton instance
ledger = TokenLedger()

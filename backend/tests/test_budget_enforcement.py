"""Tests for Token Ledger with Budget Enforcement."""

import pytest
from backend.engine.token_ledger import TokenLedger, BudgetExceededError


class TestTokenLedger:
    """Core token tracking tests."""
    
    def setup_method(self):
        self.ledger = TokenLedger()
    
    def test_record_usage(self):
        self.ledger.record("pm", input_tokens=100, output_tokens=50, cost=0.01)
        assert self.ledger.total_tokens == 150
        assert self.ledger.total_cost == 0.01
    
    def test_by_agent(self):
        self.ledger.record("pm", cost=0.01)
        self.ledger.record("engineer", cost=0.02)
        agents = self.ledger.by_agent
        assert "pm" in agents
        assert "engineer" in agents
    
    def test_reset_clears_usage(self):
        self.ledger.record("pm", cost=0.01)
        self.ledger.reset()
        assert self.ledger.total_cost == 0.0
        assert self.ledger.total_tokens == 0


class TestBudgetEnforcement:
    """Budget ceiling tests."""
    
    def setup_method(self):
        self.ledger = TokenLedger()
    
    def test_no_budget_allows_unlimited(self):
        """No budget set = no limit."""
        self.ledger.record("pm", cost=100.0)
        assert self.ledger.total_cost == 100.0
        assert not self.ledger.is_over_budget
    
    def test_set_budget(self):
        self.ledger.set_budget(1.00)
        assert self.ledger.budget == 1.00
    
    def test_budget_remaining(self):
        self.ledger.set_budget(1.00)
        self.ledger.record("pm", cost=0.25)
        assert self.ledger.budget_remaining == pytest.approx(0.75)
    
    def test_budget_utilization(self):
        self.ledger.set_budget(1.00)
        self.ledger.record("pm", cost=0.50)
        assert self.ledger.budget_utilization == pytest.approx(0.5)
    
    def test_budget_exceeded_raises(self):
        """Recording cost that exceeds budget raises BudgetExceededError."""
        self.ledger.set_budget(0.10)
        self.ledger.record("pm", cost=0.05)  # Fine
        
        with pytest.raises(BudgetExceededError) as exc_info:
            self.ledger.record("pm", cost=0.10)  # Would total 0.15 > 0.10
        
        assert exc_info.value.budget == 0.10
        assert exc_info.value.current_cost == 0.05
        assert exc_info.value.attempted_cost == 0.10
    
    def test_budget_not_exceeded_at_exact_limit(self):
        """Recording exactly up to budget should work."""
        self.ledger.set_budget(0.10)
        self.ledger.record("pm", cost=0.10)  # Exactly at limit
        assert self.ledger.is_over_budget  # At limit counts as over
    
    def test_budget_preserved_after_reset(self):
        """Budget should survive reset()."""
        self.ledger.set_budget(1.00)
        self.ledger.record("pm", cost=0.50)
        self.ledger.reset()
        
        assert self.ledger.budget == 1.00
        assert self.ledger.budget_remaining == 1.00
    
    def test_disable_budget(self):
        self.ledger.set_budget(1.00)
        self.ledger.set_budget(0)  # Disable
        assert self.ledger.budget is None
    
    def test_summary_includes_budget(self):
        self.ledger.set_budget(1.00)
        self.ledger.record("pm", cost=0.25)
        summary = self.ledger.get_summary()
        
        assert "budget_usd" in summary
        assert summary["budget_usd"] == 1.00
        assert "budget_remaining_usd" in summary
        assert "is_over_budget" in summary
    
    def test_zero_cost_bypasses_budget_check(self):
        """Zero-cost records shouldn't trigger budget check."""
        self.ledger.set_budget(0.01)
        self.ledger.record("pm", cost=0.01)
        # Zero-cost should still work even though we're at limit
        self.ledger.record("pm", input_tokens=100, output_tokens=50, cost=0.0)

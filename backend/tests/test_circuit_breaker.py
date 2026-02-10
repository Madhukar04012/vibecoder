"""Tests for Circuit Breaker."""

import time
import pytest
from backend.engine.circuit_breaker import (
    CircuitBreaker, CircuitState, CircuitOpenError,
    get_circuit_breaker, get_all_breaker_statuses, reset_all_breakers,
)


class TestCircuitBreaker:
    """Core circuit breaker tests."""
    
    def setup_method(self):
        self.cb = CircuitBreaker(name="test", max_failures=3, reset_timeout=1.0)
    
    def test_initial_state_is_closed(self):
        assert self.cb.state == CircuitState.CLOSED
    
    def test_successful_call_stays_closed(self):
        result = self.cb.call(lambda: 42)
        assert result == 42
        assert self.cb.state == CircuitState.CLOSED
    
    def test_failure_increments_count(self):
        def fail():
            raise ValueError("boom")
        
        with pytest.raises(ValueError):
            self.cb.call(fail)
        
        assert self.cb.failure_count == 1
        assert self.cb.state == CircuitState.CLOSED
    
    def test_max_failures_opens_circuit(self):
        """After max_failures, circuit should open."""
        def fail():
            raise ValueError("boom")
        
        for _ in range(3):
            with pytest.raises(ValueError):
                self.cb.call(fail)
        
        assert self.cb.state == CircuitState.OPEN
    
    def test_open_circuit_rejects_calls(self):
        """Open circuit should reject immediately with CircuitOpenError."""
        def fail():
            raise ValueError("boom")
        
        # Trip the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                self.cb.call(fail)
        
        # Next call should raise CircuitOpenError, not call the function
        with pytest.raises(CircuitOpenError) as exc_info:
            self.cb.call(lambda: 42)
        
        assert exc_info.value.breaker_name == "test"
        assert exc_info.value.failures == 3
    
    def test_auto_half_open_after_timeout(self):
        """After reset_timeout, circuit should transition to HALF_OPEN."""
        def fail():
            raise ValueError("boom")
        
        # Trip the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                self.cb.call(fail)
        
        # Wait for reset timeout
        time.sleep(1.1)
        
        # Should be HALF_OPEN now
        assert self.cb.state == CircuitState.HALF_OPEN
    
    def test_half_open_success_closes_circuit(self):
        """Success in HALF_OPEN should close the circuit."""
        def fail():
            raise ValueError("boom")
        
        # Trip the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                self.cb.call(fail)
        
        # Wait for reset
        time.sleep(1.1)
        
        # Success should close
        result = self.cb.call(lambda: "recovered")
        assert result == "recovered"
        assert self.cb.state == CircuitState.CLOSED
        assert self.cb.failure_count == 0
    
    def test_force_reset(self):
        """Manual reset should close the circuit."""
        def fail():
            raise ValueError("boom")
        
        for _ in range(3):
            with pytest.raises(ValueError):
                self.cb.call(fail)
        
        self.cb.reset()
        assert self.cb.state == CircuitState.CLOSED
        assert self.cb.failure_count == 0
    
    def test_get_status(self):
        status = self.cb.get_status()
        assert status["name"] == "test"
        assert status["state"] == "closed"
        assert status["max_failures"] == 3


class TestCircuitBreakerRegistry:
    """Tests for global circuit breaker registry."""
    
    def test_get_or_create(self):
        cb1 = get_circuit_breaker("api")
        cb2 = get_circuit_breaker("api")
        assert cb1 is cb2  # Same instance
    
    def test_different_names_different_instances(self):
        cb1 = get_circuit_breaker("api1")
        cb2 = get_circuit_breaker("api2")
        assert cb1 is not cb2
    
    def test_get_all_statuses(self):
        get_circuit_breaker("status_test")
        statuses = get_all_breaker_statuses()
        assert "status_test" in statuses

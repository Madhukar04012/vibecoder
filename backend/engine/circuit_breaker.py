"""
Circuit Breaker — Phase 3

Prevents infinite retry loops and token burn.
Stops agent retries after defined failure threshold and escalates to human.

States:
  CLOSED    → Normal operation, calls pass through
  OPEN      → Too many failures, all calls rejected immediately
  HALF_OPEN → Testing recovery with a single probe call

Usage:
    from engine.circuit_breaker import CircuitBreaker

    cb = CircuitBreaker(max_failures=3, reset_timeout=60)
    
    try:
        result = cb.call(risky_function, arg1, arg2)
    except CircuitOpenError:
        # Circuit is open — too many failures
        escalate_to_human()
"""

import time
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from backend.engine.events import get_event_emitter, EngineEventType


# ─── Circuit States ─────────────────────────────────────────────────────────

class CircuitState(Enum):
    CLOSED = "closed"        # Normal — calls pass through
    OPEN = "open"            # Tripped — rejecting all calls
    HALF_OPEN = "half_open"  # Probing — testing one call


class CircuitOpenError(Exception):
    """Raised when the circuit breaker is open and rejecting calls."""
    def __init__(self, breaker_name: str, failures: int, last_error: str):
        self.breaker_name = breaker_name
        self.failures = failures
        self.last_error = last_error
        super().__init__(
            f"Circuit '{breaker_name}' is OPEN after {failures} failures. "
            f"Last error: {last_error}"
        )


# ─── Failure Record ─────────────────────────────────────────────────────────

@dataclass
class FailureEntry:
    """Record of a single failure."""
    timestamp: float
    error_type: str
    error_message: str
    agent_name: str = ""
    context: str = ""


# ─── Circuit Breaker ────────────────────────────────────────────────────────

class CircuitBreaker:
    """
    Prevents cascading failures by stopping retries after a threshold.
    
    Features:
    - Configurable failure threshold
    - Auto-reset after timeout
    - Half-open probe for recovery testing
    - Full failure history for reporting
    - Event emission for UI visibility
    """
    
    def __init__(
        self,
        name: str = "default",
        max_failures: int = 3,
        reset_timeout: float = 60.0,
        on_open: Optional[Callable] = None,
    ):
        """
        Initialize circuit breaker.
        
        Args:
            name: Identifier for this breaker
            max_failures: Failures before tripping to OPEN
            reset_timeout: Seconds before transitioning from OPEN to HALF_OPEN
            on_open: Optional callback when circuit opens
        """
        self.name = name
        self.max_failures = max_failures
        self.reset_timeout = reset_timeout
        self._on_open = on_open
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: float = 0
        self._last_error: str = ""
        self._history: List[FailureEntry] = []
        self._success_count = 0
        self._total_calls = 0
        
        self.events = get_event_emitter()
    
    @property
    def state(self) -> CircuitState:
        """Current circuit state (with auto-transition from OPEN to HALF_OPEN)."""
        if self._state == CircuitState.OPEN:
            elapsed = time.time() - self._last_failure_time
            if elapsed >= self.reset_timeout:
                self._state = CircuitState.HALF_OPEN
                self._emit_event("CIRCUIT_HALF_OPEN", {
                    "message": f"Circuit '{self.name}' entering HALF_OPEN after {elapsed:.0f}s",
                })
        return self._state
    
    @property
    def failure_count(self) -> int:
        return self._failure_count
    
    def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        Execute function through the circuit breaker.
        
        Args:
            func: Function to call
            *args, **kwargs: Arguments to pass
            
        Returns:
            Result of func
            
        Raises:
            CircuitOpenError: If circuit is OPEN
        """
        current_state = self.state  # Triggers auto-transition check
        self._total_calls += 1
        
        if current_state == CircuitState.OPEN:
            raise CircuitOpenError(self.name, self._failure_count, self._last_error)
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure(e)
            raise
    
    async def call_async(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """Async version of call()."""
        current_state = self.state
        self._total_calls += 1
        
        if current_state == CircuitState.OPEN:
            raise CircuitOpenError(self.name, self._failure_count, self._last_error)
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure(e)
            raise
    
    def _on_success(self) -> None:
        """Handle successful call."""
        self._success_count += 1
        
        if self._state == CircuitState.HALF_OPEN:
            # Recovery confirmed — close circuit
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._emit_event("CIRCUIT_CLOSED", {
                "message": f"Circuit '{self.name}' recovered and CLOSED",
            })
    
    def _on_failure(self, error: Exception) -> None:
        """Handle failed call."""
        self._failure_count += 1
        self._last_failure_time = time.time()
        self._last_error = str(error)
        
        # Record failure
        self._history.append(FailureEntry(
            timestamp=time.time(),
            error_type=type(error).__name__,
            error_message=str(error)[:500],
        ))
        
        # Keep only last 50 failures
        if len(self._history) > 50:
            self._history = self._history[-50:]
        
        # Check if we should trip
        if self._failure_count >= self.max_failures:
            self._state = CircuitState.OPEN
            self._emit_event("CIRCUIT_OPEN", {
                "message": f"Circuit '{self.name}' OPEN after {self._failure_count} failures",
                "last_error": self._last_error,
                "failure_count": self._failure_count,
            })
            
            if self._on_open:
                try:
                    self._on_open(self)
                except Exception:
                    pass
    
    def reset(self) -> None:
        """Force-reset the circuit breaker to CLOSED."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_error = ""
        self._emit_event("CIRCUIT_RESET", {
            "message": f"Circuit '{self.name}' force-reset to CLOSED",
        })
    
    def get_status(self) -> Dict[str, Any]:
        """Get full status for API/UI."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self._failure_count,
            "max_failures": self.max_failures,
            "success_count": self._success_count,
            "total_calls": self._total_calls,
            "last_error": self._last_error,
            "reset_timeout": self.reset_timeout,
            "history": [
                {
                    "timestamp": datetime.fromtimestamp(f.timestamp).isoformat(),
                    "error_type": f.error_type,
                    "error_message": f.error_message[:200],
                }
                for f in self._history[-10:]  # Last 10 for API
            ],
        }
    
    def _emit_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Emit circuit breaker event."""
        self.events.emit(EngineEventType.WARNING, {
            "source": "circuit_breaker",
            "breaker": self.name,
            "event": event_type,
            **payload,
        })
    
    def __repr__(self) -> str:
        return f"CircuitBreaker(name={self.name}, state={self.state.value}, failures={self._failure_count}/{self.max_failures})"


# ─── Global Registry ────────────────────────────────────────────────────────

_breakers: Dict[str, CircuitBreaker] = {}


def get_circuit_breaker(
    name: str = "default",
    max_failures: int = 3,
    reset_timeout: float = 60.0,
) -> CircuitBreaker:
    """Get or create a named circuit breaker."""
    if name not in _breakers:
        _breakers[name] = CircuitBreaker(
            name=name,
            max_failures=max_failures,
            reset_timeout=reset_timeout,
        )
    return _breakers[name]


def get_all_breaker_statuses() -> Dict[str, Dict[str, Any]]:
    """Get statuses of all circuit breakers."""
    return {name: cb.get_status() for name, cb in _breakers.items()}


def reset_all_breakers() -> None:
    """Reset all circuit breakers."""
    for cb in _breakers.values():
        cb.reset()

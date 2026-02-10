"""
Engine State Machine — Phase-1 + Phase-4

Controls agent execution order with strict state transitions.
Agents can only run in their designated states.

State Flow:
  IDLE → PLANNING → APPROVED → EXECUTION → IDLE
  (any) → AWAITING_HUMAN → (user action) → IDLE

Rules (Hard Constraints):
  - IDLE: Accept user request only
  - PLANNING: PM + Architect only
  - APPROVED: No agent calls (gate state)
  - EXECUTION: Engineer only
  - AWAITING_HUMAN: Autonomy frozen, waiting for user (Phase-4)
"""

from enum import Enum
from typing import Set


class EngineState(Enum):
    """Engine execution states."""
    IDLE = "idle"
    PLANNING = "planning"
    APPROVED = "approved"
    EXECUTION = "execution"
    AWAITING_HUMAN = "awaiting_human"  # Phase-4: Escalation state


# Allowed agents per state
ALLOWED_AGENTS: dict[EngineState, Set[str]] = {
    EngineState.IDLE: set(),  # No agents allowed
    EngineState.PLANNING: {"product_manager", "architect", "team_lead"},
    EngineState.APPROVED: set(),  # Gate state - no agents
    EngineState.EXECUTION: {"engineer", "qa", "devops", "qa_tester"},
    EngineState.AWAITING_HUMAN: set(),  # Frozen - no agents
}

# Valid state transitions
VALID_TRANSITIONS: dict[EngineState, Set[EngineState]] = {
    EngineState.IDLE: {EngineState.PLANNING},
    EngineState.PLANNING: {EngineState.APPROVED, EngineState.IDLE, EngineState.AWAITING_HUMAN},
    EngineState.APPROVED: {EngineState.EXECUTION, EngineState.PLANNING, EngineState.AWAITING_HUMAN},
    EngineState.EXECUTION: {EngineState.IDLE, EngineState.AWAITING_HUMAN},
    EngineState.AWAITING_HUMAN: {EngineState.IDLE, EngineState.PLANNING},  # User can retry or abort
}


class EngineStateError(Exception):
    """Raised when an invalid state transition or agent call is attempted."""
    pass


class EngineStateMachine:
    """
    Controls engine state and enforces agent execution rules.
    
    Usage:
        engine = EngineStateMachine()
        engine.transition(EngineState.PLANNING)
        engine.validate_agent("product_manager")  # OK
        engine.validate_agent("engineer")  # Raises EngineStateError
    """
    
    def __init__(self):
        self._state = EngineState.IDLE
        self._history: list[EngineState] = [EngineState.IDLE]
    
    @property
    def state(self) -> EngineState:
        """Current engine state."""
        return self._state
    
    @property
    def history(self) -> list[EngineState]:
        """State transition history."""
        return self._history.copy()
    
    def transition(self, new_state: EngineState) -> None:
        """
        Transition to a new state.
        
        Args:
            new_state: Target state
            
        Raises:
            EngineStateError: If transition is not valid
        """
        if new_state not in VALID_TRANSITIONS[self._state]:
            raise EngineStateError(
                f"Invalid transition: {self._state.value} → {new_state.value}. "
                f"Valid targets: {[s.value for s in VALID_TRANSITIONS[self._state]]}"
            )
        
        self._state = new_state
        self._history.append(new_state)
    
    def validate_agent(self, agent_name: str) -> None:
        """
        Check if an agent is allowed to run in the current state.
        
        Args:
            agent_name: Name of the agent attempting to run
            
        Raises:
            EngineStateError: If agent is not allowed in current state
        """
        allowed = ALLOWED_AGENTS[self._state]
        if agent_name not in allowed:
            raise EngineStateError(
                f"Agent '{agent_name}' cannot run in state '{self._state.value}'. "
                f"Allowed agents: {list(allowed) or 'none'}"
            )
    
    def can_agent_run(self, agent_name: str) -> bool:
        """
        Check if an agent can run (non-throwing version).
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            True if agent is allowed in current state
        """
        return agent_name in ALLOWED_AGENTS[self._state]
    
    def reset(self) -> None:
        """Reset engine to IDLE state."""
        self._state = EngineState.IDLE
        self._history = [EngineState.IDLE]
    
    def __repr__(self) -> str:
        return f"EngineStateMachine(state={self._state.value})"

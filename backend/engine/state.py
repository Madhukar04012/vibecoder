"""
Engine state machine with explicit lifecycle governance.

Canonical states:
IDLE -> PLANNING -> WAITING_FOR_APPROVAL -> EXECUTING -> REVIEWING -> QA
then one of COMPLETED | PARTIAL_SUCCESS | FAILED | CANCELLED | TIMEOUT.
"""

from __future__ import annotations

from enum import Enum
from typing import Set


class EngineState(Enum):
    """Engine execution states with backward-compatible aliases."""

    IDLE = "idle"
    PLANNING = "planning"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    EXECUTING = "executing"
    REVIEWING = "reviewing"
    QA = "qa"
    PARTIAL_SUCCESS = "partial_success"
    AWAITING_HUMAN = "awaiting_human"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    COMPLETED = "completed"

    # Backward-compat aliases
    APPROVED = "waiting_for_approval"
    EXECUTION = "executing"


ALLOWED_AGENTS: dict[EngineState, Set[str]] = {
    EngineState.IDLE: set(),
    EngineState.PLANNING: {"product_manager", "architect", "team_lead", "planner"},
    EngineState.WAITING_FOR_APPROVAL: set(),
    EngineState.EXECUTING: {
        "engineer",
        "qa",
        "devops",
        "qa_tester",
        "planner",
        "db_schema",
        "auth",
        "coder",
        "deployer",
        "tester",
    },
    EngineState.REVIEWING: {"code_reviewer"},
    EngineState.QA: {"qa", "qa_tester", "tester"},
    EngineState.PARTIAL_SUCCESS: set(),
    EngineState.AWAITING_HUMAN: set(),
    EngineState.FAILED: set(),
    EngineState.CANCELLED: set(),
    EngineState.TIMEOUT: set(),
    EngineState.COMPLETED: set(),
}


VALID_TRANSITIONS: dict[EngineState, Set[EngineState]] = {
    EngineState.IDLE: {
        EngineState.PLANNING,
        EngineState.FAILED,
        EngineState.CANCELLED,
        EngineState.TIMEOUT,
    },
    EngineState.PLANNING: {
        EngineState.WAITING_FOR_APPROVAL,
        EngineState.FAILED,
        EngineState.CANCELLED,
        EngineState.TIMEOUT,
        EngineState.AWAITING_HUMAN,
    },
    EngineState.WAITING_FOR_APPROVAL: {
        EngineState.PLANNING,
        EngineState.EXECUTING,
        EngineState.CANCELLED,
        EngineState.TIMEOUT,
        EngineState.FAILED,
        EngineState.AWAITING_HUMAN,
    },
    EngineState.EXECUTING: {
        EngineState.REVIEWING,
        EngineState.QA,
        EngineState.PARTIAL_SUCCESS,
        EngineState.COMPLETED,
        EngineState.FAILED,
        EngineState.CANCELLED,
        EngineState.TIMEOUT,
        EngineState.AWAITING_HUMAN,
    },
    EngineState.REVIEWING: {
        EngineState.EXECUTING,
        EngineState.QA,
        EngineState.PARTIAL_SUCCESS,
        EngineState.COMPLETED,
        EngineState.FAILED,
        EngineState.CANCELLED,
        EngineState.TIMEOUT,
        EngineState.AWAITING_HUMAN,
    },
    EngineState.QA: {
        EngineState.EXECUTING,
        EngineState.PARTIAL_SUCCESS,
        EngineState.COMPLETED,
        EngineState.FAILED,
        EngineState.CANCELLED,
        EngineState.TIMEOUT,
        EngineState.AWAITING_HUMAN,
    },
    EngineState.AWAITING_HUMAN: {
        EngineState.IDLE,
        EngineState.PLANNING,
        EngineState.EXECUTING,
        EngineState.CANCELLED,
    },
    EngineState.PARTIAL_SUCCESS: {EngineState.IDLE},
    EngineState.FAILED: {EngineState.IDLE},
    EngineState.CANCELLED: {EngineState.IDLE},
    EngineState.TIMEOUT: {EngineState.IDLE},
    EngineState.COMPLETED: {EngineState.IDLE},
}


class EngineStateError(Exception):
    """Raised when an invalid state transition or agent call is attempted."""


class EngineStateMachine:
    """State machine guard for execution lifecycle."""

    def __init__(self):
        self._state = EngineState.IDLE
        self._history: list[EngineState] = [EngineState.IDLE]

    @property
    def state(self) -> EngineState:
        return self._state

    @property
    def history(self) -> list[EngineState]:
        return self._history.copy()

    def transition(self, new_state: EngineState) -> None:
        if new_state not in VALID_TRANSITIONS[self._state]:
            raise EngineStateError(
                f"Invalid transition: {self._state.value} -> {new_state.value}. "
                f"Valid targets: {[state.value for state in VALID_TRANSITIONS[self._state]]}"
            )

        self._state = new_state
        self._history.append(new_state)

    def validate_agent(self, agent_name: str) -> None:
        allowed = ALLOWED_AGENTS[self._state]
        if agent_name not in allowed:
            raise EngineStateError(
                f"Agent '{agent_name}' cannot run in state '{self._state.value}'. "
                f"Allowed agents: {list(allowed) or 'none'}"
            )

    def can_agent_run(self, agent_name: str) -> bool:
        return agent_name in ALLOWED_AGENTS[self._state]

    def reset(self) -> None:
        self._state = EngineState.IDLE
        self._history = [EngineState.IDLE]

    def __repr__(self) -> str:
        return f"EngineStateMachine(state={self._state.value})"

"""Tests for expanded engine state machine."""

from backend.engine.state import EngineState, EngineStateMachine, EngineStateError


def test_happy_path_states():
    machine = EngineStateMachine()
    machine.transition(EngineState.PLANNING)
    machine.transition(EngineState.WAITING_FOR_APPROVAL)
    machine.transition(EngineState.EXECUTING)
    machine.transition(EngineState.REVIEWING)
    machine.transition(EngineState.QA)
    machine.transition(EngineState.COMPLETED)

    assert machine.state == EngineState.COMPLETED


def test_partial_success_path():
    machine = EngineStateMachine()
    machine.transition(EngineState.PLANNING)
    machine.transition(EngineState.WAITING_FOR_APPROVAL)
    machine.transition(EngineState.EXECUTING)
    machine.transition(EngineState.QA)
    machine.transition(EngineState.PARTIAL_SUCCESS)

    assert machine.state == EngineState.PARTIAL_SUCCESS


def test_invalid_transition_raises():
    machine = EngineStateMachine()
    try:
        machine.transition(EngineState.QA)
        assert False, "Expected EngineStateError"
    except EngineStateError:
        assert True


def test_terminal_state_can_reset_to_idle():
    machine = EngineStateMachine()
    machine.transition(EngineState.FAILED)
    machine.transition(EngineState.IDLE)
    assert machine.state == EngineState.IDLE

"""
Engine Events — Phase 2

Event system for the Atoms Engine.
Engine emits events. UI listens. Agents do NOT talk to frontend directly.

Event Types:
- PLANNING_DIAGRAM_UPDATED: Mermaid diagram detected in roadmap
- AGENT_STATUS: Agent activity updates
- EXECUTION_STARTED: Execution phase started
- EXECUTION_COMPLETED: Execution phase completed
- FILE_CHANGE_PROPOSED: Agent proposes file changes
- DIFF_APPROVED: User approved a diff
- DIFF_REJECTED: User rejected a diff

Usage:
    from backend.engine.events import EventEmitter, EngineEventType
    
    emitter = EventEmitter()
    emitter.on(EngineEventType.AGENT_STATUS, handler)
    emitter.emit(EngineEventType.AGENT_STATUS, {"agent": "architect", "status": "working"})
"""

from enum import Enum
from typing import Dict, Any, Callable, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import asyncio


class EngineEventType(Enum):
    """Engine event types."""
    # Planning events
    PLANNING_STARTED = "PLANNING_STARTED"
    PLANNING_DIAGRAM_UPDATED = "PLANNING_DIAGRAM_UPDATED"
    PLANNING_COMPLETED = "PLANNING_COMPLETED"
    
    # Approval events
    DIAGRAM_ACKNOWLEDGED = "DIAGRAM_ACKNOWLEDGED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    APPROVED = "APPROVED"
    
    # Execution events
    EXECUTION_STARTED = "EXECUTION_STARTED"
    EXECUTION_COMPLETED = "EXECUTION_COMPLETED"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    
    # Agent events
    AGENT_STATUS = "AGENT_STATUS"
    AGENT_STARTED = "AGENT_STARTED"
    AGENT_COMPLETED = "AGENT_COMPLETED"
    
    # File events
    FILE_CHANGE_PROPOSED = "FILE_CHANGE_PROPOSED"
    DIFF_APPROVED = "DIFF_APPROVED"
    DIFF_REJECTED = "DIFF_REJECTED"
    FILE_WRITTEN = "FILE_WRITTEN"
    
    # Error events
    ERROR = "ERROR"
    WARNING = "WARNING"


@dataclass
class EngineEvent:
    """An engine event."""
    type: EngineEventType
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    run_id: Optional[str] = None


class EventEmitter:
    """
    Simple event emitter for engine events.
    
    Supports:
    - Sync and async handlers
    - Multiple handlers per event
    - Event history for replay
    """
    
    def __init__(self, max_history: int = 100):
        self._handlers: Dict[EngineEventType, List[Callable]] = {}
        self._async_handlers: Dict[EngineEventType, List[Callable]] = {}
        self._history: List[EngineEvent] = []
        self._max_history = max_history
    
    def on(self, event_type: EngineEventType, handler: Callable) -> None:
        """
        Register a sync handler for an event type.
        
        Args:
            event_type: Event type to listen for
            handler: Function to call when event is emitted
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    def on_async(self, event_type: EngineEventType, handler: Callable) -> None:
        """
        Register an async handler for an event type.
        
        Args:
            event_type: Event type to listen for
            handler: Async function to call when event is emitted
        """
        if event_type not in self._async_handlers:
            self._async_handlers[event_type] = []
        self._async_handlers[event_type].append(handler)
    
    def off(self, event_type: EngineEventType, handler: Callable) -> bool:
        """
        Remove a handler.
        
        Args:
            event_type: Event type
            handler: Handler to remove
            
        Returns:
            True if handler was removed
        """
        if event_type in self._handlers and handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
            return True
        if event_type in self._async_handlers and handler in self._async_handlers[event_type]:
            self._async_handlers[event_type].remove(handler)
            return True
        return False
    
    def emit(
        self, 
        event_type: EngineEventType, 
        payload: Dict[str, Any],
        run_id: Optional[str] = None,
    ) -> EngineEvent:
        """
        Emit an event (sync handlers only).
        
        Args:
            event_type: Event type
            payload: Event data
            run_id: Optional run identifier
            
        Returns:
            The emitted event
        """
        event = EngineEvent(
            type=event_type,
            payload=payload,
            run_id=run_id,
        )
        
        # Add to history
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history.pop(0)
        
        # Call sync handlers
        handlers = self._handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                print(f"Error in event handler: {e}")
        
        return event
    
    async def emit_async(
        self, 
        event_type: EngineEventType, 
        payload: Dict[str, Any],
        run_id: Optional[str] = None,
    ) -> EngineEvent:
        """
        Emit an event (includes async handlers).
        
        Args:
            event_type: Event type
            payload: Event data
            run_id: Optional run identifier
            
        Returns:
            The emitted event
        """
        event = self.emit(event_type, payload, run_id)
        
        # Call async handlers
        async_handlers = self._async_handlers.get(event_type, [])
        for handler in async_handlers:
            try:
                await handler(event)
            except Exception as e:
                print(f"Error in async event handler: {e}")
        
        return event
    
    def get_history(
        self, 
        event_type: Optional[EngineEventType] = None,
        limit: int = 50,
    ) -> List[EngineEvent]:
        """
        Get event history.
        
        Args:
            event_type: Filter by event type (optional)
            limit: Maximum number of events to return
            
        Returns:
            List of events (newest first)
        """
        events = self._history.copy()
        if event_type:
            events = [e for e in events if e.type == event_type]
        return events[-limit:][::-1]
    
    def clear_history(self) -> None:
        """Clear event history."""
        self._history.clear()
    
    def clear_handlers(self) -> None:
        """Clear all handlers."""
        self._handlers.clear()
        self._async_handlers.clear()


# ─── Global Instance ─────────────────────────────────────────────────────────

_emitter: Optional[EventEmitter] = None


def get_event_emitter() -> EventEmitter:
    """Get the global event emitter instance."""
    global _emitter
    if _emitter is None:
        _emitter = EventEmitter()
    return _emitter

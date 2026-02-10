"""
HITL Manager — Phase 4

Human-in-the-Loop Clarification Cards for agent uncertainty.

When agents encounter low confidence (<80%) at decision points,
they pause and request human guidance instead of guessing.

Flow:
1. Agent detects low confidence
2. Agent creates ClarificationCard
3. HITLManager emits CLARIFICATION_REQUIRED
4. Engine transitions to AWAITING_HUMAN
5. UI renders Clarification Card
6. User selects option or provides guidance
7. Engine resumes with User-Directed Constraint

Usage:
    card = ClarificationCard(
        agent_name="architect",
        context="database_selection",
        options=["MongoDB", "PostgreSQL"],
        reasoning="Unsure which DB best fits scaling requirements"
    )
    hitl_manager.request_clarification(card)
"""

import uuid
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from pathlib import Path

from backend.engine.events import get_event_emitter, EngineEventType


# ─── Constants ───────────────────────────────────────────────────────────────

FEEDBACK_FILE = "feedback.json"
CONFIDENCE_THRESHOLD = 0.8  # Below this, must clarify


# ─── Clarification Card ──────────────────────────────────────────────────────

@dataclass
class ClarificationCard:
    """
    A decision checkpoint requiring human input.
    
    Attributes:
        agent_name: Which agent is asking
        context: What decision area (e.g., "database_selection")
        options: Available choices
        reasoning: Why clarification is needed
        metadata: Additional context data
    """
    agent_name: str
    context: str
    options: List[str]
    reasoning: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    confidence: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict for API/events."""
        return {
            "id": self.id,
            "agent": self.agent_name,
            "title": f"Decision Required: {self.agent_name.replace('_', ' ').title()}",
            "description": self.reasoning,
            "context": self.context,
            "choices": self.options,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }


# ─── Clarification Response ──────────────────────────────────────────────────

@dataclass
class ClarificationResponse:
    """User's response to a clarification card."""
    card_id: str
    selected_option: Optional[str] = None
    custom_instruction: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "card_id": self.card_id,
            "selected_option": self.selected_option,
            "custom_instruction": self.custom_instruction,
            "timestamp": self.timestamp,
        }


# ─── HITL Manager ────────────────────────────────────────────────────────────

class HITLManager:
    """
    Manages Human-in-the-Loop clarification flow.
    
    Responsibilities:
    - Accept clarification requests from agents
    - Emit events for UI
    - Store feedback for learning
    - Provide responses back to agents
    """
    
    def __init__(self, feedback_path: str = ""):
        self.events = get_event_emitter()
        self.feedback_path = feedback_path or FEEDBACK_FILE
        self.pending_cards: Dict[str, ClarificationCard] = {}
        self.responses: Dict[str, ClarificationResponse] = {}
        self._on_response_callbacks: List[Callable[[str, ClarificationResponse], None]] = []
    
    def request_clarification(self, card: ClarificationCard) -> str:
        """
        Request human clarification.
        
        Args:
            card: The clarification card
            
        Returns:
            Card ID for tracking
        """
        # Store pending card
        self.pending_cards[card.id] = card
        
        # Emit event for UI
        self.events.emit(EngineEventType.AGENT_STATUS, {
            "agent": card.agent_name,
            "event": "CLARIFICATION_REQUIRED",
            "card": card.to_dict(),
        })
        
        return card.id
    
    def respond(self, card_id: str, response: ClarificationResponse) -> bool:
        """
        Submit user response to a clarification card.
        
        Args:
            card_id: ID of the card being responded to
            response: User's response
            
        Returns:
            True if response was accepted
        """
        if card_id not in self.pending_cards:
            return False
        
        card = self.pending_cards.pop(card_id)
        self.responses[card_id] = response
        
        # Record feedback for learning
        self._record_feedback(card, response)
        
        # Emit response event
        self.events.emit(EngineEventType.AGENT_STATUS, {
            "agent": card.agent_name,
            "event": "CLARIFICATION_RESOLVED",
            "card_id": card_id,
            "response": response.to_dict(),
        })
        
        # Notify callbacks
        for callback in self._on_response_callbacks:
            try:
                callback(card_id, response)
            except Exception:
                pass
        
        return True
    
    def get_pending_cards(self) -> List[Dict[str, Any]]:
        """Get all pending clarification cards."""
        return [card.to_dict() for card in self.pending_cards.values()]
    
    def get_response(self, card_id: str) -> Optional[ClarificationResponse]:
        """Get response for a card if available."""
        return self.responses.get(card_id)
    
    def on_response(self, callback: Callable[[str, ClarificationResponse], None]) -> None:
        """Register callback for when responses are received."""
        self._on_response_callbacks.append(callback)
    
    def _record_feedback(self, card: ClarificationCard, response: ClarificationResponse) -> None:
        """Record feedback for prompt_optimizer learning."""
        feedback_entry = {
            "card": card.to_dict(),
            "response": response.to_dict(),
            "recorded_at": datetime.now().isoformat(),
        }
        
        # Load existing feedback
        feedback_data = {"entries": []}
        if os.path.exists(self.feedback_path):
            try:
                with open(self.feedback_path, "r") as f:
                    feedback_data = json.load(f)
            except Exception:
                pass
        
        # Append new entry
        feedback_data["entries"].append(feedback_entry)
        
        # Save updated feedback
        try:
            with open(self.feedback_path, "w") as f:
                json.dump(feedback_data, f, indent=2)
        except Exception:
            pass
    
    def get_feedback_history(self) -> List[Dict[str, Any]]:
        """Get recorded feedback history."""
        if os.path.exists(self.feedback_path):
            try:
                with open(self.feedback_path, "r") as f:
                    data = json.load(f)
                    return data.get("entries", [])
            except Exception:
                pass
        return []
    
    def clear_pending(self) -> None:
        """Clear all pending cards."""
        self.pending_cards.clear()


# ─── Global Instance ─────────────────────────────────────────────────────────

_hitl_manager: Optional[HITLManager] = None


def get_hitl_manager() -> HITLManager:
    """Get the global HITL manager instance."""
    global _hitl_manager
    if _hitl_manager is None:
        _hitl_manager = HITLManager()
    return _hitl_manager


# ─── Agent Helper Functions ──────────────────────────────────────────────────

def should_clarify(confidence: float) -> bool:
    """Check if agent should request clarification based on confidence."""
    return confidence < CONFIDENCE_THRESHOLD


def create_clarification(
    agent_name: str,
    context: str,
    options: List[str],
    reasoning: str,
    confidence: float = 0.0,
    metadata: Dict[str, Any] = None,
) -> ClarificationCard:
    """Create a clarification card."""
    return ClarificationCard(
        agent_name=agent_name,
        context=context,
        options=options,
        reasoning=reasoning,
        confidence=confidence,
        metadata=metadata or {},
    )


def request_human_input(card: ClarificationCard) -> str:
    """Request human input for a decision."""
    manager = get_hitl_manager()
    return manager.request_clarification(card)

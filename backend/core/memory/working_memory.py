"""
Working Memory — Short-term context for the current run.

Holds documents, messages, and decisions for the active workflow.
Used by agents to get relevant context (plan Phase 1.3).
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any
from pydantic import BaseModel

# Avoid circular import: use string refs or lazy import for Document/Message
# Document and Message are used for type hints and dict storage


class Decision(BaseModel):
    """A recorded decision in the workflow."""
    decision_id: str
    agent: str
    description: str
    context: Dict[str, Any] = {}
    timestamp: Optional[str] = None


class WorkingMemory:
    """Short-term context for the current run."""

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id
        self._documents: Dict[str, Any] = {}  # doc_id -> Document
        self.conversation_history: List[Any] = []  # Message objects
        self.decisions: List[Decision] = []
        self.current_focus: Optional[str] = None  # doc_id or task description

    def add_document(self, doc: Any) -> None:
        """Add a document to working memory."""
        self._documents[doc.doc_id] = doc

    def get_document(self, doc_id: str) -> Optional[Any]:
        """Get a document by ID."""
        return self._documents.get(doc_id)

    def add_message(self, msg: Any) -> None:
        """Append a message to conversation history."""
        self.conversation_history.append(msg)

    def add_decision(self, decision: Decision) -> None:
        """Record a decision."""
        self.decisions.append(decision)

    def _get_relevant_docs(self, agent_name: str) -> List[Any]:
        """Documents relevant to this agent (by type / run)."""
        # Simple strategy: all docs in this run
        return list(self._documents.values())

    def _get_recent_messages(self, agent_name: str, limit: int = 20) -> List[Any]:
        """Recent messages involving this agent."""
        recent = []
        for msg in reversed(self.conversation_history):
            if getattr(msg, "from_agent", None) == agent_name or getattr(msg, "to_agent", None) == agent_name:
                recent.append(msg)
                if len(recent) >= limit:
                    break
        return list(reversed(recent))

    def _get_run_metadata(self) -> Dict[str, Any]:
        """Basic run metadata."""
        return {
            "run_id": self.run_id,
            "doc_count": len(self._documents),
            "message_count": len(self.conversation_history),
            "decision_count": len(self.decisions),
        }

    def get_context_for_agent(self, agent_name: str) -> Dict[str, Any]:
        """Get relevant context for an agent."""
        return {
            "relevant_docs": self._get_relevant_docs(agent_name),
            "recent_messages": self._get_recent_messages(agent_name),
            "decisions": self.decisions,
            "run_metadata": self._get_run_metadata(),
            "current_focus": self.current_focus,
        }

    def clear(self) -> None:
        """Clear working memory (e.g. when run ends)."""
        self._documents.clear()
        self.conversation_history.clear()
        self.decisions.clear()
        self.current_focus = None

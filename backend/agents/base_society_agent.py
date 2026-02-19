"""
Base Society Agent — Document-driven agent society (MetaGPT-style).

Agents communicate via MessageBus and produce/consume Documents from DocumentStore.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import asyncio

from backend.core.communication.message_bus import MessageBus, Message
from backend.core.documents.base import Document, DocumentStore, DocumentType


class SocietyAgent(ABC):
    """Base class for all agents in the document-driven society."""

    def __init__(
        self,
        name: str,
        message_bus: MessageBus,
        document_store: DocumentStore,
    ) -> None:
        self.name = name
        self.message_bus = message_bus
        self.document_store = document_store
        self._inbox = message_bus.subscribe(name)
        self._running = False

    @property
    @abstractmethod
    def role(self) -> str:
        """Agent's role in the society."""
        pass

    @property
    @abstractmethod
    def capabilities(self) -> List[str]:
        """What this agent can do."""
        pass

    async def start(self) -> None:
        """Start the agent's message loop."""
        self._running = True
        asyncio.create_task(self._message_loop())

    async def stop(self) -> None:
        """Stop the agent."""
        self._running = False

    async def _message_loop(self) -> None:
        """Process incoming messages."""
        while self._running:
            try:
                message = await asyncio.wait_for(self._inbox.get(), timeout=1.0)
                response = await self.receive_message(message)
                if message.requires_response and response is not None:
                    await self.message_bus.publish(response)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                # Log but don't crash the loop
                import logging
                logging.getLogger(__name__).exception("Error in %s message loop: %s", self.name, e)

    @abstractmethod
    async def receive_message(self, msg: Message) -> Optional[Message]:
        """Handle incoming message — implement in subclass."""
        pass

    @abstractmethod
    async def execute_task(self, task: Dict[str, Any]) -> Document:
        """Execute the agent's main task — implement in subclass."""
        pass

    async def send_document(self, doc: Document, to_agent: str) -> None:
        """Send a document reference to another agent."""
        message = Message(
            from_agent=self.name,
            to_agent=to_agent,
            msg_type="document",
            payload={"doc_id": doc.doc_id},
        )
        await self.message_bus.publish(message)

    async def request_document(
        self,
        doc_type: DocumentType,
        from_agent: str,
        run_id: str,
        timeout: float = 30.0,
    ) -> Optional[Document]:
        """Request a document from another agent."""
        message = Message(
            from_agent=self.name,
            to_agent=from_agent,
            msg_type="request_document",
            payload={"doc_type": doc_type.value, "run_id": run_id},
        )
        try:
            response = await self.message_bus.request_response(message, timeout=timeout)
        except asyncio.TimeoutError:
            return None
        if response is not None and "doc_id" in response.payload:
            return self.document_store.get(response.payload["doc_id"])
        return None

    async def ask_clarification(self, question: str, to_agent: str, timeout: float = 60.0) -> str:
        """Ask another agent for clarification."""
        message = Message(
            from_agent=self.name,
            to_agent=to_agent,
            msg_type="question",
            payload={"question": question},
        )
        try:
            response = await self.message_bus.request_response(message, timeout=timeout)
        except asyncio.TimeoutError:
            return ""
        return response.payload.get("answer", "") if response else ""

    async def provide_feedback(self, doc_id: str, feedback: str, to_agent: str) -> None:
        """Give feedback on a document."""
        message = Message(
            from_agent=self.name,
            to_agent=to_agent,
            msg_type="feedback",
            payload={"doc_id": doc_id, "feedback": feedback},
        )
        await self.message_bus.publish(message)

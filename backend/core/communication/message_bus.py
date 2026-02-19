"""
Message Bus — Pub/sub for agent society communication.

Agents send documents, questions, and feedback through the bus.
Enables request/response and conversation history.
"""

from __future__ import annotations
import asyncio
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from uuid import uuid4


class Message(BaseModel):
    """Message between agents in the society."""
    msg_id: str = Field(default_factory=lambda: f"msg_{uuid4().hex[:8]}")
    from_agent: str
    to_agent: str
    msg_type: str  # "document", "question", "feedback", "command", "request_document", "answer"
    payload: Dict[str, Any]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    requires_response: bool = False
    in_response_to: Optional[str] = None


# Maximum number of messages to keep in history (prevents memory leak)
MAX_HISTORY_SIZE = 10000


class MessageBus:
    """Pub/sub system for agent communication.
    
    Features:
    - Pub/sub messaging between agents
    - Request/response pattern support
    - Conversation history with automatic size limiting
    """

    def __init__(self, max_history: int = MAX_HISTORY_SIZE) -> None:
        self._subscribers: Dict[str, List[asyncio.Queue]] = {}
        self._history: List[Message] = []
        self._response_handlers: Dict[str, asyncio.Future] = {}
        self._max_history = max_history

    async def publish(self, message: Message) -> None:
        """Publish message to subscribers."""
        self._history.append(message)
        
        # CRITICAL FIX: Prevent memory leak by limiting history size
        # Remove oldest messages when history exceeds max size
        if len(self._history) > self._max_history:
            # Remove oldest 20% of messages to avoid frequent trimming
            trim_count = self._max_history // 5
            self._history = self._history[trim_count:]

        if message.to_agent in self._subscribers:
            for queue in self._subscribers[message.to_agent]:
                await queue.put(message)

        if message.in_response_to and message.in_response_to in self._response_handlers:
            future = self._response_handlers[message.in_response_to]
            if not future.done():
                future.set_result(message)
            del self._response_handlers[message.in_response_to]

    def subscribe(self, agent_name: str) -> asyncio.Queue:
        """Agent subscribes to receive messages."""
        queue: asyncio.Queue = asyncio.Queue()
        if agent_name not in self._subscribers:
            self._subscribers[agent_name] = []
        self._subscribers[agent_name].append(queue)
        return queue

    async def request_response(self, message: Message, timeout: float = 30.0) -> Message:
        """Send message and wait for a response."""
        message.requires_response = True
        future: asyncio.Future = asyncio.get_running_loop().create_future()
        self._response_handlers[message.msg_id] = future
        await self.publish(message)
        try:
            response = await asyncio.wait_for(future, timeout=timeout)
            return response
        except asyncio.TimeoutError:
            if message.msg_id in self._response_handlers:
                del self._response_handlers[message.msg_id]
            raise

    def get_conversation(self, between: tuple[str, str]) -> List[Message]:
        """Get conversation between two agents."""
        a1, a2 = between
        return [
            m
            for m in self._history
            if (m.from_agent == a1 and m.to_agent == a2) or (m.from_agent == a2 and m.to_agent == a1)
        ]

    def get_all_messages(self, agent: str) -> List[Message]:
        """Get all messages to or from an agent."""
        return [m for m in self._history if m.from_agent == agent or m.to_agent == agent]

    def get_history(self) -> List[Message]:
        """Get full message history (e.g. for debugging)."""
        return list(self._history)

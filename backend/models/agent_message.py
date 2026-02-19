"""
AgentMessage Model - Agent thoughts, actions, and communication.
MetaGPT-style: Agents have memory and reasoning trails.
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum

from backend.database import Base


class MessageType(str, Enum):
    """Types of agent messages"""
    THOUGHT = "thought"       # Internal reasoning
    PLAN = "plan"            # Architecture/plan output
    ACTION = "action"        # Task being executed
    RESULT = "result"        # Execution result
    ERROR = "error"          # Error message
    USER = "user"            # User input
    SYSTEM = "system"        # System notification


class SenderType(str, Enum):
    """Who sent the message"""
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"


class AgentMessage(Base):
    """
    Captures agent thoughts, actions, and communication.
    This is the "memory" and "conversation" layer.
    """
    __tablename__ = "agent_messages"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id", ondelete="SET NULL"), nullable=True, index=True)
    run_id = Column(Integer, ForeignKey("project_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Message content
    sender = Column(SQLEnum(SenderType), nullable=False, default=SenderType.AGENT)
    message_type = Column(SQLEnum(MessageType), nullable=False, default=MessageType.THOUGHT)
    content = Column(Text, nullable=False)
    
    # Optional metadata (JSON-serializable)
    metadata_json = Column(Text, nullable=True)  # Store extra context as JSON
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    agent = relationship("Agent", back_populates="messages")
    project = relationship("Project", back_populates="agent_messages")

    def __repr__(self) -> str:
        preview = self.content[:50] if self.content else ""
        return f"<AgentMessage id={self.id} type={self.message_type} sender={self.sender} '{preview}...'>"

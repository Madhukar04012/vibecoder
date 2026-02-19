"""
Role - MetaGPT-Style Base Agent Class

Inspired by MetaGPT's Role implementation with actions, memory, and watch patterns.
Each role is a specialized AI agent with specific responsibilities.

Usage:
    class Engineer(Role):
        name = "engineer"
        profile = "Senior Software Engineer"
        goal = "Write production-quality code"
        
        def __init__(self):
            super().__init__()
            self.set_actions([WriteCode, ReviewCode])
            self._watch([ArchitectureDesign])
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Type, Callable
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import json

from pydantic import BaseModel, Field


class RoleState(str, Enum):
    """Role execution states."""
    IDLE = "idle"
    THINKING = "thinking"
    WORKING = "working"
    REVIEWING = "reviewing"
    WAITING = "waiting"
    DONE = "done"
    ERROR = "error"


@dataclass
class Message:
    """Message passed between agents."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    role: str = ""  # sender role name
    cause_by: str = ""  # action that caused this message
    sent_to: str = ""  # recipient role name (empty = broadcast)
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "role": self.role,
            "cause_by": self.cause_by,
            "sent_to": self.sent_to,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class RoleContext:
    """Runtime context for a role."""
    env: Any = None  # Environment reference
    memory: List[Message] = field(default_factory=list)
    working_memory: List[Message] = field(default_factory=list)
    state: int = -1  # Current action index, -1 = idle
    todo: Any = None  # Current action to execute
    news: List[Message] = field(default_factory=list)  # New messages to process
    watch: Set[str] = field(default_factory=set)  # Actions to watch for
    
    @property
    def history(self) -> List[Message]:
        """Get all messages in memory."""
        return self.memory.copy()
    
    @property
    def important_memory(self) -> List[Message]:
        """Get messages that match watched actions."""
        return [m for m in self.memory if m.cause_by in self.watch]


class Action(ABC):
    """Base class for role actions."""
    
    name: str = "action"
    description: str = ""
    
    def __init__(self, context: Optional[RoleContext] = None):
        self.context = context
        self.result: Any = None
    
    @abstractmethod
    async def run(self, *args, **kwargs) -> Any:
        """Execute the action."""
        pass
    
    def __str__(self) -> str:
        return self.name


class Role(ABC):
    """
    Base Role class - MetaGPT-style agent.
    
    Each role has:
    - A profile (job title)
    - A goal (what they're trying to achieve)
    - Constraints (rules they follow)
    - Actions (what they can do)
    - Watch list (what triggers them)
    - Memory (conversation history)
    """
    
    # Class attributes (override in subclass)
    name: str = "role"
    profile: str = "Role"
    goal: str = "Accomplish the task"
    constraints: str = "Follow best practices"
    desc: str = ""
    icon: str = "brain"  # Lucide icon name
    color: str = "#3b82f6"  # Badge color
    
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.rc = RoleContext()
        self.actions: List[Type[Action]] = []
        self.state = RoleState.IDLE
        self._event_callbacks: List[Callable] = []
    
    # ─── Configuration ────────────────────────────────────────────────────────
    
    def set_actions(self, actions: List[Type[Action]]) -> None:
        """Set the actions this role can perform."""
        self.actions = actions
        if actions:
            self.rc.state = 0
    
    def _watch(self, actions: List[Type[Action]]) -> None:
        """Subscribe to messages caused by these actions."""
        self.rc.watch = {a.name if hasattr(a, 'name') else a.__name__ for a in actions}
    
    def set_env(self, env: Any) -> None:
        """Set the environment reference."""
        self.rc.env = env
    
    def on_event(self, callback: Callable) -> None:
        """Register event callback for UI updates."""
        self._event_callbacks.append(callback)
    
    def emit(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Emit event to all registered callbacks."""
        for cb in self._event_callbacks:
            try:
                cb(event_type, {"role": self.name, **payload})
            except Exception:
                pass
    
    # ─── Message Handling ─────────────────────────────────────────────────────
    
    def put_message(self, message: Message) -> None:
        """Receive a message into the buffer."""
        self.rc.news.append(message)
    
    def get_memories(self, k: int = 0) -> List[Message]:
        """Get k most recent memories (0 = all)."""
        if k == 0:
            return self.rc.memory.copy()
        return self.rc.memory[-k:]
    
    async def _observe(self) -> int:
        """
        Observe new messages in buffer.
        Returns count of relevant messages.
        """
        news = self.rc.news
        self.rc.news = []
        
        # Filter to watched messages only
        relevant = [m for m in news if m.cause_by in self.rc.watch or not self.rc.watch]
        
        # Add to memory
        self.rc.memory.extend(relevant)
        self.rc.working_memory = relevant
        
        return len(relevant)
    
    async def _think(self) -> bool:
        """
        Decide what action to take next.
        Returns True if there's work to do.
        """
        if not self.actions:
            return False
        
        # Simple sequential action selection
        if self.rc.state < 0:
            self.rc.state = 0
        
        if self.rc.state >= len(self.actions):
            self.rc.state = 0
            return False
        
        self.rc.todo = self.actions[self.rc.state](context=self.rc)
        return True
    
    async def _act(self) -> Message:
        """Execute the current action."""
        if not self.rc.todo:
            return Message(content="No action to perform", role=self.name)
        
        self.state = RoleState.WORKING
        self.emit("state_change", {"state": self.state.value})
        
        try:
            result = await self.rc.todo.run()
            self.rc.state += 1
            
            msg = Message(
                content=str(result) if result else "Action completed",
                role=self.name,
                cause_by=self.rc.todo.name,
            )
            
            self.state = RoleState.DONE
            self.emit("state_change", {"state": self.state.value})
            
            return msg
            
        except Exception as e:
            self.state = RoleState.ERROR
            self.emit("error", {"message": str(e)})
            return Message(content=f"Error: {e}", role=self.name)
    
    async def _react(self) -> Message:
        """
        React loop: think then act.
        Standard ReAct pattern.
        """
        self.state = RoleState.THINKING
        self.emit("state_change", {"state": self.state.value})
        
        has_work = await self._think()
        if not has_work:
            return Message(content="Nothing to do", role=self.name)
        
        return await self._act()
    
    async def run(self, message: Optional[Message] = None) -> Message:
        """
        Main entry point for role execution.
        
        Args:
            message: Optional incoming message to process
            
        Returns:
            Result message
        """
        if message:
            self.put_message(message)
        
        # Observe new messages
        await self._observe()
        
        # React to messages
        result = await self._react()
        
        # Publish result to environment
        if self.rc.env:
            self.rc.env.publish_message(result)
        
        return result
    
    # ─── Serialization ────────────────────────────────────────────────────────
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize role state."""
        return {
            "id": self.id,
            "name": self.name,
            "profile": self.profile,
            "goal": self.goal,
            "icon": self.icon,
            "color": self.color,
            "state": self.state.value,
            "action_count": len(self.actions),
            "memory_count": len(self.rc.memory),
        }
    
    def __str__(self) -> str:
        return f"{self.profile}({self.name})"
    
    def __repr__(self) -> str:
        return self.__str__()


# ─── Common Actions ───────────────────────────────────────────────────────────

class UserRequirement(Action):
    """Action representing user's initial requirement."""
    name = "user_requirement"
    description = "User's project requirement"
    
    async def run(self, requirement: str = "") -> str:
        return requirement


class WritePRD(Action):
    """Write Product Requirements Document."""
    name = "write_prd"
    description = "Create a detailed PRD"
    
    async def run(self, *args, **kwargs) -> Dict[str, Any]:
        # Implemented by ProductManager
        return {}


class WriteDesign(Action):
    """Write system design."""
    name = "write_design"
    description = "Create system architecture"
    
    async def run(self, *args, **kwargs) -> Dict[str, Any]:
        # Implemented by Architect
        return {}


class WriteCode(Action):
    """Write code implementation."""
    name = "write_code"
    description = "Write production code"
    
    async def run(self, *args, **kwargs) -> str:
        # Implemented by Engineer
        return ""


class WriteTest(Action):
    """Write tests."""
    name = "write_test"
    description = "Write test cases"
    
    async def run(self, *args, **kwargs) -> str:
        # Implemented by QA Engineer
        return ""


class ReviewCode(Action):
    """Review code for quality."""
    name = "review_code"
    description = "Review and critique code"
    
    async def run(self, *args, **kwargs) -> Dict[str, Any]:
        # Implemented by QA Engineer
        return {}

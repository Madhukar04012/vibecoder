"""
Environment - Shared Workspace for Multi-Agent Communication

Inspired by MetaGPT's Environment class. Provides:
- Message routing between agents
- Artifact storage (files, diagrams, etc.)
- Blackboard pattern for shared state
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from backend.engine.role import Role, Message


@dataclass
class Artifact:
    """An artifact produced by an agent."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = ""  # prd, design, code, test, deployment
    name: str = ""
    content: str = ""
    path: Optional[str] = None
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "content": self.content[:500] if self.content else "",
            "path": self.path,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }


class Environment:
    """
    Shared environment for multi-agent collaboration.
    
    Acts as a message broker and artifact store.
    """
    
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.roles: Dict[str, Role] = {}
        self.memory: List[Message] = []
        self.message_queue: List[Message] = []
        self.artifacts: Dict[str, Artifact] = {}
        self.blackboard: Dict[str, Any] = {}  # Shared state
        
    # ─── Role Management ──────────────────────────────────────────────────────
    
    def add_role(self, role: Role) -> None:
        """Add a role to the environment."""
        self.roles[role.name] = role
        role.set_env(self)
    
    def remove_role(self, role: Role) -> None:
        """Remove a role from the environment."""
        if role.name in self.roles:
            del self.roles[role.name]
    
    def get_role(self, name: str) -> Optional[Role]:
        """Get a role by name."""
        return self.roles.get(name)
    
    # ─── Message Passing ──────────────────────────────────────────────────────
    
    def publish_message(self, message: Message) -> None:
        """
        Publish a message to the environment.
        
        Messages are stored in memory and queued for delivery.
        """
        self.memory.append(message)
        self.message_queue.append(message)
    
    def get_messages_for_role(self, role: Role) -> List[Message]:
        """
        Get messages that a role should process.
        
        Filters based on:
        - Direct messages (sent_to matches role)
        - Watched actions (cause_by in role's watch set)
        - Broadcasts (no sent_to)
        """
        messages = []
        remaining = []
        
        for msg in self.message_queue:
            # Direct message to this role
            if msg.sent_to == role.name:
                messages.append(msg)
            # Broadcast that matches watch list
            elif not msg.sent_to and (not role.rc.watch or msg.cause_by in role.rc.watch):
                messages.append(msg)
            else:
                remaining.append(msg)
        
        # Remove delivered messages from queue
        self.message_queue = remaining
        return messages
    
    def has_pending_messages(self) -> bool:
        """Check if there are undelivered messages."""
        return len(self.message_queue) > 0
    
    def get_history(self, k: int = 0) -> List[Message]:
        """Get message history (0 = all)."""
        if k == 0:
            return self.memory.copy()
        return self.memory[-k:]
    
    # ─── Artifact Management ──────────────────────────────────────────────────
    
    def store_artifact(self, artifact: Artifact) -> str:
        """Store an artifact and return its ID."""
        self.artifacts[artifact.id] = artifact
        return artifact.id
    
    def get_artifact(self, artifact_id: str) -> Optional[Artifact]:
        """Get an artifact by ID."""
        return self.artifacts.get(artifact_id)
    
    def get_artifacts(self, type_filter: Optional[str] = None) -> List[Artifact]:
        """Get all artifacts, optionally filtered by type."""
        if type_filter:
            return [a for a in self.artifacts.values() if a.type == type_filter]
        return list(self.artifacts.values())
    
    def get_artifacts_by_role(self, role_name: str) -> List[Artifact]:
        """Get artifacts created by a specific role."""
        return [a for a in self.artifacts.values() if a.created_by == role_name]
    
    # ─── Blackboard (Shared State) ────────────────────────────────────────────
    
    def set_state(self, key: str, value: Any) -> None:
        """Set a value in the shared blackboard."""
        self.blackboard[key] = value
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """Get a value from the shared blackboard."""
        return self.blackboard.get(key, default)
    
    def has_state(self, key: str) -> bool:
        """Check if a key exists in the blackboard."""
        return key in self.blackboard
    
    # ─── Convenience Methods ──────────────────────────────────────────────────
    
    def store_file(self, path: str, content: str, created_by: str) -> Artifact:
        """Store a file artifact."""
        artifact = Artifact(
            type="code",
            name=path.split("/")[-1],
            content=content,
            path=path,
            created_by=created_by,
        )
        self.store_artifact(artifact)
        return artifact
    
    def store_prd(self, content: Dict[str, Any], created_by: str) -> Artifact:
        """Store a PRD artifact."""
        import json
        artifact = Artifact(
            type="prd",
            name="Product Requirements Document",
            content=json.dumps(content, indent=2),
            created_by=created_by,
            metadata=content,
        )
        self.store_artifact(artifact)
        return artifact
    
    def store_design(self, content: Dict[str, Any], created_by: str) -> Artifact:
        """Store a design artifact."""
        import json
        artifact = Artifact(
            type="design",
            name="System Design",
            content=json.dumps(content, indent=2),
            created_by=created_by,
            metadata=content,
        )
        self.store_artifact(artifact)
        return artifact
    
    def get_prd(self) -> Optional[Dict[str, Any]]:
        """Get the PRD from artifacts."""
        prds = self.get_artifacts("prd")
        if prds:
            return prds[-1].metadata
        return None
    
    def get_design(self) -> Optional[Dict[str, Any]]:
        """Get the design from artifacts."""
        designs = self.get_artifacts("design")
        if designs:
            return designs[-1].metadata
        return None
    
    def get_files(self) -> Dict[str, str]:
        """Get all code files as {path: content}."""
        files = {}
        for artifact in self.get_artifacts("code"):
            if artifact.path:
                files[artifact.path] = artifact.content
        return files
    
    # ─── Serialization ────────────────────────────────────────────────────────
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize environment state."""
        return {
            "id": self.id,
            "role_count": len(self.roles),
            "message_count": len(self.memory),
            "pending_messages": len(self.message_queue),
            "artifact_count": len(self.artifacts),
            "blackboard_keys": list(self.blackboard.keys()),
        }

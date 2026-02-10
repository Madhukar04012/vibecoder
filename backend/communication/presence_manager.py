"""
Presence Manager — Phase 5

Live presence tracking for users and agents.

Shows:
- Who is in the workspace
- What file they're viewing
- Their cursor position
- Agent ghost cursors

Usage:
    presence = get_presence_manager()
    presence.update("user_123", {"file": "main.py", "line": 42})
    all_presence = presence.list()
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from backend.engine.events import get_event_emitter, EngineEventType


# ─── Constants ───────────────────────────────────────────────────────────────

PRESENCE_TIMEOUT = 60  # Seconds before presence expires


# ─── User Type ───────────────────────────────────────────────────────────────

class UserType(Enum):
    HUMAN = "human"
    AGENT = "agent"


# ─── Presence Entry ──────────────────────────────────────────────────────────

@dataclass
class PresenceEntry:
    """Presence information for a user or agent."""
    user_id: str
    user_type: UserType
    display_name: str
    color: str
    file: str = ""
    line: int = 0
    column: int = 0
    status: str = "active"  # active, idle, busy
    last_seen: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "user_type": self.user_type.value,
            "display_name": self.display_name,
            "color": self.color,
            "file": self.file,
            "line": self.line,
            "column": self.column,
            "status": self.status,
            "last_seen": self.last_seen,
        }


# ─── Presence Manager ────────────────────────────────────────────────────────

class PresenceManager:
    """
    Manages live presence for workspace collaboration.
    
    Tracks:
    - Human users
    - Agent cursors (ghost cursors)
    - Active file per user
    - Status (active/idle/busy)
    """
    
    # Predefined colors for users/agents
    COLORS = [
        "#3b82f6",  # blue
        "#10b981",  # green
        "#f59e0b",  # amber
        "#8b5cf6",  # purple
        "#ef4444",  # red
        "#06b6d4",  # cyan
        "#ec4899",  # pink
        "#84cc16",  # lime
    ]
    
    def __init__(self):
        self.presence: Dict[str, PresenceEntry] = {}
        self._color_index = 0
        self.events = get_event_emitter()
    
    def _get_color(self) -> str:
        """Get next color in rotation."""
        color = self.COLORS[self._color_index % len(self.COLORS)]
        self._color_index += 1
        return color
    
    def update(
        self,
        user_id: str,
        location: Dict[str, Any],
        user_type: UserType = UserType.HUMAN,
        display_name: str = "",
    ) -> PresenceEntry:
        """
        Update presence for a user.
        
        Args:
            user_id: Unique user identifier
            location: {"file": str, "line": int, "column": int, "status": str}
            user_type: HUMAN or AGENT
            display_name: Display name for UI
            
        Returns:
            Updated presence entry
        """
        now = datetime.utcnow().isoformat()
        
        if user_id in self.presence:
            entry = self.presence[user_id]
            entry.file = location.get("file", entry.file)
            entry.line = location.get("line", entry.line)
            entry.column = location.get("column", entry.column)
            entry.status = location.get("status", entry.status)
            entry.last_seen = now
        else:
            entry = PresenceEntry(
                user_id=user_id,
                user_type=user_type,
                display_name=display_name or user_id,
                color=self._get_color(),
                file=location.get("file", ""),
                line=location.get("line", 0),
                column=location.get("column", 0),
                status=location.get("status", "active"),
                last_seen=now,
            )
            self.presence[user_id] = entry
        
        self._emit_event("PRESENCE_UPDATED", entry.to_dict())
        return entry
    
    def remove(self, user_id: str) -> bool:
        """Remove a user from presence."""
        if user_id in self.presence:
            del self.presence[user_id]
            self._emit_event("PRESENCE_REMOVED", {"user_id": user_id})
            return True
        return False
    
    def list(self, include_expired: bool = False) -> List[Dict[str, Any]]:
        """
        List all presence entries.
        
        Args:
            include_expired: If True, include stale entries
            
        Returns:
            List of presence dicts
        """
        result = []
        cutoff = datetime.utcnow() - timedelta(seconds=PRESENCE_TIMEOUT)
        
        for user_id, entry in list(self.presence.items()):
            if not include_expired:
                try:
                    last_seen = datetime.fromisoformat(entry.last_seen)
                    if last_seen < cutoff:
                        # Clean up expired entry
                        del self.presence[user_id]
                        continue
                except Exception:
                    pass
            
            result.append(entry.to_dict())
        
        return result
    
    def get(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get presence for a specific user."""
        if user_id in self.presence:
            return self.presence[user_id].to_dict()
        return None
    
    def get_users_in_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Get all users viewing a specific file."""
        return [
            entry.to_dict()
            for entry in self.presence.values()
            if entry.file == file_path
        ]
    
    def get_agents(self) -> List[Dict[str, Any]]:
        """Get all agent presence entries."""
        return [
            entry.to_dict()
            for entry in self.presence.values()
            if entry.user_type == UserType.AGENT
        ]
    
    def get_humans(self) -> List[Dict[str, Any]]:
        """Get all human presence entries."""
        return [
            entry.to_dict()
            for entry in self.presence.values()
            if entry.user_type == UserType.HUMAN
        ]
    
    def _emit_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Emit presence event."""
        self.events.emit(EngineEventType.AGENT_STATUS, {
            "agent": "presence_manager",
            "event": event_type,
            **payload,
        })


# ─── Global Instance ─────────────────────────────────────────────────────────

_presence_manager: Optional[PresenceManager] = None


def get_presence_manager() -> PresenceManager:
    """Get global presence manager instance."""
    global _presence_manager
    if _presence_manager is None:
        _presence_manager = PresenceManager()
    return _presence_manager

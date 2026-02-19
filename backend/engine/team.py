"""
Team - Multi-Agent Orchestrator

Inspired by MetaGPT's Team class. Manages a group of AI agents
that collaborate on software development tasks.

Usage:
    team = Team()
    team.hire([TeamLead(), ProductManager(), Architect(), Engineer()])
    result = await team.run("Build a todo app")
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import uuid

from backend.engine.role import Role, Message, RoleState
from backend.engine.environment import Environment


@dataclass
class TeamConfig:
    """Team configuration."""
    max_rounds: int = 10
    budget_usd: float = 5.0
    parallel_execution: bool = False
    emit_discussions: bool = True


class Team:
    """
    Multi-agent team orchestrator.
    
    Manages hiring agents, running projects, and tracking progress.
    """
    
    def __init__(self, config: Optional[TeamConfig] = None):
        self.id = str(uuid.uuid4())
        self.config = config or TeamConfig()
        self.env = Environment()
        self.roles: Dict[str, Role] = {}
        self.idea: str = ""
        self.round: int = 0
        self.is_running: bool = False
        self._event_callbacks: List[Callable] = []
        
    # ─── Team Management ──────────────────────────────────────────────────────
    
    def hire(self, roles: List[Role]) -> None:
        """Add roles to the team."""
        for role in roles:
            role.set_env(self.env)
            role.on_event(self._forward_event)
            self.roles[role.name] = role
            self.env.add_role(role)
        
        self._emit("team_updated", {
            "roles": [r.to_dict() for r in self.roles.values()]
        })
    
    def fire(self, role_name: str) -> None:
        """Remove a role from the team."""
        if role_name in self.roles:
            role = self.roles.pop(role_name)
            self.env.remove_role(role)
            self._emit("team_updated", {
                "roles": [r.to_dict() for r in self.roles.values()]
            })
    
    def get_role(self, name: str) -> Optional[Role]:
        """Get a role by name."""
        return self.roles.get(name)
    
    # ─── Event System ─────────────────────────────────────────────────────────
    
    def on_event(self, callback: Callable) -> None:
        """Register event callback."""
        self._event_callbacks.append(callback)
    
    def _emit(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Emit event to all callbacks."""
        event = {
            "type": event_type,
            "team_id": self.id,
            "round": self.round,
            "timestamp": datetime.now().isoformat(),
            **payload
        }
        for cb in self._event_callbacks:
            try:
                cb(event)
            except Exception:
                pass
    
    def _forward_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Forward role events to team callbacks."""
        self._emit(f"role_{event_type}", payload)
    
    # ─── Execution ────────────────────────────────────────────────────────────
    
    async def run(self, idea: str, n_round: int = 0) -> Dict[str, Any]:
        """
        Run the team on a project idea.
        
        Args:
            idea: Project description
            n_round: Max rounds (0 = use config default)
            
        Returns:
            Result with artifacts, costs, etc.
        """
        self.idea = idea
        self.round = 0
        self.is_running = True
        max_rounds = n_round or self.config.max_rounds
        
        self._emit("run_started", {"idea": idea, "max_rounds": max_rounds})
        
        # Publish initial requirement
        initial_msg = Message(
            content=idea,
            role="user",
            cause_by="user_requirement",
        )
        self.env.publish_message(initial_msg)
        
        try:
            while self.round < max_rounds and self.is_running:
                self.round += 1
                self._emit("round_started", {"round": self.round})
                
                # Run all roles that have work to do
                if self.config.parallel_execution:
                    await self._run_parallel()
                else:
                    await self._run_sequential()
                
                # Check if done (no messages in flight)
                if not self.env.has_pending_messages():
                    self._emit("run_completed", {
                        "rounds": self.round,
                        "artifacts": self.env.get_artifacts(),
                    })
                    break
                
                self._emit("round_completed", {"round": self.round})
            
        except Exception as e:
            self._emit("run_error", {"error": str(e)})
            raise
        finally:
            self.is_running = False
        
        return {
            "success": True,
            "rounds": self.round,
            "artifacts": self.env.get_artifacts(),
            "messages": [m.to_dict() for m in self.env.memory],
        }
    
    async def _run_sequential(self) -> None:
        """Run roles sequentially based on SOP order."""
        # Standard SOP order
        sop_order = [
            "team_leader",
            "product_manager", 
            "architect",
            "project_manager",
            "engineer",
            "qa_engineer",
            "devops",
        ]
        
        for role_name in sop_order:
            if role_name in self.roles:
                role = self.roles[role_name]
                
                # Check if role has messages to process
                if self.env.get_messages_for_role(role):
                    self._emit("role_started", {
                        "role": role.name,
                        "profile": role.profile,
                        "icon": role.icon,
                    })
                    
                    # Deliver messages
                    for msg in self.env.get_messages_for_role(role):
                        role.put_message(msg)
                    
                    # Run role
                    result = await role.run()
                    
                    # Emit discussion if enabled
                    if self.config.emit_discussions and result.content:
                        self._emit("discussion", {
                            "from": role.name,
                            "from_profile": role.profile,
                            "icon": role.icon,
                            "message": result.content[:500],
                        })
    
    async def _run_parallel(self) -> None:
        """Run independent roles in parallel."""
        tasks = []
        for role in self.roles.values():
            if self.env.get_messages_for_role(role):
                for msg in self.env.get_messages_for_role(role):
                    role.put_message(msg)
                tasks.append(role.run())
        
        if tasks:
            await asyncio.gather(*tasks)
    
    def stop(self) -> None:
        """Stop the current run."""
        self.is_running = False
        self._emit("run_stopped", {"round": self.round})
    
    # ─── Serialization ────────────────────────────────────────────────────────
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize team state."""
        return {
            "id": self.id,
            "roles": [r.to_dict() for r in self.roles.values()],
            "round": self.round,
            "is_running": self.is_running,
            "idea": self.idea,
        }


# ─── Default Team Factory ─────────────────────────────────────────────────────

def create_software_team() -> Team:
    """Create a default software development team."""
    from backend.engine.roles import (
        TeamLeader,
        ProductManagerRole,
        ArchitectRole,
        EngineerRole,
        QAEngineerRole,
        DevOpsRole,
    )
    
    team = Team()
    team.hire([
        TeamLeader(),
        ProductManagerRole(),
        ArchitectRole(),
        EngineerRole(),
        QAEngineerRole(),
        DevOpsRole(),
    ])
    return team

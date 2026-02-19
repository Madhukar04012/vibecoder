"""
Fleet Manager — Phase 5

Multi-agent orchestration with Team Lead pattern.

Provides:
- Fleet spawning and management
- Task distribution to agent groups
- Result aggregation
- Hierarchical coordination

Usage:
    fleet = FleetManager()
    fleet.spawn_fleet("security", [sec_agent, dep_agent])
    results = fleet.dispatch("security", task)

Team Lead Pattern:
    One TeamLeadAgent delegates to fleets, summarizes results,
    and talks to the engine only.
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import concurrent.futures

from backend.engine.events import get_event_emitter, EngineEventType


# ─── Constants ───────────────────────────────────────────────────────────────

MAX_PARALLEL_AGENTS = 10
DISPATCH_TIMEOUT = 300  # 5 minutes


# ─── Agent State ─────────────────────────────────────────────────────────────

class AgentState(Enum):
    IDLE = "idle"
    BUSY = "busy"
    BLOCKED = "blocked"
    ERROR = "error"


# ─── Fleet Member ────────────────────────────────────────────────────────────

@dataclass
class FleetMember:
    """A member of a fleet."""
    agent: Any  # BaseAgent
    state: AgentState = AgentState.IDLE
    last_task: str = ""
    task_count: int = 0
    error_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": getattr(self.agent, "name", str(self.agent)),
            "state": self.state.value,
            "last_task": self.last_task,
            "task_count": self.task_count,
            "error_count": self.error_count,
        }


# ─── Fleet ───────────────────────────────────────────────────────────────────

@dataclass
class Fleet:
    """A group of agents working together."""
    name: str
    members: List[FleetMember] = field(default_factory=list)
    team_lead: Optional[Any] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    task_history: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_agent(self, agent: Any) -> None:
        """Add an agent to the fleet."""
        self.members.append(FleetMember(agent=agent))
    
    def get_idle_agents(self) -> List[FleetMember]:
        """Get agents ready to work."""
        return [m for m in self.members if m.state == AgentState.IDLE]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "members": [m.to_dict() for m in self.members],
            "team_lead": getattr(self.team_lead, "name", None) if self.team_lead else None,
            "created_at": self.created_at,
            "task_count": len(self.task_history),
        }


# ─── Fleet Manager ───────────────────────────────────────────────────────────

class FleetManager:
    """
    Manages multiple agent fleets with hierarchical coordination.
    
    Features:
    - Fleet spawning
    - Parallel task dispatch
    - Result aggregation
    - Team Lead pattern support
    """
    
    def __init__(self):
        self.fleets: Dict[str, Fleet] = {}
        self.events = get_event_emitter()
        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=MAX_PARALLEL_AGENTS
        )
    
    def spawn_fleet(
        self,
        name: str,
        agents: List[Any],
        team_lead: Optional[Any] = None,
    ) -> Fleet:
        """
        Create a new fleet of agents.
        
        Args:
            name: Fleet identifier
            agents: List of agent instances
            team_lead: Optional team lead agent
            
        Returns:
            Fleet instance
        """
        fleet = Fleet(name=name, team_lead=team_lead)
        for agent in agents:
            fleet.add_agent(agent)
        
        self.fleets[name] = fleet
        
        self._emit_event("FLEET_SPAWNED", {
            "fleet": name,
            "size": len(agents),
            "has_lead": team_lead is not None,
        })
        
        return fleet
    
    def disband_fleet(self, name: str) -> bool:
        """Remove a fleet."""
        if name in self.fleets:
            del self.fleets[name]
            self._emit_event("FLEET_DISBANDED", {"fleet": name})
            return True
        return False
    
    def dispatch(
        self,
        fleet_name: str,
        task: Dict[str, Any],
        parallel: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Dispatch a task to all agents in a fleet.
        
        Args:
            fleet_name: Name of fleet to dispatch to
            task: Task definition
            parallel: If True, run agents in parallel
            
        Returns:
            List of results from each agent
        """
        if fleet_name not in self.fleets:
            raise ValueError(f"Fleet not found: {fleet_name}")
        
        fleet = self.fleets[fleet_name]
        
        self._emit_event("FLEET_DISPATCH", {
            "fleet": fleet_name,
            "task": str(task)[:100],
            "agent_count": len(fleet.members),
        })
        
        results = []
        
        if parallel:
            # Run agents in parallel
            futures = []
            for member in fleet.members:
                member.state = AgentState.BUSY
                future = self._executor.submit(
                    self._run_agent, member, task
                )
                futures.append((member, future))
            
            # Collect results
            for member, future in futures:
                try:
                    result = future.result(timeout=DISPATCH_TIMEOUT)
                    results.append(result)
                    member.state = AgentState.IDLE
                    member.task_count += 1
                except Exception as e:
                    results.append({"error": str(e), "agent": member.to_dict()})
                    member.state = AgentState.ERROR
                    member.error_count += 1
        else:
            # Run agents sequentially
            for member in fleet.members:
                member.state = AgentState.BUSY
                try:
                    result = self._run_agent(member, task)
                    results.append(result)
                    member.task_count += 1
                except Exception as e:
                    results.append({"error": str(e)})
                    member.error_count += 1
                finally:
                    member.state = AgentState.IDLE
        
        # Record in history
        fleet.task_history.append({
            "task": str(task)[:200],
            "results": len(results),
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        # If team lead exists, have them summarize
        if fleet.team_lead:
            summary = self._summarize_with_lead(fleet.team_lead, task, results)
            results = [{"summary": summary, "raw_results": results}]
        
        self._emit_event("FLEET_COMPLETE", {
            "fleet": fleet_name,
            "result_count": len(results),
        })
        
        return results
    
    def _run_agent(self, member: FleetMember, task: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single agent with a task."""
        agent = member.agent
        member.last_task = str(task)[:100]
        
        # Call agent's run method
        if hasattr(agent, 'run'):
            return agent.run(task)
        elif hasattr(agent, 'execute'):
            return agent.execute(task)
        else:
            return {"result": str(agent)}
    
    def _summarize_with_lead(
        self,
        team_lead: Any,
        task: Dict[str, Any],
        results: List[Dict[str, Any]]
    ) -> str:
        """Have team lead summarize fleet results."""
        if hasattr(team_lead, 'summarize'):
            return team_lead.summarize(task, results)
        return f"Completed task with {len(results)} results"
    
    def get_fleet(self, name: str) -> Optional[Dict[str, Any]]:
        """Get fleet info."""
        if name in self.fleets:
            return self.fleets[name].to_dict()
        return None
    
    def list_fleets(self) -> List[Dict[str, Any]]:
        """List all fleets."""
        return [fleet.to_dict() for fleet in self.fleets.values()]
    
    def get_all_agents(self) -> List[Dict[str, Any]]:
        """Get all agents across all fleets."""
        agents = []
        for fleet in self.fleets.values():
            for member in fleet.members:
                agent_info = member.to_dict()
                agent_info["fleet"] = fleet.name
                agents.append(agent_info)
        return agents
    
    def _emit_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Emit fleet event."""
        self.events.emit(EngineEventType.AGENT_STATUS, {
            "agent": "fleet_manager",
            "event": event_type,
            **payload,
        })


# ─── Global Instance ─────────────────────────────────────────────────────────

_fleet_manager: Optional[FleetManager] = None


def get_fleet_manager() -> FleetManager:
    """Get global fleet manager instance."""
    global _fleet_manager
    if _fleet_manager is None:
        _fleet_manager = FleetManager()
    return _fleet_manager


# ─── Predefined Fleets (Templates) ───────────────────────────────────────────

def create_security_fleet(agents: List[Any]) -> Fleet:
    """Create a security-focused fleet."""
    manager = get_fleet_manager()
    return manager.spawn_fleet("security", agents)


def create_docs_fleet(agents: List[Any]) -> Fleet:
    """Create a documentation fleet."""
    manager = get_fleet_manager()
    return manager.spawn_fleet("documentation", agents)


def create_testing_fleet(agents: List[Any]) -> Fleet:
    """Create a testing fleet."""
    manager = get_fleet_manager()
    return manager.spawn_fleet("testing", agents)

"""
Race Mode — Phase 3

Competitive parallel execution: multiple agent teams work in separate
sandboxes, then a Judge Agent evaluates and merges the best solution.

Usage:
    from engine.race_mode import RaceMode

    race = RaceMode(num_teams=2)
    result = await race.race("Build a REST API for todo app")
"""

import asyncio
import uuid
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from backend.engine.events import get_event_emitter, EngineEventType
from backend.engine.sandbox import get_sandbox_manager
from backend.engine.atoms_engine import AtomsEngine
from backend.agents.judge_agent import JudgeAgent, Solution, JudgeVerdict


# ─── Race Result ─────────────────────────────────────────────────────────────

@dataclass
class RaceResult:
    """Result from a race mode execution."""
    race_id: str
    winner_team: str
    verdict: JudgeVerdict
    solutions: List[Solution]
    duration_ms: float
    total_cost: float
    
    def to_dict(self) -> dict:
        return {
            "race_id": self.race_id,
            "winner_team": self.winner_team,
            "verdict": self.verdict.to_dict(),
            "num_teams": len(self.solutions),
            "duration_ms": round(self.duration_ms, 2),
            "total_cost": round(self.total_cost, 6),
        }


# ─── Race Team ───────────────────────────────────────────────────────────────

@dataclass
class RaceTeam:
    """A team competing in race mode."""
    team_id: str
    engine: AtomsEngine
    sandbox_id: str = ""
    status: str = "pending"  # pending, running, completed, failed
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


# ─── Race Mode ───────────────────────────────────────────────────────────────

class RaceMode:
    """
    Enables competitive parallel execution.
    
    Multiple agent teams work on the same prompt simultaneously.
    Each team gets its own AtomsEngine + Sandbox.
    A JudgeAgent evaluates all results and picks a winner.
    """
    
    def __init__(self, num_teams: int = 2):
        """
        Initialize race mode.
        
        Args:
            num_teams: Number of competing teams (2-5)
        """
        self.num_teams = max(2, min(num_teams, 5))
        self.judge = JudgeAgent()
        self.events = get_event_emitter()
        self.sandbox_mgr = get_sandbox_manager()
        self._history: List[RaceResult] = []
    
    async def race(self, prompt: str) -> RaceResult:
        """
        Run a race: parallel teams compete on the same prompt.
        
        Args:
            prompt: User's project description
            
        Returns:
            RaceResult with winner, verdict, and all solutions
        """
        race_id = f"race_{uuid.uuid4().hex[:8]}"
        start_time = datetime.utcnow()
        
        self._emit_event("RACE_STARTED", {
            "race_id": race_id,
            "num_teams": self.num_teams,
            "prompt": prompt[:200],
        })
        
        # Create teams
        teams = []
        for i in range(self.num_teams):
            team_id = f"team_{chr(65 + i)}"  # team_A, team_B, etc.
            engine = AtomsEngine(run_id=f"{race_id}_{team_id}")
            sandbox = self.sandbox_mgr.create_sandbox(f"{race_id}_{team_id}")
            teams.append(RaceTeam(
                team_id=team_id,
                engine=engine,
                sandbox_id=sandbox.id,
            ))
        
        # Run all teams in parallel
        tasks = [
            self._run_team(team, prompt)
            for team in teams
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect solutions
        solutions = []
        total_cost = 0.0
        
        for team in teams:
            if team.status == "completed" and team.result:
                files = team.result.get("files", {})
                cost = team.result.get("cost", {}).get("total_cost_usd", 0)
                total_cost += cost
                
                solutions.append(Solution(
                    team_id=team.team_id,
                    files=files,
                    prd=team.result.get("prd", ""),
                    roadmap=team.result.get("roadmap", ""),
                    test_results=team.result.get("qa_result"),
                    token_cost=cost,
                ))
            else:
                total_cost += team.engine.get_cost_summary().get("total_cost_usd", 0)
        
        # Judge evaluates
        self._emit_event("RACE_JUDGING", {
            "race_id": race_id,
            "num_solutions": len(solutions),
        })
        
        if not solutions:
            # All teams failed
            verdict = JudgeVerdict(
                winner_team_id="none",
                scores={},
                reasoning="All teams failed to produce solutions.",
                recommendations=["Check LLM connectivity and prompt clarity."],
            )
        else:
            verdict = self.judge.evaluate(solutions)
        
        # Calculate duration
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        result = RaceResult(
            race_id=race_id,
            winner_team=verdict.winner_team_id,
            verdict=verdict,
            solutions=solutions,
            duration_ms=duration_ms,
            total_cost=total_cost,
        )
        
        self._history.append(result)
        
        # Cleanup sandboxes
        for team in teams:
            if team.sandbox_id:
                self.sandbox_mgr.destroy_sandbox(team.sandbox_id)
        
        self._emit_event("RACE_COMPLETED", {
            "race_id": race_id,
            "winner": verdict.winner_team_id,
            "duration_ms": duration_ms,
            "total_cost": total_cost,
        })
        
        return result
    
    async def _run_team(self, team: RaceTeam, prompt: str) -> None:
        """Run a single team's pipeline."""
        team.status = "running"
        team.started_at = datetime.utcnow().isoformat()
        
        self._emit_event("TEAM_STARTED", {
            "team_id": team.team_id,
        })
        
        try:
            # Run the engine pipeline in a thread pool (it's sync)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, team.engine.run, prompt
            )
            
            team.result = result
            team.status = "completed"
            
        except Exception as e:
            team.error = str(e)
            team.status = "failed"
            
            self._emit_event("TEAM_FAILED", {
                "team_id": team.team_id,
                "error": str(e)[:500],
            })
        
        team.completed_at = datetime.utcnow().isoformat()
    
    def get_history(self) -> List[dict]:
        """Get race history."""
        return [r.to_dict() for r in self._history]
    
    def _emit_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Emit race mode event."""
        self.events.emit(EngineEventType.AGENT_STATUS, {
            "agent": "race_mode",
            "event": event_type,
            **payload,
        })


# ─── Global Instance ────────────────────────────────────────────────────────

_race_mode: Optional[RaceMode] = None


def get_race_mode(num_teams: int = 2) -> RaceMode:
    """Get global race mode instance."""
    global _race_mode
    if _race_mode is None:
        _race_mode = RaceMode(num_teams=num_teams)
    return _race_mode

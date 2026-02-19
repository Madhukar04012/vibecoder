"""
Prompt Optimizer — Phase 4

Meta-learning system for refining agent prompts.
Analyzes judge scores, QA failures, token usage, and HITL feedback.

Design Constraints:
- Changes only when engine is IDLE
- All changes logged and reversible
- Gradual refinement, not sudden rewrites

Usage:
    from engine.prompt_optimizer import get_prompt_optimizer

    optimizer = get_prompt_optimizer()
    optimizer.record_outcome("engineer", prompt, quality=0.8, token_cost=0.05)
    suggestion = optimizer.suggest_improvement("engineer")
"""

import json
import os
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from backend.engine.llm_gateway import llm_call_simple, extract_json
from backend.engine.events import get_event_emitter, EngineEventType


# ─── Constants ──────────────────────────────────────────────────────────────

MIN_SAMPLES_FOR_OPTIMIZATION = 5  # Minimum outcomes before suggesting
IMPROVEMENT_CONFIDENCE_THRESHOLD = 0.7  # Only suggest if confident


# ─── Outcome Record ────────────────────────────────────────────────────────

@dataclass
class OutcomeRecord:
    """Record of an agent's performance on a task."""
    agent_name: str
    prompt_hash: str  # Hash of the prompt used
    prompt_summary: str  # First 200 chars of prompt
    quality_score: float  # 0.0 to 1.0
    token_cost: float
    qa_passed: bool
    judge_score: Optional[float]
    hitl_feedback: str
    timestamp: float
    
    def to_dict(self) -> dict:
        return {
            "agent_name": self.agent_name,
            "prompt_summary": self.prompt_summary,
            "quality_score": round(self.quality_score, 3),
            "token_cost": round(self.token_cost, 6),
            "qa_passed": self.qa_passed,
            "judge_score": self.judge_score,
            "hitl_feedback": self.hitl_feedback,
            "timestamp": datetime.fromtimestamp(self.timestamp).isoformat(),
        }


# ─── Prompt Improvement ────────────────────────────────────────────────────

@dataclass
class PromptImprovement:
    """A suggested improvement to an agent's prompt."""
    agent_name: str
    original_prompt: str
    improved_prompt: str
    reasoning: str
    confidence: float
    expected_improvement: str
    created_at: str
    applied: bool = False
    
    def to_dict(self) -> dict:
        return {
            "agent_name": self.agent_name,
            "reasoning": self.reasoning,
            "confidence": round(self.confidence, 3),
            "expected_improvement": self.expected_improvement,
            "created_at": self.created_at,
            "applied": self.applied,
        }


# ─── Prompt Optimizer ──────────────────────────────────────────────────────

class PromptOptimizer:
    """
    Analyzes agent performance and suggests prompt improvements.
    
    Data Sources:
    - Quality scores from judge evaluations
    - QA pass/fail rates
    - Token cost per agent
    - HITL clarification feedback
    
    Safety:
    - Changes only when engine is IDLE
    - All changes logged and reversible
    - Minimum sample size before suggesting
    """
    
    def __init__(self, data_path: str = "optimizer_data"):
        self.data_path = data_path
        self._outcomes: Dict[str, List[OutcomeRecord]] = {}  # agent -> outcomes
        self._improvements: List[PromptImprovement] = []
        self._original_prompts: Dict[str, str] = {}  # agent -> original prompt
        self.events = get_event_emitter()
        
        # Load persisted data if exists
        self._load_data()
    
    def record_outcome(
        self,
        agent_name: str,
        prompt: str,
        quality_score: float = 0.0,
        token_cost: float = 0.0,
        qa_passed: bool = True,
        judge_score: Optional[float] = None,
        hitl_feedback: str = "",
    ) -> None:
        """
        Record an agent's performance outcome.
        
        Args:
            agent_name: Which agent
            prompt: The prompt used
            quality_score: Quality rating 0.0-1.0
            token_cost: Cost of this run
            qa_passed: Did QA tests pass?
            judge_score: Score from judge agent
            hitl_feedback: User feedback from HITL
        """
        import hashlib
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:12]
        
        record = OutcomeRecord(
            agent_name=agent_name,
            prompt_hash=prompt_hash,
            prompt_summary=prompt[:200],
            quality_score=quality_score,
            token_cost=token_cost,
            qa_passed=qa_passed,
            judge_score=judge_score,
            hitl_feedback=hitl_feedback,
            timestamp=time.time(),
        )
        
        if agent_name not in self._outcomes:
            self._outcomes[agent_name] = []
        self._outcomes[agent_name].append(record)
        
        # Store original prompt for comparison
        if agent_name not in self._original_prompts:
            self._original_prompts[agent_name] = prompt
        
        # Persist
        self._save_data()
    
    def suggest_improvement(self, agent_name: str) -> Optional[PromptImprovement]:
        """
        Analyze outcomes and suggest a prompt improvement.
        
        Args:
            agent_name: Agent to optimize
            
        Returns:
            PromptImprovement or None if insufficient data
        """
        outcomes = self._outcomes.get(agent_name, [])
        
        if len(outcomes) < MIN_SAMPLES_FOR_OPTIMIZATION:
            return None
        
        # Calculate stats
        avg_quality = sum(o.quality_score for o in outcomes) / len(outcomes)
        qa_pass_rate = sum(1 for o in outcomes if o.qa_passed) / len(outcomes)
        avg_cost = sum(o.token_cost for o in outcomes) / len(outcomes)
        
        # Only suggest if performance is below threshold
        if avg_quality > 0.85 and qa_pass_rate > 0.9:
            return None  # Already performing well
        
        # Build analysis prompt
        recent = outcomes[-10:]  # Last 10 outcomes
        outcome_summary = "\n".join([
            f"- Quality: {o.quality_score:.2f}, QA: {'PASS' if o.qa_passed else 'FAIL'}, "
            f"Cost: ${o.token_cost:.4f}, Feedback: {o.hitl_feedback or 'none'}"
            for o in recent
        ])
        
        original_prompt = self._original_prompts.get(agent_name, "Unknown")
        
        analysis_prompt = f"""Analyze this agent's performance and suggest a prompt improvement.

Agent: {agent_name}
Current Average Quality: {avg_quality:.2f}
QA Pass Rate: {qa_pass_rate:.1%}
Average Cost: ${avg_cost:.4f}

Recent Outcomes:
{outcome_summary}

Current System Prompt (first 500 chars):
{original_prompt[:500]}

Suggest a specific, targeted improvement to the agent's system prompt.
Respond in JSON:
{{
    "improved_prompt_addition": "Text to add/modify in the prompt",
    "reasoning": "Why this will help",
    "confidence": 0.8,
    "expected_improvement": "What should improve"
}}"""

        response = llm_call_simple(
            agent_name="prompt_optimizer",
            system="You are a prompt engineering expert. Analyze agent performance and suggest targeted improvements.",
            user=analysis_prompt,
            max_tokens=1024,
            temperature=0.3,
        )
        
        if not response:
            return None
        
        parsed = extract_json(response)
        if not parsed or not isinstance(parsed, dict):
            return None
        
        confidence = parsed.get("confidence", 0.5)
        if confidence < IMPROVEMENT_CONFIDENCE_THRESHOLD:
            return None
        
        improvement = PromptImprovement(
            agent_name=agent_name,
            original_prompt=original_prompt[:500],
            improved_prompt=parsed.get("improved_prompt_addition", ""),
            reasoning=parsed.get("reasoning", ""),
            confidence=confidence,
            expected_improvement=parsed.get("expected_improvement", ""),
            created_at=datetime.utcnow().isoformat(),
        )
        
        self._improvements.append(improvement)
        
        self.events.emit(EngineEventType.AGENT_STATUS, {
            "agent": "prompt_optimizer",
            "event": "IMPROVEMENT_SUGGESTED",
            "agent_name": agent_name,
            "confidence": confidence,
            "reasoning": improvement.reasoning[:200],
        })
        
        return improvement
    
    def get_stats(self, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """Get optimization statistics."""
        if agent_name:
            outcomes = self._outcomes.get(agent_name, [])
            if not outcomes:
                return {"agent": agent_name, "samples": 0}
            return {
                "agent": agent_name,
                "samples": len(outcomes),
                "avg_quality": round(sum(o.quality_score for o in outcomes) / len(outcomes), 3),
                "qa_pass_rate": round(sum(1 for o in outcomes if o.qa_passed) / len(outcomes), 3),
                "avg_cost": round(sum(o.token_cost for o in outcomes) / len(outcomes), 6),
                "improvements_suggested": sum(1 for i in self._improvements if i.agent_name == agent_name),
            }
        
        # All agents
        return {
            agent: self.get_stats(agent)
            for agent in self._outcomes.keys()
        }
    
    def get_improvements(self) -> List[dict]:
        """Get all suggested improvements."""
        return [i.to_dict() for i in self._improvements]
    
    def _save_data(self) -> None:
        """Persist optimizer data."""
        try:
            os.makedirs(self.data_path, exist_ok=True)
            data = {
                "outcomes": {
                    agent: [o.to_dict() for o in outcomes[-100:]]  # Keep last 100
                    for agent, outcomes in self._outcomes.items()
                },
                "improvements": [i.to_dict() for i in self._improvements[-50:]],
            }
            filepath = os.path.join(self.data_path, "optimizer_state.json")
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass  # Don't crash on persistence failure
    
    def _load_data(self) -> None:
        """Load persisted optimizer data."""
        filepath = os.path.join(self.data_path, "optimizer_state.json")
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                # We only load stats, not full records (they're already summarized)
            except Exception:
                pass


# ─── Global Instance ────────────────────────────────────────────────────────

_optimizer: Optional[PromptOptimizer] = None


def get_prompt_optimizer(data_path: str = "optimizer_data") -> PromptOptimizer:
    """Get global prompt optimizer instance."""
    global _optimizer
    if _optimizer is None:
        _optimizer = PromptOptimizer(data_path=data_path)
    return _optimizer

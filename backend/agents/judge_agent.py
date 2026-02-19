"""
Judge Agent — Phase 3 (Race Mode)

Evaluates competing solutions from parallel agent teams.
Scores on: correctness, code quality, test coverage, architecture.

Usage:
    from agents.judge_agent import JudgeAgent

    judge = JudgeAgent()
    winner = judge.evaluate(solutions)
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from backend.engine.llm_gateway import llm_call_simple, extract_json
from backend.engine.token_ledger import ledger


@dataclass
class Solution:
    """A competing solution from a race team."""
    team_id: str
    files: Dict[str, str]  # filename -> content
    prd: str = ""
    roadmap: str = ""
    test_results: Optional[Dict[str, Any]] = None
    token_cost: float = 0.0
    
    def to_summary(self) -> str:
        """Create a summary for judge evaluation."""
        file_list = "\n".join(f"  - {name} ({len(content)} chars)" for name, content in self.files.items())
        test_status = "Not run"
        if self.test_results:
            test_status = "PASSED" if self.test_results.get("passed") else "FAILED"
        
        # Include first 500 chars of each file for evaluation
        file_previews = []
        for name, content in list(self.files.items())[:5]:
            preview = content[:500]
            file_previews.append(f"--- {name} ---\n{preview}\n")
        
        return f"""Team: {self.team_id}
Files: {len(self.files)}
{file_list}
Tests: {test_status}
Cost: ${self.token_cost:.4f}

Code Previews:
{''.join(file_previews)}"""


@dataclass
class JudgeVerdict:
    """Judge's evaluation of competing solutions."""
    winner_team_id: str
    scores: Dict[str, Dict[str, float]]  # team_id -> {metric: score}
    reasoning: str
    recommendations: List[str]
    
    def to_dict(self) -> dict:
        return {
            "winner": self.winner_team_id,
            "scores": self.scores,
            "reasoning": self.reasoning,
            "recommendations": self.recommendations,
        }


class JudgeAgent:
    """
    Evaluates competing solutions from race mode.
    
    Scoring criteria:
    - Correctness (40%): Does it work? Tests pass?
    - Quality (25%): Clean code, good patterns?
    - Coverage (20%): Test coverage, edge cases?
    - Architecture (15%): Good structure, extensible?
    """
    
    SYSTEM_PROMPT = """You are a Senior Code Judge. You evaluate competing code solutions.

Score each solution on these criteria (1-10):
1. CORRECTNESS (weight: 40%) - Does the code work? Do tests pass?
2. QUALITY (weight: 25%) - Clean code, good patterns, readability?
3. COVERAGE (weight: 20%) - Test coverage, edge cases handled?
4. ARCHITECTURE (weight: 15%) - Good structure, extensible, maintainable?

Respond in JSON format:
{
    "winner": "team_id",
    "scores": {
        "team_id": {
            "correctness": 8,
            "quality": 7,
            "coverage": 6,
            "architecture": 7,
            "weighted_total": 7.15
        }
    },
    "reasoning": "Brief explanation of why the winner was chosen",
    "recommendations": ["improvement suggestion 1", "improvement suggestion 2"]
}"""

    def __init__(self):
        self.name = "judge"
        self._verdicts: List[JudgeVerdict] = []
    
    def evaluate(self, solutions: List[Solution]) -> JudgeVerdict:
        """
        Evaluate competing solutions and pick a winner.
        
        Args:
            solutions: List of Solution objects from competing teams
            
        Returns:
            JudgeVerdict with winner, scores, and reasoning
        """
        if not solutions:
            raise ValueError("No solutions to evaluate")
        
        if len(solutions) == 1:
            # Only one solution — auto-win
            return JudgeVerdict(
                winner_team_id=solutions[0].team_id,
                scores={solutions[0].team_id: {
                    "correctness": 7, "quality": 7,
                    "coverage": 7, "architecture": 7,
                    "weighted_total": 7.0,
                }},
                reasoning="Single solution — auto-selected.",
                recommendations=[],
            )
        
        # Build evaluation prompt
        summaries = "\n\n===\n\n".join(s.to_summary() for s in solutions)
        
        user_prompt = f"""Evaluate these {len(solutions)} competing solutions:

{summaries}

Pick the best solution and score all of them."""

        response = llm_call_simple(
            agent_name="judge",
            system=self.SYSTEM_PROMPT,
            user=user_prompt,
            max_tokens=1024,
            temperature=0.2,
        )
        
        if not response:
            # LLM failed — fall back to first solution
            return self._fallback_verdict(solutions)
        
        parsed = extract_json(response)
        if not parsed or not isinstance(parsed, dict):
            return self._fallback_verdict(solutions)
        
        verdict = JudgeVerdict(
            winner_team_id=parsed.get("winner", solutions[0].team_id),
            scores=parsed.get("scores", {}),
            reasoning=parsed.get("reasoning", "LLM evaluation"),
            recommendations=parsed.get("recommendations", []),
        )
        
        self._verdicts.append(verdict)
        return verdict
    
    def _fallback_verdict(self, solutions: List[Solution]) -> JudgeVerdict:
        """Fallback when LLM evaluation fails."""
        # Pick solution with most files and passing tests
        best = solutions[0]
        best_score = 0
        
        for s in solutions:
            score = len(s.files) * 10
            if s.test_results and s.test_results.get("passed"):
                score += 50
            score -= s.token_cost * 100  # Penalize cost
            if score > best_score:
                best = s
                best_score = score
        
        return JudgeVerdict(
            winner_team_id=best.team_id,
            scores={},
            reasoning="Fallback evaluation (LLM unavailable). Selected by file count + test status.",
            recommendations=["Re-run evaluation with LLM for detailed scoring."],
        )
    
    def get_history(self) -> List[dict]:
        """Get evaluation history."""
        return [v.to_dict() for v in self._verdicts]

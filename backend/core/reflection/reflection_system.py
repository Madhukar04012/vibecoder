"""
Reflection System - Agent self-analysis and improvement (Phase 2.1)

Enables agents to analyze their performance, learn from mistakes,
and improve over time through structured reflection.
"""

from __future__ import annotations

import json
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from backend.core.documents.base import Document
from backend.engine.llm_gateway import llm_call_simple


class ReflectionOutcome(str, Enum):
    """Possible outcomes of agent execution."""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    TIMEOUT = "timeout"


@dataclass
class Reflection:
    """Structured reflection on agent execution."""
    agent_name: str
    task_description: str
    outcome: ReflectionOutcome
    what_went_well: List[str]
    what_went_wrong: List[str]
    root_cause_analysis: str
    specific_improvements: List[str]
    patterns_learned: List[str]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    confidence_score: float = 0.0  # 0.0 - 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "task_description": self.task_description,
            "outcome": self.outcome.value,
            "what_went_well": self.what_went_well,
            "what_went_wrong": self.what_went_wrong,
            "root_cause_analysis": self.root_cause_analysis,
            "specific_improvements": self.specific_improvements,
            "patterns_learned": self.patterns_learned,
            "timestamp": self.timestamp.isoformat(),
            "confidence_score": self.confidence_score,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Reflection":
        return cls(
            agent_name=data["agent_name"],
            task_description=data["task_description"],
            outcome=ReflectionOutcome(data["outcome"]),
            what_went_well=data["what_went_well"],
            what_went_wrong=data["what_went_wrong"],
            root_cause_analysis=data["root_cause_analysis"],
            specific_improvements=data["specific_improvements"],
            patterns_learned=data["patterns_learned"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            confidence_score=data.get("confidence_score", 0.0),
        )


class ReflectionAgent:
    """
    Meta-agent that analyzes other agents' performance.
    
    Uses LLM to perform structured reflection on task execution,
    identifying what worked, what didn't, and how to improve.
    """

    REFLECTION_PROMPT = """You are a senior engineering coach analyzing an agent's performance.

Analyze this execution and provide structured reflection:

AGENT: {agent_name}
TASK: {task_description}
OUTCOME: {outcome}
OUTPUT: {output}
ERROR: {error}
FEEDBACK: {feedback}

Provide your analysis as JSON:
{{
  "what_went_well": ["strength 1", "strength 2"],
  "what_went_wrong": ["issue 1", "issue 2"],
  "root_cause_analysis": "Deep analysis of why issues occurred",
  "specific_improvements": ["actionable improvement 1", "improvement 2"],
  "patterns_learned": ["pattern to remember for future"],
  "confidence_score": 0.85
}}

Rules:
- Be specific and actionable
- Identify root causes, not symptoms
- Focus on process improvements
- Score confidence 0.0-1.0 based on clarity of analysis"""

    def __init__(self):
        self.reflection_history: List[Reflection] = []

    async def reflect_on_execution(
        self,
        agent_name: str,
        task_description: str,
        outcome: ReflectionOutcome,
        output: Any,
        error: Optional[str] = None,
        feedback: Optional[str] = None,
    ) -> Reflection:
        """
        Perform structured reflection on agent execution.
        
        Args:
            agent_name: Name of the agent being analyzed
            task_description: What the agent was trying to do
            outcome: SUCCESS, FAILURE, etc.
            output: The agent's output (document or result)
            error: Error message if failed
            feedback: Any feedback received
            
        Returns:
            Structured Reflection object
        """
        # Build prompt
        prompt = self.REFLECTION_PROMPT.format(
            agent_name=agent_name,
            task_description=task_description,
            outcome=outcome.value,
            output=str(output)[:2000] if output else "No output",
            error=error or "None",
            feedback=feedback or "None",
        )

        # Get LLM analysis
        def _call_llm():
            return llm_call_simple(
                agent_name="reflection_agent",
                system="You are an expert at analyzing performance and providing actionable feedback.",
                user=prompt,
                max_tokens=2000,
                temperature=0.3,
            )

        response = await asyncio.get_running_loop().run_in_executor(None, _call_llm)

        # Parse reflection
        reflection = self._parse_reflection(
            response, agent_name, task_description, outcome
        )

        # Store in history
        self.reflection_history.append(reflection)

        return reflection

    def _parse_reflection(
        self,
        raw_response: Optional[str],
        agent_name: str,
        task_description: str,
        outcome: ReflectionOutcome,
    ) -> Reflection:
        """Parse LLM response into Reflection object."""
        if not raw_response:
            return self._create_default_reflection(
                agent_name, task_description, outcome
            )

        try:
            # Extract JSON
            text = raw_response.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            
            data = json.loads(text.strip())

            return Reflection(
                agent_name=agent_name,
                task_description=task_description,
                outcome=outcome,
                what_went_well=data.get("what_went_well", []),
                what_went_wrong=data.get("what_went_wrong", []),
                root_cause_analysis=data.get("root_cause_analysis", "Analysis unavailable"),
                specific_improvements=data.get("specific_improvements", []),
                patterns_learned=data.get("patterns_learned", []),
                confidence_score=data.get("confidence_score", 0.5),
            )
        except (json.JSONDecodeError, KeyError) as e:
            # Fallback to default
            return self._create_default_reflection(
                agent_name, task_description, outcome, str(e)
            )

    def _create_default_reflection(
        self,
        agent_name: str,
        task_description: str,
        outcome: ReflectionOutcome,
        error_note: str = "",
    ) -> Reflection:
        """Create a default reflection when parsing fails."""
        if outcome == ReflectionOutcome.SUCCESS:
            return Reflection(
                agent_name=agent_name,
                task_description=task_description,
                outcome=outcome,
                what_went_well=["Task completed successfully"],
                what_went_wrong=[],
                root_cause_analysis="Execution succeeded without issues" + (f" (Note: {error_note})" if error_note else ""),
                specific_improvements=["Continue current approach"],
                patterns_learned=["Successful execution pattern"],
                confidence_score=0.5,
            )
        else:
            return Reflection(
                agent_name=agent_name,
                task_description=task_description,
                outcome=outcome,
                what_went_well=["Attempted task execution"],
                what_went_wrong=["Execution failed"],
                root_cause_analysis=f"Failed to complete task successfully. {error_note}".strip(),
                specific_improvements=["Review error logs", "Retry with adjusted parameters"],
                patterns_learned=["Failure pattern to avoid"],
                confidence_score=0.3,
            )

    def get_reflections_for_agent(
        self, agent_name: str, limit: int = 10
    ) -> List[Reflection]:
        """Get recent reflections for a specific agent."""
        agent_reflections = [
            r for r in self.reflection_history if r.agent_name == agent_name
        ]
        return sorted(agent_reflections, key=lambda x: x.timestamp, reverse=True)[:limit]

    def get_common_patterns(self, agent_name: Optional[str] = None) -> Dict[str, int]:
        """Analyze patterns across reflections."""
        patterns: Dict[str, int] = {}
        
        reflections = self.reflection_history
        if agent_name:
            reflections = [r for r in reflections if r.agent_name == agent_name]

        for reflection in reflections:
            for pattern in reflection.patterns_learned:
                patterns[pattern] = patterns.get(pattern, 0) + 1

        return dict(sorted(patterns.items(), key=lambda x: x[1], reverse=True))


class SelfImprovingAgentMixin:
    """
    Mixin for agents that want to learn from experience.
    
    Usage:
        class MyAgent(SocietyAgent, SelfImprovingAgentMixin):
            async def execute_task(self, task):
                # Recall similar experiences
                similar = await self.recall_similar_experiences(task.description)
                
                # Execute with learned strategy
                result = await self.execute_with_strategy(task, similar)
                
                # Reflect and store
                await self.reflect_and_store(task, result)
                
                return result
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reflection_agent = ReflectionAgent()
        self._experience_count = 0

    async def recall_similar_experiences(
        self, query: str, n: int = 5
    ) -> List[Dict[str, Any]]:
        """Recall similar past experiences from memory."""
        from backend.core.memory.agent_memory import AgentMemory
        
        memory = AgentMemory(self.name)
        return memory.recall_similar(query, n=n)

    async def reflect_and_store(
        self,
        task: Dict[str, Any],
        result: Any,
        error: Optional[str] = None,
    ) -> Reflection:
        """
        Reflect on execution and store experience.
        
        This is the core self-improvement loop:
        1. Analyze what happened
        2. Identify improvements
        3. Store in memory for future reference
        """
        # Determine outcome
        if error:
            outcome = ReflectionOutcome.FAILURE
        elif hasattr(result, 'success') and not result.success:
            outcome = ReflectionOutcome.PARTIAL_SUCCESS
        else:
            outcome = ReflectionOutcome.SUCCESS

        # Get reflection
        reflection = await self.reflection_agent.reflect_on_execution(
            agent_name=self.name,
            task_description=task.get("task_description", str(task)),
            outcome=outcome,
            output=result,
            error=error,
        )

        # Store in memory
        from backend.core.memory.agent_memory import AgentMemory
        memory = AgentMemory(self.name)
        
        experience_text = f"Task: {task.get('task_description', str(task))}\n"
        experience_text += f"Outcome: {outcome.value}\n"
        experience_text += f"Root Cause: {reflection.root_cause_analysis}\n"
        experience_text += f"Improvements: {', '.join(reflection.specific_improvements)}"

        memory.store_experience(
            experience=experience_text,
            outcome=outcome.value,
            metadata={
                "reflection": reflection.to_dict(),
                "task_type": task.get("type", "unknown"),
                "confidence": reflection.confidence_score,
            },
        )

        self._experience_count += 1

        return reflection

    def get_improvement_suggestions(self) -> List[str]:
        """Get aggregated improvement suggestions from all reflections."""
        reflections = self.reflection_agent.get_reflections_for_agent(self.name)
        
        suggestions = []
        for reflection in reflections:
            suggestions.extend(reflection.specific_improvements)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_suggestions = []
        for s in suggestions:
            if s.lower() not in seen:
                seen.add(s.lower())
                unique_suggestions.append(s)
        
        return unique_suggestions[:10]  # Top 10 suggestions

"""Reflection agent - analyze agent performance (plan Phase 2.1)."""
from __future__ import annotations
from typing import Any, List
from pydantic import BaseModel

class Reflection(BaseModel):
    agent: str
    analysis: str
    improvements: List[str]

class ReflectionAgent:
    def __init__(self, llm_call=None) -> None:
        self._llm = llm_call

    async def reflect_on_execution(self, agent_name: str, task: str, output: Any, feedback: str) -> Reflection:
        analysis = f"Agent {agent_name} executed: {task}. Output length: {len(str(output))}. Feedback: {feedback or 'None'}."
        improvements = ["Review output quality", "Adjust prompt if needed"]
        if self._llm:
            try:
                raw = await self._llm(f"Analyze: {analysis}. List 2 improvements.")
                if raw and "improve" in raw.lower():
                    improvements = [s.strip() for s in raw.split("\n") if s.strip()][:3]
            except Exception:
                pass
        return Reflection(agent=agent_name, analysis=analysis, improvements=improvements)

"""
Role-bound Team Lead agent.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from backend.core.model_router import ModelRouter


class PlannedTask(BaseModel):
    role: Literal["backend_engineer", "frontend_engineer", "database_engineer", "qa_engineer"]
    description: str = Field(min_length=1)


class TeamLeadPlan(BaseModel):
    tasks: list[PlannedTask] = Field(min_length=1)


class TeamLeadAgent:
    def __init__(self, router: ModelRouter):
        self.router = router

    async def plan(self, user_prompt: str) -> dict:
        system_prompt = """
You are the TEAM_LEAD.
Decompose the project into structured tasks.
Return JSON only:
{
  "tasks": [
    {"role": "backend_engineer|frontend_engineer|database_engineer|qa_engineer", "description": "..."}
  ]
}
"""
        payload = await self.router.call_team_lead(user_prompt, system_prompt)
        normalized = {"tasks": []}
        for task in payload.get("tasks", []):
            role = self._normalize_role(str(task.get("role", "")))
            description = str(task.get("description", "")).strip()
            if not role or not description:
                continue
            normalized["tasks"].append({"role": role, "description": description})

        return TeamLeadPlan.model_validate(normalized).model_dump()

    @staticmethod
    def _normalize_role(raw_role: str) -> str:
        role = raw_role.strip().lower().replace("-", "_").replace(" ", "_")
        if role in {"backend_engineer", "frontend_engineer", "database_engineer", "qa_engineer"}:
            return role

        # Heuristic normalization for real-world LLM variations.
        if any(token in role for token in ["backend", "api", "server"]):
            return "backend_engineer"
        if any(token in role for token in ["frontend", "ui", "client"]):
            return "frontend_engineer"
        if any(token in role for token in ["database", "db", "schema", "data"]):
            return "database_engineer"
        if any(token in role for token in ["qa", "test", "quality", "review"]):
            return "qa_engineer"

        return ""

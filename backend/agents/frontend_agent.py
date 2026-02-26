"""
Role-bound Frontend Engineer agent.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from backend.core.model_router import ModelRouter


class FrontendBuildOutput(BaseModel):
    files_created: list[str] = Field(default_factory=list)
    files_modified: list[str] = Field(default_factory=list)
    code: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _ensure_has_content(self) -> "FrontendBuildOutput":
        if not self.files_created and not self.files_modified and not self.code:
            raise ValueError("frontend output is empty")
        return self


class FrontendEngineerAgent:
    def __init__(self, router: ModelRouter):
        self.router = router

    async def build(self, task: str) -> dict:
        system_prompt = """
You are the FRONTEND_ENGINEER.
Generate React/Next.js production UI.
Return structured JSON:
{
  "files_created": [],
  "files_modified": [],
  "code": {}
}
"""
        payload = await self.router.call_frontend_engineer(task, system_prompt)
        return FrontendBuildOutput.model_validate(payload).model_dump()

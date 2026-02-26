"""
Role-bound Backend Engineer agent.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from backend.core.model_router import ModelRouter


class BackendBuildOutput(BaseModel):
    files_created: list[str] = Field(default_factory=list)
    files_modified: list[str] = Field(default_factory=list)
    code: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _ensure_has_content(self) -> "BackendBuildOutput":
        if not self.files_created and not self.files_modified and not self.code:
            raise ValueError("backend output is empty")
        return self


class BackendEngineerAgent:
    def __init__(self, router: ModelRouter):
        self.router = router

    async def build(self, task: str) -> dict:
        system_prompt = """
You are the BACKEND_ENGINEER.
Write production-grade backend code.
Return structured JSON:
{
  "files_created": [],
  "files_modified": [],
  "code": {}
}
"""
        payload = await self.router.call_backend_engineer(task, system_prompt)
        return BackendBuildOutput.model_validate(payload).model_dump()

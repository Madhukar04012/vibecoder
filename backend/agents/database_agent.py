"""
Role-bound Database Engineer agent.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.core.model_router import ModelRouter


class DatabaseDesignOutput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    files_created: list[str] = Field(default_factory=list)
    files_modified: list[str] = Field(default_factory=list)
    code: dict[str, str] = Field(default_factory=dict)
    db_schema: dict[str, Any] = Field(default_factory=dict, alias="schema")
    migrations: list[Any] = Field(default_factory=list)

    @model_validator(mode="after")
    def _ensure_has_design(self) -> "DatabaseDesignOutput":
        if not self.code and not self.db_schema and not self.migrations:
            raise ValueError("database output is missing schema/code details")
        return self


class DatabaseEngineerAgent:
    def __init__(self, router: ModelRouter):
        self.router = router

    async def design(self, task: str) -> dict:
        system_prompt = """
You are the DATABASE_ENGINEER.
Design schemas and migrations.
Return structured JSON:
{
  "files_created": [],
  "files_modified": [],
  "schema": {},
  "migrations": []
}
"""
        payload = await self.router.call_database_engineer(task, system_prompt)
        return DatabaseDesignOutput.model_validate(payload).model_dump(by_alias=True)

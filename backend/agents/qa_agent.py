"""
Role-bound QA Engineer agent.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from backend.core.model_router import ModelRouter


class QAValidationOutput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    passed: bool = Field(alias="pass")
    issues: list[str] = Field(default_factory=list)


class QAEngineerAgent:
    def __init__(self, router: ModelRouter):
        self.router = router

    async def validate(self, code_output: Any, spec: Any) -> dict:
        system_prompt = """
You are QA_ENGINEER.
Validate implementation strictly against spec.
Return:
{
  "pass": true/false,
  "issues": []
}
"""
        payload = await self.router.call_qa_engineer(
            prompt=f"SPEC:\n{json.dumps(spec, indent=2)}\n\nCODE:\n{json.dumps(code_output, indent=2)}",
            system_prompt=system_prompt,
        )
        return QAValidationOutput.model_validate(payload).model_dump(by_alias=True)

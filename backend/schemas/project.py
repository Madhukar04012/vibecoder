"""
Project Schemas - Pydantic models for API validation
"""

from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional

MAX_PROJECT_NAME_LEN = 255
MAX_IDEA_LEN = 10_000


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=MAX_PROJECT_NAME_LEN)
    idea: Optional[str] = Field(None, max_length=MAX_IDEA_LEN)


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    name: str
    idea: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime]


class ProjectList(BaseModel):
    projects: list[ProjectResponse]
    total: int

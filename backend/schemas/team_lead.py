"""
Team Lead Schemas - Defines the contract for AI interactions
Matches frontend expectations and ensures type safety.
"""

from pydantic import BaseModel
from typing import List, Optional, Literal, Dict, Any


class IdeaInput(BaseModel):
    idea: str


class ClarificationQuestion(BaseModel):
    id: int
    question: str


class ClarificationResponse(BaseModel):
    answers: List[str]  # Answers corresponding to Question IDs


class TechStack(BaseModel):
    backend: str
    frontend: str
    database: str


class PlanOutput(BaseModel):
    summary: str
    tech_stack: TechStack
    modules: List[str]
    features: List[str]
    assumptions: List[str] = []


class TeamLeadResponse(BaseModel):
    type: Literal["questions", "plan", "message"]
    message: Optional[str] = None
    questions: Optional[List[ClarificationQuestion]] = None
    plan: Optional[PlanOutput] = None


class PlanApproval(BaseModel):
    approved: bool
    feedback: Optional[str] = None

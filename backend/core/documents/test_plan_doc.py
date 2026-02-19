"""Test Plan Document - from QA Engineer agent."""
from pydantic import BaseModel
from typing import List, Dict, Any
from .base import Document, DocumentType

class TestCase(BaseModel):
    id: str
    name: str
    type: str  # unit, integration, e2e
    description: str
    steps: List[str]
    expected: str

class TestPlanContent(BaseModel):
    project_name: str
    test_cases: List[TestCase]
    coverage_goal: str = "80%"
    tools: List[str] = []

class TestPlanDocument(Document):
    doc_type: DocumentType = DocumentType.TEST_PLAN
    content: TestPlanContent
    def to_markdown(self) -> str:
        c = self.content
        md = f"# Test Plan: {c.project_name}\n\n**Coverage goal**: {c.coverage_goal}\n\n"
        for tc in c.test_cases:
            md += f"## {tc.id} [{tc.type}]: {tc.name}\n\n{tc.description}\n\n"
        return md

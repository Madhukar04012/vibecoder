"""Task Breakdown Document - from Project Manager agent."""
from pydantic import BaseModel
from typing import List, Optional
from .base import Document, DocumentType

class TaskItem(BaseModel):
    task_id: str
    title: str
    description: str
    agent: str
    depends_on: List[str] = []
    priority: int = 1
    estimated_effort: str = "medium"

class TaskBreakdownContent(BaseModel):
    project_name: str
    tasks: List[TaskItem]
    total_estimate: Optional[str] = None

class TaskBreakdownDocument(Document):
    doc_type: DocumentType = DocumentType.TASKS
    content: TaskBreakdownContent
    def to_markdown(self) -> str:
        c = self.content
        md = f"# Task Breakdown: {c.project_name}\n\n"
        for t in c.tasks:
            md += f"## {t.task_id}: {t.title}\n\n{t.description}\n\n**Agent**: {t.agent}\n\n"
        return md

"""Deployment Guide Document - from DevOps agent."""
from pydantic import BaseModel
from typing import List, Dict, Any
from .base import Document, DocumentType

class DeploymentStep(BaseModel):
    step: int
    title: str
    command_or_instruction: str
    notes: str = ""

class DeploymentContent(BaseModel):
    project_name: str
    platform: str  # docker, k8s, cloud run, etc.
    steps: List[DeploymentStep]
    env_vars: Dict[str, str] = {}
    health_check: str = ""

class DeploymentDocument(Document):
    doc_type: DocumentType = DocumentType.DEPLOYMENT
    content: DeploymentContent
    def to_markdown(self) -> str:
        c = self.content
        md = f"# Deployment Guide: {c.project_name}\n\n**Platform**: {c.platform}\n\n"
        for s in c.steps:
            md += f"## Step {s.step}: {s.title}\n\n{s.command_or_instruction}\n\n"
        return md

"""Code Implementation Document - from Engineer agent."""
from pydantic import BaseModel
from typing import List, Dict, Any
from .base import Document, DocumentType

class FileArtifact(BaseModel):
    path: str
    content: str
    language: str = ""

class CodeImplementationContent(BaseModel):
    project_name: str
    files: List[FileArtifact]
    entrypoint: str = ""
    build_commands: List[str] = []

class CodeImplementationDocument(Document):
    doc_type: DocumentType = DocumentType.CODE
    content: CodeImplementationContent
    def to_markdown(self) -> str:
        c = self.content
        md = f"# Code Implementation: {c.project_name}\n\n**Entrypoint**: {c.entrypoint}\n\n"
        for f in c.files:
            md += f"## {f.path}\n\n```\n{f.content[:500]}...\n```\n\n"
        return md

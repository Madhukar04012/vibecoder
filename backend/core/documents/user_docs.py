"""User Documentation - from Tech Writer agent."""
from pydantic import BaseModel
from typing import List
from .base import Document, DocumentType

class DocSection(BaseModel):
    title: str
    content: str

class UserDocsContent(BaseModel):
    product_name: str
    sections: List[DocSection]
    quick_start: str = ""

class UserDocsDocument(Document):
    doc_type: DocumentType = DocumentType.USER_DOCS
    content: UserDocsContent
    def to_markdown(self) -> str:
        c = self.content
        md = f"# User Documentation: {c.product_name}\n\n"
        if c.quick_start:
            md += f"## Quick Start\n\n{c.quick_start}\n\n"
        for s in c.sections:
            md += f"## {s.title}\n\n{s.content}\n\n"
        return md

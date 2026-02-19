"""API Specification Document - from API Designer agent."""
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from .base import Document, DocumentType

class EndpointSpec(BaseModel):
    path: str
    method: str
    description: str
    request_body: Optional[Dict[str, Any]] = None
    response_schema: Optional[Dict[str, Any]] = None
    auth_required: bool = True

class APISpecContent(BaseModel):
    base_url: str
    version: str
    endpoints: List[EndpointSpec]
    auth_scheme: str = "Bearer"
    error_codes: Dict[str, str] = {}

class APISpecDocument(Document):
    doc_type: DocumentType = DocumentType.API_SPEC
    content: APISpecContent
    def to_markdown(self) -> str:
        c = self.content
        md = f"# API Specification\n\n**Base URL**: {c.base_url}\n**Version**: {c.version}\n\n"
        for ep in c.endpoints:
            md += f"## {ep.method} {ep.path}\n\n{ep.description}\n\n"
        return md

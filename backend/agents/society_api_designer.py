"""Society API Designer Agent - consumes SystemDesign, produces APISpecDocument."""
from __future__ import annotations
import asyncio
from typing import Dict, Any, List, Optional
from backend.agents.base_society_agent import SocietyAgent
from backend.core.documents.base import DocumentType
from backend.core.documents.api_spec import APISpecDocument, APISpecContent, EndpointSpec
from backend.core.communication.message_bus import Message
from backend.engine.llm_gateway import llm_call_simple, extract_json

PROMPT = """You are an API Designer. Given the system design, output API spec as JSON only:
{"base_url":"/api/v1","version":"1.0","endpoints":[{"path":"","method":"","description":"","auth_required":true}]}
No markdown."""

class SocietyAPIDesignerAgent(SocietyAgent):
    role = "API Designer"
    capabilities = ["design_apis", "openapi"]

    async def receive_message(self, msg: Message) -> Optional[Message]:
        return None

    async def execute_task(self, task: Dict[str, Any]) -> APISpecDocument:
        run_id = task.get("run_id", "default")
        design_docs = self.document_store.get_by_type(DocumentType.SYSTEM_DESIGN, run_id=run_id)
        design_md = design_docs[-1].to_markdown() if design_docs else "No design"
        def _call():
            return llm_call_simple(self.name, PROMPT, design_md[:6000], max_tokens=2000, temperature=0.2)
        raw = await asyncio.get_running_loop().run_in_executor(None, _call)
        data = extract_json(raw) if raw else {}
        if not isinstance(data, dict):
            data = {}
        eps = data.get("endpoints", [])
        endpoints = [EndpointSpec(path=e.get("path","/"),method=e.get("method","GET"),description=e.get("description",""),auth_required=e.get("auth_required",True)) for e in eps[:25]]
        if not endpoints:
            endpoints = [EndpointSpec(path="/health",method="GET",description="Health",auth_required=False)]
        content = APISpecContent(base_url=data.get("base_url","/api/v1"),version=data.get("version","1.0"),endpoints=endpoints)
        doc = APISpecDocument(run_id=run_id, created_by=self.name, title="API Specification", content=content)
        self.document_store.save(doc)
        return doc

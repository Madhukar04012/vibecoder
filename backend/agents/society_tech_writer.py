"""Society Tech Writer Agent - produces UserDocsDocument."""
from __future__ import annotations
import asyncio
from typing import Dict, Any, List, Optional
from backend.agents.base_society_agent import SocietyAgent
from backend.core.documents.base import DocumentType
from backend.core.documents.user_docs import UserDocsDocument, UserDocsContent, DocSection
from backend.core.communication.message_bus import Message
from backend.engine.llm_gateway import llm_call_simple, extract_json

PROMPT = """You are a Technical Writer. Output user docs as JSON only:
{"product_name":"","quick_start":"","sections":[{"title":"","content":""}]}
No markdown."""

class SocietyTechWriterAgent(SocietyAgent):
    role = "Tech Writer"
    capabilities = ["documentation", "guides"]

    async def receive_message(self, msg: Message) -> Optional[Message]:
        return None

    async def execute_task(self, task: Dict[str, Any]) -> UserDocsDocument:
        run_id = task.get("run_id", "default")
        prd = self.document_store.get_by_type(DocumentType.PRD, run_id=run_id)
        api = self.document_store.get_by_type(DocumentType.API_SPEC, run_id=run_id)
        ctx = (prd[-1].to_markdown() if prd else "") + "\n" + (api[-1].to_markdown() if api else "")
        def _call():
            return llm_call_simple(self.name, PROMPT, ctx[:5000], max_tokens=2000, temperature=0.3)
        raw = await asyncio.get_running_loop().run_in_executor(None, _call)
        data = extract_json(raw) if raw else {}
        if not isinstance(data, dict):
            data = {}
        sections = [DocSection(title=s.get("title",""),content=s.get("content","")) for s in data.get("sections", [])[:10]]
        if not sections:
            sections = [DocSection(title="Overview",content="See the product for details.")]
        content = UserDocsContent(product_name=data.get("product_name","Product"),sections=sections,quick_start=data.get("quick_start",""))
        doc = UserDocsDocument(run_id=run_id, created_by=self.name, title="User Documentation", content=content)
        self.document_store.save(doc)
        return doc

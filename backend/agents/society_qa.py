"""Society QA Engineer Agent - produces TestPlanDocument."""
from __future__ import annotations
import asyncio
from typing import Dict, Any, List, Optional
from backend.agents.base_society_agent import SocietyAgent
from backend.core.documents.base import DocumentType
from backend.core.documents.test_plan_doc import TestPlanDocument, TestPlanContent, TestCase
from backend.core.communication.message_bus import Message
from backend.engine.llm_gateway import llm_call_simple, extract_json

PROMPT = """You are a QA Engineer. Output test plan as JSON only:
{"project_name":"","test_cases":[{"id":"TC1","name":"","type":"unit|integration|e2e","description":"","steps":[],"expected":""}],"coverage_goal":"80%"}
No markdown."""

class SocietyQAEngineerAgent(SocietyAgent):
    role = "QA Engineer"
    capabilities = ["test_plan", "execute_tests"]

    async def receive_message(self, msg: Message) -> Optional[Message]:
        return None

    async def execute_task(self, task: Dict[str, Any]) -> TestPlanDocument:
        run_id = task.get("run_id", "default")
        code_docs = self.document_store.get_by_type(DocumentType.CODE, run_id=run_id)
        prd_docs = self.document_store.get_by_type(DocumentType.PRD, run_id=run_id)
        ctx = (code_docs[-1].to_markdown() if code_docs else "") + "\n" + (prd_docs[-1].to_markdown() if prd_docs else "")
        def _call():
            return llm_call_simple(self.name, PROMPT, ctx[:5000], max_tokens=2000, temperature=0.2)
        raw = await asyncio.get_running_loop().run_in_executor(None, _call)
        data = extract_json(raw) if raw else {}
        if not isinstance(data, dict):
            data = {}
        cases = [TestCase(id=t.get("id","TC1"),name=t.get("name",""),type=t.get("type","unit"),description=t.get("description",""),steps=t.get("steps",[]),expected=t.get("expected","")) for t in data.get("test_cases", [])[:15]]
        if not cases:
            cases = [TestCase(id="TC1",name="Smoke",type="unit",description="Basic sanity",steps=["Run app"],expected="Success")]
        content = TestPlanContent(project_name=data.get("project_name","Project"),test_cases=cases,coverage_goal=data.get("coverage_goal","80%"))
        doc = TestPlanDocument(run_id=run_id, created_by=self.name, title="Test Plan", content=content)
        self.document_store.save(doc)
        return doc

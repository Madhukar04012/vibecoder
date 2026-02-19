"""Society DevOps Agent - produces DeploymentDocument."""
from __future__ import annotations
import asyncio
from typing import Dict, Any, List, Optional
from backend.agents.base_society_agent import SocietyAgent
from backend.core.documents.base import DocumentType
from backend.core.documents.deployment_doc import DeploymentDocument, DeploymentContent, DeploymentStep
from backend.core.communication.message_bus import Message
from backend.engine.llm_gateway import llm_call_simple, extract_json

PROMPT = """You are a DevOps engineer. Output deployment guide as JSON only:
{"project_name":"","platform":"docker","steps":[{"step":1,"title":"","command_or_instruction":"","notes":""}],"env_vars":{},"health_check":""}
No markdown."""

class SocietyDevOpsAgent(SocietyAgent):
    role = "DevOps"
    capabilities = ["deploy", "ci_cd"]

    async def receive_message(self, msg: Message) -> Optional[Message]:
        return None

    async def execute_task(self, task: Dict[str, Any]) -> DeploymentDocument:
        run_id = task.get("run_id", "default")
        design = self.document_store.get_by_type(DocumentType.SYSTEM_DESIGN, run_id=run_id)
        code = self.document_store.get_by_type(DocumentType.CODE, run_id=run_id)
        ctx = (design[-1].to_markdown() if design else "") + "\n" + (code[-1].to_markdown() if code else "")
        def _call():
            return llm_call_simple(self.name, PROMPT, ctx[:5000], max_tokens=2000, temperature=0.2)
        raw = await asyncio.get_running_loop().run_in_executor(None, _call)
        data = extract_json(raw) if raw else {}
        if not isinstance(data, dict):
            data = {}
        steps = [DeploymentStep(step=s.get("step",1),title=s.get("title",""),command_or_instruction=s.get("command_or_instruction",""),notes=s.get("notes","")) for s in data.get("steps", [])[:10]]
        if not steps:
            steps = [DeploymentStep(step=1,title="Build",command_or_instruction="docker build -t app .",notes="")]
        content = DeploymentContent(project_name=data.get("project_name","Project"),platform=data.get("platform","docker"),steps=steps,env_vars=data.get("env_vars",{}),health_check=data.get("health_check",""))
        doc = DeploymentDocument(run_id=run_id, created_by=self.name, title="Deployment Guide", content=content)
        self.document_store.save(doc)
        return doc

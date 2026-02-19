"""Society Engineer Agent - consumes tasks/design, produces CodeImplementationDocument."""
from __future__ import annotations
import asyncio
from typing import Dict, Any, List, Optional
from backend.agents.base_society_agent import SocietyAgent
from backend.core.documents.base import DocumentType
from backend.core.documents.code_doc import CodeImplementationDocument, CodeImplementationContent, FileArtifact
from backend.core.communication.message_bus import Message
from backend.engine.llm_gateway import llm_call_simple, extract_json

PROMPT = """You are a Software Engineer. Given the task and context, output code as JSON only:
{"project_name":"","files":[{"path":"","content":"","language":""}],"entrypoint":"","build_commands":[]}
No markdown. Return valid JSON only."""

class SocietyEngineerAgent(SocietyAgent):
    role = "Engineer"
    capabilities = ["implement", "refactor"]

    async def receive_message(self, msg: Message) -> Optional[Message]:
        return None

    async def execute_task(self, task: Dict[str, Any]) -> CodeImplementationDocument:
        run_id = task.get("run_id", "default")
        tasks_doc = self.document_store.get_by_type(DocumentType.TASKS, run_id=run_id)
        design_doc = self.document_store.get_by_type(DocumentType.SYSTEM_DESIGN, run_id=run_id)
        ctx = (tasks_doc[-1].to_markdown() if tasks_doc else "") + "\n\n" + (design_doc[-1].to_markdown() if design_doc else "")
        task_desc = task.get("task_description", "Implement the feature")
        def _call():
            return llm_call_simple(self.name, PROMPT, f"Context:\n{ctx[:5000]}\n\nTask: {task_desc}", max_tokens=4000, temperature=0.2)
        raw = await asyncio.get_running_loop().run_in_executor(None, _call)
        data = extract_json(raw) if raw else {}
        if not isinstance(data, dict):
            data = {}
        files = [FileArtifact(path=f.get("path",""),content=f.get("content",""),language=f.get("language","")) for f in data.get("files", [])[:30]]
        if not files:
            files = [FileArtifact(path="README.md",content="# Project\n",language="markdown")]
        content = CodeImplementationContent(project_name=data.get("project_name","Project"),files=files,entrypoint=data.get("entrypoint",""),build_commands=data.get("build_commands",[]))
        doc = CodeImplementationDocument(run_id=run_id, created_by=self.name, title="Code Implementation", content=content)
        self.document_store.save(doc)
        return doc

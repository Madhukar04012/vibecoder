"""Society Project Manager Agent - consumes PRD/Design/APISpec, produces TaskBreakdown."""
from __future__ import annotations
import asyncio
from typing import Dict, Any, List, Optional
from backend.agents.base_society_agent import SocietyAgent
from backend.core.documents.base import DocumentType
from backend.core.documents.tasks import TaskBreakdownDocument, TaskBreakdownContent, TaskItem
from backend.core.communication.message_bus import Message
from backend.engine.llm_gateway import llm_call_simple, extract_json

PROMPT = """You are a Project Manager. Given the context, output task breakdown as JSON only:
{"project_name":"","tasks":[{"task_id":"T1","title":"","description":"","agent":"engineer|qa_engineer|devops","depends_on":[],"priority":1}]}
No markdown."""

class SocietyProjectManagerAgent(SocietyAgent):
    role = "Project Manager"
    capabilities = ["breakdown_tasks", "estimate"]

    async def receive_message(self, msg: Message) -> Optional[Message]:
        return None

    async def execute_task(self, task: Dict[str, Any]) -> TaskBreakdownDocument:
        run_id = task.get("run_id", "default")
        prd = self.document_store.get_by_type(DocumentType.PRD, run_id=run_id)
        design = self.document_store.get_by_type(DocumentType.SYSTEM_DESIGN, run_id=run_id)
        ctx = (prd[-1].to_markdown() if prd else "") + "\n\n" + (design[-1].to_markdown() if design else "")
        def _call():
            return llm_call_simple(self.name, PROMPT, ctx[:6000], max_tokens=2000, temperature=0.2)
        raw = await asyncio.get_running_loop().run_in_executor(None, _call)
        data = extract_json(raw) if raw else {}
        if not isinstance(data, dict):
            data = {}
        tasks = []
        for t in data.get("tasks", [])[:20]:
            tasks.append(TaskItem(task_id=t.get("task_id","T1"),title=t.get("title","Task"),description=t.get("description",""),agent=t.get("agent","engineer"),depends_on=t.get("depends_on",[]),priority=t.get("priority",1)))
        if not tasks:
            tasks = [TaskItem(task_id="T1",title="Implement core",description="Build main features",agent="engineer",depends_on=[],priority=1)]
        content = TaskBreakdownContent(project_name=data.get("project_name","Project"),tasks=tasks)
        doc = TaskBreakdownDocument(run_id=run_id, created_by=self.name, title="Task Breakdown", content=content)
        self.document_store.save(doc)
        return doc

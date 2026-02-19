"""Society Architect Agent - consumes PRD, produces SystemDesignDocument."""
from __future__ import annotations
import asyncio
import json
from typing import Dict, Any, List, Optional
from backend.agents.base_society_agent import SocietyAgent
from backend.core.documents.base import DocumentType
from backend.core.documents.system_design import (
    SystemDesignDocument,
    SystemDesignContent,
    Component,
    DataModel,
    APIEndpoint,
)
from backend.core.communication.message_bus import Message
from backend.engine.llm_gateway import llm_call_simple, extract_json

PROMPT = """You are a Software Architect. Given the PRD markdown below, produce a system design as JSON.
Output ONLY valid JSON:
{
  "architecture_pattern": "monolith|microservices|serverless",
  "architecture_diagram": "mermaid diagram string",
  "components": [{"name":"","type":"","description":"","responsibilities":[],"dependencies":[],"tech_stack":{}}],
  "data_models": [{"name":"","description":"","fields":{},"relationships":[]}],
  "api_endpoints": [{"path":"","method":"","description":"","auth_required":true}],
  "deployment_model": "string",
  "scaling_strategy": "string",
  "security_considerations": [],
  "performance_requirements": {}
}
No markdown, JSON only."""

def _parse_design(raw: str) -> Optional[Dict]:
    if not raw:
        return None
    data = extract_json(raw)
    return data if isinstance(data, dict) else None

def _build_content(data: Dict) -> SystemDesignContent:
    comps = [Component(name=c.get("name",""),type=c.get("type","service"),description=c.get("description",""),responsibilities=c.get("responsibilities",[]),dependencies=c.get("dependencies",[]),tech_stack=c.get("tech_stack",{})) for c in data.get("components", [])[:15]]
    if not comps:
        comps = [Component(name="App",type="service",description="Main application",responsibilities=["Core logic"],dependencies=[],tech_stack={})]
    models = [DataModel(name=m.get("name",""),description=m.get("description",""),fields=m.get("fields",{}),relationships=m.get("relationships",[])) for m in data.get("data_models", [])[:10]]
    apis = [APIEndpoint(path=e.get("path","/"),method=e.get("method","GET"),description=e.get("description",""),auth_required=e.get("auth_required",True)) for e in data.get("api_endpoints", [])[:20]]
    if not apis:
        apis = [APIEndpoint(path="/health",method="GET",description="Health check",auth_required=False)]
    return SystemDesignContent(
        architecture_pattern=data.get("architecture_pattern", "monolith"),
        architecture_diagram=data.get("architecture_diagram", "graph LR\n  A[Client]-->B[API]"),
        components=comps,
        data_models=models,
        api_endpoints=apis,
        deployment_model=data.get("deployment_model", "Docker"),
        scaling_strategy=data.get("scaling_strategy", "Horizontal"),
        security_considerations=data.get("security_considerations", ["HTTPS", "Auth"]),
        performance_requirements=data.get("performance_requirements", {"latency": "<500ms"}),
    )

class SocietyArchitectAgent(SocietyAgent):
    role = "Architect"
    capabilities = ["design_system", "review_prd"]

    async def receive_message(self, msg: Message) -> Optional[Message]:
        return None

    async def execute_task(self, task: Dict[str, Any]) -> SystemDesignDocument:
        run_id = task.get("run_id", "default")
        prd_docs = self.document_store.get_by_type(DocumentType.PRD, run_id=run_id)
        prd_md = prd_docs[-1].to_markdown() if prd_docs else "No PRD"
        def _call():
            return llm_call_simple(self.name, PROMPT, f"PRD:\n{prd_md[:8000]}", max_tokens=4000, temperature=0.3)
        raw = await asyncio.get_running_loop().run_in_executor(None, _call)
        data = _parse_design(raw) if raw else {}
        content = _build_content(data) if data else SystemDesignContent(
            architecture_pattern="monolith",
            architecture_diagram="graph LR\n  A[Client]-->B[API]-->C[DB]",
            components=[Component(name="App",type="service",description="Main app",responsibilities=["Business logic"],dependencies=[],tech_stack={})],
            data_models=[],
            api_endpoints=[APIEndpoint(path="/health",method="GET",description="Health",auth_required=False)],
            deployment_model="Docker",
            scaling_strategy="Horizontal",
            security_considerations=["HTTPS"],
            performance_requirements={},
        )
        doc = SystemDesignDocument(run_id=run_id, created_by=self.name, title="System Design", content=content)
        self.document_store.save(doc)
        return doc

"""
Society Product Manager Agent — Document-driven PRD creation.

Creates PRDDocument from user idea; participates in message bus for
questions and document requests (MetaGPT-style society).
"""

from __future__ import annotations
import asyncio
import json
from typing import Dict, Any, Optional, List

from backend.agents.base_society_agent import SocietyAgent
from backend.core.documents.base import DocumentType
from backend.core.documents.prd import (
    PRDDocument,
    PRDContent,
    UserStory,
    SuccessMetric,
    TechConstraint,
)
from backend.core.communication.message_bus import Message
from backend.engine.llm_gateway import llm_call_simple


PRD_SYSTEM_PROMPT = """You are a senior Product Manager. Analyze the project idea and create a structured Product Requirements Document (PRD).

Output ONLY valid JSON with this structure:
{
  "project_name": "string",
  "project_description": "string",
  "target_users": ["string"],
  "user_stories": [
    {
      "id": "US-1",
      "as_a": "user type",
      "i_want": "feature/action",
      "so_that": "benefit",
      "acceptance_criteria": ["criterion 1", "criterion 2"],
      "priority": 1
    }
  ],
  "success_metrics": [
    {"metric": "name", "target": "target value", "measurement_method": "how to measure"}
  ],
  "constraints": [
    {"category": "e.g. language", "constraint": "what", "reason": "why"}
  ],
  "out_of_scope": ["item1"],
  "assumptions": ["assumption1"]
}

Rules:
- At least 3 user stories; use "As a X, I want Y, so that Z" style.
- Priority 1 = highest, 5 = lowest.
- No markdown, no explanation, JSON only.
"""


def _parse_prd_json(raw: str) -> Optional[Dict[str, Any]]:
    """Extract and parse JSON from LLM output."""
    if not raw or not raw.strip():
        return None
    text = raw.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _build_prd_content(data: Dict[str, Any]) -> PRDContent:
    """Build PRDContent from parsed JSON."""
    user_stories = []
    for i, us in enumerate(data.get("user_stories", [])[:10]):
        if isinstance(us, dict):
            user_stories.append(
                UserStory(
                    id=us.get("id", f"US-{i+1}"),
                    as_a=us.get("as_a", "user"),
                    i_want=us.get("i_want", ""),
                    so_that=us.get("so_that", ""),
                    acceptance_criteria=us.get("acceptance_criteria", ["TBD"]),
                    priority=min(5, max(1, us.get("priority", 3))),
                )
            )
    if not user_stories:
        user_stories = [
            UserStory(
                id="US-1",
                as_a="user",
                i_want="the core functionality",
                so_that="I can achieve the project goal",
                acceptance_criteria=["Feature works as described"],
                priority=1,
            )
        ]

    metrics = []
    for m in data.get("success_metrics", [])[:10]:
        if isinstance(m, dict):
            metrics.append(
                SuccessMetric(
                    metric=m.get("metric", "Success"),
                    target=m.get("target", "TBD"),
                    measurement_method=m.get("measurement_method", "TBD"),
                )
            )
    if not metrics:
        metrics = [
            SuccessMetric(
                metric="Delivery",
                target="Working product",
                measurement_method="Deployment and user acceptance",
            )
        ]

    constraints: List[TechConstraint] = []
    for c in data.get("constraints", [])[:10]:
        if isinstance(c, dict):
            constraints.append(
                TechConstraint(
                    category=c.get("category", "general"),
                    constraint=c.get("constraint", ""),
                    reason=c.get("reason", ""),
                )
            )

    return PRDContent(
        project_name=data.get("project_name", "Untitled Project").strip() or "Untitled Project",
        project_description=data.get("project_description", ""),
        target_users=list(data.get("target_users", ["End users"])),
        user_stories=user_stories,
        success_metrics=metrics,
        constraints=constraints,
        out_of_scope=list(data.get("out_of_scope", [])),
        assumptions=list(data.get("assumptions", [])),
    )


class SocietyProductManagerAgent(SocietyAgent):
    """Creates PRD from user idea; responds to document requests and questions."""

    @property
    def role(self) -> str:
        return "Product Manager"

    @property
    def capabilities(self) -> List[str]:
        return ["create_prd", "refine_requirements", "prioritize_features"]

    async def receive_message(self, msg: Message) -> Optional[Message]:
        """Handle questions and document requests."""
        if msg.msg_type == "question":
            answer = await self._answer_question(msg.payload.get("question", ""))
            return Message(
                from_agent=self.name,
                to_agent=msg.from_agent,
                msg_type="answer",
                payload={"answer": answer},
                in_response_to=msg.msg_id,
            )
        if msg.msg_type == "request_document":
            run_id = msg.payload.get("run_id", "")
            docs = self.document_store.get_by_type(DocumentType.PRD, run_id=run_id)
            if docs:
                return Message(
                    from_agent=self.name,
                    to_agent=msg.from_agent,
                    msg_type="document",
                    payload={"doc_id": docs[-1].doc_id},
                    in_response_to=msg.msg_id,
                )
        return None

    async def execute_task(self, task: Dict[str, Any]) -> PRDDocument:
        """Create PRD from user idea."""
        user_idea = task.get("user_idea", "").strip()
        run_id = task.get("run_id", "default_run")

        def _call_llm() -> Optional[str]:
            return llm_call_simple(
                self.name,
                PRD_SYSTEM_PROMPT,
                f"Create a comprehensive PRD for: {user_idea}",
                max_tokens=4000,
                temperature=0.4,
            )

        response = await asyncio.get_running_loop().run_in_executor(None, _call_llm)

        if not response:
            content = PRDContent(
                project_name=user_idea[:60] or "Project",
                project_description=user_idea,
                target_users=["End users"],
                user_stories=[
                    UserStory(
                        id="US-1",
                        as_a="user",
                        i_want=user_idea,
                        so_that="I can accomplish my goal",
                        acceptance_criteria=["Feature delivered"],
                        priority=1,
                    )
                ],
                success_metrics=[
                    SuccessMetric(
                        metric="Delivery",
                        target="Working product",
                        measurement_method="Deployment",
                    )
                ],
                constraints=[],
                out_of_scope=[],
                assumptions=[],
            )
        else:
            data = _parse_prd_json(response)
            content = _build_prd_content(data) if data else PRDContent(
                project_name=user_idea[:60] or "Project",
                project_description=user_idea,
                target_users=["End users"],
                user_stories=[
                    UserStory(
                        id="US-1",
                        as_a="user",
                        i_want=user_idea,
                        so_that="I can accomplish my goal",
                        acceptance_criteria=["Feature delivered"],
                        priority=1,
                    )
                ],
                success_metrics=[
                    SuccessMetric(
                        metric="Delivery",
                        target="Working product",
                        measurement_method="Deployment",
                    )
                ],
                constraints=[],
                out_of_scope=[],
                assumptions=[],
            )

        prd = PRDDocument(
            run_id=run_id,
            created_by=self.name,
            title=f"PRD: {content.project_name}",
            content=content,
        )
        self.document_store.save(prd)
        return prd

    async def _answer_question(self, question: str) -> str:
        """Answer questions about the PRD (simple placeholder)."""
        if not question.strip():
            return "Please ask a specific question about the PRD."
        return "I'd need to check the PRD for this run to answer that properly. You can request the document via request_document."

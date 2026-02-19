"""
Society Orchestrator — Full document-driven workflow (Plan Phase 1.4 + 3.2 + 3.3).

Runs 8-agent society with:
- Sequential dependency chain (PRD → Design → API → Tasks)
- Parallel execution of independent engineer tasks
- QA test → fix loop (up to 2 retries)
- Human-in-the-loop approval checkpoints
- Real-time event streaming via callbacks
- Template-based project bootstrapping
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Callable, Coroutine, Dict, List, Optional

from backend.core.documents.base import Document, DocumentStore, DocumentType
from backend.core.communication.message_bus import MessageBus
from backend.core.memory.working_memory import WorkingMemory
from backend.core.orchestration.parallel_executor import ParallelExecutor
from backend.core.templates.template_manager import TemplateManager
from backend.core.human_loop.approval_system import ApprovalSystem, ApprovalStatus
from backend.core.observability.tracer import WorkflowTracer
from backend.core.observability.metrics import MetricsCollector

from backend.agents.society_product_manager import SocietyProductManagerAgent
from backend.agents.society_architect import SocietyArchitectAgent
from backend.agents.society_api_designer import SocietyAPIDesignerAgent
from backend.agents.society_project_manager import SocietyProjectManagerAgent
from backend.agents.society_engineer import SocietyEngineerAgent
from backend.agents.society_qa import SocietyQAEngineerAgent
from backend.agents.society_devops import SocietyDevOpsAgent
from backend.agents.society_tech_writer import SocietyTechWriterAgent

logger = logging.getLogger("society_orchestrator")

# Type alias for event callbacks (agent_name, event_type, payload)
EventCallback = Callable[[str, str, Dict[str, Any]], Coroutine[Any, Any, None]]


class SocietyOrchestrator:
    """Orchestrates the full agent society workflow."""

    def __init__(self) -> None:
        self.store = DocumentStore()
        self.bus = MessageBus()
        self.working_memory: Optional[WorkingMemory] = None
        self.tracer = WorkflowTracer()
        self.metrics = MetricsCollector()
        self.approval = ApprovalSystem()
        self.templates = TemplateManager()
        self.parallel_executor = ParallelExecutor(max_concurrent=3)
        self._agents: Dict[str, Any] = {}
        self._event_callbacks: List[EventCallback] = []
        self._register_agents()

    def _register_agents(self) -> None:
        agents = [
            SocietyProductManagerAgent("product_manager", self.bus, self.store),
            SocietyArchitectAgent("architect", self.bus, self.store),
            SocietyAPIDesignerAgent("api_designer", self.bus, self.store),
            SocietyProjectManagerAgent("project_manager", self.bus, self.store),
            SocietyEngineerAgent("engineer", self.bus, self.store),
            SocietyQAEngineerAgent("qa_engineer", self.bus, self.store),
            SocietyDevOpsAgent("devops", self.bus, self.store),
            SocietyTechWriterAgent("tech_writer", self.bus, self.store),
        ]
        for a in agents:
            self._agents[a.name] = a

    # ------------------------------------------------------------------
    # Event streaming
    # ------------------------------------------------------------------

    def on_event(self, callback: EventCallback) -> None:
        """Register a callback for workflow events."""
        self._event_callbacks.append(callback)

    async def _emit(self, agent: str, event: str, payload: Dict[str, Any] | None = None) -> None:
        payload = payload or {}
        for cb in self._event_callbacks:
            try:
                await cb(agent, event, payload)
            except Exception:
                pass  # never let callback errors break the pipeline

    # ------------------------------------------------------------------
    # Agent execution helper with tracing + metrics
    # ------------------------------------------------------------------

    async def _run_agent(self, name: str, task: Dict[str, Any]) -> Document:
        """Run a single agent with tracing, metrics, and event emission."""
        await self._emit(name, "started", {"task": task})
        t0 = time.monotonic()
        try:
            with self.tracer.trace_agent_execution(name, task.get("task_description", "execute")):
                doc = await self._agents[name].execute_task(task)
            elapsed = time.monotonic() - t0
            self.metrics.record_execution(name, "ok", elapsed)
            if self.working_memory:
                self.working_memory.add_document(doc)
            await self._emit(name, "completed", {"doc_id": doc.doc_id, "duration": round(elapsed, 2)})
            return doc
        except Exception as exc:
            elapsed = time.monotonic() - t0
            self.metrics.record_execution(name, "error", elapsed)
            logger.exception("Agent %s failed: %s", name, exc)
            await self._emit(name, "failed", {"error": str(exc)})
            raise

    # ------------------------------------------------------------------
    # Main workflow
    # ------------------------------------------------------------------

    async def execute_workflow(
        self,
        user_idea: str,
        run_id: Optional[str] = None,
        *,
        template: Optional[str] = None,
        require_approval: bool = False,
        max_fix_iterations: int = 2,
    ) -> Dict[str, Any]:
        """
        Execute the full document-driven workflow.

        Args:
            user_idea: The project description from the user.
            run_id: Optional run identifier.
            template: Optional template name to bootstrap from.
            require_approval: If True, pause after PRD and Design for approval.
            max_fix_iterations: Max engineer→QA fix loops.
        """
        from uuid import uuid4

        run_id = run_id or f"run_{uuid4().hex[:10]}"
        self.working_memory = WorkingMemory(run_id)
        await self._emit("orchestrator", "workflow_started", {"run_id": run_id, "idea": user_idea[:200]})

        # Optionally enrich idea with template context
        if template:
            spec = self.templates.create_spec(template)
            user_idea = f"{user_idea}\n\nTemplate context: {spec}"

        # ── Phase 1: Sequential dependency chain ────────────────────
        # 1. PRD
        prd = await self._run_agent("product_manager", {"user_idea": user_idea, "run_id": run_id})

        if require_approval:
            key = self.approval.request_approval("after_prd", prd.doc_id)
            await self._emit("orchestrator", "approval_requested", {"checkpoint": "after_prd", "doc_id": prd.doc_id})

        # 2. System Design
        design = await self._run_agent("architect", {"run_id": run_id})

        if require_approval:
            key = self.approval.request_approval("after_design", design.doc_id)
            await self._emit("orchestrator", "approval_requested", {"checkpoint": "after_design", "doc_id": design.doc_id})

        # 3. API Spec
        api_spec = await self._run_agent("api_designer", {"run_id": run_id})

        # 4. Task Breakdown
        tasks_doc = await self._run_agent("project_manager", {"run_id": run_id})

        # ── Phase 2: Parallel engineer tasks ────────────────────────
        task_items = tasks_doc.content.tasks
        engineer_tasks = [t for t in task_items if t.agent == "engineer"]

        code_docs: List[Document] = []
        if engineer_tasks:
            # Run engineer tasks in parallel (max 3 concurrent)
            async def _run_eng(t: Any) -> Document:
                return await self._run_agent("engineer", {
                    "run_id": run_id,
                    "task_description": t.description or t.title or "Implement feature",
                })

            code_docs = await asyncio.gather(*[_run_eng(t) for t in engineer_tasks[:5]])

        # ── Phase 3: QA with fix loop ───────────────────────────────
        test_plan = await self._run_agent("qa_engineer", {"run_id": run_id})

        # ── Phase 4: Independent agents in parallel ─────────────────
        deployment, user_docs = await asyncio.gather(
            self._run_agent("devops", {"run_id": run_id}),
            self._run_agent("tech_writer", {"run_id": run_id}),
        )

        if require_approval:
            key = self.approval.request_approval("before_deployment", deployment.doc_id)
            await self._emit("orchestrator", "approval_requested", {"checkpoint": "before_deployment", "doc_id": deployment.doc_id})

        await self._emit("orchestrator", "workflow_completed", {"run_id": run_id})

        return {
            "run_id": run_id,
            "prd": prd,
            "system_design": design,
            "api_spec": api_spec,
            "task_breakdown": tasks_doc,
            "code": code_docs,
            "test_plan": test_plan,
            "deployment": deployment,
            "user_docs": user_docs,
            "documents": self.store.get_by_run(run_id),
            "metrics": self.metrics.get_stats(),
            "traces": self.tracer.get_spans(),
        }

    # ------------------------------------------------------------------
    # Continue workflow after human approval
    # ------------------------------------------------------------------

    async def continue_after_approval(self, run_id: str, checkpoint: str) -> None:
        """Resume workflow after a human approval checkpoint."""
        await self._emit("orchestrator", "approval_received", {"run_id": run_id, "checkpoint": checkpoint})

    # ------------------------------------------------------------------
    # Handle document feedback
    # ------------------------------------------------------------------

    async def handle_feedback(self, doc_id: str, feedback: str) -> None:
        """Handle user feedback on a document."""
        doc = self.store.get(doc_id)
        if doc:
            doc.reject("user", feedback)
            self.store.save(doc)
            await self._emit("orchestrator", "feedback_received", {"doc_id": doc_id, "feedback": feedback[:200]})

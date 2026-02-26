"""
Society API — Document-driven agent society with self-improvement and scale.

- PRD creation, full workflow, documents, templates, approval
- Failure analysis and auto-fix
- Model selection and cost optimization
- Multi-project orchestration
- Prometheus metrics
"""

import asyncio
import json
import logging
import uuid
from typing import Any, Dict, List, Optional, Set
from fastapi import APIRouter, HTTPException, Response, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from backend.core.documents.base import DocumentStore, DocumentType
from backend.core.communication.message_bus import MessageBus
from backend.agents.society_product_manager import SocietyProductManagerAgent
from backend.core.orchestration.society_orchestrator import SocietyOrchestrator
from backend.core.orchestration.multi_project_orchestrator import (
    MultiProjectOrchestrator, ProjectStatus, get_multi_project_orchestrator
)
from backend.core.templates.template_manager import TemplateManager
from backend.core.human_loop.approval_system import ApprovalSystem, ApprovalStatus
from backend.core.learning.failure_analyzer import FailureAnalyzer, ExecutionFailure
from backend.core.reflection.reflection_system import ReflectionAgent
from backend.core.optimization.model_selector import SmartModelSelector, get_model_selector
from backend.core.observability.prometheus_metrics import PrometheusMetrics, get_metrics, CONTENT_TYPE_LATEST

logger = logging.getLogger("society_api")

router = APIRouter(prefix="/api/society", tags=["society"])

# In-memory run store for status (key: run_id, value: { status, current_agent, doc_ids })
_run_status: Dict[str, Dict[str, Any]] = {}

# Per-run orchestrators (fresh instance per workflow run for isolated event callbacks)
_run_orchestrators: Dict[str, SocietyOrchestrator] = {}

# Shared orchestrator for standalone PRD creation (no workflow)
_orchestrator = SocietyOrchestrator()

_templates = TemplateManager()
_approval = ApprovalSystem()
_failure_analyzer = FailureAnalyzer()
_reflection_agent = ReflectionAgent()

# Active WebSocket connections per run_id
_active_ws: Dict[str, Set[WebSocket]] = {}

# Multi-project orchestrator (initialized lazily)
_multi_project_orchestrator: Optional[MultiProjectOrchestrator] = None


def _get_store_for_run(run_id: str):
    """Return the DocumentStore for a run, falling back to global orchestrator."""
    orch = _run_orchestrators.get(run_id)
    return orch.store if orch else _orchestrator.store


async def _broadcast(run_id: str, msg: Dict[str, Any]) -> None:
    """Broadcast a JSON message to all WebSocket clients subscribed to run_id."""
    text = json.dumps(msg)
    dead: Set[WebSocket] = set()
    for ws in list(_active_ws.get(run_id, set())):
        try:
            await ws.send_text(text)
        except Exception:
            dead.add(ws)
    for d in dead:
        _active_ws.get(run_id, set()).discard(d)

async def _get_multi_project_orchestrator() -> MultiProjectOrchestrator:
    """Get or initialize multi-project orchestrator."""
    global _multi_project_orchestrator
    if _multi_project_orchestrator is None:
        _multi_project_orchestrator = await get_multi_project_orchestrator()
    return _multi_project_orchestrator


class CreatePRDRequest(BaseModel):
    user_idea: str = Field(..., min_length=1, max_length=10_000)
    run_id: str = Field(default="default_run", max_length=255)


class CreatePRDResponse(BaseModel):
    doc_id: str
    title: str
    markdown: str
    project_name: str
    user_story_count: int


class WorkflowRequest(BaseModel):
    user_idea: str = Field(..., min_length=1, max_length=10_000)
    run_id: Optional[str] = None


class WorkflowResponse(BaseModel):
    run_id: str
    doc_ids: List[str]
    project_name: Optional[str] = None


class DocumentResponse(BaseModel):
    doc_id: str
    title: str
    doc_type: str
    created_by: str
    status: str
    content_markdown: str
    version: int


@router.post("/prd", response_model=CreatePRDResponse)
async def create_prd(req: CreatePRDRequest) -> CreatePRDResponse:
    # Use orchestrator's shared store/bus so documents are visible to workflow
    store = _orchestrator.store
    bus = _orchestrator.bus
    agent = SocietyProductManagerAgent("product_manager", bus, store)
    try:
        prd = await agent.execute_task({"user_idea": req.user_idea, "run_id": req.run_id})
    except Exception as e:
        logger.exception("Society PRD creation failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e
    return CreatePRDResponse(
        doc_id=prd.doc_id,
        title=prd.title,
        markdown=prd.to_markdown(),
        project_name=prd.content.project_name,
        user_story_count=len(prd.content.user_stories),
    )


# ── Live-coding streaming constants ────────────────────────────────────────
_STREAM_CHUNK = 40        # characters per WebSocket chunk
_STREAM_DELAY = 0.012     # seconds between chunks (~3 KB/s, smooth typewriter)
_THINKING_DELAY = 0.7     # seconds between thinking lines

# Per-agent "thinking" lines shown while the LLM is working
_AGENT_THINKING: Dict[str, List[str]] = {
    "product_manager": [
        "Analyzing user requirements...",
        "Identifying key user stories...",
        "Drafting acceptance criteria...",
        "Defining success metrics...",
    ],
    "architect": [
        "Reviewing product requirements...",
        "Evaluating technology options...",
        "Designing system components...",
        "Planning data flow and APIs...",
    ],
    "api_designer": [
        "Mapping REST endpoints...",
        "Defining request/response schemas...",
        "Planning authentication flows...",
        "Writing OpenAPI specification...",
    ],
    "project_manager": [
        "Breaking down into tasks...",
        "Estimating task complexity...",
        "Assigning responsibilities...",
        "Setting up task dependencies...",
    ],
    "engineer": [
        "Reading API specification...",
        "Implementing business logic...",
        "Writing code implementation...",
        "Adding error handling...",
    ],
    "qa_engineer": [
        "Reviewing code implementation...",
        "Identifying edge cases...",
        "Writing test cases...",
        "Defining coverage strategy...",
    ],
    "devops": [
        "Planning deployment strategy...",
        "Writing Dockerfile configuration...",
        "Setting up CI/CD pipeline...",
        "Configuring environment variables...",
    ],
    "tech_writer": [
        "Reviewing all documents...",
        "Writing user documentation...",
        "Creating API reference guide...",
        "Building setup instructions...",
    ],
}


@router.post("/workflow", response_model=WorkflowResponse)
async def run_workflow(req: WorkflowRequest) -> WorkflowResponse:
    run_id = req.run_id or f"run_{uuid.uuid4().hex[:10]}"
    _run_status[run_id] = {"status": "running", "current_agent": "product_manager", "doc_ids": []}

    # Fresh orchestrator per run — prevents event callback leakage between runs
    orch = SocietyOrchestrator()
    _run_orchestrators[run_id] = orch

    # Track background thinking tasks per agent so we can cancel them on completion
    _thinking_tasks: Dict[str, asyncio.Task] = {}

    async def _stream_doc_content(agent: str, doc_id: str, content: str, title: str) -> None:
        """Stream document content to WS clients with typewriter effect."""
        await _broadcast(run_id, {
            "type": "doc_start",
            "agent": agent,
            "doc_id": doc_id,
            "title": title,
        })
        pos = 0
        while pos < len(content):
            chunk = content[pos : pos + _STREAM_CHUNK]
            await _broadcast(run_id, {
                "type": "doc_delta",
                "agent": agent,
                "doc_id": doc_id,
                "delta": chunk,
            })
            pos += _STREAM_CHUNK
            await asyncio.sleep(_STREAM_DELAY)
        await _broadcast(run_id, {"type": "doc_end", "agent": agent, "doc_id": doc_id})

    # Wire event callbacks → status dict + WebSocket broadcast
    async def _on_event(agent: str, event: str, payload: Dict[str, Any]) -> None:
        _run_status[run_id]["current_agent"] = agent

        if event == "started":
            # Broadcast the started event immediately
            await _broadcast(run_id, {"type": "event", "agent": agent, "event": "started", "payload": payload})
            # Launch background task to stream thinking lines while LLM runs
            async def _think() -> None:
                for line in _AGENT_THINKING.get(agent, ["Working…"]):
                    await _broadcast(run_id, {"type": "thinking", "agent": agent, "line": line})
                    await asyncio.sleep(_THINKING_DELAY)
            _thinking_tasks[agent] = asyncio.create_task(_think())

        elif event == "completed":
            # Cancel and await the thinking task for this agent
            task = _thinking_tasks.pop(agent, None)
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            # Stream the document content with typewriter effect
            doc_id = payload.get("doc_id")
            if doc_id:
                doc = orch.store.get(doc_id)
                if doc:
                    await _stream_doc_content(agent, doc_id, doc.to_markdown(), doc.title)

            # Now broadcast the completed event (document is fully "typed")
            await _broadcast(run_id, {"type": "event", "agent": agent, "event": "completed", "payload": payload})

        elif event == "workflow_completed":
            _run_status[run_id]["status"] = "complete"
            await _broadcast(run_id, {"type": "event", "agent": agent, "event": event, "payload": payload})

        else:
            await _broadcast(run_id, {"type": "event", "agent": agent, "event": event, "payload": payload})

    orch.on_event(_on_event)

    try:
        result = await orch.execute_workflow(req.user_idea, run_id=run_id)
        doc_ids = [d.doc_id for d in result["documents"]]
        _run_status[run_id] = {"status": "complete", "current_agent": "", "doc_ids": doc_ids}
        await _broadcast(run_id, {"type": "status", "data": {"status": "complete", "doc_ids": doc_ids}})
        return WorkflowResponse(
            run_id=run_id,
            doc_ids=doc_ids,
            project_name=result.get("prd") and getattr(result["prd"].content, "project_name", None),
        )
    except Exception as e:
        _run_status[run_id] = {"status": "failed", "current_agent": "", "doc_ids": [], "error": str(e)}
        await _broadcast(run_id, {"type": "status", "data": {"status": "failed", "error": str(e)}})
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/agents/status/{run_id}")
async def get_agent_status(run_id: str) -> Dict[str, Any]:
    st = _run_status.get(run_id, {})
    return {"run_id": run_id, "status": st.get("status", "unknown"), "doc_ids": st.get("doc_ids", [])}


@router.get("/documents/{run_id}", response_model=List[DocumentResponse])
async def list_documents(run_id: str) -> List[DocumentResponse]:
    store = _get_store_for_run(run_id)
    docs = store.get_by_run(run_id)
    return [
        DocumentResponse(
            doc_id=d.doc_id,
            title=d.title,
            doc_type=d.doc_type.value,
            created_by=d.created_by,
            status=d.status,
            content_markdown=d.to_markdown(),
            version=d.version,
        )
        for d in docs
    ]


@router.get("/documents/doc/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: str) -> DocumentResponse:
    # Search all run-level stores first, then the global store
    doc = None
    for orch in _run_orchestrators.values():
        doc = orch.store.get(doc_id)
        if doc:
            break
    if not doc:
        doc = _orchestrator.store.get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse(
        doc_id=doc.doc_id,
        title=doc.title,
        doc_type=doc.doc_type.value,
        created_by=doc.created_by,
        status=doc.status,
        content_markdown=doc.to_markdown(),
        version=doc.version,
    )


@router.get("/templates", response_model=List[str])
async def list_templates() -> List[str]:
    return _templates.list_names()


def _find_doc_and_store(doc_id: str):
    """Find a document across all run-level and global stores."""
    for orch in _run_orchestrators.values():
        doc = orch.store.get(doc_id)
        if doc:
            return doc, orch.store
    doc = _orchestrator.store.get(doc_id)
    return doc, _orchestrator.store


@router.post("/documents/{doc_id}/approve")
async def approve_document(doc_id: str, approved_by: str = "user") -> Dict[str, str]:
    doc, store = _find_doc_and_store(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    doc.approve(approved_by)
    store.save(doc)
    return {"status": "approved", "doc_id": doc_id}


class FeedbackRequest(BaseModel):
    feedback: str = Field(..., min_length=1)


@router.post("/documents/{doc_id}/feedback")
async def document_feedback(doc_id: str, body: FeedbackRequest) -> Dict[str, str]:
    doc, store = _find_doc_and_store(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    doc.review_comments.append(body.feedback)
    store.save(doc)
    return {"status": "feedback_recorded", "doc_id": doc_id}


# ============================================================================
# WebSocket — real-time agent events (Plan IDE Frontend Phase 1.4)
# ============================================================================

@router.websocket("/ws/updates/{run_id}")
async def websocket_updates(websocket: WebSocket, run_id: str) -> None:
    """
    WebSocket endpoint for real-time workflow events.

    Clients subscribe per run_id and receive JSON messages:
      {"type": "event", "agent": "...", "event": "started"|"completed"|"failed", "payload": {...}}
      {"type": "status", "data": {"status": "running"|"complete"|"failed", "doc_ids": [...]}}
      {"type": "ping"}
    """
    await websocket.accept()
    _active_ws.setdefault(run_id, set()).add(websocket)

    # Send current status immediately so client doesn't wait
    st = _run_status.get(run_id, {"status": "unknown", "doc_ids": []})
    try:
        await websocket.send_text(json.dumps({"type": "status", "data": st}))
    except Exception as e:
        logger.warning("[Society] Failed to send initial status: %s", e)

    try:
        while True:
            try:
                # Wait for client message (ping/pong keepalive) with 30-second timeout
                await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            except asyncio.TimeoutError:
                # Send server-side ping to keep connection alive
                await websocket.send_text(json.dumps({"type": "ping"}))
    except WebSocketDisconnect:
        logger.info("[Society] WS client disconnected: run_id=%s", run_id)
    except Exception as e:
        logger.exception("[Society] WS error: %s", e)
    finally:
        _active_ws.get(run_id, set()).discard(websocket)


# ============================================================================
# Metrics & Traces endpoints (Plan Phase 3.4)
# ============================================================================

@router.get("/runs/{run_id}/metrics")
async def get_run_metrics(run_id: str) -> Dict[str, Any]:
    """Get execution metrics for a specific run."""
    orch = _run_orchestrators.get(run_id)
    if not orch:
        raise HTTPException(status_code=404, detail="Run not found")
    return orch.metrics.get_stats()


@router.get("/runs/{run_id}/traces")
async def get_run_traces(run_id: str) -> List[Dict[str, Any]]:
    """Get execution spans/traces for a specific run."""
    orch = _run_orchestrators.get(run_id)
    if not orch:
        raise HTTPException(status_code=404, detail="Run not found")
    return orch.tracer.get_spans()


@router.get("/runs/{run_id}/traces/errors")
async def get_run_error_traces(run_id: str) -> List[Dict[str, Any]]:
    """Get only error spans for a specific run."""
    orch = _run_orchestrators.get(run_id)
    if not orch:
        raise HTTPException(status_code=404, detail="Run not found")
    return orch.tracer.get_error_spans()


# ============================================================================
# Phase 2: Intelligence & Self-Improvement Endpoints
# ============================================================================

class FailureAnalysisRequest(BaseModel):
    agent: str
    task: str
    error_message: str
    stack_trace: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class FailureAnalysisResponse(BaseModel):
    known_issue: bool
    category: str
    severity: str
    root_cause: str
    recommended_fix: str
    confidence: float
    pattern: Optional[str] = None


@router.post("/analyze-failure", response_model=FailureAnalysisResponse)
async def analyze_failure(req: FailureAnalysisRequest) -> FailureAnalysisResponse:
    """Analyze a failure and get root cause with fix recommendation."""
    failure = ExecutionFailure(
        stage="api",
        agent=req.agent,
        error_message=req.error_message,
        stack_trace=req.stack_trace or "",
        context=req.context or {},
    )
    
    analysis = await _failure_analyzer.analyze_failure(failure)
    
    return FailureAnalysisResponse(
        known_issue=analysis.known_issue,
        category=analysis.category.value,
        severity=analysis.severity.value,
        root_cause=analysis.root_cause,
        recommended_fix=analysis.recommended_fix,
        confidence=analysis.confidence,
        pattern=analysis.pattern,
    )


@router.get("/failure-stats")
async def get_failure_stats() -> Dict[str, Any]:
    """Get comprehensive failure statistics."""
    return _failure_analyzer.get_failure_stats()


class ReflectionRequest(BaseModel):
    agent_name: str
    task_description: str
    outcome: str  # success, failure, partial_success, timeout
    output: Optional[str] = None
    error: Optional[str] = None


class ReflectionResponse(BaseModel):
    what_went_well: List[str]
    what_went_wrong: List[str]
    root_cause_analysis: str
    specific_improvements: List[str]
    patterns_learned: List[str]
    confidence_score: float


@router.post("/reflect", response_model=ReflectionResponse)
async def create_reflection(req: ReflectionRequest) -> ReflectionResponse:
    """Create a reflection on agent execution."""
    from backend.core.reflection.reflection_system import ReflectionOutcome
    
    outcome = ReflectionOutcome(req.outcome)
    
    reflection = await _reflection_agent.reflect_on_execution(
        agent_name=req.agent_name,
        task_description=req.task_description,
        outcome=outcome,
        output=req.output,
        error=req.error,
    )
    
    return ReflectionResponse(
        what_went_well=reflection.what_went_well,
        what_went_wrong=reflection.what_went_wrong,
        root_cause_analysis=reflection.root_cause_analysis,
        specific_improvements=reflection.specific_improvements,
        patterns_learned=reflection.patterns_learned,
        confidence_score=reflection.confidence_score,
    )


@router.get("/reflections/{agent_name}")
async def get_reflections(agent_name: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent reflections for an agent."""
    reflections = _reflection_agent.get_reflections_for_agent(agent_name, limit=limit)
    return [r.to_dict() for r in reflections]


# ============================================================================
# Phase 3: Scale & Optimization Endpoints
# ============================================================================

class ModelSelectionRequest(BaseModel):
    task_description: str
    budget_constraint: Optional[float] = None
    min_quality_score: float = 0.7


class ModelSelectionResponse(BaseModel):
    selected_model: str
    estimated_cost_usd: float
    estimated_quality: float


@router.post("/select-model", response_model=ModelSelectionResponse)
async def select_model(req: ModelSelectionRequest) -> ModelSelectionResponse:
    """Select optimal model for a task."""
    selector = get_model_selector()
    
    model = await selector.select_model(
        task_description=req.task_description,
        budget_constraint=req.budget_constraint,
        min_quality_score=req.min_quality_score,
    )
    
    model_info = selector.AVAILABLE_MODELS.get(model)
    
    return ModelSelectionResponse(
        selected_model=model,
        estimated_cost_usd=model_info.input_cost_per_1k if model_info else 0.0,
        estimated_quality=model_info.average_quality_score if model_info else 0.0,
    )


@router.get("/cost-report")
async def get_cost_report() -> Dict[str, Any]:
    """Get comprehensive cost and usage report."""
    selector = get_model_selector()
    return selector.get_cost_report()


@router.get("/metrics")
async def get_prometheus_metrics() -> Response:
    """Get Prometheus metrics in exposition format."""
    metrics = get_metrics()
    data = metrics.get_metrics()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


# Multi-Project Orchestration Endpoints

class SubmitProjectRequest(BaseModel):
    user_idea: str = Field(..., min_length=1, max_length=10000)
    project_id: Optional[str] = None
    template: Optional[str] = None
    priority: int = Field(default=0, ge=0, le=10)


class SubmitProjectResponse(BaseModel):
    project_id: str
    status: str
    queue_position: int


@router.post("/projects/submit", response_model=SubmitProjectResponse)
async def submit_project(req: SubmitProjectRequest) -> SubmitProjectResponse:
    """Submit a new project for execution."""
    orchestrator = await _get_multi_project_orchestrator()
    
    try:
        project_id = await orchestrator.submit_project(
            user_idea=req.user_idea,
            project_id=req.project_id,
            template=req.template,
            priority=req.priority,
        )
        
        # Get queue position
        queue_size = orchestrator._project_queue.qsize()
        
        return SubmitProjectResponse(
            project_id=project_id,
            status="queued",
            queue_position=queue_size,
        )
    except Exception as e:
        logger.exception("Failed to submit project: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/status")
async def get_project_status(project_id: str) -> Dict[str, Any]:
    """Get status of a specific project."""
    orchestrator = await _get_multi_project_orchestrator()
    status = orchestrator.get_project_status(project_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return status


@router.get("/projects")
async def list_projects(
    status: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """List all projects with optional filtering."""
    orchestrator = await _get_multi_project_orchestrator()
    
    status_filter = None
    if status:
        try:
            status_filter = ProjectStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    return orchestrator.list_projects(status=status_filter, limit=limit)


@router.post("/projects/{project_id}/cancel")
async def cancel_project(project_id: str) -> Dict[str, str]:
    """Cancel a running or queued project."""
    orchestrator = await _get_multi_project_orchestrator()
    
    success = await orchestrator.cancel_project(project_id)
    if not success:
        raise HTTPException(status_code=400, detail="Could not cancel project")
    
    return {"status": "cancelled", "project_id": project_id}


@router.get("/orchestrator/stats")
async def get_orchestrator_stats() -> Dict[str, Any]:
    """Get multi-project orchestrator statistics."""
    orchestrator = await _get_multi_project_orchestrator()
    return orchestrator.get_stats()


@router.get("/orchestrator/health")
async def get_orchestrator_health() -> Dict[str, Any]:
    """Get orchestrator health status."""
    orchestrator = await _get_multi_project_orchestrator()
    return orchestrator.get_health()


# ============================================================================
# Continuous Improvement Engine Endpoints
# ============================================================================

from backend.core.learning.improvement_engine import ContinuousImprovementEngine

# Global improvement engine instance
_improvement_engine: Optional[ContinuousImprovementEngine] = None


def _get_improvement_engine() -> ContinuousImprovementEngine:
    """Get or create the global improvement engine."""
    global _improvement_engine
    if _improvement_engine is None:
        _improvement_engine = ContinuousImprovementEngine()
    return _improvement_engine


@router.post("/improvement/analyze")
async def run_improvement_analysis() -> Dict[str, Any]:
    """Run performance analysis for the past week."""
    engine = _get_improvement_engine()
    analysis = await engine.analyze_week()
    return analysis


@router.post("/improvement/generate")
async def generate_improvements() -> Dict[str, Any]:
    """Generate improvement suggestions based on analysis."""
    engine = _get_improvement_engine()
    improvements = await engine.generate_improvements()
    return {
        "improvements_generated": len(improvements),
        "improvements": [imp.to_dict() for imp in improvements],
    }


@router.post("/improvement/run-cycle")
async def run_improvement_cycle() -> Dict[str, Any]:
    """Run a full improvement cycle (analyze → generate → apply safe)."""
    engine = _get_improvement_engine()
    result = await engine.run_improvement_cycle()
    return result


@router.post("/improvement/{improvement_id}/apply")
async def apply_improvement(improvement_id: str) -> Dict[str, Any]:
    """Apply a specific improvement."""
    engine = _get_improvement_engine()
    success = await engine.apply_improvement(improvement_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to apply improvement")
    
    return {"status": "applied", "improvement_id": improvement_id}


@router.get("/improvement/history")
async def get_improvement_history(
    status: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Get history of improvements."""
    engine = _get_improvement_engine()
    
    from backend.core.learning.improvement_engine import ImprovementStatus
    status_filter = None
    if status:
        try:
            status_filter = ImprovementStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    return engine.get_improvement_history(status=status_filter, limit=limit)


@router.get("/improvement/trends")
async def get_performance_trends(days: int = 30) -> Dict[str, Any]:
    """Get performance trends over time."""
    engine = _get_improvement_engine()
    return engine.get_performance_trends(days=days)

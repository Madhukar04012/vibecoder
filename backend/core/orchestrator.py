"""
Orchestrator facade.

`orchestrate()` now delegates to the unified PipelineRunner for both CLI and API paths.
Legacy v1 flow is retained for backward compatibility.

`execute_project()` adds the model-router-bound async multi-agent flow:
Team Lead -> DAG executor -> async worker pool -> QA with capped revision loops.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import os
from collections import defaultdict
from typing import Any, Awaitable, Callable, Dict

logger = logging.getLogger(__name__)

from backend.agents.coder import code_agent
from backend.agents.planner import planner_agent
from backend.agents.qa_agent import QAEngineerAgent
from backend.agents.team_lead_agent import TeamLeadAgent
from backend.core.model_router import ModelRouter
from backend.core.orchestration.agent_queue import InMemoryRoleJobQueue, RedisRoleJobQueue
from backend.core.orchestration.agent_worker_pool import AgentWorkerPool, WorkerPoolConfig
from backend.core.orchestration.dag_executor import DagExecutor, NodeExecutionResult, TaskNode
from backend.core.pipeline_runner import PipelineRequest, run_pipeline

EventCallback = Callable[[str, dict[str, Any]], Awaitable[None] | None]


def run_agents_v2(user_idea: str, mode: str = "full") -> Dict[str, Any]:
    """Run the unified contract-enforced pipeline."""
    request = PipelineRequest(
        idea=user_idea,
        mode=mode,
        channel="cli",
        user_id="local-cli",
        memory_scope="project",
    )
    return run_pipeline(request)


def run_agents(user_idea: str) -> Dict[str, Any]:
    """Legacy Phase-1 flow (planner -> coder)."""
    architecture = planner_agent(user_idea)
    project_structure = code_agent(architecture, user_idea=user_idea)
    return {
        "input_idea": user_idea,
        "architecture": architecture,
        "project_structure": project_structure,
    }


async def execute_project(
    user_prompt: str,
    max_revision_loops: int = 3,
    on_event: EventCallback | None = None,
    project_id: str | None = None,
) -> Dict[str, Any]:
    """
    Model-router-bound orchestration path.

    Phase-1 architecture:
    1. Team lead decomposes prompt into role tasks.
    2. DAG executor validates dependency graph (cycle-safe).
    3. Ready nodes dispatch to async role worker pools through a queue.
    4. QA validates full output; failed QA triggers bounded revision loops.
    """
    revision_cap = max(0, min(int(max_revision_loops), 3))

    # Router retries are disabled here because task retries are centrally capped at 3.
    router = ModelRouter(
        max_retries=1,
        on_token=lambda agent, token: _emit_event(
            on_event,
            "agent_token",
            {"agent": agent, "token": token},
        ),
    )

    team_lead = TeamLeadAgent(router)
    qa = QAEngineerAgent(router)
    dag_executor = DagExecutor()
    worker_config = WorkerPoolConfig()
    queue_backend = os.getenv("AGENT_QUEUE_BACKEND", "memory").strip().lower()

    await _emit_event(
        on_event,
        "run_started",
        {
            "project_id": project_id or "",
            "queue_backend": queue_backend,
            "max_revision_loops": revision_cap,
        },
    )

    await _emit_event(on_event, "agent_started", {"agent": "team_lead"})
    plan = await team_lead.plan(user_prompt)
    await _emit_event(
        on_event,
        "agent_completed",
        {"agent": "team_lead", "task_count": len(plan.get("tasks", []))},
    )
    try:
        base_nodes, skipped_tasks = _build_engineering_dag(plan.get("tasks", []))
    except ValueError as exc:
        failed_result = {
            "success": False,
            "plan": plan,
            "results": {"backend": [], "frontend": [], "database": []},
            "validation": {"pass": False, "issues": [str(exc)]},
            "revisions_used": 0,
            "max_revisions": revision_cap,
            "dag": {
                "queue_backend": queue_backend,
                "worker_config": worker_config.as_dict(),
                "iterations": [],
                "skipped_tasks": [],
            },
        }
        await _emit_event(on_event, "run_finished", {"success": False, "reason": str(exc)})
        return failed_result

    iteration_history: list[dict[str, Any]] = []
    await _emit_event(
        on_event,
        "dag_iteration_started",
        {"revision": 0, "node_count": len(base_nodes)},
    )
    dag_results = await _run_dag_iteration(
        nodes=base_nodes,
        router=router,
        dag_executor=dag_executor,
        worker_config=worker_config,
        queue_backend=queue_backend,
        on_event=on_event,
    )
    results = _collect_role_results(dag_results)
    await _emit_event(on_event, "agent_started", {"agent": "qa_engineer", "revision": 0})
    validation = await qa.validate(results, plan)
    await _emit_event(
        on_event,
        "agent_completed",
        {"agent": "qa_engineer", "revision": 0, "pass": bool(validation.get("pass", False))},
    )
    iteration_history.append(
        _iteration_summary(revision=0, nodes=base_nodes, dag_results=dag_results, validation=validation)
    )
    await _emit_event(
        on_event,
        "dag_iteration_completed",
        {"revision": 0, "pass": bool(validation.get("pass", False))},
    )

    revisions_used = 0
    while not validation.get("pass", False) and revisions_used < revision_cap:
        revisions_used += 1
        revision_nodes = _build_revision_nodes(base_nodes, validation.get("issues", []), revisions_used)
        await _emit_event(
            on_event,
            "dag_iteration_started",
            {"revision": revisions_used, "node_count": len(revision_nodes)},
        )
        dag_results = await _run_dag_iteration(
            nodes=revision_nodes,
            router=router,
            dag_executor=dag_executor,
            worker_config=worker_config,
            queue_backend=queue_backend,
            on_event=on_event,
        )
        results = _collect_role_results(dag_results)
        await _emit_event(on_event, "agent_started", {"agent": "qa_engineer", "revision": revisions_used})
        validation = await qa.validate(results, plan)
        await _emit_event(
            on_event,
            "agent_completed",
            {
                "agent": "qa_engineer",
                "revision": revisions_used,
                "pass": bool(validation.get("pass", False)),
            },
        )
        iteration_history.append(
            _iteration_summary(
                revision=revisions_used,
                nodes=revision_nodes,
                dag_results=dag_results,
                validation=validation,
            )
        )
        await _emit_event(
            on_event,
            "dag_iteration_completed",
            {"revision": revisions_used, "pass": bool(validation.get("pass", False))},
        )

    final_result = {
        "success": bool(validation.get("pass", False)),
        "plan": plan,
        "results": results,
        "validation": validation,
        "revisions_used": revisions_used,
        "max_revisions": revision_cap,
        "dag": {
            "queue_backend": queue_backend,
            "worker_config": worker_config.as_dict(),
            "iterations": iteration_history,
            "skipped_tasks": skipped_tasks,
        },
    }
    await _emit_event(
        on_event,
        "run_finished",
        {
            "success": final_result["success"],
            "revisions_used": revisions_used,
            "project_id": project_id or "",
        },
    )
    return final_result


def orchestrate(user_idea: str, mode: str = "full", use_v2: bool = True) -> Dict[str, Any]:
    """Main orchestration entry point."""
    if use_v2:
        return run_agents_v2(user_idea, mode=mode)
    return run_agents(user_idea)


def _build_engineering_dag(tasks: list[dict]) -> tuple[list[TaskNode], list[dict]]:
    """
    Build a dependency-safe engineering DAG.

    Dependency model:
    - database -> backend -> frontend
    - qa role tasks are handled as dedicated post-DAG QA stage
    """
    supported_roles = ["database_engineer", "backend_engineer", "frontend_engineer"]
    role_dependencies = {
        "database_engineer": [],
        "backend_engineer": ["database_engineer"],
        "frontend_engineer": ["backend_engineer"],
    }

    grouped: dict[str, list[str]] = defaultdict(list)
    skipped: list[dict] = []

    for task in tasks:
        role = str(task.get("role", "")).strip().lower()
        description = str(task.get("description", "")).strip()
        if not role or not description:
            continue
        if role in supported_roles:
            grouped[role].append(description)
        elif role == "qa_engineer":
            # QA is executed as a dedicated validation stage after DAG completion.
            continue
        else:
            skipped.append({"role": role, "description": description})

    if not any(grouped.values()):
        raise ValueError("no executable engineering tasks found in plan")

    role_to_node_ids: dict[str, list[str]] = defaultdict(list)
    nodes: list[TaskNode] = []

    for role in supported_roles:
        for index, description in enumerate(grouped.get(role, []), start=1):
            node_id = f"{role}_{index}"
            role_to_node_ids[role].append(node_id)
            nodes.append(
                TaskNode(
                    id=node_id,
                    role=role,
                    description=description,
                    dependencies=[],
                )
            )

    for node in nodes:
        deps: list[str] = []
        for dep_role in role_dependencies.get(node.role, []):
            deps.extend(role_to_node_ids.get(dep_role, []))
        node.dependencies = deps

    return nodes, skipped


def _build_revision_nodes(base_nodes: list[TaskNode], issues: list[str], revision: int) -> list[TaskNode]:
    issue_lines = "\n".join(f"- {item}" for item in issues) if issues else "- QA reported a mismatch."
    id_map = {node.id: f"{node.id}_r{revision}" for node in base_nodes}

    revised_nodes: list[TaskNode] = []
    for node in base_nodes:
        revised_nodes.append(
            TaskNode(
                id=id_map[node.id],
                role=node.role,
                description=(
                    f"{node.description}\n\n"
                    f"Revision #{revision}: apply these QA issues and regenerate full JSON output.\n"
                    f"{issue_lines}"
                ),
                dependencies=[id_map[dep] for dep in node.dependencies],
            )
        )
    return revised_nodes


async def _run_dag_iteration(
    nodes: list[TaskNode],
    router: ModelRouter,
    dag_executor: DagExecutor,
    worker_config: WorkerPoolConfig,
    queue_backend: str,
    on_event: EventCallback | None = None,
) -> dict[str, NodeExecutionResult]:
    roles = sorted(worker_config.as_dict().keys())
    if queue_backend == "redis":
        queue = RedisRoleJobQueue(roles=roles)
    else:
        queue = InMemoryRoleJobQueue(roles=roles)

    worker_pool = AgentWorkerPool(
        queue=queue,
        router=router,
        config=worker_config,
        max_attempts=3,
        on_event=lambda event_name, payload: _emit_event_noawait(
            on_event,
            event_name,
            payload,
        ),
    )

    await worker_pool.start()
    try:
        return await dag_executor.execute(
            nodes=nodes,
            dispatch=worker_pool.submit_and_wait,
            on_event=lambda event_name, payload: _emit_event(
                on_event,
                event_name,
                payload,
            ),
        )
    finally:
        await worker_pool.stop()


def _collect_role_results(dag_results: dict[str, NodeExecutionResult]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {"backend": [], "frontend": [], "database": []}
    role_to_key = {
        "backend_engineer": "backend",
        "frontend_engineer": "frontend",
        "database_engineer": "database",
    }
    for item in dag_results.values():
        if item.status != "completed" or not item.output:
            continue
        key = role_to_key.get(item.role)
        if key:
            grouped[key].append(item.output)
    return grouped


def _iteration_summary(
    revision: int,
    nodes: list[TaskNode],
    dag_results: dict[str, NodeExecutionResult],
    validation: dict[str, Any],
) -> dict[str, Any]:
    return {
        "revision": revision,
        "nodes": [
            {
                "id": node.id,
                "role": node.role,
                "dependencies": node.dependencies,
            }
            for node in nodes
        ],
        "node_results": {
            node_id: {
                "status": result.status,
                "error": result.error,
                "attempts": result.attempts,
                "token_usage": result.token_usage,
            }
            for node_id, result in dag_results.items()
        },
        "qa": validation,
    }


async def _emit_event(
    callback: EventCallback | None,
    event_name: str,
    payload: dict[str, Any],
) -> None:
    if callback is None:
        return
    maybe = callback(event_name, payload)
    if inspect.isawaitable(maybe):
        await maybe


def _emit_event_noawait(
    callback: EventCallback | None,
    event_name: str,
    payload: dict[str, Any],
) -> None:
    if callback is None:
        return
    maybe = callback(event_name, payload)
    if inspect.isawaitable(maybe):
        try:
            asyncio.create_task(maybe)
        except Exception as e:
            logger.warning("orchestrator event callback failed: %s", e)

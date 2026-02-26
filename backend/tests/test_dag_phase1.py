from __future__ import annotations

import pytest

from backend.core.model_router import ModelRouter
from backend.core.orchestration.agent_queue import InMemoryRoleJobQueue
from backend.core.orchestration.agent_worker_pool import AgentWorkerPool, WorkerPoolConfig
from backend.core.orchestration.dag_executor import DagExecutor, DagValidationError, NodeExecutionResult, TaskNode


def test_dag_validation_rejects_cycles():
    nodes = [
        TaskNode(id="db", role="database_engineer", description="db", dependencies=["frontend"]),
        TaskNode(id="backend", role="backend_engineer", description="backend", dependencies=["db"]),
        TaskNode(id="frontend", role="frontend_engineer", description="frontend", dependencies=["backend"]),
    ]

    with pytest.raises(DagValidationError):
        DagExecutor.validate(nodes)


@pytest.mark.asyncio
async def test_dag_marks_blocked_nodes_when_dependency_fails():
    nodes = [
        TaskNode(id="db", role="database_engineer", description="db"),
        TaskNode(id="backend", role="backend_engineer", description="backend", dependencies=["db"]),
    ]

    async def dispatch(node: TaskNode) -> NodeExecutionResult:
        if node.id == "db":
            return NodeExecutionResult(node_id="db", role=node.role, status="failed", error="boom", attempts=3)
        return NodeExecutionResult(node_id=node.id, role=node.role, status="completed", output={}, attempts=1)

    results = await DagExecutor().execute(nodes, dispatch)

    assert results["db"].status == "failed"
    assert results["backend"].status == "blocked"


@pytest.mark.asyncio
async def test_worker_pool_retries_up_to_three_then_succeeds(monkeypatch):
    calls = {"count": 0}

    async def fake_backend(self, prompt, system_prompt):
        calls["count"] += 1
        if calls["count"] < 3:
            raise RuntimeError("transient")
        return {"files_created": ["backend/app.py"], "files_modified": [], "code": {"backend/app.py": "ok"}}

    monkeypatch.setattr(ModelRouter, "call_backend_engineer", fake_backend)

    router = ModelRouter(max_retries=1)
    queue = InMemoryRoleJobQueue(["backend_engineer", "frontend_engineer", "database_engineer"])
    pool = AgentWorkerPool(
        queue=queue,
        router=router,
        config=WorkerPoolConfig(backend_engineer=1, frontend_engineer=1, database_engineer=1),
        max_attempts=3,
    )

    await pool.start()
    try:
        result = await pool.submit_and_wait(
            TaskNode(
                id="backend_1",
                role="backend_engineer",
                description="Build backend",
            )
        )
    finally:
        await pool.stop()

    assert result.status == "completed"
    assert result.attempts == 3
    assert calls["count"] == 3

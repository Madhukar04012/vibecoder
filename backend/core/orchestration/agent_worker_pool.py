"""
Role-specific async worker pool for agent task execution.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable

from backend.agents.backend_agent import BackendEngineerAgent
from backend.agents.database_agent import DatabaseEngineerAgent
from backend.agents.frontend_agent import FrontendEngineerAgent
from backend.core.model_router import ModelRouter
from backend.core.orchestration.agent_queue import AgentJob, AgentJobQueue
from backend.core.orchestration.dag_executor import NodeExecutionResult, TaskNode
from backend.engine.token_ledger import ledger


logger = logging.getLogger(__name__)


@dataclass
class WorkerPoolConfig:
    """Role worker counts."""

    backend_engineer: int = 4
    frontend_engineer: int = 2
    database_engineer: int = 1

    def as_dict(self) -> dict[str, int]:
        return {
            "backend_engineer": max(1, int(self.backend_engineer)),
            "frontend_engineer": max(1, int(self.frontend_engineer)),
            "database_engineer": max(1, int(self.database_engineer)),
        }


class AgentWorkerPool:
    """Executes queued tasks with role-specific worker concurrency."""

    def __init__(
        self,
        queue: AgentJobQueue,
        router: ModelRouter,
        config: WorkerPoolConfig | None = None,
        max_attempts: int = 3,
        on_event: Callable[[str, dict[str, Any]], Any] | None = None,
    ):
        self.queue = queue
        self.router = router
        self.config = (config or WorkerPoolConfig()).as_dict()
        self.max_attempts = max(1, min(int(max_attempts), 3))
        self.on_event = on_event

        self._running = False
        self._workers: list[asyncio.Task] = []
        self._futures: dict[str, asyncio.Future[NodeExecutionResult]] = {}

        self.backend_agent = BackendEngineerAgent(router)
        self.frontend_agent = FrontendEngineerAgent(router)
        self.database_agent = DatabaseEngineerAgent(router)

    async def start(self) -> None:
        if self._running:
            return
        self._running = True

        for role, count in self.config.items():
            for index in range(count):
                task = asyncio.create_task(self._worker_loop(role, index + 1))
                self._workers.append(task)

    async def stop(self) -> None:
        self._running = False
        for task in self._workers:
            task.cancel()
        if self._workers:
            await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()

    async def submit_and_wait(self, node: TaskNode) -> NodeExecutionResult:
        if not self._running:
            raise RuntimeError("worker pool is not running")

        future: asyncio.Future[NodeExecutionResult] = asyncio.get_running_loop().create_future()
        self._futures[node.id] = future

        payload = dict(node.payload)
        payload.setdefault("description", node.description)
        job = AgentJob(
            task_id=node.id,
            role=node.role,
            payload=payload,
            attempt=1,
            max_attempts=self.max_attempts,
            metadata={"dependencies": node.dependencies},
        )
        await self.queue.enqueue(job)
        return await future

    async def _worker_loop(self, role: str, worker_index: int) -> None:
        while self._running:
            try:
                job = await self.queue.dequeue(role)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.exception("queue dequeue failed for role=%s worker=%s: %s", role, worker_index, exc)
                await asyncio.sleep(0.25)
                continue

            started_at = datetime.now(timezone.utc)
            self._emit(
                "task_started",
                {
                    "task_id": job.task_id,
                    "role": job.role,
                    "attempt": job.attempt,
                    "worker_index": worker_index,
                    "started_at": started_at.isoformat(),
                },
            )

            before_usage = self._usage_snapshot(job.role)
            try:
                output = await self._execute_job(job)
                after_usage = self._usage_snapshot(job.role)
                result = NodeExecutionResult(
                    node_id=job.task_id,
                    role=job.role,
                    status="completed",
                    output=output,
                    attempts=job.attempt,
                    token_usage=self._usage_delta(before_usage, after_usage),
                )
                self._resolve(job.task_id, result)
                self._emit(
                    "task_completed",
                    {
                        "task_id": job.task_id,
                        "role": job.role,
                        "attempt": job.attempt,
                        "token_usage": result.token_usage,
                    },
                )
            except Exception as exc:
                if job.attempt < min(job.max_attempts, self.max_attempts):
                    retry_job = AgentJob(
                        task_id=job.task_id,
                        role=job.role,
                        payload=job.payload,
                        attempt=job.attempt + 1,
                        max_attempts=min(job.max_attempts, self.max_attempts),
                        metadata=job.metadata,
                    )
                    self._emit(
                        "task_retry",
                        {
                            "task_id": job.task_id,
                            "role": job.role,
                            "attempt": job.attempt,
                            "next_attempt": retry_job.attempt,
                            "error": str(exc),
                        },
                    )
                    await self.queue.enqueue(retry_job)
                else:
                    after_usage = self._usage_snapshot(job.role)
                    result = NodeExecutionResult(
                        node_id=job.task_id,
                        role=job.role,
                        status="failed",
                        error=str(exc),
                        attempts=job.attempt,
                        token_usage=self._usage_delta(before_usage, after_usage),
                    )
                    self._resolve(job.task_id, result)
                    self._emit(
                        "task_failed",
                        {
                            "task_id": job.task_id,
                            "role": job.role,
                            "attempt": job.attempt,
                            "error": str(exc),
                        },
                    )
            finally:
                try:
                    self.queue.task_done(role)
                except Exception as e:
                    logger.debug("queue.task_done failed for role=%s: %s", role, e)

    async def _execute_job(self, job: AgentJob) -> dict[str, Any]:
        description = str(job.payload.get("description", "")).strip()
        if not description:
            raise ValueError("job payload missing description")

        if job.role == "backend_engineer":
            return await self.backend_agent.build(description)
        if job.role == "frontend_engineer":
            return await self.frontend_agent.build(description)
        if job.role == "database_engineer":
            return await self.database_agent.design(description)
        raise ValueError(f"unsupported worker role: {job.role}")

    def _resolve(self, task_id: str, result: NodeExecutionResult) -> None:
        future = self._futures.pop(task_id, None)
        if future and not future.done():
            future.set_result(result)

    @staticmethod
    def _usage_snapshot(role: str) -> dict[str, float]:
        usage = ledger.by_agent.get(role, {})
        return {
            "input_tokens": float(usage.get("input_tokens", 0)),
            "output_tokens": float(usage.get("output_tokens", 0)),
            "total_tokens": float(usage.get("total_tokens", 0)),
            "cost_usd": float(usage.get("cost_usd", 0.0)),
            "call_count": float(usage.get("call_count", 0)),
        }

    @staticmethod
    def _usage_delta(before: dict[str, float], after: dict[str, float]) -> dict[str, Any]:
        return {
            "input_tokens": int(after["input_tokens"] - before["input_tokens"]),
            "output_tokens": int(after["output_tokens"] - before["output_tokens"]),
            "total_tokens": int(after["total_tokens"] - before["total_tokens"]),
            "cost_usd": round(after["cost_usd"] - before["cost_usd"], 6),
            "call_count": int(after["call_count"] - before["call_count"]),
        }

    def _emit(self, event_name: str, payload: dict[str, Any]) -> None:
        if self.on_event is None:
            return
        try:
            maybe = self.on_event(event_name, payload)
            if inspect.isawaitable(maybe):
                asyncio.create_task(maybe)
        except Exception as e:
            logger.warning("on_event callback failed: %s", e)

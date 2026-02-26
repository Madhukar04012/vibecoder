"""
DAG Executor — Phase 2: Task dependency resolution and dispatch

Components:
  - DAGParser        : validates DAG JSON from TEAM_LEAD, detects cycles
  - DependencyResolver: topological sort → ordered parallel batches
  - TaskDispatcher   : per-task state machine, releases tasks when deps complete

Expected DAG JSON from TEAM_LEAD::

    {
      "tasks": [
        {"id": "t1", "role": "database_engineer", "dependencies": [], "description": "..."},
        {"id": "t2", "role": "backend_engineer",  "dependencies": ["t1"], "description": "..."},
        {"id": "t3", "role": "frontend_engineer", "dependencies": [],     "description": "..."},
        {"id": "t4", "role": "qa_engineer",       "dependencies": ["t2", "t3"], "description": "..."}
      ]
    }

Task state machine:  PENDING → RUNNING → COMPLETE | FAILED
                     PENDING → BLOCKED  (when a dependency fails)
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set

logger = logging.getLogger("dag_executor")

VALID_ROLES = {
    "team_lead",
    "backend_engineer",
    "frontend_engineer",
    "database_engineer",
    "qa_engineer",
}


# ── Data Model ─────────────────────────────────────────────────────────────────

class TaskStatus(str, Enum):
    PENDING  = "PENDING"
    RUNNING  = "RUNNING"
    COMPLETE = "COMPLETE"
    FAILED   = "FAILED"
    BLOCKED  = "BLOCKED"   # dependency failed — will never run


@dataclass
class DAGTask:
    id: str
    role: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    output: Optional[str] = None
    error: Optional[str] = None
    retry_count: int = 0


# ── DAGParser ──────────────────────────────────────────────────────────────────

class DAGParser:
    """
    Validates DAG JSON produced by TEAM_LEAD.

    Raises ValueError on:
      - Missing or empty "tasks" key
      - Task missing "id", "role", or "dependencies"
      - Unknown agent role
      - Duplicate task IDs
      - Reference to non-existent dependency
      - Circular dependency
    """

    @staticmethod
    def parse(dag_json: dict) -> List[DAGTask]:
        """Parse and validate DAG JSON. Returns list of DAGTask objects."""
        if not isinstance(dag_json, dict) or "tasks" not in dag_json:
            raise ValueError("DAG JSON must be an object with a 'tasks' array.")

        raw_tasks: list = dag_json["tasks"]
        if not raw_tasks:
            raise ValueError("DAG 'tasks' array is empty.")

        tasks: List[DAGTask] = []
        seen_ids: Set[str] = set()

        for i, raw in enumerate(raw_tasks):
            if not isinstance(raw, dict):
                raise ValueError(f"Task at index {i} is not an object.")

            tid  = raw.get("id", "").strip()
            role = raw.get("role", "").strip().lower()
            deps = raw.get("dependencies", [])
            desc = raw.get("description", "")

            if not tid:
                raise ValueError(f"Task at index {i} is missing 'id'.")
            if not role:
                raise ValueError(f"Task '{tid}' is missing 'role'.")
            if role not in VALID_ROLES:
                raise ValueError(
                    f"Task '{tid}' has unknown role '{role}'. "
                    f"Valid roles: {sorted(VALID_ROLES)}"
                )
            if tid in seen_ids:
                raise ValueError(f"Duplicate task id '{tid}'.")
            if not isinstance(deps, list):
                raise ValueError(f"Task '{tid}' dependencies must be an array.")

            seen_ids.add(tid)
            tasks.append(DAGTask(id=tid, role=role, description=desc, dependencies=deps))

        # Validate dependency references
        for task in tasks:
            for dep in task.dependencies:
                if dep not in seen_ids:
                    raise ValueError(
                        f"Task '{task.id}' depends on '{dep}' which does not exist."
                    )

        # Detect cycles
        DAGParser._detect_cycles(tasks)

        return tasks

    @staticmethod
    def _detect_cycles(tasks: List[DAGTask]) -> None:
        """Raise ValueError if the task graph contains a cycle (Kahn's algorithm)."""
        in_degree: Dict[str, int] = {t.id: 0 for t in tasks}
        adj: Dict[str, List[str]] = defaultdict(list)

        for task in tasks:
            for dep in task.dependencies:
                adj[dep].append(task.id)
                in_degree[task.id] += 1

        queue = deque(tid for tid, deg in in_degree.items() if deg == 0)
        visited = 0

        while queue:
            node = queue.popleft()
            visited += 1
            for neighbor in adj[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if visited != len(tasks):
            cycle_nodes = [tid for tid, deg in in_degree.items() if deg > 0]
            raise ValueError(
                f"DAG contains a circular dependency involving: {cycle_nodes}"
            )


# ── DependencyResolver ─────────────────────────────────────────────────────────

class DependencyResolver:
    """
    Converts a validated task list into ordered parallel execution batches.

    Each batch is a list of task IDs that can run concurrently (no intra-batch deps).
    Batches must be executed in order — all tasks in batch N must complete before
    batch N+1 is dispatched.

    Example::

        resolver = DependencyResolver(tasks)
        for batch in resolver.batches():
            await asyncio.gather(*[run(tid) for tid in batch])
    """

    def __init__(self, tasks: List[DAGTask]) -> None:
        self._tasks = {t.id: t for t in tasks}

    def batches(self) -> List[List[str]]:
        """Return list of parallel batches in topological order."""
        in_degree: Dict[str, int] = {tid: 0 for tid in self._tasks}
        adj: Dict[str, List[str]] = defaultdict(list)

        for task in self._tasks.values():
            for dep in task.dependencies:
                adj[dep].append(task.id)
                in_degree[task.id] += 1

        queue = deque(tid for tid, deg in in_degree.items() if deg == 0)
        result: List[List[str]] = []

        while queue:
            batch = list(queue)
            queue.clear()
            result.append(batch)

            for node in batch:
                for neighbor in adj[node]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)

        return result


# ── TaskDispatcher ─────────────────────────────────────────────────────────────

# Callback type: called when a task reaches a terminal state
TaskCallback = Callable[[DAGTask], Coroutine[Any, Any, None]]


class TaskDispatcher:
    """
    Manages per-task state machine and dispatches tasks to an executor when
    all their dependencies have completed successfully.

    State transitions:
      PENDING → RUNNING  (when dispatched)
      RUNNING → COMPLETE (on success)
      RUNNING → FAILED   (on error, after retries exhausted)
      PENDING → BLOCKED  (when a dependency task failed)

    Usage::

        dispatcher = TaskDispatcher(tasks, max_retries=3)
        results = await dispatcher.run(executor_fn, event_cb)
    """

    MAX_TASK_RETRIES = 3

    def __init__(
        self,
        tasks: List[DAGTask],
        max_workers: int = 3,
        max_retries: int = 3,
    ) -> None:
        self._tasks: Dict[str, DAGTask] = {t.id: t for t in tasks}
        self._resolver = DependencyResolver(tasks)
        self._max_workers = max_workers
        self._max_retries = max_retries
        self._sem = asyncio.Semaphore(max_workers)

    @property
    def tasks(self) -> Dict[str, DAGTask]:
        return self._tasks

    def snapshot(self) -> List[dict]:
        """Return current task states as a list of dicts (for serialisation)."""
        return [
            {
                "id":          t.id,
                "role":        t.role,
                "description": t.description,
                "status":      t.status.value,
                "retry_count": t.retry_count,
                "error":       t.error,
            }
            for t in self._tasks.values()
        ]

    async def run(
        self,
        executor: Callable[[DAGTask, Dict[str, str]], Coroutine[Any, Any, str]],
        on_event: Optional[TaskCallback] = None,
        context: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        """
        Execute the DAG in topological order with parallel batch dispatch.

        Args:
            executor : async callable(task, context) → str output
            on_event : optional async callback called on each state change
            context  : shared context dict (task outputs written here by key=task.id)

        Returns:
            Dict mapping task_id → output string for all COMPLETE tasks.
        """
        context = context or {}
        failed_tasks: Set[str] = set()

        for batch in self._resolver.batches():
            # Mark tasks whose deps failed as BLOCKED
            runnable = []
            for tid in batch:
                task = self._tasks[tid]
                if any(dep in failed_tasks for dep in task.dependencies):
                    task.status = TaskStatus.BLOCKED
                    logger.warning("[DAG] Task '%s' BLOCKED (dependency failed)", tid)
                    if on_event:
                        await on_event(task)
                else:
                    runnable.append(tid)

            if not runnable:
                continue

            # Run all runnable tasks in this batch concurrently
            await asyncio.gather(
                *[self._run_task(tid, executor, on_event, context, failed_tasks)
                  for tid in runnable]
            )

        return {tid: t.output for tid, t in self._tasks.items()
                if t.status == TaskStatus.COMPLETE and t.output}

    async def _run_task(
        self,
        tid: str,
        executor: Callable[[DAGTask, Dict[str, str]], Coroutine[Any, Any, str]],
        on_event: Optional[TaskCallback],
        context: Dict[str, str],
        failed_tasks: Set[str],
    ) -> None:
        task = self._tasks[tid]

        async with self._sem:
            for attempt in range(self._max_retries):
                task.status = TaskStatus.RUNNING
                task.retry_count = attempt
                logger.info(
                    "[DAG] Task '%s' RUNNING (attempt %d/%d)",
                    tid, attempt + 1, self._max_retries,
                )
                if on_event:
                    await on_event(task)

                try:
                    output = await executor(task, context)
                    task.output = output
                    task.status = TaskStatus.COMPLETE
                    context[tid] = output
                    logger.info("[DAG] Task '%s' COMPLETE", tid)
                    if on_event:
                        await on_event(task)
                    return

                except Exception as exc:
                    task.error = str(exc)
                    logger.warning(
                        "[DAG] Task '%s' failed on attempt %d: %s",
                        tid, attempt + 1, exc,
                    )
                    if attempt < self._max_retries - 1:
                        await asyncio.sleep(0.5 * (2 ** attempt))  # fast backoff before retry
                    else:
                        task.status = TaskStatus.FAILED
                        failed_tasks.add(tid)
                        logger.error("[DAG] Task '%s' FAILED after %d attempts", tid, self._max_retries)
                        if on_event:
                            await on_event(task)
                        return

"""
DAG executor with strict cycle validation and async batch dispatch.
"""

from __future__ import annotations

import asyncio
import inspect
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Literal


class DagValidationError(ValueError):
    """Raised when DAG structure is invalid."""


@dataclass
class TaskNode:
    """One DAG node executed by an agent role."""

    id: str
    role: str
    description: str
    dependencies: list[str] = field(default_factory=list)
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class NodeExecutionResult:
    """Execution status for one DAG node."""

    node_id: str
    role: str
    status: Literal["completed", "failed", "blocked"]
    output: dict[str, Any] | None = None
    error: str | None = None
    attempts: int = 0
    token_usage: dict[str, Any] = field(default_factory=dict)


class DagExecutor:
    """Validates and executes DAG nodes in dependency-safe parallel batches."""

    @staticmethod
    def validate(nodes: list[TaskNode]) -> None:
        if not nodes:
            raise DagValidationError("DAG is empty")

        by_id: dict[str, TaskNode] = {}
        for node in nodes:
            if not node.id:
                raise DagValidationError("node id is required")
            if node.id in by_id:
                raise DagValidationError(f"duplicate node id: {node.id}")
            by_id[node.id] = node

        for node in nodes:
            for dep in node.dependencies:
                if dep not in by_id:
                    raise DagValidationError(f"node '{node.id}' depends on unknown node '{dep}'")

        # Kahn's algorithm for cycle detection.
        in_degree = {node.id: 0 for node in nodes}
        adjacency: dict[str, list[str]] = {node.id: [] for node in nodes}
        for node in nodes:
            for dep in node.dependencies:
                in_degree[node.id] += 1
                adjacency[dep].append(node.id)

        ready = [node_id for node_id, degree in in_degree.items() if degree == 0]
        visited = 0

        while ready:
            node_id = ready.pop()
            visited += 1
            for nxt in adjacency[node_id]:
                in_degree[nxt] -= 1
                if in_degree[nxt] == 0:
                    ready.append(nxt)

        if visited != len(nodes):
            raise DagValidationError("DAG contains a cycle")

    async def execute(
        self,
        nodes: list[TaskNode],
        dispatch: Callable[[TaskNode], Awaitable[NodeExecutionResult]],
        on_event: Callable[[str, dict[str, Any]], Any] | None = None,
    ) -> dict[str, NodeExecutionResult]:
        self.validate(nodes)
        node_map = {node.id: node for node in nodes}

        remaining = set(node_map.keys())
        completed: set[str] = set()
        failed: set[str] = set()
        results: dict[str, NodeExecutionResult] = {}

        while remaining:
            ready = [
                node_map[node_id]
                for node_id in remaining
                if all(dep in completed for dep in node_map[node_id].dependencies)
                and not any(dep in failed for dep in node_map[node_id].dependencies)
            ]

            if not ready:
                # Remaining nodes are blocked by failed dependencies.
                for node_id in sorted(remaining):
                    blocked_deps = [dep for dep in node_map[node_id].dependencies if dep in failed]
                    results[node_id] = NodeExecutionResult(
                        node_id=node_id,
                        role=node_map[node_id].role,
                        status="blocked",
                        error=f"blocked by failed dependencies: {blocked_deps}",
                    )
                break

            if on_event:
                maybe = on_event(
                    "dag_batch_started",
                    {"node_ids": [node.id for node in ready], "size": len(ready)},
                )
                if inspect.isawaitable(maybe):
                    await maybe

            batch_results = await asyncio.gather(*[dispatch(node) for node in ready])
            for node, outcome in zip(ready, batch_results):
                results[node.id] = outcome
                if outcome.status == "completed":
                    completed.add(node.id)
                else:
                    failed.add(node.id)
                remaining.remove(node.id)

            if on_event:
                maybe = on_event(
                    "dag_batch_finished",
                    {
                        "node_ids": [node.id for node in ready],
                        "completed": [node.id for node in ready if results[node.id].status == "completed"],
                        "failed": [node.id for node in ready if results[node.id].status == "failed"],
                    },
                )
                if inspect.isawaitable(maybe):
                    await maybe

        return results

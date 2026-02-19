"""Parallel task execution with dependency grouping (plan Phase 3)."""
from __future__ import annotations
import asyncio
from typing import List, Callable, Any, TypeVar

T = TypeVar("T")

def _topological_groups(tasks: List[Any], get_deps: Callable[[Any], List[str]], get_id: Callable[[Any], str]) -> List[List[Any]]:
    ids = {get_id(t): t for t in tasks}
    in_degree = {get_id(t): 0 for t in tasks}
    for t in tasks:
        for d in get_deps(t):
            if d in ids:
                in_degree[get_id(t)] = in_degree.get(get_id(t), 0) + 1
    groups = []
    remaining = list(tasks)
    while remaining:
        ready = [t for t in remaining if in_degree.get(get_id(t), 0) == 0]
        if not ready:
            break
        groups.append(ready)
        for t in ready:
            remaining.remove(t)
            tid = get_id(t)
            for o in remaining:
                if tid in get_deps(o):
                    in_degree[get_id(o)] = in_degree.get(get_id(o), 1) - 1
    if remaining:
        groups.append(remaining)
    return groups

class ParallelExecutor:
    """Execute independent tasks in parallel with concurrency limit."""
    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def execute_parallel(
        self,
        tasks: List[Any],
        execute_fn: Callable[[Any], Any],
        get_deps: Callable[[Any], List[str]],
        get_id: Callable[[Any], str],
    ) -> List[Any]:
        groups = _topological_groups(tasks, get_deps, get_id)
        results = []
        async def run_one(t):
            async with self._semaphore:
                out = execute_fn(t)
                return await out if asyncio.iscoroutine(out) else out
        for group in groups:
            batch = await asyncio.gather(*[run_one(t) for t in group])
            results.extend(batch)
        return results

"""
Role-aware async job queue for agent workers.

Phase 1 implementation uses an in-memory queue and provides an optional Redis
backend for production queueing.
"""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import asdict, dataclass, field
from typing import Any, Protocol


@dataclass
class AgentJob:
    """A single agent execution job."""

    task_id: str
    role: str
    payload: dict[str, Any]
    attempt: int = 1
    max_attempts: int = 3
    metadata: dict[str, Any] = field(default_factory=dict)


class AgentJobQueue(Protocol):
    """Queue interface used by worker pools."""

    async def enqueue(self, job: AgentJob) -> None:
        ...

    async def dequeue(self, role: str) -> AgentJob:
        ...

    def task_done(self, role: str) -> None:
        ...


class InMemoryRoleJobQueue:
    """In-memory role-partitioned async queues."""

    def __init__(self, roles: list[str]):
        self._queues: dict[str, asyncio.Queue[AgentJob]] = {role: asyncio.Queue() for role in roles}

    async def enqueue(self, job: AgentJob) -> None:
        queue = self._queues.get(job.role)
        if queue is None:
            raise ValueError(f"unknown role queue: {job.role}")
        await queue.put(job)

    async def dequeue(self, role: str) -> AgentJob:
        queue = self._queues.get(role)
        if queue is None:
            raise ValueError(f"unknown role queue: {role}")
        return await queue.get()

    def task_done(self, role: str) -> None:
        queue = self._queues.get(role)
        if queue is None:
            raise ValueError(f"unknown role queue: {role}")
        queue.task_done()


class RedisRoleJobQueue:
    """
    Optional Redis-backed role queues.

    Uses one Redis list per role and BLPOP for worker consumption.
    """

    def __init__(self, roles: list[str], redis_url: str | None = None, namespace: str = "vibecober:queue"):
        self.roles = set(roles)
        self.namespace = namespace
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._redis = None

    async def _client(self):
        if self._redis is not None:
            return self._redis
        try:
            import redis.asyncio as redis  # type: ignore
        except Exception as exc:  # pragma: no cover - import guard
            raise RuntimeError("redis.asyncio is required for RedisRoleJobQueue") from exc

        self._redis = redis.from_url(self.redis_url, decode_responses=True)
        return self._redis

    def _key(self, role: str) -> str:
        return f"{self.namespace}:{role}"

    async def enqueue(self, job: AgentJob) -> None:
        if job.role not in self.roles:
            raise ValueError(f"unknown role queue: {job.role}")
        client = await self._client()
        await client.rpush(self._key(job.role), json.dumps(asdict(job)))

    async def dequeue(self, role: str) -> AgentJob:
        if role not in self.roles:
            raise ValueError(f"unknown role queue: {role}")

        client = await self._client()
        while True:
            result = await client.blpop(self._key(role), timeout=1)
            if result:
                _, raw = result
                data = json.loads(raw)
                return AgentJob(**data)

    def task_done(self, role: str) -> None:
        # Redis lists do not need explicit ack in this simple implementation.
        _ = role

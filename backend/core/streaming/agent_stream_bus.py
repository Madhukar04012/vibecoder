"""
WebSocket broadcast bus for per-project agent events.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any, Dict, Set

from fastapi import WebSocket


class AgentStreamBus:
    """Tracks active WebSocket clients and broadcasts events by project_id."""

    def __init__(self):
        self._connections: Dict[str, Set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, project_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections[project_id].add(websocket)

    async def disconnect(self, project_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.get(project_id, set()).discard(websocket)
            if not self._connections.get(project_id):
                self._connections.pop(project_id, None)

    async def broadcast(self, project_id: str, payload: dict[str, Any]) -> None:
        async with self._lock:
            targets = list(self._connections.get(project_id, set()))

        dead: list[WebSocket] = []
        for ws in targets:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)

        if dead:
            async with self._lock:
                for ws in dead:
                    self._connections.get(project_id, set()).discard(ws)

    async def count_connections(self, project_id: str) -> int:
        async with self._lock:
            return len(self._connections.get(project_id, set()))


_agent_stream_bus = AgentStreamBus()


def get_agent_stream_bus() -> AgentStreamBus:
    return _agent_stream_bus

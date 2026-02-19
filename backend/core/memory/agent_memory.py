"""Agent vector memory - store/recall experiences (plan Phase 1.3)."""
from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime
from backend.memory.indexer import embed, index_chunk, search, build_scope_key

def _scope_for_agent(agent_name: str, run_id: str = "global") -> str:
    return build_scope_key("project", project_id=f"agent_{agent_name}_{run_id}", version="v1")

class AgentMemory:
    def __init__(self, agent_name: str, run_id: str = "global") -> None:
        self.agent_name = agent_name
        self.run_id = run_id
        self._scope = _scope_for_agent(agent_name, run_id)

    def store_experience(self, experience: str, outcome: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        meta = metadata or {}
        meta["outcome"] = outcome
        meta["timestamp"] = datetime.utcnow().isoformat()
        meta["agent"] = self.agent_name
        index_chunk(experience, meta, scope_key=self._scope)

    def recall_similar(self, query: str, n: int = 5) -> List[Dict[str, Any]]:
        results = search(query, k=n, scope_key=self._scope)
        return [{"text": text, "metadata": meta, "distance": dist} for _, dist, text, meta in results]

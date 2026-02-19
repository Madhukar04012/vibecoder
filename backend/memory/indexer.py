"""
Semantic memory indexer with scope and version governance.

Memory can be isolated by project, user, or global scope and cleared per scope.
"""

from __future__ import annotations

import hashlib
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


DEFAULT_SCOPE_KEY = "global:v1"
_DIMENSION = 384


class MockIndex:
    """Mock FAISS-compatible index used when faiss is unavailable."""

    def __init__(self, dimension: int):
        self.dimension = dimension
        self.vectors: List[np.ndarray] = []

    def add(self, vectors: np.ndarray) -> None:
        for vector in vectors:
            self.vectors.append(vector)

    def search(self, query: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
        if not self.vectors:
            return np.array([[-1.0] * k]), np.array([[-1] * k])

        k = min(k, len(self.vectors))
        distances = [float(np.linalg.norm(query - vector)) for vector in self.vectors]
        indices = np.argsort(distances)[:k]
        dists = np.array([distances[int(i)] for i in indices])
        return dists.reshape(1, -1), indices.reshape(1, -1)

    @property
    def ntotal(self) -> int:
        return len(self.vectors)


@dataclass
class ScopedIndex:
    """In-memory scoped index store."""

    version: str
    index: Any
    chunks: List[str] = field(default_factory=list)
    metadata: List[Dict[str, Any]] = field(default_factory=list)


_LOCK = threading.Lock()
_SCOPES: Dict[str, ScopedIndex] = {}


_EMBED_MODEL = None
_USE_TRANSFORMER: Optional[bool] = None


def build_scope_key(
    scope: str = "global",
    project_id: str | None = None,
    user_id: str | None = None,
    version: str = "v1",
) -> str:
    """Build a canonical memory scope key."""
    scope = (scope or "global").strip().lower()
    version = (version or "v1").strip() or "v1"

    if scope == "project":
        if not project_id:
            raise ValueError("project scope requires project_id")
        return f"project:{project_id}:{version}"

    if scope == "user":
        if not user_id:
            raise ValueError("user scope requires user_id")
        return f"user:{user_id}:{version}"

    if scope == "global":
        return f"global:{version}"

    # custom namespace
    return f"{scope}:{version}"


def _create_index() -> Any:
    try:
        import faiss

        return faiss.IndexFlatL2(_DIMENSION)
    except ImportError:
        return MockIndex(_DIMENSION)


def _ensure_scope(scope_key: str) -> ScopedIndex:
    scoped = _SCOPES.get(scope_key)
    if scoped is None:
        version = scope_key.split(":")[-1] if ":" in scope_key else "v1"
        scoped = ScopedIndex(version=version, index=_create_index())
        _SCOPES[scope_key] = scoped
    return scoped


def _get_embed_model():
    global _EMBED_MODEL, _USE_TRANSFORMER

    if _USE_TRANSFORMER is not None:
        return _EMBED_MODEL

    try:
        from sentence_transformers import SentenceTransformer

        _EMBED_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
        _USE_TRANSFORMER = True
    except ImportError:
        _USE_TRANSFORMER = False

    return _EMBED_MODEL


def embed(text: str) -> np.ndarray:
    """Embed text using sentence-transformers or deterministic hash fallback."""
    model = _get_embed_model()
    if model is not None and _USE_TRANSFORMER:
        vec = model.encode(text, show_progress_bar=False)
        return np.array(vec, dtype=np.float32)

    result: List[float] = []
    for i in range(12):
        digest = hashlib.sha256(f"{i}:{text}".encode("utf-8")).digest()
        result.extend(float(byte) / 255.0 for byte in digest)

    arr = np.array(result[:_DIMENSION], dtype=np.float32)
    norm = np.linalg.norm(arr)
    if norm > 0:
        arr = arr / norm
    return arr


def index_chunk(
    text: str,
    metadata: Optional[Dict[str, Any]] = None,
    scope_key: str = DEFAULT_SCOPE_KEY,
) -> int:
    """Add a text chunk to a scoped index."""
    with _LOCK:
        scoped = _ensure_scope(scope_key)
        vector = embed(text)
        scoped.index.add(vector.reshape(1, -1))
        scoped.chunks.append(text)
        scoped.metadata.append(metadata or {})
        return len(scoped.chunks) - 1


def _split_into_chunks(content: str, max_lines: int = 50) -> List[str]:
    lines = content.split("\n")
    chunks: List[str] = []
    bucket: List[str] = []

    for line in lines:
        bucket.append(line)
        if len(bucket) >= max_lines:
            chunks.append("\n".join(bucket))
            bucket = []

    if bucket:
        chunks.append("\n".join(bucket))

    return chunks


def index_file(path: str, content: str, scope_key: str = DEFAULT_SCOPE_KEY) -> List[int]:
    """Index a file by chunking it and storing chunks under a scope."""
    chunk_ids: List[int] = []
    for chunk in _split_into_chunks(content):
        chunk_id = index_chunk(chunk, {"file": path, "type": "code"}, scope_key=scope_key)
        chunk_ids.append(chunk_id)
    return chunk_ids


def search(
    query: str,
    k: int = 5,
    scope_key: str = DEFAULT_SCOPE_KEY,
) -> List[Tuple[int, float, str, Dict[str, Any]]]:
    """Search similar chunks in the given scope."""
    with _LOCK:
        scoped = _ensure_scope(scope_key)
        if scoped.index.ntotal == 0:
            return []

        vector = embed(query)
        distances, indices = scoped.index.search(vector.reshape(1, -1), k)

        results: List[Tuple[int, float, str, Dict[str, Any]]] = []
        for distance, index in zip(distances[0], indices[0]):
            idx = int(index)
            if idx < 0 or idx >= len(scoped.chunks):
                continue
            results.append((idx, float(distance), scoped.chunks[idx], scoped.metadata[idx]))
        return results


def list_scopes() -> List[str]:
    """List all known memory scopes."""
    with _LOCK:
        return sorted(_SCOPES.keys())


def get_index_stats(scope_key: str | None = None) -> Dict[str, Any]:
    """Get stats for one scope or all scopes."""
    with _LOCK:
        if scope_key is not None:
            scoped = _ensure_scope(scope_key)
            return {
                "scope": scope_key,
                "version": scoped.version,
                "total_chunks": len(scoped.chunks),
                "index_size": scoped.index.ntotal,
                "dimension": _DIMENSION,
            }

        scoped_stats = {}
        for key in _SCOPES:
            scoped = _SCOPES[key]
            scoped_stats[key] = {
                "version": scoped.version,
                "total_chunks": len(scoped.chunks),
                "index_size": scoped.index.ntotal,
            }

        return {
            "scopes": scoped_stats,
            "scope_count": len(scoped_stats),
            "dimension": _DIMENSION,
        }


def clear_index(scope_key: str | None = None) -> None:
    """Clear a single scope or all scopes."""
    with _LOCK:
        if scope_key is None:
            _SCOPES.clear()
            return

        _SCOPES.pop(scope_key, None)

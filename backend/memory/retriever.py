"""
Semantic retriever for scoped memory contexts.
"""

from __future__ import annotations

from typing import List

from backend.memory.indexer import search, get_index_stats, DEFAULT_SCOPE_KEY


def retrieve_context(query: str, k: int = 5, scope_key: str = DEFAULT_SCOPE_KEY) -> str:
    """Retrieve formatted context from the scoped index."""
    results = search(query, k=k, scope_key=scope_key)

    if not results:
        return "No relevant context found in memory."

    lines = [f"Retrieved {len(results)} related chunks from scope '{scope_key}':"]
    for idx, distance, text, metadata in results:
        file_path = metadata.get("file", "unknown")
        preview = text[:500] + "..." if len(text) > 500 else text
        relevance = 1 / (1 + distance)
        lines.append(f"\n{idx}. [{file_path}] (relevance: {relevance:.2f})")
        lines.append(f"   {preview[:200].replace(chr(10), ' ')}")

    return "\n".join(lines)


def retrieve_for_file(file_path: str, k: int = 3, scope_key: str = DEFAULT_SCOPE_KEY) -> str:
    """Retrieve context relevant to a specific file path in a scope."""
    parts = file_path.replace("\\", "/").split("/")
    query_parts = []
    if len(parts) >= 2:
        query_parts.append(parts[-2])
    query_parts.append(parts[-1])
    return retrieve_context(" ".join(query_parts), k=k, scope_key=scope_key)


def get_similar_files(
    file_path: str,
    content: str,
    k: int = 3,
    scope_key: str = DEFAULT_SCOPE_KEY,
) -> List[str]:
    """Find similar files in a scoped memory index."""
    results = search(f"{file_path} {content[:200]}", k=k, scope_key=scope_key)

    seen = set()
    files: List[str] = []
    for _, _, _, metadata in results:
        path = metadata.get("file", "")
        if path and path not in seen:
            seen.add(path)
            files.append(path)

    return files


def has_indexed_content(scope_key: str = DEFAULT_SCOPE_KEY) -> bool:
    """Check whether the selected scope has indexed chunks."""
    stats = get_index_stats(scope_key=scope_key)
    return int(stats.get("total_chunks", 0)) > 0

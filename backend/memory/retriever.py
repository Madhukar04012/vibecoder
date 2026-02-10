"""
Semantic Retriever — Phase-1

Retrieves relevant context from the semantic index.
Used by Engineer agent before generating code.

Usage:
    from memory.retriever import retrieve_context
    
    context = retrieve_context("React component with state")
    # Returns: "Found 3 related chunks:\n1. src/App.jsx: ..."
"""

from typing import List, Optional

from backend.memory.indexer import search, get_index_stats


def retrieve_context(query: str, k: int = 5) -> str:
    """
    Retrieve relevant code context for a query.
    
    Args:
        query: Search query (can be file path, description, etc.)
        k: Number of chunks to retrieve
        
    Returns:
        Formatted context string for LLM consumption
    """
    results = search(query, k)
    
    if not results:
        return "No relevant context found in memory."
    
    parts = [f"Retrieved {len(results)} related chunks:"]
    
    for i, (idx, dist, text, meta) in enumerate(results, 1):
        file_path = meta.get("file", "unknown")
        
        # Truncate long chunks
        preview = text[:500] + "..." if len(text) > 500 else text
        
        parts.append(f"\n{i}. [{file_path}] (relevance: {1/(1+dist):.2f})")
        parts.append(f"   {preview[:200].replace(chr(10), ' ')}")
    
    return "\n".join(parts)


def retrieve_for_file(file_path: str, k: int = 3) -> str:
    """
    Retrieve context relevant to a specific file being generated.
    
    Args:
        file_path: Path of file being generated
        k: Number of chunks
        
    Returns:
        Context string
    """
    # Extract meaningful parts from file path
    parts = file_path.replace("\\", "/").split("/")
    
    # Build query from filename and parent folder
    query_parts = []
    if len(parts) >= 2:
        query_parts.append(parts[-2])  # Parent folder
    query_parts.append(parts[-1])  # Filename
    
    query = " ".join(query_parts)
    
    return retrieve_context(query, k)


def get_similar_files(file_path: str, content: str, k: int = 3) -> List[str]:
    """
    Find files similar to the one being created.
    
    Args:
        file_path: New file path
        content: New file content (partial)
        k: Number of similar files
        
    Returns:
        List of similar file paths
    """
    # Search by both path pattern and content
    results = search(f"{file_path} {content[:200]}", k)
    
    seen = set()
    files = []
    for _, _, _, meta in results:
        path = meta.get("file", "")
        if path and path not in seen:
            seen.add(path)
            files.append(path)
    
    return files


def has_indexed_content() -> bool:
    """Check if there's any indexed content."""
    stats = get_index_stats()
    return stats.get("total_chunks", 0) > 0

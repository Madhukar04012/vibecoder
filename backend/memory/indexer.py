"""
Semantic Indexer — Phase-1

FAISS-based indexer for semantic code search.
Indexes code chunks for retrieval during Engineer execution.

Usage:
    from memory.indexer import index_chunk, get_index_stats
    
    index_chunk("def hello(): print('world')", metadata={"file": "main.py"})
    stats = get_index_stats()
"""

import numpy as np
from typing import Optional, List, Dict, Any


# Index state
_index = None
_chunks: List[str] = []
_metadata: List[Dict[str, Any]] = []
_dimension = 384  # Embedding dimension


def _init_index():
    """Lazily initialize FAISS index."""
    global _index
    if _index is None:
        try:
            import faiss
            _index = faiss.IndexFlatL2(_dimension)
        except ImportError:
            print("[Memory] FAISS not installed, using mock index")
            _index = MockIndex(_dimension)


class MockIndex:
    """Mock FAISS index for when FAISS isn't installed."""
    
    def __init__(self, dimension: int):
        self.dimension = dimension
        self.vectors: List[np.ndarray] = []
    
    def add(self, vectors: np.ndarray):
        for v in vectors:
            self.vectors.append(v)
    
    def search(self, query: np.ndarray, k: int):
        if not self.vectors:
            return np.array([[-1.0] * k]), np.array([[-1] * k])
        
        # Simple cosine-ish search
        k = min(k, len(self.vectors))
        distances = []
        for v in self.vectors:
            dist = np.linalg.norm(query - v)
            distances.append(dist)
        
        indices = np.argsort(distances)[:k]
        dists = np.array([distances[i] for i in indices])
        
        return dists.reshape(1, -1), indices.reshape(1, -1)
    
    @property
    def ntotal(self) -> int:
        return len(self.vectors)


# ─── Embedding Model (Lazy Singleton) ───────────────────────────────────────

_embed_model = None
_use_transformer = None


def _get_embed_model():
    """Lazy-load sentence-transformers model."""
    global _embed_model, _use_transformer
    
    if _use_transformer is not None:
        return _embed_model
    
    try:
        from sentence_transformers import SentenceTransformer
        _embed_model = SentenceTransformer("all-MiniLM-L6-v2")
        _use_transformer = True
        print("[Memory] Using sentence-transformers (all-MiniLM-L6-v2)")
    except ImportError:
        _use_transformer = False
        print("[Memory] sentence-transformers not installed, using hash embeddings")
    
    return _embed_model


def embed(text: str) -> np.ndarray:
    """
    Convert text to embedding vector.
    
    Uses sentence-transformers (all-MiniLM-L6-v2) when available.
    Falls back to hash-based embedding otherwise.
    
    Args:
        text: Text to embed
        
    Returns:
        384-dimensional vector
    """
    model = _get_embed_model()
    
    if model is not None and _use_transformer:
        # Use real transformer embeddings
        vec = model.encode(text, show_progress_bar=False)
        return np.array(vec, dtype=np.float32)
    
    # Fallback: deterministic hash-based embedding
    import hashlib
    
    result = []
    for i in range(12):
        variant = f"{i}:{text}"
        h = hashlib.sha256(variant.encode()).digest()
        result.extend([float(b) / 255.0 for b in h])
    
    arr = np.array(result[:_dimension], dtype=np.float32)
    
    # Normalize
    norm = np.linalg.norm(arr)
    if norm > 0:
        arr = arr / norm
    
    return arr


def index_chunk(
    text: str,
    metadata: Optional[Dict[str, Any]] = None
) -> int:
    """
    Add a text chunk to the index.
    
    Args:
        text: Code or text to index
        metadata: Optional metadata (file path, etc.)
        
    Returns:
        Index ID of the chunk
    """
    _init_index()
    
    vector = embed(text)
    _index.add(vector.reshape(1, -1))
    
    _chunks.append(text)
    _metadata.append(metadata or {})
    
    return len(_chunks) - 1


def index_file(path: str, content: str) -> List[int]:
    """
    Index a file by splitting into chunks.
    
    Args:
        path: File path
        content: File content
        
    Returns:
        List of chunk IDs
    """
    # Split by functions/classes or by lines
    chunks = _split_into_chunks(content)
    
    ids = []
    for chunk in chunks:
        idx = index_chunk(chunk, {"file": path, "type": "code"})
        ids.append(idx)
    
    return ids


def _split_into_chunks(content: str, max_lines: int = 50) -> List[str]:
    """Split content into indexable chunks."""
    lines = content.split('\n')
    chunks = []
    
    current_chunk = []
    for line in lines:
        current_chunk.append(line)
        if len(current_chunk) >= max_lines:
            chunks.append('\n'.join(current_chunk))
            current_chunk = []
    
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
    
    return chunks


def search(query: str, k: int = 5) -> List[tuple[int, float, str, dict]]:
    """
    Search for similar chunks.
    
    Args:
        query: Search query
        k: Number of results
        
    Returns:
        List of (id, distance, text, metadata) tuples
    """
    _init_index()
    
    if _index.ntotal == 0:
        return []
    
    vector = embed(query)
    distances, indices = _index.search(vector.reshape(1, -1), k)
    
    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx >= 0 and idx < len(_chunks):
            results.append((int(idx), float(dist), _chunks[idx], _metadata[idx]))
    
    return results


def get_index_stats() -> Dict[str, int]:
    """Get index statistics."""
    _init_index()
    return {
        "total_chunks": len(_chunks),
        "index_size": _index.ntotal,
        "dimension": _dimension,
    }


def clear_index() -> None:
    """Clear all indexed data."""
    global _index, _chunks, _metadata
    _index = None
    _chunks = []
    _metadata = []

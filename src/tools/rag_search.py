"""
RAG search functionality for querying the internal knowledge base.

Provides vector similarity search over the indexed documents.
"""

from typing import List, Optional, Dict, Any
from langchain_community.vectorstores import FAISS
from rich.console import Console

from src.config.settings import get_settings
from src.tools.rag_loader import get_or_create_vectorstore
from src.tools.api_logger import (
    APICallLogger,
    log_search_query,
    log_search_results,
)

console = Console()

# Global vector store cache
_vectorstore_cache: Optional[FAISS] = None
_cache_kb_path: Optional[str] = None


def initialize_vectorstore(kb_path: str, force_rebuild: bool = False) -> FAISS:
    """
    Initialize or get cached vector store for a knowledge base.

    Args:
        kb_path: Path to knowledge base directory
        force_rebuild: Force rebuild of vector store

    Returns:
        Initialized FAISS vector store
    """
    global _vectorstore_cache, _cache_kb_path

    # Return cached vectorstore if same kb_path and not forcing rebuild
    if not force_rebuild and _vectorstore_cache is not None and _cache_kb_path == kb_path:
        return _vectorstore_cache

    # Load or create vector store
    vectorstore = get_or_create_vectorstore(
        kb_path=kb_path,
        force_rebuild=force_rebuild,
    )

    # Cache it
    _vectorstore_cache = vectorstore
    _cache_kb_path = kb_path

    return vectorstore


def search_internal(
    query: str,
    kb_path: Optional[str] = None,
    top_k: int = 5,
    score_threshold: Optional[float] = None,
) -> List[str]:
    """
    Search the internal knowledge base using vector similarity.

    Args:
        query: The search query
        kb_path: Path to knowledge base (required for first call)
        top_k: Number of top results to return
        score_threshold: Optional minimum similarity score (0-1)

    Returns:
        List of relevant document chunks as strings

    Raises:
        ValueError: If kb_path not provided and vectorstore not initialized
    """
    settings = get_settings()

    # Use default top_k from settings if not specified
    if top_k is None:
        top_k = settings.top_k_results

    # Need kb_path for first initialization
    if _vectorstore_cache is None and kb_path is None:
        raise ValueError(
            "kb_path must be provided for first search call to initialize vectorstore"
        )

    # Initialize vectorstore if needed
    if kb_path:
        vectorstore = initialize_vectorstore(kb_path)
    else:
        vectorstore = _vectorstore_cache

    # Log search query details
    log_search_query(
        query=query,
        top_k=top_k,
        vectorstore_size=vectorstore.index.ntotal,
    )

    # Perform similarity search
    console.print(f"[cyan]🔍 Searching knowledge base for:[/cyan] {query}")
    console.print(f"  Retrieving top {top_k} results")

    # Similarity search with API call tracking
    with APICallLogger(
        api_name="OpenAI Embeddings",
        operation="Query embedding generation",
        model=settings.embedding_model,
        query_length=len(query),
    ) as logger:
        if score_threshold:
            # Search with score threshold
            docs_with_scores = vectorstore.similarity_search_with_score(query, k=top_k)
            # Filter by threshold (FAISS returns distance, lower is better)
            # Convert to similarity (1 - normalized_distance)
            results = [
                doc for doc, score in docs_with_scores
                if score <= (1 - score_threshold) * 100  # Rough conversion
            ]
            scores = [score for doc, score in docs_with_scores if score <= (1 - score_threshold) * 100]
        else:
            # Simple similarity search
            results = vectorstore.similarity_search(query, k=top_k)
            scores = None

        logger.log_result(
            results_found=len(results),
            query_tokens_estimated=int(len(query) / 4),
        )

    # Extract page content
    chunks = [doc.page_content for doc in results]

    console.print(f"[green]✓[/green] Found {len(chunks)} relevant chunks")

    # Log search results
    log_search_results(results=chunks, scores=scores)

    # Log preview of first result
    if chunks:
        preview = chunks[0][:100] + "..." if len(chunks[0]) > 100 else chunks[0]
        console.print(f"  [dim]First result preview: {preview}[/dim]")

    return chunks


def search_internal_with_metadata(
    query: str,
    kb_path: Optional[str] = None,
    top_k: int = 5,
    score_threshold: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """
    Search the internal knowledge base and return results with metadata.

    Args:
        query: The search query
        kb_path: Path to knowledge base (required for first call)
        top_k: Number of top results to return
        score_threshold: Optional minimum similarity score

    Returns:
        List of dicts with 'content', 'source', and 'score' keys
    """
    settings = get_settings()

    if top_k is None:
        top_k = settings.top_k_results

    if _vectorstore_cache is None and kb_path is None:
        raise ValueError(
            "kb_path must be provided for first search call to initialize vectorstore"
        )

    # Initialize vectorstore if needed
    if kb_path:
        vectorstore = initialize_vectorstore(kb_path)
    else:
        vectorstore = _vectorstore_cache

    # Perform similarity search with scores
    console.print(f"[cyan]🔍 Searching knowledge base (with metadata) for:[/cyan] {query}")

    docs_with_scores = vectorstore.similarity_search_with_score(query, k=top_k)

    # Format results
    results = []
    for doc, score in docs_with_scores:
        result = {
            "content": doc.page_content,
            "source": doc.metadata.get("source", "unknown"),
            "score": float(score),
        }
        results.append(result)

    console.print(f"[green]✓[/green] Found {len(results)} relevant chunks with metadata")

    return results


def clear_vectorstore_cache():
    """
    Clear the cached vector store.

    Useful when switching between different knowledge bases or forcing reload.
    """
    global _vectorstore_cache, _cache_kb_path

    _vectorstore_cache = None
    _cache_kb_path = None

    console.print("[yellow]Vector store cache cleared[/yellow]")


def get_vectorstore_info() -> Dict[str, Any]:
    """
    Get information about the currently loaded vector store.

    Returns:
        Dict with vectorstore information or None if not loaded
    """
    if _vectorstore_cache is None:
        return {
            "loaded": False,
            "kb_path": None,
            "num_chunks": 0,
        }

    return {
        "loaded": True,
        "kb_path": _cache_kb_path,
        "num_chunks": _vectorstore_cache.index.ntotal,
    }

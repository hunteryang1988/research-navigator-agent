"""
RAG document loader and vector store builder.

Handles loading documents from a directory, splitting them into chunks,
generating embeddings, and building/persisting a FAISS vector store.
"""

import os
from pathlib import Path
from typing import List, Optional
import pickle

from langchain_community.document_loaders import (
    DirectoryLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from rich.console import Console

from src.config.settings import get_settings
from src.tools.api_logger import (
    APICallLogger,
    log_embedding_call,
    log_vectorstore_operation,
)

console = Console()


def load_documents(kb_path: str) -> List[Document]:
    """
    Load documents from a knowledge base directory.

    Supports .txt, .md files. Can be extended to support PDF, DOCX, etc.

    Args:
        kb_path: Path to directory containing documents

    Returns:
        List of LangChain Document objects

    Raises:
        ValueError: If kb_path doesn't exist or contains no documents
    """
    kb_dir = Path(kb_path)

    if not kb_dir.exists():
        raise ValueError(f"Knowledge base path does not exist: {kb_path}")

    if not kb_dir.is_dir():
        raise ValueError(f"Knowledge base path is not a directory: {kb_path}")

    console.print(f"[cyan]Loading documents from:[/cyan] {kb_path}")

    documents = []

    # Load markdown files
    try:
        md_loader = DirectoryLoader(
            kb_path,
            glob="**/*.md",
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"},
            show_progress=True,
        )
        md_docs = md_loader.load()
        documents.extend(md_docs)
        console.print(f"  Loaded {len(md_docs)} markdown files")
    except Exception as e:
        console.print(f"  [yellow]Warning loading markdown files: {e}[/yellow]")

    # Load text files
    try:
        txt_loader = DirectoryLoader(
            kb_path,
            glob="**/*.txt",
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"},
            show_progress=True,
        )
        txt_docs = txt_loader.load()
        documents.extend(txt_docs)
        console.print(f"  Loaded {len(txt_docs)} text files")
    except Exception as e:
        console.print(f"  [yellow]Warning loading text files: {e}[/yellow]")

    if not documents:
        raise ValueError(f"No documents found in {kb_path}")

    console.print(f"[green]✓[/green] Total documents loaded: {len(documents)}")
    return documents


def split_documents(
    documents: List[Document],
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> List[Document]:
    """
    Split documents into smaller chunks for better retrieval.

    Args:
        documents: List of documents to split
        chunk_size: Maximum characters per chunk
        chunk_overlap: Number of overlapping characters between chunks

    Returns:
        List of document chunks
    """
    console.print(f"[cyan]Splitting documents into chunks...[/cyan]")
    console.print(f"  Chunk size: {chunk_size}, Overlap: {chunk_overlap}")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""],
    )

    chunks = text_splitter.split_documents(documents)

    console.print(f"[green]✓[/green] Created {len(chunks)} chunks from {len(documents)} documents")
    return chunks


def build_vectorstore(
    documents: List[Document],
    output_dir: Optional[str] = None,
) -> FAISS:
    """
    Build a FAISS vector store from documents.

    Args:
        documents: List of document chunks
        output_dir: Optional directory to save the vector store

    Returns:
        FAISS vector store

    Raises:
        ValueError: If OpenAI API key is not configured
    """
    settings = get_settings()

    if not settings.openai_api_key:
        raise ValueError(
            "OPENAI_API_KEY not configured. Set it in .env file or environment."
        )

    console.print(f"[cyan]Building vector store with embeddings...[/cyan]")
    console.print(f"  Embedding model: {settings.embedding_model}")
    console.print(f"  Number of chunks: {len(documents)}")

    # Calculate text statistics for logging
    total_chars = sum(len(doc.page_content) for doc in documents)
    estimated_tokens = int(total_chars / 4)  # Rough estimate: 1 token ≈ 4 chars

    # Log embedding call details
    log_embedding_call(
        model=settings.embedding_model,
        num_texts=len(documents),
        total_chars=total_chars,
        estimated_tokens=estimated_tokens,
    )

    # Initialize embeddings
    embeddings_kwargs = {
        "model": settings.embedding_model,
        "openai_api_key": settings.openai_api_key,
    }

    # Add custom base URL if configured
    if settings.openai_base_url:
        embeddings_kwargs["openai_api_base"] = settings.openai_base_url
        console.print(f"  [dim]Using custom API base: {settings.openai_base_url}[/dim]")

    embeddings = OpenAIEmbeddings(**embeddings_kwargs)

    # Build FAISS index with API call tracking
    console.print("  [dim]Generating embeddings (this may take a moment)...[/dim]")

    with APICallLogger(
        api_name="OpenAI Embeddings",
        operation="Generate document embeddings",
        model=settings.embedding_model,
        num_documents=len(documents),
        estimated_tokens=estimated_tokens,
    ) as logger:
        vectorstore = FAISS.from_documents(documents, embeddings)
        logger.log_result(
            vectors_created=len(documents),
            vectorstore_type="FAISS",
        )

    console.print(f"[green]✓[/green] Vector store built with {len(documents)} chunks")

    # Log vectorstore operation
    log_vectorstore_operation(
        operation="BUILD",
        num_documents=len(set(doc.metadata.get("source", "") for doc in documents)),
        num_chunks=len(documents),
        vectorstore_path=output_dir,
    )

    # Save if output directory specified
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        vectorstore.save_local(str(output_path))
        console.print(f"[green]✓[/green] Saved vector store to: {output_dir}")

    return vectorstore


def load_vectorstore(vectorstore_dir: str) -> FAISS:
    """
    Load an existing FAISS vector store from disk.

    Args:
        vectorstore_dir: Directory containing the saved vector store

    Returns:
        Loaded FAISS vector store

    Raises:
        ValueError: If vector store doesn't exist or can't be loaded
    """
    settings = get_settings()

    vectorstore_path = Path(vectorstore_dir)

    if not vectorstore_path.exists():
        raise ValueError(f"Vector store directory does not exist: {vectorstore_dir}")

    # Check for FAISS index file
    index_file = vectorstore_path / "index.faiss"
    if not index_file.exists():
        raise ValueError(f"No FAISS index found in {vectorstore_dir}")

    console.print(f"[cyan]Loading vector store from:[/cyan] {vectorstore_dir}")

    # Initialize embeddings
    embeddings_kwargs = {
        "model": settings.embedding_model,
        "openai_api_key": settings.openai_api_key,
    }

    # Add custom base URL if configured
    if settings.openai_base_url:
        embeddings_kwargs["openai_api_base"] = settings.openai_base_url

    embeddings = OpenAIEmbeddings(**embeddings_kwargs)

    # Load the vector store (no API call, just local loading)
    vectorstore = FAISS.load_local(
        str(vectorstore_path),
        embeddings,
        allow_dangerous_deserialization=True,  # Required for FAISS
    )

    console.print(f"[green]✓[/green] Vector store loaded successfully")

    # Log vectorstore operation
    log_vectorstore_operation(
        operation="LOAD",
        num_documents=0,  # Don't know original doc count
        num_chunks=vectorstore.index.ntotal,
        vectorstore_path=vectorstore_dir,
    )

    return vectorstore


def get_or_create_vectorstore(
    kb_path: str,
    vectorstore_dir: Optional[str] = None,
    force_rebuild: bool = False,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> FAISS:
    """
    Get existing vector store or create a new one from knowledge base.

    This is the main entry point for RAG setup. It will:
    1. Check if a vector store already exists
    2. If not (or force_rebuild=True), load documents and build new store
    3. Return the vector store ready for searching

    Args:
        kb_path: Path to knowledge base directory
        vectorstore_dir: Directory to save/load vector store (uses config default if None)
        force_rebuild: Force rebuild even if vector store exists
        chunk_size: Size of document chunks
        chunk_overlap: Overlap between chunks

    Returns:
        FAISS vector store ready for searching
    """
    settings = get_settings()

    # Use default vector store directory if not specified
    if vectorstore_dir is None:
        vectorstore_dir = str(settings.vectorstore_dir)

    vectorstore_path = Path(vectorstore_dir)

    # Try to load existing vector store
    if not force_rebuild and vectorstore_path.exists():
        index_file = vectorstore_path / "index.faiss"
        if index_file.exists():
            try:
                console.print("[cyan]Existing vector store found, loading...[/cyan]")
                return load_vectorstore(vectorstore_dir)
            except Exception as e:
                console.print(f"[yellow]Warning: Could not load existing vector store: {e}[/yellow]")
                console.print("[yellow]Building new vector store...[/yellow]")

    # Build new vector store
    console.print("[cyan]Building new vector store from knowledge base...[/cyan]")

    # Load documents
    documents = load_documents(kb_path)

    # Split into chunks
    chunks = split_documents(documents, chunk_size, chunk_overlap)

    # Build and save vector store
    vectorstore = build_vectorstore(chunks, vectorstore_dir)

    return vectorstore

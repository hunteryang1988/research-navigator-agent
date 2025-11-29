"""
API call logging utilities for OpenAI API interactions.

Provides verbose logging for embeddings, LLM calls, token usage, and timing.
"""

import time
from typing import Optional, Dict, Any, List
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

# Global verbose flag
_verbose_mode = False


def set_verbose(enabled: bool):
    """Enable or disable verbose logging."""
    global _verbose_mode
    _verbose_mode = enabled


def is_verbose() -> bool:
    """Check if verbose mode is enabled."""
    return _verbose_mode


class APICallLogger:
    """Context manager for logging API calls with timing and details."""

    def __init__(
        self,
        api_name: str,
        operation: str,
        model: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize API call logger.

        Args:
            api_name: Name of the API (e.g., "OpenAI Embeddings", "OpenAI Chat")
            operation: Operation being performed (e.g., "Generate embeddings", "ReAct reasoning")
            model: Model being used
            **kwargs: Additional context to log
        """
        self.api_name = api_name
        self.operation = operation
        self.model = model
        self.context = kwargs
        self.start_time = None
        self.end_time = None
        self.error = None
        self.result_info = {}

    def __enter__(self):
        """Start logging."""
        self.start_time = time.time()

        if _verbose_mode:
            console.print(f"\n[bold cyan]{'='*80}[/bold cyan]")
            console.print(f"[bold cyan]🔌 API CALL START[/bold cyan]")
            console.print(f"[bold cyan]{'='*80}[/bold cyan]")

            table = Table(show_header=False, box=None, padding=(0, 2))
            table.add_column("Key", style="cyan")
            table.add_column("Value", style="white")

            table.add_row("API", self.api_name)
            table.add_row("Operation", self.operation)
            if self.model:
                table.add_row("Model", self.model)
            table.add_row("Time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

            for key, value in self.context.items():
                table.add_row(key.replace("_", " ").title(), str(value))

            console.print(table)
            console.print(f"[dim]Sending request...[/dim]\n")

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """End logging with results."""
        self.end_time = time.time()
        duration = self.end_time - self.start_time

        if exc_type is not None:
            self.error = str(exc_val)

        if _verbose_mode:
            console.print(f"\n[bold cyan]{'='*80}[/bold cyan]")

            if self.error:
                console.print(f"[bold red]❌ API CALL FAILED[/bold red]")
                console.print(f"[red]Error: {self.error}[/red]")
            else:
                console.print(f"[bold green]✅ API CALL SUCCESS[/bold green]")

            console.print(f"[bold cyan]{'='*80}[/bold cyan]")

            # Results table
            table = Table(show_header=False, box=None, padding=(0, 2))
            table.add_column("Key", style="cyan")
            table.add_column("Value", style="white")

            table.add_row("Duration", f"{duration:.2f}s")

            for key, value in self.result_info.items():
                table.add_row(key.replace("_", " ").title(), str(value))

            console.print(table)
            console.print(f"[bold cyan]{'='*80}[/bold cyan]\n")

        return False  # Don't suppress exceptions

    def log_result(self, **kwargs):
        """Log result information (tokens, chunks, etc.)."""
        self.result_info.update(kwargs)


def log_embedding_call(
    model: str,
    num_texts: int,
    total_chars: int,
    estimated_tokens: Optional[int] = None,
):
    """
    Log details about an embedding API call.

    Args:
        model: Embedding model name
        num_texts: Number of texts to embed
        total_chars: Total character count
        estimated_tokens: Estimated token count
    """
    if not _verbose_mode:
        return

    console.print(f"\n[bold yellow]📊 EMBEDDING CALL DETAILS[/bold yellow]")

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Metric", style="yellow")
    table.add_column("Value", style="white")

    table.add_row("Model", model)
    table.add_row("Number of Texts", str(num_texts))
    table.add_row("Total Characters", f"{total_chars:,}")

    if estimated_tokens:
        table.add_row("Estimated Tokens", f"{estimated_tokens:,}")
        # Rough cost estimation for text-embedding-3-small: $0.00002 per 1K tokens
        estimated_cost = (estimated_tokens / 1000) * 0.00002
        table.add_row("Estimated Cost", f"${estimated_cost:.6f}")

    console.print(table)


def log_llm_call(
    model: str,
    prompt: str,
    max_tokens: int,
    temperature: float,
    prompt_length: Optional[int] = None,
):
    """
    Log details about an LLM API call.

    Args:
        model: LLM model name
        prompt: The prompt being sent
        max_tokens: Maximum tokens in response
        temperature: Temperature setting
        prompt_length: Length of prompt in characters
    """
    if not _verbose_mode:
        return

    console.print(f"\n[bold magenta]🤖 LLM CALL DETAILS[/bold magenta]")

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Parameter", style="magenta")
    table.add_column("Value", style="white")

    table.add_row("Model", model)
    table.add_row("Temperature", str(temperature))
    table.add_row("Max Tokens", str(max_tokens))

    if prompt_length:
        table.add_row("Prompt Length", f"{prompt_length:,} chars")

    console.print(table)

    # Show prompt preview
    console.print(f"\n[bold magenta]📝 PROMPT PREVIEW:[/bold magenta]")
    prompt_preview = prompt[:500] + "..." if len(prompt) > 500 else prompt
    console.print(Panel(
        prompt_preview,
        border_style="magenta",
        padding=(1, 2)
    ))


def log_llm_response(
    response_text: str,
    prompt_tokens: Optional[int] = None,
    completion_tokens: Optional[int] = None,
    total_tokens: Optional[int] = None,
):
    """
    Log details about an LLM response.

    Args:
        response_text: The response text
        prompt_tokens: Number of tokens in prompt
        completion_tokens: Number of tokens in completion
        total_tokens: Total tokens used
    """
    if not _verbose_mode:
        return

    console.print(f"\n[bold green]💬 LLM RESPONSE:[/bold green]")

    # Show response preview
    response_preview = response_text[:500] + "..." if len(response_text) > 500 else response_text
    console.print(Panel(
        response_preview,
        border_style="green",
        padding=(1, 2)
    ))

    # Token usage
    if total_tokens:
        console.print(f"\n[bold green]📊 TOKEN USAGE:[/bold green]")

        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Type", style="green")
        table.add_column("Count", style="white")

        if prompt_tokens:
            table.add_row("Prompt Tokens", f"{prompt_tokens:,}")
        if completion_tokens:
            table.add_row("Completion Tokens", f"{completion_tokens:,}")
        table.add_row("Total Tokens", f"{total_tokens:,}")

        console.print(table)


def log_vectorstore_operation(
    operation: str,
    num_documents: int,
    num_chunks: int,
    vectorstore_path: Optional[str] = None,
):
    """
    Log vector store operations.

    Args:
        operation: Operation type (build, load, save)
        num_documents: Number of documents
        num_chunks: Number of chunks
        vectorstore_path: Path to vector store
    """
    if not _verbose_mode:
        return

    console.print(f"\n[bold blue]💾 VECTORSTORE OPERATION[/bold blue]")

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Item", style="blue")
    table.add_column("Value", style="white")

    table.add_row("Operation", operation)
    table.add_row("Documents", str(num_documents))
    table.add_row("Chunks", str(num_chunks))

    if vectorstore_path:
        table.add_row("Path", vectorstore_path)

    console.print(table)


def log_search_query(
    query: str,
    top_k: int,
    vectorstore_size: int,
):
    """
    Log vector search query details.

    Args:
        query: Search query
        top_k: Number of results to retrieve
        vectorstore_size: Total number of vectors in store
    """
    if not _verbose_mode:
        return

    console.print(f"\n[bold cyan]🔍 VECTOR SEARCH QUERY[/bold cyan]")

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Query", query[:100] + "..." if len(query) > 100 else query)
    table.add_row("Top K", str(top_k))
    table.add_row("Vectorstore Size", f"{vectorstore_size:,} vectors")

    console.print(table)


def log_search_results(
    results: List[str],
    scores: Optional[List[float]] = None,
):
    """
    Log vector search results.

    Args:
        results: List of retrieved chunks
        scores: Optional similarity scores
    """
    if not _verbose_mode:
        return

    console.print(f"\n[bold green]📋 SEARCH RESULTS:[/bold green]")
    console.print(f"Found {len(results)} results\n")

    for i, result in enumerate(results[:3], 1):  # Show top 3
        preview = result[:200] + "..." if len(result) > 200 else result
        score_info = f" (score: {scores[i-1]:.4f})" if scores and i-1 < len(scores) else ""
        console.print(f"[cyan]Result {i}{score_info}:[/cyan]")
        console.print(f"[dim]{preview}[/dim]\n")

    if len(results) > 3:
        console.print(f"[dim]... and {len(results) - 3} more results[/dim]\n")


def log_web_search_query(
    query: str,
    max_results: int,
    search_depth: str = "basic",
):
    """
    Log web search query details.

    Args:
        query: Search query
        max_results: Number of results requested
        search_depth: Search depth setting
    """
    if not _verbose_mode:
        return

    console.print(f"\n[bold blue]🌐 WEB SEARCH QUERY[/bold blue]")

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Parameter", style="blue")
    table.add_column("Value", style="white")

    table.add_row("Query", query[:100] + "..." if len(query) > 100 else query)
    table.add_row("Max Results", str(max_results))
    table.add_row("Search Depth", search_depth)

    console.print(table)


def log_web_search_results(
    results: List[Dict[str, Any]],
):
    """
    Log web search results.

    Args:
        results: List of web search results with title, url, content
    """
    if not _verbose_mode:
        return

    console.print(f"\n[bold green]🌍 WEB SEARCH RESULTS:[/bold green]")
    console.print(f"Found {len(results)} results\n")

    for i, result in enumerate(results[:3], 1):  # Show top 3
        title = result.get("title", "Untitled")
        url = result.get("url", "")
        content = result.get("content", "")
        score = result.get("score")

        preview = content[:200] + "..." if len(content) > 200 else content
        score_info = f" (score: {score:.4f})" if score else ""

        console.print(f"[blue]Result {i}{score_info}:[/blue]")
        console.print(f"[bold]{title}[/bold]")
        console.print(f"[dim]{url}[/dim]")
        console.print(f"{preview}\n")

    if len(results) > 3:
        console.print(f"[dim]... and {len(results) - 3} more results[/dim]\n")

"""
Tavily web search tool for external information retrieval.

Provides real-time web search capabilities using the Tavily API.
"""

from typing import List, Dict, Any, Optional
from rich.console import Console

from src.config.settings import get_settings
from src.tools.api_logger import (
    APICallLogger,
    log_web_search_query,
    log_web_search_results,
)

console = Console()


def web_search(
    query: str,
    max_results: int = 5,
    search_depth: str = "basic",
    include_domains: Optional[List[str]] = None,
    exclude_domains: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Perform web search using Tavily API.

    Args:
        query: The search query
        max_results: Maximum number of results to return (default: 5)
        search_depth: Search depth - "basic" or "advanced" (default: "basic")
        include_domains: Optional list of domains to include
        exclude_domains: Optional list of domains to exclude

    Returns:
        List of search results, each containing:
            - title: Page title
            - url: Page URL
            - content: Content snippet/summary
            - score: Relevance score (if available)
            - published_date: Publication date (if available)

    Raises:
        ValueError: If Tavily API key is not configured
        Exception: If API call fails
    """
    settings = get_settings()

    if not settings.tavily_api_key:
        raise ValueError(
            "TAVILY_API_KEY not configured. Set it in .env file or environment."
        )

    console.print(f"[bold blue]🌐 External Web Search[/bold blue]")
    console.print(f"  Query: {query}")
    console.print(f"  Max results: {max_results}")

    # Log search query details
    log_web_search_query(
        query=query,
        max_results=max_results,
        search_depth=search_depth,
    )

    try:
        # Import tavily here to avoid import errors if not installed
        from tavily import TavilyClient

        # Initialize Tavily client
        client = TavilyClient(api_key=settings.tavily_api_key)

        # Prepare search parameters
        search_params = {
            "query": query,
            "max_results": max_results,
            "search_depth": search_depth,
        }

        if include_domains:
            search_params["include_domains"] = include_domains
        if exclude_domains:
            search_params["exclude_domains"] = exclude_domains

        # Perform search with API call tracking
        with APICallLogger(
            api_name="Tavily Search",
            operation="Web search",
            query=query,
            max_results=max_results,
            search_depth=search_depth,
        ) as logger:
            response = client.search(**search_params)

            # Extract results
            results = []
            raw_results = response.get("results", [])

            for result in raw_results:
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "content": result.get("content", ""),
                    "score": result.get("score"),
                    "published_date": result.get("published_date"),
                })

            logger.log_result(
                results_found=len(results),
                total_sources=len(raw_results),
            )

        console.print(f"[green]✓[/green] Found {len(results)} web results")

        # Log search results
        log_web_search_results(results)

        # Log preview of first result
        if results:
            preview = results[0]["content"][:100] + "..." if len(results[0]["content"]) > 100 else results[0]["content"]
            console.print(f"  [dim]First result: {results[0]['title']}[/dim]")
            console.print(f"  [dim]{preview}[/dim]")

        return results

    except ImportError:
        error_msg = "tavily-python package not installed. Install with: pip install tavily-python"
        console.print(f"[red]✗ {error_msg}[/red]")
        raise ImportError(error_msg)

    except Exception as e:
        console.print(f"[red]✗ Error during web search: {e}[/red]")
        raise


def web_search_simple(query: str, max_results: int = 5) -> List[str]:
    """
    Simplified web search that returns only content strings.

    Convenience wrapper around web_search() that returns just the content
    as a list of strings, similar to RAG search output format.

    Args:
        query: The search query
        max_results: Maximum number of results

    Returns:
        List of content strings from search results
    """
    results = web_search(query, max_results)
    return [result["content"] for result in results if result.get("content")]


def web_search_with_context(
    query: str,
    max_results: int = 5,
    context: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Perform web search with optional context for better results.

    Args:
        query: The search query
        max_results: Maximum number of results
        context: Optional context to improve search relevance

    Returns:
        List of search results
    """
    # If context provided, prepend to query for better results
    enhanced_query = query
    if context:
        enhanced_query = f"{context} {query}"
        console.print(f"  [dim]Enhanced query with context[/dim]")

    return web_search(enhanced_query, max_results)


def validate_tavily_config() -> tuple[bool, Optional[str]]:
    """
    Validate Tavily API configuration.

    Returns:
        Tuple of (is_valid, error_message)
    """
    settings = get_settings()

    if not settings.tavily_api_key:
        return False, "TAVILY_API_KEY not set in .env file"

    # Try a simple test search
    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=settings.tavily_api_key)

        # Perform minimal test search
        response = client.search(query="test", max_results=1)

        if "results" in response:
            return True, None
        else:
            return False, "Unexpected response format from Tavily API"

    except ImportError:
        return False, "tavily-python package not installed"
    except Exception as e:
        return False, f"Tavily API error: {str(e)}"


def get_tavily_info() -> Dict[str, Any]:
    """
    Get information about current Tavily configuration.

    Returns:
        Dictionary with configuration info
    """
    settings = get_settings()

    info = {
        "api_key_configured": bool(settings.tavily_api_key),
        "api_key_length": len(settings.tavily_api_key) if settings.tavily_api_key else 0,
    }

    # Test connection if key is configured
    if info["api_key_configured"]:
        is_valid, error = validate_tavily_config()
        info["connection_valid"] = is_valid
        info["error"] = error
    else:
        info["connection_valid"] = False
        info["error"] = "API key not configured"

    return info

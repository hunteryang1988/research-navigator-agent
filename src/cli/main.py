"""
CLI entrypoint for the Research Navigator Agent.

Provides command-line interface using Typer.
"""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from src.config.settings import get_settings
from src.agent.controller import run_agent
from src.tools.api_logger import set_verbose

app = typer.Typer(
    name="research-nav",
    help="Research Navigator Agent - AI-powered research with internal RAG and web search",
    add_completion=False,
)

console = Console()


@app.command()
def main(
    query: str = typer.Argument(
        ...,
        help="The research question to investigate"
    ),
    kb: Optional[Path] = typer.Option(
        None,
        "--kb",
        help="Path to knowledge base directory for internal RAG search"
    ),
    max_steps: int = typer.Option(
        10,
        "--max-steps",
        help="Maximum number of reasoning steps before forcing completion"
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Path to save the research brief (markdown format)"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging for API calls (embeddings, LLM, timing)"
    ),
    check_config: bool = typer.Option(
        False,
        "--check-config",
        help="Validate configuration and API keys before running"
    ),
):
    """
    Run the research navigator agent on a query.

    Examples:

        research-nav main "What is quantum computing?"

        research-nav main "Compare quantum and classical computing" --kb ./knowledge

        research-nav main "Latest AI developments" --max-steps 8 --output report.md

        research-nav main "Quantum vs Classical" --kb ./knowledge --verbose
    """
    # Load settings
    settings = get_settings()

    # Enable verbose logging if requested
    if verbose:
        set_verbose(True)
        console.print("[bold yellow]📊 Verbose logging enabled[/bold yellow]")
        console.print("[dim]All API calls will show detailed timing, token usage, and request/response data[/dim]\n")

    # Check configuration if requested
    if check_config:
        console.print("[bold]Configuration Check:[/bold]")
        console.print(f"  OpenAI Model: {settings.llm_model}")
        console.print(f"  Embedding Model: {settings.embedding_model}")
        console.print(f"  Vector Store: {settings.vectorstore_dir}")
        console.print(f"  Max Steps: {settings.max_steps}")

        valid, missing = settings.validate_api_keys()
        if not valid:
            console.print(f"\n[bold red]Missing API Keys:[/bold red]")
            for key in missing:
                console.print(f"  - {key}")
            console.print(f"\n[yellow]Set these in your .env file or environment[/yellow]")
            sys.exit(1)
        else:
            console.print(f"\n[green]✓ All API keys configured[/green]")
            return

    # Validate KB path if provided
    if kb and not kb.exists():
        console.print(f"[red]Error: Knowledge base path does not exist: {kb}[/red]")
        sys.exit(1)

    # Run the agent
    try:
        final_state = run_agent(
            query=query,
            kb_path=str(kb) if kb else None,
            max_steps=max_steps,
            output_file=str(output) if output else None,
        )

        # Exit successfully
        sys.exit(0)

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(130)

    except Exception as e:
        console.print(f"\n[bold red]Fatal error:[/bold red] {str(e)}")
        if "--debug" in sys.argv:
            raise
        sys.exit(1)


@app.command()
def config():
    """
    Display current configuration settings.
    """
    settings = get_settings()

    console.print("[bold cyan]Research Navigator Configuration[/bold cyan]\n")

    console.print("[bold]API Configuration:[/bold]")
    console.print(f"  OpenAI API Key: {'✓ Set' if settings.openai_api_key else '✗ Not set'}")
    if settings.openai_base_url:
        console.print(f"  OpenAI Base URL: {settings.openai_base_url}")
    console.print(f"  Tavily API Key: {'✓ Set' if settings.tavily_api_key else '✗ Not set'}")

    console.print("\n[bold]LLM Configuration:[/bold]")
    console.print(f"  Model: {settings.llm_model}")
    console.print(f"  Temperature: {settings.llm_temperature}")
    console.print(f"  Max Tokens: {settings.llm_max_tokens}")

    console.print("\n[bold]Embedding Configuration:[/bold]")
    console.print(f"  Model: {settings.embedding_model}")
    console.print(f"  Dimension: {settings.embedding_dimension}")

    console.print("\n[bold]Agent Configuration:[/bold]")
    console.print(f"  Default Max Steps: {settings.max_steps}")
    console.print(f"  Top K Results: {settings.top_k_results}")

    console.print("\n[bold]Storage:[/bold]")
    console.print(f"  Vector Store: {settings.vectorstore_dir}")
    console.print(f"  Type: {settings.vectorstore_type}")

    # Validate API keys
    valid, missing = settings.validate_api_keys()
    if not valid:
        console.print(f"\n[bold yellow]⚠️  Missing API Keys:[/bold yellow]")
        for key in missing:
            console.print(f"  - {key}")
        console.print(f"\n[dim]Add these to your .env file or set as environment variables[/dim]")
    else:
        console.print(f"\n[bold green]✓ Configuration is valid[/bold green]")


@app.command()
def version():
    """
    Display version information.
    """
    console.print("[bold cyan]Research Navigator Agent[/bold cyan]")
    console.print("Version: 0.1.0 (Phase 3 - RAG + Web Search)")
    console.print("Framework: LangGraph + LangChain")
    console.print("LLM: OpenAI gpt-5-mini")
    console.print("Search: Internal (FAISS) + External (Tavily)")


if __name__ == "__main__":
    app()

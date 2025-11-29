"""
Agent controller for running the research agent.

Provides high-level functions to initialize and execute the agent graph.
"""

from typing import Optional
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from .schema import create_initial_state, AgentState
from .graph import create_research_graph

console = Console()


def run_agent(
    query: str,
    kb_path: Optional[str] = None,
    max_steps: int = 10,
    output_file: Optional[str] = None,
) -> AgentState:
    """
    Run the research agent on a query.

    Args:
        query: The research question to answer
        kb_path: Optional path to knowledge base directory for RAG
        max_steps: Maximum number of reasoning steps
        output_file: Optional path to save the final report

    Returns:
        Final AgentState with results
    """
    console.print(Panel.fit(
        f"[bold]Research Navigator Agent[/bold]\n"
        f"Query: {query}\n"
        f"Max Steps: {max_steps}\n"
        f"KB Path: {kb_path or 'None'}\n"
        f"Mode: [green]Phase 4 - Full ReAct Loop (LLM Reasoning + Synthesis)[/green]",
        border_style="cyan"
    ))

    # Create initial state
    console.print("\n[bold]Initializing agent state...[/bold]")
    state = create_initial_state(query=query, max_steps=max_steps, kb_path=kb_path)

    # Create and run the graph
    console.print("[bold]Building research graph...[/bold]")
    graph = create_research_graph()

    console.print("[bold]Executing research pipeline...[/bold]\n")
    try:
        # Run the graph
        final_state = graph.invoke(state)

        # Display the final answer
        console.print("\n" + "=" * 80 + "\n")
        if final_state.get("final_answer"):
            console.print(Panel(
                Markdown(final_state["final_answer"]),
                title="[bold green]Research Brief[/bold green]",
                border_style="green"
            ))

            # Save to file if requested
            if output_file:
                output_path = Path(output_file)
                output_path.write_text(final_state["final_answer"])
                console.print(f"\n[green]✓[/green] Saved research brief to: {output_file}")

        # Display summary
        console.print(f"\n[bold]Execution Summary:[/bold]")
        console.print(f"  Steps taken: {final_state['step']}")
        console.print(f"  Tool calls: {len(final_state['tool_calls'])}")
        console.print(f"  Internal sources: {len(final_state['internal_context'])}")
        console.print(f"  External sources: {len(final_state['external_context'])}")

        return final_state

    except Exception as e:
        console.print(f"\n[bold red]Error during agent execution:[/bold red]")
        console.print(f"[red]{str(e)}[/red]")
        raise


def visualize_graph(output_path: str = "graph.png"):
    """
    Generate a visualization of the agent graph.

    Args:
        output_path: Path to save the graph visualization
    """
    try:
        graph = create_research_graph()
        # Note: Graph visualization requires additional dependencies
        # This is a placeholder for future implementation
        console.print(f"[yellow]Graph visualization not yet implemented[/yellow]")
        console.print(f"[dim]Will save to: {output_path}[/dim]")
    except Exception as e:
        console.print(f"[red]Error generating graph visualization: {e}[/red]")

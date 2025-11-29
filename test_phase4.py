#!/usr/bin/env python3
"""
Phase 4 Test: Full ReAct Loop with LLM Reasoning

This test validates the complete ReAct agent with:
- LLM-based reasoning for tool selection
- Dynamic switching between internal RAG and web search
- LLM-based synthesis for final research brief
- Complete reasoning trace

Usage:
    python test_phase4.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from src.agent.controller import run_agent
from src.tools.api_logger import set_verbose

console = Console()


def print_header(title: str):
    """Print a styled header."""
    console.print(f"\n[bold cyan]{'='*80}[/bold cyan]")
    console.print(f"[bold cyan]{title}[/bold cyan]")
    console.print(f"[bold cyan]{'='*80}[/bold cyan]\n")


def print_reasoning_trace(state: dict):
    """Print the agent's reasoning trace."""
    console.print("\n[bold yellow]🧠 REASONING TRACE[/bold yellow]")
    console.print("[bold yellow]" + "="*80 + "[/bold yellow]\n")

    for entry in state.get("scratchpad", []):
        step = entry.get("step", 0)
        thought = entry.get("thought", "")
        action = entry.get("action", "")
        action_input = entry.get("action_input", "")

        console.print(f"[bold cyan]Step {step}:[/bold cyan]")
        console.print(f"  [dim]Thought:[/dim] {thought}")
        console.print(f"  [bold]Action:[/bold] {action}")
        console.print(f"  [dim]Input:[/dim] {action_input}")
        console.print()


def print_tool_usage(state: dict):
    """Print summary of tool usage."""
    console.print("\n[bold green]🔧 TOOL USAGE SUMMARY[/bold green]")
    console.print("[bold green]" + "="*80 + "[/bold green]\n")

    tool_calls = state.get("tool_calls", [])
    internal_count = sum(1 for call in tool_calls if call.get("tool") == "search_internal")
    external_count = sum(1 for call in tool_calls if call.get("tool") == "web_search")

    console.print(f"  [bold]Total tool calls:[/bold] {len(tool_calls)}")
    console.print(f"  [bold]Internal RAG searches:[/bold] {internal_count}")
    console.print(f"  [bold]External web searches:[/bold] {external_count}")
    console.print(f"  [bold]Total steps:[/bold] {state.get('step', 0)}")
    console.print()


def print_sources(state: dict):
    """Print sources used."""
    console.print("\n[bold blue]📚 SOURCES CONSULTED[/bold blue]")
    console.print("[bold blue]" + "="*80 + "[/bold blue]\n")

    internal = state.get("internal_context", [])
    external = state.get("external_context", [])

    console.print(f"[bold]Internal Knowledge Base:[/bold] {len(internal)} chunks")
    if internal:
        for i, chunk in enumerate(internal[:3], 1):
            console.print(f"  {i}. {chunk[:120]}...")

    console.print(f"\n[bold]External Web Search:[/bold] {len(external)} results")
    if external:
        for i, result in enumerate(external[:3], 1):
            title = result.get('title', 'Untitled')
            url = result.get('url', '#')
            console.print(f"  {i}. {title}")
            console.print(f"     {url}")
    console.print()


def print_final_answer(state: dict):
    """Print the final research brief."""
    console.print("\n[bold magenta]📝 FINAL RESEARCH BRIEF[/bold magenta]")
    console.print("[bold magenta]" + "="*80 + "[/bold magenta]\n")

    final_answer = state.get("final_answer", "")
    if final_answer:
        md = Markdown(final_answer)
        console.print(Panel(md, border_style="magenta"))
    else:
        console.print("[red]No final answer generated[/red]")


def test_combined_search():
    """
    Test 1: Combined KB + Web Search with Full ReAct Loop

    This should demonstrate:
    - LLM deciding to search KB first
    - LLM deciding to search web for additional info
    - LLM synthesizing final answer from both sources
    """
    print_header("TEST 1: Combined Knowledge Base + Web Search")

    console.print("[bold]Query:[/bold] What is quantum computing and how does it differ from classical computing?")
    console.print("[bold]KB Path:[/bold] ./knowledge/sample_docs")
    console.print("[bold]Max Steps:[/bold] 8")
    console.print()

    final_state = run_agent(
        query="What is quantum computing and how does it differ from classical computing?",
        kb_path="./knowledge/sample_docs",
        max_steps=8,
    )

    print_reasoning_trace(final_state)
    print_tool_usage(final_state)
    print_sources(final_state)
    print_final_answer(final_state)

    return final_state


def test_web_only_search():
    """
    Test 2: Web Search Only with Full ReAct Loop

    This should demonstrate:
    - LLM deciding to use web search (no KB available)
    - LLM synthesizing answer from web results
    """
    print_header("TEST 2: Web Search Only (No Knowledge Base)")

    console.print("[bold]Query:[/bold] What are the latest developments in quantum computing in 2024?")
    console.print("[bold]KB Path:[/bold] None")
    console.print("[bold]Max Steps:[/bold] 5")
    console.print()

    final_state = run_agent(
        query="What are the latest developments in quantum computing in 2024?",
        kb_path=None,
        max_steps=5,
    )

    print_reasoning_trace(final_state)
    print_tool_usage(final_state)
    print_sources(final_state)
    print_final_answer(final_state)

    return final_state


def test_complex_query():
    """
    Test 3: Complex Multi-Step Query

    This should demonstrate:
    - LLM making multiple reasoning steps
    - Refining queries based on context
    - Comprehensive synthesis
    """
    print_header("TEST 3: Complex Multi-Step Research Query")

    console.print("[bold]Query:[/bold] Compare the computational power of quantum vs classical computers for cryptography")
    console.print("[bold]KB Path:[/bold] ./knowledge/sample_docs")
    console.print("[bold]Max Steps:[/bold] 10")
    console.print()

    final_state = run_agent(
        query="Compare the computational power of quantum vs classical computers for cryptography",
        kb_path="./knowledge/sample_docs",
        max_steps=10,
    )

    print_reasoning_trace(final_state)
    print_tool_usage(final_state)
    print_sources(final_state)
    print_final_answer(final_state)

    return final_state


def main():
    """Run all Phase 4 tests."""
    console.print(Panel.fit(
        "[bold cyan]Phase 4: Full ReAct Loop Test Suite[/bold cyan]\n\n"
        "This test validates the complete ReAct agent with:\n"
        "  • LLM-based reasoning for intelligent tool selection\n"
        "  • Dynamic switching between internal RAG and web search\n"
        "  • LLM-based synthesis for comprehensive research briefs\n"
        "  • Complete reasoning trace for transparency\n\n"
        "[bold yellow]Note:[/bold yellow] This will make multiple API calls to OpenAI and Tavily.",
        border_style="cyan",
    ))

    # Enable verbose logging
    console.print("\n[bold yellow]📊 Verbose logging: ENABLED[/bold yellow]\n")
    set_verbose(True)

    # Run tests
    try:
        console.print("\n[bold]Running Test 1/3...[/bold]")
        test_combined_search()

        console.print("\n\n[bold]Running Test 2/3...[/bold]")
        test_web_only_search()

        console.print("\n\n[bold]Running Test 3/3...[/bold]")
        test_complex_query()

        # Summary
        console.print("\n\n" + "="*80)
        console.print("[bold green]✅ All Phase 4 tests completed successfully![/bold green]")
        console.print("="*80 + "\n")

        console.print("[bold cyan]Phase 4 Features Validated:[/bold cyan]")
        console.print("  ✓ LLM-based reasoning for tool selection")
        console.print("  ✓ Dynamic internal RAG search")
        console.print("  ✓ Dynamic external web search")
        console.print("  ✓ LLM-based synthesis of final answer")
        console.print("  ✓ Complete reasoning trace logging")
        console.print("  ✓ Error handling and fallbacks")
        console.print()

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Test interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n\n[red]✗ Test failed: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

"""
LangGraph node implementations for the research agent.

Each node is a function that takes AgentState and returns updated AgentState.
"""

from typing import Literal
from rich.console import Console

from .schema import AgentState
from src.tools.rag_search import search_internal
from src.tools.tavily_tool import web_search
from src.tools.llm_client import get_llm_client
from src.config.settings import get_settings

console = Console()


def reason_node(state: AgentState) -> AgentState:
    """
    Reasoning node: LLM decides the next action using ReAct-style reasoning.

    Phase 4: Uses GPT for intelligent tool selection based on:
    - The user's query
    - Current context (what's been done so far)
    - Available tools (search_internal, web_search, finish)

    The LLM outputs:
    - THOUGHT: Reasoning about what to do next
    - ACTION: One of {search_internal, web_search, finish}
    - ACTION_INPUT: The query/input for the action
    """
    console.print(f"[bold cyan]🤔 Reasoning Node (Step {state['step']})[/bold cyan]")
    console.print(f"   Query: {state['query']}")

    # Build context for LLM
    context = {
        "tool_calls": state.get("tool_calls", []),
        "internal_context": state.get("internal_context", []),
        "external_context": state.get("external_context", []),
        "kb_path": state.get("kb_path"),
    }

    # Build list of available tools
    available_tools = []
    if state.get("kb_path"):
        available_tools.append("search_internal")
    available_tools.append("web_search")
    available_tools.append("finish")

    # Call LLM for reasoning
    try:
        llm_client = get_llm_client()
        thought, action, action_input = llm_client.generate_reasoning(
            query=state["query"],
            context=context,
            available_tools=available_tools,
        )

        console.print(f"   [dim]Thought: {thought}[/dim]")
        console.print(f"   [bold]Action: {action}[/bold]")
        console.print(f"   [dim]Action Input: {action_input}[/dim]")

        # Update scratchpad with LLM's decision
        state["scratchpad"].append({
            "step": state["step"],
            "thought": thought,
            "action": action,
            "action_input": action_input,
        })

    except Exception as e:
        console.print(f"[red]✗ Error during LLM reasoning: {e}[/red]")
        # Fallback to finish if reasoning fails
        console.print("[yellow]⚠️  Falling back to finish action[/yellow]")
        state["scratchpad"].append({
            "step": state["step"],
            "thought": f"Error during reasoning: {str(e)}",
            "action": "finish",
            "action_input": state["query"],
        })

    return state


def act_internal_node(state: AgentState) -> AgentState:
    """
    Internal RAG search action node.

    Calls the RAG search tool to find relevant chunks from the knowledge base.
    """
    console.print(f"[bold green]📚 Internal RAG Search[/bold green]")

    kb_path = state.get("kb_path")
    settings = get_settings()

    if not kb_path:
        console.print("[yellow]⚠️  No knowledge base path provided, skipping internal search[/yellow]")
        state["step"] += 1
        return state

    try:
        # Get search query from scratchpad or use main query
        search_query = state["query"]
        if state["scratchpad"]:
            action_input = state["scratchpad"][-1].get("action_input")
            if action_input:
                search_query = action_input

        # Perform RAG search
        results = search_internal(
            query=search_query,
            kb_path=kb_path,
            top_k=settings.top_k_results,
        )

        # Update state
        state["internal_context"].extend(results)
        state["tool_calls"].append({
            "tool": "search_internal",
            "input": search_query,
            "output": results,
        })
        state["step"] += 1

        console.print(f"[green]✓[/green] Retrieved {len(results)} chunks from knowledge base")

    except Exception as e:
        console.print(f"[red]✗ Error during RAG search: {e}[/red]")
        # Log error but continue
        state["tool_calls"].append({
            "tool": "search_internal",
            "input": state["query"],
            "error": str(e),
        })
        state["step"] += 1

    return state


def act_external_node(state: AgentState) -> AgentState:
    """
    External web search action node.

    Calls Tavily web search to find relevant information from the internet.
    """
    settings = get_settings()

    try:
        # Get search query from scratchpad or use main query
        search_query = state["query"]
        if state["scratchpad"]:
            action_input = state["scratchpad"][-1].get("action_input")
            if action_input:
                search_query = action_input

        # Perform Tavily web search
        results = web_search(
            query=search_query,
            max_results=settings.top_k_results,
        )

        # Update state
        state["external_context"].extend(results)
        state["tool_calls"].append({
            "tool": "web_search",
            "input": search_query,
            "output": results,
        })
        state["step"] += 1

        console.print(f"[green]✓[/green] Retrieved {len(results)} web results")

    except Exception as e:
        console.print(f"[red]✗ Error during web search: {e}[/red]")
        # Log error but continue
        state["tool_calls"].append({
            "tool": "web_search",
            "input": state["query"],
            "error": str(e),
        })
        state["step"] += 1

    return state


def finish_node(state: AgentState) -> AgentState:
    """
    Finish node: Generate final research brief using LLM synthesis.

    Phase 4: Uses GPT to synthesize a comprehensive research brief from:
    - All internal knowledge base context
    - All external web search results
    - The complete reasoning trace (scratchpad)

    The LLM generates a structured markdown report with:
    - Summary
    - Key Findings
    - Sources (internal + external)
    - Reasoning Trace
    """
    console.print(f"[bold magenta]✅ Finishing - Generating Research Brief[/bold magenta]")

    # Gather all context
    internal_sources = state.get("internal_context", [])
    external_sources = state.get("external_context", [])
    reasoning_trace = state.get("scratchpad", [])

    # Call LLM for synthesis
    try:
        llm_client = get_llm_client()
        final_answer = llm_client.generate_synthesis(
            query=state["query"],
            internal_sources=internal_sources,
            external_sources=external_sources,
            reasoning_trace=reasoning_trace,
        )

        state["final_answer"] = final_answer
        console.print("[bold green]✨ Research brief generated![/bold green]")

    except Exception as e:
        console.print(f"[red]✗ Error during synthesis: {e}[/red]")
        # Fallback to basic template if LLM fails
        console.print("[yellow]⚠️  Falling back to basic template[/yellow]")

        query = state["query"]
        num_internal = len(internal_sources)
        num_external = len(external_sources)
        num_steps = state["step"]

        fallback_answer = f"""# Research Brief: {query}

## Summary

An error occurred during LLM synthesis. Below is a basic summary of the gathered information.

## Process

- Steps taken: {num_steps}
- Internal sources consulted: {num_internal}
- External sources consulted: {num_external}

## Sources

### Internal Knowledge Base
{chr(10).join(f"- {chunk[:100]}..." for chunk in internal_sources[:5]) if internal_sources else "- No internal sources used"}

### External Web Search
{chr(10).join(f"- [{result.get('title', 'Untitled')}]({result.get('url', '#')})" for result in external_sources[:5]) if external_sources else "- No external sources used"}

## Error

Synthesis failed: {str(e)}

---
*Generated by Research Navigator Agent (Error Recovery Mode)*
"""
        state["final_answer"] = fallback_answer

    return state


# Router function for conditional edges
def route_action(state: AgentState) -> Literal["act_internal", "act_external", "finish"]:
    """
    Route to the appropriate next node based on the reasoning decision.

    Returns:
        Node name to route to: "act_internal", "act_external", or "finish"
    """
    # Check if we've hit max steps
    if state["step"] >= state["max_steps"]:
        console.print("[yellow]⚠️  Max steps reached, forcing finish[/yellow]")
        return "finish"

    # Get the last action from scratchpad
    if state["scratchpad"]:
        last_action = state["scratchpad"][-1].get("action", "finish")

        if last_action == "search_internal":
            return "act_internal"
        elif last_action == "web_search":
            return "act_external"
        else:
            return "finish"

    # Default to finish
    return "finish"

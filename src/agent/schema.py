"""
Agent state schema for LangGraph.

Defines the AgentState TypedDict that flows through the graph nodes.
"""

from typing import TypedDict, List, Dict, Any, Optional


class AgentState(TypedDict):
    """
    State object that flows through the LangGraph state machine.

    Attributes:
        query: The original user research query
        kb_path: Optional path to knowledge base for RAG search
        history: Optional conversation history
        scratchpad: List of reasoning steps (thought/action/observation)
        tool_calls: Record of all tool invocations with results
        internal_context: Results from internal RAG search
        external_context: Results from external web search
        step: Current step counter
        max_steps: Maximum allowed steps before forcing finish
        final_answer: The generated research brief
    """
    query: str
    kb_path: Optional[str]
    history: Optional[List[str]]
    scratchpad: List[Dict[str, Any]]
    tool_calls: List[Dict[str, Any]]
    internal_context: List[str]
    external_context: List[Dict[str, Any]]
    step: int
    max_steps: int
    final_answer: Optional[str]


def create_initial_state(
    query: str,
    max_steps: int = 10,
    kb_path: Optional[str] = None,
) -> AgentState:
    """
    Create an initial state for a new agent run.

    Args:
        query: User's research question
        max_steps: Maximum number of reasoning steps
        kb_path: Optional path to knowledge base directory

    Returns:
        Initialized AgentState
    """
    return AgentState(
        query=query,
        kb_path=kb_path,
        history=None,
        scratchpad=[],
        tool_calls=[],
        internal_context=[],
        external_context=[],
        step=0,
        max_steps=max_steps,
        final_answer=None,
    )

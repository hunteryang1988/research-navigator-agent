"""
LangGraph state machine construction for the research agent.

Defines the graph structure:
    START -> reason_node -> [act_internal | act_external | finish] -> END
                              ↓              ↓
                              └──────────────┴─────> (loop back to reason)
"""

from langgraph.graph import StateGraph, END

from .schema import AgentState
from .nodes import (
    reason_node,
    act_internal_node,
    act_external_node,
    finish_node,
    route_action,
)


def create_research_graph() -> StateGraph:
    """
    Create and compile the research agent graph.

    Returns:
        Compiled LangGraph StateGraph ready for execution
    """
    # Initialize the state graph
    graph = StateGraph(AgentState)

    # Add all nodes
    graph.add_node("reason", reason_node)
    graph.add_node("act_internal", act_internal_node)
    graph.add_node("act_external", act_external_node)
    graph.add_node("finish", finish_node)

    # Set entry point
    graph.set_entry_point("reason")

    # Add conditional edges from reason node
    graph.add_conditional_edges(
        "reason",
        route_action,
        {
            "act_internal": "act_internal",
            "act_external": "act_external",
            "finish": "finish",
        },
    )

    # Add edges back to reason node for continued reasoning
    graph.add_edge("act_internal", "reason")
    graph.add_edge("act_external", "reason")

    # Finish node goes to END
    graph.add_edge("finish", END)

    # Compile the graph
    return graph.compile()

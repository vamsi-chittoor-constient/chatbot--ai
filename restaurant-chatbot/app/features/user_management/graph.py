"""
User Management Feature Graph
=============================
LangGraph orchestration for user_management sub-agents.

Routing:
- authenticate → authenticator
- manage_sessions → session_manager
- migrate_identity → identity_migrator
- update_identity → identity_manager
"""

from typing import Dict, Any
from langgraph.graph import StateGraph, END
import structlog

from app.features.user_management.state import AuthenticationState
from app.features.user_management.agents import (
    authenticator_agent,
    session_manager_agent,
    identity_migrator_agent,
    identity_manager_agent
)

logger = structlog.get_logger("user_management.graph")


def route_to_agent(classification: Dict[str, Any]) -> str:
    """Route to appropriate sub-agent based on classification."""
    sub_intent = classification.get("sub_intent")

    routing_map = {
        "authenticate": "authenticator",
        "manage_sessions": "session_manager",
        "migrate_identity": "identity_migrator",
        "update_identity": "identity_manager"
    }

    agent_name = routing_map.get(sub_intent, "authenticator")  # Default to authenticator

    logger.info(
        "Routing to agent",
        sub_intent=sub_intent,
        agent=agent_name
    )

    return agent_name


def create_user_management_graph() -> StateGraph:
    """Create the user_management feature graph."""

    graph = StateGraph(AuthenticationState)

    # Add nodes
    graph.add_node("authenticator", authenticator_agent)
    graph.add_node("session_manager", session_manager_agent)
    graph.add_node("identity_migrator", identity_migrator_agent)
    graph.add_node("identity_manager", identity_manager_agent)

    # Set entry point
    graph.set_entry_point("authenticator")  # Default entry

    # All agents → END
    graph.add_edge("authenticator", END)
    graph.add_edge("session_manager", END)
    graph.add_edge("identity_migrator", END)
    graph.add_edge("identity_manager", END)

    return graph.compile()


__all__ = ["create_user_management_graph", "route_to_agent"]

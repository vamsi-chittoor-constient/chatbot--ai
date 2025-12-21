"""
User Profile Feature Graph
==========================
LangGraph orchestration for user_profile sub-agents.

Routing:
- manage_preferences → preference_manager
- manage_favorites → favorites_manager
- view_history → history_manager
"""

from typing import Dict, Any
from langgraph.graph import StateGraph, END
import structlog

from app.features.user_profile.state import ProfileState
from app.features.user_profile.agents import (
    preference_manager_agent,
    favorites_manager_agent,
    history_manager_agent
)

logger = structlog.get_logger("user_profile.graph")


def route_to_agent(classification: Dict[str, Any]) -> str:
    """Route to appropriate sub-agent based on classification."""
    sub_intent = classification.get("sub_intent")

    routing_map = {
        "manage_preferences": "preference_manager",
        "manage_favorites": "favorites_manager",
        "view_history": "history_manager"
    }

    agent_name = routing_map.get(sub_intent, "history_manager")  # Default to history

    logger.info(
        "Routing to agent",
        sub_intent=sub_intent,
        agent=agent_name
    )

    return agent_name


def create_user_profile_graph() -> StateGraph:
    """Create the user_profile feature graph."""

    graph = StateGraph(ProfileState)

    # Add nodes
    graph.add_node("preference_manager", preference_manager_agent)
    graph.add_node("favorites_manager", favorites_manager_agent)
    graph.add_node("history_manager", history_manager_agent)

    # Set entry point
    graph.set_entry_point("history_manager")  # Default entry

    # All agents → END
    graph.add_edge("preference_manager", END)
    graph.add_edge("favorites_manager", END)
    graph.add_edge("history_manager", END)

    return graph.compile()


__all__ = ["create_user_profile_graph", "route_to_agent"]

"""
General Queries Feature Graph
=============================
LangGraph orchestration for general_queries sub-agents.

Routing:
- search_knowledge → knowledge_agent
- get_restaurant_info → restaurant_info_agent
- general_inquiry → general_assistant_agent
"""

from typing import Dict, Any
from langgraph.graph import StateGraph, END
import structlog

from app.features.general_queries.state import GeneralQueriesState
from app.features.general_queries.agents import (
    knowledge_agent,
    restaurant_info_agent,
    general_assistant_agent
)

logger = structlog.get_logger("general_queries.graph")


def route_to_agent(classification: Dict[str, Any]) -> str:
    """Route to appropriate sub-agent based on classification."""
    sub_intent = classification.get("sub_intent")

    routing_map = {
        "search_knowledge": "knowledge_agent",
        "get_restaurant_info": "restaurant_info_agent",
        "general_inquiry": "general_assistant_agent"
    }

    agent_name = routing_map.get(sub_intent, "general_assistant_agent")  # Default to general assistant

    logger.info(
        "Routing to agent",
        sub_intent=sub_intent,
        agent=agent_name
    )

    return agent_name


def create_general_queries_graph() -> StateGraph:
    """Create the general_queries feature graph."""

    graph = StateGraph(GeneralQueriesState)

    # Add nodes
    graph.add_node("knowledge_agent", knowledge_agent)
    graph.add_node("restaurant_info_agent", restaurant_info_agent)
    graph.add_node("general_assistant_agent", general_assistant_agent)

    # Set entry point
    graph.set_entry_point("general_assistant_agent")  # Default entry

    # All agents → END
    graph.add_edge("knowledge_agent", END)
    graph.add_edge("restaurant_info_agent", END)
    graph.add_edge("general_assistant_agent", END)

    return graph.compile()


__all__ = ["create_general_queries_graph", "route_to_agent"]

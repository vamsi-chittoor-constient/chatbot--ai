"""
Feedback Feature Graph
======================
LangGraph orchestration for feedback sub-agents.

Routing:
- submit_complaint → complaint_creator
- track_complaint → complaint_tracker
- submit_feedback → feedback_collector
- nps_survey → nps_surveyor
- view_metrics → satisfaction_analyst
"""

from typing import Dict, Any
from langgraph.graph import StateGraph, END
import structlog

from app.features.feedback.state import FeedbackState
from app.features.feedback.agents.complaint_creator import complaint_creator_agent
from app.features.feedback.agents.complaint_tracker import complaint_tracker_agent
from app.features.feedback.agents.feedback_collector import feedback_collector_agent
from app.features.feedback.agents.nps_surveyor import nps_surveyor_agent
from app.features.feedback.agents.satisfaction_analyst import satisfaction_analyst_agent

logger = structlog.get_logger("feedback.graph")


def route_to_agent(classification: Dict[str, Any]) -> str:
    """Route to appropriate sub-agent based on classification."""
    sub_intent = classification.get("sub_intent")

    routing_map = {
        "submit_complaint": "complaint_creator",
        "track_complaint": "complaint_tracker",
        "submit_feedback": "feedback_collector",
        "nps_survey": "nps_surveyor",
        "view_metrics": "satisfaction_analyst"
    }

    agent_name = routing_map.get(sub_intent, "feedback_collector")  # Default

    logger.info(
        "Routing to agent",
        sub_intent=sub_intent,
        agent=agent_name
    )

    return agent_name


def create_feedback_graph() -> StateGraph:
    """Create the feedback feature graph."""

    graph = StateGraph(FeedbackState)

    # Add nodes
    graph.add_node("complaint_creator", complaint_creator_agent)
    graph.add_node("complaint_tracker", complaint_tracker_agent)
    graph.add_node("feedback_collector", feedback_collector_agent)
    graph.add_node("nps_surveyor", nps_surveyor_agent)
    graph.add_node("satisfaction_analyst", satisfaction_analyst_agent)

    # Set entry point
    graph.set_entry_point("feedback_collector")  # Default entry

    # All agents → END
    graph.add_edge("complaint_creator", END)
    graph.add_edge("complaint_tracker", END)
    graph.add_edge("feedback_collector", END)
    graph.add_edge("nps_surveyor", END)
    graph.add_edge("satisfaction_analyst", END)

    return graph.compile()


__all__ = ["create_feedback_graph", "route_to_agent"]

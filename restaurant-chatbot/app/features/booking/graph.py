"""
Booking Feature Orchestration Graph
===================================

Orchestrates booking sub-agents based on sub-intent classification.

Sub-agents:
- availability_checker: Check table availability
- booking_creator: Create new bookings
- booking_viewer: View existing bookings
- booking_modifier: Modify bookings
- booking_canceller: Cancel bookings
"""

from typing import Literal, Dict, Any
from langgraph.graph import StateGraph, END

from app.features.booking.state import BookingState, BOOKING_SUB_INTENTS
from app.features.booking.logger import booking_logger


# Import sub-agents (will be created)
from app.features.booking.agents.availability_checker.node import availability_checker_node
from app.features.booking.agents.booking_creator.node import booking_creator_node
from app.features.booking.agents.booking_viewer.node import booking_viewer_node
from app.features.booking.agents.booking_modifier.node import booking_modifier_node
from app.features.booking.agents.booking_canceller.node import booking_canceller_node


def classify_booking_sub_intent(state: BookingState) -> str:
    """
    Classify the booking sub-intent from the current state.

    Sub-intents:
    - check_availability: Check if tables available
    - create_booking: Create new reservation
    - view_bookings: View existing bookings
    - modify_booking: Modify existing booking
    - cancel_booking: Cancel booking

    Returns:
        str: Sub-intent name
    """
    # If sub-intent already classified, use it
    if state.get("current_sub_intent"):
        sub_intent = state["current_sub_intent"]
        booking_logger.info(
            "Using pre-classified sub-intent",
            sub_intent=sub_intent
        )
        return sub_intent

    # Get the last message
    messages = state.get("messages", [])
    if not messages:
        booking_logger.warning("No messages in state for sub-intent classification")
        return "create_booking"  # Default

    last_message = messages[-1]
    message_content = getattr(last_message, 'content', '')
    message_text = message_content.lower() if isinstance(message_content, str) else ""

    # Simple keyword-based classification (can be enhanced with LLM)
    if any(word in message_text for word in ["available", "availability", "check", "free", "open"]):
        sub_intent = "check_availability"
    elif any(word in message_text for word in ["view", "show", "see", "my bookings", "reservations"]):
        sub_intent = "view_bookings"
    elif any(word in message_text for word in ["cancel", "delete", "remove"]):
        sub_intent = "cancel_booking"
    elif any(word in message_text for word in ["change", "modify", "update", "reschedule"]):
        sub_intent = "modify_booking"
    else:
        # Default to create booking
        sub_intent = "create_booking"

    booking_logger.info(
        "Classified booking sub-intent",
        sub_intent=sub_intent,
        message_preview=message_text[:100]
    )

    return sub_intent


def route_to_sub_agent(
    state: BookingState
) -> Literal[
    "availability_checker",
    "booking_creator",
    "booking_viewer",
    "booking_modifier",
    "booking_canceller"
]:
    """
    Route to appropriate sub-agent based on sub-intent.

    Returns:
        str: Sub-agent node name or "end"
    """
    sub_intent = classify_booking_sub_intent(state)

    routing_map = {
        "check_availability": "availability_checker",
        "create_booking": "booking_creator",
        "view_bookings": "booking_viewer",
        "modify_booking": "booking_modifier",
        "cancel_booking": "booking_canceller"
    }

    target_agent = routing_map.get(sub_intent, "booking_creator")

    booking_logger.info(
        "Routing to booking sub-agent",
        sub_intent=sub_intent,
        target_agent=target_agent
    )

    return target_agent


def should_continue_booking(
    state: BookingState
) -> Literal[
    "availability_checker",
    "booking_creator",
    "booking_viewer",
    "booking_modifier",
    "booking_canceller",
    "end"
]:
    """
    Determine if booking flow should continue or end, and route to appropriate sub-agent.

    Checks:
    - Is booking complete? → end
    - User wants to stop? → end
    - Otherwise → route to appropriate sub-agent
    """
    # Check if booking is complete
    booking_progress = state.get("booking_progress")
    if booking_progress and booking_progress.is_booking_complete():
        booking_logger.info("Booking complete, ending flow")
        return "end"

    # Check for cancellation signals in messages
    messages = state.get("messages", [])
    if messages:
        last_message = messages[-1]
        message_content = getattr(last_message, 'content', '')
        message_text = message_content.lower() if isinstance(message_content, str) else ""

        if any(word in message_text for word in ["stop", "quit", "exit", "nevermind", "cancel this"]):
            booking_logger.info("User requested to stop booking flow")
            return "end"

    # Route to appropriate sub-agent
    return route_to_sub_agent(state)


# ============================================================================
# BUILD GRAPH
# ============================================================================

def create_booking_graph():
    """Create the booking feature graph with sub-agent routing"""

    # Create graph
    graph = StateGraph(BookingState)

    # Add sub-agent nodes
    graph.add_node("availability_checker", availability_checker_node)
    graph.add_node("booking_creator", booking_creator_node)
    graph.add_node("booking_viewer", booking_viewer_node)
    graph.add_node("booking_modifier", booking_modifier_node)
    graph.add_node("booking_canceller", booking_canceller_node)

    # Set entry point with conditional routing
    graph.set_entry_point("booking_creator")  # Default entry

    # Add conditional routing from entry
    graph.add_conditional_edges(
        "booking_creator",
        should_continue_booking,
        {
            "availability_checker": "availability_checker",
            "booking_creator": "booking_creator",
            "booking_viewer": "booking_viewer",
            "booking_modifier": "booking_modifier",
            "booking_canceller": "booking_canceller",
            "end": END
        }
    )

    # Add edges from each sub-agent back to routing decision
    for sub_agent in [
        "availability_checker",
        "booking_viewer",
        "booking_modifier",
        "booking_canceller"
    ]:
        graph.add_conditional_edges(
            sub_agent,
            should_continue_booking,
            {
                "availability_checker": "availability_checker",
                "booking_creator": "booking_creator",
                "booking_viewer": "booking_viewer",
                "booking_modifier": "booking_modifier",
                "booking_canceller": "booking_canceller",
                "end": END
            }
        )

    # Compile graph
    compiled_graph = graph.compile()

    booking_logger.info("Booking orchestration graph created successfully")

    return compiled_graph


# Create the graph instance
graph = create_booking_graph()

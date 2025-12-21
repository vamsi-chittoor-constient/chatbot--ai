"""
General Assistant Agent
=======================
Handles general questions, analytics, and fallback scenarios.

Responsibilities:
- Handle general restaurant questions
- Track query analytics
- Provide capability information
- Fallback handler for unclear queries
"""

from typing import Dict, Any
import structlog

from app.features.general_queries.state import GeneralQueriesState
from app.features.general_queries.tools import (
    track_query,
    get_query_statistics
)

logger = structlog.get_logger("general_queries.agents.general_assistant")


async def general_assistant_agent(
    entities: Dict[str, Any],
    state: GeneralQueriesState
) -> Dict[str, Any]:
    """
    General Assistant agent: Handle general queries and fallback.

    Args:
        entities: Extracted entities (query, query_category)
        state: Current queries state

    Returns:
        Response dict with action, success, and data
    """
    session_id = state.get("session_id", "unknown")
    user_message = state.get("user_message", "")
    queries_progress = state.get("queries_progress")

    logger.info(
        "General assistant agent executing",
        session_id=session_id,
        entities=entities
    )

    # Extract entities
    query = entities.get("query") or user_message
    query_category = entities.get("query_category", "general")

    # Handle capability questions (what can you do, what features, etc.)
    capability_keywords = ["can you", "do you", "what can", "help me", "capabilities", "features"]
    if any(keyword in query.lower() for keyword in capability_keywords):
        logger.info("Handling capability question")

        # Track this query
        if queries_progress:
            await track_query(
                query_text=query,
                query_category="capability",
                response_type="direct_answer",
                confidence_score=0.9
            )

        return {
            "action": "capabilities_explained",
            "success": True,
            "data": {
                "message": """I can help you with:

**Restaurant Information:**
- Business hours and opening times
- Location and directions
- Contact information
- Parking details

**Knowledge Base:**
- Frequently asked questions (FAQs)
- Restaurant policies (cancellation, refund, dietary, etc.)
- Dining information

**Food & Reservations:**
- Menu browsing and ordering
- Table reservations
- Order tracking

**Account Management:**
- Login and registration
- Profile and preferences
- Order history

What would you like to know more about?"""
            },
            "context": {
                "action_completed": "show_capabilities"
            }
        }

    # Handle general thank you / acknowledgment
    gratitude_keywords = ["thank you", "thanks", "appreciate", "helpful"]
    if any(keyword in query.lower() for keyword in gratitude_keywords):
        logger.info("Handling gratitude")

        # Mark user as satisfied
        if queries_progress:
            queries_progress.mark_query_resolved(satisfied=True)
            await track_query(
                query_text=query,
                query_category="gratitude",
                response_type="acknowledgment",
                confidence_score=1.0,
                user_satisfied=True
            )

        return {
            "action": "acknowledged",
            "success": True,
            "data": {
                "message": "You're welcome! Is there anything else I can help you with?"
            },
            "context": {
                "action_completed": "acknowledge"
            }
        }

    # Handle vague/unclear queries
    vague_keywords = ["help", "question", "ask", "tell me"]
    if len(query.split()) <= 2 or any(keyword == query.lower().strip() for keyword in vague_keywords):
        logger.info("Handling vague query")

        return {
            "action": "clarification_needed",
            "success": False,
            "data": {
                "message": """I'd be happy to help! I can assist with:

- **Restaurant info**: Hours, location, contact
- **FAQs**: Common questions and policies
- **Menu & Orders**: Browse menu and place orders
- **Reservations**: Book a table

What would you like to know about?"""
            },
            "context": {
                "needs_clarification": True
            }
        }

    # General query - provide helpful response
    logger.info("Handling general query")

    # Track the query
    if queries_progress:
        await track_query(
            query_text=query,
            query_category=query_category,
            response_type="general_response",
            confidence_score=0.7
        )

    # Generic helpful response
    return {
        "action": "general_response",
        "success": True,
        "data": {
            "message": f"""I understand you're asking about: "{query}"

I can help you with restaurant information, FAQs, menu browsing, reservations, and more.

Could you please be more specific about what you'd like to know? For example:
- "What are your hours?"
- "What's your cancellation policy?"
- "Show me the menu"
- "I want to make a reservation" """
        },
        "context": {
            "action_completed": "general_response",
            "needs_followup": True
        }
    }


__all__ = ["general_assistant_agent"]

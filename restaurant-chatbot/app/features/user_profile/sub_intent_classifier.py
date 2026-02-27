"""
User Profile Sub-Intent Classifier
==================================
LLM-based classification for routing to appropriate handler.

Sub-Intents:
- manage_preferences: Update dietary restrictions, cuisines, allergies, spice level
- manage_favorites: Add/remove/view favorite menu items
- view_history: View order/booking history and reorder
"""

from typing import Dict, Any, List, Literal
from pydantic import BaseModel, Field
import structlog

from app.ai_services.llm_manager import get_llm_manager
from app.core.config import config
from app.features.user_profile.state import ProfileState

logger = structlog.get_logger("user_profile.classifier")

# Get LLM manager instance
llm_manager = get_llm_manager()


class SubIntentClassification(BaseModel):
    """Classification result for user_profile sub-intent."""

    sub_intent: Literal[
        "manage_preferences",
        "manage_favorites",
        "view_history"
    ]
    confidence: float = Field(ge=0.0, le=1.0)
    entities: Dict[str, Any] = Field(default_factory=dict)
    missing_entities: List[str] = Field(default_factory=list)
    reasoning: str


async def classify_sub_intent(
    user_message: str,
    state: ProfileState
) -> SubIntentClassification:
    """
    Classify user message into user_profile sub-intent.

    Args:
        user_message: User's message
        state: Current profile state

    Returns:
        SubIntentClassification with sub-intent, entities, and metadata
    """
    session_id = state.get("session_id", "unknown")

    logger.info(
        "Classifying user_profile sub-intent",
        session_id=session_id,
        message_length=len(user_message)
    )

    # Build classification prompt
    system_prompt = """You are a sub-intent classifier for user profile management.

Your task is to classify the user's message into ONE of these sub-intents:

1. **manage_preferences**: Update dietary and cuisine preferences
   - Keywords: dietary, allergy, allergic, vegetarian, vegan, gluten-free, cuisine, spice, seating
   - Examples: "I'm vegetarian", "I'm allergic to peanuts", "I like Chinese food", "I prefer medium spice"
   - Entities: dietary_restrictions, allergies, favorite_cuisines, spice_level, preferred_seating, action (add/remove)

2. **manage_favorites**: Manage favorite menu items
   - Keywords: favorite, save, bookmark, add to favorites, remove from favorites
   - Examples: "Add this to my favorites", "Save this item", "Remove from my favorites"
   - Entities: item_id, item_name, action (add/remove/view)

3. **view_history**: View order/booking history or reorder
   - Keywords: history, past orders, previous bookings, reorder, order again
   - Examples: "Show my order history", "What did I order last time?", "Reorder my last order"
   - Entities: history_type (orders/bookings/browsing), limit, order_id (for reorder)

Extract relevant entities from the message and list any missing required entities.

Return your classification in JSON format."""

    user_prompt = f"""User message: "{user_message}"

Current state:
- User authenticated: {state.get('user_id') is not None}
- User ID: {state.get('user_id', 'not provided')}
- Session ID: {session_id}

Classify the sub-intent and extract entities."""

    try:
        # Get LLM with structured output
        structured_llm = await llm_manager.get_llm_with_structured_output(
            schema=SubIntentClassification,
            model=config.INTENT_CLASSIFICATION_MODEL,
            temperature=0.1
        )

        # Invoke LLM
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        classification = await structured_llm.ainvoke(messages)

        logger.info(
            "Sub-intent classified",
            session_id=session_id,
            sub_intent=classification.sub_intent,
            confidence=classification.confidence,
            entities=classification.entities
        )

        return classification

    except Exception as e:
        logger.error(
            "Sub-intent classification failed",
            session_id=session_id,
            error=str(e)
        )

        # Fallback to default
        return SubIntentClassification(
            sub_intent="view_history",
            confidence=0.5,
            entities={},
            missing_entities=[],
            reasoning="Classification failed, defaulting to view_history"
        )


__all__ = ["classify_sub_intent", "SubIntentClassification"]

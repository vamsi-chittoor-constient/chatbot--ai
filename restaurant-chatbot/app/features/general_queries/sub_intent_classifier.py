"""
General Queries Sub-Intent Classifier
=====================================
LLM-based classification for routing to appropriate handler.

Sub-Intents:
- search_knowledge: FAQ and policy queries
- get_restaurant_info: Hours, location, contact information
- general_inquiry: General questions and fallback
"""

from typing import Dict, Any, List, Literal
from pydantic import BaseModel, Field
import structlog

from app.ai_services.llm_manager import get_llm_manager
from app.core.config import config
from app.features.general_queries.state import GeneralQueriesState

logger = structlog.get_logger("general_queries.classifier")

# Get LLM manager instance
llm_manager = get_llm_manager()


class SubIntentClassification(BaseModel):
    """Classification result for general_queries sub-intent."""

    sub_intent: Literal[
        "search_knowledge",
        "get_restaurant_info",
        "general_inquiry"
    ]
    confidence: float = Field(ge=0.0, le=1.0)
    entities: Dict[str, Any] = Field(default_factory=dict)
    missing_entities: List[str] = Field(default_factory=list)
    reasoning: str


async def classify_sub_intent(
    user_message: str,
    state: GeneralQueriesState
) -> SubIntentClassification:
    """
    Classify user message into general_queries sub-intent.

    Args:
        user_message: User's message
        state: Current queries state

    Returns:
        SubIntentClassification with sub-intent, entities, and metadata
    """
    session_id = state.get("session_id", "unknown")

    logger.info(
        "Classifying general_queries sub-intent",
        session_id=session_id,
        message_length=len(user_message)
    )

    # Build classification prompt
    system_prompt = """You are a sub-intent classifier for general queries about a restaurant.

Your task is to classify the user's message into ONE of these sub-intents:

1. **search_knowledge**: FAQ and policy questions
   - Keywords: question, how, what, policy, rule, faq, help, cancellation, refund, dietary, allergen
   - Examples: "What are your cancellation policies?", "Do you have vegetarian options?", "How do I make a reservation?"
   - Entities: query, faq_category, policy_type

2. **get_restaurant_info**: Restaurant operational information
   - Keywords: hours, open, close, location, address, phone, contact, email, parking, directions
   - Examples: "What are your hours?", "Where are you located?", "What's your phone number?"
   - Entities: info_type (hours/location/contact/parking)

3. **general_inquiry**: General questions and fallback
   - Keywords: anything not covered above, capability questions, general information
   - Examples: "Tell me about your restaurant", "What can you help me with?", "I have a question"
   - Entities: query, query_category

Extract relevant entities from the message and list any missing required entities.

Return your classification in JSON format."""

    user_prompt = f"""User message: "{user_message}"

Current state:
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
            sub_intent="general_inquiry",
            confidence=0.5,
            entities={},
            missing_entities=[],
            reasoning="Classification failed, defaulting to general_inquiry"
        )


__all__ = ["classify_sub_intent", "SubIntentClassification"]

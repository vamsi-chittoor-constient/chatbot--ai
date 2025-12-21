"""
Sub-Intent Classifier for Feedback Feature
===========================================
LLM-based intent classification and entity extraction for feedback/complaints.

Uses structured output with Pydantic models for type-safe parsing.
"""

from typing import Dict, Any, List, Literal
import structlog
from pydantic import BaseModel, Field

from langchain_core.messages import SystemMessage, HumanMessage

from app.features.feedback.state import FeedbackState
from app.ai_services.llm_manager import get_llm_manager
from app.core.config import config

logger = structlog.get_logger("feedback.sub_intent_classifier")


class SubIntentClassification(BaseModel):
    """Result of sub-intent classification with entities."""

    sub_intent: Literal[
        "submit_complaint",
        "track_complaint",
        "submit_feedback",
        "nps_survey",
        "view_metrics"
    ] = Field(..., description="Classified sub-intent category")

    confidence: float = Field(..., ge=0.0, le=1.0, description="Classification confidence")

    entities: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extracted entities from user message"
    )

    missing_entities: List[str] = Field(
        default_factory=list,
        description="Required entities that are missing"
    )

    reasoning: str = Field(
        ...,
        description="Why this intent was chosen (for debugging)"
    )


async def classify_sub_intent(
    user_message: str,
    state: FeedbackState
) -> SubIntentClassification:
    """
    Classify user's sub-intent and extract entities.

    Args:
        user_message: User's current message
        state: Current feedback state (for context)

    Returns:
        SubIntentClassification with intent, entities, and missing fields
    """
    session_id = state.get("session_id", "unknown")

    logger.info(
        "Classifying feedback sub-intent",
        session_id=session_id,
        message=user_message[:50]
    )

    # Build context from state
    context_parts = []

    # Existing complaint context
    complaint_id = state.get("complaint_id")
    if complaint_id:
        complaint_status = state.get("complaint_status", "unknown")
        context_parts.append(f"Active complaint: {complaint_id} (Status: {complaint_status})")

    # Recent orders/bookings for context
    recent_orders = state.get("recent_orders", [])
    if recent_orders:
        context_parts.append(f"User has {len(recent_orders)} recent orders")

    recent_bookings = state.get("recent_bookings", [])
    if recent_bookings:
        context_parts.append(f"User has {len(recent_bookings)} recent bookings")

    # Auth context
    if state.get("user_id"):
        context_parts.append(f"User authenticated: {state.get('user_name', 'Guest')}")
    else:
        context_parts.append("User NOT authenticated")

    context = "\n".join(context_parts) if context_parts else "No context"

    # System prompt for classification
    system_prompt = """You are a feedback/complaints intent classifier for a restaurant.

Your task: Classify the user's message into ONE of 5 sub-intents and extract entities.

## Sub-Intents:

1. **submit_complaint** - User wants to file a complaint
   Examples: "I want to complain about", "the food was terrible", "service was poor", "I have a complaint"
   Entities: category, description, priority (optional)
   Categories: food_quality, service, cleanliness, wait_time, billing, other

2. **track_complaint** - User wants to check complaint status or update existing complaint
   Examples: "what's my complaint status", "check complaint #123", "any update on my complaint"
   Entities: complaint_id (optional - can look up by user)

3. **submit_feedback** - User wants to provide general feedback or rating
   Examples: "I'd like to leave feedback", "rate my experience", "the food was great", "5 stars"
   Entities: rating (1-5), feedback_text (optional), feedback_type (optional)
   Feedback types: general, food, service, ambiance, value

4. **nps_survey** - User responding to NPS survey or wants to rate likelihood to recommend
   Examples: "I'd rate 9 out of 10", "how likely am I to recommend", "NPS survey", "I'd give you 10"
   Entities: nps_score (0-10), nps_reason (optional)

5. **view_metrics** - User/staff wants to see satisfaction metrics and analytics
   Examples: "show satisfaction metrics", "what's our NPS", "complaint trends", "customer feedback report"
   Entities: metric_type (optional), time_period (optional)

## Entity Extraction Rules:

- **category**: Complaint category (food_quality, service, cleanliness, wait_time, billing, other)
- **description**: Complaint or feedback description text
- **priority**: low, medium, high, critical (auto-assign based on sentiment if not explicit)
- **rating**: 1-5 stars for feedback
- **nps_score**: 0-10 for NPS survey
- **feedback_text**: Written feedback or review
- **feedback_type**: general, food, service, ambiance, value
- **complaint_id**: Complaint ticket ID for tracking
- **order_id**: Related order ID
- **booking_id**: Related booking ID

## Sentiment-Based Priority Assignment:

When user submits complaint, analyze sentiment:
- Very negative language, words like "terrible", "horrible", "worst", "disgusting" → high/critical
- Negative language, words like "bad", "poor", "disappointed" → medium
- Mild complaints → low

## Automatic Complaint Detection:

If user provides negative feedback (rating 1-2 stars or very negative text), consider:
- If they explicitly say "complaint" or "issue" → submit_complaint
- If they're just expressing dissatisfaction → could be submit_feedback (we'll auto-convert to complaint in agent)

## Missing Entities:

If an intent REQUIRES an entity but it's missing:
- Add to "missing_entities" list
- System will ask user for it

Example:
  Message: "I want to file a complaint"
  Intent: submit_complaint
  Missing: ["description", "category"]

## Context Awareness:

Use the provided context to:
- Know if user has existing complaint (track vs submit)
- Know if user has recent orders/bookings (for linking)
- Know authentication status

## Output Format:

Return VALID JSON following this schema:
{
  "sub_intent": "submit_complaint",
  "confidence": 0.95,
  "entities": {
    "category": "food_quality",
    "description": "The butter chicken was cold",
    "priority": "medium"
  },
  "missing_entities": [],
  "reasoning": "User describing negative food experience with specific details"
}

CRITICAL: Return ONLY valid JSON, no markdown, no explanation."""

    user_prompt = f"""Context:
{context}

User Message: "{user_message}"

Classify intent and extract entities:"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]

    try:
        # Get LLM manager
        llm_manager = get_llm_manager()

        # Use structured output with Pydantic model
        structured_llm = await llm_manager.get_llm_with_structured_output(
            schema=SubIntentClassification,
            model=config.INTENT_CLASSIFICATION_MODEL,
            temperature=0.1
        )

        # Invoke with type-safe structured response
        classification: SubIntentClassification = await structured_llm.ainvoke(messages)

        logger.info(
            "Sub-intent classified",
            session_id=session_id,
            sub_intent=classification.sub_intent,
            confidence=classification.confidence,
            entities=classification.entities,
            missing=classification.missing_entities
        )

        return classification

    except Exception as e:
        logger.error(
            "Sub-intent classification failed",
            error=str(e),
            session_id=session_id,
            exc_info=True
        )

        # Fallback: Try to infer from keywords
        return _fallback_classification(user_message, state)


def _fallback_classification(
    user_message: str,
    state: FeedbackState
) -> SubIntentClassification:
    """
    Fallback classification using keyword matching.

    Used when LLM fails to return valid JSON.
    """
    message_lower = user_message.lower()

    # Complaint keywords
    if any(word in message_lower for word in ["complaint", "complain", "issue", "problem", "terrible", "horrible", "worst"]):
        # Check if tracking existing complaint
        if any(word in message_lower for word in ["status", "check", "update", "track"]) and state.get("complaint_id"):
            return SubIntentClassification(
                sub_intent="track_complaint",
                confidence=0.7,
                entities={},
                missing_entities=[],
                reasoning="Fallback: Tracking complaint keywords detected"
            )
        else:
            return SubIntentClassification(
                sub_intent="submit_complaint",
                confidence=0.7,
                entities={},
                missing_entities=["description", "category"],
                reasoning="Fallback: Complaint keywords detected"
            )

    # NPS keywords (0-10 score, "out of 10", "recommend")
    if any(word in message_lower for word in ["out of 10", "recommend", "/10", "nps"]):
        return SubIntentClassification(
            sub_intent="nps_survey",
            confidence=0.7,
            entities={},
            missing_entities=["nps_score"],
            reasoning="Fallback: NPS keywords detected"
        )

    # Feedback/rating keywords
    if any(word in message_lower for word in ["feedback", "rating", "rate", "review", "stars", "experience"]):
        return SubIntentClassification(
            sub_intent="submit_feedback",
            confidence=0.6,
            entities={},
            missing_entities=["rating"],
            reasoning="Fallback: Feedback keywords detected"
        )

    # Metrics keywords (for staff/analytics)
    if any(word in message_lower for word in ["metrics", "analytics", "trends", "report", "dashboard"]):
        return SubIntentClassification(
            sub_intent="view_metrics",
            confidence=0.6,
            entities={},
            missing_entities=[],
            reasoning="Fallback: Metrics keywords detected"
        )

    # Default: Submit feedback (most common)
    return SubIntentClassification(
        sub_intent="submit_feedback",
        confidence=0.4,
        entities={},
        missing_entities=["rating"],
        reasoning="Fallback: No clear intent, defaulting to feedback"
    )


__all__ = ["classify_sub_intent", "SubIntentClassification"]

"""
User Management Sub-Intent Classifier
=====================================
LLM-based classification for routing to appropriate handler.

Sub-Intents:
- authenticate: Login/register flow (phone → OTP → verify)
- manage_sessions: View/revoke sessions, manage devices
- migrate_identity: Migrate anonymous device data to user account
- update_identity: Update name, email, phone number
"""

from typing import Dict, Any, List, Literal
from pydantic import BaseModel, Field
import structlog

from app.ai_services.llm_manager import get_llm_manager
from app.core.config import config
from app.features.user_management.state import AuthenticationState

logger = structlog.get_logger("user_management.classifier")

# Get LLM manager instance
llm_manager = get_llm_manager()


class SubIntentClassification(BaseModel):
    """Classification result for user_management sub-intent."""

    sub_intent: Literal[
        "authenticate",
        "manage_sessions",
        "migrate_identity",
        "update_identity"
    ]
    confidence: float = Field(ge=0.0, le=1.0)
    entities: Dict[str, Any] = Field(default_factory=dict)
    missing_entities: List[str] = Field(default_factory=list)
    reasoning: str


async def classify_sub_intent(
    user_message: str,
    state: AuthenticationState
) -> SubIntentClassification:
    """
    Classify user message into user_management sub-intent.

    Args:
        user_message: User's message
        state: Current authentication state

    Returns:
        SubIntentClassification with sub-intent, entities, and metadata
    """
    session_id = state.get("session_id", "unknown")

    logger.info(
        "Classifying user_management sub-intent",
        session_id=session_id,
        message_length=len(user_message)
    )

    # Build classification prompt
    system_prompt = """You are a sub-intent classifier for user management and authentication.

Your task is to classify the user's message into ONE of these sub-intents:

1. **authenticate**: Login or register flow
   - Keywords: login, register, sign in, sign up, verify, OTP, code
   - Examples: "I want to login", "Send me OTP", "My code is 1234"
   - Entities: phone, otp_code, full_name, email

2. **manage_sessions**: View or manage authentication sessions/devices
   - Keywords: logout, sessions, devices, sign out, view devices
   - Examples: "Show my logged in devices", "Logout from all devices"
   - Entities: action (view/revoke), session_id, device_id

3. **migrate_identity**: Migrate anonymous device data to user account
   - Keywords: transfer, migrate, merge, cart, favorites, anonymous
   - Examples: "Transfer my cart after login", "Migrate my favorites"
   - Entities: migration_type (cart/favorites/all)

4. **update_identity**: Update personal identity information
   - Keywords: update, change, edit, name, email, phone number
   - Examples: "Change my name", "Update my email address"
   - Entities: field (name/email/phone), new_value

Extract relevant entities from the message and list any missing required entities.

Return your classification in JSON format."""

    user_prompt = f"""User message: "{user_message}"

Current state:
- User authenticated: {state.get('user_id') is not None}
- Phone: {state.get('phone', 'not provided')}
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
            sub_intent="authenticate",
            confidence=0.5,
            entities={},
            missing_entities=[],
            reasoning="Classification failed, defaulting to authenticate"
        )


__all__ = ["classify_sub_intent", "SubIntentClassification"]

"""
Common Models for Agent Communication
======================================
Shared models used across all agents for structured communication.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class ActionResult(BaseModel):
    """
    Structured result from specialist agents.

    This model ensures agents return DATA (not prose), which the response_agent
    then transforms into warm, hospitality-focused responses.

    Example:
        booking_agent returns:
        ActionResult(
            action="booking_created",
            success=True,
            data={
                "booking_id": "BK12345",
                "party_size": 4,
                "time": "19:00",
                "table_number": 12
            },
            suggestions=["Would you like to see the chef's tasting menu?"]
        )

        response_agent transforms to:
        "Awesome! Got you all set for 4 people at 7pm at table 12.
         Can't wait to see you! Want to check out our chef's special menu?"
    """

    action: str = Field(
        ...,
        description="Type of action performed (e.g., 'booking_created', 'item_added', 'menu_displayed')"
    )

    success: bool = Field(
        ...,
        description="Whether the action succeeded"
    )

    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Structured data about the action"
    )

    error: Optional[str] = Field(
        None,
        description="Error message if success=False"
    )

    suggestions: Optional[List[str]] = Field(
        None,
        description="Upselling suggestions or recommendations (used by response_agent for contextual upselling)"
    )

    context: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional context for response formatting (e.g., special_occasion, dietary_needs)"
    )

    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Agent-specific metadata for debugging/analytics"
    )


class ConversationContext(BaseModel):
    """
    Context about the current conversation for response personalization.

    Used by response_agent to adjust tone, upselling strategy, etc.
    """

    user_tier: Optional[str] = Field(
        None,
        description="User tier (VIP, regular, new) - affects response style"
    )

    special_occasion: Optional[str] = Field(
        None,
        description="Special occasion (birthday, anniversary, etc.)"
    )

    dietary_restrictions: Optional[List[str]] = Field(
        None,
        description="User's dietary restrictions for contextual recommendations"
    )

    conversation_stage: Optional[str] = Field(
        None,
        description="Stage of conversation (greeting, ordering, checkout, etc.)"
    )

    previous_orders: Optional[int] = Field(
        None,
        description="Number of previous orders (for personalization)"
    )

    cart_value: Optional[float] = Field(
        None,
        description="Current cart value (for upselling threshold)"
    )


# Common action types (for consistency across agents)
class ActionType:
    """Standard action types used across all agents"""

    # Booking actions
    BOOKING_CREATED = "booking_created"
    BOOKING_MODIFIED = "booking_modified"
    BOOKING_CANCELLED = "booking_cancelled"
    AVAILABILITY_CHECKED = "availability_checked"

    # Order actions
    ITEM_ADDED = "item_added"
    ITEM_REMOVED = "item_removed"
    CART_VIEWED = "cart_viewed"
    ORDER_PLACED = "order_placed"
    CHECKOUT_INITIATED = "checkout_initiated"

    # Menu actions
    MENU_DISPLAYED = "menu_displayed"
    CATEGORY_VIEWED = "category_viewed"
    ITEM_DETAILS_SHOWN = "item_details_shown"
    SEARCH_PERFORMED = "search_performed"

    # Payment actions
    PAYMENT_LINK_CREATED = "payment_link_created"
    PAYMENT_STATUS_CHECKED = "payment_status_checked"

    # Auth actions
    OTP_SENT = "otp_sent"
    USER_AUTHENTICATED = "user_authenticated"
    USER_CREATED = "user_created"
    SESSION_REVOKED = "session_revoked"

    # Profile actions
    PROFILE_UPDATED = "profile_updated"
    PREFERENCES_UPDATED = "preferences_updated"
    FAVORITE_ADDED = "favorite_added"
    HISTORY_VIEWED = "history_viewed"

    # Support/Satisfaction actions
    COMPLAINT_CREATED = "complaint_created"
    FEEDBACK_SUBMITTED = "feedback_submitted"
    FAQ_ANSWERED = "faq_answered"

    # Error/Clarification actions
    CLARIFICATION_NEEDED = "clarification_needed"
    ERROR_OCCURRED = "error_occurred"
    VALIDATION_FAILED = "validation_failed"

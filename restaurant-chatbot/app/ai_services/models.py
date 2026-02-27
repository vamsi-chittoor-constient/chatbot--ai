"""
AI Services Pydantic Models
============================
Structured output models for LLM responses using LangChain's with_structured_output.

These models ensure type safety and validation for all AI service responses.
"""

from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field, field_validator


class IntentAnalysis(BaseModel):
    """
    Structured intent analysis result from LLM.

    Used with .with_structured_output() for reliable intent detection.
    """
    intent: Literal[
        "greeting",
        "menu_inquiry",
        "order_request",
        "booking_request",
        "booking_management",
        "payment_question",
        "complaint",
        "feedback",
        "satisfaction_survey",
        "faq",
        "policy_inquiry",
        "hours_inquiry",
        "location_inquiry",
        "general_question",
        "support_request"
    ] = Field(
        description="Primary intent classification"
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score between 0.0 and 1.0"
    )

    entities: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extracted entities like dates, times, food items, quantities"
    )

    context_needed: List[str] = Field(
        default_factory=list,
        description="Additional information required from user"
    )

    user_sentiment: Literal["positive", "neutral", "negative", "confused"] = Field(
        default="neutral",
        description="User's emotional tone"
    )

    complexity: Literal["simple", "moderate", "complex"] = Field(
        default="simple",
        description="Message complexity level"
    )

    requires_clarification: bool = Field(
        default=False,
        description="Whether the message is unclear and needs clarification"
    )

    pre_filter_matched: bool = Field(
        default=False,
        description="Whether this was matched by rule-based pre-filter"
    )

    @field_validator('entities', mode='before')
    @classmethod
    def validate_entities(cls, v: Any) -> Dict[str, Any]:
        """Convert empty list to empty dict (LLM sometimes returns [] instead of {})."""
        if isinstance(v, list) and len(v) == 0:
            return {}
        if not isinstance(v, dict):
            return {}
        return v

    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Ensure confidence is between 0 and 1."""
        if not 0.0 <= v <= 1.0:
            return 0.5  # Default fallback
        return v


class ExtractedEntity(BaseModel):
    """Single extracted entity with metadata."""
    value: Any = Field(description="Entity value")
    type: str = Field(description="Entity type (e.g., food_item, date, time, phone)")
    confidence: Optional[float] = Field(default=None, description="Extraction confidence")


class EntityExtractionResult(BaseModel):
    """
    Structured entity extraction result from LLM.

    Used with .with_structured_output() for reliable entity extraction.
    """
    # Core entities
    food_items: List[str] = Field(
        default_factory=list,
        description="Mentioned food/menu items"
    )

    quantities: List[int] = Field(
        default_factory=list,
        description="Quantities or numbers mentioned"
    )

    preferences: List[str] = Field(
        default_factory=list,
        description="Dietary preferences or requirements"
    )

    # Date/time entities
    date: Optional[str] = Field(
        default=None,
        description="Date mentioned (ISO format or relative like 'tomorrow')"
    )

    time: Optional[str] = Field(
        default=None,
        description="Time mentioned (e.g., '6pm', '18:00')"
    )

    # Contact entities
    phone_number: Optional[str] = Field(
        default=None,
        description="Phone number (10 digits)"
    )

    email: Optional[str] = Field(
        default=None,
        description="Email address"
    )

    name: Optional[str] = Field(
        default=None,
        description="Person's name"
    )

    # Booking/order entities
    party_size: Optional[int] = Field(
        default=None,
        description="Number of people for booking"
    )

    special_requests: Optional[str] = Field(
        default=None,
        description="Special requests or notes"
    )

    # OTP/verification
    otp_code: Optional[str] = Field(
        default=None,
        description="OTP or verification code (4-6 digits)"
    )

    # Additional structured data
    raw_entities: Dict[str, Any] = Field(
        default_factory=dict,
        description="Raw entity data for any additional fields"
    )

    extraction_notes: Optional[str] = Field(
        default=None,
        description="Notes about entity extraction (ambiguities, assumptions)"
    )

    @field_validator('raw_entities', mode='before')
    @classmethod
    def validate_raw_entities(cls, v: Any) -> Dict[str, Any]:
        """Convert empty list to empty dict (LLM sometimes returns [] instead of {})."""
        if isinstance(v, list) and len(v) == 0:
            return {}
        if not isinstance(v, dict):
            return {}
        return v

    @field_validator('phone_number')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format."""
        if v is None:
            return v
        # Remove common separators
        cleaned = v.replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
        # Indian phone numbers are typically 10 digits
        if cleaned.isdigit() and len(cleaned) == 10:
            return cleaned
        return v  # Return as-is if not standard format

    @field_validator('otp_code')
    @classmethod
    def validate_otp(cls, v: Optional[str]) -> Optional[str]:
        """Validate OTP code format."""
        if v is None:
            return v
        # OTP should be 4-6 digits
        if v.isdigit() and 4 <= len(v) <= 6:
            return v
        return None  # Invalid OTP format


class FoodOrderingDecision(BaseModel):
    """
    Structured decision output for food ordering operations.

    Used by browse_menu, discover_items, manage_cart, etc.
    """
    action: Literal[
        "show_items",
        "add_to_cart",
        "remove_from_cart",
        "update_quantity",
        "show_cart",
        "validate_order",
        "proceed_to_checkout",
        "ask_for_clarification",
        "delegate_to_auth",
        "delegate_to_payment"
    ] = Field(description="Recommended action to take")

    items: List[str] = Field(
        default_factory=list,
        description="Menu item IDs or names"
    )

    reasoning: str = Field(
        description="Why this action was chosen"
    )

    requires_auth: bool = Field(
        default=False,
        description="Whether authentication is needed"
    )

    cart_operation: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Cart operation details (item_id, quantity, etc.)"
    )

    validation_issues: List[str] = Field(
        default_factory=list,
        description="Any validation problems found"
    )

    next_step: Optional[str] = Field(
        default=None,
        description="What should happen next"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for the decision"
    )

    @field_validator('cart_operation', mode='before')
    @classmethod
    def validate_cart_operation(cls, v: Any) -> Optional[Dict[str, Any]]:
        """Convert empty list to None (LLM sometimes returns [] instead of null)."""
        if v is None:
            return None
        if isinstance(v, list) and len(v) == 0:
            return None
        if not isinstance(v, dict):
            return None
        return v

    @field_validator('metadata', mode='before')
    @classmethod
    def validate_metadata(cls, v: Any) -> Dict[str, Any]:
        """Convert empty list to empty dict (LLM sometimes returns [] instead of {})."""
        if isinstance(v, list) and len(v) == 0:
            return {}
        if not isinstance(v, dict):
            return {}
        return v

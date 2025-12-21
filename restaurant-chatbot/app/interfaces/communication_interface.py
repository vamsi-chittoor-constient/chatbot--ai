"""
Communication Interface for Agent-to-Agent Communication
======================================================

Provides a standardized interface for all agents to communicate with the CommunicationAgent.
This interface ensures consistent communication patterns across the entire restaurant AI system.

Key Features:
- Type-safe communication methods
- Standardized notification types
- Error handling and fallbacks
- Dependency injection support
- Async communication patterns
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass


class CommunicationType(Enum):
    """Standard communication types used across all agents"""

    # Payment notifications
    PAYMENT_LINK = "payment_link"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILED = "payment_failed"
    PAYMENT_REMINDER = "payment_reminder"

    # Order notifications
    ORDER_CONFIRMATION = "order_confirmation"
    ORDER_READY = "order_ready"
    ORDER_DELIVERED = "order_delivered"
    ORDER_CANCELLED = "order_cancelled"

    # Booking notifications
    BOOKING_CONFIRMATION = "booking_confirmation"
    BOOKING_REMINDER = "booking_reminder"
    BOOKING_MODIFIED = "booking_modified"
    BOOKING_CANCELLED = "booking_cancelled"
    BOOKING_CANCELLATION = "booking_cancellation"  # Alias for backwards compatibility

    # Support/Complaint notifications
    COMPLAINT_ACKNOWLEDGED = "complaint_acknowledged"
    COMPLAINT_RESOLVED = "complaint_resolved"
    SUPPORT_FOLLOWUP = "support_followup"
    SUPPORT_ESCALATION = "support_escalation"

    # General notifications
    PROMOTIONAL_MESSAGE = "promotional_message"
    SYSTEM_NOTIFICATION = "system_notification"
    FEEDBACK_REQUEST = "feedback_request"
    GENERAL_NOTIFICATION = "general_notification"


@dataclass
class CommunicationRequest:
    """Standardized communication request structure"""

    user_id: str
    communication_type: CommunicationType
    template_params: Dict[str, Any]
    priority: str = "medium"  # low, medium, high, urgent
    preferred_channels: Optional[List[str]] = None
    retry_enabled: bool = True
    context: Optional[Dict[str, Any]] = None


@dataclass
class CommunicationResult:
    """Result of communication attempt"""

    success: bool
    channels_used: List[str]
    message_ids: Dict[str, str]  # channel -> message_id mapping
    error_message: Optional[str] = None
    retry_count: int = 0


class ICommunicationProvider(ABC):
    """
    Interface that all agents must implement to support communication.
    This allows for dependency injection of the CommunicationAgent.
    """

    @abstractmethod
    async def send_notification(
        self,
        request: CommunicationRequest
    ) -> CommunicationResult:
        """Send a notification through available channels"""
        pass

    @abstractmethod
    async def send_payment_notification(
        self,
        user_id: str,
        notification_type: str,
        **kwargs
    ) -> CommunicationResult:
        """Send payment-related notifications"""
        pass

    @abstractmethod
    async def send_order_notification(
        self,
        user_id: str,
        notification_type: str,
        **kwargs
    ) -> CommunicationResult:
        """Send order-related notifications"""
        pass

    @abstractmethod
    async def send_booking_notification(
        self,
        user_id: str,
        notification_type: str,
        **kwargs
    ) -> CommunicationResult:
        """Send booking-related notifications"""
        pass

    @abstractmethod
    async def send_support_notification(
        self,
        user_id: str,
        notification_type: str,
        **kwargs
    ) -> CommunicationResult:
        """Send support/complaint notifications"""
        pass


class AgentCommunicationMixin:
    """
    Mixin class that provides communication capabilities to any agent.

    Usage:
        class MyAgent(AgentCommunicationMixin):
            def __init__(self):
                super().__init__()
                # Agent-specific initialization

    The agent orchestrator will inject the communication_provider during initialization.
    """

    def __init__(self):
        self.communication_provider: Optional[ICommunicationProvider] = None

    def set_communication_provider(self, provider: ICommunicationProvider):
        """Inject the communication provider (typically CommunicationAgent)"""
        self.communication_provider = provider

    async def send_notification(
        self,
        user_id: str,
        communication_type: CommunicationType,
        template_params: Dict[str, Any],
        **kwargs
    ) -> CommunicationResult:
        """Send a generic notification"""

        if not self.communication_provider:
            return CommunicationResult(
                success=False,
                channels_used=[],
                message_ids={},
                error_message="No communication provider available"
            )

        request = CommunicationRequest(
            user_id=user_id,
            communication_type=communication_type,
            template_params=template_params,
            priority=kwargs.get("priority", "medium"),
            preferred_channels=kwargs.get("preferred_channels"),
            retry_enabled=kwargs.get("retry_enabled", True),
            context=kwargs.get("context")
        )

        return await self.communication_provider.send_notification(request)

    async def send_payment_notification(
        self,
        user_id: str,
        notification_type: str,
        **kwargs
    ) -> CommunicationResult:
        """Send payment-related notification"""

        if not self.communication_provider:
            return CommunicationResult(
                success=False,
                channels_used=[],
                message_ids={},
                error_message="No communication provider available"
            )

        return await self.communication_provider.send_payment_notification(
            user_id=user_id,
            notification_type=notification_type,
            **kwargs
        )

    async def send_order_notification(
        self,
        user_id: str,
        notification_type: str,
        **kwargs
    ) -> CommunicationResult:
        """Send order-related notification"""

        if not self.communication_provider:
            return CommunicationResult(
                success=False,
                channels_used=[],
                message_ids={},
                error_message="No communication provider available"
            )

        return await self.communication_provider.send_order_notification(
            user_id=user_id,
            notification_type=notification_type,
            **kwargs
        )

    async def send_booking_notification(
        self,
        user_id: str,
        notification_type: str,
        **kwargs
    ) -> CommunicationResult:
        """Send booking-related notification"""

        if not self.communication_provider:
            return CommunicationResult(
                success=False,
                channels_used=[],
                message_ids={},
                error_message="No communication provider available"
            )

        return await self.communication_provider.send_booking_notification(
            user_id=user_id,
            notification_type=notification_type,
            **kwargs
        )

    async def send_support_notification(
        self,
        user_id: str,
        notification_type: str,
        **kwargs
    ) -> CommunicationResult:
        """Send support/complaint notification"""

        if not self.communication_provider:
            return CommunicationResult(
                success=False,
                channels_used=[],
                message_ids={},
                error_message="No communication provider available"
            )

        return await self.communication_provider.send_support_notification(
            user_id=user_id,
            notification_type=notification_type,
            **kwargs
        )


# Template parameter constants for consistency across agents
class TemplateParams:
    """Standard template parameter names"""

    # Payment parameters
    ORDER_ID = "order_id"
    PAYMENT_LINK = "payment_link"
    AMOUNT = "amount"
    EXPIRY_MINUTES = "expiry_minutes"
    FAILURE_REASON = "failure_reason"

    # Order parameters
    ORDER_NUMBER = "order_number"
    TOTAL_AMOUNT = "total_amount"
    ESTIMATED_TIME = "estimated_time"
    PICKUP_INSTRUCTIONS = "pickup_instructions"
    DELIVERY_ADDRESS = "delivery_address"

    # Booking parameters
    GUEST_NAME = "guest_name"
    DATE = "date"
    TIME = "time"
    PARTY_SIZE = "party_size"
    CONFIRMATION_CODE = "confirmation_code"
    RESTAURANT_NAME = "restaurant_name"

    # Support parameters
    COMPLAINT_ID = "complaint_id"
    ISSUE_TYPE = "issue_type"
    RESOLUTION_DETAILS = "resolution_details"

    # General parameters
    USER_NAME = "user_name"
    PHONE_NUMBER = "phone_number"
    EMAIL = "email"


# Utility functions for building communication requests
def build_payment_request(
    user_id: str,
    order_id: str,
    payment_link: str,
    amount: str,
    expiry_minutes: str = "15"
) -> CommunicationRequest:
    """Build a payment link notification request"""

    return CommunicationRequest(
        user_id=user_id,
        communication_type=CommunicationType.PAYMENT_LINK,
        template_params={
            TemplateParams.ORDER_ID: order_id,
            TemplateParams.PAYMENT_LINK: payment_link,
            TemplateParams.AMOUNT: amount,
            TemplateParams.EXPIRY_MINUTES: expiry_minutes
        },
        priority="high"
    )


def build_order_confirmation_request(
    user_id: str,
    order_id: str,
    total_amount: str,
    estimated_time: str
) -> CommunicationRequest:
    """Build an order confirmation request"""

    return CommunicationRequest(
        user_id=user_id,
        communication_type=CommunicationType.ORDER_CONFIRMATION,
        template_params={
            TemplateParams.ORDER_ID: order_id,
            TemplateParams.TOTAL_AMOUNT: total_amount,
            TemplateParams.ESTIMATED_TIME: estimated_time
        },
        priority="medium"
    )


def build_booking_confirmation_request(
    user_id: str,
    guest_name: str,
    date: str,
    time: str,
    party_size: str,
    confirmation_code: str
) -> CommunicationRequest:
    """Build a booking confirmation request"""

    return CommunicationRequest(
        user_id=user_id,
        communication_type=CommunicationType.BOOKING_CONFIRMATION,
        template_params={
            TemplateParams.GUEST_NAME: guest_name,
            TemplateParams.DATE: date,
            TemplateParams.TIME: time,
            TemplateParams.PARTY_SIZE: party_size,
            TemplateParams.CONFIRMATION_CODE: confirmation_code
        },
        priority="medium"
    )

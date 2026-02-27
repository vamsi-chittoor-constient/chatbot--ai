"""
Unified Communication Service
============================

Orchestrates omnichannel communication across SMS, Email, and WhatsApp.
Provides intelligent channel selection, delivery tracking, and fallback strategies.

Features:
- Multi-channel message delivery
- Intelligent channel prioritization
- Delivery failure handling with fallbacks
- Template management across channels
- Delivery status tracking and analytics
- User preference management
"""

import os
import asyncio
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from app.tools.external_apis.whatsapp_tools import WhatsAppBusinessTool, WhatsAppTemplateManager
from app.tools.external_apis.notification_tools import SendSMSConfirmationTool, SendEmailConfirmationTool
from app.core.database import get_db_session
from app.shared.models import User
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class CommunicationChannel(Enum):
    """Available communication channels"""
    WHATSAPP = "whatsapp"
    SMS = "sms"
    EMAIL = "email"
    CHAT = "chat"  # In-app chat


class MessagePriority(Enum):
    """Message priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class DeliveryStatus(Enum):
    """Message delivery status"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass
class CommunicationMessage:
    """Unified message structure for all channels"""
    recipient_id: str  # User ID or phone/email
    message_type: str  # payment_link, booking_confirmation, order_update, etc.
    content: str
    priority: MessagePriority = MessagePriority.MEDIUM
    preferred_channels: Optional[List[CommunicationChannel]] = None
    template_name: Optional[str] = None
    template_params: Optional[Dict[str, Any]] = None
    media_url: Optional[str] = None
    fallback_enabled: bool = True
    retry_count: int = 0
    max_retries: int = 3
    session_id: Optional[str] = None


@dataclass
class DeliveryResult:
    """Result of message delivery attempt"""
    channel: CommunicationChannel
    status: DeliveryStatus
    message_id: Optional[str] = None
    error_message: Optional[str] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class CommunicationService:
    """
    Unified communication service for omnichannel messaging.
    Handles routing, delivery, and fallback strategies.
    """

    def __init__(self):
        self.service_name = "CommunicationService"

        # Initialize channel tools
        self.whatsapp_tool = WhatsAppBusinessTool()
        self.sms_tool = SendSMSConfirmationTool()
        self.email_tool = SendEmailConfirmationTool()
        self.template_manager = WhatsAppTemplateManager()

        # Channel priority configuration
        self.default_channel_priority = [
            CommunicationChannel.WHATSAPP,
            CommunicationChannel.SMS,
            CommunicationChannel.EMAIL
        ]

        # Message type to template mapping
        self.message_templates = {
            "payment_link": {
                "whatsapp": "payment_link",
                "sms": "Your order #{order_id} payment link: {payment_link}. Valid for {expiry_minutes} minutes.",
                "email": "payment_link_email"
            },
            "payment_success": {
                "whatsapp": "payment_success",
                "sms": "Payment successful! Your order #{order_id} is confirmed for ₹{amount}.",
                "email": "payment_success_email"
            },
            "payment_failed": {
                "whatsapp": "payment_failed",
                "sms": "Payment failed for order #{order_id}. {failure_reason}. Please try again.",
                "email": "payment_failed_email"
            },
            "booking_confirmation": {
                "whatsapp": "booking_confirmation",
                "sms": "Hi {guest_name}! Your table for {party_size} is confirmed on {date} at {time}. Confirmation: {confirmation_code}",
                "email": "booking_confirmation_email"
            },
            "order_ready": {
                "whatsapp": "order_ready",
                "sms": "Your order #{order_id} is ready for pickup! {pickup_instructions}",
                "email": "order_ready_email"
            }
        }

    async def send_message(self, message: CommunicationMessage) -> List[DeliveryResult]:
        """
        Send message via optimal channel(s) with fallback strategy
        """
        results = []

        # Get user preferences and contact info
        user_info = await self._get_user_contact_info(message.recipient_id)
        if not user_info:
            return [DeliveryResult(
                channel=CommunicationChannel.CHAT,
                status=DeliveryStatus.FAILED,
                error_message="User not found"
            )]

        # Determine channels to try
        channels_to_try = await self._determine_channels(message, user_info)

        # Attempt delivery on each channel
        for channel in channels_to_try:
            try:
                result = await self._send_via_channel(channel, message, user_info)
                results.append(result)

                # If successful and not urgent, stop trying other channels
                if result.status in [DeliveryStatus.SENT, DeliveryStatus.DELIVERED]:
                    if message.priority != MessagePriority.URGENT:
                        break

            except Exception as e:
                logger.error(f"Error sending via {channel.value}: {str(e)}")
                results.append(DeliveryResult(
                    channel=channel,
                    status=DeliveryStatus.FAILED,
                    error_message=str(e)
                ))

        return results

    async def send_payment_notification(
        self,
        user_id: str,
        notification_type: str,
        **kwargs
    ) -> List[DeliveryResult]:
        """Send payment-related notifications"""

        # Build message based on notification type
        if notification_type == "payment_link":
            message = CommunicationMessage(
                recipient_id=user_id,
                message_type="payment_link",
                content=f"Payment link for order #{kwargs.get('order_id')}",
                priority=MessagePriority.HIGH,
                template_params=kwargs
            )

        elif notification_type == "payment_success":
            message = CommunicationMessage(
                recipient_id=user_id,
                message_type="payment_success",
                content=f"Payment confirmed for order #{kwargs.get('order_id')}",
                priority=MessagePriority.MEDIUM,
                template_params=kwargs
            )

        elif notification_type == "payment_failed":
            message = CommunicationMessage(
                recipient_id=user_id,
                message_type="payment_failed",
                content=f"Payment failed for order #{kwargs.get('order_id')}",
                priority=MessagePriority.HIGH,
                template_params=kwargs
            )

        else:
            return [DeliveryResult(
                channel=CommunicationChannel.CHAT,
                status=DeliveryStatus.FAILED,
                error_message=f"Unknown notification type: {notification_type}"
            )]

        return await self.send_message(message)

    async def send_booking_notification(
        self,
        user_id: str,
        notification_type: str,
        **kwargs
    ) -> List[DeliveryResult]:
        """Send booking-related notifications"""

        if notification_type == "confirmation":
            message = CommunicationMessage(
                recipient_id=user_id,
                message_type="booking_confirmation",
                content=f"Booking confirmed for {kwargs.get('date')}",
                priority=MessagePriority.MEDIUM,
                template_params=kwargs
            )

        elif notification_type == "reminder":
            message = CommunicationMessage(
                recipient_id=user_id,
                message_type="booking_reminder",
                content=f"Reminder: Your table is booked for {kwargs.get('date')}",
                priority=MessagePriority.LOW,
                template_params=kwargs
            )

        else:
            return [DeliveryResult(
                channel=CommunicationChannel.CHAT,
                status=DeliveryStatus.FAILED,
                error_message=f"Unknown booking notification type: {notification_type}"
            )]

        return await self.send_message(message)

    async def _determine_channels(
        self,
        message: CommunicationMessage,
        user_info: Dict[str, Any]
    ) -> List[CommunicationChannel]:
        """Determine which channels to use for message delivery"""

        available_channels = []

        # Check user preferences if specified
        if message.preferred_channels:
            for channel in message.preferred_channels:
                if await self._is_channel_available(channel, user_info):
                    available_channels.append(channel)

        # Use default priority if no preferences or no available preferred channels
        if not available_channels:
            for channel in self.default_channel_priority:
                if await self._is_channel_available(channel, user_info):
                    available_channels.append(channel)

        # Always ensure at least one channel (fallback to chat)
        if not available_channels:
            available_channels.append(CommunicationChannel.CHAT)

        return available_channels

    async def _is_channel_available(
        self,
        channel: CommunicationChannel,
        user_info: Dict[str, Any]
    ) -> bool:
        """Check if a communication channel is available for the user"""

        if channel == CommunicationChannel.WHATSAPP:
            return bool(user_info.get("phone_number") and self.whatsapp_tool.api_token)

        elif channel == CommunicationChannel.SMS:
            return user_info.get("phone_number") is not None

        elif channel == CommunicationChannel.EMAIL:
            return user_info.get("email") is not None

        elif channel == CommunicationChannel.CHAT:
            return True  # Always available

        return False

    async def _send_via_channel(
        self,
        channel: CommunicationChannel,
        message: CommunicationMessage,
        user_info: Dict[str, Any]
    ) -> DeliveryResult:
        """Send message via specific channel"""

        try:
            if channel == CommunicationChannel.WHATSAPP:
                return await self._send_whatsapp_message(message, user_info)

            elif channel == CommunicationChannel.SMS:
                return await self._send_sms_message(message, user_info)

            elif channel == CommunicationChannel.EMAIL:
                return await self._send_email_message(message, user_info)

            elif channel == CommunicationChannel.CHAT:
                return await self._send_chat_message(message, user_info)

            else:
                return DeliveryResult(
                    channel=channel,
                    status=DeliveryStatus.FAILED,
                    error_message="Unsupported channel"
                )

        except Exception as e:
            return DeliveryResult(
                channel=channel,
                status=DeliveryStatus.FAILED,
                error_message=str(e)
            )

    async def _send_whatsapp_message(
        self,
        message: CommunicationMessage,
        user_info: Dict[str, Any]
    ) -> DeliveryResult:
        """Send message via WhatsApp"""

        phone_number = user_info.get("phone_number")
        if not phone_number:
            return DeliveryResult(
                channel=CommunicationChannel.WHATSAPP,
                status=DeliveryStatus.FAILED,
                error_message="No phone number available"
            )

        # Check if we should use template or text message
        template_name = self.message_templates.get(message.message_type, {}).get("whatsapp")

        if template_name and message.template_params:
            # Send template message
            template_def = self.template_manager.get_template(template_name)
            template_params = [
                str(message.template_params.get(param, ""))
                for param in (template_def.get("params", []) if template_def else [])
            ]

            result = await self.whatsapp_tool._execute_impl(
                operation="send_template",
                to=phone_number,
                template_name=template_name,
                template_params=template_params
            )
        else:
            # Send text message
            formatted_content = self._format_message_content(
                message.message_type, "whatsapp", message.template_params or {}
            )

            result = await self.whatsapp_tool._execute_impl(
                operation="send_text",
                to=phone_number,
                message=formatted_content or message.content
            )

        if result.status.value == "success":
            return DeliveryResult(
                channel=CommunicationChannel.WHATSAPP,
                status=DeliveryStatus.SENT,
                message_id=result.data.get("message_id")
            )
        else:
            return DeliveryResult(
                channel=CommunicationChannel.WHATSAPP,
                status=DeliveryStatus.FAILED,
                error_message=result.data.get("error", "WhatsApp delivery failed")
            )

    async def _send_sms_message(
        self,
        message: CommunicationMessage,
        user_info: Dict[str, Any]
    ) -> DeliveryResult:
        """Send message via SMS"""

        phone_number = user_info.get("phone_number")
        if not phone_number:
            return DeliveryResult(
                channel=CommunicationChannel.SMS,
                status=DeliveryStatus.FAILED,
                error_message="No phone number available"
            )

        # Format message content
        formatted_content = self._format_message_content(
            message.message_type, "sms", message.template_params or {}
        )

        # Send SMS via Twilio
        try:
            from app.tools.external_apis.notification_tools import SendSMSConfirmationTool
            sms_tool = SendSMSConfirmationTool()

            # Use the Twilio SMS method directly
            success = await sms_tool._send_sms_twilio(
                phone_number=phone_number,
                message=formatted_content or message.content
            )

            if success:
                return DeliveryResult(
                    channel=CommunicationChannel.SMS,
                    status=DeliveryStatus.SENT,
                    message_id=f"sms_{datetime.now().timestamp()}"
                )
            else:
                return DeliveryResult(
                    channel=CommunicationChannel.SMS,
                    status=DeliveryStatus.FAILED,
                    error_message="SMS delivery failed"
                )
        except Exception as e:
            return DeliveryResult(
                channel=CommunicationChannel.SMS,
                status=DeliveryStatus.FAILED,
                error_message=f"SMS service error: {str(e)}"
            )

    async def _send_email_message(
        self,
        message: CommunicationMessage,
        user_info: Dict[str, Any]
    ) -> DeliveryResult:
        """Send message via Email"""

        email = user_info.get("email")
        if not email:
            return DeliveryResult(
                channel=CommunicationChannel.EMAIL,
                status=DeliveryStatus.FAILED,
                error_message="No email address available"
            )

        # Format message content
        formatted_content = self._format_message_content(
            message.message_type, "email", message.template_params or {}
        )

        # Send email via AWS SES
        try:
            from app.tools.external_apis.notification_tools import SendEmailConfirmationTool
            email_tool = SendEmailConfirmationTool()

            # Create subject and body
            subject = f"Notification - {message.message_type.replace('_', ' ').title()}"
            body = formatted_content or message.content

            # Use the AWS SES method directly
            success = await email_tool._send_email_ses(
                to_email=email,
                subject=subject,
                body=body
            )

            if success:
                return DeliveryResult(
                    channel=CommunicationChannel.EMAIL,
                    status=DeliveryStatus.SENT,
                    message_id=f"email_{datetime.now().timestamp()}"
                )
            else:
                return DeliveryResult(
                    channel=CommunicationChannel.EMAIL,
                    status=DeliveryStatus.FAILED,
                    error_message="Email delivery failed"
                )
        except Exception as e:
            return DeliveryResult(
                channel=CommunicationChannel.EMAIL,
                status=DeliveryStatus.FAILED,
                error_message=f"Email service error: {str(e)}"
            )

    async def _send_chat_message(
        self,
        message: CommunicationMessage,
        user_info: Dict[str, Any]
    ) -> DeliveryResult:
        """Send message via in-app chat (WebSocket)"""

        try:
            # Format message content
            formatted_content = self._format_message_content(
                message.message_type, "chat", message.template_params or {}
            )

            # Try to find active WebSocket session for user
            from app.api.routes.chat import websocket_manager
            from app.services.session_manager import get_session_manager

            # Get active session for this user
            session_manager = get_session_manager()
            
            target_sessions = []
            if message.session_id:
                # Target specific session if provided
                target_sessions = [message.session_id]
            else:
                # Broadcast to all active sessions (legacy behavior / fallback)
                target_sessions = await session_manager.get_user_sessions(message.recipient_id)

            message_sent = False
            for session_id in target_sessions:
                if session_id in websocket_manager.active_connections:
                    # Send real-time notification via WebSocket
                    await websocket_manager.send_message_with_metadata(
                        session_id=session_id,
                        message=formatted_content or message.content,
                        message_type="notification",
                        metadata={
                            "notification_type": message.message_type,
                            "priority": message.priority.value,
                            "template_params": message.template_params or {}
                        }
                    )
                    message_sent = True
                    # If targeting a specific session, we're done.
                    # If broadcasting (target_sessions list), we might want to send to all?
                    # The original behavior was "break" (send to first). 
                    # For leakage prevention: if we are broadcasting, "break" is safer (only one device gets it).
                    # But ideally notifications (like "Order Ready") should go to all.
                    # For now, keeping "break" to minimize change impact, but respecting targeted session.
                    break

            if message_sent:
                return DeliveryResult(
                    channel=CommunicationChannel.CHAT,
                    status=DeliveryStatus.DELIVERED,
                    message_id=f"chat_{datetime.now().timestamp()}"
                )
            else:
                # No active WebSocket connection found
                return DeliveryResult(
                    channel=CommunicationChannel.CHAT,
                    status=DeliveryStatus.FAILED,
                    error_message="No active chat session found"
                )

        except Exception as e:
            return DeliveryResult(
                channel=CommunicationChannel.CHAT,
                status=DeliveryStatus.FAILED,
                error_message=f"Chat delivery error: {str(e)}"
            )

    def _format_message_content(
        self,
        message_type: str,
        channel: str,
        template_params: Dict[str, Any]
    ) -> Optional[str]:
        """Format message content using templates and parameters"""

        template = self.message_templates.get(message_type, {}).get(channel)
        if not template or not template_params:
            return None

        try:
            return template.format(**template_params)
        except KeyError as e:
            logger.warning(f"Missing template parameter {e} for {message_type}")
            return template  # Return unformatted template

    async def _get_user_contact_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user contact information from database"""

        try:
            async with get_db_session() as session:
                from sqlalchemy import select

                user_query = select(User).where(User.id == user_id)
                result = await session.execute(user_query)
                user = result.scalar_one_or_none()

                if user:
                    return {
                        "user_id": user.id,
                        "phone_number": user.phone_number,
                        "email": user.email,
                        "full_name": user.full_name,
                        "communication_preferences": {}  # Could be extended
                    }

                return None

        except Exception as e:
            logger.error(f"Error fetching user contact info: {str(e)}")
            return None


# Initialize service for easy import
communication_service = CommunicationService()

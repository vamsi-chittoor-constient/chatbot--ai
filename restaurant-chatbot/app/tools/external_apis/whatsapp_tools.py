"""
WhatsApp Business API Tools
===========================

WhatsApp Business API integration for omnichannel communication:
- Message sending via WhatsApp Business API
- Template message support
- Delivery status tracking
- Media message support
- Interactive message capabilities

Built for restaurant AI assistant notifications and customer communication.
"""

import os
import requests
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass

from app.tools.base.tool_base import ToolBase, ToolResult, ToolStatus
from app.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class WhatsAppMessage:
    """Structured WhatsApp message data"""
    to: str  # Phone number in international format
    message_type: str  # text, template, media, interactive
    content: str
    template_name: Optional[str] = None
    template_params: Optional[List[str]] = None
    media_url: Optional[str] = None
    media_type: Optional[str] = None  # image, document, video, audio


@dataclass
class WhatsAppResponse:
    """WhatsApp API response structure"""
    success: bool
    message_id: Optional[str] = None
    status: Optional[str] = None
    error_message: Optional[str] = None
    delivery_status: Optional[str] = None


class WhatsAppBusinessTool(ToolBase):
    """
    WhatsApp Business API tool for sending messages and notifications.
    Supports text, template, and media messages with delivery tracking.
    """

    def __init__(self):
        super().__init__(
            name="whatsapp_business",
            description="Send WhatsApp messages via Business API"
        )

        # WhatsApp Business API configuration
        self.api_token = os.getenv("WHATSAPP_API_TOKEN")
        self.phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        self.business_account_id = os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID")

        # API endpoints
        self.base_url = f"https://graph.facebook.com/v18.0/{self.phone_number_id}"
        self.messages_url = f"{self.base_url}/messages"

        # Request headers
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

    async def _execute_impl(self, **kwargs) -> ToolResult:
        """
        Execute WhatsApp operations

        Operations:
        - send_text: Send text message
        - send_template: Send template message
        - send_media: Send media message
        - get_status: Get message delivery status
        """
        operation = kwargs.get("operation")

        try:
            if operation == "send_text":
                return await self._send_text_message(kwargs)

            elif operation == "send_template":
                return await self._send_template_message(kwargs)

            elif operation == "send_media":
                return await self._send_media_message(kwargs)

            elif operation == "get_status":
                return await self._get_message_status(kwargs)

            else:
                return ToolResult(
                    status=ToolStatus.FAILURE,
                    data={"error": f"Unknown operation: {operation}"}
                )

        except Exception as e:
            logger.error(f"WhatsAppBusinessTool error: {str(e)}")
            return ToolResult(
                status=ToolStatus.FAILURE,
                data={"error": f"WhatsApp operation failed: {str(e)}"}
            )

    async def _send_text_message(self, params: Dict[str, Any]) -> ToolResult:
        """Send a text message via WhatsApp"""
        to = params.get("to")
        message = params.get("message")

        if not to or not message:
            return ToolResult(
                status=ToolStatus.FAILURE,
                data={"error": "Both 'to' and 'message' are required"}
            )

        # Format phone number (ensure international format)
        formatted_phone = self._format_phone_number(to)

        payload = {
            "messaging_product": "whatsapp",
            "to": formatted_phone,
            "type": "text",
            "text": {
                "body": message
            }
        }

        try:
            response = requests.post(
                self.messages_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                message_id = result.get("messages", [{}])[0].get("id")

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={
                        "message_id": message_id,
                        "status": "sent",
                        "to": formatted_phone,
                        "message": message,
                        "timestamp": datetime.now().isoformat()
                    }
                )
            else:
                error_data = response.json() if response.content else {}
                return ToolResult(
                    status=ToolStatus.FAILURE,
                    data={
                        "error": f"WhatsApp API error: {response.status_code}",
                        "details": error_data
                    }
                )

        except requests.exceptions.RequestException as e:
            return ToolResult(
                status=ToolStatus.FAILURE,
                data={"error": f"Network error: {str(e)}"}
            )

    async def _send_template_message(self, params: Dict[str, Any]) -> ToolResult:
        """Send a template message via WhatsApp"""
        to = params.get("to")
        template_name = params.get("template_name")
        template_params = params.get("template_params", [])

        if not to or not template_name:
            return ToolResult(
                status=ToolStatus.FAILURE,
                data={"error": "'to' and 'template_name' are required"}
            )

        formatted_phone = self._format_phone_number(to)

        # Build template parameters
        components = []
        if template_params:
            parameters = [{"type": "text", "text": param} for param in template_params]
            components.append({
                "type": "body",
                "parameters": parameters
            })

        payload = {
            "messaging_product": "whatsapp",
            "to": formatted_phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": "en"  # Can be made configurable
                },
                "components": components
            }
        }

        try:
            response = requests.post(
                self.messages_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                message_id = result.get("messages", [{}])[0].get("id")

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={
                        "message_id": message_id,
                        "status": "sent",
                        "to": formatted_phone,
                        "template_name": template_name,
                        "template_params": template_params,
                        "timestamp": datetime.now().isoformat()
                    }
                )
            else:
                error_data = response.json() if response.content else {}
                return ToolResult(
                    status=ToolStatus.FAILURE,
                    data={
                        "error": f"WhatsApp template API error: {response.status_code}",
                        "details": error_data
                    }
                )

        except requests.exceptions.RequestException as e:
            return ToolResult(
                status=ToolStatus.FAILURE,
                data={"error": f"Network error: {str(e)}"}
            )

    async def _send_media_message(self, params: Dict[str, Any]) -> ToolResult:
        """Send a media message via WhatsApp"""
        to = params.get("to")
        media_url = params.get("media_url")
        media_type = params.get("media_type", "image")  # image, document, video, audio
        caption = params.get("caption", "")

        if not to or not media_url:
            return ToolResult(
                status=ToolStatus.FAILURE,
                data={"error": "'to' and 'media_url' are required"}
            )

        formatted_phone = self._format_phone_number(to)

        # Build media payload based on type
        media_object = {
            "link": media_url
        }

        if caption and media_type in ["image", "video"]:
            media_object["caption"] = caption

        payload = {
            "messaging_product": "whatsapp",
            "to": formatted_phone,
            "type": media_type,
            media_type: media_object
        }

        try:
            response = requests.post(
                self.messages_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                message_id = result.get("messages", [{}])[0].get("id")

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={
                        "message_id": message_id,
                        "status": "sent",
                        "to": formatted_phone,
                        "media_type": media_type,
                        "media_url": media_url,
                        "caption": caption,
                        "timestamp": datetime.now().isoformat()
                    }
                )
            else:
                error_data = response.json() if response.content else {}
                return ToolResult(
                    status=ToolStatus.FAILURE,
                    data={
                        "error": f"WhatsApp media API error: {response.status_code}",
                        "details": error_data
                    }
                )

        except requests.exceptions.RequestException as e:
            return ToolResult(
                status=ToolStatus.FAILURE,
                data={"error": f"Network error: {str(e)}"}
            )

    async def _get_message_status(self, params: Dict[str, Any]) -> ToolResult:
        """Get message delivery status"""
        message_id = params.get("message_id")

        if not message_id:
            return ToolResult(
                status=ToolStatus.FAILURE,
                data={"error": "message_id is required"}
            )

        # Note: WhatsApp Business API doesn't have direct status endpoint
        # Status updates come via webhooks. This is a placeholder for future implementation
        return ToolResult(
            status=ToolStatus.SUCCESS,
            data={
                "message_id": message_id,
                "status": "unknown",
                "note": "Status tracking requires webhook implementation"
            }
        )

    def _format_phone_number(self, phone: str) -> str:
        """Format phone number to international format without + sign"""
        # Remove any non-numeric characters except +
        cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')

        # Remove + if present
        if cleaned.startswith('+'):
            cleaned = cleaned[1:]

        # Add country code if missing (assuming India +91 as default)
        if len(cleaned) == 10:  # Indian mobile number without country code
            cleaned = f"91{cleaned}"

        return cleaned

    def _validate_phone_number(self, phone: str) -> bool:
        """Validate phone number format"""
        formatted = self._format_phone_number(phone)

        # Check if it's a valid length (minimum 10 digits, maximum 15)
        if len(formatted) < 10 or len(formatted) > 15:
            return False

        # Check if all characters are digits
        return formatted.isdigit()


class WhatsAppTemplateManager:
    """
    Manages WhatsApp Business API approved templates.
    Templates must be pre-approved by WhatsApp before use.
    """

    def __init__(self):
        self.templates = {
            # Payment Templates
            "payment_link": {
                "name": "payment_link",
                "params": ["order_id", "payment_link", "amount", "expiry_time"]
            },
            "payment_success": {
                "name": "payment_success",
                "params": ["order_id", "amount"]
            },
            "payment_failed": {
                "name": "payment_failed",
                "params": ["order_id", "failure_reason"]
            },

            # Booking Templates
            "booking_confirmation": {
                "name": "booking_confirmation",
                "params": ["guest_name", "date", "time", "party_size", "confirmation_code"]
            },
            "booking_reminder": {
                "name": "booking_reminder",
                "params": ["guest_name", "date", "time", "restaurant_name"]
            },

            # Order Templates
            "order_confirmation": {
                "name": "order_confirmation",
                "params": ["order_id", "total_amount", "estimated_time"]
            },
            "order_ready": {
                "name": "order_ready",
                "params": ["order_id", "pickup_instructions"]
            }
        }

    def get_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get template configuration by name"""
        return self.templates.get(template_name)

    def get_available_templates(self) -> List[str]:
        """Get list of available template names"""
        return list(self.templates.keys())

    def validate_template_params(self, template_name: str, params: List[str]) -> bool:
        """Validate that provided parameters match template requirements"""
        template = self.get_template(template_name)
        if not template:
            return False

        required_params = template.get("params", [])
        return len(params) == len(required_params)


# Initialize tools for easy import
whatsapp_business_tool = WhatsAppBusinessTool()
whatsapp_template_manager = WhatsAppTemplateManager()

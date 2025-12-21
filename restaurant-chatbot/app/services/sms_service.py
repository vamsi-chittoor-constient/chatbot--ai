"""
SMS Service using Twilio API (with Mock Mode Support)

This module handles SMS operations including OTP sending and delivery confirmation.
Integrates with Twilio's REST API for reliable SMS delivery.
Falls back to mock mode when Twilio is not available (for testing).
"""

import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv

from app.core.logging_config import get_logger

# Load environment variables
load_dotenv()

logger = get_logger(__name__)

# Try to import Twilio - if not available, use mock mode
try:
    from twilio.rest import Client
    from twilio.base.exceptions import TwilioException
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    Client = None
    TwilioException = Exception
    logger.warning("Twilio not installed - SMS service will run in MOCK mode")


class MockSMSService:
    """
    Mock SMS Service for testing without Twilio.

    Logs OTP codes to console instead of sending real SMS.
    OTPs can be verified using the test code from config (default: 123456).
    """

    def __init__(self):
        logger.info("Mock SMS service initialized (Twilio not available)")

    async def send_otp(
        self,
        phone_number: str,
        otp_code: str,
        purpose: str = "verification",
        restaurant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Mock OTP sending - logs to console instead of sending SMS.
        """
        logger.info(
            "=== MOCK OTP SMS ===",
            phone_number=phone_number,
            otp_code=otp_code,
            purpose=purpose
        )
        print(f"\n{'='*50}")
        print(f"MOCK SMS OTP for {phone_number}")
        print(f"OTP Code: {otp_code}")
        print(f"Purpose: {purpose}")
        print(f"(For testing, use OTP: 123456)")
        print(f"{'='*50}\n")

        return {
            "success": True,
            "message_sid": f"MOCK_{phone_number}_{otp_code}",
            "status": "mock_sent",
            "phone_number": phone_number,
            "purpose": purpose,
            "error": None,
            "mock_mode": True
        }

    async def send_notification(
        self,
        phone_number: str,
        message: str,
        notification_type: str = "order_update"
    ) -> Dict[str, Any]:
        """Mock notification sending - logs to console."""
        logger.info(
            "=== MOCK SMS NOTIFICATION ===",
            phone_number=phone_number,
            notification_type=notification_type,
            message=message[:50] + "..." if len(message) > 50 else message
        )

        return {
            "success": True,
            "message_sid": f"MOCK_NOTIF_{phone_number}",
            "status": "mock_sent",
            "phone_number": phone_number,
            "notification_type": notification_type,
            "error": None,
            "mock_mode": True
        }

    def check_delivery_status(self, message_sid: str) -> Dict[str, Any]:
        """Mock delivery status check."""
        return {
            "success": True,
            "message_sid": message_sid,
            "status": "delivered" if message_sid.startswith("MOCK_") else "unknown",
            "error_code": None,
            "error_message": None,
            "mock_mode": True
        }


class SMSService:
    """
    SMS Service for sending text messages via Twilio

    Handles OTP delivery, promotional messages, and order notifications.
    """

    def __init__(self):
        """Initialize Twilio client with credentials from environment"""
        self.account_sid: Optional[str] = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token: Optional[str] = os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number: Optional[str] = os.getenv('TWILIO_PHONE_NUMBER')

        # Validate required credentials
        if not all([self.account_sid, self.auth_token, self.from_number]):
            missing = []
            if not self.account_sid: missing.append('TWILIO_ACCOUNT_SID')
            if not self.auth_token: missing.append('TWILIO_AUTH_TOKEN')
            if not self.from_number: missing.append('TWILIO_PHONE_NUMBER')

            raise ValueError(f"Missing Twilio credentials in environment: {', '.join(missing)}")

        # Initialize Twilio client
        try:
            self.client = Client(self.account_sid, self.auth_token)
            logger.info("Twilio SMS service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Twilio client: {str(e)}")
            raise

    async def send_otp(
        self,
        phone_number: str,
        otp_code: str,
        purpose: str = "verification",
        restaurant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send OTP via SMS to the specified phone number

        Args:
            phone_number: Target phone number in E.164 format (+1234567890)
            otp_code: 6-digit OTP code to send
            purpose: Purpose of the OTP (verification, reset, etc.)
            restaurant_id: Restaurant ID for multi-tenant support (optional)

        Returns:
            Dict containing delivery status and metadata
        """
        try:
            # Create message content based on purpose (multi-tenant support)
            message_content = await self._create_otp_message(otp_code, purpose, restaurant_id)

            # Format phone number with country code (E.164 format)
            formatted_phone = self._format_phone_number(phone_number)

            # DEBUG: Log the phone number being sent to
            logger.info(f"SENDING OTP - To: {formatted_phone}, From: {self.from_number}, Purpose: {purpose}")

            # Send SMS via Twilio
            message = self.client.messages.create(
                body=message_content,
                from_=self.from_number,
                to=formatted_phone
            )

            logger.info("OTP SMS sent successfully",
                phone_number=phone_number[-4:],  # Log only last 4 digits for privacy
                message_sid=message.sid,
                purpose=purpose,
                status=message.status
            )

            return {
                "success": True,
                "message_sid": message.sid,
                "status": message.status,
                "phone_number": phone_number,
                "purpose": purpose,
                "error": None
            }

        except TwilioException as e:
            error_code = getattr(e, 'code', 'unknown_error')
            logger.error("Twilio SMS delivery failed",
                phone_number=phone_number[-4:],
                error_code=error_code,
                error_message=str(e),
                purpose=purpose
            )

            return {
                "success": False,
                "message_sid": None,
                "status": "failed",
                "phone_number": phone_number,
                "purpose": purpose,
                "error": {
                    "code": error_code,
                    "message": str(e)
                }
            }

        except Exception as e:
            logger.error("Unexpected error sending OTP SMS",
                phone_number=phone_number[-4:],
                error=str(e),
                purpose=purpose
            )

            return {
                "success": False,
                "message_sid": None,
                "status": "failed",
                "phone_number": phone_number,
                "purpose": purpose,
                "error": {
                    "code": "unknown_error",
                    "message": str(e)
                }
            }

    async def send_notification(self, phone_number: str, message: str, notification_type: str = "order_update") -> Dict[str, Any]:
        """
        Send general notification SMS

        Args:
            phone_number: Target phone number
            message: Message content to send
            notification_type: Type of notification (order_update, booking_reminder, etc.)

        Returns:
            Dict containing delivery status and metadata
        """
        try:
            # Format phone number with country code (E.164 format)
            formatted_phone = self._format_phone_number(phone_number)

            # DEBUG: Log the phone number being sent to
            logger.info(f"SENDING SMS - To: {formatted_phone}, From: {self.from_number}, Type: {notification_type}")

            # Send SMS via Twilio
            twilio_message = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=formatted_phone
            )

            logger.info("Notification SMS sent successfully",
                phone_number=phone_number[-4:],
                message_sid=twilio_message.sid,
                notification_type=notification_type,
                status=twilio_message.status
            )

            return {
                "success": True,
                "message_sid": twilio_message.sid,
                "status": twilio_message.status,
                "phone_number": phone_number,
                "notification_type": notification_type,
                "error": None
            }

        except TwilioException as e:
            error_code = getattr(e, 'code', 'unknown_error')
            logger.error("Twilio notification SMS failed",
                phone_number=phone_number[-4:],
                error_code=error_code,
                error_message=str(e),
                notification_type=notification_type
            )

            return {
                "success": False,
                "message_sid": None,
                "status": "failed",
                "phone_number": phone_number,
                "notification_type": notification_type,
                "error": {
                    "code": error_code,
                    "message": str(e)
                }
            }

    def _format_phone_number(self, phone_number: str) -> str:
        """
        Format phone number to E.164 format with proper country code.

        Args:
            phone_number: Phone number (may or may not have country code)

        Returns:
            Phone number in E.164 format (e.g., +919566070120)
        """
        # Remove any whitespace, dashes, or parentheses
        clean_number = ''.join(filter(str.isdigit, phone_number))

        # If already has country code (starts with country code)
        if phone_number.startswith('+'):
            return phone_number

        # If number starts with 91 (India country code), add +
        if clean_number.startswith('91') and len(clean_number) == 12:
            return f'+{clean_number}'

        # If it's a 10-digit Indian number (starts with 6-9), add +91
        if len(clean_number) == 10 and clean_number[0] in ['6', '7', '8', '9']:
            return f'+91{clean_number}'

        # If it's an 11-digit number starting with 1 (US), add +
        if clean_number.startswith('1') and len(clean_number) == 11:
            return f'+{clean_number}'

        # Default: assume Indian number and add +91
        logger.warning(f"Uncertain phone format, assuming Indian number: {phone_number}")
        return f'+91{clean_number}'

    async def _create_otp_message(
        self,
        otp_code: str,
        purpose: str,
        restaurant_id: Optional[str] = None
    ) -> str:
        """
        Create formatted OTP message content

        Args:
            otp_code: 6-digit OTP code
            purpose: Purpose of the OTP
            restaurant_id: Restaurant ID for multi-tenant branding (optional)

        Returns:
            Formatted SMS message content
        """
        purpose_texts = {
            "phone_verification": "phone number verification",
            "password_reset": "password reset",
            "login": "login authentication",
            "account_verification": "account verification",
            "order_confirmation": "order confirmation"
        }

        purpose_text = purpose_texts.get(purpose, "verification")

        # Get restaurant name for branding (multi-tenant support)
        restaurant_name = await self._get_restaurant_name(restaurant_id)

        # Create message with restaurant branding
        message = f"Your {restaurant_name} verification code is: {otp_code}\n\n"
        message += f"This code is for {purpose_text} and expires in 10 minutes.\n"
        message += "Do not share this code with anyone."

        return message

    async def _get_restaurant_name(self, restaurant_id: Optional[str] = None) -> str:
        """
        Get restaurant name from cache for multi-tenant branding.

        Uses restaurant_config_cache for fast lookups with database fallback.

        Args:
            restaurant_id: Restaurant ID

        Returns:
            Restaurant name or default name
        """
        if restaurant_id:
            try:
                from app.services.restaurant_cache_service import get_restaurant_config_cache

                # Get restaurant config from cache (cache-first, DB fallback)
                restaurant_cache = get_restaurant_config_cache()
                restaurant_data = await restaurant_cache.get_by_id(restaurant_id)

                if restaurant_data and restaurant_data.get("name"):
                    logger.debug(
                        "Restaurant name fetched from cache for SMS",
                        restaurant_id=restaurant_id,
                        restaurant_name=restaurant_data.get("name")
                    )
                    return restaurant_data.get("name")

            except Exception as e:
                logger.warning(
                    "Failed to fetch restaurant name from cache for SMS, using default",
                    restaurant_id=restaurant_id,
                    error=str(e)
                )

        # Fallback to default from config
        from app.core.config import config
        return config.APP_NAME or "Restaurant"

    def check_delivery_status(self, message_sid: str) -> Dict[str, Any]:
        """
        Check the delivery status of a sent message

        Args:
            message_sid: Twilio message SID to check

        Returns:
            Dict containing current delivery status
        """
        try:
            message = self.client.messages(message_sid).fetch()

            return {
                "success": True,
                "message_sid": message_sid,
                "status": message.status,
                "error_code": message.error_code,
                "error_message": message.error_message,
                "date_sent": message.date_sent,
                "date_updated": message.date_updated
            }

        except TwilioException as e:
            logger.error("Failed to check message status",
                message_sid=message_sid,
                error=str(e)
            )

            return {
                "success": False,
                "message_sid": message_sid,
                "error": str(e)
            }


# Global SMS service instance
sms_service: Optional[SMSService] = None

def get_sms_service():
    """
    Get global SMS service instance (singleton pattern).

    Returns MockSMSService if Twilio is not available or not configured.
    """
    global sms_service

    if sms_service is None:
        # Check if Twilio is available and configured
        if not TWILIO_AVAILABLE:
            logger.info("Using MockSMSService - Twilio not installed")
            sms_service = MockSMSService()
        else:
            # Check for Twilio credentials
            account_sid = os.getenv('TWILIO_ACCOUNT_SID')
            auth_token = os.getenv('TWILIO_AUTH_TOKEN')
            from_number = os.getenv('TWILIO_PHONE_NUMBER')

            if not all([account_sid, auth_token, from_number]):
                logger.info("Using MockSMSService - Twilio credentials not configured")
                sms_service = MockSMSService()
            else:
                try:
                    sms_service = SMSService()
                except Exception as e:
                    logger.warning(f"Failed to initialize Twilio, using MockSMSService: {e}")
                    sms_service = MockSMSService()

    return sms_service


# Message status constants for reference
class SMSStatus:
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    UNDELIVERED = "undelivered"
    FAILED = "failed"

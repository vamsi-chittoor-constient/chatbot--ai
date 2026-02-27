"""
Notification Tools
=================
SMS and Email notification tools for booking confirmations and reminders.

Features:
- SMS confirmation sending (Twilio integration ready)
- Email confirmation sending (SMTP integration ready)
- Template-based messaging
- Delivery status tracking
- Retry logic for failed notifications
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from datetime import datetime
import pybreaker

from app.tools.base.tool_base import ToolBase, ToolResult, ToolStatus, ToolError
from app.core.logging_config import get_logger
from app.services.circuit_breaker_service import sms_breaker

logger = get_logger(__name__)


class SendSMSConfirmationTool(ToolBase):
    """Send SMS booking confirmation."""

    def __init__(self):
        super().__init__(
            name="send_sms_confirmation",
            description="Send SMS booking confirmation",
            max_retries=3,
            timeout_seconds=30
        )

    @sms_breaker
    def _send_twilio_message(self, client, body: str, from_: str, to: str):
        """
        Circuit breaker protected Twilio message send.
        Raises pybreaker.CircuitBreakerError when Twilio is down.
        """
        return client.messages.create(body=body, from_=from_, to=to)

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        required_fields = ['phone_number', 'guest_name', 'booking_date', 'confirmation_code']
        validated_data = {}

        for field in required_fields:
            if field not in kwargs or not kwargs[field]:
                raise ValueError(f"Missing required field: {field}")
            validated_data[field] = kwargs[field]

        # Optional fields
        optional_fields = [
            'party_size', 'table_number', 'special_requests', 'restaurant_name', 'restaurant_phone'
        ]
        for field in optional_fields:
            if field in kwargs:
                validated_data[field] = kwargs[field]

        return validated_data

    async def _execute_impl(self, **kwargs) -> ToolResult:
        try:
            # Format booking date
            if isinstance(kwargs['booking_date'], str):
                booking_date = datetime.fromisoformat(kwargs['booking_date'].replace('Z', '+00:00'))
            else:
                booking_date = kwargs['booking_date']

            formatted_date = booking_date.strftime("%B %d, %Y at %I:%M %p")

            # Create SMS message
            message = self._create_sms_message(
                guest_name=kwargs['guest_name'],
                booking_date=formatted_date,
                confirmation_code=kwargs['confirmation_code'],
                party_size=kwargs.get('party_size'),
                table_number=kwargs.get('table_number'),
                restaurant_name=kwargs.get('restaurant_name', 'Restaurant'),
                restaurant_phone=kwargs.get('restaurant_phone')
            )

            # Send SMS via Twilio
            success = await self._send_sms_twilio(
                phone_number=kwargs['phone_number'],
                message=message
            )

            if success:
                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={
                        "message_sent": True,
                        "phone_number": kwargs['phone_number'][-4:].rjust(len(kwargs['phone_number']), '*'),
                        "message_length": len(message),
                        "delivery_status": "sent",
                        "sent_at": datetime.now().isoformat()
                    },
                    metadata={"operation": "send_sms_confirmation"}
                )
            else:
                raise Exception("SMS delivery failed")

        except Exception as e:
            logger.error(f"Failed to send SMS confirmation: {str(e)}")
            raise ToolError(
                f"SMS service error: {str(e)}",
                tool_name=self.name,
                retry_suggested=True
            )

    def _create_sms_message(self, **kwargs) -> str:
        """Create formatted SMS message"""
        guest_name = kwargs['guest_name']
        booking_date = kwargs['booking_date']
        confirmation_code = kwargs['confirmation_code']
        party_size = kwargs.get('party_size')
        table_number = kwargs.get('table_number')
        restaurant_name = kwargs.get('restaurant_name', 'Restaurant')
        restaurant_phone = kwargs.get('restaurant_phone')

        message_parts = [
            f"Hi {guest_name}! Your reservation at {restaurant_name} is confirmed.",
            f"Date: {booking_date}"
        ]

        if party_size:
            message_parts.append(f"Party size: {party_size}")

        if table_number:
            message_parts.append(f"Table: {table_number}")

        message_parts.extend([
            f"Confirmation: {confirmation_code}",
        ])

        if restaurant_phone:
            message_parts.append(f"Call us: {restaurant_phone}")

        return "\n".join(message_parts)

    async def _send_sms_twilio(self, phone_number: str, message: str) -> bool:
        """Send SMS via Twilio"""
        try:
            # Get Twilio credentials from environment
            account_sid = os.getenv('TWILIO_ACCOUNT_SID')
            auth_token = os.getenv('TWILIO_AUTH_TOKEN')
            from_number = os.getenv('TWILIO_PHONE_NUMBER')

            if not all([account_sid, auth_token, from_number]):
                logger.error("Missing Twilio credentials in environment variables")
                return False

            # Import Twilio client
            try:
                from twilio.rest import Client
            except ImportError:
                logger.error("Twilio package not installed. Run: pip install twilio")
                return False

            # Create Twilio client and send message with circuit breaker protection
            client = Client(account_sid, auth_token)

            try:
                twilio_message = self._send_twilio_message(
                    client=client,
                    body=message,
                    from_=from_number,
                    to=phone_number
                )
            except pybreaker.CircuitBreakerError:
                logger.warning("SMS circuit breaker OPEN - Twilio service unavailable")
                # Graceful degradation - agent continues without SMS
                return False

            # Check if message was successfully queued/sent
            if twilio_message.status in ['queued', 'sent', 'delivered']:
                logger.info(f"SMS sent successfully to {phone_number}. Message SID: {twilio_message.sid}")
                return True
            else:
                logger.error(f"SMS failed to send. Status: {twilio_message.status}")
                return False

        except Exception as e:
            logger.error(f"Twilio SMS error: {str(e)}")
            return False


class SendEmailConfirmationTool(ToolBase):
    """Send email booking confirmation."""

    def __init__(self):
        super().__init__(
            name="send_email_confirmation",
            description="Send email booking confirmation",
            max_retries=3,
            timeout_seconds=30
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        required_fields = ['email', 'guest_name', 'booking_date', 'confirmation_code']
        validated_data = {}

        for field in required_fields:
            if field not in kwargs or not kwargs[field]:
                raise ValueError(f"Missing required field: {field}")
            validated_data[field] = kwargs[field]

        # Validate email format
        email = validated_data['email']
        if '@' not in email or '.' not in email.split('@')[1]:
            raise ValueError("Invalid email address format")

        # Optional fields
        optional_fields = [
            'party_size', 'table_number', 'special_requests', 'restaurant_name',
            'restaurant_address', 'restaurant_phone', 'restaurant_email'
        ]
        for field in optional_fields:
            if field in kwargs:
                validated_data[field] = kwargs[field]

        return validated_data

    async def _execute_impl(self, **kwargs) -> ToolResult:
        try:
            # Format booking date
            if isinstance(kwargs['booking_date'], str):
                booking_date = datetime.fromisoformat(kwargs['booking_date'].replace('Z', '+00:00'))
            else:
                booking_date = kwargs['booking_date']

            formatted_date = booking_date.strftime("%B %d, %Y at %I:%M %p")

            # Create email content
            subject, body = self._create_email_content(
                guest_name=kwargs['guest_name'],
                booking_date=formatted_date,
                confirmation_code=kwargs['confirmation_code'],
                party_size=kwargs.get('party_size'),
                table_number=kwargs.get('table_number'),
                special_requests=kwargs.get('special_requests'),
                restaurant_name=kwargs.get('restaurant_name', 'Restaurant'),
                restaurant_address=kwargs.get('restaurant_address'),
                restaurant_phone=kwargs.get('restaurant_phone'),
                restaurant_email=kwargs.get('restaurant_email')
            )

            # Send email via AWS SES
            success = await self._send_email_ses(
                to_email=kwargs['email'],
                subject=subject,
                body=body
            )

            if success:
                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={
                        "email_sent": True,
                        "email": kwargs['email'][:3] + '***@' + kwargs['email'].split('@')[1],
                        "subject": subject,
                        "delivery_status": "sent",
                        "sent_at": datetime.now().isoformat()
                    },
                    metadata={"operation": "send_email_confirmation"}
                )
            else:
                raise Exception("Email delivery failed")

        except Exception as e:
            logger.error(f"Failed to send email confirmation: {str(e)}")
            raise ToolError(
                f"Email service error: {str(e)}",
                tool_name=self.name,
                retry_suggested=True
            )

    def _create_email_content(self, **kwargs) -> tuple[str, str]:
        """Create formatted email subject and body"""
        guest_name = kwargs['guest_name']
        booking_date = kwargs['booking_date']
        confirmation_code = kwargs['confirmation_code']
        party_size = kwargs.get('party_size')
        table_number = kwargs.get('table_number')
        special_requests = kwargs.get('special_requests')
        restaurant_name = kwargs.get('restaurant_name', 'Restaurant')
        restaurant_address = kwargs.get('restaurant_address')
        restaurant_phone = kwargs.get('restaurant_phone')
        restaurant_email = kwargs.get('restaurant_email')

        subject = f"Booking Confirmed - {restaurant_name} - {confirmation_code}"

        body = """
Dear {guest_name},

Your reservation at {restaurant_name} has been confirmed!

BOOKING DETAILS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Date & Time: {booking_date}
Party Size: {party_size or 'Not specified'}
Confirmation Code: {confirmation_code}
"""

        if table_number:
            body += f"Table Number: {table_number}\n"

        if special_requests:
            body += f"Special Requests: {special_requests}\n"

        body += "\nRESTAURANT INFORMATION:\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

        if restaurant_address:
            body += f"Address: {restaurant_address}\n"

        if restaurant_phone:
            body += f"Phone: {restaurant_phone}\n"

        if restaurant_email:
            body += f"Email: {restaurant_email}\n"

        body += """
IMPORTANT REMINDERS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Please arrive 10 minutes before your reservation time
• Bring your confirmation code: {confirmation_code}
• Call us if you need to make any changes
• We hold reservations for 15 minutes past the booking time

Thank you for choosing {restaurant_name}!
We look forward to serving you.

Best regards,
{restaurant_name} Team

---
This is an automated confirmation email.
"""

        return subject, body

    async def _send_email_ses(self, to_email: str, subject: str, body: str) -> bool:
        """Send email via AWS SES"""
        try:
            # Get AWS credentials from environment
            aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
            aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
            aws_region = os.getenv('AWS_REGION', 'us-east-1')
            from_email = os.getenv('SES_FROM_EMAIL')

            if not all([aws_access_key, aws_secret_key, from_email]):
                logger.error("Missing AWS SES credentials in environment variables")
                return False

            # Import AWS SES client
            try:
                import boto3
                from botocore.exceptions import ClientError
            except ImportError:
                logger.error("boto3 package not installed. Run: pip install boto3")
                return False

            # Create SES client
            ses_client = boto3.client(
                'ses',
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=aws_region
            )

            # Send email
            try:
                response = ses_client.send_email(
                    Source=from_email,
                    Destination={'ToAddresses': [to_email]},
                    Message={
                        'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                        'Body': {'Text': {'Data': body, 'Charset': 'UTF-8'}}
                    }
                )

                message_id = response['MessageId']
                logger.info(f"Email sent successfully to {to_email}. Message ID: {message_id}")
                return True

            except ClientError as e:
                error_code = e.response['Error']['Code']
                error_message = e.response['Error']['Message']
                logger.error(f"AWS SES error [{error_code}]: {error_message}")
                return False

        except Exception as e:
            logger.error(f"Email sending error: {str(e)}")
            return False


class SendBookingReminderTool(ToolBase):
    """Send booking reminder SMS/Email."""

    def __init__(self):
        super().__init__(
            name="send_booking_reminder",
            description="Send booking reminder notification",
            max_retries=3,
            timeout_seconds=30
        )

    @sms_breaker
    def _send_twilio_message(self, client, body: str, from_: str, to: str):
        """
        Circuit breaker protected Twilio message send.
        Raises pybreaker.CircuitBreakerError when Twilio is down.
        """
        return client.messages.create(body=body, from_=from_, to=to)

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        required_fields = ['guest_name', 'booking_date', 'confirmation_code']
        validated_data = {}

        for field in required_fields:
            if field not in kwargs or not kwargs[field]:
                raise ValueError(f"Missing required field: {field}")
            validated_data[field] = kwargs[field]

        # At least one contact method required
        if 'phone_number' not in kwargs and 'email' not in kwargs:
            raise ValueError("Either phone_number or email is required")

        # Optional fields
        optional_fields = [
            'phone_number', 'email', 'party_size', 'table_number', 'restaurant_name'
        ]
        for field in optional_fields:
            if field in kwargs:
                validated_data[field] = kwargs[field]

        return validated_data

    async def _execute_impl(self, **kwargs) -> ToolResult:
        try:
            results = {}

            # Send SMS reminder if phone provided
            if 'phone_number' in kwargs:
                sms_message = self._create_reminder_sms(**kwargs)
                sms_success = await self._send_sms_twilio(kwargs['phone_number'], sms_message)
                results['sms_sent'] = sms_success

            # Send email reminder if email provided
            if 'email' in kwargs:
                subject, body = self._create_reminder_email(**kwargs)
                email_success = await self._send_email_ses(kwargs['email'], subject, body)
                results['email_sent'] = email_success

            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    **results,
                    "reminder_type": "booking_reminder",
                    "sent_at": datetime.now().isoformat()
                },
                metadata={"operation": "send_booking_reminder"}
            )

        except Exception as e:
            logger.error(f"Failed to send booking reminder: {str(e)}")
            raise ToolError(
                f"Reminder service error: {str(e)}",
                tool_name=self.name,
                retry_suggested=True
            )

    def _create_reminder_sms(self, **kwargs) -> str:
        """Create reminder SMS message"""
        guest_name = kwargs['guest_name']
        booking_date = kwargs['booking_date']
        confirmation_code = kwargs['confirmation_code']
        restaurant_name = kwargs.get('restaurant_name', 'Restaurant')

        if isinstance(booking_date, str):
            booking_date = datetime.fromisoformat(booking_date.replace('Z', '+00:00'))

        formatted_date = booking_date.strftime("%B %d at %I:%M %p")

        return f"Hi {guest_name}! Reminder: Your reservation at {restaurant_name} is tomorrow, {formatted_date}. Confirmation: {confirmation_code}. See you then!"

    def _create_reminder_email(self, **kwargs) -> tuple[str, str]:
        """Create reminder email subject and body"""
        guest_name = kwargs['guest_name']
        booking_date = kwargs['booking_date']
        confirmation_code = kwargs['confirmation_code']
        restaurant_name = kwargs.get('restaurant_name', 'Restaurant')

        if isinstance(booking_date, str):
            booking_date = datetime.fromisoformat(booking_date.replace('Z', '+00:00'))

        formatted_date = booking_date.strftime("%B %d, %Y at %I:%M %p")

        subject = f"Reminder: Your reservation at {restaurant_name} tomorrow"

        body = """
Dear {guest_name},

This is a friendly reminder about your upcoming reservation:

Date: {formatted_date}
Restaurant: {restaurant_name}
Confirmation: {confirmation_code}

We look forward to seeing you!

Best regards,
{restaurant_name} Team
"""

        return subject, body

    async def _send_email_ses(self, to_email: str, subject: str, body: str) -> bool:
        """Send email via AWS SES (shared method)"""
        try:
            # Get AWS credentials from environment
            aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
            aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
            aws_region = os.getenv('AWS_REGION', 'us-east-1')
            from_email = os.getenv('SES_FROM_EMAIL')

            if not all([aws_access_key, aws_secret_key, from_email]):
                logger.error("Missing AWS SES credentials in environment variables")
                return False

            # Import AWS SES client
            try:
                import boto3
                from botocore.exceptions import ClientError
            except ImportError:
                logger.error("boto3 package not installed. Run: pip install boto3")
                return False

            # Create SES client
            ses_client = boto3.client(
                'ses',
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=aws_region
            )

            # Send email
            try:
                response = ses_client.send_email(
                    Source=from_email,
                    Destination={'ToAddresses': [to_email]},
                    Message={
                        'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                        'Body': {'Text': {'Data': body, 'Charset': 'UTF-8'}}
                    }
                )

                message_id = response['MessageId']
                logger.info(f"Email sent successfully to {to_email}. Message ID: {message_id}")
                return True

            except ClientError as e:
                error_code = e.response['Error']['Code']
                error_message = e.response['Error']['Message']
                logger.error(f"AWS SES error [{error_code}]: {error_message}")
                return False

        except Exception as e:
            logger.error(f"Email sending error: {str(e)}")
            return False

    async def _send_sms_twilio(self, phone_number: str, message: str) -> bool:
        """Send SMS via Twilio (shared method)"""
        try:
            # Get Twilio credentials from environment
            account_sid = os.getenv('TWILIO_ACCOUNT_SID')
            auth_token = os.getenv('TWILIO_AUTH_TOKEN')
            from_number = os.getenv('TWILIO_PHONE_NUMBER')

            if not all([account_sid, auth_token, from_number]):
                logger.error("Missing Twilio credentials in environment variables")
                return False

            # Import Twilio client
            try:
                from twilio.rest import Client
            except ImportError:
                logger.error("Twilio package not installed. Run: pip install twilio")
                return False

            # Create Twilio client and send message with circuit breaker protection
            client = Client(account_sid, auth_token)

            try:
                twilio_message = self._send_twilio_message(
                    client=client,
                    body=message,
                    from_=from_number,
                    to=phone_number
                )
            except pybreaker.CircuitBreakerError:
                logger.warning("SMS circuit breaker OPEN - Twilio service unavailable")
                # Graceful degradation - agent continues without SMS
                return False

            # Check if message was successfully queued/sent
            if twilio_message.status in ['queued', 'sent', 'delivered']:
                logger.info(f"SMS sent successfully to {phone_number}. Message SID: {twilio_message.sid}")
                return True
            else:
                logger.error(f"SMS failed to send. Status: {twilio_message.status}")
                return False

        except Exception as e:
            logger.error(f"Twilio SMS error: {str(e)}")
            return False


# Create tool instances for easy importing
send_sms_confirmation_tool = SendSMSConfirmationTool()
send_email_confirmation_tool = SendEmailConfirmationTool()
send_booking_reminder_tool = SendBookingReminderTool()

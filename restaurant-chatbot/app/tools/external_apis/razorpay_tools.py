"""
Razorpay External API Tools
===========================

External API integration tools for Razorpay payment gateway:
- Payment order creation and management
- Payment link generation
- Payment signature verification
- Direct Razorpay API interactions

Separated from database operations for clean architecture.
"""

import os
import hmac
import hashlib
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from dataclasses import dataclass
from uuid import UUID
import pybreaker

import razorpay
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.tools.base.tool_base import ToolBase, ToolResult, ToolStatus
from app.core.database import get_db_session
from app.features.food_ordering.models import PaymentOrder, Order
from app.shared.models.payment import PaymentRetryAttempt
from app.core.logging_config import get_logger
from app.utils.validation_decorators import require_tables
from app.services.circuit_breaker_service import razorpay_breaker

logger = get_logger(__name__)


@dataclass
class PaymentRequest:
    """Structured payment request"""
    order_id: str
    user_id: str
    amount: Decimal  # Amount in rupees
    currency: str = "INR"
    notes: Optional[Dict[str, Any]] = None
    callback_url: Optional[str] = None
    notify_url: Optional[str] = None


@dataclass
class PaymentResponse:
    """Structured payment response"""
    success: bool
    payment_order_id: Optional[int] = None
    razorpay_order_id: Optional[str] = None
    payment_link: Optional[str] = None
    expires_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0


class RazorpayPaymentTool(ToolBase):
    """
    Razorpay payment order creation and management tool.
    Handles direct Razorpay API interactions for payment processing.
    """

    def __init__(self):
        super().__init__(
            name="razorpay_payment",
            description="Create and manage Razorpay payment orders with link generation"
        )

        # Validate required Razorpay credentials
        razorpay_key_id = os.getenv("RAZORPAY_KEY_ID")
        razorpay_key_secret = os.getenv("RAZORPAY_KEY_SECRET")

        if not razorpay_key_id or not razorpay_key_secret:
            error_msg = (
                "Razorpay credentials missing! "
                "Please set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in .env file. "
                "Get your credentials from: https://dashboard.razorpay.com/app/keys"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Initialize Razorpay client with validated credentials
        self.client = razorpay.Client(auth=(razorpay_key_id, razorpay_key_secret))

        # Payment configuration
        self.currency = os.getenv("PAYMENT_CURRENCY", "INR")
        self.link_expiry_minutes = int(os.getenv("PAYMENT_LINK_EXPIRY_MINUTES", "15"))
        self.max_retry_attempts = int(os.getenv("PAYMENT_MAX_RETRY_ATTEMPTS", "3"))
        self.callback_url = os.getenv("PAYMENT_CALLBACK_URL")
        self.success_url = os.getenv("PAYMENT_SUCCESS_URL")
        self.failure_url = os.getenv("PAYMENT_FAILURE_URL")

    @razorpay_breaker
    def _create_razorpay_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Circuit breaker protected Razorpay order creation.
        Raises pybreaker.CircuitBreakerError when Razorpay is down.
        """
        return self.client.order.create(order_data)  # type: ignore

    @razorpay_breaker
    def _create_razorpay_payment_link(self, link_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Circuit breaker protected payment link creation.
        Raises pybreaker.CircuitBreakerError when Razorpay is down.
        """
        return self.client.payment_link.create(link_data)  # type: ignore

    async def _send_payment_link_sms(
        self,
        phone_number: str,
        payment_link: str,
        order_number: str,
        amount: float,
        customer_name: str,
        order_items: list = None,
        order_type: str = None
    ) -> bool:
        """Send payment link via SMS using Twilio"""
        try:
            # Get Twilio credentials
            account_sid = os.getenv('TWILIO_ACCOUNT_SID')
            auth_token = os.getenv('TWILIO_AUTH_TOKEN')
            from_number = os.getenv('TWILIO_PHONE_NUMBER')

            if not all([account_sid, auth_token, from_number]):
                logger.warning("Missing Twilio credentials - SMS not sent")
                return False

            # Import Twilio client
            try:
                from twilio.rest import Client
            except ImportError:
                logger.warning("Twilio package not installed - SMS not sent")
                return False

            # Build items summary
            items_summary = ""
            if order_items and len(order_items) > 0:
                # Get first item name
                first_item = order_items[0]
                item_name = first_item.menu_item.name if hasattr(first_item, 'menu_item') and first_item.menu_item else "items"

                if len(order_items) == 1:
                    items_summary = item_name
                else:
                    items_summary = f"{item_name} and {len(order_items) - 1} more item{'s' if len(order_items) - 1 > 1 else ''}"
            else:
                items_summary = f"₹{amount:.2f}"

            # Order type display
            order_type_text = ""
            if order_type:
                order_type_display = "dine-in" if order_type == "dine_in" else "takeout" if order_type == "takeaway" else order_type
                order_type_text = f" for {order_type_display}"

            # Create SMS message
            message = f"""Hi {customer_name}!

Your order #{order_number} for {items_summary} has been placed successfully{order_type_text}.

Complete your payment securely:
{payment_link}

Link expires in {self.link_expiry_minutes} minutes.

Thank you for choosing A24 Restaurant!"""

            # Send SMS
            client = Client(account_sid, auth_token)
            twilio_message = client.messages.create(
                body=message,
                from_=from_number,
                to=phone_number
            )

            if twilio_message.status in ['queued', 'sent', 'delivered']:
                logger.info(
                    "Payment link SMS sent",
                    phone=phone_number[-4:].rjust(10, '*'),
                    order_number=order_number,
                    message_sid=twilio_message.sid
                )
                return True
            else:
                logger.warning(f"SMS failed with status: {twilio_message.status}")
                return False

        except Exception as e:
            logger.error(f"Failed to send payment link SMS: {str(e)}")
            return False

    @require_tables("payment_orders,payment_transactions,orders")
    async def _execute_impl(self, **kwargs) -> ToolResult:
        """
        Execute payment operations with Razorpay integration

        Operations:
        - create_order: Create new payment order and link
        - create_link: Generate payment link for existing order
        - retry_payment: Retry failed payment with new link
        """
        operation = kwargs.get("operation")

        try:
            async with get_db_session() as session:
                if operation == "create_order":
                    return await self._create_payment_order(session, kwargs)

                elif operation == "create_link":
                    return await self._create_payment_link(session, kwargs)

                elif operation == "retry_payment":
                    return await self._retry_payment(session, kwargs)

                else:
                    return ToolResult(
                        status=ToolStatus.FAILURE,
                        data={"error": f"Unknown operation: {operation}"}
                    )

        except Exception as e:
            logger.error(f"RazorpayPaymentTool error: {str(e)}")
            return ToolResult(
                status=ToolStatus.FAILURE,
                data={"error": f"Payment operation failed: {str(e)}"}
            )

    async def _create_payment_order(self, session, params: Dict[str, Any]) -> ToolResult:
        """
        Create new payment order with Razorpay and generate payment link.

        SECURITY: Payment amount is ALWAYS sourced from Order.total_amount in database.
        This is a deterministic, non-LLM operation to prevent hallucination-based tampering.

        Params:
            - order_id: Order ID
            - user_id: User ID
            - payment_source: "chat" or "external" (default: "external")
            - session_id: Session ID (required if payment_source=chat)
            - notes: Additional notes
        """
        order_id = params.get("order_id")
        user_id = params.get("user_id")
        payment_source = params.get("payment_source", "external")  # "chat" or "external"
        session_id = params.get("session_id")
        notes = params.get("notes", {})

        if not order_id or not user_id:
            return ToolResult(
                status=ToolStatus.FAILURE,
                data={"error": "order_id and user_id are required"}
            )

        try:
            # Get order details - THIS is the source of truth for amount
            # Eagerly load user and items relationships to avoid lazy-loading in async context
            from sqlalchemy.orm import selectinload
            # from app.shared.models import OrderItem
            from app.features.food_ordering.models import OrderItem

            from app.features.food_ordering.models import OrderTotal

            order_query = select(Order).where(Order.order_id == order_id).options(
                selectinload(Order.items).selectinload(OrderItem.menu_item),
                selectinload(Order.totals)
            )
            order_result = await session.execute(order_query)
            order = order_result.scalar_one_or_none()

            if not order:
                return ToolResult(
                    status=ToolStatus.FAILURE,
                    data={"error": "Order not found"}
                )

            # Calculate amount from order items
            if not order.items or len(order.items) == 0:
                return ToolResult(
                    status=ToolStatus.FAILURE,
                    data={"error": "Order has no items"}
                )

            # Use OrderTotal.final_amount (includes packaging charges) if available,
            # otherwise fall back to summing item base_prices
            if order.totals and order.totals.final_amount:
                amount = Decimal(str(order.totals.final_amount))
            else:
                amount = sum(
                    Decimal(str(item.base_price or 0)) for item in order.items
                )

            if amount <= 0:
                return ToolResult(
                    status=ToolStatus.FAILURE,
                    data={"error": f"Invalid order amount: {amount}"}
                )

            # Check if payment order already exists
            existing_payment_query = select(PaymentOrder).where(
                PaymentOrder.order_id == order_id
            )
            existing_result = await session.execute(existing_payment_query)
            existing_payment = existing_result.scalar_one_or_none()

            if existing_payment and existing_payment.status in ["created", "processing"]:
                return ToolResult(
                    status=ToolStatus.FAILURE,
                    data={"error": "Payment order already exists for this order"}
                )

            # Convert amount to paise (smallest currency unit)
            amount_paise = int(amount * 100)

            # Calculate expiry time in UTC (same as booking implementation)
            # Add 1 extra minute buffer to ensure Razorpay sees > 15 minutes
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=self.link_expiry_minutes + 1)

            # Build callback URL with source parameter
            callback_url = self.callback_url
            if payment_source == "chat" and session_id:
                callback_url = f"{self.callback_url}?source=chat&session_id={session_id}"
            else:
                callback_url = f"{self.callback_url}?source=external"

            # Create payment link FIRST to get Razorpay's order_id
            # Get customer info from session (user already authenticated via OTP)
            from app.core.redis import get_sync_redis_client
            redis_client = get_sync_redis_client()

            customer_name = "Customer"
            customer_phone = None

            # Fetch user name from session
            user_name_key = f"session:{session_id}:user_name"
            user_name_bytes = redis_client.get(user_name_key)
            if user_name_bytes:
                customer_name = user_name_bytes.decode('utf-8')

            # Fetch user phone from session
            user_phone_key = f"session:{session_id}:user_phone"
            user_phone_bytes = redis_client.get(user_phone_key)
            if user_phone_bytes:
                customer_phone = user_phone_bytes.decode('utf-8')

            customer_data = {
                "name": customer_name,
            }

            # Add phone if available (optional for Razorpay)
            if customer_phone:
                customer_data["contact"] = customer_phone

            payment_link_data = {
                "amount": amount_paise,
                "currency": self.currency,
                "reference_id": str(order.order_invoice_number) if order.order_invoice_number else str(order_id),
                "callback_url": callback_url,
                "callback_method": "get",
                "description": f"Payment for Order #{order.order_invoice_number or order_id}",
                "customer": customer_data,
                "notify": {
                    "sms": False,   # We send our own branded SMS via Twilio
                    "email": False  # We send our own branded email via SMTP
                },
                "reminder_enable": False,  # We handle reminders ourselves
                "notes": {
                    "internal_order_id": str(order_id),
                    "order_number": str(order.order_invoice_number) if order.order_invoice_number else str(order_id),
                    "session_id": session_id,
                    **notes
                },
                "expire_by": int(expires_at.timestamp())
            }

            # Create payment link with circuit breaker protection
            try:
                payment_link = self._create_razorpay_payment_link(payment_link_data)
            except pybreaker.CircuitBreakerError:
                logger.error("Razorpay circuit breaker OPEN - payment link creation failed")
                return ToolResult(
                    status=ToolStatus.FAILURE,
                    error="Payment service is temporarily unavailable. Your order has been saved and we'll process the payment when service resumes. We'll notify you via SMS once payment is ready."
                )

            # IMPORTANT: Razorpay Payment Links API does NOT return order_id in create response
            # The gateway_order_id will be populated later from webhook/callback when payment is completed
            # For now, we track via payment_link_id and reference_id (order_invoice_number)

            # Convert user_id to UUID if it's a string
            customer_uuid = None
            if user_id:
                try:
                    if isinstance(user_id, UUID):
                        customer_uuid = user_id
                    elif isinstance(user_id, str):
                        customer_uuid = UUID(user_id)
                except (ValueError, AttributeError) as e:
                    logger.warning(f"Invalid user_id format: {user_id}, error: {e}")
                    customer_uuid = None

            payment_order = PaymentOrder(
                order_id=order_id,
                restaurant_id=order.restaurant_id,  # Copy from order
                customer_id=customer_uuid,
                gateway_order_id=None,  # Will be updated from webhook when payment is made
                order_amount=amount,  # Store as Decimal, not paise
                order_currency=self.currency,
                payment_order_status="created",
                payment_link_url=payment_link["short_url"],
                payment_link_id=payment_link["id"],  # Primary identifier for payment link
                payment_link_short_url=payment_link.get("short_url"),
                payment_link_expires_at=expires_at,
                retry_count=0,
                max_retry_attempts=self.max_retry_attempts,
                payment_metadata=notes  # Maps to 'metadata' column in database
            )

            session.add(payment_order)
            await session.flush()
            await session.commit()

            payment_order_id = payment_order.payment_order_id

            logger.info(
                "Payment link created successfully",
                payment_order_id=payment_order_id,
                order_invoice_number=order.order_invoice_number,
                payment_link_id=payment_link["id"],
                reference_id=str(order.order_invoice_number) if order.order_invoice_number else str(order_id),
                note="razorpay_order_id will be populated from webhook"
            )

            # SMS sending skipped for guest checkout (no user phone number available)
            # Payment link will be displayed in the UI instead
            sms_sent = False

            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "payment_order_id": payment_order.payment_order_id,
                    "razorpay_order_id": payment_order.gateway_order_id,
                    "payment_link": payment_link["short_url"],
                    "payment_link_id": payment_link["id"],
                    "reference_id": order.order_invoice_number,
                    "amount": float(amount),
                    "currency": self.currency,
                    "expires_at": expires_at.isoformat(),
                    "sms_sent": sms_sent,
                    "order_details": {
                        "order_number": order.order_invoice_number,
                        "total_amount": float(amount)
                    }
                }
            )

        except Exception as e:
            await session.rollback()
            logger.error(f"Error creating payment order: {str(e)}")
            return ToolResult(
                status=ToolStatus.FAILURE,
                data={"error": f"Failed to create payment order: {str(e)}"}
            )

    async def _create_payment_link(self, session, params: Dict[str, Any]) -> ToolResult:
        """Create payment link for existing payment order"""
        payment_order_id = params.get("payment_order_id")

        if not payment_order_id:
            return ToolResult(
                status=ToolStatus.FAILURE,
                data={"error": "payment_order_id is required"}
            )

        try:
            # Get payment order
            payment_query = select(PaymentOrder).options(
                selectinload(PaymentOrder.order),
                selectinload(PaymentOrder.user)
            ).where(PaymentOrder.id == payment_order_id)

            payment_result = await session.execute(payment_query)
            payment_order = payment_result.scalar_one_or_none()

            if not payment_order:
                return ToolResult(
                    status=ToolStatus.FAILURE,
                    data={"error": "Payment order not found"}
                )

            # Check if already has valid link
            if (payment_order.payment_link and
                payment_order.payment_link_expires_at > datetime.now()):
                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={
                        "payment_link": payment_order.payment_link,
                        "expires_at": payment_order.payment_link_expires_at.isoformat(),
                        "message": "Existing valid payment link returned"
                    }
                )

            # Create new payment link (existing logic from _create_payment_order)
            # ... (similar to payment link creation above)

            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={"message": "Payment link creation not fully implemented yet"}
            )

        except Exception as e:
            logger.error(f"Error creating payment link: {str(e)}")
            return ToolResult(
                status=ToolStatus.FAILURE,
                data={"error": f"Failed to create payment link: {str(e)}"}
            )

    async def _retry_payment(self, session, params: Dict[str, Any]) -> ToolResult:
        """
        Retry failed payment with new payment link

        Params:
            - payment_order_id: Payment order ID to retry
            - payment_source: "chat" or "external" (default: "external")
            - session_id: Session ID (required if payment_source=chat)
        """
        payment_order_id = params.get("payment_order_id")
        payment_source = params.get("payment_source", "external")
        session_id = params.get("session_id")

        if not payment_order_id:
            return ToolResult(
                status=ToolStatus.FAILURE,
                data={"error": "payment_order_id is required"}
            )

        try:
            # Get payment order
            payment_query = select(PaymentOrder).options(
                selectinload(PaymentOrder.order),
                selectinload(PaymentOrder.user)
            ).where(PaymentOrder.id == payment_order_id)

            payment_result = await session.execute(payment_query)
            payment_order = payment_result.scalar_one_or_none()

            if not payment_order:
                return ToolResult(
                    status=ToolStatus.FAILURE,
                    data={"error": "Payment order not found"}
                )

            # Check retry limit
            if payment_order.retry_count >= payment_order.max_retry_attempts:
                return ToolResult(
                    status=ToolStatus.FAILURE,
                    data={
                        "error": "Maximum retry attempts exceeded",
                        "retry_count": payment_order.retry_count,
                        "max_attempts": payment_order.max_retry_attempts
                    }
                )

            # Record retry attempt
            retry_attempt = PaymentRetryAttempt(
                payment_order_id=payment_order.payment_order_id,
                user_id=payment_order.customer_id,
                attempt_number=payment_order.retry_count + 1,
                status="attempted"
            )
            session.add(retry_attempt)

            # Increment retry count
            payment_order.retry_count += 1

            # Generate new expiry time in UTC (same as booking implementation)
            # Add 1 extra minute buffer to ensure Razorpay sees > 15 minutes
            new_expires_at = datetime.now(timezone.utc) + timedelta(minutes=self.link_expiry_minutes + 1)
            payment_order.payment_link_expires_at = new_expires_at

            # Build callback URL with source parameter
            callback_url = self.callback_url
            if payment_source == "chat" and session_id:
                callback_url = f"{self.callback_url}?source=chat&session_id={session_id}"
            else:
                callback_url = f"{self.callback_url}?source=external"

            # Create new payment link (reuse existing Razorpay order)
            payment_link_data = {
                "amount": payment_order.order_amount,
                "currency": payment_order.order_currency,
                "order_id": payment_order.gateway_order_id,
                "callback_url": callback_url,
                "callback_method": "get",
                "description": f"Payment for Order #{payment_order.order.order_invoice_number} (Retry {payment_order.retry_count})",
                "customer": {
                    "name": "Customer",  # Default for retry attempts
                },
                "notify": {
                    "sms": False,   # We send our own branded SMS via Twilio
                    "email": False  # We send our own branded email via SMTP
                },
                "reminder_enable": False,  # We handle reminders ourselves
                "notes": {
                    "restaurant_order_id": payment_order.order_id,
                    "user_id": payment_order.customer_id,
                    "retry_attempt": payment_order.retry_count
                },
                "expire_by": int(new_expires_at.timestamp())
            }

            # Create payment link with circuit breaker protection
            try:
                payment_link = self._create_razorpay_payment_link(payment_link_data)
            except pybreaker.CircuitBreakerError:
                logger.error("Razorpay circuit breaker OPEN - payment retry failed")
                # Rollback the retry attempt
                await session.rollback()
                return ToolResult(
                    status=ToolStatus.FAILURE,
                    error="Payment service is temporarily unavailable. We'll automatically retry when service resumes. Your order is safe."
                )

            # Update payment order
            payment_order.payment_link_url = payment_link["short_url"]
            payment_order.payment_link_id = payment_link["id"]
            payment_order.payment_order_status = "created"

            await session.commit()

            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "payment_order_id": payment_order.payment_order_id,
                    "razorpay_order_id": payment_order.gateway_order_id,
                    "payment_link": payment_link["short_url"],
                    "expires_at": new_expires_at.isoformat(),
                    "retry_count": payment_order.retry_count,
                    "max_attempts": payment_order.max_retry_attempts,
                    "attempts_remaining": payment_order.max_retry_attempts - payment_order.retry_count
                }
            )

        except Exception as e:
            await session.rollback()
            logger.error(f"Error retrying payment: {str(e)}")
            return ToolResult(
                status=ToolStatus.FAILURE,
                data={"error": f"Failed to retry payment: {str(e)}"}
            )


class PaymentVerificationTool(ToolBase):
    """
    Payment verification and signature validation tool.
    Ensures payment security through Razorpay signature verification.
    """

    def __init__(self):
        super().__init__(
            name="payment_verification",
            description="Verify payment signatures and validate payment authenticity"
        )
        self.razorpay_secret = os.getenv("RAZORPAY_KEY_SECRET")
        self.webhook_secret = os.getenv("RAZORPAY_WEBHOOK_SECRET")

    @require_tables("payment_orders,payment_transactions")
    async def _execute_impl(self, **kwargs) -> ToolResult:
        """
        Execute payment verification operations

        Operations:
        - verify_payment: Verify payment signature from frontend
        - verify_webhook: Verify webhook signature from Razorpay
        """
        operation = kwargs.get("operation")

        try:
            if operation == "verify_payment":
                return await self._verify_payment_signature(kwargs)

            elif operation == "verify_webhook":
                return await self._verify_webhook_signature(kwargs)

            else:
                return ToolResult(
                    status=ToolStatus.FAILURE,
                    data={"error": f"Unknown operation: {operation}"}
                )

        except Exception as e:
            logger.error(f"PaymentVerificationTool error: {str(e)}")
            return ToolResult(
                status=ToolStatus.FAILURE,
                data={"error": f"Verification failed: {str(e)}"}
            )

    async def _verify_payment_signature(self, params: Dict[str, Any]) -> ToolResult:
        """Verify payment signature from frontend callback"""
        razorpay_order_id = params.get("razorpay_order_id")
        razorpay_payment_id = params.get("razorpay_payment_id")
        razorpay_signature = params.get("razorpay_signature")

        if not all([razorpay_order_id, razorpay_payment_id]) or razorpay_signature is None:
            return ToolResult(
                status=ToolStatus.FAILURE,
                data={"error": "razorpay_order_id, razorpay_payment_id, and razorpay_signature are required"}
            )

        try:
            # Create signature verification message
            message = f"{razorpay_order_id}|{razorpay_payment_id}"

            # Generate expected signature
            if not self.razorpay_secret:
                return ToolResult(
                    status=ToolStatus.FAILURE,
                    data={"error": "Razorpay secret not configured"}
                )

            expected_signature = hmac.new(
                self.razorpay_secret.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()

            # Verify signature (ensure string type)
            signature_str = str(razorpay_signature) if razorpay_signature is not None else ""
            is_valid = hmac.compare_digest(expected_signature, signature_str)

            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "is_valid": is_valid,
                    "razorpay_order_id": razorpay_order_id,
                    "razorpay_payment_id": razorpay_payment_id,
                    "verification_message": "Payment signature verified successfully" if is_valid else "Invalid payment signature"
                }
            )

        except Exception as e:
            logger.error(f"Error verifying payment signature: {str(e)}")
            return ToolResult(
                status=ToolStatus.FAILURE,
                data={"error": f"Signature verification failed: {str(e)}"}
            )

    async def _verify_webhook_signature(self, params: Dict[str, Any]) -> ToolResult:
        """Verify webhook signature from Razorpay"""
        webhook_payload = params.get("webhook_payload")
        webhook_signature = params.get("webhook_signature")

        if not all([webhook_payload, webhook_signature]):
            return ToolResult(
                status=ToolStatus.FAILURE,
                data={"error": "webhook_payload and webhook_signature are required"}
            )

        try:
            # Generate expected signature
            if not self.webhook_secret:
                return ToolResult(
                    status=ToolStatus.FAILURE,
                    data={"error": "Webhook secret not configured"}
                )

            # Ensure webhook_secret is string and not None
            secret_str = str(self.webhook_secret)
            payload_str = str(webhook_payload) if webhook_payload is not None else ""

            expected_signature = hmac.new(
                secret_str.encode(),
                payload_str.encode(),
                hashlib.sha256
            ).hexdigest()

            # Verify signature (ensure string type)
            signature_str = str(webhook_signature) if webhook_signature is not None else ""
            is_valid = hmac.compare_digest(expected_signature, signature_str)

            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "is_valid": is_valid,
                    "verification_message": "Webhook signature verified successfully" if is_valid else "Invalid webhook signature"
                }
            )

        except Exception as e:
            logger.error(f"Error verifying webhook signature: {str(e)}")
            return ToolResult(
                status=ToolStatus.FAILURE,
                data={"error": f"Webhook verification failed: {str(e)}"}
            )


# Initialize tools for easy import
razorpay_payment_tool = RazorpayPaymentTool()
payment_verification_tool = PaymentVerificationTool()

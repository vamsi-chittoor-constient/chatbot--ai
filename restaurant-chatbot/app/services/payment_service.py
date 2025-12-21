"""
Payment Service
===============
Deterministic payment operations using Razorpay integration.

This service handles all payment-related operations without LLM reasoning:
- Creating payment orders
- Generating payment links
- Checking payment status
- Retrying failed payments
- Sending payment links via SMS/WhatsApp
- Retrieving payment history

All operations are deterministic and do not require autonomous decision-making.
"""

from typing import Dict, Any, Optional, List
from decimal import Decimal

from app.core.logging_config import get_logger
from app.tools.external_apis.razorpay_tools import RazorpayPaymentTool
from app.tools.database.payment_db_tools import PaymentStatusTool
from app.tools.base.tool_base import ToolStatus
from app.services.sms_service import get_sms_service
from app.tools.external_apis.whatsapp_tools import WhatsAppBusinessTool

logger = get_logger(__name__)


class PaymentService:
    """
    Service for deterministic payment operations.

    This is a pure service (no LLM reasoning) that provides payment functionality
    to agents and orchestrators. All operations are synchronous API calls to Razorpay
    and database operations.

    SECURITY: Payment amounts are ALWAYS sourced from the Order database record,
    never from parameters. This prevents amount tampering.
    """

    def __init__(self):
        """Initialize payment service with required tools."""
        self.razorpay_tool = RazorpayPaymentTool()
        self.payment_status_tool = PaymentStatusTool()
        self.sms_service = get_sms_service()
        self.whatsapp_tool = WhatsAppBusinessTool()
        logger.info("PaymentService initialized")

    async def create_payment_order(
        self,
        order_id: str,
        user_id: str,
        payment_source: str = "external",
        session_id: Optional[str] = None,
        notes: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new payment order and generate payment link.

        Creates a Razorpay payment order for the customer's order and generates
        a secure payment link that can be sent to the customer.

        SECURITY: Payment amount is ALWAYS sourced from the Order database record,
        never from parameters. This prevents hallucination-based amount tampering.

        Args:
            order_id: ID of the restaurant order to create payment for
            user_id: Customer's user ID
            payment_source: "chat" or "external" - determines callback redirect behavior
            session_id: Chat session ID (required if payment_source="chat" for callback redirect)
            notes: Optional notes/metadata for the payment

        Returns:
            Dict with payment order details and payment link:
            {
                "success": bool,
                "payment_order_id": str,
                "razorpay_order_id": str,
                "payment_link": str,
                "amount": float,
                "expires_at": datetime,
                "message": str
            }
        """
        logger.info(
            "Creating payment order",
            order_id=order_id,
            user_id=user_id,
            payment_source=payment_source
        )

        try:
            result = await self.razorpay_tool.execute(
                operation="create_order",
                order_id=order_id,
                user_id=user_id,
                payment_source=payment_source,
                session_id=session_id,
                # amount is intentionally NOT passed - tool fetches from DB
                notes=notes or {}
            )

            if result.status != ToolStatus.SUCCESS:
                error_message = result.data.get("error", "Failed to create payment order")
                logger.error(
                    "Failed to create payment order",
                    order_id=order_id,
                    error=error_message
                )
                return {
                    "success": False,
                    "message": error_message
                }

            data = result.data
            logger.info(
                "Payment order created successfully",
                order_id=order_id,
                payment_order_id=data.get("payment_order_id"),
                amount=data.get("amount")
            )

            return {
                "success": True,
                "payment_order_id": data.get("payment_order_id"),
                "razorpay_order_id": data.get("razorpay_order_id"),
                "payment_link": data.get("payment_link"),
                "amount": data.get("amount"),
                "expires_at": data.get("expires_at"),
                "message": f"Payment link created for ₹{data.get('amount', 0):.2f}"
            }

        except Exception as e:
            logger.error(
                "Unexpected error creating payment order",
                order_id=order_id,
                error=str(e)
            )
            return {
                "success": False,
                "message": f"Failed to create payment order: {str(e)}"
            }

    async def generate_payment_link(
        self,
        payment_order_id: str
    ) -> Dict[str, Any]:
        """
        Generate a new payment link for an existing payment order.

        Creates a fresh payment link if the previous one expired or needs to be resent.

        Args:
            payment_order_id: ID of the payment order

        Returns:
            Dict with new payment link details:
            {
                "success": bool,
                "payment_link": str,
                "expires_at": datetime,
                "message": str
            }
        """
        logger.info("Generating payment link", payment_order_id=payment_order_id)

        try:
            result = await self.razorpay_tool.execute(
                operation="create_link",
                payment_order_id=payment_order_id
            )

            if result.status != ToolStatus.SUCCESS:
                error_message = result.data.get("error", "Failed to generate payment link")
                logger.error(
                    "Failed to generate payment link",
                    payment_order_id=payment_order_id,
                    error=error_message
                )
                return {
                    "success": False,
                    "message": error_message
                }

            data = result.data
            logger.info(
                "Payment link generated successfully",
                payment_order_id=payment_order_id
            )

            return {
                "success": True,
                "payment_link": data.get("payment_link"),
                "expires_at": data.get("expires_at"),
                "message": "New payment link generated"
            }

        except Exception as e:
            logger.error(
                "Unexpected error generating payment link",
                payment_order_id=payment_order_id,
                error=str(e)
            )
            return {
                "success": False,
                "message": f"Failed to generate payment link: {str(e)}"
            }

    async def check_payment_status(
        self,
        order_id: Optional[str] = None,
        payment_order_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check the current status of a payment.

        Retrieves payment status and details. Can query by order_id or payment_order_id.

        Args:
            order_id: Restaurant order ID (optional)
            payment_order_id: Payment order ID (optional)

        Returns:
            Dict with payment status and transaction details:
            {
                "success": bool,
                "payment_order_id": str,
                "razorpay_order_id": str,
                "status": str,
                "amount": float,
                "payment_link": str,
                "expires_at": datetime,
                "retry_count": int,
                "can_retry": bool,
                "latest_transaction": dict,
                "message": str
            }
        """
        logger.info(
            "Checking payment status",
            order_id=order_id,
            payment_order_id=payment_order_id
        )

        try:
            result = await self.payment_status_tool.execute(
                operation="get_status",
                order_id=order_id,
                payment_order_id=payment_order_id
            )

            if result.status != ToolStatus.SUCCESS:
                error_message = result.data.get("error", "Failed to get payment status")
                logger.error(
                    "Failed to check payment status",
                    order_id=order_id,
                    payment_order_id=payment_order_id,
                    error=error_message
                )
                return {
                    "success": False,
                    "message": error_message
                }

            data = result.data
            status = data.get("status", "unknown")

            status_messages = {
                "created": "Payment pending - awaiting customer payment",
                "processing": "Payment is being processed",
                "paid": "Payment successful",
                "failed": "Payment failed",
                "expired": "Payment link expired"
            }

            logger.info(
                "Payment status retrieved",
                payment_order_id=data.get("payment_order_id"),
                status=status
            )

            return {
                "success": True,
                "payment_order_id": data.get("payment_order_id"),
                "razorpay_order_id": data.get("razorpay_order_id"),
                "status": status,
                "amount": data.get("amount"),
                "payment_link": data.get("payment_link"),
                "expires_at": data.get("expires_at"),
                "retry_count": data.get("retry_count"),
                "can_retry": data.get("can_retry"),
                "latest_transaction": data.get("latest_transaction"),
                "message": status_messages.get(status, f"Payment status: {status}")
            }

        except Exception as e:
            logger.error(
                "Unexpected error checking payment status",
                order_id=order_id,
                payment_order_id=payment_order_id,
                error=str(e)
            )
            return {
                "success": False,
                "message": f"Failed to check payment status: {str(e)}"
            }

    async def retry_payment(
        self,
        payment_order_id: str
    ) -> Dict[str, Any]:
        """
        Retry a failed or expired payment.

        Creates a new payment attempt for a previously failed payment.
        Generates a fresh payment link.

        Args:
            payment_order_id: ID of the payment order to retry

        Returns:
            Dict with new payment details and link:
            {
                "success": bool,
                "payment_link": str,
                "retry_count": int,
                "expires_at": datetime,
                "can_retry": bool,
                "message": str
            }
        """
        logger.info("Retrying payment", payment_order_id=payment_order_id)

        try:
            result = await self.razorpay_tool.execute(
                operation="retry_payment",
                payment_order_id=payment_order_id
            )

            if result.status != ToolStatus.SUCCESS:
                error = result.data.get("error", "Failed to retry payment")
                logger.error(
                    "Failed to retry payment",
                    payment_order_id=payment_order_id,
                    error=error,
                    can_retry=result.data.get("can_retry", False)
                )
                return {
                    "success": False,
                    "message": error,
                    "can_retry": result.data.get("can_retry", False)
                }

            data = result.data
            logger.info(
                "Payment retry successful",
                payment_order_id=payment_order_id,
                retry_count=data.get("retry_count")
            )

            return {
                "success": True,
                "payment_link": data.get("payment_link"),
                "retry_count": data.get("retry_count"),
                "expires_at": data.get("expires_at"),
                "message": f"Payment retry #{data.get('retry_count')} - new link generated"
            }

        except Exception as e:
            logger.error(
                "Unexpected error retrying payment",
                payment_order_id=payment_order_id,
                error=str(e)
            )
            return {
                "success": False,
                "message": f"Failed to retry payment: {str(e)}"
            }

    async def send_payment_link_sms(
        self,
        payment_order_id: str,
        phone: str
    ) -> Dict[str, Any]:
        """
        Send payment link to customer via SMS using existing SMSService.

        Fetches payment details from database and sends SMS with payment link.
        Uses the centralized SMSService for consistent SMS delivery.

        SECURITY: Payment amount and link are fetched from PaymentOrder database record,
        never from parameters.

        Args:
            payment_order_id: ID of the payment order
            phone: Customer's phone number

        Returns:
            Dict confirming SMS was sent:
            {
                "success": bool,
                "message": str,
                "amount": float,
                "order_number": str
            }
        """
        logger.info(
            "Sending payment link via SMS",
            payment_order_id=payment_order_id,
            phone=phone[-4:]  # Log only last 4 digits
        )

        try:
            from app.core.database import get_db_session
            # from app.shared.models import PaymentOrder
            from app.features.food_ordering.models import PaymentOrder
            from sqlalchemy import select
            from sqlalchemy.orm import selectinload

            # Fetch payment order from database (source of truth)
            async with get_db_session() as session:
                query = select(PaymentOrder).options(
                    selectinload(PaymentOrder.order)
                ).where(PaymentOrder.id == payment_order_id)

                result = await session.execute(query)
                payment_order = result.scalar_one_or_none()

                if not payment_order:
                    logger.error(
                        "Payment order not found",
                        payment_order_id=payment_order_id
                    )
                    return {
                        "success": False,
                        "message": "Payment order not found"
                    }

                if not payment_order.payment_link:
                    logger.error(
                        "No payment link available",
                        payment_order_id=payment_order_id
                    )
                    return {
                        "success": False,
                        "message": "No payment link available"
                    }

                # Use database values (not parameters)
                amount_rupees = float(payment_order.amount) / 100  # Convert paise to rupees
                order_number = payment_order.order.order_number
                payment_link = payment_order.payment_link

            # Create payment link SMS message
            message = (
                f"Payment link for your order {order_number} (₹{amount_rupees:.2f}): "
                f"{payment_link}\n\n"
                f"Link expires in 15 minutes."
            )

            # Use existing SMSService to send message
            sms_result = await self.sms_service.send_notification(
                phone_number=phone,
                message=message,
                notification_type="payment_link"
            )

            if not sms_result.get("success"):
                logger.error(
                    "Failed to send payment link SMS",
                    payment_order_id=payment_order_id,
                    phone=phone[-4:],
                    error=sms_result.get("error")
                )
                return {
                    "success": False,
                    "message": "Failed to send SMS"
                }

            logger.info(
                "Payment link SMS sent successfully",
                payment_order_id=payment_order_id,
                phone=phone[-4:],
                order_number=order_number,
                amount=amount_rupees
            )

            return {
                "success": True,
                "message": f"Payment link sent to {phone} via SMS",
                "amount": amount_rupees,
                "order_number": order_number
            }

        except Exception as e:
            logger.error(
                "Unexpected error sending payment link SMS",
                payment_order_id=payment_order_id,
                phone=phone[-4:],
                error=str(e)
            )
            return {
                "success": False,
                "message": f"Failed to send payment link: {str(e)}"
            }

    async def send_payment_link_whatsapp(
        self,
        payment_order_id: str,
        phone: str
    ) -> Dict[str, Any]:
        """
        Send payment link to customer via WhatsApp.

        Fetches payment details from database and sends WhatsApp message with payment link.

        SECURITY: Payment amount and link are fetched from PaymentOrder database record,
        never from parameters.

        Args:
            payment_order_id: ID of the payment order
            phone: Customer's WhatsApp number

        Returns:
            Dict confirming WhatsApp message was sent:
            {
                "success": bool,
                "message": str,
                "amount": float,
                "order_number": str
            }
        """
        logger.info(
            "Sending payment link via WhatsApp",
            payment_order_id=payment_order_id,
            phone=phone[-4:]  # Log only last 4 digits
        )

        try:
            from app.core.database import get_db_session
            # from app.shared.models import PaymentOrder
            from app.features.food_ordering.models import PaymentOrder
            from sqlalchemy import select
            from sqlalchemy.orm import selectinload

            # Fetch payment order from database (source of truth)
            async with get_db_session() as session:
                query = select(PaymentOrder).options(
                    selectinload(PaymentOrder.order)
                ).where(PaymentOrder.id == payment_order_id)

                result = await session.execute(query)
                payment_order = result.scalar_one_or_none()

                if not payment_order:
                    logger.error(
                        "Payment order not found",
                        payment_order_id=payment_order_id
                    )
                    return {
                        "success": False,
                        "message": "Payment order not found"
                    }

                if not payment_order.payment_link:
                    logger.error(
                        "No payment link available",
                        payment_order_id=payment_order_id
                    )
                    return {
                        "success": False,
                        "message": "No payment link available"
                    }

                # Use database values (not parameters)
                amount_rupees = float(payment_order.amount) / 100  # Convert paise to rupees
                order_number = payment_order.order.order_number
                payment_link = payment_order.payment_link

            # Create payment link WhatsApp message
            message = (
                f"Payment link for your order {order_number} (₹{amount_rupees:.2f}): "
                f"{payment_link}\n\n"
                f"Link expires in 15 minutes."
            )

            # Use WhatsApp Business tool to send message
            whatsapp_result = await self.whatsapp_tool.execute(
                operation="send_text",
                to_phone=phone,
                message=message
            )

            if whatsapp_result.status != ToolStatus.SUCCESS:
                logger.error(
                    "Failed to send payment link WhatsApp",
                    payment_order_id=payment_order_id,
                    phone=phone[-4:]
                )
                return {
                    "success": False,
                    "message": "Failed to send WhatsApp message"
                }

            logger.info(
                "Payment link WhatsApp sent successfully",
                payment_order_id=payment_order_id,
                phone=phone[-4:],
                order_number=order_number,
                amount=amount_rupees
            )

            return {
                "success": True,
                "message": f"Payment link sent to {phone} via WhatsApp",
                "amount": amount_rupees,
                "order_number": order_number
            }

        except Exception as e:
            logger.error(
                "Unexpected error sending payment link WhatsApp",
                payment_order_id=payment_order_id,
                phone=phone[-4:],
                error=str(e)
            )
            return {
                "success": False,
                "message": f"Failed to send payment link: {str(e)}"
            }

    async def get_payment_history(
        self,
        user_id: Optional[str] = None,
        order_id: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get payment history for a user or order.

        Retrieves past payment records and transaction history.

        Args:
            user_id: User ID to get payment history for (optional)
            order_id: Order ID to get payment history for (optional)
            limit: Maximum number of records to return (default 10)

        Returns:
            Dict with payment history records:
            {
                "success": bool,
                "history": List[dict],
                "count": int,
                "message": str
            }
        """
        logger.info(
            "Retrieving payment history",
            user_id=user_id,
            order_id=order_id,
            limit=limit
        )

        try:
            result = await self.payment_status_tool.execute(
                operation="get_history",
                user_id=user_id,
                order_id=order_id,
                limit=limit
            )

            if result.status != ToolStatus.SUCCESS:
                error_message = result.data.get("error", "Failed to get payment history")
                logger.error(
                    "Failed to retrieve payment history",
                    user_id=user_id,
                    order_id=order_id,
                    error=error_message
                )
                return {
                    "success": False,
                    "message": error_message,
                    "history": []
                }

            payments = result.data.get("payments", [])

            logger.info(
                "Payment history retrieved",
                user_id=user_id,
                order_id=order_id,
                count=len(payments)
            )

            return {
                "success": True,
                "history": payments,
                "count": len(payments),
                "message": f"Retrieved {len(payments)} payment record(s)"
            }

        except Exception as e:
            logger.error(
                "Unexpected error retrieving payment history",
                user_id=user_id,
                order_id=order_id,
                error=str(e)
            )
            return {
                "success": False,
                "message": f"Failed to get payment history: {str(e)}",
                "history": []
            }


# Global payment service instance (singleton pattern)
_payment_service: Optional[PaymentService] = None


def get_payment_service() -> PaymentService:
    """
    Get global payment service instance (singleton pattern).

    Returns:
        PaymentService instance
    """
    global _payment_service

    if _payment_service is None:
        _payment_service = PaymentService()
        logger.info("Global PaymentService instance created")

    return _payment_service


__all__ = ["PaymentService", "get_payment_service"]

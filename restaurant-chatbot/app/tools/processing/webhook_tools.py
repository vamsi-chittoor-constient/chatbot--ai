"""
Webhook Processing Tools
========================

Event processing tools for handling Razorpay webhook events:
- Webhook event processing with idempotency
- Payment status updates from webhooks
- Event-driven payment state management
- Reliable webhook event handling

Separated from external API calls for clean architecture.
"""

from datetime import datetime
from typing import Dict, Any

from sqlalchemy import select, update

from app.tools.base.tool_base import ToolBase, ToolResult, ToolStatus
from app.core.database import get_db_session
from app.shared.models import (
    PaymentOrder, PaymentTransaction, WebhookEvent, Order
)
from app.core.logging_config import get_logger
from app.utils.validation_decorators import require_tables
from app.utils.schema_serializer import serialize_output_with_schema
from app.schemas.payment import (
    PaymentOrderResponse,
    PaymentTransactionResponse,
    WebhookEventResponse
)

logger = get_logger(__name__)


class WebhookProcessingTool(ToolBase):
    """
    Webhook event processing tool for Razorpay events.
    Handles payment status updates and ensures exactly-once processing.
    """

    def __init__(self):
        super().__init__(
            name="webhook_processing",
            description="Process Razorpay webhook events and update payment status"
        )

    @require_tables("webhook_events,payment_transactions,payment_orders")
    async def _execute_impl(self, **kwargs) -> ToolResult:
        """
        Process webhook event with idempotency
        """
        event_id = kwargs.get("event_id")
        event_type = kwargs.get("event_type")
        payload = kwargs.get("payload")

        try:
            async with get_db_session() as session:
                # Check if event already processed (idempotency)
                existing_event_query = select(WebhookEvent).where(
                    WebhookEvent.event_id == event_id
                )
                existing_result = await session.execute(existing_event_query)
                existing_event = existing_result.scalar_one_or_none()

                if existing_event and existing_event.processed:
                    processed_time = existing_event.processed_at.isoformat() if existing_event.processed_at else "unknown"

                    # Serialize webhook event with schema
                    event_data = serialize_output_with_schema(
                        WebhookEventResponse,
                        existing_event,
                        self.name,
                        from_orm=True
                    )

                    return ToolResult(
                        status=ToolStatus.SUCCESS,
                        data={
                            "message": "Event already processed",
                            "event_id": event_id,
                            "processed_at": processed_time,
                            "webhook_event": event_data
                        }
                    )

                # Create webhook event record
                if not existing_event:
                    webhook_event = WebhookEvent(
                        event_id=event_id,
                        event_type=event_type,
                        account_id=kwargs.get("account_id"),
                        entity_type=kwargs.get("entity_type"),
                        entity_id=kwargs.get("entity_id"),
                        payload=payload,
                        processed=False
                    )
                    session.add(webhook_event)
                    await session.flush()
                else:
                    webhook_event = existing_event

                # Process based on event type (ensure not None)
                event_type_str = str(event_type) if event_type is not None else "unknown"
                payload_dict = payload if payload is not None else {}
                processing_result = await self._process_event_by_type(session, event_type_str, payload_dict)

                # Mark as processed
                webhook_event.processed = True
                webhook_event.processed_at = datetime.now()

                if not processing_result["success"]:
                    webhook_event.error_message = processing_result.get("error")

                await session.commit()

                # Serialize webhook event with schema
                event_data = serialize_output_with_schema(
                    WebhookEventResponse,
                    webhook_event,
                    self.name,
                    from_orm=True
                )

                return ToolResult(
                    status=ToolStatus.SUCCESS if processing_result["success"] else ToolStatus.FAILURE,
                    data={
                        "event_processed": True,
                        "event_id": event_id,
                        "event_type": event_type,
                        "webhook_event": event_data,
                        **processing_result
                    }
                )

        except Exception as e:
            logger.error(f"Webhook processing error: {str(e)}")
            return ToolResult(
                status=ToolStatus.FAILURE,
                data={"error": f"Webhook processing failed: {str(e)}"}
            )

    async def _process_event_by_type(self, session, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process webhook event based on type"""
        try:
            if event_type == "payment.captured":
                return await self._handle_payment_captured(session, payload)

            elif event_type == "payment.failed":
                return await self._handle_payment_failed(session, payload)

            elif event_type == "payment.authorized":
                return await self._handle_payment_authorized(session, payload)

            elif event_type == "order.paid":
                return await self._handle_order_paid(session, payload)

            else:
                logger.info(f"Unhandled event type: {event_type}")
                return {"success": True, "message": f"Event type {event_type} noted but not processed"}

        except Exception as e:
            logger.error(f"Error processing event type {event_type}: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _handle_payment_captured(self, session, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful payment capture"""
        payment_data = payload.get("payment", {}).get("entity", {})

        razorpay_payment_id = payment_data.get("id")
        razorpay_order_id = payment_data.get("order_id")
        amount = payment_data.get("amount")
        status = payment_data.get("status")
        method = payment_data.get("method")

        if not razorpay_payment_id or not razorpay_order_id:
            return {"success": False, "error": "Missing payment or order ID"}

        # Find payment order
        payment_order_query = select(PaymentOrder).where(
            PaymentOrder.razorpay_order_id == razorpay_order_id
        )
        payment_order_result = await session.execute(payment_order_query)
        payment_order = payment_order_result.scalar_one_or_none()

        if not payment_order:
            return {"success": False, "error": f"Payment order not found for {razorpay_order_id}"}

        # Create or update payment transaction
        transaction_query = select(PaymentTransaction).where(
            PaymentTransaction.razorpay_payment_id == razorpay_payment_id
        )
        transaction_result = await session.execute(transaction_query)
        transaction = transaction_result.scalar_one_or_none()

        if not transaction:
            transaction = PaymentTransaction(
                payment_order_id=payment_order.id,
                user_id=payment_order.user_id,
                order_id=payment_order.order_id,
                razorpay_payment_id=razorpay_payment_id,
                razorpay_order_id=razorpay_order_id,
                amount=amount,
                currency=payment_order.currency,
                method=method,
                status=status,
                gateway_response=payment_data
            )
            session.add(transaction)
        else:
            transaction.status = status
            transaction.gateway_response = payment_data

        # Update payment order status
        payment_order.status = "paid"

        # Update restaurant order status
        order_update = update(Order).where(Order.id == payment_order.order_id).values(
            status="confirmed"
        )
        await session.execute(order_update)

        return {
            "success": True,
            "message": "Payment captured successfully",
            "razorpay_payment_id": razorpay_payment_id,
            "amount": amount / 100,  # Convert back to rupees
            "order_id": payment_order.order_id
        }

    async def _handle_payment_failed(self, session, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle failed payment"""
        payment_data = payload.get("payment", {}).get("entity", {})

        razorpay_payment_id = payment_data.get("id")
        razorpay_order_id = payment_data.get("order_id")
        error_description = payment_data.get("error_description")

        # Find payment order and create failed transaction record
        payment_order_query = select(PaymentOrder).where(
            PaymentOrder.razorpay_order_id == razorpay_order_id
        )
        payment_order_result = await session.execute(payment_order_query)
        payment_order = payment_order_result.scalar_one_or_none()

        if payment_order:
            # Create failed transaction record
            failed_transaction = PaymentTransaction(
                payment_order_id=payment_order.id,
                user_id=payment_order.user_id,
                order_id=payment_order.order_id,
                razorpay_payment_id=razorpay_payment_id,
                razorpay_order_id=razorpay_order_id,
                amount=payment_order.amount,
                currency=payment_order.currency,
                status="failed",
                failure_reason=error_description,
                gateway_response=payment_data
            )
            session.add(failed_transaction)

            payment_order.status = "failed"

        return {
            "success": True,
            "message": "Payment failure recorded",
            "razorpay_payment_id": razorpay_payment_id,
            "failure_reason": error_description
        }

    async def _handle_payment_authorized(self, session, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle payment authorization (before capture)"""
        # Mark session as used for future implementation
        _ = session  # Will be used for payment authorization logic
        _ = payload  # Will be used for payment data processing

        # Similar logic to captured but with different status
        return {"success": True, "message": "Payment authorization handled"}

    async def _handle_order_paid(self, session, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle order fully paid event"""
        # Mark session as used for future implementation
        _ = session  # Will be used for order status updates
        _ = payload  # Will be used for order data processing

        # Additional processing for complete order payment
        return {"success": True, "message": "Order paid event handled"}


# Initialize tools for easy import
webhook_processing_tool = WebhookProcessingTool()

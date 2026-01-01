"""
Payment Message Handler
========================
Intercepts payment-related messages and routes them to the payment workflow.

This runs BEFORE the main crew agent to ensure payment is deterministic.
"""

import structlog
from typing import Optional, Dict, Any

from app.services.payment_state_service import (
    PaymentStep,
    PaymentMethod,
    get_payment_state,
    update_payment_step,
    is_payment_completed
)
from app.workflows.payment_workflow import run_payment_workflow
import asyncio

logger = structlog.get_logger("services.payment_handler")


async def handle_payment_message(
    session_id: str,
    message: str
) -> Optional[str]:
    """
    Check if message is payment-related and handle it.

    Returns:
        Response message if handled, None if should pass to crew agent
    """
    # Get current payment state
    payment_state = get_payment_state(session_id)
    current_step = payment_state.get("step")

    # Only intercept if we're in an active payment workflow
    if current_step not in [
        PaymentStep.SELECT_METHOD.value,
        PaymentStep.AWAITING_PAYMENT.value
    ]:
        return None  # Not in payment flow, let crew handle it

    message_lower = message.lower().strip()

    logger.info(
        "payment_message_intercepted",
        session_id=session_id,
        message=message_lower,
        current_step=current_step
    )

    # =========================================================================
    # STEP 1: Payment Method Selection
    # =========================================================================
    if current_step == PaymentStep.SELECT_METHOD.value:
        # Detect payment method from message
        method = None

        if any(word in message_lower for word in ["online", "pay_online", "card", "upi", "pay with card", "razorpay"]):
            method = PaymentMethod.ONLINE.value
        elif any(word in message_lower for word in ["cash", "pay_cash", "cod", "cash on delivery"]):
            method = PaymentMethod.CASH.value
        elif any(word in message_lower for word in ["pay_card_counter", "card at counter", "card later"]):
            method = PaymentMethod.CARD_AT_COUNTER.value

        if method:
            logger.info(
                "payment_method_selected",
                session_id=session_id,
                method=method
            )

            # Resume payment workflow with selected method
            order_id = payment_state.get("order_id")
            amount = payment_state.get("amount", 0.0)

            try:
                # Run payment workflow with selected method
                final_state = await run_payment_workflow(
                    session_id=session_id,
                    order_id=order_id,
                    amount=amount,
                    initial_method=method
                )

                # Workflow has completed - return confirmation
                if final_state.get("step") == PaymentStep.CASH_SELECTED.value:
                    return "✅ Payment method confirmed! Your order has been placed."
                elif final_state.get("step") == PaymentStep.AWAITING_PAYMENT.value:
                    return "✅ Payment link sent! Please complete the payment to confirm your order."
                elif final_state.get("step") == PaymentStep.PAYMENT_FAILED.value:
                    error = final_state.get("error", "Unknown error")
                    return f"❌ Payment setup failed: {error}"

            except Exception as e:
                logger.error(
                    "payment_workflow_resume_failed",
                    session_id=session_id,
                    error=str(e),
                    exc_info=True
                )
                return f"❌ Error processing payment: {str(e)}"

    # =========================================================================
    # STEP 2: Awaiting Payment Completion
    # =========================================================================
    elif current_step == PaymentStep.AWAITING_PAYMENT.value:
        # User is waiting for payment - inform them
        payment_link = payment_state.get("payment_link")

        if "status" in message_lower or "check" in message_lower or "completed" in message_lower:
            return (
                f"⏳ **Payment Status:** Awaiting payment\n\n"
                f"Please complete the payment using the link sent earlier:\n"
                f"{payment_link}\n\n"
                f"After payment, you'll receive a confirmation automatically."
            )

        # User asking something else while payment pending - remind them
        return (
            f"💡 **Quick Reminder:** You have a pending payment for your order.\n\n"
            f"Please complete payment here: {payment_link}\n\n"
            f"I'm here to help if you have any questions about your order!"
        )

    # Message not payment-related - let crew handle it
    return None


def is_payment_active(session_id: str) -> bool:
    """
    Check if there's an active payment workflow.

    Returns:
        True if payment is in progress
    """
    payment_state = get_payment_state(session_id)
    current_step = payment_state.get("step")

    return current_step in [
        PaymentStep.SELECT_METHOD.value,
        PaymentStep.AWAITING_PAYMENT.value
    ]

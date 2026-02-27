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


def _classify_payment_method(message: str) -> Optional[str]:
    """
    Classify natural language into a payment method.

    Checks keyword patterns in priority order (most specific first)
    to map user intent to PaymentMethod values.

    Returns:
        PaymentMethod value string, or None if no match.
    """
    msg = message.lower().strip()

    # --- Card at counter (check first — most specific) ---
    CARD_COUNTER_PHRASES = [
        "card at counter", "pay at counter", "pay at the counter",
        "card at the counter", "pay when i arrive", "pay at restaurant",
        "pay at the restaurant", "pay there", "pay later", "at counter",
        "at the counter", "when i arrive", "when i come",
    ]
    if any(phrase in msg for phrase in CARD_COUNTER_PHRASES):
        return PaymentMethod.CARD_AT_COUNTER.value

    # --- Cash ---
    CASH_PHRASES = [
        "cash on delivery", "pay cash", "pay by cash", "pay in cash",
        "cash payment",
    ]
    CASH_KEYWORDS = ["cash", "cod"]
    if any(phrase in msg for phrase in CASH_PHRASES):
        return PaymentMethod.CASH.value
    if any(word in msg.split() for word in CASH_KEYWORDS):
        return PaymentMethod.CASH.value

    # --- Online (broadest — check last) ---
    ONLINE_PHRASES = [
        "pay online", "online payment", "net banking", "netbanking",
    ]
    ONLINE_KEYWORDS = [
        "online", "upi", "razorpay", "gpay", "phonepe", "paytm",
        "digital", "card", "netbanking",
    ]
    if any(phrase in msg for phrase in ONLINE_PHRASES):
        return PaymentMethod.ONLINE.value
    if any(word in msg.split() for word in ONLINE_KEYWORDS):
        return PaymentMethod.ONLINE.value

    return None


async def handle_payment_message(
    session_id: str,
    message: str
) -> Optional[str]:
    """
    Check if message is payment-related and handle it.

    Returns:
        Response message if handled, None if should pass to crew agent
    """
    message_lower = message.lower().strip()

    # =========================================================================
    # POST-PAYMENT QUICK REPLY ACTIONS
    # =========================================================================
    # Handle quick replies from payment success card (view_receipt, order_more)
    # Also match natural language variations so typed requests work too.
    # Natural language only matches when a payment was actually completed
    # to avoid false triggers in normal conversation.
    _is_view_receipt = message_lower == "view_receipt"  # Button action: always match
    if not _is_view_receipt:
        _ps = get_payment_state(session_id)
        if _ps.get("order_id") and _ps.get("step") in ("payment_success", "cash_selected"):
            _is_view_receipt = (
                message_lower in ("view receipt", "show receipt", "show my receipt", "my receipt", "receipt", "download receipt")
                or ("receipt" in message_lower and any(kw in message_lower for kw in ["view", "show", "see", "get", "download"]))
            )
    if _is_view_receipt:
        payment_state = get_payment_state(session_id)
        display_id = payment_state.get("order_id", "")  # Display ID like "ORD-830A98E5"
        order_number = payment_state.get("order_number") or display_id or "N/A"
        payment_id = payment_state.get("payment_id", "")
        amount = payment_state.get("amount", 0)
        method = payment_state.get("method", "")
        method_label = {
            "online": "Online (Razorpay)",
            "cash": "Cash",
            "card_at_counter": "Card at Counter",
            "card": "Card at Counter",
        }.get(method, method or "Online")

        if display_id:
            pdf_url = f"/api/v1/payment/receipt/pdf?session_id={session_id}"

            lines = [
                "📄 **Order Receipt**\n",
                f"**Order:** {order_number}",
                f"**Amount:** ₹{amount:.2f}",
                f"**Payment:** {method_label}",
            ]
            if payment_id:
                lines.append(f"**Payment ID:** {payment_id}")
            lines.append("**Status:** Paid ✅\n")
            lines.append(f"📥 [Download PDF Receipt]({pdf_url})\n")
            lines.append("Anything else I can help you with?")

            return "\n".join(lines)

        return "📄 **Order Receipt**\n\nYour receipt will be sent to you via SMS and email shortly.\n\nAnything else I can help you with?"

    _is_order_more = message_lower == "order_more"  # Button action: always match
    if not _is_order_more:
        _ps2 = get_payment_state(session_id)
        if _ps2.get("order_id") and _ps2.get("step") in ("payment_success", "cash_selected"):
            _is_order_more = message_lower in ("order more", "order again", "order something else")
    if _is_order_more:
        from app.services.payment_state_service import clear_payment_state

        # Clear only payment state, keep cart and session intact for continuation
        clear_payment_state(session_id)

        return "🍽️ Great! What else would you like to order? I can show you our menu or you can tell me what you're craving!"

    # Get current payment state
    payment_state = get_payment_state(session_id)
    current_step = payment_state.get("step")
    order_id = payment_state.get("order_id")

    # Only intercept if we're in an active payment workflow
    # Check: 1) step is payment-related AND 2) there's an actual order_id
    if current_step not in [
        PaymentStep.SELECT_METHOD.value,
        PaymentStep.AWAITING_PAYMENT.value
    ] or not order_id:
        return None  # Not in payment flow, let crew handle it

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
        # Match exact button actions first, then fall back to NL classification.
        BUTTON_ACTION_MAP = {
            "pay_online": PaymentMethod.ONLINE.value,
            "pay_cash": PaymentMethod.CASH.value,
            "pay_card_counter": PaymentMethod.CARD_AT_COUNTER.value,
        }
        method = BUTTON_ACTION_MAP.get(message_lower)

        if not method:
            method = _classify_payment_method(message_lower)

        if method:
            logger.info(
                "payment_method_selected",
                session_id=session_id,
                method=method
            )

            # Resume payment workflow with selected method
            order_id = payment_state.get("order_id")
            amount = payment_state.get("amount", 0.0)
            existing_items = payment_state.get("items")
            existing_order_type = payment_state.get("order_type")
            existing_subtotal = payment_state.get("subtotal")
            existing_packaging = payment_state.get("packaging_charges")

            try:
                # Run payment workflow with selected method
                # Pass existing items/order_type/packaging so init doesn't lose them
                final_state = await run_payment_workflow(
                    session_id=session_id,
                    order_id=order_id,
                    amount=amount,
                    initial_method=method,
                    items=existing_items,
                    order_type=existing_order_type,
                    subtotal=existing_subtotal,
                    packaging_charges=existing_packaging
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

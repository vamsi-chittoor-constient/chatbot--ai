"""
Payment State Service
=====================
Manages payment workflow state per session in Redis.

Deterministic payment flow after checkout:
- Step 1: Select payment method (cash/online/card)
- Step 2: Generate payment link (if online)
- Step 3: Wait for payment completion
- Step 4: Payment confirmed/failed

This ensures payment is a guaranteed workflow, not probabilistic LLM decision.
"""

import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import structlog

from app.core.redis import get_sync_redis_client

logger = structlog.get_logger("services.payment_state")


class PaymentStep(str, Enum):
    """Payment workflow steps"""
    SELECT_METHOD = "select_method"           # Selecting payment method
    GENERATE_LINK = "generate_link"           # Generating payment link (online)
    AWAITING_PAYMENT = "awaiting_payment"     # Payment link sent, waiting
    PAYMENT_SUCCESS = "payment_success"       # Payment completed successfully
    PAYMENT_FAILED = "payment_failed"         # Payment failed/cancelled
    CASH_SELECTED = "cash_selected"           # Cash payment selected


class PaymentMethod(str, Enum):
    """Payment methods"""
    ONLINE = "online"          # Online payment (Razorpay)
    CASH = "cash"              # Cash on delivery/at counter
    CARD_AT_COUNTER = "card"   # Card payment at counter


def _get_payment_state_key(session_id: str) -> str:
    """Get Redis key for payment state"""
    return f"payment_state:{session_id}"


def get_payment_state(session_id: str) -> Dict[str, Any]:
    """
    Get current payment state for a session.

    Returns:
        Dict with:
        - step: Current payment step
        - method: Selected payment method
        - payment_link: Razorpay payment link (if online)
        - order_id: Order ID being paid for
        - amount: Payment amount
        - payment_id: Payment transaction ID (if completed)
        - completed: Boolean if payment workflow completed
    """
    redis = get_sync_redis_client()
    key = _get_payment_state_key(session_id)

    try:
        data = redis.get(key)
        if data:
            state = json.loads(data)
            logger.debug("payment_state_loaded", session_id=session_id, step=state.get("step"))
            return state
    except Exception as e:
        logger.warning("payment_state_load_failed", session_id=session_id, error=str(e))

    # Default state - need to select payment method
    return {
        "step": PaymentStep.SELECT_METHOD.value,
        "method": None,
        "payment_link": None,
        "order_id": None,
        "amount": 0.0,
        "payment_id": None,
        "completed": False,
        "created_at": datetime.now().isoformat()
    }


def set_payment_state(session_id: str, state: Dict[str, Any], ttl_hours: int = 2) -> bool:
    """
    Save payment state for a session.

    Args:
        session_id: Session identifier
        state: State dict to save
        ttl_hours: Time to live in hours (default 2 - payment links expire)

    Returns:
        True if saved successfully
    """
    redis = get_sync_redis_client()
    key = _get_payment_state_key(session_id)

    try:
        state["updated_at"] = datetime.now().isoformat()
        redis.setex(key, timedelta(hours=ttl_hours), json.dumps(state))
        logger.debug("payment_state_saved", session_id=session_id, step=state.get("step"))
        return True
    except Exception as e:
        logger.error("payment_state_save_failed", session_id=session_id, error=str(e))
        return False


def init_payment_workflow(
    session_id: str,
    order_id: str,
    amount: float,
    items: Optional[list] = None,
    order_type: Optional[str] = None,
    subtotal: Optional[float] = None,
    packaging_charges: Optional[float] = None
) -> Dict[str, Any]:
    """
    Initialize payment workflow for an order.

    Args:
        session_id: Session identifier
        order_id: Order ID to pay for
        amount: Total amount to pay (includes packaging)
        items: Cart items list (name, price, quantity) for receipt generation
        order_type: Order type (take_away) for receipt
        subtotal: Item subtotal before packaging charges
        packaging_charges: Total packaging charges

    Returns:
        Initial payment state
    """
    state = {
        "step": PaymentStep.SELECT_METHOD.value,
        "method": None,
        "payment_link": None,
        "order_id": order_id,
        "amount": amount,
        "payment_id": None,
        "completed": False,
        "created_at": datetime.now().isoformat()
    }

    # Store items for receipt generation
    if items:
        state["items"] = items
    if order_type:
        state["order_type"] = order_type
    if subtotal is not None:
        state["subtotal"] = subtotal
    if packaging_charges is not None:
        state["packaging_charges"] = packaging_charges

    set_payment_state(session_id, state)

    logger.info(
        "payment_workflow_initialized",
        session_id=session_id,
        order_id=order_id,
        amount=amount
    )

    return state


def update_payment_step(
    session_id: str,
    step: PaymentStep,
    method: Optional[str] = None,
    payment_link: Optional[str] = None,
    payment_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update payment workflow step.

    Args:
        session_id: Session identifier
        step: New payment step
        method: Payment method (optional)
        payment_link: Payment link (optional)
        payment_id: Payment transaction ID (optional)

    Returns:
        Updated state dict
    """
    state = get_payment_state(session_id)

    state["step"] = step.value

    if method:
        state["method"] = method
    if payment_link:
        state["payment_link"] = payment_link
    if payment_id:
        state["payment_id"] = payment_id

    state["completed"] = step in [
        PaymentStep.PAYMENT_SUCCESS,
        PaymentStep.PAYMENT_FAILED,
        PaymentStep.CASH_SELECTED
    ]

    set_payment_state(session_id, state)

    logger.info(
        "payment_step_updated",
        session_id=session_id,
        step=step.value,
        method=method,
        completed=state["completed"]
    )

    return state


def mark_payment_success(
    session_id: str,
    payment_id: str
) -> Dict[str, Any]:
    """
    Mark payment as successful.

    Args:
        session_id: Session identifier
        payment_id: Payment transaction ID

    Returns:
        Updated state dict
    """
    state = get_payment_state(session_id)

    state["step"] = PaymentStep.PAYMENT_SUCCESS.value
    state["payment_id"] = payment_id
    state["completed"] = True
    state["completed_at"] = datetime.now().isoformat()

    set_payment_state(session_id, state)

    logger.info(
        "payment_success",
        session_id=session_id,
        payment_id=payment_id,
        order_id=state.get("order_id")
    )

    return state


def mark_payment_failed(
    session_id: str,
    error: str
) -> Dict[str, Any]:
    """
    Mark payment as failed.

    Args:
        session_id: Session identifier
        error: Error message

    Returns:
        Updated state dict
    """
    state = get_payment_state(session_id)

    state["step"] = PaymentStep.PAYMENT_FAILED.value
    state["error"] = error
    state["completed"] = True
    state["failed_at"] = datetime.now().isoformat()

    set_payment_state(session_id, state)

    logger.info(
        "payment_failed",
        session_id=session_id,
        error=error,
        order_id=state.get("order_id")
    )

    return state


def is_payment_completed(session_id: str) -> bool:
    """Check if payment workflow is completed."""
    state = get_payment_state(session_id)
    return state.get("completed", False)


def clear_payment_state(session_id: str) -> bool:
    """Clear payment state for a session."""
    redis = get_sync_redis_client()
    key = _get_payment_state_key(session_id)

    try:
        redis.delete(key)
        logger.info("payment_state_cleared", session_id=session_id)
        return True
    except Exception as e:
        logger.error("payment_state_clear_failed", session_id=session_id, error=str(e))
        return False

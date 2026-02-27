"""
Payment Workflow
=================
Deterministic payment flow triggered after checkout.

Flow:
1. SELECT_METHOD → Ask user to choose payment method (Cash/Online/Card)
2. GENERATE_LINK → If online, generate Razorpay payment link
3. AWAIT_PAYMENT → Wait for payment completion (webhook callback)
4. COMPLETE → Payment success/failure

All messages are sent to the chat UI via AG-UI events.
"""

from typing import TypedDict, Literal, Dict, Any
from langgraph.graph import StateGraph, END
from datetime import datetime, timezone, timedelta
import structlog

from app.services.payment_state_service import (
    PaymentStep,
    PaymentMethod,
    init_payment_workflow,
    update_payment_step,
    mark_payment_success,
    mark_payment_failed,
    get_payment_state
)
from app.core.agui_events import (
    emit_quick_replies,
    emit_payment_link,
    emit_payment_method_selection
)
from app.tools.external_apis.razorpay_tools import razorpay_payment_tool
from app.core.redis import get_sync_redis_client
import json

logger = structlog.get_logger("workflows.payment")


class PaymentWorkflowState(TypedDict):
    """Payment workflow state"""
    session_id: str
    order_id: str
    amount: float
    method: str | None
    payment_link: str | None
    payment_id: str | None
    step: str
    error: str | None


async def select_payment_method_node(state: PaymentWorkflowState) -> PaymentWorkflowState:
    """
    Node 1: Ask user to select payment method.
    Shows QUICK_REPLIES with payment options (only if method not already selected).
    """
    session_id = state["session_id"]
    order_id = state["order_id"]
    amount = state["amount"]
    method = state.get("method")

    logger.info(
        "payment_workflow_select_method",
        session_id=session_id,
        order_id=order_id,
        amount=amount,
        pre_selected_method=method
    )

    # Only show payment method card if no method is pre-selected
    if not method:
        emit_payment_method_selection(session_id, [
            {
                "label": "💳 Pay Online",
                "action": "pay_online",
                "description": "Secure payment via Razorpay (Card/UPI/NetBanking)"
            },
            {
                "label": "💵 Cash",
                "action": "pay_cash",
                "description": "Pay cash on delivery or at counter"
            },
            {
                "label": "💳 Card at Counter",
                "action": "pay_card_counter",
                "description": "Pay by card when you arrive"
            }
        ], amount=amount, order_id=order_id)

    # Update state to waiting for method selection
    update_payment_step(session_id, PaymentStep.SELECT_METHOD)

    state["step"] = PaymentStep.SELECT_METHOD.value
    return state


async def generate_payment_link_node(state: PaymentWorkflowState) -> PaymentWorkflowState:
    """
    Node 2: Generate Razorpay payment link for online payment.

    Creates a DB Order + OrderItems first (Razorpay tool queries Order by UUID),
    then calls Razorpay to generate the payment link.
    """
    session_id = state["session_id"]
    order_id = state["order_id"]  # Display ID like "ORD-7AA36E8D"
    amount = state["amount"]

    logger.info(
        "payment_workflow_generate_link",
        session_id=session_id,
        order_id=order_id
    )

    try:
        # Get customer info from session
        redis_client = get_sync_redis_client()
        customer_key = f"session:{session_id}:customer"
        customer_data = redis_client.get(customer_key)

        customer_name = "Guest Customer"
        customer_email = f"guest_{session_id[:8]}@restaurant.com"
        customer_phone = "9999999999"

        if customer_data:
            customer = json.loads(customer_data)
            customer_name = customer.get("name", customer_name)
            customer_email = customer.get("email", customer_email)
            customer_phone = customer.get("phone", customer_phone)

        # ================================================================
        # CREATE DATABASE ORDER FIRST (Razorpay tool queries Order by UUID)
        # ================================================================
        import uuid as uuid_module
        from app.core.database import get_db_session
        from app.features.food_ordering.models import Order, OrderItem, OrderTotal
        from decimal import Decimal

        pending_order_key = f"pending_order:{session_id}"
        pending_order_data = redis_client.get(pending_order_key)

        if not pending_order_data:
            mark_payment_failed(session_id, "No pending order found")
            state["error"] = "No pending order found"
            state["step"] = PaymentStep.PAYMENT_FAILED.value
            return state

        pending_order = json.loads(pending_order_data)
        db_order_id = uuid_module.uuid4()

        async with get_db_session() as db_session:
            order = Order(
                order_id=db_order_id,
                order_invoice_number=order_id,  # Display ID "ORD-7AA36E8D"
            )
            db_session.add(order)
            await db_session.flush()

            for item in pending_order.get("items", []):
                item_price = float(item.get("price", 0))
                item_qty = int(item.get("quantity", 1))
                menu_item_id = item.get("id") or item.get("menu_item_id")

                order_item = OrderItem(
                    order_item_id=uuid_module.uuid4(),
                    order_id=db_order_id,
                    menu_item_id=uuid_module.UUID(menu_item_id) if menu_item_id else None,
                    base_price=item_price * item_qty,
                )
                db_session.add(order_item)

            # Create OrderTotal with packaging charges
            items_total = Decimal(str(pending_order.get("subtotal", amount)))
            packaging = Decimal(str(pending_order.get("packaging_charges", 0)))
            final = Decimal(str(pending_order.get("total", amount)))
            order_total = OrderTotal(
                order_total_id=uuid_module.uuid4(),
                order_id=db_order_id,
                items_total=items_total,
                charges_total=packaging,
                subtotal=items_total,
                final_amount=final,
            )
            db_session.add(order_total)

            await db_session.commit()

        logger.info(
            "db_order_created_for_payment",
            session_id=session_id,
            db_order_id=str(db_order_id),
            display_id=order_id
        )

        # Generate payment link using Razorpay (pass real UUID)
        payment_result = await razorpay_payment_tool._execute_impl(
            operation="create_order",
            order_id=str(db_order_id),  # Real UUID for DB query
            user_id="guest",
            payment_source="chat",
            session_id=session_id,
            notes={
                "order_id": order_id,  # Display ID for reference
                "db_order_id": str(db_order_id),
                "session_id": session_id,
                "customer_name": customer_name
            }
        )

        if payment_result.status.value == "success":
            payment_link = payment_result.data.get("payment_link")
            expires_at = payment_result.data.get("expires_at")

            # Update state
            update_payment_step(
                session_id,
                PaymentStep.AWAITING_PAYMENT,
                method=PaymentMethod.ONLINE.value,
                payment_link=payment_link
            )

            # Emit payment link via AG-UI event
            emit_payment_link(session_id, payment_link, amount, expires_at or "")

            # Clean up pending order from Redis
            redis_client.delete(pending_order_key)

            state["payment_link"] = payment_link
            state["step"] = PaymentStep.AWAITING_PAYMENT.value

            logger.info(
                "payment_link_generated",
                session_id=session_id,
                payment_link=payment_link[:50]
            )

        else:
            error_msg = payment_result.data.get("error", "Unknown error")
            logger.error("payment_link_generation_failed", error=error_msg)

            mark_payment_failed(session_id, error_msg)

            state["error"] = error_msg
            state["step"] = PaymentStep.PAYMENT_FAILED.value

    except Exception as e:
        logger.error("payment_link_error", error=str(e), exc_info=True)

        mark_payment_failed(session_id, str(e))

        state["error"] = str(e)
        state["step"] = PaymentStep.PAYMENT_FAILED.value

    return state


async def handle_cash_payment_node(state: PaymentWorkflowState) -> PaymentWorkflowState:
    """
    Node 3: Handle cash payment selection.
    """
    session_id = state["session_id"]
    order_id = state["order_id"]
    amount = state["amount"]

    logger.info(
        "payment_workflow_cash_selected",
        session_id=session_id,
        order_id=order_id
    )

    # Update state
    update_payment_step(
        session_id,
        PaymentStep.CASH_SELECTED,
        method=PaymentMethod.CASH.value
    )

    # ================================================================
    # CREATE DATABASE ORDER FOR CASH PAYMENT (No Razorpay needed)
    # ================================================================
    redis_client = get_sync_redis_client()
    pending_order_key = f"pending_order:{session_id}"
    pending_order_data = redis_client.get(pending_order_key)

    if pending_order_data:
        pending_order = json.loads(pending_order_data)

        from app.core.database import get_db_session
        from app.features.food_ordering.models import Order, OrderItem, OrderTotal
        from decimal import Decimal
        import uuid

        async with get_db_session() as db_session:
            db_order_id = uuid.uuid4()
            order = Order(
                order_id=db_order_id,
                order_invoice_number=order_id,  # Display ID "ORD-xxx" (String column)
            )
            db_session.add(order)
            await db_session.flush()

            for item in pending_order.get("items", []):
                item_price = float(item.get("price", 0))
                item_qty = int(item.get("quantity", 1))
                menu_item_id = item.get("id") or item.get("menu_item_id")

                order_item = OrderItem(
                    order_item_id=uuid.uuid4(),
                    order_id=db_order_id,
                    menu_item_id=uuid.UUID(menu_item_id) if menu_item_id else None,
                    base_price=item_price * item_qty,
                )
                db_session.add(order_item)

            # Create OrderTotal with packaging charges
            items_total = Decimal(str(pending_order.get("subtotal", amount)))
            packaging = Decimal(str(pending_order.get("packaging_charges", 0)))
            final = Decimal(str(pending_order.get("total", amount)))
            order_total = OrderTotal(
                order_total_id=uuid.uuid4(),
                order_id=db_order_id,
                items_total=items_total,
                charges_total=packaging,
                subtotal=items_total,
                final_amount=final,
            )
            db_session.add(order_total)

            await db_session.commit()

            redis_client.delete(pending_order_key)

            logger.info(
                "order_created_cash_payment",
                order_id=str(db_order_id),
                display_id=order_id,
                session_id=session_id
            )

    state["method"] = PaymentMethod.CASH.value
    state["step"] = PaymentStep.CASH_SELECTED.value

    return state


async def handle_card_counter_payment_node(state: PaymentWorkflowState) -> PaymentWorkflowState:
    """
    Node 4: Handle card at counter payment selection.
    """
    session_id = state["session_id"]
    order_id = state["order_id"]
    amount = state["amount"]

    logger.info(
        "payment_workflow_card_counter_selected",
        session_id=session_id,
        order_id=order_id
    )

    # Update state
    update_payment_step(
        session_id,
        PaymentStep.CASH_SELECTED,  # Reuse cash selected state (both are offline)
        method=PaymentMethod.CARD_AT_COUNTER.value
    )

    # ================================================================
    # CREATE DATABASE ORDER FOR CARD AT COUNTER (No Razorpay needed)
    # ================================================================
    redis_client = get_sync_redis_client()
    pending_order_key = f"pending_order:{session_id}"
    pending_order_data = redis_client.get(pending_order_key)

    if pending_order_data:
        pending_order = json.loads(pending_order_data)

        from app.core.database import get_db_session
        from app.features.food_ordering.models import Order, OrderItem, OrderTotal
        from decimal import Decimal
        import uuid

        async with get_db_session() as db_session:
            db_order_id = uuid.uuid4()
            order = Order(
                order_id=db_order_id,
                order_invoice_number=order_id,  # Display ID "ORD-xxx" (String column)
            )
            db_session.add(order)
            await db_session.flush()

            for item in pending_order.get("items", []):
                item_price = float(item.get("price", 0))
                item_qty = int(item.get("quantity", 1))
                menu_item_id = item.get("id") or item.get("menu_item_id")

                order_item = OrderItem(
                    order_item_id=uuid.uuid4(),
                    order_id=db_order_id,
                    menu_item_id=uuid.UUID(menu_item_id) if menu_item_id else None,
                    base_price=item_price * item_qty,
                )
                db_session.add(order_item)

            # Create OrderTotal with packaging charges
            items_total = Decimal(str(pending_order.get("subtotal", amount)))
            packaging = Decimal(str(pending_order.get("packaging_charges", 0)))
            final = Decimal(str(pending_order.get("total", amount)))
            order_total = OrderTotal(
                order_total_id=uuid.uuid4(),
                order_id=db_order_id,
                items_total=items_total,
                charges_total=packaging,
                subtotal=items_total,
                final_amount=final,
            )
            db_session.add(order_total)

            await db_session.commit()

            redis_client.delete(pending_order_key)

            logger.info(
                "order_created_card_counter_payment",
                order_id=str(db_order_id),
                display_id=order_id,
                session_id=session_id
            )

    state["method"] = PaymentMethod.CARD_AT_COUNTER.value
    state["step"] = PaymentStep.CASH_SELECTED.value

    return state


def route_payment_method(state: PaymentWorkflowState) -> Literal[
    "generate_link",
    "cash_payment",
    "card_counter_payment",
    "end"
]:
    """
    Router: Determine next step based on selected payment method.
    """
    method = state.get("method")

    if method == PaymentMethod.ONLINE.value or method == "pay_online":
        return "generate_link"
    elif method == PaymentMethod.CASH.value or method == "pay_cash":
        return "cash_payment"
    elif method == PaymentMethod.CARD_AT_COUNTER.value or method == "pay_card_counter":
        return "card_counter_payment"
    else:
        # No method selected - end workflow after showing options
        # User will respond, and payment_handler will resume with selected method
        return "end"


def should_end(state: PaymentWorkflowState) -> Literal["end"]:
    """Check if workflow should end."""
    step = state.get("step")

    if step in [
        PaymentStep.CASH_SELECTED.value,
        PaymentStep.PAYMENT_SUCCESS.value,
        PaymentStep.PAYMENT_FAILED.value,
        PaymentStep.AWAITING_PAYMENT.value  # End after sending payment link
    ]:
        return "end"

    return "select_method"


# Build the payment workflow graph
def create_payment_workflow() -> StateGraph:
    """
    Create the payment workflow graph.

    Flow:
    START → select_method → route → (generate_link | cash | card_counter) → END
    """
    workflow = StateGraph(PaymentWorkflowState)

    # Add nodes
    workflow.add_node("select_method", select_payment_method_node)
    workflow.add_node("generate_link", generate_payment_link_node)
    workflow.add_node("cash_payment", handle_cash_payment_node)
    workflow.add_node("card_counter_payment", handle_card_counter_payment_node)

    # Set entry point
    workflow.set_entry_point("select_method")

    # Add conditional routing from select_method
    workflow.add_conditional_edges(
        "select_method",
        route_payment_method,
        {
            "generate_link": "generate_link",
            "cash_payment": "cash_payment",
            "card_counter_payment": "card_counter_payment",
            "end": END
        }
    )

    # All payment paths end after completion
    workflow.add_edge("generate_link", END)
    workflow.add_edge("cash_payment", END)
    workflow.add_edge("card_counter_payment", END)

    return workflow.compile()


# Singleton instance
payment_workflow_graph = create_payment_workflow()


async def run_payment_workflow(
    session_id: str,
    order_id: str,
    amount: float,
    initial_method: str | None = None,
    items: list | None = None,
    order_type: str | None = None,
    subtotal: float | None = None,
    packaging_charges: float | None = None
) -> Dict[str, Any]:
    """
    Run the payment workflow for an order.

    Args:
        session_id: Session identifier
        order_id: Order ID to pay for
        amount: Total amount (includes packaging)
        initial_method: Pre-selected payment method (optional)
        items: Cart items for receipt generation (optional)
        order_type: Order type for receipt (optional)
        subtotal: Item subtotal before packaging (optional)
        packaging_charges: Total packaging charges (optional)

    Returns:
        Final workflow state
    """
    logger.info(
        "starting_payment_workflow",
        session_id=session_id,
        order_id=order_id,
        amount=amount,
        initial_method=initial_method
    )

    # Initialize payment state in Redis (with items for receipt)
    init_payment_workflow(
        session_id, order_id, amount,
        items=items, order_type=order_type,
        subtotal=subtotal, packaging_charges=packaging_charges
    )

    # Create initial state
    initial_state: PaymentWorkflowState = {
        "session_id": session_id,
        "order_id": order_id,
        "amount": amount,
        "method": initial_method,
        "payment_link": None,
        "payment_id": None,
        "step": PaymentStep.SELECT_METHOD.value,
        "error": None
    }

    # Run the workflow directly as a state machine.
    # Direct execution avoids async loop conflicts
    # when called from CrewAI tool threads via run_async().
    try:
        state = initial_state

        # Step 1: Select method (shows UI card if no method pre-selected)
        state = await select_payment_method_node(state)

        # Step 2: Route based on selected method
        route = route_payment_method(state)

        if route == "generate_link":
            state = await generate_payment_link_node(state)
        elif route == "cash_payment":
            state = await handle_cash_payment_node(state)
        elif route == "card_counter_payment":
            state = await handle_card_counter_payment_node(state)
        # else "end" — no method selected, workflow pauses for user input

        logger.info(
            "payment_workflow_completed",
            session_id=session_id,
            final_step=state.get("step"),
            method=state.get("method")
        )

        return state

    except Exception as e:
        logger.error(
            "payment_workflow_error",
            session_id=session_id,
            error=str(e),
            exc_info=True
        )

        mark_payment_failed(session_id, str(e))

        return {
            **initial_state,
            "step": PaymentStep.PAYMENT_FAILED.value,
            "error": str(e)
        }

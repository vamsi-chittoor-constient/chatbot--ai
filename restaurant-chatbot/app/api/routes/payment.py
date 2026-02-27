"""
Payment Callback Routes
=======================
Handles Razorpay payment callbacks and redirects based on payment source.

Two scenarios:
1. Chat payment: User pays from chat interface  Redirect back to chat
2. External payment: User pays from SMS/Email link  Show success page and close window
"""

from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional
from datetime import datetime, timezone
import structlog

from app.core.database import get_db_session
# from app.shared.models import PaymentOrder, Order, OrderItem
from app.features.food_ordering.models import PaymentOrder, Order
from app.core.config import config

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.post("/payment/verify")
async def verify_payment(
    request: Request,
    payment_link_id: Optional[str] = None,
    razorpay_payment_id: Optional[str] = None,
    session_id: Optional[str] = None
):
    """
    Client-side payment verification endpoint.

    This endpoint is called by the frontend after Razorpay redirects to success page.
    It verifies payment status by calling Razorpay API directly, then sends notifications.

    This approach works with localhost because:
    - Razorpay redirects to success URL (browser redirect - works locally)
    - Success page calls this endpoint (frontend to backend - works locally)
    - This endpoint calls Razorpay API to verify payment status
    - Then sends WebSocket notification and SMS

    Args:
        payment_link_id: Razorpay payment link ID
        razorpay_payment_id: Razorpay payment ID (if available)
        session_id: Chat session ID for WebSocket notification

    Returns:
        {
            "success": true/false,
            "payment_status": "paid"/"pending"/"failed",
            "order_id": "...",
            "message": "..."
        }
    """

    logger.info(
        "payment_verification_requested",
        payment_link_id=payment_link_id,
        razorpay_payment_id=razorpay_payment_id,
        session_id=session_id
    )

    if not payment_link_id:
        raise HTTPException(status_code=400, detail="payment_link_id is required")

    try:
        # Import Razorpay client
        import razorpay

        # Use payment config from app.utils.config
        razorpay_client = razorpay.Client(
            auth=(config.RAZORPAY_KEY_ID, config.RAZORPAY_KEY_SECRET)
        )

        # Fetch payment link details from Razorpay API
        payment_link = razorpay_client.payment_link.fetch(payment_link_id)

        logger.info(
            "razorpay_payment_link_fetched",
            payment_link_id=payment_link_id,
            status=payment_link.get('status'),
            amount_paid=payment_link.get('amount_paid')
        )

        # Check if payment is completed
        if payment_link.get('status') == 'paid':
            # Payment successful - process it
            async with get_db_session() as session:
                # Find payment order by link ID
                payment_query = select(PaymentOrder).where(
                    PaymentOrder.payment_link_id == payment_link_id
                )
                result = await session.execute(payment_query)
                payment_order = result.scalar_one_or_none()

                if not payment_order:
                    logger.warning(
                        "payment_order_not_found_for_link",
                        payment_link_id=payment_link_id
                    )
                    return {
                        "success": False,
                        "payment_status": "paid",
                        "message": "Payment successful but order not found"
                    }

                # Check if already processed (avoid duplicate notifications)
                if payment_order.status == "paid":
                    logger.info(
                        "payment_already_processed",
                        payment_order_id=payment_order.id
                    )
                    return {
                        "success": True,
                        "payment_status": "paid",
                        "order_id": payment_order.order_id,
                        "message": "Payment already processed"
                    }

                # Update payment order status
                payment_order.status = "paid"
                if razorpay_payment_id:
                    payment_order.razorpay_payment_id = razorpay_payment_id

                # ================================================================
                # LOOK UP EXISTING ORDER (already created by payment workflow)
                # ================================================================
                order = None
                if payment_order.order_id:
                    order_query = select(Order).where(
                        Order.order_id == payment_order.order_id
                    )
                    order_result = await session.execute(order_query)
                    order = order_result.scalar_one_or_none()

                    if order:
                        logger.info(
                            "payment_verified_order_found",
                            order_id=str(order.order_id),
                            payment_order_id=payment_order.payment_order_id
                        )
                    else:
                        logger.warning(
                            "payment_verified_order_not_found",
                            order_id=str(payment_order.order_id),
                            payment_order_id=payment_order.payment_order_id
                        )

                await session.commit()

                # Send WebSocket notification to chat (if session_id provided)
                if session_id:
                    try:
                        from app.api.routes.chat import websocket_manager
                        import asyncio

                        # Send payment confirmation
                        await websocket_manager.send_message(
                            session_id=session_id,
                            message="Payment received! Your order has been confirmed. You will receive an SMS confirmation shortly.",
                            message_type="system_message"
                        )

                        logger.info(
                            "payment_verified_websocket_sent",
                            session_id=session_id,
                            order_id=str(order.order_id) if order else None
                        )

                        # Send follow-up message to continue conversation
                        await asyncio.sleep(1)  # Small delay for better UX
                        await websocket_manager.send_message(
                            session_id=session_id,
                            message="Is there anything else I can help you with? You can order more items, check our menu, or ask any questions!",
                            message_type="ai_response"
                        )

                    except Exception as e:
                        logger.warning(
                            "payment_verified_websocket_failed",
                            session_id=session_id,
                            error=str(e)
                        )

                # Send post-payment confirmation SMS
                try:
                    from app.services.sms_service import get_sms_service

                    if order and order.contact_phone:
                        # Calculate estimated ready time
                        ready_minutes = "20-25"
                        if order.estimated_ready_time:
                            time_diff = order.estimated_ready_time - datetime.now(timezone.utc)
                            ready_minutes = str(max(15, int(time_diff.total_seconds() / 60)))

                        # Format amount
                        amount_rupees = float(payment_order.amount) / 100

                        # Order type display
                        order_type_display = "dine-in" if order.order_type == "dine_in" else "takeout"

                        # Build items list
                        items_text = ""
                        if order.order_items:
                            items_list = []
                            for item in order.order_items[:5]:
                                item_name = item.menu_item.name if item.menu_item else "Item"
                                items_list.append(f"- {item.quantity}x {item_name}")
                            items_text = "\n".join(items_list)
                            if len(order.order_items) > 5:
                                items_text += f"\n...and {len(order.order_items) - 5} more"

                        # Create confirmation message
                        confirmation_message = (
                            f"Order Confirmed #{order.order_number}\n\n"
                            f"Items Ordered:\n{items_text}\n\n"
                            f"Total Paid: Rs.{amount_rupees:.2f}\n"
                            f"Ready in: {ready_minutes} minutes\n"
                            f"Order Type: {order_type_display.title()}\n\n"
                            f"Thank you for your order.\n"
                            f"A24 Restaurant"
                        )

                        # Send SMS
                        sms_service = get_sms_service()
                        sms_result = await sms_service.send_notification(
                            phone_number=order.contact_phone,
                            message=confirmation_message,
                            notification_type="order_confirmation"
                        )

                        if sms_result.get("success"):
                            logger.info(
                                "payment_verified_sms_sent",
                                order_id=str(order.order_id),
                                phone=order.contact_phone[-4:],
                                amount=amount_rupees
                            )
                        else:
                            logger.warning(
                                "payment_verified_sms_failed",
                                order_id=str(order.order_id),
                                error=sms_result.get("error")
                            )

                except Exception as e:
                    logger.error(
                        "payment_verified_sms_exception",
                        order_id=str(order.order_id) if order else None,
                        error=str(e)
                    )

                return {
                    "success": True,
                    "payment_status": "paid",
                    "order_id": payment_order.order_id,
                    "order_number": order.order_number if order else None,
                    "message": "Payment verified successfully"
                }

        else:
            # Payment not completed yet
            return {
                "success": False,
                "payment_status": payment_link.get('status', 'unknown'),
                "message": f"Payment status: {payment_link.get('status', 'unknown')}"
            }

    except Exception as e:
        logger.error(
            "payment_verification_error",
            payment_link_id=payment_link_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Payment verification failed: {str(e)}"
        )


@router.get("/payment/callback")
async def payment_callback(
    request: Request,
    razorpay_payment_id: Optional[str] = None,
    razorpay_payment_link_id: Optional[str] = None,
    razorpay_payment_link_reference_id: Optional[str] = None,
    razorpay_payment_link_status: Optional[str] = None,
    razorpay_signature: Optional[str] = None,
    source: str = "chat",  # "chat" or "external"
    session_id: Optional[str] = None
):
    """
    Payment callback from Razorpay after user completes payment.

    Only updates PaymentOrder status since Order is already created in checkout.
    """

    logger.info(
        "payment_callback_received",
        payment_id=razorpay_payment_id,
        link_id=razorpay_payment_link_id,
        reference_id=razorpay_payment_link_reference_id,
        status=razorpay_payment_link_status,
        source=source,
        session_id=session_id
    )

    # Payment successful
    if razorpay_payment_link_status == "paid":
        try:
            async with get_db_session() as session:
                # Find and update payment order
                payment_query = select(PaymentOrder).where(
                    PaymentOrder.payment_link_id == razorpay_payment_link_id
                )
                result = await session.execute(payment_query)
                payment_order = result.scalar_one_or_none()

                if payment_order:
                    # Update payment order status
                    payment_order.payment_order_status = "paid"
                    # Store the actual Razorpay payment ID (not order ID)
                    if razorpay_payment_id:
                        # Create a notes/metadata entry for the payment ID
                        if not payment_order.payment_metadata:
                            payment_order.payment_metadata = {}
                        payment_order.payment_metadata["razorpay_payment_id"] = razorpay_payment_id

                    await session.commit()

                    # Fetch the order to get order_invoice_number
                    from app.features.food_ordering.models.order import Order
                    order_query = select(Order).where(Order.order_id == payment_order.order_id)
                    order_result = await session.execute(order_query)
                    order = order_result.scalar_one_or_none()

                    logger.info(
                        "payment_success_updated",
                        payment_order_id=str(payment_order.payment_order_id),
                        order_id=str(payment_order.order_id),
                        amount=float(payment_order.order_amount) if payment_order.order_amount else 0
                    )

                    # Update Redis payment state so payment_handler stops intercepting
                    # Also store order_number and db_order_id for receipt generation
                    if session_id:
                        try:
                            from app.services.payment_state_service import (
                                mark_payment_success as _mark_success,
                                set_payment_state as _set_state
                            )
                            state = _mark_success(session_id, razorpay_payment_id or "")
                            # Store order details needed by view_receipt handler
                            state["order_number"] = str(order.order_invoice_number) if order and order.order_invoice_number else ""
                            state["db_order_id"] = str(payment_order.order_id)
                            _set_state(session_id, state)
                        except Exception as e:
                            logger.warning("mark_payment_success_failed", session_id=session_id, error=str(e))

                    # Send WebSocket notification to chat
                    # NOTE: Must send directly via WebSocket (not AGUI event queue)
                    # because the agui_task consumer has already exited after the
                    # previous message cycle's RUN_FINISHED.
                    if source == "chat" and session_id:
                        try:
                            from app.core.agui_events import PaymentSuccessEvent
                            from app.api.routes.chat import websocket_manager
                            import json as _json

                            order_number = str(order.order_invoice_number) if order and order.order_invoice_number else str(payment_order.order_id)
                            amount = float(payment_order.order_amount) if payment_order.order_amount else 0

                            # Build the AGUI event directly
                            event = PaymentSuccessEvent(
                                order_id=str(payment_order.order_id),
                                order_number=order_number,
                                amount=amount,
                                payment_id=razorpay_payment_id or "",
                                order_type="takeaway",
                                quick_replies=[
                                    {"label": "📄 View Receipt", "action": "view_receipt"},
                                    {"label": "🍽️ Order More", "action": "order_more"}
                                ]
                            )

                            # Send directly via WebSocket (same format as agui_task)
                            event_data = _json.loads(event.to_json())
                            ws_sent = await websocket_manager.send_message_with_metadata(
                                session_id=session_id,
                                message="",
                                message_type="agui_event",
                                metadata={
                                    "agui": event_data,
                                    "target_session": session_id
                                }
                            )

                            if ws_sent:
                                # Mark as delivered so reconnect doesn't re-send
                                try:
                                    from app.services.payment_state_service import (
                                        get_payment_state as _get_ps,
                                        set_payment_state as _set_ps
                                    )
                                    ps = _get_ps(session_id)
                                    ps["ws_delivered"] = True
                                    _set_ps(session_id, ps)
                                except Exception:
                                    pass  # Non-critical; reconnect will just re-deliver

                            logger.info(
                                "payment_success_sent_direct_websocket",
                                session_id=session_id,
                                order_number=order_number,
                                ws_delivered=ws_sent
                            )
                        except Exception as e:
                            logger.warning(
                                "payment_success_notification_failed",
                                session_id=session_id,
                                error=str(e)
                            )
                else:
                    logger.warning(
                        "payment_order_not_found",
                        payment_link_id=razorpay_payment_link_id
                    )

        except Exception as e:
            logger.error(
                "payment_callback_error",
                error=str(e),
                payment_id=razorpay_payment_id
            )

        # Show success page
        return HTMLResponse(content=f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Payment Successful</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        min-height: 100vh;
                        margin: 0;
                        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                    }}
                    .container {{
                        background: white;
                        padding: 3rem;
                        border-radius: 20px;
                        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                        text-align: center;
                        max-width: 400px;
                        animation: slideIn 0.3s ease-out;
                    }}
                    @keyframes slideIn {{
                        from {{ opacity: 0; transform: translateY(-20px); }}
                        to {{ opacity: 1; transform: translateY(0); }}
                    }}
                    .success-icon {{
                        width: 80px;
                        height: 80px;
                        background: #10b981;
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        margin: 0 auto 1.5rem;
                        animation: scaleIn 0.5s ease-out 0.2s both;
                    }}
                    @keyframes scaleIn {{
                        from {{ transform: scale(0); }}
                        to {{ transform: scale(1); }}
                    }}
                    .checkmark {{
                        width: 40px;
                        height: 40px;
                        border: 4px solid white;
                        border-left: none;
                        border-top: none;
                        transform: rotate(45deg);
                    }}
                    h1 {{
                        color: #1f2937;
                        margin: 0 0 0.5rem;
                        font-size: 1.875rem;
                    }}
                    p {{
                        color: #6b7280;
                        margin: 0 0 1.5rem;
                        font-size: 1rem;
                    }}
                    .payment-id {{
                        background: #f3f4f6;
                        padding: 0.75rem;
                        border-radius: 8px;
                        font-family: monospace;
                        font-size: 0.875rem;
                        color: #4b5563;
                        margin-bottom: 1.5rem;
                        word-break: break-all;
                    }}
                    .close-info {{
                        color: #9ca3af;
                        font-size: 0.875rem;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="success-icon">
                        <div class="checkmark"></div>
                    </div>
                    <h1>Payment Successful!</h1>
                    <p>Your payment has been processed successfully.</p>
                    <div class="payment-id">
                        Order: {razorpay_payment_link_reference_id or 'N/A'}
                    </div>
                    <p class="close-info">You can close this window and return to chat.</p>
                </div>

                <script>
                    // Auto-close window after 3 seconds
                    setTimeout(function() {{
                        window.close();
                    }}, 3000);
                </script>
            </body>
            </html>
        """)

    elif razorpay_payment_link_status == "cancelled":
        # Payment cancelled
        logger.info(
            "payment_cancelled",
            payment_link_id=razorpay_payment_link_id,
            source=source
        )

        return HTMLResponse(content="""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Payment Cancelled</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        min-height: 100vh;
                        margin: 0;
                        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
                    }
                    .container {
                        background: white;
                        padding: 3rem;
                        border-radius: 20px;
                        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                        text-align: center;
                        max-width: 400px;
                    }
                    .warning-icon {
                        width: 80px;
                        height: 80px;
                        background: #f59e0b;
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        margin: 0 auto 1.5rem;
                        font-size: 3rem;
                        color: white;
                    }
                    h1 {
                        color: #1f2937;
                        margin: 0 0 0.5rem;
                        font-size: 1.875rem;
                    }
                    p {
                        color: #6b7280;
                        margin: 0 0 1.5rem;
                        font-size: 1rem;
                    }
                    .close-info {
                        color: #9ca3af;
                        font-size: 0.875rem;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="warning-icon">!</div>
                    <h1>Payment Cancelled</h1>
                    <p>You cancelled the payment. No charges were made.</p>
                    <p class="close-info">This window will close in 3 seconds...</p>
                </div>

                <script>
                    setTimeout(function() {
                        window.close();
                    }, 3000);
                </script>
            </body>
            </html>
        """)

    else:
        # Payment failed
        logger.error(
            "payment_failed",
            payment_link_id=razorpay_payment_link_id,
            status=razorpay_payment_link_status,
            source=source
        )

        return HTMLResponse(content="""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Payment Failed</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        min-height: 100vh;
                        margin: 0;
                        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
                    }
                    .container {
                        background: white;
                        padding: 3rem;
                        border-radius: 20px;
                        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                        text-align: center;
                        max-width: 400px;
                    }
                    .error-icon {
                        width: 80px;
                        height: 80px;
                        background: #ef4444;
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        margin: 0 auto 1.5rem;
                        font-size: 3rem;
                        color: white;
                    }
                    h1 {
                        color: #1f2937;
                        margin: 0 0 0.5rem;
                        font-size: 1.875rem;
                    }
                    p {
                        color: #6b7280;
                        margin: 0 0 1.5rem;
                        font-size: 1rem;
                    }
                    .close-info {
                        color: #9ca3af;
                        font-size: 0.875rem;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="error-icon">✕</div>
                    <h1>Payment Failed</h1>
                    <p>Unfortunately, your payment could not be processed.</p>
                    <p>Please try again or contact support.</p>
                    <p class="close-info">This window will close in 5 seconds...</p>
                </div>

                <script>
                    setTimeout(function() {
                        window.close();
                    }, 5000);
                </script>
            </body>
            </html>
        """)


@router.get("/payment/receipt/pdf")
async def download_receipt_pdf(
    session_id: str = Query(..., description="Session ID to generate receipt for")
):
    """
    Generate and download a PDF receipt for a completed payment.

    Reads the payment state from Redis (which includes order details and
    cart items) and generates a formatted PDF receipt.
    """
    try:
        from app.services.payment_state_service import get_payment_state
        from app.services.receipt_pdf_service import generate_receipt_pdf

        payment_state = get_payment_state(session_id)

        if not payment_state.get("order_id"):
            raise HTTPException(status_code=404, detail="No order found for this session")

        if payment_state.get("step") not in ["payment_success", "cash_selected"]:
            raise HTTPException(status_code=400, detail="Payment not completed yet")

        pdf_bytes = generate_receipt_pdf(payment_state)

        order_id = payment_state.get("order_id", "order")
        filename = f"receipt_{order_id}.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("receipt_pdf_generation_failed", session_id=session_id, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate receipt: {str(e)}")




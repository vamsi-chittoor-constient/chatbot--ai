"""
Payment Callback Routes
=======================
Handles Razorpay payment callbacks and redirects based on payment source.

Two scenarios:
1. Chat payment: User pays from chat interface  Redirect back to chat
2. External payment: User pays from SMS/Email link  Show success page and close window
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional
from datetime import datetime, timezone
import structlog

from app.core.database import get_db_session
# from app.shared.models import PaymentOrder, Order, OrderItem
from app.features.food_ordering.models import PaymentOrder, Order, OrderItem
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
                # CREATE DATABASE ORDER AFTER PAYMENT SUCCESS
                # ================================================================
                # Retrieve pending order from Redis
                from app.core.redis import get_sync_redis_client
                import json

                redis_client = get_sync_redis_client()
                # Try to get pending order by order_id from payment_order notes
                notes = payment_order.notes or {}
                pending_session_id = notes.get("session_id")

                order = None
                if pending_session_id:
                    pending_order_key = f"pending_order:{pending_session_id}"
                    pending_order_data = redis_client.get(pending_order_key)

                    if pending_order_data:
                        pending_order = json.loads(pending_order_data)

                        # Create actual database order now that payment succeeded
                        from app.features.food_ordering.models import OrderType, OrderSourceType, OrderStatusType
                        from datetime import timedelta
                        import uuid

                        # Create order
                        order = Order(
                            order_id=uuid.uuid4(),
                            order_number=pending_order["order_id"],  # Use the reference ID
                            restaurant_id=uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890"),  # Default restaurant
                            user_id=payment_order.user_id if payment_order.user_id else None,
                            order_type_id=uuid.UUID("d1e2f3a4-b5c6-7890-abcd-123456789def"),  # Default order type
                            order_source_type_id=uuid.UUID("11111111-2222-3333-4444-555555555555"),  # Chat source
                            order_status_type_id=uuid.UUID("a1a1a1a1-b2b2-c3c3-d4d4-e5e5e5e5e5e5"),  # Confirmed status
                            total_amount=pending_order["total"],
                            payment_status="paid",
                            status="confirmed",
                            estimated_ready_time=datetime.now(timezone.utc) + timedelta(minutes=25),
                            created_at=datetime.now(timezone.utc)
                        )
                        session.add(order)
                        await session.flush()  # Get order.order_id

                        # Create order items
                        for item in pending_order.get("items", []):
                            order_item = OrderItem(
                                order_item_id=uuid.uuid4(),
                                order_id=order.order_id,
                                menu_item_id=uuid.UUID(item.get("menu_item_id")) if item.get("menu_item_id") else None,
                                quantity=item.get("quantity", 1),
                                unit_price=item.get("price", 0),
                                total_price=item.get("price", 0) * item.get("quantity", 1)
                            )
                            session.add(order_item)

                        # Delete pending order from Redis (order now confirmed)
                        redis_client.delete(pending_order_key)

                        logger.info(
                            "order_created_after_payment",
                            order_id=order.order_number,
                            order_uuid=str(order.order_id),
                            payment_order_id=payment_order.id,
                            amount=payment_order.amount / 100
                        )
                else:
                    logger.warning(
                        "pending_order_not_found_in_redis",
                        payment_order_id=payment_order.id,
                        session_id=pending_session_id
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
                            order_id=order.id if order else None
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
                                order_id=order.id,
                                phone=order.contact_phone[-4:],
                                amount=amount_rupees
                            )
                        else:
                            logger.warning(
                                "payment_verified_sms_failed",
                                order_id=order.id,
                                error=sms_result.get("error")
                            )

                except Exception as e:
                    logger.error(
                        "payment_verified_sms_exception",
                        order_id=order.id if order else None,
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
    source: str = "external",  # "chat" or "external"
    session_id: Optional[str] = None
):
    """
    Payment callback from Razorpay after user completes payment.

    Handles two scenarios:
    - source=chat: Redirect back to chat interface
    - source=external: Show success page and auto-close window

    Args:
        razorpay_payment_id: Payment ID from Razorpay
        razorpay_payment_link_id: Payment link ID
        razorpay_payment_link_reference_id: Reference ID (our order ID)
        razorpay_payment_link_status: Payment status (paid, cancelled, failed)
        razorpay_signature: Signature for verification
        source: Payment source ("chat" or "external")
        session_id: Chat session ID for chat payments
    """

    logger.info(
        "payment_callback_received",
        payment_id=razorpay_payment_id,
        link_id=razorpay_payment_link_id,
        status=razorpay_payment_link_status,
        source=source,
        session_id=session_id
    )

    # Check payment status
    if razorpay_payment_link_status == "paid":
        # Payment successful - update order status
        try:
            async with get_db_session() as session:
                # Find payment order by link ID
                payment_query = select(PaymentOrder).where(
                    PaymentOrder.payment_link_id == razorpay_payment_link_id
                )
                result = await session.execute(payment_query)
                payment_order = result.scalar_one_or_none()

                if payment_order:
                    # Update payment order status
                    payment_order.status = "paid"
                    payment_order.razorpay_payment_id = razorpay_payment_id

                    # Update associated order status (load order items for SMS)
                    order_query = select(Order).options(
                        selectinload(Order.order_items).selectinload(OrderItem.menu_item)
                    ).where(
                        Order.id == payment_order.order_id
                    )
                    order_result = await session.execute(order_query)
                    order = order_result.scalar_one_or_none()

                    if order:
                        order.payment_status = "paid"
                        order.status = "confirmed"

                        logger.info(
                            "payment_success_order_updated",
                            order_id=order.id,
                            payment_order_id=payment_order.id,
                            amount=payment_order.amount / 100  # Convert paise to rupees
                        )

                    await session.commit()

                    # Send WebSocket notification to original chat session (if chat payment)
                    if source == "chat" and session_id:
                        try:
                            from app.api.routes.chat import websocket_manager
                            import asyncio

                            # Send payment success message to original chat window
                            await websocket_manager.send_message(
                                session_id=session_id,
                                message="Payment received! Your order has been confirmed. You will receive an SMS confirmation shortly.",
                                message_type="system_message"
                            )

                            logger.info(
                                "payment_success_websocket_sent",
                                session_id=session_id,
                                order_id=order.id if order else None
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
                                "payment_success_websocket_failed",
                                session_id=session_id,
                                error=str(e)
                            )

                    # Send post-payment confirmation SMS (graceful degradation if fails)
                    try:
                        from app.services.sms_service import get_sms_service

                        if order and order.contact_phone:
                            # Calculate estimated ready time in minutes
                            ready_minutes = "20-25"  # default
                            if order.estimated_ready_time:
                                time_diff = order.estimated_ready_time - datetime.now(timezone.utc)
                                ready_minutes = str(max(15, int(time_diff.total_seconds() / 60)))

                            # Format amount in rupees
                            amount_rupees = float(payment_order.amount) / 100

                            # Order type display
                            order_type_display = "dine-in" if order.order_type == "dine_in" else "takeout"

                            # Build items list for SMS
                            items_text = ""
                            if order.order_items:
                                items_list = []
                                for item in order.order_items[:5]:  # Limit to first 5 items for SMS
                                    item_name = item.menu_item.name if item.menu_item else "Item"
                                    items_list.append(f"- {item.quantity}x {item_name}")
                                items_text = "\n".join(items_list)
                                if len(order.order_items) > 5:
                                    items_text += f"\n...and {len(order.order_items) - 5} more"

                            # Create ORDER confirmation message (plain text, no emojis)
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
                                    "post_payment_sms_sent",
                                    order_id=order.id,
                                    phone=order.contact_phone[-4:],
                                    amount=amount_rupees
                                )
                            else:
                                logger.warning(
                                    "post_payment_sms_failed",
                                    order_id=order.id,
                                    error=sms_result.get("error")
                                )

                    except Exception as e:
                        # SMS failure should NOT break payment callback
                        logger.error(
                            "post_payment_sms_exception",
                            order_id=order.id if order else None,
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
            # Continue to show success even if DB update fails
            # We can reconcile later via Razorpay API

        # Redirect based on source
        if source == "chat" and session_id:
            # Show success page and auto-close (WebSocket handles sending message to chat)
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
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
                            from {{
                                opacity: 0;
                                transform: translateY(-20px);
                            }}
                            to {{
                                opacity: 1;
                                transform: translateY(0);
                            }}
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
                            from {{
                                transform: scale(0);
                            }}
                            to {{
                                transform: scale(1);
                            }}
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
                            Payment ID: {razorpay_payment_id}
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

        else:
            # Show success page and auto-close window (for SMS/Email payments)
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
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
                            from {{
                                opacity: 0;
                                transform: translateY(-20px);
                            }}
                            to {{
                                opacity: 1;
                                transform: translateY(0);
                            }}
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
                            from {{
                                transform: scale(0);
                            }}
                            to {{
                                transform: scale(1);
                            }}
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
                            Payment ID: {razorpay_payment_id}
                        </div>
                        <p class="close-info">This window will close automatically in 3 seconds...</p>
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
        # Payment cancelled by user
        logger.info(
            "payment_cancelled",
            payment_link_id=razorpay_payment_link_id,
            source=source
        )

        if source == "chat" and session_id:
            # Show cancelled page that communicates back to parent chat window
            return HTMLResponse(content=f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Payment Cancelled</title>
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <style>
                        body {{
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            min-height: 100vh;
                            margin: 0;
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        }}
                        .container {{
                            background: white;
                            padding: 3rem;
                            border-radius: 20px;
                            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                            text-align: center;
                            max-width: 400px;
                        }}
                        .warning-icon {{
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
                        .close-info {{
                            color: #9ca3af;
                            font-size: 0.875rem;
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="warning-icon">!</div>
                        <h1>Payment Cancelled</h1>
                        <p>You cancelled the payment. No charges were made.</p>
                        <p class="close-info">Returning to chat...</p>
                    </div>

                    <script>
                        // Send payment cancelled message to parent chat window
                        if (window.opener && !window.opener.closed) {{
                            window.opener.postMessage({{
                                type: 'payment_cancelled',
                                session_id: '{session_id}'
                            }}, '*');

                            setTimeout(function() {{
                                window.close();
                            }}, 2000);
                        }} else {{
                            setTimeout(function() {{
                                window.location.href = '{config.FRONTEND_URL or "http://localhost:3000"}?payment=cancelled&session_id={session_id}';
                            }}, 2000);
                        }}
                    </script>
                </body>
                </html>
            """)
        else:
            # Show cancelled page
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
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
        # Payment failed or unknown status
        logger.error(
            "payment_failed",
            payment_link_id=razorpay_payment_link_id,
            status=razorpay_payment_link_status,
            source=source
        )

        if source == "chat" and session_id:
            # Show failure page that communicates back to parent chat window
            return HTMLResponse(content=f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Payment Failed</title>
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <style>
                        body {{
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            min-height: 100vh;
                            margin: 0;
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        }}
                        .container {{
                            background: white;
                            padding: 3rem;
                            border-radius: 20px;
                            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                            text-align: center;
                            max-width: 400px;
                        }}
                        .error-icon {{
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
                        .close-info {{
                            color: #9ca3af;
                            font-size: 0.875rem;
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="error-icon">X</div>
                        <h1>Payment Failed</h1>
                        <p>Unfortunately, your payment could not be processed.</p>
                        <p>Please try again or contact support.</p>
                        <p class="close-info">Returning to chat...</p>
                    </div>

                    <script>
                        // Send payment failed message to parent chat window
                        if (window.opener && !window.opener.closed) {{
                            window.opener.postMessage({{
                                type: 'payment_failed',
                                session_id: '{session_id}'
                            }}, '*');

                            setTimeout(function() {{
                                window.close();
                            }}, 2000);
                        }} else {{
                            setTimeout(function() {{
                                window.location.href = '{config.FRONTEND_URL or "http://localhost:3000"}?payment=failed&session_id={session_id}';
                            }}, 2000);
                        }}
                    </script>
                </body>
                </html>
            """)
        else:
            # Show failure page
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
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
                        <div class="error-icon">X</div>
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

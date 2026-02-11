"""
Cash on Delivery (COD) Order Confirmation Handler
"""
import json
from datetime import datetime
from pymongo import MongoClient
import os


def confirm_cod_order(session_id: str) -> str:
    """
    Confirm a pending order with Cash on Delivery payment method.

    Args:
        session_id: User session ID

    Returns:
        Confirmation message
    """
    from app.core.redis import redis_client, set_cart_sync
    from app.core.agui_events import emit_order_data
    import structlog

    logger = structlog.get_logger()

    try:
        # Get pending order from Redis
        pending_order_key = f"pending_order:{session_id}"
        pending_order_raw = redis_client.get(pending_order_key)

        if not pending_order_raw:
            return "No pending order found. Please checkout first."

        pending_order = json.loads(pending_order_raw)
        order_id = pending_order.get('order_id')
        items = pending_order.get('items', [])
        total = pending_order.get('total', 0)
        subtotal = pending_order.get('subtotal', total)
        packaging_charges = pending_order.get('packaging_charges', 0)
        order_type = pending_order.get('order_type', 'take_away')

        # Save to MongoDB
        try:
            mongo_url = os.getenv("MONGODB_CONNECTION_STRING", "mongodb://mongodb:27017")
            mongo_db = os.getenv("MONGODB_DATABASE_NAME", "restaurant_ai_analytics")

            client = MongoClient(mongo_url, serverSelectionTimeoutMS=2000)
            db = client[mongo_db]

            order_items_data = []
            for item in items:
                order_items_data.append({
                    "name": item.get("name", "Item"),
                    "quantity": item.get("quantity", 1),
                    "price": item.get("price", 0),
                    "item_total": item.get("price", 0) * item.get("quantity", 1)
                })

            order_doc = {
                "order_id": order_id,
                "session_id": session_id,
                "items": order_items_data,
                "subtotal": subtotal,
                "packaging_charges": packaging_charges,
                "total": total,
                "order_type": order_type,
                "status": "confirmed",
                "payment_status": "pending",
                "payment_method": "cash_on_delivery",
                "created_at": pending_order.get('created_at', datetime.now().isoformat()),
                "confirmed_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }

            db.orders.insert_one(order_doc)
            client.close()
            logger.info("cod_order_confirmed", session_id=session_id, order_id=order_id)

        except Exception as mongo_error:
            logger.warning("mongodb_order_persist_failed", error=str(mongo_error))
            return f"Order confirmation failed. Please try again."

        # Clear cart and pending order
        set_cart_sync(session_id, {"items": [], "total": 0})
        redis_client.delete(pending_order_key)

        # Emit order confirmation
        emit_order_data(
            session_id=session_id,
            order_id=order_id,
            items=items,
            total=total,
            status="confirmed",
            order_type=order_type
        )

        items_summary = ", ".join([f"{i.get('name')} x{i.get('quantity', 1)}" for i in items[:3]])
        if len(items) > 3:
            items_summary += f" and {len(items) - 3} more"

        total_quantity = sum(i.get('quantity', 1) for i in items)
        return (
            f"✅ Order confirmed!\n\n"
            f"📋 Order ID: {order_id}\n"
            f"🍽️ Items: {items_summary}\n"
            f"💰 Subtotal: Rs.{subtotal}\n"
            f"📦 Packaging: Rs.{packaging_charges} ({total_quantity} items x Rs.30)\n"
            f"💰 Total: Rs.{total}\n"
            f"📍 Type: Take-away\n"
            f"💵 Payment: Cash on Delivery\n\n"
            f"Please pay Rs.{total} in cash when your order arrives.\n"
            f"You can view your receipt by saying 'show receipt for {order_id}'\n\n"
            f"Thank you for your order!"
        )

    except Exception as e:
        logger.error("cod_confirmation_failed", error=str(e), session_id=session_id)
        return f"Order confirmation failed: {str(e)}"

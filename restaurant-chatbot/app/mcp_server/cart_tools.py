"""
MCP Cart Tools
==============
Direct database-backed tools for cart operations.
Uses Redis for fast access + PostgreSQL for persistence.
"""

from typing import Dict, Any, List, Optional
from langchain_core.tools import tool
import structlog

from app.services.hybrid_cart_manager import HybridCartManager
from app.mcp_server.menu_tools import get_menu_item

logger = structlog.get_logger("mcp.cart_tools")

# Initialize cart manager
cart_manager = HybridCartManager()


@tool
async def add_to_cart(
    item_name: str,
    quantity: int,
    session_id: str,
    user_id: Optional[str] = None,
    restaurant_id: str = "rest_001"
) -> Dict[str, Any]:
    """
    Add an item to the shopping cart.

    Args:
        item_name: Name of the menu item to add
        quantity: Quantity to add
        session_id: User session ID
        user_id: Optional user ID (for authenticated users)
        restaurant_id: Restaurant identifier

    Returns:
        Dict with cart update confirmation
    """
    logger.info(
        "add_to_cart called",
        item_name=item_name,
        quantity=quantity,
        session_id=session_id
    )

    try:
        # Get the menu item details
        item_result = await get_menu_item.ainvoke({"item_name": item_name, "restaurant_id": restaurant_id})

        if not item_result.get("success"):
            return {
                "success": False,
                "error": f"Item '{item_name}' not found in menu",
                "cart": None
            }

        item = item_result["item"]

        # Check availability
        if not item.get("is_available"):
            return {
                "success": False,
                "error": f"{item['name']} is currently out of stock",
                "cart": None
            }

        # Add to cart using hybrid cart manager
        cart_item = {
            "menu_item_id": item["id"],
            "name": item["name"],
            "price": item["price"],
            "quantity": quantity,
            "subtotal": item["price"] * quantity
        }

        # Get or create cart
        cart = await cart_manager.get_cart(session_id, user_id)
        if cart is None:
            cart = {
                "session_id": session_id,
                "user_id": user_id,
                "restaurant_id": restaurant_id,
                "items": [],
                "total": 0.0
            }

        # Add or update item in cart
        existing_item = None
        for idx, existing in enumerate(cart.get("items", [])):
            if existing.get("menu_item_id") == item["id"]:
                existing_item = existing
                cart["items"][idx]["quantity"] += quantity
                cart["items"][idx]["subtotal"] = cart["items"][idx]["quantity"] * cart["items"][idx]["price"]
                break

        if not existing_item:
            cart.setdefault("items", []).append(cart_item)

        # Recalculate total
        cart["total"] = sum(item["subtotal"] for item in cart.get("items", []))

        # Save to both Redis and PostgreSQL
        await cart_manager.save_cart(session_id, cart, user_id)

        logger.info(
            "add_to_cart success",
            item_name=item_name,
            quantity=quantity,
            cart_total=cart["total"]
        )

        return {
            "success": True,
            "message": f"Added {quantity}x {item['name']} to cart",
            "cart": cart,
            "item_added": {
                "name": item["name"],
                "quantity": quantity,
                "price": item["price"]
            }
        }

    except Exception as e:
        logger.error("add_to_cart failed", error=str(e), exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "cart": None
        }


@tool
async def view_cart(
    session_id: str,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    View the current shopping cart.

    Args:
        session_id: User session ID
        user_id: Optional user ID (for authenticated users)

    Returns:
        Dict with cart contents
    """
    logger.info("view_cart called", session_id=session_id)

    try:
        # Get cart from hybrid manager (returns List[Dict])
        cart_items = await cart_manager.get_cart(session_id, user_id)

        # Handle empty cart
        if not cart_items:
            return {
                "success": True,
                "cart": {
                    "items": [],
                    "total": 0.0,
                    "item_count": 0
                },
                "message": "Your cart is empty"
            }

        # Wrap list in dict structure
        cart = {
            "items": cart_items,
            "total": sum(item.get("subtotal", 0) for item in cart_items),
            "item_count": len(cart_items)
        }

        logger.info("view_cart success", session_id=session_id, item_count=cart["item_count"])

        return {
            "success": True,
            "cart": cart
        }

    except Exception as e:
        logger.error("view_cart failed", error=str(e), exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "cart": None
        }


@tool
async def update_cart_item(
    item_name: str,
    new_quantity: int,
    session_id: str,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update the quantity of an item in the cart.

    Args:
        item_name: Name of the item to update
        new_quantity: New quantity (0 to remove)
        session_id: User session ID
        user_id: Optional user ID

    Returns:
        Dict with updated cart
    """
    logger.info(
        "update_cart_item called",
        item_name=item_name,
        new_quantity=new_quantity,
        session_id=session_id
    )

    try:
        # Get current cart
        cart = await cart_manager.get_cart(session_id, user_id)

        if cart is None or not cart.get("items"):
            return {
                "success": False,
                "error": "Cart is empty",
                "cart": None
            }

        # Find and update item
        item_found = False
        updated_items = []

        for item in cart.get("items", []):
            if item["name"].lower() == item_name.lower():
                item_found = True
                if new_quantity > 0:
                    item["quantity"] = new_quantity
                    item["subtotal"] = item["price"] * new_quantity
                    updated_items.append(item)
                # If new_quantity is 0, skip adding (removes item)
            else:
                updated_items.append(item)

        if not item_found:
            return {
                "success": False,
                "error": f"Item '{item_name}' not found in cart",
                "cart": None
            }

        # Update cart
        cart["items"] = updated_items
        cart["total"] = sum(item["subtotal"] for item in updated_items)

        # Save updated cart
        await cart_manager.save_cart(session_id, cart, user_id)

        logger.info("update_cart_item success", item_name=item_name, new_quantity=new_quantity)

        return {
            "success": True,
            "message": f"Updated {item_name} quantity to {new_quantity}" if new_quantity > 0 else f"Removed {item_name} from cart",
            "cart": cart
        }

    except Exception as e:
        logger.error("update_cart_item failed", error=str(e), exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "cart": None
        }


@tool
async def clear_cart(
    session_id: str,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Clear all items from the cart.

    Args:
        session_id: User session ID
        user_id: Optional user ID

    Returns:
        Dict with confirmation
    """
    logger.info("clear_cart called", session_id=session_id)

    try:
        # Clear cart using hybrid manager
        await cart_manager.clear_cart(session_id, user_id)

        logger.info("clear_cart success", session_id=session_id)

        return {
            "success": True,
            "message": "Cart cleared successfully",
            "cart": {
                "items": [],
                "total": 0.0,
                "item_count": 0
            }
        }

    except Exception as e:
        logger.error("clear_cart failed", error=str(e), exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


# Export all cart tools
CART_TOOLS = [add_to_cart, view_cart, update_cart_item, clear_cart]

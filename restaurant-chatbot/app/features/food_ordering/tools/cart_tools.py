"""
Cart Management Tools
=====================
Tools for managing shopping cart during order building phase.

Cart is stored in Redis for fast access during active session.
Once order is finalized, cart converts to actual order in database.
"""

from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime
import structlog

from app.tools.base.tool_base import ToolBase, ToolResult, ToolStatus, ToolError
from app.services.redis_service import RedisService
from app.services.inventory_cache_service import get_inventory_cache_service, InventoryReservationError
# NOTE: get_menu_cache_service imported lazily inside _execute_impl to avoid circular import
from app.utils.schema_tool_integration import serialize_output_with_schema
from app.schemas.common import (
    CartResponse,
    CartOperationResponse,
    ExistingCartResponse
)
# List formatting utilities for cart display
from app.utils.list_formatter import (
    format_cart_display,
    format_price
)

logger = structlog.get_logger(__name__)


class ViewCartTool(ToolBase):
    """
    View current cart contents with items, quantities, and total.
    """

    def __init__(self):
        super().__init__(
            name="view_cart",
            description="View current shopping cart contents",
            max_retries=1,
            timeout_seconds=5
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        if not kwargs.get('session_id'):
            raise ToolError("session_id is required", tool_name=self.name)
        return kwargs

    async def _execute_impl(self, **kwargs) -> ToolResult:
        session_id = kwargs['session_id']

        try:
            redis = RedisService()
            cart_key = f"cart:{session_id}"

            # Get cart from Redis
            cart_data = await redis.get(cart_key)

            if not cart_data or not cart_data.get('items'):
                cart_response = serialize_output_with_schema(
                    CartResponse,
                    {
                        "items": [],
                        "item_count": 0,
                        "subtotal": 0.0,
                        "message": "Your cart is empty"
                    },
                    self.name,
                    from_orm=False
                )
                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=cart_response
                )

            items = cart_data.get('items', [])
            subtotal = sum(item['price'] * item['quantity'] for item in items)

            cart_response = serialize_output_with_schema(
                CartResponse,
                {
                    "items": items,
                    "item_count": len(items),
                    "subtotal": float(subtotal),
                    "order_type": cart_data.get('order_type'),
                    "message": f"Your cart has {len(items)} items"
                },
                self.name,
                from_orm=False
            )

            return ToolResult(
                status=ToolStatus.SUCCESS,
                data=cart_response
            )

        except Exception as e:
            logger.error(f"Failed to view cart: {str(e)}")
            raise ToolError(f"Cart error: {str(e)}", tool_name=self.name)


class AddToCartTool(ToolBase):
    """
    Add item to cart with quantity.
    """

    def __init__(self):
        super().__init__(
            name="add_to_cart",
            description="Add menu item to shopping cart",
            max_retries=2,
            timeout_seconds=10
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        required = ['session_id', 'item_id', 'quantity']
        for field in required:
            if not kwargs.get(field):
                raise ToolError(f"{field} is required", tool_name=self.name)

        # Validate quantity
        try:
            quantity = int(kwargs['quantity'])
            if quantity < 1 or quantity > 50:
                raise ToolError("Quantity must be between 1 and 50", tool_name=self.name)
            kwargs['quantity'] = quantity
        except (ValueError, TypeError):
            raise ToolError("Quantity must be a valid number", tool_name=self.name)

        return kwargs

    async def _execute_impl(self, **kwargs) -> ToolResult:
        session_id = kwargs['session_id']
        item_id = kwargs['item_id']
        quantity = kwargs['quantity']

        # Use session_id as user_id for inventory reservations
        user_id = session_id

        try:
            # Lazy import to avoid circular import
            from app.services.menu_cache_service import get_menu_cache_service

            # Get menu item details from Redis cache (NO database query)
            menu_cache = get_menu_cache_service()
            menu_item_data = await menu_cache.get_item(item_id)

            # If not found by ID, try to find by name (context resolution)
            if not menu_item_data:
                # Search all items for name match (case-insensitive)
                all_items = await menu_cache.get_all_items()
                for item in all_items:
                    if item.get('name', '').lower() == item_id.lower():
                        menu_item_data = item
                        item_id = item['id']  # Use the actual ID
                        break

            if not menu_item_data:
                return ToolResult(
                    status=ToolStatus.FAILURE,
                    error=f"Menu item '{item_id}' not found"
                )

            if not menu_item_data.get("is_available", False):
                return ToolResult(
                    status=ToolStatus.FAILURE,
                    error=f"{menu_item_data['name']} is currently unavailable"
                )

            # Get or create cart
            redis = RedisService()
            cart_key = f"cart:{session_id}"
            cart_data = await redis.get(cart_key) or {"items": []}

            items = cart_data.get('items', [])

            # Check if item already in cart
            existing_item = None
            existing_qty = 0
            for item in items:
                if item['item_id'] == item_id:
                    existing_item = item
                    existing_qty = item['quantity']
                    break

            # Calculate final quantity
            if existing_item:
                final_quantity = existing_qty + quantity
                action = "updated"
            else:
                final_quantity = quantity
                action = "added"

            # CRITICAL: Reserve inventory BEFORE adding to cart
            inventory_cache = get_inventory_cache_service()
            try:
                # Check availability first
                is_available, available_qty = await inventory_cache.check_availability(
                    item_id=item_id,
                    quantity=final_quantity
                )

                if not is_available:
                    # Get alternative recommendations
                    alternatives_msg = await self._get_alternatives_message(item_id, menu_item_data['name'])

                    if available_qty > 0:
                        error_msg = f"Sorry, we only have {available_qty} of {menu_item_data['name']} available. Please reduce your quantity."
                    else:
                        error_msg = f"Sorry, {menu_item_data['name']} is currently out of stock."

                    # Append alternatives if found
                    if alternatives_msg:
                        error_msg += f" {alternatives_msg}"

                    return ToolResult(
                        status=ToolStatus.FAILURE,
                        error=error_msg
                    )

                # Reserve inventory atomically
                reservation_result = await inventory_cache.reserve_inventory(
                    item_id=item_id,
                    quantity=final_quantity,
                    user_id=user_id
                )

                logger.info(
                    "Inventory reserved for cart",
                    session_id=session_id,
                    item_id=item_id,
                    quantity=final_quantity,
                    reservation=reservation_result
                )

            except InventoryReservationError as e:
                # Out of stock or reservation failed - get alternatives
                alternatives_msg = await self._get_alternatives_message(item_id, menu_item_data['name'])

                error_msg = f"Sorry, {menu_item_data['name']} is out of stock."
                if alternatives_msg:
                    error_msg += f" {alternatives_msg}"

                return ToolResult(
                    status=ToolStatus.FAILURE,
                    error=error_msg
                )

            # Reservation successful - now update cart
            if existing_item:
                # Update existing item quantity
                existing_item['quantity'] = final_quantity
            else:
                # Add new item
                items.append({
                    'item_id': item_id,
                    'name': menu_item_data['name'],
                    'price': float(menu_item_data['price']),
                    'quantity': final_quantity,
                    'category': menu_item_data['category_id']
                })

            # Save cart
            cart_data['items'] = items
            cart_data['updated_at'] = str(datetime.now())
            await redis.set(cart_key, cart_data, ttl=3600)  # 1 hour TTL

            # Calculate new total
            subtotal = sum(item['price'] * item['quantity'] for item in items)

            logger.info(
                f"Cart {action}",
                session_id=session_id,
                item=menu_item_data['name'],
                quantity=final_quantity,
                subtotal=subtotal
            )

            operation_response = serialize_output_with_schema(
                CartOperationResponse,
                {
                    "action": action,
                    "item_name": menu_item_data['name'],
                    "quantity": final_quantity,
                    "item_price": float(menu_item_data['price']),
                    "item_total": float(menu_item_data['price'] * final_quantity),
                    "cart_subtotal": float(subtotal),
                    "cart_item_count": len(items),
                    "message": f"{action.capitalize()}: {final_quantity}x {menu_item_data['name']} (₹{float(menu_item_data['price'] * final_quantity)})"
                },
                self.name,
                from_orm=False
            )

            return ToolResult(
                status=ToolStatus.SUCCESS,
                data=operation_response
            )

        except Exception as e:
            logger.error(f"Failed to add to cart: {str(e)}", exc_info=True)
            raise ToolError(f"Cart error: {str(e)}", tool_name=self.name, retry_suggested=True)

    async def _get_alternatives_message(self, item_id: str, item_name: str) -> Optional[str]:
        """
        Get alternative recommendations for an out-of-stock item.

        Args:
            item_id: ID of the out-of-stock item
            item_name: Name of the out-of-stock item

        Returns:
            Formatted message with alternatives, or None if no alternatives found
        """
        try:
            # Import here to avoid circular dependency
            from app.features.food_ordering.tools.menu_ai_tools import FindSimilarItemsTool

            # Find similar items (limit to 3 for brevity)
            find_similar = FindSimilarItemsTool()
            result = await find_similar.execute(
                reference_item_id=item_id,
                limit=3,
                similarity_threshold=0.5,  # Lower threshold for more alternatives
                include_same_category=True  # Prefer same category
            )

            if result.status == ToolStatus.SUCCESS and result.data:
                similar_items = result.data.get('items', [])

                if similar_items:
                    # Format alternatives message
                    alt_names = [item['name'] for item in similar_items[:2]]  # Show max 2
                    if len(alt_names) == 1:
                        return f"However, you might like our {alt_names[0]}!"
                    elif len(alt_names) == 2:
                        return f"However, you might like our {alt_names[0]} or {alt_names[1]}!"

            return None

        except Exception as e:
            logger.warning(
                "Failed to get alternative recommendations",
                item_id=item_id,
                error=str(e)
            )
            return None


class RemoveFromCartTool(ToolBase):
    """
    Remove item from cart completely.
    """

    def __init__(self):
        super().__init__(
            name="remove_from_cart",
            description="Remove item from shopping cart",
            max_retries=1,
            timeout_seconds=5
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        if not kwargs.get('session_id'):
            raise ToolError("session_id is required", tool_name=self.name)
        if not kwargs.get('item_id'):
            raise ToolError("item_id is required", tool_name=self.name)
        return kwargs

    async def _execute_impl(self, **kwargs) -> ToolResult:
        session_id = kwargs['session_id']
        item_id = kwargs['item_id']

        # Use session_id as user_id for inventory reservations
        user_id = session_id

        try:
            redis = RedisService()
            cart_key = f"cart:{session_id}"
            cart_data = await redis.get(cart_key)

            if not cart_data or not cart_data.get('items'):
                return ToolResult(
                    status=ToolStatus.FAILURE,
                    error="Cart is empty"
                )

            items = cart_data['items']
            item_found = False
            item_name = ""

            # Remove item
            updated_items = []
            for item in items:
                if item['item_id'] == item_id:
                    item_found = True
                    item_name = item['name']
                else:
                    updated_items.append(item)

            if not item_found:
                return ToolResult(
                    status=ToolStatus.FAILURE,
                    error=f"Item not found in cart"
                )

            # CRITICAL: Release inventory reservation BEFORE removing from cart
            inventory_cache = get_inventory_cache_service()
            try:
                await inventory_cache.release_reservation(
                    item_id=item_id,
                    user_id=user_id
                )

                logger.info(
                    "Inventory reservation released",
                    session_id=session_id,
                    item_id=item_id,
                    item_name=item_name
                )

            except Exception as e:
                # Log error but continue with cart removal
                # (cart and inventory might be out of sync, but prioritize cart operation)
                logger.error(
                    "Failed to release inventory reservation",
                    session_id=session_id,
                    item_id=item_id,
                    error=str(e)
                )

            # Update cart
            cart_data['items'] = updated_items
            await redis.set(cart_key, cart_data, ttl=3600)

            # Calculate new total
            subtotal = sum(item['price'] * item['quantity'] for item in updated_items)

            logger.info(
                "Item removed from cart",
                session_id=session_id,
                item=item_name,
                remaining_items=len(updated_items)
            )

            operation_response = serialize_output_with_schema(
                CartOperationResponse,
                {
                    "item_name": item_name,
                    "cart_subtotal": float(subtotal),
                    "cart_item_count": len(updated_items),
                    "message": f"Removed {item_name} from cart"
                },
                self.name,
                from_orm=False
            )

            return ToolResult(
                status=ToolStatus.SUCCESS,
                data=operation_response
            )

        except Exception as e:
            logger.error(f"Failed to remove from cart: {str(e)}")
            raise ToolError(f"Cart error: {str(e)}", tool_name=self.name)


class UpdateCartQuantityTool(ToolBase):
    """
    Update quantity of an item already in cart.
    """

    def __init__(self):
        super().__init__(
            name="update_cart_quantity",
            description="Update quantity of item in cart",
            max_retries=1,
            timeout_seconds=5
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        required = ['session_id', 'item_id', 'new_quantity']
        for field in required:
            if not kwargs.get(field):
                raise ToolError(f"{field} is required", tool_name=self.name)

        # Validate quantity
        try:
            quantity = int(kwargs['new_quantity'])
            if quantity < 1 or quantity > 50:
                raise ToolError("Quantity must be between 1 and 50", tool_name=self.name)
            kwargs['new_quantity'] = quantity
        except (ValueError, TypeError):
            raise ToolError("Quantity must be a valid number", tool_name=self.name)

        return kwargs

    async def _execute_impl(self, **kwargs) -> ToolResult:
        session_id = kwargs['session_id']
        item_id = kwargs['item_id']
        new_quantity = kwargs['new_quantity']

        try:
            redis = RedisService()
            cart_key = f"cart:{session_id}"
            cart_data = await redis.get(cart_key)

            if not cart_data or not cart_data.get('items'):
                return ToolResult(
                    status=ToolStatus.FAILURE,
                    error="Cart is empty"
                )

            items = cart_data['items']
            item_found = False

            # Update quantity
            for item in items:
                if item['item_id'] == item_id:
                    old_quantity = item['quantity']
                    item['quantity'] = new_quantity
                    item_found = True
                    item_name = item['name']
                    item_price = item['price']
                    break

            if not item_found:
                return ToolResult(
                    status=ToolStatus.FAILURE,
                    error="Item not found in cart"
                )

            # Save cart
            await redis.set(cart_key, cart_data, ttl=3600)

            # Calculate new total
            subtotal = sum(item['price'] * item['quantity'] for item in items)

            logger.info(
                "Cart quantity updated",
                session_id=session_id,
                item=item_name,
                old_quantity=old_quantity,
                new_quantity=new_quantity
            )

            operation_response = serialize_output_with_schema(
                CartOperationResponse,
                {
                    "item_name": item_name,
                    "new_quantity": new_quantity,
                    "item_total": float(item_price * new_quantity),
                    "cart_subtotal": float(subtotal),
                    "message": f"Updated {item_name} quantity to {new_quantity}"
                },
                self.name,
                from_orm=False
            )

            return ToolResult(
                status=ToolStatus.SUCCESS,
                data=operation_response
            )

        except Exception as e:
            logger.error(f"Failed to update cart: {str(e)}")
            raise ToolError(f"Cart error: {str(e)}", tool_name=self.name)


class ClearCartTool(ToolBase):
    """
    Clear entire cart - start over.
    """

    def __init__(self):
        super().__init__(
            name="clear_cart",
            description="Clear all items from cart",
            max_retries=1,
            timeout_seconds=5
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        if not kwargs.get('session_id'):
            raise ToolError("session_id is required", tool_name=self.name)
        return kwargs

    async def _execute_impl(self, **kwargs) -> ToolResult:
        session_id = kwargs['session_id']

        # Use session_id as user_id for inventory reservations
        user_id = session_id

        try:
            redis = RedisService()
            cart_key = f"cart:{session_id}"

            # CRITICAL: Get cart items before clearing to release reservations
            cart_data = await redis.get(cart_key)

            if cart_data and cart_data.get('items'):
                items = cart_data.get('items', [])
                inventory_cache = get_inventory_cache_service()

                # Release all inventory reservations
                for item in items:
                    item_id = item.get('item_id')
                    if item_id:
                        try:
                            await inventory_cache.release_reservation(
                                item_id=item_id,
                                user_id=user_id
                            )

                            logger.info(
                                "Inventory reservation released during cart clear",
                                session_id=session_id,
                                item_id=item_id,
                                item_name=item.get('name')
                            )

                        except Exception as e:
                            # Log error but continue clearing other items
                            logger.error(
                                "Failed to release reservation during cart clear",
                                session_id=session_id,
                                item_id=item_id,
                                error=str(e)
                            )

            # Delete cart
            await redis.delete(cart_key)

            logger.info("Cart cleared", session_id=session_id)

            operation_response = serialize_output_with_schema(
                CartOperationResponse,
                {"message": "Cart cleared successfully"},
                self.name,
                from_orm=False
            )

            return ToolResult(
                status=ToolStatus.SUCCESS,
                data=operation_response
            )

        except Exception as e:
            logger.error(f"Failed to clear cart: {str(e)}")
            raise ToolError(f"Cart error: {str(e)}", tool_name=self.name)


class CheckExistingCartTool(ToolBase):
    """
    Check if user has existing cart items and prompt for continuation.

    Returns cart status and items so agent can ask:
    "I see you have items from your previous order. Would you like to continue with them or start fresh?"
    """

    def __init__(self):
        super().__init__(
            name="check_existing_cart",
            description="Check for existing cart items from previous session",
            max_retries=1,
            timeout_seconds=5
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        if not kwargs.get('session_id'):
            raise ToolError("session_id is required", tool_name=self.name)
        return kwargs

    async def _execute_impl(self, **kwargs) -> ToolResult:
        session_id = kwargs['session_id']

        try:
            redis = RedisService()
            cart_key = f"cart:{session_id}"

            # Get cart from Redis
            cart_data = await redis.get(cart_key)

            if not cart_data or not cart_data.get('items'):
                cart_response = serialize_output_with_schema(
                    ExistingCartResponse,
                    {
                        "has_existing_cart": False,
                        "items": [],
                        "item_count": 0,
                        "subtotal": 0.0,
                        "message": "No existing cart found"
                    },
                    self.name,
                    from_orm=False
                )
                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=cart_response
                )

            items = cart_data.get('items', [])
            subtotal = sum(item['price'] * item['quantity'] for item in items)

            logger.info(
                "Existing cart found",
                session_id=session_id,
                item_count=len(items),
                subtotal=subtotal
            )

            cart_response = serialize_output_with_schema(
                ExistingCartResponse,
                {
                    "has_existing_cart": True,
                    "items": items,
                    "item_count": len(items),
                    "subtotal": float(subtotal),
                    "cart_age_minutes": self._calculate_cart_age(cart_data),
                    "message": f"Found existing cart with {len(items)} items (₹{float(subtotal):.2f})"
                },
                self.name,
                from_orm=False
            )

            return ToolResult(
                status=ToolStatus.SUCCESS,
                data=cart_response
            )

        except Exception as e:
            logger.error(f"Failed to check existing cart: {str(e)}")
            raise ToolError(f"Cart error: {str(e)}", tool_name=self.name)

    def _calculate_cart_age(self, cart_data: Dict[str, Any]) -> Optional[int]:
        """Calculate how old the cart is in minutes"""
        try:
            if 'updated_at' in cart_data:
                from dateutil import parser
                updated_at = parser.parse(cart_data['updated_at'])
                age = (datetime.now() - updated_at).total_seconds() / 60
                return int(age)
        except Exception:
            pass
        return None


class MergeCartItemsTool(ToolBase):
    """
    Merge new items with existing cart items.

    Used when customer wants to keep previous cart and add new items.
    """

    def __init__(self):
        super().__init__(
            name="merge_cart_items",
            description="Merge new items with existing cart",
            max_retries=1,
            timeout_seconds=5
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        if not kwargs.get('session_id'):
            raise ToolError("session_id is required", tool_name=self.name)
        return kwargs

    async def _execute_impl(self, **kwargs) -> ToolResult:
        session_id = kwargs['session_id']
        new_items = kwargs.get('new_items', [])  # List of {item_id, quantity}
        keep_existing = kwargs.get('keep_existing', True)

        try:
            redis = RedisService()
            cart_key = f"cart:{session_id}"

            if not keep_existing:
                # Clear cart and start fresh
                logger.info(
                    "Clearing cart - user requested fresh start",
                    session_id=session_id,
                    cart_key=cart_key
                )

                # Delete the cart key and verify it worked
                deleted_count = await redis.delete(cart_key)

                # Verify cart is actually gone
                verification = await redis.get(cart_key)

                if verification is not None:
                    # Cart still exists! Something went wrong
                    logger.error(
                        "Cart deletion FAILED - cart still exists after delete",
                        session_id=session_id,
                        deleted_count=deleted_count,
                        cart_still_exists=True
                    )
                    return ToolResult(
                        status=ToolStatus.FAILURE,
                        error="Failed to clear cart - please try again"
                    )

                logger.info(
                    "Cart successfully cleared",
                    session_id=session_id,
                    deleted_count=deleted_count,
                    verified_empty=True
                )

                operation_response = serialize_output_with_schema(
                    CartOperationResponse,
                    {
                        "action": "cleared",
                        "message": "Cart cleared. You can now add new items."
                    },
                    self.name,
                    from_orm=False
                )
                # Add extra field
                operation_response['verified'] = True

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=operation_response
                )

            # Get existing cart
            cart_data = await redis.get(cart_key) or {"items": []}
            existing_items = cart_data.get('items', [])

            logger.info(
                "Keeping existing cart items",
                session_id=session_id,
                existing_count=len(existing_items)
            )

            # Calculate subtotal
            subtotal = sum(item['price'] * item['quantity'] for item in existing_items)

            # Use CartResponse for "kept" action since it includes items
            cart_response = serialize_output_with_schema(
                CartResponse,
                {
                    "items": existing_items,
                    "item_count": len(existing_items),
                    "subtotal": float(subtotal),
                    "message": f"Continuing with your previous cart ({len(existing_items)} items, ₹{float(subtotal):.2f})"
                },
                self.name,
                from_orm=False
            )
            # Add extra field
            cart_response['action'] = "kept"

            return ToolResult(
                status=ToolStatus.SUCCESS,
                data=cart_response
            )

        except Exception as e:
            logger.error(f"Failed to merge cart items: {str(e)}")
            raise ToolError(f"Cart error: {str(e)}", tool_name=self.name)


# Import datetime for timestamps
from datetime import datetime
from typing import Optional
from dateutil import parser

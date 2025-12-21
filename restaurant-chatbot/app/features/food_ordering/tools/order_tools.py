"""
Order Management Tools
=====================
Comprehensive tools for managing customer orders and order items.

Provides complete order lifecycle management:
- Create new orders
- Add/update/remove order items
- Calculate order totals with tax and discounts
- Update order status
- Retrieve order details and lists
"""

import uuid
import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional

from sqlalchemy import select, and_, or_, text, func, update
from sqlalchemy.orm import selectinload

from app.tools.base.tool_base import ToolBase, ToolResult, ToolStatus, ToolError
from app.core.database import get_db_session
from app.features.food_ordering.models import Order, OrderItem, MenuItem
from app.shared.models import User, OrderStatus
from app.core.logging_config import get_feature_logger
from app.utils.validation_decorators import validate_schema, require_tables
from app.utils.schema_tool_integration import (
    serialize_output_with_schema,
    safe_isoformat
)
from app.features.food_ordering.schemas.order import (
    OrderResponse,
    OrderItemResponse,
    OrderCalculationResponse,
    OrderSummaryResponse
)
# List formatting utilities for order display
from app.utils.list_formatter import (
    format_order_summary,
    format_price
)
# Phone normalization utility
from app.utils.phone_utils import normalize_phone_number

logger = get_feature_logger("food_ordering")


@validate_schema(Order)
@require_tables("orders", "users")
class CreateOrderTool(ToolBase):
    """
    Create a new customer order.

    Creates order with basic information and calculates initial totals.
    Order items are added separately using AddOrderItemTool.
    """

    def __init__(self):
        super().__init__(
            name="create_order",
            description="Create new customer order",
            max_retries=2,
            timeout_seconds=15
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        """
        Validate order creation parameters with detailed error messages.

        CRITICAL WORKFLOW: Order creation is the FINAL step, not first!
        - FIRST: Build cart with add_to_cart tool
        - THEN: Determine order_type (dine_in/takeout)
        - THEN: Get contact_phone from customer
        - FINALLY: Call create_order to finalize
        """
        # 3-Tier Authentication: At least one of user_id or device_id must be provided
        user_id = kwargs.get('user_id')
        device_id = kwargs.get('device_id')

        missing_fields = []

        if not user_id and not device_id:
            missing_fields.append("user_id or device_id (customer identification)")

        if not kwargs.get('order_type'):
            missing_fields.append("order_type (ask customer: 'Will this be dine-in or takeout?')")

        if not kwargs.get('contact_phone'):
            missing_fields.append("contact_phone (ask customer for their phone number)")

        # Normalize phone number to international format
        if kwargs.get('contact_phone'):
            try:
                kwargs['contact_phone'] = normalize_phone_number(kwargs['contact_phone'])
                logger.debug(f"Normalized phone number: {kwargs['contact_phone']}")
            except Exception as e:
                logger.warning(f"Failed to normalize phone number: {str(e)}")
                # Continue with original phone if normalization fails

        # If any fields are missing, provide comprehensive error message
        if missing_fields:
            error_details = "\n".join([f"  - {field}" for field in missing_fields])
            error_msg = (
                f"Cannot create order yet. Missing required information:\n"
                f"{error_details}\n\n"
                f"IMPORTANT WORKFLOW:\n"
                f"  1. Build cart FIRST using add_to_cart (don't create order yet!)\n"
                f"  2. Once cart is ready, ask: 'Will this be dine-in or takeout?'\n"
                f"  3. Get customer's phone number\n"
                f"  4. THEN create order to finalize\n\n"
                f"TIP: Don't rush to create_order! Let customer build their cart first."
            )
            raise ToolError(error_msg, tool_name=self.name)

        # Validate order_type - ONLY dine_in and takeout supported (NO delivery)
        valid_order_types = ['dine_in', 'takeout']
        if kwargs['order_type'] not in valid_order_types:
            raise ToolError(
                f"order_type must be one of: {valid_order_types}. Delivery is not supported.",
                tool_name=self.name
            )

        return kwargs

    def generate_order_number(self) -> str:
        """Generate unique order number"""
        # Format: ORD-YYYYMMDD-XXXX (where XXXX is random)
        date_part = datetime.now().strftime("%Y%m%d")
        random_part = str(uuid.uuid4())[:4].upper()
        return f"ORD-{date_part}-{random_part}"

    async def _execute_impl(self, **kwargs) -> ToolResult:
        try:
            async with get_db_session() as session:
                # 3-Tier Authentication: Handle user_id and device_id
                user_id = kwargs.get('user_id')
                device_id = kwargs.get('device_id')

                # Verify user exists if user_id is provided
                if user_id:
                    user_query = select(User).where(User.id == user_id)
                    user_result = await session.execute(user_query)
                    user = user_result.scalar_one_or_none()

                    if not user:
                        return ToolResult(
                            status=ToolStatus.FAILURE,
                            error="User not found"
                        )

                # Generate unique order number
                order_number = self.generate_order_number()

                # Ensure order number is unique
                while True:
                    existing_query = select(Order).where(Order.order_number == order_number)
                    existing_result = await session.execute(existing_query)
                    if not existing_result.scalar_one_or_none():
                        break
                    order_number = self.generate_order_number()

                # Create new order with 3-tier auth support
                new_order = Order(
                    user_id=user_id,  # May be None for Tier 2
                    device_id=device_id,  # May be None for Tier 3
                    order_number=order_number,
                    order_type=kwargs['order_type'],
                    status="pending",  # Use string for enum
                    subtotal=Decimal('0.00'),
                    tax_amount=kwargs.get('tax_amount', Decimal('0.00')),
                    discount_amount=kwargs.get('discount_amount', Decimal('0.00')),
                    total_amount=Decimal('0.00'),
                    special_instructions=kwargs.get('special_instructions'),
                    delivery_address=kwargs.get('delivery_address'),
                    contact_phone=kwargs['contact_phone'],
                    booking_id=kwargs.get('booking_id')
                )

                # Calculate estimated ready time if not provided
                if not kwargs.get('estimated_ready_time'):
                    if kwargs['order_type'] == 'dine_in':
                        base_time = 30  # Dine-in service
                    else:  # takeout
                        base_time = 25  # Takeout service

                    new_order.estimated_ready_time = datetime.now() + timedelta(minutes=base_time)
                else:
                    new_order.estimated_ready_time = kwargs['estimated_ready_time']

                session.add(new_order)
                await session.commit()
                await session.refresh(new_order)

                # Serialize order response using schema
                order_data = serialize_output_with_schema(
                    OrderResponse,
                    new_order,
                    self.name,
                    from_orm=True
                )

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=order_data,
                    metadata={"operation": "create_order"}
                )

        except Exception as e:
            logger.error(f"Failed to create order: {str(e)}")
            raise ToolError(f"Database error: {str(e)}", tool_name=self.name, retry_suggested=True)


@validate_schema(OrderItem)
@require_tables("order_items", "orders", "menu_items")
class AddOrderItemTool(ToolBase):
    """
    Add menu item to existing order.

    Creates order item with specified quantity and calculates pricing.
    Automatically updates order totals.
    """

    def __init__(self):
        super().__init__(
            name="add_order_item",
            description="Add menu item to order",
            max_retries=2,
            timeout_seconds=15
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        """Validate order item parameters"""
        required_fields = ['order_id', 'menu_item_id', 'quantity']
        for field in required_fields:
            if not kwargs.get(field):
                raise ToolError(f"{field} is required", tool_name=self.name)

        # Validate quantity
        if kwargs['quantity'] <= 0:
            raise ToolError("quantity must be positive", tool_name=self.name)

        return kwargs

    async def _execute_impl(self, **kwargs) -> ToolResult:
        try:
            async with get_db_session() as session:
                # Verify order exists and is modifiable
                order_query = select(Order).where(Order.id == kwargs['order_id'])
                order_result = await session.execute(order_query)
                order = order_result.scalar_one_or_none()

                if not order:
                    return ToolResult(
                        status=ToolStatus.FAILURE,
                        error="Order not found"
                    )

                if order.status in ['delivered', 'cancelled']:
                    return ToolResult(
                        status=ToolStatus.FAILURE,
                        error="Cannot modify completed or cancelled order"
                    )

                # Verify menu item exists and is available
                item_query = select(MenuItem).where(MenuItem.id == kwargs['menu_item_id'])
                item_result = await session.execute(item_query)
                menu_item = item_result.scalar_one_or_none()

                if not menu_item:
                    return ToolResult(
                        status=ToolStatus.FAILURE,
                        error="Menu item not found"
                    )

                if not menu_item.is_available:
                    return ToolResult(
                        status=ToolStatus.FAILURE,
                        error="Menu item is not available"
                    )

                # ========================================================================
                # INVENTORY CHECK & RESERVATION (Phase 2 Integration)
                # ========================================================================
                from app.services.inventory_cache_service import get_inventory_cache_service

                inventory_cache = get_inventory_cache_service()
                requested_quantity = kwargs['quantity']

                # Check if item already exists in order to calculate total quantity needed
                existing_item_query = select(OrderItem).where(
                    and_(
                        OrderItem.order_id == kwargs['order_id'],
                        OrderItem.menu_item_id == kwargs['menu_item_id']
                    )
                )
                existing_result = await session.execute(existing_item_query)
                existing_item = existing_result.scalar_one_or_none()

                if existing_item:
                    # Adding to existing item - only need to reserve the additional quantity
                    quantity_to_reserve = requested_quantity
                else:
                    # New item - reserve the full quantity
                    quantity_to_reserve = requested_quantity

                # Check availability and reserve inventory
                is_available, available_qty = await inventory_cache.check_availability(
                    kwargs['menu_item_id'],
                    quantity_to_reserve
                )

                if not is_available:
                    return ToolResult(
                        status=ToolStatus.FAILURE,
                        error=f"Insufficient inventory. Only {available_qty} available, but you requested {quantity_to_reserve}. Please reduce quantity."
                    )

                # Reserve the inventory for this user or device (3-tier auth)
                identifier = order.user_id or order.device_id
                reservation_success = await inventory_cache.reserve_inventory(
                    kwargs['menu_item_id'],
                    identifier,
                    quantity_to_reserve
                )

                if not reservation_success:
                    return ToolResult(
                        status=ToolStatus.FAILURE,
                        error="Failed to reserve inventory. Item may have been taken by another customer. Please try again."
                    )

                logger.info(
                    "inventory_reserved",
                    order_id=kwargs['order_id'],
                    user_id=order.user_id,
                    device_id=order.device_id,
                    item_id=kwargs['menu_item_id'],
                    quantity=quantity_to_reserve
                )
                # ========================================================================

                # Process the order item (existing_item already queried above)
                if existing_item:
                    # Update quantity of existing item
                    existing_item.quantity += kwargs['quantity']
                    existing_item.total_price = existing_item.unit_price * existing_item.quantity

                    if kwargs.get('customizations'):
                        existing_item.customizations = kwargs['customizations']
                    if kwargs.get('special_instructions'):
                        existing_item.special_instructions = kwargs['special_instructions']

                    order_item = existing_item
                    operation = "update_quantity"
                else:
                    # Create new order item
                    unit_price = menu_item.price
                    total_price = unit_price * kwargs['quantity']

                    new_order_item = OrderItem(
                        order_id=kwargs['order_id'],
                        menu_item_id=kwargs['menu_item_id'],
                        quantity=kwargs['quantity'],
                        unit_price=unit_price,
                        total_price=total_price,
                        customizations=kwargs.get('customizations'),
                        special_instructions=kwargs.get('special_instructions')
                    )

                    session.add(new_order_item)
                    order_item = new_order_item
                    operation = "add_item"

                # Recalculate order totals
                items_query = select(OrderItem).where(OrderItem.order_id == kwargs['order_id'])
                all_items_result = await session.execute(items_query)
                all_items = all_items_result.scalars().all()

                subtotal = sum(item.total_price for item in all_items)
                if not existing_item:  # Include new item if it's new
                    subtotal += order_item.total_price

                # Update order totals in database
                update_query = update(Order).where(Order.id == kwargs['order_id']).values(
                    subtotal=subtotal,
                    total_amount=subtotal + order.tax_amount - order.discount_amount
                )
                await session.execute(update_query)

                await session.commit()
                await session.refresh(order_item)

                # Serialize order item response using schema
                order_item_data = serialize_output_with_schema(
                    OrderItemResponse,
                    order_item,
                    self.name,
                    from_orm=True
                )

                # Add extra fields not in base schema
                order_item_data['menu_item_name'] = menu_item.name
                order_item_data['order_subtotal'] = float(order.subtotal)
                order_item_data['order_total'] = float(order.total_amount)

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=order_item_data,
                    metadata={"operation": operation}
                )

        except Exception as e:
            logger.error(f"Failed to add order item: {str(e)}")
            raise ToolError(f"Database error: {str(e)}", tool_name=self.name, retry_suggested=True)


@validate_schema(OrderItem)
class UpdateOrderItemTool(ToolBase):
    """
    Update existing order item quantity or customizations.

    Modifies order item details and recalculates order totals.
    """

    def __init__(self):
        super().__init__(
            name="update_order_item",
            description="Update order item details",
            max_retries=2,
            timeout_seconds=15
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        """Validate update parameters"""
        if not kwargs.get('order_item_id'):
            raise ToolError("order_item_id is required", tool_name=self.name)

        if 'quantity' in kwargs and kwargs['quantity'] <= 0:
            raise ToolError("quantity must be positive", tool_name=self.name)

        return kwargs

    async def _execute_impl(self, **kwargs) -> ToolResult:
        try:
            async with get_db_session() as session:
                # Get order item with related data
                item_query = select(OrderItem).options(selectinload(OrderItem.order)).where(
                    OrderItem.id == kwargs['order_item_id']
                )
                item_result = await session.execute(item_query)
                order_item = item_result.scalar_one_or_none()

                if not order_item:
                    return ToolResult(
                        status=ToolStatus.FAILURE,
                        error="Order item not found"
                    )

                # Check if order is modifiable
                if order_item.order.status in ['delivered', 'cancelled']:
                    return ToolResult(
                        status=ToolStatus.FAILURE,
                        error="Cannot modify completed or cancelled order"
                    )

                # ========================================================================
                # INVENTORY MANAGEMENT FOR QUANTITY CHANGES (Phase 2 Integration)
                # ========================================================================
                if 'quantity' in kwargs:
                    from app.services.inventory_cache_service import get_inventory_cache_service

                    inventory_cache = get_inventory_cache_service()
                    old_quantity = order_item.quantity
                    new_quantity = kwargs['quantity']
                    quantity_diff = new_quantity - old_quantity

                    if quantity_diff > 0:
                        # Increasing quantity - reserve additional inventory
                        is_available, available_qty = await inventory_cache.check_availability(
                            order_item.menu_item_id,
                            quantity_diff
                        )

                        if not is_available:
                            return ToolResult(
                                status=ToolStatus.FAILURE,
                                error=f"Insufficient inventory. Only {available_qty} more available. You currently have {old_quantity}, trying to update to {new_quantity}."
                            )

                        # 3-Tier auth: Use user_id or device_id as identifier
                        identifier = order_item.order.user_id or order_item.order.device_id
                        reservation_success = await inventory_cache.reserve_inventory(
                            order_item.menu_item_id,
                            identifier,
                            quantity_diff
                        )

                        if not reservation_success:
                            return ToolResult(
                                status=ToolStatus.FAILURE,
                                error="Failed to reserve additional inventory. Please try again."
                            )

                        logger.info(
                            "inventory_reserved_additional",
                            order_item_id=kwargs['order_item_id'],
                            item_id=order_item.menu_item_id,
                            quantity_added=quantity_diff,
                            new_total=new_quantity
                        )

                    elif quantity_diff < 0:
                        # Decreasing quantity - release inventory
                        # 3-Tier auth: Use user_id or device_id as identifier
                        identifier = order_item.order.user_id or order_item.order.device_id
                        await inventory_cache.release_reservation(
                            order_item.menu_item_id,
                            identifier,
                            abs(quantity_diff)
                        )

                        logger.info(
                            "inventory_released_partial",
                            order_item_id=kwargs['order_item_id'],
                            item_id=order_item.menu_item_id,
                            quantity_released=abs(quantity_diff),
                            new_total=new_quantity
                        )
                    # If quantity_diff == 0, no inventory changes needed
                # ========================================================================

                # Update fields
                if 'quantity' in kwargs:
                    order_item.quantity = kwargs['quantity']
                    order_item.total_price = order_item.unit_price * order_item.quantity

                if 'customizations' in kwargs:
                    order_item.customizations = kwargs['customizations']

                if 'special_instructions' in kwargs:
                    order_item.special_instructions = kwargs['special_instructions']

                # Recalculate order totals
                items_query = select(OrderItem).where(OrderItem.order_id == order_item.order_id)
                all_items_result = await session.execute(items_query)
                all_items = all_items_result.scalars().all()

                subtotal = sum(item.total_price for item in all_items)

                # Update order totals in database
                update_query = update(Order).where(Order.id == order_item.order_id).values(
                    subtotal=subtotal,
                    total_amount=subtotal + order_item.order.tax_amount - order_item.order.discount_amount
                )
                await session.execute(update_query)

                await session.commit()
                await session.refresh(order_item)

                # Serialize order item response using schema
                order_item_data = serialize_output_with_schema(
                    OrderItemResponse,
                    order_item,
                    self.name,
                    from_orm=True
                )

                # Add extra order summary fields
                order_item_data['order_subtotal'] = float(order_item.order.subtotal)
                order_item_data['order_total'] = float(order_item.order.total_amount)

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=order_item_data,
                    metadata={"operation": "update_order_item"}
                )

        except Exception as e:
            logger.error(f"Failed to update order item: {str(e)}")
            raise ToolError(f"Database error: {str(e)}", tool_name=self.name, retry_suggested=True)


@validate_schema(OrderItem)
class RemoveOrderItemTool(ToolBase):
    """
    Remove item from order.

    Deletes order item and recalculates order totals.
    """

    def __init__(self):
        super().__init__(
            name="remove_order_item",
            description="Remove item from order",
            max_retries=2,
            timeout_seconds=15
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        """Validate removal parameters"""
        if not kwargs.get('order_item_id'):
            raise ToolError("order_item_id is required", tool_name=self.name)
        return kwargs

    async def _execute_impl(self, **kwargs) -> ToolResult:
        try:
            async with get_db_session() as session:
                # Get order item with related data
                item_query = select(OrderItem).options(selectinload(OrderItem.order)).where(
                    OrderItem.id == kwargs['order_item_id']
                )
                item_result = await session.execute(item_query)
                order_item = item_result.scalar_one_or_none()

                if not order_item:
                    return ToolResult(
                        status=ToolStatus.FAILURE,
                        error="Order item not found"
                    )

                # Check if order is modifiable
                if order_item.order.status in ['delivered', 'cancelled']:
                    return ToolResult(
                        status=ToolStatus.FAILURE,
                        error="Cannot modify completed or cancelled order"
                    )

                order_id = order_item.order_id
                # 3-Tier auth: Use user_id or device_id as identifier
                identifier = order_item.order.user_id or order_item.order.device_id

                # Serialize removed item using schema
                removed_item_data = serialize_output_with_schema(
                    OrderItemResponse,
                    order_item,
                    self.name,
                    from_orm=True
                )

                # ========================================================================
                # INVENTORY RELEASE (Phase 2 Integration)
                # ========================================================================
                from app.services.inventory_cache_service import get_inventory_cache_service

                inventory_cache = get_inventory_cache_service()

                # Release the inventory reservation for this item
                await inventory_cache.release_reservation(
                    order_item.menu_item_id,
                    identifier,
                    order_item.quantity
                )

                logger.info(
                    "inventory_released",
                    order_id=order_id,
                    user_id=order_item.order.user_id,
                    device_id=order_item.order.device_id,
                    item_id=order_item.menu_item_id,
                    quantity=order_item.quantity
                )
                # ========================================================================

                # Remove item
                await session.delete(order_item)

                # Recalculate order totals
                remaining_items_query = select(OrderItem).where(OrderItem.order_id == order_id)
                remaining_items_result = await session.execute(remaining_items_query)
                remaining_items = remaining_items_result.scalars().all()

                # Get order for tax and discount amounts
                order_query = select(Order).where(Order.id == order_id)
                order_result = await session.execute(order_query)
                order = order_result.scalar_one()

                subtotal = sum(item.total_price for item in remaining_items)

                # Update order totals in database
                update_query = update(Order).where(Order.id == order_id).values(
                    subtotal=subtotal,
                    total_amount=subtotal + order.tax_amount - order.discount_amount
                )
                await session.execute(update_query)

                await session.commit()

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={
                        "removed_item": removed_item_data,
                        "order_id": order_id,
                        "remaining_items": len(remaining_items),
                        "order_subtotal": float(order.subtotal),
                        "order_total": float(order.total_amount)
                    },
                    metadata={"operation": "remove_order_item"}
                )

        except Exception as e:
            logger.error(f"Failed to remove order item: {str(e)}")
            raise ToolError(f"Database error: {str(e)}", tool_name=self.name, retry_suggested=True)


@validate_schema(Order)
class CalculateOrderTotalTool(ToolBase):
    """
    Calculate order totals with taxes and discounts.

    Recalculates subtotal, applies tax rates and discounts, updates total.
    """

    def __init__(self):
        super().__init__(
            name="calculate_order_total",
            description="Calculate order totals with tax and discounts",
            max_retries=2,
            timeout_seconds=10
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        """Validate calculation parameters"""
        if not kwargs.get('order_id'):
            raise ToolError("order_id is required", tool_name=self.name)
        return kwargs

    async def _execute_impl(self, **kwargs) -> ToolResult:
        try:
            async with get_db_session() as session:
                # Get order with items
                order_query = select(Order).options(selectinload(Order.order_items)).where(
                    Order.id == kwargs['order_id']
                )
                order_result = await session.execute(order_query)
                order = order_result.scalar_one_or_none()

                if not order:
                    return ToolResult(
                        status=ToolStatus.FAILURE,
                        error="Order not found"
                    )

                # Calculate subtotal from items
                subtotal = sum(item.total_price for item in order.order_items)

                # Apply tax rate (if provided)
                tax_rate = kwargs.get('tax_rate', 0.0)  # Default 0% tax
                tax_amount = subtotal * Decimal(str(tax_rate))

                # Apply discount (ensure it's a Decimal)
                discount_value = kwargs.get('discount_amount', 0.00)
                discount_amount = Decimal(str(discount_value))

                # Calculate final total
                total_amount = subtotal + tax_amount - discount_amount

                # Ensure total is not negative
                if total_amount < 0:
                    total_amount = Decimal('0.00')

                # Update order in database
                update_query = update(Order).where(Order.id == kwargs['order_id']).values(
                    subtotal=subtotal,
                    tax_amount=tax_amount,
                    discount_amount=discount_amount,
                    total_amount=total_amount
                )
                await session.execute(update_query)

                await session.commit()

                # Serialize calculation response using schema
                calc_data = serialize_output_with_schema(
                    OrderCalculationResponse,
                    order,
                    self.name,
                    from_orm=True
                )

                # Add calculation-specific fields
                calc_data['items_count'] = len(order.order_items)
                calc_data['tax_rate'] = tax_rate

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=calc_data,
                    metadata={"operation": "calculate_total"}
                )

        except Exception as e:
            logger.error(f"Failed to calculate order total: {str(e)}")
            raise ToolError(f"Database error: {str(e)}", tool_name=self.name, retry_suggested=True)


@validate_schema(Order)
class GetOrderTool(ToolBase):
    """
    Retrieve order details with items.

    Gets complete order information including all order items and menu details.
    """

    def __init__(self):
        super().__init__(
            name="get_order",
            description="Retrieve order details with items",
            max_retries=2,
            timeout_seconds=10
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        """Validate retrieval parameters"""
        if not kwargs.get('order_id') and not kwargs.get('order_number'):
            raise ToolError("Either order_id or order_number is required", tool_name=self.name)
        return kwargs

    async def _execute_impl(self, **kwargs) -> ToolResult:
        try:
            async with get_db_session() as session:
                # Build query conditions
                if kwargs.get('order_id'):
                    condition = Order.id == kwargs['order_id']
                else:
                    condition = Order.order_number == kwargs['order_number']

                # Get order with related data
                order_query = select(Order).options(
                    selectinload(Order.order_items).selectinload(OrderItem.menu_item),
                    selectinload(Order.user)
                ).where(condition)

                order_result = await session.execute(order_query)
                order = order_result.scalar_one_or_none()

                if not order:
                    return ToolResult(
                        status=ToolStatus.FAILURE,
                        error="Order not found"
                    )

                # Format order items
                # Serialize order items using schema
                items_data = []
                for item in order.order_items:
                    item_data = serialize_output_with_schema(
                        OrderItemResponse,
                        item,
                        self.name,
                        from_orm=True
                    )
                    # Add menu item name for convenience
                    item_data['menu_item_name'] = item.menu_item.name
                    items_data.append(item_data)

                # Serialize order response using schema
                order_data = serialize_output_with_schema(
                    OrderResponse,
                    order,
                    self.name,
                    from_orm=True
                )

                # Add items and computed fields
                order_data['user_name'] = order.user.full_name if order.user else None
                order_data['items'] = items_data
                order_data['items_count'] = len(items_data)

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=order_data,
                    metadata={"operation": "get_order"}
                )

        except Exception as e:
            logger.error(f"Failed to get order: {str(e)}")
            raise ToolError(f"Database error: {str(e)}", tool_name=self.name, retry_suggested=True)


@validate_schema(Order)
class UpdateOrderStatusTool(ToolBase):
    """
    Update order status and tracking information.

    Changes order status and updates relevant timestamps.
    """

    def __init__(self):
        super().__init__(
            name="update_order_status",
            description="Update order status and tracking",
            max_retries=2,
            timeout_seconds=10
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        """Validate status update parameters"""
        required_fields = ['order_id', 'status']
        for field in required_fields:
            if not kwargs.get(field):
                raise ToolError(f"{field} is required", tool_name=self.name)

        # Validate status
        valid_statuses = ['pending', 'confirmed', 'preparing', 'ready', 'delivered', 'cancelled']
        if kwargs['status'] not in valid_statuses:
            raise ToolError(f"status must be one of: {valid_statuses}", tool_name=self.name)

        return kwargs

    async def _execute_impl(self, **kwargs) -> ToolResult:
        try:
            async with get_db_session() as session:
                # Get order with items
                order_query = select(Order).options(selectinload(Order.order_items)).where(Order.id == kwargs['order_id'])
                order_result = await session.execute(order_query)
                order = order_result.scalar_one_or_none()

                if not order:
                    return ToolResult(
                        status=ToolStatus.FAILURE,
                        error="Order not found"
                    )

                old_status = order.status or "pending"
                new_status = kwargs['status']

                # CRITICAL VALIDATION: Prevent confirming orders without items
                if new_status == 'confirmed' and (not order.order_items or len(order.order_items) == 0):
                    logger.error(
                        "Order confirmation blocked - order has no items",
                        order_id=kwargs['order_id'],
                        order_number=order.order_number,
                        status=old_status
                    )
                    return ToolResult(
                        status=ToolStatus.FAILURE,
                        error="Cannot confirm order without items. Please add items to the order first."
                    )

                # Update status
                order.status = new_status

                # Update timestamps based on status
                if new_status == 'ready' and not order.estimated_ready_time:
                    order.estimated_ready_time = datetime.now()

                # Update estimated ready time if provided
                if kwargs.get('estimated_ready_time'):
                    order.estimated_ready_time = kwargs['estimated_ready_time']

                await session.commit()

                # ========================================================================
                # INVENTORY SYNC AFTER ORDER CONFIRMATION (Phase 2 Integration)
                # ========================================================================
                if new_status == 'confirmed' and old_status != 'confirmed':
                    # Order is being confirmed - sync inventory to database
                    # This updates total_stock_quantity (items leave kitchen)
                    from app.features.food_ordering.services.inventory_sync import get_inventory_sync_service

                    # Get order items for sync
                    items_query = select(OrderItem).where(OrderItem.order_id == kwargs['order_id'])
                    items_result = await session.execute(items_query)
                    order_items = items_result.scalars().all()

                    if order_items:
                        order_items_data = [
                            {
                                "item_id": item.menu_item_id,
                                "quantity": item.quantity
                            }
                            for item in order_items
                        ]

                        inventory_sync = get_inventory_sync_service()
                        # Run sync in background (non-blocking)
                        import asyncio
                        asyncio.create_task(
                            inventory_sync.sync_after_order(order_items_data)
                        )

                        logger.info(
                            "order_confirmed_inventory_sync_triggered",
                            order_id=kwargs['order_id'],
                            order_number=order.order_number,
                            items_count=len(order_items_data)
                        )

                    # Send order confirmation email ONLY if explicitly requested
                    # COMMUNICATION PRIORITY: SMS (primary)  WhatsApp (future)  Email (backup)
                    # Email is OPTIONAL/BACKUP for order confirmations
                    send_email_confirmation = kwargs.get('send_email_confirmation', False)

                    if send_email_confirmation:
                        try:
                            # Get full order details with items and user
                            order_details_query = select(Order).options(
                                selectinload(Order.order_items).selectinload(OrderItem.menu_item),
                                selectinload(Order.user)
                            ).where(Order.id == kwargs['order_id'])
                            order_details_result = await session.execute(order_details_query)
                            order_with_details = order_details_result.scalar_one_or_none()

                            if order_with_details and order_with_details.user and order_with_details.user.email:
                                from app.services.email_manager_service import create_email_service
                                from app.services.email_template_service import get_email_template_service
                                from app.utils.timezone import format_datetime_for_display

                                template_service = get_email_template_service()
                                email_service = create_email_service(session)

                                # Prepare order items data for template
                                email_order_items = [
                                    {
                                        "quantity": item.quantity,
                                        "name": item.menu_item.name,
                                        "total_price": float(item.total_price),
                                        "special_instructions": item.special_instructions
                                    }
                                    for item in order_with_details.order_items
                                ]

                                # Render order confirmation template
                                html_content = template_service.render_order_confirmation(
                                    customer_name=order_with_details.user.full_name or "Valued Customer",
                                    order_number=order_with_details.order_number,
                                    order_type=order_with_details.order_type,
                                    order_time=format_datetime_for_display(order_with_details.created_at),
                                    order_items=email_order_items,
                                    subtotal=float(order_with_details.subtotal),
                                    tax_amount=float(order_with_details.tax_amount),
                                    discount_amount=float(order_with_details.discount_amount),
                                    total_amount=float(order_with_details.total_amount),
                                    estimated_ready_time=format_datetime_for_display(order_with_details.estimated_ready_time) if order_with_details.estimated_ready_time else None
                                )

                                # Send email (BACKUP channel - SMS is primary)
                                email_result = await email_service.send_email(
                                    to_email=order_with_details.user.email,
                                    subject=f"Order Confirmation - {order_with_details.order_number}",
                                    html_content=html_content,
                                    user_id=order_with_details.user_id
                                )

                                if email_result.get("success"):
                                    logger.info(
                                        "Order confirmation email sent (backup channel)",
                                        order_id=kwargs['order_id'],
                                        email=order_with_details.user.email,
                                        email_log_id=email_result.get("email_log_id")
                                    )
                                else:
                                    logger.warning(
                                        "Failed to send order confirmation email",
                                        order_id=kwargs['order_id'],
                                        error=email_result.get("error")
                                    )
                        except Exception as e:
                            logger.error(f"Email sending failed: {str(e)}")
                            # Don't fail the order confirmation if email fails - just log it

                # Schedule feedback request email for 2 DAYS after delivery
                # FEEDBACK STRATEGY: Email sent 2 days after order delivery (not immediate)
                # This gives customers time to experience the service before requesting feedback
                if new_status == 'delivered' and old_status != 'delivered':
                    # Mark the delivery time for scheduled feedback
                    # The actual email will be sent by a scheduled task (cron job)
                    # See: send_scheduled_feedback_emails.py
                    logger.info(
                        "Order delivered - feedback email will be sent in 2 days",
                        order_id=kwargs['order_id'],
                        order_number=order.order_number,
                        delivered_at=datetime.now().isoformat()
                    )
                # ========================================================================

                # Serialize order response using schema
                order_data = serialize_output_with_schema(
                    OrderResponse,
                    order,
                    self.name,
                    from_orm=True
                )

                # Add status transition metadata
                order_data['old_status'] = old_status
                order_data['new_status'] = new_status

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=order_data,
                    metadata={"operation": "update_status"}
                )

        except Exception as e:
            logger.error(f"Failed to update order status: {str(e)}")
            raise ToolError(f"Database error: {str(e)}", tool_name=self.name, retry_suggested=True)


@validate_schema(Order)
class ListOrdersTool(ToolBase):
    """
    List orders with filtering and pagination.

    Retrieves orders based on filters like user, status, date range, etc.
    """

    def __init__(self):
        super().__init__(
            name="list_orders",
            description="List orders with filtering and pagination",
            max_retries=2,
            timeout_seconds=15
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        """Validate listing parameters"""
        # Validate pagination
        if 'limit' in kwargs and kwargs['limit'] <= 0:
            raise ToolError("limit must be positive", tool_name=self.name)

        if 'offset' in kwargs and kwargs['offset'] < 0:
            raise ToolError("offset must be non-negative", tool_name=self.name)

        return kwargs

    async def _execute_impl(self, **kwargs) -> ToolResult:
        try:
            async with get_db_session() as session:
                # Build base query
                query = select(Order).options(selectinload(Order.user))

                # Apply filters
                conditions = []

                if kwargs.get('user_id'):
                    conditions.append(Order.user_id == kwargs['user_id'])

                if kwargs.get('device_id'):
                    conditions.append(Order.device_id == kwargs['device_id'])

                if kwargs.get('status'):
                    conditions.append(Order.status == kwargs['status'])

                if kwargs.get('order_type'):
                    conditions.append(Order.order_type == kwargs['order_type'])

                if kwargs.get('date_from'):
                    conditions.append(Order.created_at >= kwargs['date_from'])

                if kwargs.get('date_to'):
                    conditions.append(Order.created_at <= kwargs['date_to'])

                if conditions:
                    query = query.where(and_(*conditions))

                # Apply ordering
                order_by = kwargs.get('order_by', 'created_at')
                if order_by == 'created_at':
                    query = query.order_by(Order.created_at.desc())
                elif order_by == 'total_amount':
                    query = query.order_by(Order.total_amount.desc())
                elif order_by == 'status':
                    query = query.order_by(Order.status)

                # Apply pagination
                limit = kwargs.get('limit', 50)
                offset = kwargs.get('offset', 0)
                query = query.limit(limit).offset(offset)

                # Execute query
                result = await session.execute(query)
                orders = result.scalars().all()

                # Serialize orders using schema
                orders_data = []
                for order in orders:
                    order_summary = serialize_output_with_schema(
                        OrderSummaryResponse,
                        order,
                        self.name,
                        from_orm=True
                    )
                    # Add user name for convenience
                    order_summary['user_name'] = order.user.full_name if order.user else None
                    orders_data.append(order_summary)

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={
                        "orders": orders_data,
                        "count": len(orders_data),
                        "limit": limit,
                        "offset": offset,
                        "filters_applied": {k: v for k, v in kwargs.items()
                                          if k in ['user_id', 'device_id', 'status', 'order_type', 'date_from', 'date_to']}
                    },
                    metadata={"operation": "list_orders"}
                )

        except Exception as e:
            logger.error(f"Failed to list orders: {str(e)}")
            raise ToolError(f"Database error: {str(e)}", tool_name=self.name, retry_suggested=True)


@validate_schema(Order)
@require_tables("orders", "order_items", "menu_items")
class CheckoutCartTool(ToolBase):
    """
    Convert shopping cart to finalized order.

    This is the bridge between cart (Redis) and orders (Database).
    Takes all items from cart, creates order, adds order items, and clears cart.

    WORKFLOW:
    1. Get cart from Redis
    2. Create order in database
    3. Add all cart items as order_items
    4. Calculate totals
    5. Clear cart from Redis
    6. Return complete order
    """

    def __init__(self):
        super().__init__(
            name="checkout_cart",
            description="Convert cart to order and finalize checkout",
            max_retries=2,
            timeout_seconds=30
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        """Validate checkout parameters"""
        required_fields = ['session_id', 'order_type', 'contact_phone']
        missing_fields = []

        for field in required_fields:
            if not kwargs.get(field):
                missing_fields.append(field)

        # Normalize phone number to international format
        if kwargs.get('contact_phone'):
            try:
                kwargs['contact_phone'] = normalize_phone_number(kwargs['contact_phone'])
                logger.debug(f"Normalized phone number for checkout: {kwargs['contact_phone']}")
            except Exception as e:
                logger.warning(f"Failed to normalize phone number: {str(e)}")
                # Continue with original phone if normalization fails

        if missing_fields:
            raise ToolError(
                f"Missing required fields for checkout: {', '.join(missing_fields)}",
                tool_name=self.name
            )

        # Validate order_type
        valid_order_types = ['dine_in', 'takeout']
        if kwargs['order_type'] not in valid_order_types:
            raise ToolError(
                f"order_type must be one of: {valid_order_types}",
                tool_name=self.name
            )

        return kwargs

    async def _execute_impl(self, **kwargs) -> ToolResult:
        """Execute cart checkout"""
        from app.services.redis_service import RedisService

        session_id = kwargs['session_id']
        order_type = kwargs['order_type']
        contact_phone = kwargs['contact_phone']
        user_id = kwargs.get('user_id')
        device_id = kwargs.get('device_id')

        try:
            # Step 1: Get cart from Redis
            redis = RedisService()
            cart_key = f"cart:{session_id}"
            cart_data = await redis.get(cart_key)

            if not cart_data or not cart_data.get('items'):
                logger.warning(
                    "Checkout attempted with empty cart",
                    session_id=session_id,
                    cart_exists=bool(cart_data)
                )
                return ToolResult(
                    status=ToolStatus.FAILURE,
                    error="Cart is empty. Please add items before checkout."
                )

            cart_items = cart_data.get('items', [])

            logger.info(
                "Starting cart checkout",
                session_id=session_id,
                cart_item_count=len(cart_items),
                order_type=order_type,
                has_user_id=bool(user_id),
                has_device_id=bool(device_id)
            )

            # Step 2: Create order in database
            async with get_db_session() as session:
                # Generate unique order number
                order_number = self._generate_order_number()

                # Ensure uniqueness
                while True:
                    existing_query = select(Order).where(Order.order_number == order_number)
                    existing_result = await session.execute(existing_query)
                    if not existing_result.scalar_one_or_none():
                        break
                    order_number = self._generate_order_number()

                # CRITICAL: Ensure device exists in database before creating order
                # This prevents foreign key violations from race conditions
                if device_id:
                    from app.shared.models import UserDevice
                    device_query = select(UserDevice).where(UserDevice.device_id == device_id)
                    device_result = await session.execute(device_query)
                    device_record = device_result.scalar_one_or_none()

                    if not device_record:
                        # Device doesn't exist - create it now to prevent FK violation
                        from app.utils.id_generator import generate_id
                        from datetime import timezone

                        device_db_id = await generate_id(session, "user_devices")
                        new_device = UserDevice(
                            id=device_db_id,
                            device_id=device_id,
                            user_id=user_id,
                            first_seen_at=datetime.now(timezone.utc),
                            last_seen_at=datetime.now(timezone.utc),
                            is_active=True
                        )
                        session.add(new_device)
                        await session.flush()  # Ensure device is committed before order

                        logger.info(
                            "Device created during checkout",
                            device_id=device_id,
                            session_id=session_id
                        )

                # Create order
                new_order = Order(
                    user_id=user_id,
                    device_id=device_id,
                    order_number=order_number,
                    order_type=order_type,
                    status="pending",
                    subtotal=Decimal('0.00'),
                    tax_amount=Decimal('0.00'),
                    discount_amount=Decimal('0.00'),
                    total_amount=Decimal('0.00'),
                    contact_phone=contact_phone,
                    special_instructions=kwargs.get('special_instructions'),
                    booking_id=kwargs.get('booking_id')
                )

                # Set estimated ready time
                if order_type == 'dine_in':
                    base_time = 30
                else:  # takeout
                    base_time = 25
                new_order.estimated_ready_time = datetime.now() + timedelta(minutes=base_time)

                session.add(new_order)
                await session.flush()  # Get order ID

                logger.info(
                    "Order created from cart",
                    order_id=new_order.id,
                    order_number=new_order.order_number,
                    session_id=session_id
                )

                # Step 3: Add all cart items as order_items
                subtotal = Decimal('0.00')
                order_items_data = []

                for cart_item in cart_items:
                    # Get menu item details
                    menu_query = select(MenuItem).where(MenuItem.id == cart_item['item_id'])
                    menu_result = await session.execute(menu_query)
                    menu_item = menu_result.scalar_one_or_none()

                    if not menu_item:
                        logger.warning(
                            "Menu item not found during checkout",
                            item_id=cart_item['item_id'],
                            session_id=session_id
                        )
                        continue

                    if not menu_item.is_available:
                        logger.warning(
                            "Unavailable item in cart during checkout",
                            item_id=menu_item.id,
                            item_name=menu_item.name,
                            session_id=session_id
                        )
                        # Skip unavailable items
                        continue

                    # Create order item
                    quantity = cart_item['quantity']
                    unit_price = menu_item.price
                    total_price = unit_price * quantity

                    order_item = OrderItem(
                        order_id=new_order.id,
                        menu_item_id=menu_item.id,
                        quantity=quantity,
                        unit_price=unit_price,
                        total_price=total_price
                        # special_instructions is optional and not stored in cart
                    )

                    session.add(order_item)
                    subtotal += total_price

                    order_items_data.append({
                        "item_id": menu_item.id,
                        "item_name": menu_item.name,
                        "quantity": quantity,
                        "unit_price": float(unit_price),
                        "total_price": float(total_price)
                    })

                # Step 4: Calculate totals
                tax_rate = kwargs.get('tax_rate', 0.0)
                tax_amount = subtotal * Decimal(str(tax_rate))
                discount_amount = Decimal(str(kwargs.get('discount_amount', 0.0)))
                total_amount = subtotal + tax_amount - discount_amount

                # Update order totals
                new_order.subtotal = subtotal
                new_order.tax_amount = tax_amount
                new_order.discount_amount = discount_amount
                new_order.total_amount = total_amount

                await session.commit()
                await session.refresh(new_order)

                logger.info(
                    "Cart checkout completed successfully",
                    order_id=new_order.id,
                    order_number=new_order.order_number,
                    items_count=len(order_items_data),
                    subtotal=float(subtotal),
                    total=float(total_amount),
                    session_id=session_id
                )

                # Step 5: Clear cart from Redis
                redis.delete(cart_key)

                logger.info(
                    "Cart cleared after successful checkout",
                    session_id=session_id,
                    order_number=new_order.order_number
                )

                # Step 6: Return complete order details using schema
                order_data = serialize_output_with_schema(
                    OrderResponse,
                    new_order,
                    self.name,
                    from_orm=True
                )

                # Add items and checkout metadata
                order_data['items'] = order_items_data
                order_data['item_count'] = len(order_items_data)

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=order_data,
                    metadata={"operation": "checkout_cart", "session_id": session_id}
                )

        except Exception as e:
            logger.error(
                "Failed to checkout cart",
                error=str(e),
                session_id=session_id,
                order_type=order_type,
                exc_info=True
            )
            raise ToolError(
                f"Checkout failed: {str(e)}",
                tool_name=self.name,
                retry_suggested=True
            )

    def _generate_order_number(self) -> str:
        """Generate unique order number"""
        import uuid
        date_part = datetime.now().strftime("%Y%m%d")
        random_part = str(uuid.uuid4())[:4].upper()
        return f"ORD-{date_part}-{random_part}"


@validate_schema(Order)
@require_tables("orders", "order_items")
class CheckoutCartDraftTool(ToolBase):
    """
    Convert shopping cart to DRAFT order (hybrid flow).

    Creates order in 'draft' status before authentication/payment.
    Cart is NOT cleared - preserved for potential modifications.

    WORKFLOW (Hybrid Flow):
    1. Get cart from Redis
    2. Create DRAFT order in database
    3. Add all cart items as order_items
    4. Calculate totals
    5. Keep cart in Redis (for modifications)
    6. Return draft order for payment flow

    After payment success:
    - Webhook updates order status: draft  confirmed
    - Cart is cleared
    """

    def __init__(self):
        super().__init__(
            name="checkout_cart_draft",
            description="Create draft order from cart before payment",
            max_retries=2,
            timeout_seconds=30
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        """Validate draft checkout parameters"""
        required_fields = ['session_id', 'order_type']
        missing_fields = []

        for field in required_fields:
            if not kwargs.get(field):
                missing_fields.append(field)

        if missing_fields:
            raise ToolError(
                f"Missing required fields for draft checkout: {', '.join(missing_fields)}",
                tool_name=self.name
            )

        # Validate order_type
        valid_order_types = ['dine_in', 'takeout']
        if kwargs['order_type'] not in valid_order_types:
            raise ToolError(
                f"order_type must be one of: {valid_order_types}",
                tool_name=self.name
            )

        return kwargs

    async def _execute_impl(self, **kwargs) -> ToolResult:
        """Execute draft cart checkout"""
        from app.services.redis_service import RedisService

        session_id = kwargs['session_id']
        order_type = kwargs['order_type']
        contact_phone = kwargs.get('contact_phone', '')  # Optional for draft
        user_id = kwargs.get('user_id')
        device_id = kwargs.get('device_id')

        try:
            # Step 1: Get cart from Redis
            redis = RedisService()
            cart_key = f"cart:{session_id}"
            cart_data = await redis.get(cart_key)

            if not cart_data or not cart_data.get('items'):
                logger.warning(
                    "Draft checkout attempted with empty cart",
                    session_id=session_id,
                    cart_exists=bool(cart_data)
                )
                return ToolResult(
                    status=ToolStatus.FAILURE,
                    error="Cart is empty. Please add items before checkout."
                )

            cart_items = cart_data.get('items', [])

            logger.info(
                "Starting draft cart checkout",
                session_id=session_id,
                cart_item_count=len(cart_items),
                order_type=order_type,
                has_user_id=bool(user_id),
                has_device_id=bool(device_id)
            )

            # Step 2: Create DRAFT order in database
            async with get_db_session() as session:
                # Generate unique order number
                order_number = self._generate_order_number()

                # Ensure uniqueness
                while True:
                    existing_query = select(Order).where(Order.order_number == order_number)
                    existing_result = await session.execute(existing_query)
                    if not existing_result.scalar_one_or_none():
                        break
                    order_number = self._generate_order_number()

                # Handle device if provided
                if device_id:
                    from app.shared.models import UserDevice
                    device_query = select(UserDevice).where(UserDevice.device_id == device_id)
                    device_result = await session.execute(device_query)
                    device_record = device_result.scalar_one_or_none()

                    if not device_record:
                        from app.utils.id_generator import generate_id
                        from datetime import timezone

                        device_db_id = await generate_id(session, "user_devices")
                        new_device = UserDevice(
                            id=device_db_id,
                            device_id=device_id,
                            user_id=user_id,
                            first_seen_at=datetime.now(timezone.utc),
                            last_seen_at=datetime.now(timezone.utc),
                            is_active=True
                        )
                        session.add(new_device)
                        await session.flush()

                        logger.info(
                            "Device created during draft checkout",
                            device_id=device_id,
                            session_id=session_id
                        )

                # Create DRAFT order
                new_order = Order(
                    user_id=user_id,
                    device_id=device_id,
                    order_number=order_number,
                    order_type=order_type,
                    status="draft",  # DRAFT status - key difference
                    subtotal=Decimal('0.00'),
                    tax_amount=Decimal('0.00'),
                    discount_amount=Decimal('0.00'),
                    total_amount=Decimal('0.00'),
                    contact_phone=contact_phone,
                    special_instructions=kwargs.get('special_instructions'),
                    booking_id=kwargs.get('booking_id')
                )

                # Set estimated ready time
                if order_type == 'dine_in':
                    base_time = 30
                else:  # takeout
                    base_time = 25
                new_order.estimated_ready_time = datetime.now() + timedelta(minutes=base_time)

                session.add(new_order)
                await session.flush()  # Get order ID

                logger.info(
                    "DRAFT order created from cart",
                    order_id=new_order.id,
                    order_number=new_order.order_number,
                    status=new_order.status,
                    session_id=session_id
                )

                # Step 3: Add all cart items as order_items
                subtotal = Decimal('0.00')
                order_items_data = []

                for cart_item in cart_items:
                    # Get menu item details
                    menu_query = select(MenuItem).where(MenuItem.id == cart_item['item_id'])
                    menu_result = await session.execute(menu_query)
                    menu_item = menu_result.scalar_one_or_none()

                    if not menu_item:
                        logger.warning(
                            "Menu item not found during draft checkout",
                            item_id=cart_item['item_id'],
                            session_id=session_id
                        )
                        continue

                    if not menu_item.is_available:
                        logger.warning(
                            "Unavailable item in cart during draft checkout",
                            item_id=menu_item.id,
                            item_name=menu_item.name,
                            session_id=session_id
                        )
                        continue

                    # Create order item
                    quantity = cart_item['quantity']
                    unit_price = menu_item.price
                    total_price = unit_price * quantity

                    order_item = OrderItem(
                        order_id=new_order.id,
                        menu_item_id=menu_item.id,
                        quantity=quantity,
                        unit_price=unit_price,
                        total_price=total_price
                    )

                    session.add(order_item)
                    subtotal += total_price

                    order_items_data.append({
                        "item_id": menu_item.id,
                        "item_name": menu_item.name,
                        "quantity": quantity,
                        "unit_price": float(unit_price),
                        "total_price": float(total_price)
                    })

                # Step 4: Calculate totals
                tax_rate = kwargs.get('tax_rate', 0.0)
                tax_amount = subtotal * Decimal(str(tax_rate))
                discount_amount = Decimal(str(kwargs.get('discount_amount', 0.0)))
                total_amount = subtotal + tax_amount - discount_amount

                # Update order totals
                new_order.subtotal = subtotal
                new_order.tax_amount = tax_amount
                new_order.discount_amount = discount_amount
                new_order.total_amount = total_amount

                await session.commit()
                await session.refresh(new_order)

                logger.info(
                    "Draft checkout completed - cart preserved",
                    order_id=new_order.id,
                    order_number=new_order.order_number,
                    status="draft",
                    items_count=len(order_items_data),
                    subtotal=float(subtotal),
                    total=float(total_amount),
                    session_id=session_id
                )

                # Step 5: KEEP cart in Redis (NOT cleared - for modifications)
                logger.info(
                    "Cart preserved for draft order",
                    session_id=session_id,
                    order_number=new_order.order_number,
                    cart_key=cart_key
                )

                # Step 6: Return draft order details
                order_data = serialize_output_with_schema(
                    OrderResponse,
                    new_order,
                    self.name,
                    from_orm=True
                )

                # Add items and draft metadata
                order_data['items'] = order_items_data
                order_data['item_count'] = len(order_items_data)
                order_data['is_draft'] = True
                order_data['cart_preserved'] = True

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=order_data,
                    metadata={
                        "operation": "checkout_cart_draft",
                        "session_id": session_id,
                        "status": "draft"
                    }
                )

        except Exception as e:
            logger.error(
                "Failed to create draft order",
                error=str(e),
                session_id=session_id,
                order_type=order_type,
                exc_info=True
            )
            raise ToolError(
                f"Draft checkout failed: {str(e)}",
                tool_name=self.name,
                retry_suggested=True
            )

    def _generate_order_number(self) -> str:
        """Generate unique order number"""
        import uuid
        date_part = datetime.now().strftime("%Y%m%d")
        random_part = str(uuid.uuid4())[:4].upper()
        return f"ORD-{date_part}-{random_part}"


# Testing function
if __name__ == "__main__":
    import asyncio

    async def test_order_tools():
        """Test order management tools"""
        print("Testing Order Management Tools...")

        from app.database.connection import init_database
        await init_database(create_tables=False)

        try:
            # Test 1: Create Order
            print("\n1. Testing CreateOrderTool...")
            create_tool = CreateOrderTool()
            result = await create_tool.execute(
                user_id="11111111-1111-1111-1111-111111111111",  # Rajesh Kumar
                order_type="takeout",
                contact_phone="+1234567890"
            )

            if result.status == ToolStatus.SUCCESS:
                print(f"SUCCESS: Order created: {result.data['order_number']}")
                order_id = result.data['id']

                # Test 2: Add Order Item
                print("\n2. Testing AddOrderItemTool...")
                add_item_tool = AddOrderItemTool()
                item_result = await add_item_tool.execute(
                    order_id=order_id,
                    menu_item_id="e9961954-ecad-48cf-b003-3309fcc4345b",  # Butter Chicken
                    quantity=2,
                    customizations={"spice_level": "medium"}
                )

                if item_result.status == ToolStatus.SUCCESS:
                    print(f"SUCCESS: Item added: {item_result.data['menu_item_name']}")
                    order_item_id = item_result.data['id']

                    # Test 3: Update Order Item
                    print("\n3. Testing UpdateOrderItemTool...")
                    update_tool = UpdateOrderItemTool()
                    update_result = await update_tool.execute(
                        order_item_id=order_item_id,
                        quantity=3
                    )

                    if update_result.status == ToolStatus.SUCCESS:
                        print(f"SUCCESS: Item updated: quantity = {update_result.data['quantity']}")

                        # Test 4: Calculate Total
                        print("\n4. Testing CalculateOrderTotalTool...")
                        calc_tool = CalculateOrderTotalTool()
                        calc_result = await calc_tool.execute(
                            order_id=order_id,
                            tax_rate=0.08,
                            discount_amount=5.00
                        )

                        if calc_result.status == ToolStatus.SUCCESS:
                            print(f"SUCCESS: Total calculated: ₹{calc_result.data['total_amount']}")

                            # Test 5: Get Order
                            print("\n5. Testing GetOrderTool...")
                            get_tool = GetOrderTool()
                            get_result = await get_tool.execute(order_id=order_id)

                            if get_result.status == ToolStatus.SUCCESS:
                                print(f"SUCCESS: Order retrieved: {len(get_result.data['items'])} items")

                                # Test 6: Update Status
                                print("\n6. Testing UpdateOrderStatusTool...")
                                status_tool = UpdateOrderStatusTool()
                                status_result = await status_tool.execute(
                                    order_id=order_id,
                                    status="confirmed"
                                )

                                if status_result.status == ToolStatus.SUCCESS:
                                    print(f"SUCCESS: Status updated: {status_result.data['new_status']}")

                                    # Test 7: List Orders
                                    print("\n7. Testing ListOrdersTool...")
                                    list_tool = ListOrdersTool()
                                    list_result = await list_tool.execute(
                                        limit=10,
                                        order_by="created_at"
                                    )

                                    if list_result.status == ToolStatus.SUCCESS:
                                        print(f"SUCCESS: Orders listed: {list_result.data['count']} orders")
                                        print("SUCCESS: All order tools working!")
                                    else:
                                        print(f"ERROR: List failed: {list_result.error}")
                                else:
                                    print(f"ERROR: Status update failed: {status_result.error}")
                            else:
                                print(f"ERROR: Get failed: {get_result.error}")
                        else:
                            print(f"ERROR: Calculate failed: {calc_result.error}")
                    else:
                        print(f"ERROR: Update failed: {update_result.error}")
                else:
                    print(f"ERROR: Add item failed: {item_result.error}")
            else:
                print(f"ERROR: Create failed: {result.error}")

        except Exception as e:
            print(f"ERROR: Test failed: {str(e)}")

    asyncio.run(test_order_tools())

"""
Enhanced AI-Powered Order Tools for OrderAgent
=============================================

These tools provide intelligent order operations including smart cart management,
intelligent upselling, order validation, and modification handling. Built specifically
for the OrderAgent to deliver a conversational ordering experience.

AI-Enhanced Tools:
- SmartCartManagementTool: Natural language cart operations with intelligent parsing
- IntelligentUpsellingTool: Revenue optimization through strategic recommendations
- OrderValidationTool: Comprehensive order verification before confirmation
- OrderModificationTool: Handle post-confirmation changes with business rules
- SmartOrderTrackingTool: Proactive status communication and updates
- OrderPersonalizationTool: User history-based suggestions and quick reorders
- OrderAnalyticsTool: Business intelligence for order optimization
"""

import re
from decimal import Decimal
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass

from app.tools.base.tool_base import ToolBase, ToolResult, ToolStatus
from app.core.database import get_db_session
from app.features.food_ordering.models import Order, OrderItem, MenuItem, MenuCategory
from app.shared.models import User, OrderStatus
from sqlalchemy import select, and_, or_, func, desc, update
from app.core.logging_config import get_logger
from app.utils.validation_decorators import validate_schema, require_tables
from app.utils.schema_tool_integration import serialize_output_with_schema, safe_isoformat
from app.features.food_ordering.schemas.order import OrderResponse, OrderItemResponse, OrderSummaryResponse
from app.features.food_ordering.schemas.menu import MenuItemResponse, MenuItemSummaryResponse

logger = get_logger(__name__)

@dataclass
class CartItem:
    """Structured cart item for intelligent operations"""
    item_id: str
    name: str
    quantity: int
    unit_price: Decimal
    total_price: Decimal
    customizations: Dict[str, Any]
    special_instructions: Optional[str] = None
    dietary_info: Optional[List[str]] = None
    allergens: Optional[List[str]] = None

@dataclass
class OrderSuggestion:
    """Structured order suggestion for upselling"""
    item_id: str
    name: str
    description: str
    price: Decimal
    suggestion_reason: str
    confidence_score: float
    category_name: str
    estimated_revenue_increase: Decimal

@dataclass
class OrderValidationResult:
    """Comprehensive order validation result"""
    is_valid: bool
    issues: List[str]
    warnings: List[str]
    estimated_ready_time: Optional[datetime]
    total_amount: Decimal
    availability_status: Dict[str, bool]
    dietary_conflicts: List[str]

@validate_schema(Order)
@require_tables("orders", "order_items", "menu_items")
class SmartCartManagementTool(ToolBase):
    """
    Intelligent cart operations with natural language understanding.

    Handles complex cart operations like:
    - "Add 2 medium pizzas, one with extra cheese"
    - "Remove the spicy items from my cart"
    - "Change the large pizza to medium"
    - "Make everything mild spice level"
    """

    def __init__(self):
        super().__init__(
            name="smart_cart_management",
            description="Intelligent cart operations with natural language processing"
        )

    async def _execute_impl(self, **kwargs) -> ToolResult:
        """Execute smart cart management operations"""
        try:
            # Extract parameters
            operation = kwargs.get('operation', 'add')  # add, remove, modify, clear, list
            user_id = kwargs.get('user_id')
            order_id = kwargs.get('order_id')
            natural_query = kwargs.get('query', '')
            item_details = kwargs.get('item_details', {})

            if not user_id:
                return ToolResult(
                    status=ToolStatus.FAILURE,
                    data={"error": "User ID is required for cart operations"}
                )

            async with get_db_session() as session:
                # Get or create active order (cart)
                order = await self._get_or_create_cart(session, user_id, order_id)

                if operation == 'add':
                    result = await self._handle_add_items(session, order, natural_query, item_details)
                elif operation == 'remove':
                    result = await self._handle_remove_items(session, order, natural_query, item_details)
                elif operation == 'modify':
                    result = await self._handle_modify_items(session, order, natural_query, item_details)
                elif operation == 'clear':
                    result = await self._handle_clear_cart(session, order)
                elif operation == 'list':
                    result = await self._handle_list_cart(session, order)
                else:
                    return ToolResult(
                        status=ToolStatus.FAILURE,
                        data={"error": f"Unknown operation: {operation}"}
                    )

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=result
                )

        except Exception as e:
            logger.error(f"SmartCartManagementTool error: {str(e)}")
            return ToolResult(
                status=ToolStatus.FAILURE,
                data={"error": f"Cart operation failed: {str(e)}"}
            )

    async def _get_or_create_cart(self, session, user_id: str, order_id: Optional[str] = None):
        """Get existing cart or create new one"""
        if order_id:
            # Get specific order
            result = await session.execute(
                select(Order).where(
                    and_(Order.id == order_id, Order.user_id == user_id)
                )
            )
            order = result.scalar_one_or_none()
            if not order:
                raise ValueError(f"Order {order_id} not found for user")
        else:
            # Get or create active cart (pending order)
            result = await session.execute(
                select(Order).where(
                    and_(
                        Order.user_id == user_id,
                        Order.status == OrderStatus.PENDING.value
                    )
                ).order_by(desc(Order.created_at))
            )
            order = result.scalar_one_or_none()

            if not order:
                # Create new cart
                from app.features.food_ordering.tools.order_tools import CreateOrderTool
                create_tool = CreateOrderTool()
                create_result = await create_tool.execute(
                    user_id=user_id,
                    order_type="dine_in",
                    contact_phone="",  # Will be updated when order is placed
                    special_instructions=""
                )

                if create_result.status != ToolStatus.SUCCESS:
                    raise ValueError("Failed to create new cart")

                order_id = create_result.data['order_id']
                result = await session.execute(
                    select(Order).where(Order.id == order_id)
                )
                order = result.scalar_one()

        return order

    async def _handle_add_items(self, session, order: Order, natural_query: str, item_details: Dict):
        """Handle adding items to cart with natural language parsing"""
        try:
            # Parse natural language query for items and quantities
            parsed_items = await self._parse_add_query(session, natural_query, item_details)

            added_items = []
            for item_info in parsed_items:
                # Add item using existing tool
                from app.features.food_ordering.tools.order_tools import AddOrderItemTool
                add_tool = AddOrderItemTool()

                result = await add_tool.execute(
                    order_id=order.id,
                    menu_item_id=item_info['item_id'],
                    quantity=item_info['quantity'],
                    customizations=item_info.get('customizations', {}),
                    special_instructions=item_info.get('special_instructions')
                )

                if result.status == ToolStatus.SUCCESS:
                    added_items.append({
                        'name': item_info['name'],
                        'quantity': item_info['quantity'],
                        'price': item_info['price']
                    })

            # Recalculate order total
            await self._recalculate_order_total(session, order.id)

            return {
                'operation': 'add',
                'order_id': order.id,
                'added_items': added_items,
                'message': f"Added {len(added_items)} item(s) to your cart"
            }

        except Exception as e:
            logger.error(f"Error adding items: {str(e)}")
            return {'error': f"Failed to add items: {str(e)}"}

    async def _parse_add_query(self, session, natural_query: str, item_details: Dict):
        """Parse natural language query to extract items and quantities"""
        parsed_items = []

        # If item_details provided directly, use that
        if item_details and 'item_id' in item_details:
            menu_item = await self._get_menu_item(session, item_details['item_id'])
            if menu_item:
                parsed_items.append({
                    'item_id': menu_item.id,
                    'name': menu_item.name,
                    'quantity': item_details.get('quantity', 1),
                    'price': menu_item.price,
                    'customizations': item_details.get('customizations', {}),
                    'special_instructions': item_details.get('special_instructions')
                })

        # Parse natural language query
        elif natural_query:
            # Extract quantity patterns like "2 pizzas", "three burgers"
            quantity_patterns = [
                r'(\d+)\s+([a-zA-Z\s]+)',
                r'(one|two|three|four|five|six|seven|eight|nine|ten)\s+([a-zA-Z\s]+)',
                r'add\s+(\d+)\s+([a-zA-Z\s]+)',
                r'get\s+(\d+)\s+([a-zA-Z\s]+)'
            ]

            # Search for menu items mentioned in the query
            menu_items = await self._search_menu_items_in_query(session, natural_query)

            for item in menu_items:
                # Default to quantity 1
                quantity = 1

                # Try to extract quantity from query
                for pattern in quantity_patterns:
                    match = re.search(pattern, natural_query.lower())
                    if match and item.name.lower() in natural_query.lower():
                        qty_str = match.group(1)
                        if qty_str.isdigit():
                            quantity = int(qty_str)
                        else:
                            # Convert word numbers to digits
                            word_to_num = {
                                'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
                                'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
                            }
                            quantity = word_to_num.get(qty_str.lower(), 1)

                # Extract customizations from query
                customizations = self._extract_customizations(natural_query, item.name)

                parsed_items.append({
                    'item_id': item.id,
                    'name': item.name,
                    'quantity': quantity,
                    'price': item.price,
                    'customizations': customizations,
                    'special_instructions': self._extract_special_instructions(natural_query)
                })

        return parsed_items

    async def _search_menu_items_in_query(self, session, query: str):
        """Search for menu items mentioned in natural language query"""
        # Get all menu items for fuzzy matching
        result = await session.execute(
            select(MenuItem).where(MenuItem.is_available == True)
        )
        all_items = result.scalars().all()

        mentioned_items = []
        query_lower = query.lower()

        for item in all_items:
            # Check if item name is mentioned in query
            item_name_lower = item.name.lower()
            if item_name_lower in query_lower:
                mentioned_items.append(item)
            # Check for partial matches
            elif any(word in query_lower for word in item_name_lower.split() if len(word) > 3):
                mentioned_items.append(item)

        return mentioned_items

    def _extract_customizations(self, query: str, item_name: str) -> Dict[str, Any]:
        """Extract customizations from natural language"""
        customizations = {}
        query_lower = query.lower()

        # Common customization patterns
        if 'extra cheese' in query_lower or 'more cheese' in query_lower:
            customizations['cheese'] = 'extra'

        if 'no cheese' in query_lower or 'without cheese' in query_lower:
            customizations['cheese'] = 'none'

        if 'spicy' in query_lower or 'hot' in query_lower:
            customizations['spice_level'] = 'hot'

        if 'mild' in query_lower or 'not spicy' in query_lower:
            customizations['spice_level'] = 'mild'

        if 'large' in query_lower:
            customizations['size'] = 'large'
        elif 'medium' in query_lower:
            customizations['size'] = 'medium'
        elif 'small' in query_lower:
            customizations['size'] = 'small'

        return customizations

    def _extract_special_instructions(self, query: str) -> Optional[str]:
        """Extract special instructions from query"""
        instruction_patterns = [
            r'make it (.+?)(?:\sand\s|\.|$)',
            r'with (.+?)(?:\sand\s|\.|$)',
            r'please (.+?)(?:\sand\s|\.|$)'
        ]

        for pattern in instruction_patterns:
            match = re.search(pattern, query.lower())
            if match:
                instruction = match.group(1).strip()
                if len(instruction) > 3:  # Avoid short meaningless extractions
                    return instruction

        return None

    async def _handle_remove_items(self, session, order: Order, natural_query: str, item_details: Dict):
        """Handle removing items from cart"""
        try:
            # Get current cart items
            result = await session.execute(
                select(OrderItem, MenuItem).join(MenuItem).where(
                    OrderItem.order_id == order.id
                )
            )
            cart_items = result.all()

            removed_items = []

            if item_details and 'item_id' in item_details:
                # Remove specific item by ID
                for order_item, menu_item in cart_items:
                    if order_item.menu_item_id == item_details['item_id']:
                        from app.features.food_ordering.tools.order_tools import RemoveOrderItemTool
                        remove_tool = RemoveOrderItemTool()
                        await remove_tool.execute(order_item_id=order_item.id)
                        removed_items.append({'name': menu_item.name, 'quantity': order_item.quantity})

            elif natural_query:
                # Parse natural language to identify items to remove
                items_to_remove = await self._parse_remove_query(natural_query, cart_items)

                for order_item in items_to_remove:
                    from app.features.food_ordering.tools.order_tools import RemoveOrderItemTool
                    remove_tool = RemoveOrderItemTool()
                    await remove_tool.execute(order_item_id=order_item.id)
                    removed_items.append({'name': order_item.name, 'quantity': order_item.quantity})

            # Recalculate order total
            await self._recalculate_order_total(session, order.id)

            return {
                'operation': 'remove',
                'order_id': order.id,
                'removed_items': removed_items,
                'message': f"Removed {len(removed_items)} item(s) from your cart"
            }

        except Exception as e:
            logger.error(f"Error removing items: {str(e)}")
            return {'error': f"Failed to remove items: {str(e)}"}

    async def _parse_remove_query(self, query: str, cart_items):
        """Parse natural language query to identify items to remove"""
        items_to_remove = []
        query_lower = query.lower()

        for order_item, menu_item in cart_items:
            # Check if item is mentioned for removal
            if menu_item.name.lower() in query_lower:
                items_to_remove.append(order_item)

            # Check for pattern matching (e.g., "spicy items")
            if 'spicy' in query_lower and menu_item.spice_level and menu_item.spice_level != 'mild':
                items_to_remove.append(order_item)

        return items_to_remove

    async def _handle_modify_items(self, session, order: Order, natural_query: str, item_details: Dict):
        """Handle modifying items in cart"""
        try:
            modifications = []

            if item_details:
                # Direct modification
                from app.features.food_ordering.tools.order_tools import UpdateOrderItemTool
                update_tool = UpdateOrderItemTool()

                result = await update_tool.execute(
                    order_item_id=item_details['order_item_id'],
                    quantity=item_details.get('quantity'),
                    customizations=item_details.get('customizations'),
                    special_instructions=item_details.get('special_instructions')
                )

                if result.status == ToolStatus.SUCCESS:
                    modifications.append(result.data)

            # Recalculate order total
            await self._recalculate_order_total(session, order.id)

            return {
                'operation': 'modify',
                'order_id': order.id,
                'modifications': modifications,
                'message': f"Modified {len(modifications)} item(s) in your cart"
            }

        except Exception as e:
            logger.error(f"Error modifying items: {str(e)}")
            return {'error': f"Failed to modify items: {str(e)}"}

    async def _handle_clear_cart(self, session, order: Order):
        """Handle clearing entire cart"""
        try:
            # Get all order items
            result = await session.execute(
                select(OrderItem).where(OrderItem.order_id == order.id)
            )
            order_items = result.scalars().all()

            cleared_count = len(order_items)

            # Remove all items
            for order_item in order_items:
                from app.features.food_ordering.tools.order_tools import RemoveOrderItemTool
                remove_tool = RemoveOrderItemTool()
                await remove_tool.execute(order_item_id=order_item.id)

            return {
                'operation': 'clear',
                'order_id': order.id,
                'cleared_items': cleared_count,
                'message': f"Cleared {cleared_count} item(s) from your cart"
            }

        except Exception as e:
            logger.error(f"Error clearing cart: {str(e)}")
            return {'error': f"Failed to clear cart: {str(e)}"}

    async def _handle_list_cart(self, session, order: Order):
        """Handle listing cart contents"""
        try:
            # Get all order items with menu item details
            result = await session.execute(
                select(OrderItem, MenuItem, MenuCategory.menu_category_name.label('category_name')).
                join(MenuItem, OrderItem.menu_item_id == MenuItem.id).
                join(MenuCategory, MenuItem.category_id == MenuCategory.menu_category_id).
                where(OrderItem.order_id == order.id)
            )
            cart_items = result.all()

            items = []
            total_amount = Decimal('0')

            for order_item, menu_item, category_name in cart_items:
                # Serialize order item
                order_item_data = serialize_output_with_schema(
                    OrderItemResponse,
                    order_item,
                    "smart_cart_management",
                    from_orm=True
                )
                # Serialize menu item info
                menu_item_data = serialize_output_with_schema(
                    MenuItemSummaryResponse,
                    menu_item,
                    "smart_cart_management",
                    from_orm=True
                )
                # Combine data
                item_data = {**order_item_data, 'menu_item': menu_item_data, 'category': category_name}
                items.append(item_data)
                total_amount += order_item.total_price

            return {
                'operation': 'list',
                'order_id': order.id,
                'items': items,
                'item_count': len(items),
                'total_amount': float(total_amount),
                'order_status': order.status
            }

        except Exception as e:
            logger.error(f"Error listing cart: {str(e)}")
            return {'error': f"Failed to list cart: {str(e)}"}

    async def _get_menu_item(self, session, item_id: str):
        """Get menu item by ID"""
        result = await session.execute(
            select(MenuItem).where(MenuItem.id == item_id)
        )
        return result.scalar_one_or_none()

    async def _recalculate_order_total(self, session, order_id: str):
        """Recalculate order total after changes"""
        from app.features.food_ordering.tools.order_tools import CalculateOrderTotalTool
        calc_tool = CalculateOrderTotalTool()
        await calc_tool.execute(order_id=order_id)


@validate_schema(MenuItem)
@require_tables("menu_items", "order_items", "orders")
class IntelligentUpsellingTool(ToolBase):
    """
    Revenue optimization through strategic recommendations.

    Provides context-aware upselling suggestions based on:
    - Current cart contents
    - User preferences and history
    - Menu item relationships
    - Revenue optimization opportunities
    """

    def __init__(self):
        super().__init__(
            name="intelligent_upselling",
            description="Strategic upselling recommendations for revenue optimization"
        )

    async def _execute_impl(self, **kwargs) -> ToolResult:
        """Execute intelligent upselling analysis"""
        try:
            order_id = kwargs.get('order_id')
            user_id = kwargs.get('user_id')
            strategy = kwargs.get('strategy', 'balanced')  # aggressive, balanced, subtle
            limit = kwargs.get('limit', 5)

            if not order_id:
                return ToolResult(
                    status=ToolStatus.FAILURE,
                    data={"error": "Order ID is required for upselling"}
                )

            async with get_db_session() as session:
                # Get current cart contents
                cart_items = await self._get_cart_items(session, order_id)

                # Generate upselling suggestions
                suggestions = await self._generate_upselling_suggestions(
                    session, cart_items, user_id, strategy, limit
                )

                # Convert suggestions dataclass to dict
                suggestions_data = [
                    {
                        'item_id': s.item_id,
                        'name': s.name,
                        'description': s.description,
                        'price': float(s.price),
                        'suggestion_reason': s.suggestion_reason,
                        'confidence_score': s.confidence_score,
                        'category_name': s.category_name,
                        'estimated_revenue_increase': float(s.estimated_revenue_increase)
                    }
                    for s in suggestions
                ]

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={
                        'order_id': order_id,
                        'suggestions': suggestions_data,
                        'strategy': strategy,
                        'total_suggestions': len(suggestions_data)
                    }
                )

        except Exception as e:
            logger.error(f"IntelligentUpsellingTool error: {str(e)}")
            return ToolResult(
                status=ToolStatus.FAILURE,
                data={"error": f"Upselling analysis failed: {str(e)}"}
            )

    async def _get_cart_items(self, session, order_id: str):
        """Get current cart items with menu details"""
        result = await session.execute(
            select(OrderItem, MenuItem, MenuCategory.menu_category_name.label('category_name')).
            join(MenuItem, OrderItem.menu_item_id == MenuItem.id).
            join(MenuCategory, MenuItem.category_id == MenuCategory.menu_category_id).
            where(OrderItem.order_id == order_id)
        )
        return result.all()

    async def _generate_upselling_suggestions(self, session, cart_items, user_id, strategy, limit):
        """Generate intelligent upselling suggestions"""
        suggestions = []

        # Analyze current cart
        cart_analysis = self._analyze_cart_composition(cart_items)

        # Different upselling strategies
        if strategy == 'aggressive':
            # Focus on higher-value items and premium options
            suggestions.extend(await self._suggest_premium_upgrades(session, cart_items))
            suggestions.extend(await self._suggest_high_value_additions(session, cart_analysis))

        elif strategy == 'balanced':
            # Mix of complementary items and moderate upgrades
            suggestions.extend(await self._suggest_complementary_items(session, cart_items))
            suggestions.extend(await self._suggest_meal_completion(session, cart_analysis))

        elif strategy == 'subtle':
            # Focus on natural pairings and small additions
            suggestions.extend(await self._suggest_natural_pairings(session, cart_items))
            suggestions.extend(await self._suggest_small_additions(session, cart_analysis))

        # Add personalized suggestions if user available
        if user_id:
            suggestions.extend(await self._suggest_based_on_history(session, user_id, cart_analysis))

        # Score and rank suggestions
        ranked_suggestions = self._rank_suggestions(suggestions, cart_analysis, strategy)

        return ranked_suggestions[:limit]

    def _analyze_cart_composition(self, cart_items):
        """Analyze current cart composition for strategic upselling"""
        analysis = {
            'categories': set(),
            'total_value': Decimal('0'),
            'item_count': len(cart_items),
            'has_main_dish': False,
            'has_beverage': False,
            'has_dessert': False,
            'has_appetizer': False,
            'spice_levels': set(),
            'dietary_preferences': set()
        }

        for order_item, menu_item, category_name in cart_items:
            analysis['categories'].add(category_name.lower())
            analysis['total_value'] += order_item.total_price

            # Categorize items
            if category_name.lower() in ['main', 'entree', 'pizza', 'burger']:
                analysis['has_main_dish'] = True
            elif category_name.lower() in ['beverage', 'drink']:
                analysis['has_beverage'] = True
            elif category_name.lower() in ['dessert', 'sweet']:
                analysis['has_dessert'] = True
            elif category_name.lower() in ['appetizer', 'starter']:
                analysis['has_appetizer'] = True

            if menu_item.spice_level:
                analysis['spice_levels'].add(menu_item.spice_level)

            if menu_item.dietary_info:
                analysis['dietary_preferences'].update(menu_item.dietary_info)

        return analysis

    async def _suggest_complementary_items(self, session, cart_items):
        """Suggest items that complement current cart contents"""
        suggestions = []

        # Get complementary items based on current cart
        for order_item, menu_item, category_name in cart_items:
            # Find items that pair well with current items
            complementary_query = select(MenuItem, MenuCategory.menu_category_name.label('cat_name')).join(
                MenuCategory, MenuItem.category_id == MenuCategory.menu_category_id
            ).where(
                and_(
                    MenuItem.is_available == True,
                    MenuItem.id != menu_item.id,
                    # Look for different categories that complement
                    or_(
                        MenuCategory.menu_category_name.ilike('%side%'),
                        MenuCategory.menu_category_name.ilike('%beverage%'),
                        MenuCategory.menu_category_name.ilike('%sauce%')
                    )
                )
            ).limit(3)

            result = await session.execute(complementary_query)
            complementary_items = result.all()

            for comp_item, comp_category in complementary_items:
                suggestions.append(OrderSuggestion(
                    item_id=comp_item.id,
                    name=comp_item.name,
                    description=comp_item.description or "",
                    price=comp_item.price,
                    suggestion_reason=f"Perfect pairing with {menu_item.name}",
                    confidence_score=0.7,
                    category_name=comp_category,
                    estimated_revenue_increase=comp_item.price
                ))

        return suggestions

    async def _suggest_meal_completion(self, session, cart_analysis):
        """Suggest items to complete the meal"""
        suggestions = []

        # Suggest beverage if none
        if not cart_analysis['has_beverage']:
            beverage_query = select(MenuItem, MenuCategory.menu_category_name.label('cat_name')).join(
                MenuCategory, MenuItem.category_id == MenuCategory.menu_category_id
            ).where(
                and_(
                    MenuItem.is_available == True,
                    MenuCategory.menu_category_name.ilike('%beverage%')
                )
            ).order_by(MenuItem.is_popular.desc()).limit(2)

            result = await session.execute(beverage_query)
            beverages = result.all()

            for beverage, cat_name in beverages:
                suggestions.append(OrderSuggestion(
                    item_id=beverage.id,
                    name=beverage.name,
                    description=beverage.description or "",
                    price=beverage.price,
                    suggestion_reason="Complete your meal with a refreshing drink",
                    confidence_score=0.8,
                    category_name=cat_name,
                    estimated_revenue_increase=beverage.price
                ))

        # Suggest dessert if none and order value is high enough
        if not cart_analysis['has_dessert'] and cart_analysis['total_value'] > Decimal('25'):
            dessert_query = select(MenuItem, MenuCategory.menu_category_name.label('cat_name')).join(
                MenuCategory, MenuItem.category_id == MenuCategory.menu_category_id
            ).where(
                and_(
                    MenuItem.is_available == True,
                    MenuCategory.menu_category_name.ilike('%dessert%')
                )
            ).order_by(MenuItem.is_popular.desc()).limit(2)

            result = await session.execute(dessert_query)
            desserts = result.all()

            for dessert, cat_name in desserts:
                suggestions.append(OrderSuggestion(
                    item_id=dessert.id,
                    name=dessert.name,
                    description=dessert.description or "",
                    price=dessert.price,
                    suggestion_reason="End your meal on a sweet note",
                    confidence_score=0.6,
                    category_name=cat_name,
                    estimated_revenue_increase=dessert.price
                ))

        return suggestions

    async def _suggest_premium_upgrades(self, session, cart_items):
        """Suggest premium upgrades for existing items"""
        suggestions = []

        for order_item, menu_item, category_name in cart_items:
            # Look for premium versions in same category
            premium_query = select(MenuItem).where(
                and_(
                    MenuItem.is_available == True,
                    MenuItem.category_id == menu_item.category_id,
                    MenuItem.price > menu_item.price,
                    MenuItem.id != menu_item.id
                )
            ).order_by(MenuItem.price.desc()).limit(2)

            result = await session.execute(premium_query)
            premium_items = result.all()

            for premium_item in premium_items:
                price_diff = premium_item.price - menu_item.price
                suggestions.append(OrderSuggestion(
                    item_id=premium_item.id,
                    name=premium_item.name,
                    description=premium_item.description or "",
                    price=premium_item.price,
                    suggestion_reason=f"Upgrade from {menu_item.name} for just ₹{price_diff} more",
                    confidence_score=0.5,
                    category_name=category_name,
                    estimated_revenue_increase=price_diff
                ))

        return suggestions

    async def _suggest_natural_pairings(self, session, cart_items):
        """Suggest natural food pairings"""
        suggestions = []

        pairing_rules = {
            'pizza': ['garlic bread', 'salad', 'soda'],
            'burger': ['fries', 'onion rings', 'shake'],
            'pasta': ['garlic bread', 'salad', 'wine'],
            'curry': ['rice', 'naan', 'lassi'],
            'biryani': ['raita', 'shorba', 'pickle']
        }

        for order_item, menu_item, category_name in cart_items:
            item_name_lower = menu_item.name.lower()

            for food_type, pairings in pairing_rules.items():
                if food_type in item_name_lower:
                    for pairing in pairings:
                        # Search for pairing items
                        pairing_query = select(MenuItem, MenuCategory.menu_category_name.label('cat_name')).join(
                            MenuCategory, MenuItem.category_id == MenuCategory.menu_category_id
                        ).where(
                            and_(
                                MenuItem.is_available == True,
                                MenuItem.name.ilike(f'%{pairing}%')
                            )
                        ).limit(1)

                        result = await session.execute(pairing_query)
                        pairing_items = result.all()

                        for pairing_item, cat_name in pairing_items:
                            suggestions.append(OrderSuggestion(
                                item_id=pairing_item.id,
                                name=pairing_item.name,
                                description=pairing_item.description or "",
                                price=pairing_item.price,
                                suggestion_reason=f"Classic pairing with {menu_item.name}",
                                confidence_score=0.9,
                                category_name=cat_name,
                                estimated_revenue_increase=pairing_item.price
                            ))

        return suggestions

    async def _suggest_high_value_additions(self, session, cart_analysis):
        """Suggest high-value additions for revenue optimization"""
        suggestions = []

        # If cart value is low, suggest popular high-value items
        if cart_analysis['total_value'] < Decimal('30'):
            high_value_query = select(MenuItem, MenuCategory.menu_category_name.label('cat_name')).join(
                MenuCategory, MenuItem.category_id == MenuCategory.menu_category_id
            ).where(
                and_(
                    MenuItem.is_available == True,
                    MenuItem.price >= Decimal('15'),
                    MenuItem.is_popular == True
                )
            ).order_by(MenuItem.price.desc()).limit(3)

            result = await session.execute(high_value_query)
            high_value_items = result.all()

            for item, cat_name in high_value_items:
                suggestions.append(OrderSuggestion(
                    item_id=item.id,
                    name=item.name,
                    description=item.description or "",
                    price=item.price,
                    suggestion_reason="Popular premium choice - treat yourself!",
                    confidence_score=0.6,
                    category_name=cat_name,
                    estimated_revenue_increase=item.price
                ))

        return suggestions

    async def _suggest_small_additions(self, session, cart_analysis):
        """Suggest small, low-commitment additions"""
        suggestions = []

        # Small, affordable items that are easy to add
        small_items_query = select(MenuItem, MenuCategory.menu_category_name.label('cat_name')).join(
            MenuCategory, MenuItem.category_id == MenuCategory.menu_category_id
        ).where(
            and_(
                MenuItem.is_available == True,
                MenuItem.price <= Decimal('5'),
                or_(
                    MenuCategory.menu_category_name.ilike('%sauce%'),
                    MenuCategory.menu_category_name.ilike('%addon%'),
                    MenuCategory.menu_category_name.ilike('%extra%')
                )
            )
        ).limit(3)

        result = await session.execute(small_items_query)
        small_items = result.all()

        for item, cat_name in small_items:
            suggestions.append(OrderSuggestion(
                item_id=item.id,
                name=item.name,
                description=item.description or "",
                price=item.price,
                suggestion_reason="Small addition for extra flavor",
                confidence_score=0.4,
                category_name=cat_name,
                estimated_revenue_increase=item.price
            ))

        return suggestions

    async def _suggest_based_on_history(self, session, user_id: str, cart_analysis):
        """Suggest items based on user order history"""
        suggestions = []

        # Get user's frequently ordered items not in current cart
        history_query = select(
            MenuItem,
            MenuCategory.menu_category_name.label('cat_name'),
            func.count(OrderItem.id).label('order_count')
        ).join(OrderItem, MenuItem.id == OrderItem.menu_item_id).join(
            Order, OrderItem.order_id == Order.id
        ).join(MenuCategory, MenuItem.category_id == MenuCategory.menu_category_id).where(
            and_(
                Order.user_id == user_id,
                Order.status != OrderStatus.CANCELLED.value,
                MenuItem.is_available == True
            )
        ).group_by(MenuItem.id, MenuCategory.menu_category_name).order_by(
            desc('order_count')
        ).limit(3)

        result = await session.execute(history_query)
        history_items = result.all()

        for item, cat_name, order_count in history_items:
            suggestions.append(OrderSuggestion(
                item_id=item.id,
                name=item.name,
                description=item.description or "",
                price=item.price,
                suggestion_reason=f"You've enjoyed this {order_count} times before",
                confidence_score=0.8,
                category_name=cat_name,
                estimated_revenue_increase=item.price
            ))

        return suggestions

    def _rank_suggestions(self, suggestions, cart_analysis, strategy):
        """Rank and score suggestions based on strategy and context"""

        # Remove duplicates
        unique_suggestions = {}
        for suggestion in suggestions:
            if suggestion.item_id not in unique_suggestions:
                unique_suggestions[suggestion.item_id] = suggestion

        # Apply strategy-specific scoring
        for suggestion in unique_suggestions.values():
            base_score = suggestion.confidence_score

            if strategy == 'aggressive':
                # Boost high-value items
                if suggestion.price > Decimal('20'):
                    suggestion.confidence_score += 0.2
            elif strategy == 'subtle':
                # Boost low-value items
                if suggestion.price < Decimal('10'):
                    suggestion.confidence_score += 0.1

            # Boost based on cart context
            if 'beverage' in suggestion.suggestion_reason.lower() and not cart_analysis['has_beverage']:
                suggestion.confidence_score += 0.3

        # Sort by confidence score
        return sorted(unique_suggestions.values(), key=lambda x: x.confidence_score, reverse=True)


@validate_schema(Order)
@require_tables("orders", "order_items", "menu_items")
class OrderValidationTool(ToolBase):
    """
    Comprehensive order verification before confirmation.

    Validates:
    - Item availability and stock levels
    - Dietary restrictions compliance
    - Modification feasibility
    - Delivery zones and timing
    - Business rules and constraints
    """

    def __init__(self):
        super().__init__(
            name="order_validation",
            description="Comprehensive order verification and validation"
        )

    async def _execute_impl(self, **kwargs) -> ToolResult:
        """Execute comprehensive order validation"""
        try:
            order_id = kwargs.get('order_id')
            validation_level = kwargs.get('level', 'full')  # basic, full, strict

            if not order_id:
                return ToolResult(
                    status=ToolStatus.FAILURE,
                    data={"error": "Order ID is required for validation"}
                )

            async with get_db_session() as session:
                # Get order details
                order = await self._get_order_with_items(session, order_id)

                if not order:
                    return ToolResult(
                        status=ToolStatus.FAILURE,
                        data={"error": "Order not found"}
                    )

                # Perform validation checks
                validation_result = await self._perform_validation_checks(
                    session, order, validation_level
                )

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={
                        'order_id': order_id,
                        'validation_result': validation_result.__dict__,
                        'validation_level': validation_level
                    }
                )

        except Exception as e:
            logger.error(f"OrderValidationTool error: {str(e)}")
            return ToolResult(
                status=ToolStatus.FAILURE,
                data={"error": f"Order validation failed: {str(e)}"}
            )

    async def _get_order_with_items(self, session, order_id: str):
        """Get order with all items and menu details"""
        result = await session.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()

        if order:
            # Get order items
            items_result = await session.execute(
                select(OrderItem, MenuItem).join(MenuItem).where(
                    OrderItem.order_id == order_id
                )
            )
            order.items_with_menu = items_result.all()

        return order

    async def _perform_validation_checks(self, session, order, validation_level):
        """Perform comprehensive validation checks"""
        validation_result = OrderValidationResult(
            is_valid=True,
            issues=[],
            warnings=[],
            estimated_ready_time=None,
            total_amount=order.total_amount,
            availability_status={},
            dietary_conflicts=[]
        )

        # 1. Availability Check
        await self._check_item_availability(session, order, validation_result)

        # 2. Dietary Restrictions Check (if user profile available)
        await self._check_dietary_compliance(session, order, validation_result)

        # 3. Business Rules Check
        await self._check_business_rules(session, order, validation_result)

        # 4. Modification Feasibility Check
        await self._check_modification_feasibility(session, order, validation_result)

        if validation_level in ['full', 'strict']:
            # 5. Estimated Time Calculation
            await self._calculate_estimated_ready_time(session, order, validation_result)

            # 6. Delivery Zone Check (if delivery order)
            await self._check_delivery_constraints(session, order, validation_result)

        if validation_level == 'strict':
            # 7. Payment Method Validation
            await self._check_payment_constraints(session, order, validation_result)

            # 8. Peak Hours and Capacity Check
            await self._check_capacity_constraints(session, order, validation_result)

        # Final validation status
        validation_result.is_valid = len(validation_result.issues) == 0

        return validation_result

    async def _check_item_availability(self, session, order, validation_result):
        """Check if all ordered items are available"""
        for order_item, menu_item in order.items_with_menu:
            # Check basic availability
            if not menu_item.is_available:
                validation_result.issues.append(
                    f"{menu_item.name} is currently unavailable"
                )
                validation_result.availability_status[menu_item.id] = False
            else:
                validation_result.availability_status[menu_item.id] = True

            # Check quantity constraints (if any)
            if order_item.quantity > 10:  # Business rule: max 10 of same item
                validation_result.warnings.append(
                    f"Large quantity ({order_item.quantity}) of {menu_item.name} - please confirm"
                )

    async def _check_dietary_compliance(self, session, order, validation_result):
        """Check dietary restrictions compliance"""
        # Get user dietary preferences (if available)
        if hasattr(order, 'user_id'):
            user_result = await session.execute(
                select(User).where(User.id == order.user_id)
            )
            user = user_result.scalar_one_or_none()

            if user:
                # Check for dietary conflicts
                for order_item, menu_item in order.items_with_menu:
                    if menu_item.allergens:
                        # Example: Check common allergens
                        common_allergens = ['nuts', 'dairy', 'gluten', 'shellfish']
                        for allergen in menu_item.allergens:
                            if allergen.lower() in common_allergens:
                                validation_result.warnings.append(
                                    f"{menu_item.name} contains {allergen} - please verify if this is acceptable"
                                )

    async def _check_business_rules(self, session, order, validation_result):
        """Check business rules and constraints"""
        # Minimum order value check
        min_order_value = Decimal('10')  # Business rule
        if order.total_amount < min_order_value:
            validation_result.issues.append(
                f"Minimum order value is ₹{min_order_value}. Current total: ₹{order.total_amount}"
            )

        # Maximum order value check (for fraud prevention)
        max_order_value = Decimal('2000')  # Business rule
        if order.total_amount > max_order_value:
            validation_result.warnings.append(
                f"Large order value (₹{order.total_amount}) - may require additional verification"
            )

        # Check if order has items
        if not hasattr(order, 'items_with_menu') or len(order.items_with_menu) == 0:
            validation_result.issues.append("Order cannot be empty")

    async def _check_modification_feasibility(self, session, order, validation_result):
        """Check if modifications are feasible"""
        for order_item, menu_item in order.items_with_menu:
            if order_item.customizations:
                # Check if customizations are valid
                for customization, value in order_item.customizations.items():
                    if customization == 'spice_level' and value not in ['mild', 'medium', 'hot']:
                        validation_result.warnings.append(
                            f"Invalid spice level '{value}' for {menu_item.name}"
                        )
                    elif customization == 'size' and value not in ['small', 'medium', 'large']:
                        validation_result.warnings.append(
                            f"Invalid size '{value}' for {menu_item.name}"
                        )

    async def _calculate_estimated_ready_time(self, session, order, validation_result):
        """Calculate estimated preparation time"""
        base_prep_time = 15  # Base preparation time in minutes

        # Add time based on number of items and complexity
        item_count = sum(order_item.quantity for order_item, _ in order.items_with_menu)
        additional_time = item_count * 2  # 2 minutes per item

        # Add time for customizations
        customization_time = 0
        for order_item, menu_item in order.items_with_menu:
            if order_item.customizations:
                customization_time += len(order_item.customizations) * 1  # 1 minute per customization

        total_prep_time = base_prep_time + additional_time + customization_time

        # Consider current time and add to estimated ready time
        estimated_ready = datetime.now() + timedelta(minutes=total_prep_time)
        validation_result.estimated_ready_time = estimated_ready

    async def _check_delivery_constraints(self, session, order, validation_result):
        """Check delivery zone and constraints"""
        if order.order_type == 'delivery':
            if not order.delivery_address:
                validation_result.issues.append("Delivery address is required for delivery orders")

            # Add more delivery zone validation logic here
            # For now, assume all addresses are valid

            # Check delivery time constraints
            current_hour = datetime.now().hour
            if current_hour < 10 or current_hour > 22:  # Business hours 10 AM - 10 PM
                validation_result.warnings.append("Delivery may be delayed outside business hours")

    async def _check_payment_constraints(self, session, order, validation_result):
        """Check payment method constraints"""
        # Example payment constraints
        if order.total_amount > Decimal('500') and order.order_type == 'delivery':
            validation_result.warnings.append("Large delivery orders may require advance payment")

    async def _check_capacity_constraints(self, session, order, validation_result):
        """Check restaurant capacity and peak hours"""
        current_hour = datetime.now().hour

        # Peak hours check (12-2 PM, 7-9 PM)
        if (12 <= current_hour <= 14) or (19 <= current_hour <= 21):
            validation_result.warnings.append("Peak hours - longer preparation time expected")

            # Adjust estimated ready time
            if validation_result.estimated_ready_time:
                validation_result.estimated_ready_time += timedelta(minutes=15)


@validate_schema(Order)
@require_tables("orders", "order_items")
class OrderModificationTool(ToolBase):
    """
    Handle post-confirmation order changes with business rules.

    Manages:
    - Order status-based modification rules
    - Cost impact calculations
    - Kitchen notification requirements
    - Customer communication needs
    """

    def __init__(self):
        super().__init__(
            name="order_modification",
            description="Handle post-confirmation order modifications"
        )

    async def _execute_impl(self, **kwargs) -> ToolResult:
        """Execute order modification with business rules"""
        try:
            order_id = kwargs.get('order_id')
            modification_type = kwargs.get('type', 'item_change')  # item_change, cancel, special_request
            modification_details = kwargs.get('details', {})
            reason = kwargs.get('reason', '')

            if not order_id:
                return ToolResult(
                    status=ToolStatus.FAILURE,
                    data={"error": "Order ID is required for modification"}
                )

            async with get_db_session() as session:
                # Get order details
                order = await self._get_order_details(session, order_id)

                if not order:
                    return ToolResult(
                        status=ToolStatus.FAILURE,
                        data={"error": "Order not found"}
                    )

                # Check if modification is allowed
                modification_check = await self._check_modification_allowed(order, modification_type)

                if not modification_check['allowed']:
                    return ToolResult(
                        status=ToolStatus.FAILURE,
                        data={
                            "error": modification_check['reason'],
                            "order_status": order.status
                        }
                    )

                # Process the modification
                result = await self._process_modification(
                    session, order, modification_type, modification_details, reason
                )

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=result
                )

        except Exception as e:
            logger.error(f"OrderModificationTool error: {str(e)}")
            return ToolResult(
                status=ToolStatus.FAILURE,
                data={"error": f"Order modification failed: {str(e)}"}
            )

    async def _get_order_details(self, session, order_id: str):
        """Get comprehensive order details"""
        result = await session.execute(
            select(Order).where(Order.id == order_id)
        )
        return result.scalar_one_or_none()

    async def _check_modification_allowed(self, order: Order, modification_type: str):
        """Check if modification is allowed based on order status and timing"""
        current_status = order.status
        order_age = datetime.now() - order.created_at

        # Business rules for modifications
        if current_status == OrderStatus.PENDING.value:
            # All modifications allowed for pending orders
            return {'allowed': True, 'reason': 'Order is still pending'}

        elif current_status == OrderStatus.CONFIRMED.value:
            # Limited modifications allowed within 5 minutes
            if order_age.total_seconds() <= 300:  # 5 minutes
                return {'allowed': True, 'reason': 'Order confirmed recently'}
            else:
                return {
                    'allowed': False,
                    'reason': 'Order confirmed more than 5 minutes ago - modifications not allowed'
                }

        elif current_status == OrderStatus.PREPARING.value:
            # Only cancellation allowed, with potential charges
            if modification_type == 'cancel':
                return {
                    'allowed': True,
                    'reason': 'Cancellation allowed but may incur charges'
                }
            else:
                return {
                    'allowed': False,
                    'reason': 'Order is being prepared - only cancellation possible'
                }

        elif current_status in [OrderStatus.READY.value, OrderStatus.DELIVERED.value]:
            # No modifications allowed
            return {
                'allowed': False,
                'reason': f'Order is {current_status} - modifications not possible'
            }

        elif current_status == OrderStatus.CANCELLED.value:
            # No modifications allowed for cancelled orders
            return {
                'allowed': False,
                'reason': 'Order is already cancelled'
            }

        return {'allowed': False, 'reason': 'Unknown order status'}

    async def _process_modification(self, session, order, modification_type, details, reason):
        """Process the actual modification"""
        modification_result = {
            'order_id': order.id,
            'modification_type': modification_type,
            'success': False,
            'changes_made': [],
            'cost_impact': Decimal('0'),
            'requires_kitchen_notification': False,
            'requires_customer_confirmation': False,
            'message': ''
        }

        if modification_type == 'item_change':
            result = await self._handle_item_changes(session, order, details, modification_result)

        elif modification_type == 'cancel':
            result = await self._handle_order_cancellation(session, order, reason, modification_result)

        elif modification_type == 'special_request':
            result = await self._handle_special_request(session, order, details, modification_result)
        else:
            result = modification_result

        return result

    async def _handle_item_changes(self, session, order, details, modification_result):
        """Handle item additions, removals, or quantity changes"""
        try:
            changes_made = []
            total_cost_impact = Decimal('0')

            # Handle item additions
            if 'add_items' in details:
                for item_to_add in details['add_items']:
                    from app.features.food_ordering.tools.order_tools import AddOrderItemTool
                    add_tool = AddOrderItemTool()

                    result = await add_tool.execute(
                        order_id=order.id,
                        menu_item_id=item_to_add['item_id'],
                        quantity=item_to_add.get('quantity', 1),
                        customizations=item_to_add.get('customizations', {}),
                        special_instructions=item_to_add.get('special_instructions')
                    )

                    if result.status == ToolStatus.SUCCESS:
                        # Get item price for cost calculation
                        item_result = await session.execute(
                            select(MenuItem).where(MenuItem.id == item_to_add['item_id'])
                        )
                        menu_item = item_result.scalar_one()

                        item_cost = menu_item.price * item_to_add.get('quantity', 1)
                        total_cost_impact += item_cost

                        changes_made.append(f"Added {item_to_add.get('quantity', 1)}x {menu_item.name}")

            # Handle item removals
            if 'remove_items' in details:
                for item_to_remove in details['remove_items']:
                    # Get order item details first
                    order_item_result = await session.execute(
                        select(OrderItem, MenuItem).join(MenuItem).where(
                            and_(
                                OrderItem.order_id == order.id,
                                OrderItem.menu_item_id == item_to_remove['item_id']
                            )
                        )
                    )
                    order_item_data = order_item_result.first()

                    if order_item_data:
                        order_item, menu_item = order_item_data

                        from app.features.food_ordering.tools.order_tools import RemoveOrderItemTool
                        remove_tool = RemoveOrderItemTool()

                        result = await remove_tool.execute(order_item_id=order_item.id)

                        if result.status == ToolStatus.SUCCESS:
                            total_cost_impact -= order_item.total_price
                            changes_made.append(f"Removed {order_item.quantity}x {menu_item.name}")

            # Handle quantity updates
            if 'update_quantities' in details:
                for item_update in details['update_quantities']:
                    from app.features.food_ordering.tools.order_tools import UpdateOrderItemTool
                    update_tool = UpdateOrderItemTool()

                    # Get current order item
                    order_item_result = await session.execute(
                        select(OrderItem, MenuItem).join(MenuItem).where(
                            OrderItem.id == item_update['order_item_id']
                        )
                    )
                    order_item_data = order_item_result.first()

                    if order_item_data:
                        order_item, menu_item = order_item_data
                        old_quantity = order_item.quantity
                        new_quantity = item_update['new_quantity']

                        result = await update_tool.execute(
                            order_item_id=item_update['order_item_id'],
                            quantity=new_quantity
                        )

                        if result.status == ToolStatus.SUCCESS:
                            quantity_diff = new_quantity - old_quantity
                            cost_diff = menu_item.price * quantity_diff
                            total_cost_impact += cost_diff

                            changes_made.append(
                                f"Updated {menu_item.name} quantity from {old_quantity} to {new_quantity}"
                            )

            # Recalculate order total
            if changes_made:
                from app.features.food_ordering.tools.order_tools import CalculateOrderTotalTool
                calc_tool = CalculateOrderTotalTool()
                await calc_tool.execute(order_id=order.id)

            modification_result.update({
                'success': len(changes_made) > 0,
                'changes_made': changes_made,
                'cost_impact': total_cost_impact,
                'requires_kitchen_notification': len(changes_made) > 0,
                'requires_customer_confirmation': abs(total_cost_impact) > Decimal('10'),
                'message': f"Successfully made {len(changes_made)} changes to your order"
            })

        except Exception as e:
            modification_result.update({
                'success': False,
                'message': f"Failed to modify items: {str(e)}"
            })

        return modification_result

    async def _handle_order_cancellation(self, session, order, reason, modification_result):
        """Handle complete order cancellation"""
        try:
            # Update order status to cancelled
            from app.features.food_ordering.tools.order_tools import UpdateOrderStatusTool
            status_tool = UpdateOrderStatusTool()

            result = await status_tool.execute(
                order_id=order.id,
                new_status=OrderStatus.CANCELLED.value,
                status_reason=reason
            )

            if result.status == ToolStatus.SUCCESS:
                # Calculate cancellation charges if applicable
                cancellation_charge = Decimal('0')
                if order.status == OrderStatus.PREPARING.value:
                    # 20% cancellation charge for orders being prepared
                    cancellation_charge = order.total_amount * Decimal('0.2')

                modification_result.update({
                    'success': True,
                    'changes_made': ['Order cancelled'],
                    'cost_impact': -order.total_amount + cancellation_charge,
                    'cancellation_charge': cancellation_charge,
                    'requires_kitchen_notification': True,
                    'requires_customer_confirmation': True,
                    'message': f"Order cancelled successfully. Cancellation charge: ₹{cancellation_charge}"
                })
            else:
                modification_result.update({
                    'success': False,
                    'message': 'Failed to cancel order'
                })

        except Exception as e:
            modification_result.update({
                'success': False,
                'message': f"Failed to cancel order: {str(e)}"
            })

        return modification_result

    async def _handle_special_request(self, session, order, details, modification_result):
        """Handle special requests and instructions"""
        try:
            # Update order special instructions
            await session.execute(
                update(Order).where(Order.id == order.id).values(
                    special_instructions=details.get('instructions', '')
                )
            )
            await session.commit()

            modification_result.update({
                'success': True,
                'changes_made': ['Added special instructions'],
                'cost_impact': Decimal('0'),
                'requires_kitchen_notification': True,
                'requires_customer_confirmation': False,
                'message': 'Special instructions added to your order'
            })

        except Exception as e:
            modification_result.update({
                'success': False,
                'message': f"Failed to add special instructions: {str(e)}"
            })

        return modification_result


@validate_schema(Order)
@require_tables("orders", "order_items")
class SmartOrderTrackingTool(ToolBase):
    """
    Proactive order status communication and tracking.

    Provides:
    - Real-time preparation tracking
    - Estimated delivery/pickup time updates
    - Delay notifications with compensation
    - Integration with kitchen workflow
    """

    def __init__(self):
        super().__init__(
            name="smart_order_tracking",
            description="Proactive order status tracking and communication"
        )

    async def _execute_impl(self, **kwargs) -> ToolResult:
        """Execute smart order tracking operations"""
        try:
            operation = kwargs.get('operation', 'get_status')  # get_status, update_status, check_delays
            order_id = kwargs.get('order_id')
            user_id = kwargs.get('user_id')

            if operation == 'get_status' and not order_id:
                return ToolResult(
                    status=ToolStatus.FAILURE,
                    data={"error": "Order ID is required for status tracking"}
                )

            async with get_db_session() as session:
                if operation == 'get_status' and order_id:
                    result = await self._get_order_status(session, order_id)
                elif operation == 'update_status':
                    # Handle status update (would need to implement this method)
                    result = {"message": "Status update not implemented yet"}
                elif operation == 'check_delays':
                    if user_id:
                        result = await self._check_order_delays(session, user_id)
                    else:
                        result = {"error": "User ID required for delay check"}
                elif operation == 'get_user_orders':
                    if user_id:
                        result = await self._get_user_active_orders(session, user_id)
                    else:
                        result = {"error": "User ID required for user orders"}
                else:
                    return ToolResult(
                        status=ToolStatus.FAILURE,
                        data={"error": f"Unknown operation: {operation}"}
                    )

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=result
                )

        except Exception as e:
            logger.error(f"SmartOrderTrackingTool error: {str(e)}")
            return ToolResult(
                status=ToolStatus.FAILURE,
                data={"error": f"Order tracking failed: {str(e)}"}
            )

    async def _get_order_status(self, session, order_id: str):
        """Get comprehensive order status with tracking information"""
        # Get order with items
        order_result = await session.execute(
            select(Order).where(Order.id == order_id)
        )
        order = order_result.scalar_one_or_none()

        if not order:
            return {"error": "Order not found"}

        # Calculate time-based information
        order_age = datetime.now() - order.created_at

        # Estimate completion based on status
        estimated_completion = self._calculate_estimated_completion(order, order_age)

        # Check for delays
        is_delayed = self._check_if_delayed(order, order_age)

        return {
            'order_id': order.id,
            'order_number': order.order_number,
            'status': order.status,
            'order_type': order.order_type,
            'total_amount': float(order.total_amount),
            'created_at': order.created_at.isoformat(),
            'order_age_minutes': int(order_age.total_seconds() / 60),
            'estimated_ready_time': order.estimated_ready_time.isoformat() if order.estimated_ready_time else None,
            'estimated_completion': estimated_completion.isoformat() if estimated_completion else None,
            'is_delayed': is_delayed,
            'tracking_info': self._generate_tracking_info(order, order_age),
            'next_status': self._get_next_expected_status(order.status),
            'can_cancel': self._can_cancel_order(order, order_age)
        }

    def _calculate_estimated_completion(self, order: Order, order_age: timedelta):
        """Calculate estimated completion time based on current status"""
        if order.estimated_ready_time:
            return order.estimated_ready_time

        # Default estimation based on status
        status_time_estimates = {
            OrderStatus.PENDING.value: 30,  # 30 minutes from now
            OrderStatus.CONFIRMED.value: 25,  # 25 minutes remaining
            OrderStatus.PREPARING.value: 15,  # 15 minutes remaining
            OrderStatus.READY.value: 0,      # Ready now
        }

        if order.status in status_time_estimates:
            remaining_minutes = status_time_estimates[order.status]
            return datetime.now() + timedelta(minutes=remaining_minutes)

        return None

    def _check_if_delayed(self, order: Order, order_age: timedelta):
        """Check if order is delayed based on expected times"""
        expected_times = {
            OrderStatus.PENDING.value: 5,   # Should be confirmed within 5 minutes
            OrderStatus.CONFIRMED.value: 10, # Should start preparing within 10 minutes
            OrderStatus.PREPARING.value: 30, # Should be ready within 30 minutes
        }

        if order.status in expected_times:
            expected_minutes = expected_times[order.status]
            return order_age.total_seconds() > (expected_minutes * 60)

        return False

    def _generate_tracking_info(self, order: Order, order_age: timedelta):
        """Generate user-friendly tracking information"""
        status_messages = {
            OrderStatus.PENDING.value: "Your order has been received and is being reviewed",
            OrderStatus.CONFIRMED.value: "Your order has been confirmed and will start preparation soon",
            OrderStatus.PREPARING.value: "Your order is being prepared by our kitchen team",
            OrderStatus.READY.value: "Your order is ready for pickup/delivery",
            OrderStatus.DELIVERED.value: "Your order has been delivered",
            OrderStatus.CANCELLED.value: "Your order has been cancelled"
        }

        progress_steps = [
            {'step': 'Order Placed', 'completed': True, 'time': order.created_at},
            {'step': 'Order Confirmed', 'completed': order.status != OrderStatus.PENDING.value, 'time': None},
            {'step': 'Preparation Started', 'completed': order.status in [OrderStatus.PREPARING.value, OrderStatus.READY.value, OrderStatus.DELIVERED.value], 'time': None},
            {'step': 'Order Ready', 'completed': order.status in [OrderStatus.READY.value, OrderStatus.DELIVERED.value], 'time': None},
        ]

        if order.order_type == 'delivery':
            progress_steps.append({
                'step': 'Delivered',
                'completed': order.status == OrderStatus.DELIVERED.value,
                'time': None
            })
        else:
            progress_steps.append({
                'step': 'Picked Up',
                'completed': order.status == OrderStatus.DELIVERED.value,
                'time': None
            })

        return {
            'message': status_messages.get(order.status, "Unknown status"),
            'progress_steps': progress_steps,
            'order_age_friendly': self._format_time_friendly(order_age)
        }

    def _format_time_friendly(self, time_delta: timedelta):
        """Format time delta in user-friendly way"""
        minutes = int(time_delta.total_seconds() / 60)
        if minutes < 1:
            return "Just now"
        elif minutes < 60:
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            hours = minutes // 60
            remaining_minutes = minutes % 60
            if remaining_minutes == 0:
                return f"{hours} hour{'s' if hours != 1 else ''} ago"
            else:
                return f"{hours}h {remaining_minutes}m ago"

    def _get_next_expected_status(self, current_status: str):
        """Get the next expected status in the workflow"""
        status_flow = {
            OrderStatus.PENDING.value: OrderStatus.CONFIRMED.value,
            OrderStatus.CONFIRMED.value: OrderStatus.PREPARING.value,
            OrderStatus.PREPARING.value: OrderStatus.READY.value,
            OrderStatus.READY.value: OrderStatus.DELIVERED.value,
        }
        return status_flow.get(current_status)

    def _can_cancel_order(self, order: Order, order_age: timedelta):
        """Determine if order can still be cancelled"""
        if order.status in [OrderStatus.DELIVERED.value, OrderStatus.CANCELLED.value]:
            return False

        if order.status == OrderStatus.PREPARING.value and order_age.total_seconds() > 300:  # 5 minutes
            return False  # Too late to cancel without charges

        return True

    async def _get_user_active_orders(self, session, user_id: str):
        """Get all active orders for a user"""
        if not user_id:
            return {"error": "User ID is required"}

        result = await session.execute(
            select(Order).where(
                and_(
                    Order.user_id == user_id,
                    Order.status.in_([
                        OrderStatus.PENDING.value,
                        OrderStatus.CONFIRMED.value,
                        OrderStatus.PREPARING.value,
                        OrderStatus.READY.value
                    ])
                )
            ).order_by(desc(Order.created_at))
        )

        active_orders = result.scalars().all()

        orders_info = []
        for order in active_orders:
            order_age = datetime.now() - order.created_at
            orders_info.append({
                'order_id': order.id,
                'order_number': order.order_number,
                'status': order.status,
                'total_amount': float(order.total_amount),
                'order_type': order.order_type,
                'created_at': order.created_at.isoformat(),
                'is_delayed': self._check_if_delayed(order, order_age),
                'estimated_ready_time': order.estimated_ready_time.isoformat() if order.estimated_ready_time else None
            })

        return {
            'user_id': user_id,
            'active_orders': orders_info,
            'total_active_orders': len(orders_info)
        }

    async def _check_order_delays(self, session, user_id: Optional[str] = None):
        """Check for delayed orders and generate notifications"""
        # Get orders that might be delayed
        delay_threshold = datetime.now() - timedelta(minutes=30)

        query = select(Order).where(
            and_(
                Order.status.in_([
                    OrderStatus.CONFIRMED.value,
                    OrderStatus.PREPARING.value
                ]),
                Order.created_at < delay_threshold
            )
        )

        if user_id:
            query = query.where(Order.user_id == user_id)

        result = await session.execute(query)
        potentially_delayed_orders = result.scalars().all()

        delayed_orders = []
        for order in potentially_delayed_orders:
            order_age = datetime.now() - order.created_at
            if self._check_if_delayed(order, order_age):
                delayed_orders.append({
                    'order_id': order.id,
                    'order_number': order.order_number,
                    'user_id': order.user_id,
                    'status': order.status,
                    'delay_minutes': int(order_age.total_seconds() / 60) - 30,  # Minutes over expected
                    'total_amount': float(order.total_amount),
                    'requires_notification': True,
                    'suggested_compensation': self._suggest_compensation(order, order_age)
                })

        return {
            'delayed_orders': delayed_orders,
            'total_delayed': len(delayed_orders)
        }

    def _suggest_compensation(self, order: Order, order_age: timedelta):
        """Suggest appropriate compensation for delayed orders"""
        delay_minutes = order_age.total_seconds() / 60 - 30  # Minutes over expected 30 minutes

        if delay_minutes > 60:  # More than 1 hour delay
            return {
                'type': 'discount',
                'value': 20,  # 20% discount
                'description': 'Significant delay - 20% discount on this order'
            }
        elif delay_minutes > 30:  # 30-60 minutes delay
            return {
                'type': 'discount',
                'value': 10,  # 10% discount
                'description': 'Extended delay - 10% discount on this order'
            }
        elif delay_minutes > 15:  # 15-30 minutes delay
            return {
                'type': 'coupon',
                'value': 50,  # ₹50 coupon
                'description': 'Delay apology - ₹50 coupon for next order'
            }
        else:
            return {
                'type': 'apology',
                'value': 0,
                'description': 'Sincere apology for the delay'
            }


@validate_schema(Order)
@require_tables("orders", "order_items", "menu_items", "users")
class OrderPersonalizationTool(ToolBase):
    """
    User history-based suggestions and quick reorders.

    Provides:
    - Previous order quick-reorder
    - Favorite items suggestions
    - Dietary preference memory
    - Custom modification templates
    """

    def __init__(self):
        super().__init__(
            name="order_personalization",
            description="User history-based order personalization and suggestions"
        )

    async def _execute_impl(self, **kwargs) -> ToolResult:
        """Execute order personalization operations"""
        try:
            operation = kwargs.get('operation', 'get_suggestions')  # get_suggestions, reorder, favorites
            user_id = kwargs.get('user_id')
            limit = kwargs.get('limit', 5)

            if not user_id:
                return ToolResult(
                    status=ToolStatus.FAILURE,
                    data={"error": "User ID is required for personalization"}
                )

            async with get_db_session() as session:
                if operation == 'get_suggestions':
                    result = await self._get_personalized_suggestions(session, user_id, limit)
                elif operation == 'reorder':
                    result = await self._handle_reorder(session, user_id, kwargs)
                elif operation == 'favorites':
                    result = await self._get_favorite_items(session, user_id, limit)
                elif operation == 'order_history':
                    result = await self._get_order_history(session, user_id, limit)
                else:
                    return ToolResult(
                        status=ToolStatus.FAILURE,
                        data={"error": f"Unknown operation: {operation}"}
                    )

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=result
                )

        except Exception as e:
            logger.error(f"OrderPersonalizationTool error: {str(e)}")
            return ToolResult(
                status=ToolStatus.FAILURE,
                data={"error": f"Order personalization failed: {str(e)}"}
            )

    async def _get_personalized_suggestions(self, session, user_id: str, limit: int):
        """Get personalized menu suggestions based on user history"""

        # Get user's order history
        order_history = await self._analyze_user_order_patterns(session, user_id)

        suggestions = {
            'user_id': user_id,
            'suggestion_categories': [],
            'total_suggestions': 0
        }

        # Category 1: Frequently ordered items
        frequent_items = await self._get_frequently_ordered_items(session, user_id, limit=3)
        if frequent_items:
            suggestions['suggestion_categories'].append({
                'category': 'Your Favorites',
                'description': 'Items you order most often',
                'items': frequent_items
            })

        # Category 2: Items similar to user preferences
        similar_items = await self._get_similar_preference_items(session, user_id, order_history, limit=3)
        if similar_items:
            suggestions['suggestion_categories'].append({
                'category': 'You Might Like',
                'description': 'Based on your taste preferences',
                'items': similar_items
            })

        # Category 3: New items in favorite categories
        new_items = await self._get_new_items_in_favorite_categories(session, user_id, order_history, limit=2)
        if new_items:
            suggestions['suggestion_categories'].append({
                'category': 'New Arrivals',
                'description': 'New items in categories you love',
                'items': new_items
            })

        # Category 4: Seasonal/promotional recommendations
        seasonal_items = await self._get_seasonal_recommendations(session, user_id, limit=2)
        if seasonal_items:
            suggestions['suggestion_categories'].append({
                'category': 'Seasonal Picks',
                'description': 'Special items for this time',
                'items': seasonal_items
            })

        suggestions['total_suggestions'] = sum(len(cat['items']) for cat in suggestions['suggestion_categories'])

        return suggestions

    async def _analyze_user_order_patterns(self, session, user_id: str):
        """Analyze user's ordering patterns and preferences"""

        # Get order statistics
        order_stats_query = select(
            func.count(Order.id).label('total_orders'),
            func.avg(Order.total_amount).label('avg_order_value'),
            func.array_agg(Order.order_type).label('order_types')
        ).where(
            and_(
                Order.user_id == user_id,
                Order.status != OrderStatus.CANCELLED.value
            )
        )

        stats_result = await session.execute(order_stats_query)
        order_stats = stats_result.first()

        # Get category preferences
        category_prefs_query = select(
            MenuCategory.menu_category_name,
            func.count(OrderItem.id).label('order_count'),
            func.sum(OrderItem.total_price).label('total_spent')
        ).select_from(
            OrderItem.join(Order).join(MenuItem).join(MenuCategory)
        ).where(
            and_(
                Order.user_id == user_id,
                Order.status != OrderStatus.CANCELLED.value
            )
        ).group_by(MenuCategory.menu_category_name).order_by(desc('order_count'))

        category_result = await session.execute(category_prefs_query)
        category_preferences = category_result.all()

        # Get dietary patterns
        dietary_patterns = await self._extract_dietary_patterns(session, user_id)

        return {
            'total_orders': order_stats.total_orders if order_stats else 0,
            'avg_order_value': float(order_stats.avg_order_value) if order_stats and order_stats.avg_order_value else 0,
            'preferred_order_types': order_stats.order_types if order_stats else [],
            'category_preferences': [
                {
                    'category': cat.name,
                    'order_count': cat.order_count,
                    'total_spent': float(cat.total_spent)
                } for cat in category_preferences
            ],
            'dietary_patterns': dietary_patterns
        }

    async def _extract_dietary_patterns(self, session, user_id: str):
        """Extract dietary patterns from user's order history"""

        # Get dietary info from ordered items
        dietary_query = select(
            MenuItem.dietary_info,
            MenuItem.spice_level,
            func.count(OrderItem.id).label('count')
        ).select_from(
            OrderItem.join(Order).join(MenuItem)
        ).where(
            and_(
                Order.user_id == user_id,
                Order.status != OrderStatus.CANCELLED.value,
                MenuItem.dietary_info.isnot(None)
            )
        ).group_by(MenuItem.dietary_info, MenuItem.spice_level)

        result = await session.execute(dietary_query)
        dietary_data = result.all()

        # Analyze patterns
        dietary_preferences = {}
        spice_preferences = {}

        for item in dietary_data:
            if item.dietary_info:
                for dietary_tag in item.dietary_info:
                    dietary_preferences[dietary_tag] = dietary_preferences.get(dietary_tag, 0) + item.count

            if item.spice_level:
                spice_preferences[item.spice_level] = spice_preferences.get(item.spice_level, 0) + item.count

        return {
            'dietary_preferences': dietary_preferences,
            'spice_preferences': spice_preferences
        }

    async def _get_frequently_ordered_items(self, session, user_id: str, limit: int):
        """Get user's most frequently ordered items"""

        frequent_query = select(
            MenuItem,
            MenuCategory.menu_category_name.label('category_name'),
            func.count(OrderItem.id).label('order_count'),
            func.sum(OrderItem.quantity).label('total_quantity'),
            func.avg(OrderItem.unit_price).label('avg_price')
        ).select_from(
            OrderItem.join(Order).join(MenuItem).join(MenuCategory)
        ).where(
            and_(
                Order.user_id == user_id,
                Order.status != OrderStatus.CANCELLED.value,
                MenuItem.is_available == True
            )
        ).group_by(
            MenuItem.id, MenuCategory.menu_category_name
        ).order_by(
            desc('order_count'), desc('total_quantity')
        ).limit(limit)

        result = await session.execute(frequent_query)
        frequent_items = result.all()

        items = []
        for item_data in frequent_items:
            menu_item, category_name, order_count, total_quantity, avg_price = item_data
            # Serialize menu item
            item_dict = serialize_output_with_schema(
                MenuItemSummaryResponse,
                menu_item,
                "order_personalization",
                from_orm=True
            )
            # Add personalization metadata
            item_dict.update({
                'category_name': category_name,
                'order_count': order_count,
                'total_quantity': total_quantity,
                'avg_price': float(avg_price) if avg_price else float(menu_item.price),
                'dietary_info': menu_item.dietary_info or [],
                'reason': f"You've ordered this {order_count} times"
            })
            items.append(item_dict)

        return items

    async def _get_similar_preference_items(self, session, user_id: str, order_history: Dict, limit: int):
        """Get items similar to user's preferences but not yet ordered"""

        if not order_history['category_preferences']:
            return []

        # Get top preferred categories
        top_categories = [cat['category'] for cat in order_history['category_preferences'][:3]]

        # Get items from preferred categories that user hasn't ordered
        ordered_items_query = select(MenuItem.id).select_from(
            OrderItem.join(Order).join(MenuItem)
        ).where(
            and_(
                Order.user_id == user_id,
                Order.status != OrderStatus.CANCELLED.value
            )
        )

        ordered_items_result = await session.execute(ordered_items_query)
        ordered_item_ids = {item.id for item in ordered_items_result.scalars().all()}

        # Get unordered items from preferred categories
        base_conditions = [
            MenuCategory.menu_category_name.in_(top_categories),
            MenuItem.is_available == True
        ]

        if ordered_item_ids:
            base_conditions.append(~MenuItem.id.in_(ordered_item_ids))

        similar_query = select(
            MenuItem,
            MenuCategory.menu_category_name.label('category_name')
        ).join(MenuCategory).where(
            and_(*base_conditions)
        ).order_by(MenuItem.is_popular.desc()).limit(limit)

        result = await session.execute(similar_query)
        similar_items = result.all()

        items = []
        for menu_item, category_name in similar_items:
            items.append({
                'item_id': menu_item.id,
                'name': menu_item.name,
                'description': menu_item.description,
                'price': float(menu_item.price),
                'category_name': category_name,
                'dietary_info': menu_item.dietary_info or [],
                'is_popular': menu_item.is_popular,
                'reason': f"Popular in {category_name}, which you love"
            })

        return items

    async def _get_new_items_in_favorite_categories(self, session, user_id: str, order_history: Dict, limit: int):
        """Get new items in user's favorite categories"""

        if not order_history['category_preferences']:
            return []

        top_categories = [cat['category'] for cat in order_history['category_preferences'][:2]]

        # Get items added in last 30 days from preferred categories
        new_items_cutoff = datetime.now() - timedelta(days=30)

        new_items_query = select(
            MenuItem,
            MenuCategory.menu_category_name.label('category_name')
        ).join(MenuCategory).where(
            and_(
                MenuCategory.menu_category_name.in_(top_categories),
                MenuItem.is_available == True,
                MenuItem.created_at >= new_items_cutoff
            )
        ).order_by(desc(MenuItem.created_at)).limit(limit)

        result = await session.execute(new_items_query)
        new_items = result.all()

        items = []
        for menu_item, category_name in new_items:
            items.append({
                'item_id': menu_item.id,
                'name': menu_item.name,
                'description': menu_item.description,
                'price': float(menu_item.price),
                'category_name': category_name,
                'dietary_info': menu_item.dietary_info or [],
                'reason': f"New in {category_name}"
            })

        return items

    async def _get_seasonal_recommendations(self, session, user_id: str, limit: int):
        """Get seasonal or promotional recommendations"""

        # Get popular items that user hasn't ordered recently
        recent_orders_query = select(MenuItem.id).select_from(
            OrderItem.join(Order).join(MenuItem)
        ).where(
            and_(
                Order.user_id == user_id,
                Order.created_at >= datetime.now() - timedelta(days=30),
                Order.status != OrderStatus.CANCELLED.value
            )
        )

        recent_items_result = await session.execute(recent_orders_query)
        recent_item_ids = {item.id for item in recent_items_result.scalars().all()}

        # Get popular items not ordered recently
        seasonal_conditions = [
            MenuItem.is_available == True,
            MenuItem.is_popular == True
        ]

        if recent_item_ids:
            seasonal_conditions.append(~MenuItem.id.in_(recent_item_ids))

        seasonal_query = select(
            MenuItem,
            MenuCategory.menu_category_name.label('category_name')
        ).join(MenuCategory).where(
            and_(*seasonal_conditions)
        ).order_by(func.random()).limit(limit)

        result = await session.execute(seasonal_query)
        seasonal_items = result.all()

        items = []
        for menu_item, category_name in seasonal_items:
            items.append({
                'item_id': menu_item.id,
                'name': menu_item.name,
                'description': menu_item.description,
                'price': float(menu_item.price),
                'category_name': category_name,
                'dietary_info': menu_item.dietary_info or [],
                'reason': "Trending choice among our customers"
            })

        return items

    async def _handle_reorder(self, session, user_id: str, kwargs):
        """Handle quick reorder from previous orders"""

        order_to_reorder = kwargs.get('previous_order_id')
        target_cart_id = kwargs.get('target_order_id')  # Cart to add items to

        if not order_to_reorder:
            # Get most recent order if not specified
            recent_order_query = select(Order).where(
                and_(
                    Order.user_id == user_id,
                    Order.status != OrderStatus.CANCELLED.value
                )
            ).order_by(desc(Order.created_at)).limit(1)

            result = await session.execute(recent_order_query)
            recent_order = result.scalar_one_or_none()

            if not recent_order:
                return {"error": "No previous orders found"}

            order_to_reorder = recent_order.id

        # Get items from the order to reorder
        reorder_items_query = select(
            OrderItem, MenuItem
        ).join(MenuItem).where(
            OrderItem.order_id == order_to_reorder
        )

        result = await session.execute(reorder_items_query)
        items_to_reorder = result.all()

        if not items_to_reorder:
            return {"error": "No items found in the specified order"}

        # Add items to current cart
        reordered_items = []
        for order_item, menu_item in items_to_reorder:
            if menu_item.is_available:
                # Use SmartCartManagementTool to add items
                cart_tool = SmartCartManagementTool()
                add_result = await cart_tool.execute(
                    operation='add',
                    user_id=user_id,
                    order_id=target_cart_id,
                    item_details={
                        'item_id': menu_item.id,
                        'quantity': order_item.quantity,
                        'customizations': order_item.customizations or {},
                        'special_instructions': order_item.special_instructions
                    }
                )

                if add_result.status == ToolStatus.SUCCESS:
                    reordered_items.append({
                        'name': menu_item.name,
                        'quantity': order_item.quantity,
                        'price': float(menu_item.price)
                    })
            else:
                # Item not available
                reordered_items.append({
                    'name': menu_item.name,
                    'quantity': order_item.quantity,
                    'status': 'unavailable',
                    'message': 'This item is currently unavailable'
                })

        return {
            'operation': 'reorder',
            'previous_order_id': order_to_reorder,
            'target_order_id': target_cart_id,
            'reordered_items': reordered_items,
            'successful_items': len([item for item in reordered_items if 'status' not in item]),
            'unavailable_items': len([item for item in reordered_items if item.get('status') == 'unavailable']),
            'message': f"Successfully reordered {len([item for item in reordered_items if 'status' not in item])} items"
        }

    async def _get_favorite_items(self, session, user_id: str, limit: int):
        """Get user's top favorite items based on frequency and recency"""

        # Weight recent orders more heavily
        favorites_query = select(
            MenuItem,
            MenuCategory.menu_category_name.label('category_name'),
            func.count(OrderItem.id).label('order_count'),
            func.max(Order.created_at).label('last_ordered'),
            func.avg(OrderItem.unit_price).label('avg_price')
        ).select_from(
            OrderItem.join(Order).join(MenuItem).join(MenuCategory)
        ).where(
            and_(
                Order.user_id == user_id,
                Order.status != OrderStatus.CANCELLED.value,
                MenuItem.is_available == True
            )
        ).group_by(
            MenuItem.id, MenuCategory.menu_category_name
        ).order_by(
            desc('order_count'),
            desc('last_ordered')
        ).limit(limit)

        result = await session.execute(favorites_query)
        favorite_items = result.all()

        items = []
        for item_data in favorite_items:
            menu_item, category_name, order_count, last_ordered, avg_price = item_data

            # Calculate recency score
            days_since_last = (datetime.now() - last_ordered).days if last_ordered else 999
            recency_bonus = max(0, 30 - days_since_last) / 30  # Bonus for recent orders

            items.append({
                'item_id': menu_item.id,
                'name': menu_item.name,
                'description': menu_item.description,
                'price': float(menu_item.price),
                'category_name': category_name,
                'order_count': order_count,
                'last_ordered': last_ordered.isoformat() if last_ordered else None,
                'days_since_last': days_since_last,
                'recency_bonus': recency_bonus,
                'dietary_info': menu_item.dietary_info or [],
                'favorite_score': order_count + (recency_bonus * 5)  # Combined score
            })

        # Sort by favorite score
        items.sort(key=lambda x: x['favorite_score'], reverse=True)

        return {
            'user_id': user_id,
            'favorite_items': items,
            'total_favorites': len(items)
        }

    async def _get_order_history(self, session, user_id: str, limit: int):
        """Get user's order history with details"""

        history_query = select(Order).where(
            Order.user_id == user_id
        ).order_by(desc(Order.created_at)).limit(limit)

        result = await session.execute(history_query)
        orders = result.scalars().all()

        order_history = []
        for order in orders:
            # Get order items
            items_query = select(
                OrderItem, MenuItem
            ).join(MenuItem).where(
                OrderItem.order_id == order.id
            )

            items_result = await session.execute(items_query)
            order_items = items_result.all()

            order_history.append({
                'order_id': order.id,
                'order_number': order.order_number,
                'status': order.status,
                'order_type': order.order_type,
                'total_amount': float(order.total_amount),
                'created_at': order.created_at.isoformat(),
                'items': [
                    {
                        'name': menu_item.name,
                        'quantity': order_item.quantity,
                        'unit_price': float(order_item.unit_price),
                        'total_price': float(order_item.total_price),
                        'customizations': order_item.customizations or {}
                    }
                    for order_item, menu_item in order_items
                ],
                'item_count': len(order_items),
                'can_reorder': order.status != OrderStatus.CANCELLED.value
            })

        return {
            'user_id': user_id,
            'order_history': order_history,
            'total_orders': len(order_history)
        }


@validate_schema(Order)
@require_tables("orders", "order_items", "menu_items")
class OrderAnalyticsTool(ToolBase):
    """
    Business intelligence for order optimization.

    Provides:
    - Cart abandonment analysis
    - Upselling success tracking
    - Popular modification patterns
    - Revenue optimization insights
    """

    def __init__(self):
        super().__init__(
            name="order_analytics",
            description="Business intelligence and analytics for order optimization"
        )

    async def _execute_impl(self, **kwargs) -> ToolResult:
        """Execute order analytics operations"""
        try:
            analysis_type = kwargs.get('type', 'overview')  # overview, abandonment, upselling, patterns
            time_period = kwargs.get('period', 7)  # days
            user_id = kwargs.get('user_id')  # for user-specific analytics

            async with get_db_session() as session:
                if analysis_type == 'overview':
                    result = await self._get_analytics_overview(session, time_period, user_id)
                elif analysis_type == 'abandonment':
                    result = await self._analyze_cart_abandonment(session, time_period, user_id)
                elif analysis_type == 'upselling':
                    result = await self._analyze_upselling_performance(session, time_period, user_id)
                elif analysis_type == 'patterns':
                    result = await self._analyze_order_patterns(session, time_period, user_id)
                elif analysis_type == 'revenue':
                    result = await self._analyze_revenue_metrics(session, time_period, user_id)
                else:
                    return ToolResult(
                        status=ToolStatus.FAILURE,
                        data={"error": f"Unknown analysis type: {analysis_type}"}
                    )

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=result
                )

        except Exception as e:
            logger.error(f"OrderAnalyticsTool error: {str(e)}")
            return ToolResult(
                status=ToolStatus.FAILURE,
                data={"error": f"Order analytics failed: {str(e)}"}
            )

    async def _get_analytics_overview(self, session, time_period: int, user_id: Optional[str]):
        """Get comprehensive analytics overview"""

        cutoff_date = datetime.now() - timedelta(days=time_period)

        # Base query filters
        base_filters = [Order.created_at >= cutoff_date]
        if user_id:
            base_filters.append(Order.user_id == user_id)

        # Total orders and revenue
        overview_query = select(
            func.count(Order.id).label('total_orders'),
            func.sum(Order.total_amount).label('total_revenue'),
            func.avg(Order.total_amount).label('avg_order_value'),
            func.count(func.distinct(Order.user_id)).label('unique_customers')
        ).where(and_(*base_filters, Order.status != OrderStatus.CANCELLED.value))

        overview_result = await session.execute(overview_query)
        overview = overview_result.first()

        # Order status distribution
        status_query = select(
            Order.status,
            func.count(Order.id).label('count')
        ).where(and_(*base_filters)).group_by(Order.status)

        status_result = await session.execute(status_query)
        status_distribution = {row.status: row.count for row in status_result.all()}

        # Order type distribution
        type_query = select(
            Order.order_type,
            func.count(Order.id).label('count'),
            func.avg(Order.total_amount).label('avg_value')
        ).where(and_(*base_filters, Order.status != OrderStatus.CANCELLED.value)).group_by(Order.order_type)

        type_result = await session.execute(type_query)
        type_distribution = [
            {
                'type': row.order_type,
                'count': row.count,
                'avg_value': float(row.avg_value) if row.avg_value else 0
            }
            for row in type_result.all()
        ]

        # Top selling items
        top_items_query = select(
            MenuItem.name,
            MenuCategory.menu_category_name.label('category'),
            func.sum(OrderItem.quantity).label('total_quantity'),
            func.sum(OrderItem.total_price).label('total_revenue')
        ).select_from(
            OrderItem.join(Order).join(MenuItem).join(MenuCategory)
        ).where(
            and_(*base_filters, Order.status != OrderStatus.CANCELLED.value)
        ).group_by(
            MenuItem.name, MenuCategory.menu_category_name
        ).order_by(desc('total_quantity')).limit(10)

        top_items_result = await session.execute(top_items_query)
        top_items = [
            {
                'name': row.name,
                'category': row.category,
                'quantity_sold': row.total_quantity,
                'revenue': float(row.total_revenue)
            }
            for row in top_items_result.all()
        ]

        return {
            'time_period_days': time_period,
            'is_user_specific': user_id is not None,
            'overview': {
                'total_orders': overview.total_orders or 0,
                'total_revenue': float(overview.total_revenue) if overview.total_revenue else 0,
                'avg_order_value': float(overview.avg_order_value) if overview.avg_order_value else 0,
                'unique_customers': overview.unique_customers or 0
            },
            'status_distribution': status_distribution,
            'order_type_distribution': type_distribution,
            'top_selling_items': top_items
        }

    async def _analyze_cart_abandonment(self, session, time_period: int, user_id: Optional[str]):
        """Analyze cart abandonment patterns"""

        cutoff_date = datetime.now() - timedelta(days=time_period)

        # Base query filters
        base_filters = [Order.created_at >= cutoff_date]
        if user_id:
            base_filters.append(Order.user_id == user_id)

        # Get abandoned carts (orders that stayed in pending too long)
        abandonment_threshold = datetime.now() - timedelta(hours=1)  # 1 hour threshold

        abandoned_query = select(
            func.count(Order.id).label('abandoned_count'),
            func.avg(Order.total_amount).label('avg_abandoned_value')
        ).where(
            and_(
                *base_filters,
                Order.status == OrderStatus.PENDING.value,
                Order.created_at < abandonment_threshold
            )
        )

        abandoned_result = await session.execute(abandoned_query)
        abandoned_stats = abandoned_result.first()

        # Get completed orders for comparison
        completed_query = select(
            func.count(Order.id).label('completed_count'),
            func.avg(Order.total_amount).label('avg_completed_value')
        ).where(
            and_(
                *base_filters,
                Order.status.in_([
                    OrderStatus.CONFIRMED.value,
                    OrderStatus.PREPARING.value,
                    OrderStatus.READY.value,
                    OrderStatus.DELIVERED.value
                ])
            )
        )

        completed_result = await session.execute(completed_query)
        completed_stats = completed_result.first()

        # Calculate abandonment rate
        total_carts = (abandoned_stats.abandoned_count or 0) + (completed_stats.completed_count or 0)
        abandonment_rate = (abandoned_stats.abandoned_count or 0) / total_carts if total_carts > 0 else 0

        # Analyze abandonment by cart value ranges
        value_ranges = [
            (0, 200, 'Low (₹0-200)'),
            (200, 500, 'Medium (₹200-500)'),
            (500, 1000, 'High (₹500-1000)'),
            (1000, float('in'), 'Premium (₹1000+)')
        ]

        abandonment_by_value = []
        for min_val, max_val, label in value_ranges:
            range_query = select(
                func.count(Order.id).label('count')
            ).where(
                and_(
                    *base_filters,
                    Order.status == OrderStatus.PENDING.value,
                    Order.created_at < abandonment_threshold,
                    Order.total_amount >= min_val,
                    *([] if max_val == float('inf') else [Order.total_amount < max_val])
                )
            )

            range_result = await session.execute(range_query)
            count = range_result.scalar()

            abandonment_by_value.append({
                'range': label,
                'abandoned_count': count or 0
            })

        # Get most abandoned items (items in abandoned carts)
        abandoned_items_query = select(
            MenuItem.name,
            func.count(OrderItem.id).label('abandonment_count'),
            func.avg(OrderItem.unit_price).label('avg_price')
        ).select_from(
            OrderItem.join(Order).join(MenuItem)
        ).where(
            and_(
                *base_filters,
                Order.status == OrderStatus.PENDING.value,
                Order.created_at < abandonment_threshold
            )
        ).group_by(MenuItem.name).order_by(desc('abandonment_count')).limit(10)

        abandoned_items_result = await session.execute(abandoned_items_query)
        most_abandoned_items = [
            {
                'item_name': row.name,
                'abandonment_count': row.abandonment_count,
                'avg_price': float(row.avg_price)
            }
            for row in abandoned_items_result.all()
        ]

        return {
            'time_period_days': time_period,
            'abandonment_summary': {
                'total_abandoned_carts': abandoned_stats.abandoned_count or 0,
                'total_completed_orders': completed_stats.completed_count or 0,
                'abandonment_rate': round(abandonment_rate * 100, 2),
                'avg_abandoned_value': float(abandoned_stats.avg_abandoned_value) if abandoned_stats.avg_abandoned_value else 0,
                'avg_completed_value': float(completed_stats.avg_completed_value) if completed_stats.avg_completed_value else 0,
                'potential_lost_revenue': float(abandoned_stats.avg_abandoned_value or 0) * (abandoned_stats.abandoned_count or 0)
            },
            'abandonment_by_value_range': abandonment_by_value,
            'most_abandoned_items': most_abandoned_items,
            'recommendations': self._generate_abandonment_recommendations(abandonment_rate, abandoned_stats, most_abandoned_items)
        }

    def _generate_abandonment_recommendations(self, abandonment_rate: float, abandoned_stats, most_abandoned_items):
        """Generate recommendations to reduce cart abandonment"""
        recommendations = []

        if abandonment_rate > 0.3:  # 30% abandonment rate
            recommendations.append("High abandonment rate detected - consider implementing cart recovery notifications")

        if abandoned_stats.avg_abandoned_value and abandoned_stats.avg_abandoned_value > 300:
            recommendations.append("High-value carts are being abandoned - consider offering limited-time incentives")

        if most_abandoned_items and len(most_abandoned_items) > 0:
            top_abandoned = most_abandoned_items[0]
            recommendations.append(f"'{top_abandoned['item_name']}' has high abandonment - review pricing or availability")

        if not recommendations:
            recommendations.append("Cart abandonment rate is within acceptable range")

        return recommendations

    async def _analyze_upselling_performance(self, session, time_period: int, user_id: Optional[str]):
        """Analyze upselling success and patterns"""

        cutoff_date = datetime.now() - timedelta(days=time_period)

        # Base query filters
        base_filters = [Order.created_at >= cutoff_date]
        if user_id:
            base_filters.append(Order.user_id == user_id)

        # Analyze orders by item count (indicator of upselling success)
        upselling_query = select(
            func.count(OrderItem.id).label('item_count'),
            func.count(func.distinct(Order.id)).label('order_count'),
            func.avg(Order.total_amount).label('avg_order_value')
        ).select_from(
            OrderItem.join(Order)
        ).where(
            and_(*base_filters, Order.status != OrderStatus.CANCELLED.value)
        ).group_by(Order.id).subquery()

        # Categorize orders by item count
        single_item_orders = await session.execute(
            select(func.count()).select_from(upselling_query).where(upselling_query.c.item_count == 1)
        )

        multi_item_orders = await session.execute(
            select(func.count()).select_from(upselling_query).where(upselling_query.c.item_count > 1)
        )

        # Average order values by item count
        value_by_items_query = select(
            func.case(
                (upselling_query.c.item_count == 1, 'Single Item'),
                (upselling_query.c.item_count.between(2, 3), '2-3 Items'),
                (upselling_query.c.item_count.between(4, 6), '4-6 Items'),
                else_='7+ Items'
            ).label('item_range'),
            func.avg(upselling_query.c.avg_order_value).label('avg_value'),
            func.count().label('order_count')
        ).select_from(upselling_query).group_by('item_range')

        value_result = await session.execute(value_by_items_query)
        value_by_items = [
            {
                'item_range': row.item_range,
                'avg_order_value': float(row.avg_value) if row.avg_value else 0,
                'order_count': row.order_count
            }
            for row in value_result.all()
        ]

        # Most common item combinations (frequent pairs)
        combinations_query = select(
            MenuItem.name.label('item1'),
            func.count().label('combination_count')
        ).select_from(
            OrderItem.alias('oi1').join(OrderItem.alias('oi2'),
                and_(
                    OrderItem.alias('oi1').c.order_id == OrderItem.alias('oi2').c.order_id,
                    OrderItem.alias('oi1').c.id != OrderItem.alias('oi2').c.id
                )
            ).join(MenuItem, OrderItem.alias('oi1').c.menu_item_id == MenuItem.id).join(Order)
        ).where(
            and_(*base_filters, Order.status != OrderStatus.CANCELLED.value)
        ).group_by(MenuItem.name).order_by(desc('combination_count')).limit(10)

        # Note: This is a simplified version - a full implementation would need more complex pairing logic

        return {
            'time_period_days': time_period,
            'upselling_metrics': {
                'single_item_orders': single_item_orders.scalar() or 0,
                'multi_item_orders': multi_item_orders.scalar() or 0,
                'upselling_success_rate': round((multi_item_orders.scalar() or 0) / max(1, (single_item_orders.scalar() or 0) + (multi_item_orders.scalar() or 0)) * 100, 2)
            },
            'order_value_by_item_count': value_by_items,
            'recommendations': self._generate_upselling_recommendations(value_by_items)
        }

    def _generate_upselling_recommendations(self, value_by_items):
        """Generate upselling optimization recommendations"""
        recommendations = []

        # Find the highest value item range
        if value_by_items:
            highest_value_range = max(value_by_items, key=lambda x: x['avg_order_value'])
            recommendations.append(f"Orders with {highest_value_range['item_range']} have highest average value (₹{highest_value_range['avg_order_value']:.0f})")

        recommendations.append("Focus on converting single-item orders to multi-item orders")
        recommendations.append("Implement strategic item pairing suggestions")

        return recommendations

    async def _analyze_order_patterns(self, session, time_period: int, user_id: Optional[str]):
        """Analyze ordering patterns and trends"""

        cutoff_date = datetime.now() - timedelta(days=time_period)

        # Base query filters
        base_filters = [Order.created_at >= cutoff_date]
        if user_id:
            base_filters.append(Order.user_id == user_id)

        # Orders by hour of day
        hourly_pattern_query = select(
            func.extract('hour', Order.created_at).label('hour'),
            func.count(Order.id).label('order_count'),
            func.avg(Order.total_amount).label('avg_value')
        ).where(
            and_(*base_filters, Order.status != OrderStatus.CANCELLED.value)
        ).group_by('hour').order_by('hour')

        hourly_result = await session.execute(hourly_pattern_query)
        hourly_patterns = [
            {
                'hour': int(row.hour),
                'order_count': row.order_count,
                'avg_order_value': float(row.avg_value) if row.avg_value else 0
            }
            for row in hourly_result.all()
        ]

        # Orders by day of week
        daily_pattern_query = select(
            func.extract('dow', Order.created_at).label('day_of_week'),
            func.count(Order.id).label('order_count'),
            func.avg(Order.total_amount).label('avg_value')
        ).where(
            and_(*base_filters, Order.status != OrderStatus.CANCELLED.value)
        ).group_by('day_of_week').order_by('day_of_week')

        daily_result = await session.execute(daily_pattern_query)
        day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        daily_patterns = [
            {
                'day_of_week': day_names[int(row.day_of_week)],
                'order_count': row.order_count,
                'avg_order_value': float(row.avg_value) if row.avg_value else 0
            }
            for row in daily_result.all()
        ]

        # Popular customizations
        customizations_query = select(
            OrderItem.customizations,
            func.count(OrderItem.id).label('usage_count')
        ).select_from(
            OrderItem.join(Order)
        ).where(
            and_(
                *base_filters,
                Order.status != OrderStatus.CANCELLED.value,
                OrderItem.customizations.isnot(None)
            )
        ).group_by(OrderItem.customizations).order_by(desc('usage_count')).limit(10)

        customizations_result = await session.execute(customizations_query)
        popular_customizations = []

        for row in customizations_result.all():
            if row.customizations:
                for key, value in row.customizations.items():
                    popular_customizations.append({
                        'customization_type': key,
                        'customization_value': value,
                        'usage_count': row.usage_count
                    })

        return {
            'time_period_days': time_period,
            'temporal_patterns': {
                'hourly_distribution': hourly_patterns,
                'daily_distribution': daily_patterns,
                'peak_hour': max(hourly_patterns, key=lambda x: x['order_count'])['hour'] if hourly_patterns else None,
                'peak_day': max(daily_patterns, key=lambda x: x['order_count'])['day_of_week'] if daily_patterns else None
            },
            'customization_patterns': popular_customizations[:10],
            'insights': self._generate_pattern_insights(hourly_patterns, daily_patterns)
        }

    def _generate_pattern_insights(self, hourly_patterns, daily_patterns):
        """Generate insights from ordering patterns"""
        insights = []

        if hourly_patterns:
            peak_hour = max(hourly_patterns, key=lambda x: x['order_count'])
            insights.append(f"Peak ordering hour is {peak_hour['hour']}:00 with {peak_hour['order_count']} orders")

        if daily_patterns:
            peak_day = max(daily_patterns, key=lambda x: x['order_count'])
            insights.append(f"Busiest day is {peak_day['day_of_week']} with {peak_day['order_count']} orders")

        return insights

    async def _analyze_revenue_metrics(self, session, time_period: int, user_id: Optional[str]):
        """Analyze revenue metrics and trends"""

        cutoff_date = datetime.now() - timedelta(days=time_period)

        # Base query filters
        base_filters = [Order.created_at >= cutoff_date]
        if user_id:
            base_filters.append(Order.user_id == user_id)

        # Daily revenue trend
        daily_revenue_query = select(
            func.date(Order.created_at).label('date'),
            func.sum(Order.total_amount).label('daily_revenue'),
            func.count(Order.id).label('daily_orders'),
            func.avg(Order.total_amount).label('daily_avg_order')
        ).where(
            and_(*base_filters, Order.status != OrderStatus.CANCELLED.value)
        ).group_by('date').order_by('date')

        daily_result = await session.execute(daily_revenue_query)
        daily_revenue = [
            {
                'date': row.date.isoformat(),
                'revenue': float(row.daily_revenue),
                'orders': row.daily_orders,
                'avg_order_value': float(row.daily_avg_order)
            }
            for row in daily_result.all()
        ]

        # Revenue by order type
        revenue_by_type_query = select(
            Order.order_type,
            func.sum(Order.total_amount).label('total_revenue'),
            func.count(Order.id).label('order_count'),
            func.avg(Order.total_amount).label('avg_order_value')
        ).where(
            and_(*base_filters, Order.status != OrderStatus.CANCELLED.value)
        ).group_by(Order.order_type)

        type_result = await session.execute(revenue_by_type_query)
        revenue_by_type = [
            {
                'order_type': row.order_type,
                'total_revenue': float(row.total_revenue),
                'order_count': row.order_count,
                'avg_order_value': float(row.avg_order_value)
            }
            for row in type_result.all()
        ]

        # Top revenue generating items
        top_revenue_items_query = select(
            MenuItem.name,
            MenuCategory.menu_category_name.label('category'),
            func.sum(OrderItem.total_price).label('total_revenue'),
            func.sum(OrderItem.quantity).label('total_quantity'),
            func.avg(OrderItem.unit_price).label('avg_price')
        ).select_from(
            OrderItem.join(Order).join(MenuItem).join(MenuCategory)
        ).where(
            and_(*base_filters, Order.status != OrderStatus.CANCELLED.value)
        ).group_by(
            MenuItem.name, MenuCategory.menu_category_name
        ).order_by(desc('total_revenue')).limit(10)

        top_items_result = await session.execute(top_revenue_items_query)
        top_revenue_items = [
            {
                'item_name': row.name,
                'category': row.category,
                'total_revenue': float(row.total_revenue),
                'quantity_sold': row.total_quantity,
                'avg_price': float(row.avg_price)
            }
            for row in top_items_result.all()
        ]

        # Calculate growth rate (if we have enough data)
        growth_rate = None
        if len(daily_revenue) > 1:
            first_day_revenue = daily_revenue[0]['revenue']
            last_day_revenue = daily_revenue[-1]['revenue']
            if first_day_revenue > 0:
                growth_rate = ((last_day_revenue - first_day_revenue) / first_day_revenue) * 100

        return {
            'time_period_days': time_period,
            'revenue_summary': {
                'total_revenue': sum(day['revenue'] for day in daily_revenue),
                'total_orders': sum(day['orders'] for day in daily_revenue),
                'avg_daily_revenue': sum(day['revenue'] for day in daily_revenue) / len(daily_revenue) if daily_revenue else 0,
                'growth_rate_percent': round(growth_rate, 2) if growth_rate else None
            },
            'daily_revenue_trend': daily_revenue,
            'revenue_by_order_type': revenue_by_type,
            'top_revenue_items': top_revenue_items
        }

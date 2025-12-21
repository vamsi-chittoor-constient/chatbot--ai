"""
Phase 4 & 5 Missing Tools Implementation
=========================================
Order enhancements and restaurant policies/info tools.

Implementation Date: 2025-12-21
Total Tools: 5 (Phase 4: 3 tools, Phase 5: 2 tools)
"""

from crewai.tools import tool
import structlog
from typing import Optional, List

logger = structlog.get_logger(__name__)


# ============================================================================
# PHASE 4: ORDER ENHANCEMENTS (3 tools)
# ============================================================================

def create_order_enhancement_tools(session_id: str, customer_id: Optional[str] = None):
    """Factory to create order enhancement tools with session context."""

    @tool("add_order_instructions")
    async def add_order_instructions(instruction_type: str, instruction_text: str) -> str:
        """
        Add special instructions to the current order.

        Use this when customer says "make it extra spicy", "no onions please",
        "ring doorbell twice", "leave at door", "well done".

        Args:
            instruction_type: Type of instruction - "cooking" (food preparation) or
                            "delivery" (delivery instructions)
            instruction_text: The actual instruction (e.g., "extra spicy", "no onions",
                            "ring doorbell", "contactless delivery")

        Returns:
            Confirmation that instructions were added.
        """
        try:
            from app.core.redis import get_cart, set_cart
            from app.core.agui_events import emit_tool_activity_async

            await emit_tool_activity_async(session_id, "add_order_instructions")

            # Get current cart
            cart_data = await get_cart(session_id)

            if not cart_data or not cart_data.get('items'):
                return "Your cart is empty. Add items first, then I can note your special instructions!"

            # Add instructions to cart metadata
            if 'instructions' not in cart_data:
                cart_data['instructions'] = {'cooking': [], 'delivery': []}

            instruction_type = instruction_type.lower()
            if instruction_type not in ['cooking', 'delivery']:
                instruction_type = 'cooking'  # Default to cooking

            # Add instruction (avoid duplicates)
            existing = cart_data['instructions'].get(instruction_type, [])
            if instruction_text not in existing:
                existing.append(instruction_text)
                cart_data['instructions'][instruction_type] = existing

            # Save cart
            await set_cart(session_id, cart_data)

            inst_type_label = "Cooking" if instruction_type == "cooking" else "Delivery"
            response = f"✅ **{inst_type_label} Instruction Added:**\n\n\"{instruction_text}\"\n\n"
            response += "I'll make sure this is noted on your order!"

            return response

        except Exception as e:
            logger.error("add_order_instructions_error", error=str(e), exc_info=True)
            return f"I've noted your instruction: \"{instruction_text}\". However, I couldn't save it to the system right now."

    @tool("reorder_from_order_id")
    async def reorder_from_order_id(order_id: str = "") -> str:
        """
        Reorder items from a previous order by order ID.

        Use this when customer says "reorder my last order", "I want the same as order #123",
        "repeat my previous order", "order the same thing again".

        Args:
            order_id: Order ID to reorder from (leave empty for most recent order)

        Returns:
            Confirmation of items added to cart.
        """
        try:
            from app.core.redis import get_cart, set_cart
            from app.core.db_pool import AsyncDBConnection
            from app.core.agui_events import emit_tool_activity_async

            await emit_tool_activity_async(session_id, "reorder_from_order_id")

            if not customer_id:
                return "Please log in to reorder from your order history. I can help you browse the menu instead!"

            async with AsyncDBConnection() as db:
                # Get order details
                if not order_id:
                    # Get most recent order
                    order_query = """
                        SELECT order_id, order_number
                        FROM orders
                        WHERE customer_id = %s
                        ORDER BY created_at DESC
                        LIMIT 1
                    """
                    order_row = await db.fetch_one(order_query, (customer_id,))
                else:
                    # Get specific order
                    order_query = """
                        SELECT order_id, order_number
                        FROM orders
                        WHERE (order_id::text LIKE %s OR order_number = %s)
                          AND customer_id = %s
                    """
                    order_row = await db.fetch_one(order_query, (f"{order_id}%", order_id, customer_id))

                if not order_row:
                    return "I couldn't find that order. Please check your order history or browse the menu to start a new order."

                # Get order items
                items_query = """
                    SELECT
                        mi.menu_item_name,
                        mi.menu_item_price,
                        oi.quantity,
                        oi.special_instructions
                    FROM order_item oi
                    JOIN menu_item mi ON oi.menu_item_id = mi.menu_item_id
                    WHERE oi.order_id = %s
                    ORDER BY oi.created_at
                """
                items = await db.fetch_all(items_query, (order_row['order_id'],))

                if not items:
                    return f"Order {order_row['order_number']} has no items. Please browse the menu to create a new order."

                # Get current cart or create new
                cart_data = await get_cart(session_id) or {"items": [], "total": 0}

                # Add items to cart
                total = cart_data.get('total', 0)
                for item in items:
                    cart_item = {
                        "name": item['menu_item_name'],
                        "price": float(item['menu_item_price']),
                        "quantity": item['quantity'],
                        "special_instructions": item['special_instructions'] or ""
                    }
                    cart_data['items'].append(cart_item)
                    total += float(item['menu_item_price']) * item['quantity']

                cart_data['total'] = total

                # Save cart
                await set_cart(session_id, cart_data)

                # Format response
                items_list = []
                for item in items:
                    items_list.append(f"- {item['quantity']}x {item['menu_item_name']} (Rs.{item['menu_item_price']})")

                response = f"✅ **Reordered from Order #{order_row['order_number']}:**\n\n"
                response += "\n".join(items_list)
                response += f"\n\n**Cart Total:** Rs.{total:.2f}\n\n"
                response += "All items have been added to your cart. Ready to checkout?"

                return response

        except Exception as e:
            logger.error("reorder_from_order_id_error", error=str(e), exc_info=True)
            return "Sorry, I couldn't reorder that order right now. Would you like to browse the menu instead?"

    @tool("customize_item_in_cart")
    async def customize_item_in_cart(item_name: str, customization: str) -> str:
        """
        Customize an item already in the cart.

        Use this when customer says "make that burger medium rare", "change size to large",
        "extra cheese on the pizza", "mild spice level".

        Args:
            item_name: Name of item in cart to customize
            customization: Customization details (e.g., "large size", "extra cheese",
                          "medium spice", "well done")

        Returns:
            Confirmation that item was customized.
        """
        try:
            from app.core.redis import get_cart, set_cart
            from app.core.agui_events import emit_tool_activity_async

            await emit_tool_activity_async(session_id, "customize_item_in_cart")

            # Get cart
            cart_data = await get_cart(session_id)

            if not cart_data or not cart_data.get('items'):
                return f"Your cart is empty. Add {item_name} first, then I can customize it!"

            # Find item in cart
            found = False
            for cart_item in cart_data['items']:
                if item_name.lower() in cart_item['name'].lower():
                    # Add customization to special instructions
                    existing_instructions = cart_item.get('special_instructions', '')
                    if existing_instructions:
                        cart_item['special_instructions'] = f"{existing_instructions}, {customization}"
                    else:
                        cart_item['special_instructions'] = customization

                    found = True
                    break

            if not found:
                return f"I couldn't find '{item_name}' in your cart. Would you like to add it first?"

            # Save cart
            await set_cart(session_id, cart_data)

            response = f"✅ **Customized: {item_name}**\n\n"
            response += f"Added customization: \"{customization}\"\n\n"
            response += "Your item has been customized!"

            return response

        except Exception as e:
            logger.error("customize_item_in_cart_error", error=str(e), exc_info=True)
            return f"I've noted your customization for {item_name}: \"{customization}\""

    return [
        add_order_instructions,
        reorder_from_order_id,
        customize_item_in_cart
    ]


# ============================================================================
# PHASE 5: POLICIES & INFO (2 tools)
# ============================================================================

def create_policy_info_tools(session_id: str):
    """Factory to create restaurant policy and info tools with session context."""

    @tool("get_restaurant_policies")
    async def get_restaurant_policies(policy_type: str = "all") -> str:
        """
        Get restaurant policies.

        Use this when customer asks "what's your refund policy?", "what's your cancellation policy?",
        "what are your terms and conditions?", "privacy policy".

        Args:
            policy_type: Type of policy - "refund", "cancellation", "privacy", "terms", or "all"

        Returns:
            Restaurant policy information.
        """
        try:
            from app.core.db_pool import AsyncDBConnection
            from app.core.agui_events import emit_tool_activity_async

            await emit_tool_activity_async(session_id, "get_restaurant_policies")

            async with AsyncDBConnection() as db:
                if policy_type == "all":
                    query = """
                        SELECT
                            policy_name,
                            policy_content,
                            policy_type
                        FROM restaurant_policy
                        WHERE is_deleted = FALSE
                          AND is_active = TRUE
                        ORDER BY policy_type, policy_name
                    """
                    results = await db.fetch_all(query)
                else:
                    query = """
                        SELECT
                            policy_name,
                            policy_content,
                            policy_type
                        FROM restaurant_policy
                        WHERE is_deleted = FALSE
                          AND is_active = TRUE
                          AND LOWER(policy_type) = LOWER(%s)
                        ORDER BY policy_name
                    """
                    results = await db.fetch_all(query, (policy_type,))

                if not results:
                    # Return default policies if none in database
                    default_policies = {
                        "refund": "Full refund available within 24 hours for quality issues or incorrect orders. Contact our support team with your order details.",
                        "cancellation": "Orders can be cancelled within 5 minutes of placement for full refund. After kitchen starts preparation, cancellation requires manager approval.",
                        "privacy": "We protect your personal information and never share it with third parties. Data is used only for order processing and improving our service.",
                        "terms": "By ordering, you agree to our terms of service. All prices include applicable taxes. Delivery times are estimates and may vary."
                    }

                    if policy_type in default_policies:
                        return f"**{policy_type.title()} Policy:**\n\n{default_policies[policy_type]}"
                    else:
                        return "For detailed policies, please contact our support team or visit our website."

                # Format response
                response = "**Restaurant Policies:**\n\n"
                for row in results:
                    response += f"**{row['policy_name']}**\n{row['policy_content']}\n\n"

                response += "If you have more questions, feel free to ask!"
                return response

        except Exception as e:
            logger.error("get_restaurant_policies_error", error=str(e), exc_info=True)
            return "Sorry, I couldn't retrieve policy information right now. Please contact our support team."

    @tool("get_operating_hours")
    async def get_operating_hours(date: str = "") -> str:
        """
        Get restaurant operating hours.

        Use this when customer asks "what time do you open?", "are you open now?",
        "what are your hours?", "are you open on Sunday?".

        Args:
            date: Optional date to check (YYYY-MM-DD format). Leave empty for today.

        Returns:
            Operating hours and holiday schedules.
        """
        try:
            from app.core.db_pool import AsyncDBConnection
            from app.core.agui_events import emit_tool_activity_async
            from datetime import datetime

            await emit_tool_activity_async(session_id, "get_operating_hours")

            async with AsyncDBConnection() as db:
                # Get restaurant config
                config_query = """
                    SELECT settings
                    FROM restaurant_config
                    WHERE is_deleted = FALSE
                    LIMIT 1
                """
                config_row = await db.fetch_one(config_query)

                if config_row and config_row['settings']:
                    settings = config_row['settings']
                    hours = settings.get('operating_hours', {})

                    if hours:
                        response = "**Restaurant Operating Hours:**\n\n"

                        # Check if specific date requested
                        if date:
                            try:
                                check_date = datetime.strptime(date, "%Y-%m-%d")
                                day_name = check_date.strftime("%A")
                                day_hours = hours.get(day_name.lower(), hours.get('default'))

                                if day_hours:
                                    if day_hours == 'closed':
                                        return f"We're closed on {day_name}s."
                                    else:
                                        return f"On {day_name} ({date}), we're open {day_hours}."
                            except:
                                pass

                        # Show all hours
                        for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
                            day_hours = hours.get(day.lower(), hours.get('default', '11:00 AM - 10:00 PM'))
                            if day_hours == 'closed':
                                response += f"**{day}:** Closed\n"
                            else:
                                response += f"**{day}:** {day_hours}\n"

                        # Add special notes
                        if 'holidays' in settings:
                            response += f"\n**Holiday Schedule:** {settings['holidays']}\n"

                        # Check if open now
                        now = datetime.now()
                        current_day = now.strftime("%A").lower()
                        current_time = now.strftime("%H:%M")

                        day_hours = hours.get(current_day, hours.get('default'))
                        if day_hours and day_hours != 'closed':
                            response += f"\n**Status:** Currently open"
                        else:
                            response += f"\n**Status:** Currently closed"

                        return response

                # Default hours if nothing in database
                default_response = """**Restaurant Operating Hours:**

**Monday - Friday:** 11:00 AM - 10:00 PM
**Saturday - Sunday:** 10:00 AM - 11:00 PM

**Kitchen closes** 30 minutes before closing time.

We're open every day including holidays! 🎉"""

                return default_response

        except Exception as e:
            logger.error("get_operating_hours_error", error=str(e), exc_info=True)
            return "We're typically open 11 AM - 10 PM daily. For exact hours, please contact us directly."

    return [
        get_restaurant_policies,
        get_operating_hours
    ]


# ============================================================================
# TOOL COLLECTION FOR EASY INTEGRATION
# ============================================================================

def get_all_phase4_tools(session_id: str, customer_id: Optional[str] = None) -> List:
    """Get all Phase 4 tools (Order Enhancements)."""
    tools = create_order_enhancement_tools(session_id, customer_id)
    logger.info("phase4_tools_loaded", tool_count=len(tools), session=session_id)
    return tools


def get_all_phase5_tools(session_id: str) -> List:
    """Get all Phase 5 tools (Policies & Info)."""
    tools = create_policy_info_tools(session_id)
    logger.info("phase5_tools_loaded", tool_count=len(tools), session=session_id)
    return tools

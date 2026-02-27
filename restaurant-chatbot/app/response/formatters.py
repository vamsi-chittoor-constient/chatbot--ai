"""
Response Formatters
===================
Helper functions to format ActionResult data into prompts for the virtual waiter LLM.
"""

from typing import Dict, Any, List
from app.response.models import ActionResult, ConversationContext


def format_booking_details(data: Dict[str, Any]) -> str:
    """Format booking data for prompt"""
    parts = []

    if data.get("party_size"):
        parts.append(f"- Party size: {data['party_size']} guests")

    if data.get("date"):
        parts.append(f"- Date: {data['date']}")

    if data.get("time"):
        parts.append(f"- Time: {data['time']}")

    if data.get("table_number"):
        parts.append(f"- Table: {data['table_number']}")

    if data.get("booking_id"):
        parts.append(f"- Booking ID: {data['booking_id']}")

    if data.get("special_requests"):
        parts.append(f"- Special requests: {data['special_requests']}")

    return "\n".join(parts) if parts else "Booking confirmed"


def format_order_items(items: List[Dict[str, Any]]) -> str:
    """Format order items for prompt"""
    if not items:
        return "No items"

    formatted = []
    for item in items:
        name = item.get("item_name", item.get("name", "Unknown"))
        qty = item.get("quantity", 1)
        price = item.get("price", item.get("unit_price", 0))

        formatted.append(f"- {qty}x {name} (₹{price})")

    return "\n".join(formatted)


def format_menu_items(items: List[Dict[str, Any]], limit: int = None) -> str:
    """
    Format menu items for customer display (name + price only)

    Descriptions are NOT shown - they're used internally for:
    - Semantic search
    - AI recommendations
    - Upselling suggestions

    Args:
        items: List of menu items to format
        limit: Maximum number of items to show. None = show all items
    """
    if not items:
        return "No items available"

    # Determine how many items to show
    items_to_show = items if limit is None else items[:limit]

    formatted = []
    for idx, item in enumerate(items_to_show, 1):
        name = item.get("name", "Unknown")
        price = item.get("price", 0)

        # Only show name and price (descriptions are for backend use only)
        item_text = f"{idx}. {name} (₹{price})"
        formatted.append(item_text)

    # Only show "... and X more" if we limited the display
    if limit is not None and len(items) > limit:
        formatted.append(f"... and {len(items) - limit} more items")

    return "\n".join(formatted)


def format_cart_summary(data: Dict[str, Any]) -> str:
    """Format cart/order summary"""
    parts = []

    items = data.get("items", [])
    if items:
        parts.append("Items:")
        parts.append(format_order_items(items))

    if data.get("subtotal"):
        parts.append(f"\nSubtotal: ₹{data['subtotal']}")

    if data.get("tax_amount"):
        parts.append(f"Tax: ₹{data['tax_amount']}")

    if data.get("total_amount"):
        parts.append(f"Total: ₹{data['total_amount']}")

    return "\n".join(parts) if parts else "Cart is empty"


def format_error_details(error: str, data: Dict[str, Any]) -> str:
    """Format error information for friendly error messages"""
    parts = [f"Error: {error}"]

    # Add context if available
    if data.get("item_name"):
        parts.append(f"Item: {data['item_name']}")

    if data.get("reason"):
        parts.append(f"Reason: {data['reason']}")

    if data.get("alternatives"):
        parts.append("\nSuggested alternatives:")
        for alt in data["alternatives"]:
            parts.append(f"- {alt}")

    return "\n".join(parts)


def format_action_details(action_result: ActionResult) -> str:
    """
    Format ActionResult data into a readable string for LLM prompt.

    Args:
        action_result: The structured action result from specialist agent

    Returns:
        Formatted details string for inclusion in prompt
    """
    action_type = action_result.action
    data = action_result.data
    error = action_result.error

    # Handle errors
    if not action_result.success and error:
        return format_error_details(error, data)

    # Handle successful actions based on type
    if "booking" in action_type:
        return format_booking_details(data)

    elif action_type in ["item_added", "item_removed", "cart_updated"]:
        details = []

        if data.get("item_name"):
            details.append(f"Item: {data['item_name']}")

        if data.get("quantity"):
            details.append(f"Quantity: {data['quantity']}")

        if data.get("price") or data.get("item_price"):
            price = data.get("price") or data.get("item_price")
            details.append(f"Price: ₹{price}")

        if data.get("cart_subtotal"):
            details.append(f"Cart total: ₹{data['cart_subtotal']}")

        return "\n".join(details) if details else "Item updated"

    elif action_type == "menu_displayed":
        # Full menu structure (organized by categories)
        menu = data.get("menu", [])

        if menu and isinstance(menu, list) and len(menu) > 0:
            # Check if it's hierarchical menu (categories with items)
            if isinstance(menu[0], dict) and "items" in menu[0]:
                # Format as organized menu by category
                result_lines = []

                meal_time = data.get("meal_time_display_name", data.get("current_meal_time", ""))
                if meal_time:
                    result_lines.append(f"{meal_time.upper()} MENU")
                    result_lines.append("")

                for category in menu:
                    category_name = category.get("category_name", "Unknown Category")
                    items = category.get("items", [])

                    if items:  # Only show categories that have items
                        result_lines.append(f"{category_name.upper()}")
                        result_lines.append("")

                        for idx, item in enumerate(items[:10], 1):  # Limit to 10 items per category
                            name = item.get("name", "Unknown")
                            price = item.get("price", 0)
                            result_lines.append(f"{idx}. {name} - Rs {price}")

                        if len(items) > 10:
                            result_lines.append(f"   ...and {len(items) - 10} more items")

                        result_lines.append("")  # Blank line between categories

                return "\n".join(result_lines)
            else:
                # Simple flat list of items
                return format_menu_items(menu, limit=10)

        return "No items available"

    elif action_type == "search_results":
        # Semantic search results from menu discovery agent
        items = data.get("items", [])

        if items:
            search_query = data.get("search_query", "your search")
            total_found = data.get("total_found", len(items))

            # Build conversational but structured list
            result_lines = []

            # Conversational intro
            result_lines.append(f"We've got {total_found} great options for you:")
            result_lines.append("")

            # Show all items found (name + price only, clean list)
            for idx, item in enumerate(items, 1):
                name = item.get("name", "Unknown")
                price = item.get("price", 0)
                result_lines.append(f"{idx}. {name} - Rs {price}")

            result_lines.append("")

            # Natural waiter closing with suggestions hint
            result_lines.append("What sounds good to you? Or I can recommend some of our popular ones if you'd like!")

            return "\n".join(result_lines)

        return "No items found matching your search"

    elif action_type == "recommendations":
        # Personalized recommendations from menu discovery agent
        recommendations = data.get("recommendations", [])

        if recommendations:
            total_found = data.get("total_found", len(recommendations))
            result_text = f"Based on what I know, here are {total_found} great recommendations:\n\n"
            result_text += format_menu_items(recommendations, limit=10)
            return result_text

        return "I don't have enough information to make recommendations yet. What kind of food do you like?"

    elif action_type == "categories_listed":
        # Category list from menu browsing agent
        # Return STRUCTURED data for clean display (not conversational)
        categories = data.get("categories", [])

        if categories:
            # Build clean, structured list
            result_lines = ["MENU CATEGORIES", ""]

            for idx, category in enumerate(categories, 1):
                if isinstance(category, dict):
                    cat_name = category.get("name", "Unknown")
                    item_count = category.get("item_count", 0)
                    cat_desc = category.get("description", "")

                    result_lines.append(f"{idx}. {cat_name.upper()}")
                    if cat_desc:
                        result_lines.append(f"   {cat_desc}")
                    result_lines.append(f"   ({item_count} items available)")
                    result_lines.append("")  # Blank line between categories
                else:
                    result_lines.append(f"{idx}. {category}")
                    result_lines.append("")

            result_lines.append("Which category would you like to explore?")
            return "\n".join(result_lines)

        return "No categories available"

    elif action_type == "category_browsed":
        # Category browsing results from menu browsing agent
        items = data.get("items", [])

        if items:
            category_name = data.get("category_name", "this category")
            total_count = data.get("total_count", len(items))

            result_text = f"Here are our {category_name} items ({total_count} available):\n\n"
            # Show all items (name + price only, descriptions are for backend use)
            result_text += format_menu_items(items, limit=None)
            return result_text

        return "No items found in this category"

    elif action_type in ["order_placed", "checkout_initiated"]:
        return format_cart_summary(data)

    elif action_type == "payment_link_created":
        details = []

        if data.get("order_id"):
            details.append(f"Order ID: {data['order_id']}")

        if data.get("amount") or data.get("total_amount"):
            amount = data.get("amount") or data.get("total_amount")
            details.append(f"Amount: ₹{amount}")

        if data.get("payment_method"):
            details.append(f"Method: {data['payment_method']}")

        return "\n".join(details) if details else "Payment link created"

    elif "auth" in action_type or "otp" in action_type:
        details = []

        if data.get("phone_number") or data.get("user_phone"):
            phone = data.get("phone_number") or data.get("user_phone")
            # Mask phone number for privacy
            masked = phone[:2] + "****" + phone[-2:] if len(phone) > 4 else "****"
            details.append(f"Phone: {masked}")

        if data.get("user_name"):
            details.append(f"Name: {data['user_name']}")

        return "\n".join(details) if details else "Authentication step"

    # Generic fallback
    else:
        # Just show key-value pairs
        details = []
        for key, value in data.items():
            if isinstance(value, (str, int, float, bool)):
                details.append(f"{key}: {value}")

        return "\n".join(details) if details else "Action completed"


def should_upsell(action_result: ActionResult, context: ConversationContext) -> bool:
    """
    Determine if upselling is appropriate for this interaction.

    Contextual upselling rules:
    - High-value carts (> ₹500)
    - Special occasions
    - Certain item categories
    - NOT on every single interaction

    Args:
        action_result: The action that just happened
        context: Conversation context

    Returns:
        True if upselling should be attempted
    """
    from app.response.prompts import UPSELLING_RULES

    # Don't upsell on errors or auth flows
    if not action_result.success:
        return False

    if "auth" in action_result.action or "otp" in action_result.action:
        return False

    # Upsell on special occasions
    if context.special_occasion:
        return True

    # Upsell on high-value carts
    cart_value = context.cart_value or action_result.data.get("cart_subtotal", 0)
    if cart_value and cart_value > UPSELLING_RULES["cart_value_threshold"]:
        return True

    # Upsell on specific item additions (main courses, etc.)
    if action_result.action == "item_added":
        # Only upsell ~40% of the time for items to avoid being pushy
        import random
        return random.random() < 0.4

    # Don't upsell otherwise
    return False


def get_upsell_suggestions(action_result: ActionResult, context: ConversationContext) -> List[str]:
    """
    Generate contextual upsell suggestions.

    Args:
        action_result: The action that just happened
        context: Conversation context

    Returns:
        List of upsell suggestion strings
    """
    # If agent already provided suggestions, use those
    if action_result.suggestions:
        return action_result.suggestions

    suggestions = []

    # Special occasion upsells
    if context.special_occasion:
        suggestions.extend([
            "chef's special dessert",
            "complimentary wine pairing"
        ])

    # Item-specific upsells
    if action_result.action == "item_added":
        item_name = action_result.data.get("item_name", "").lower()

        # Suggest drinks with food
        if any(word in item_name for word in ["pizza", "pasta", "biryani", "curry"]):
            suggestions.append("refreshing drink or lassi")

        # Suggest sides with mains
        if any(word in item_name for word in ["chicken", "paneer", "dal"]):
            suggestions.append("garlic naan or rice")

    return suggestions[:2]  # Max 2 suggestions to avoid overwhelming

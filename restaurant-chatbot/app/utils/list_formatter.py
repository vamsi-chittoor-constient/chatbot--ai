"""
List and Menu Formatting Utility
=================================
Centralized formatting for consistent presentation of lists, menus, and options.

Provides standardized formatting for:
- Category listings
- Menu item listings
- Cart displays
- Order summaries
- Generic option lists
"""

from typing import List, Dict, Any, Optional, Literal
from decimal import Decimal


def format_price(amount: float | Decimal) -> str:
    """
    Format price with Indian Rupee symbol and 2 decimal places.

    Args:
        amount: Price amount (float or Decimal)

    Returns:
        Formatted price string (e.g., "₹350.00")
    """
    return f"₹{float(amount):.2f}"


def format_category_list(
    categories: List[Dict[str, Any]],
    include_item_count: bool = True,
    numbered: bool = True,
    plain_text: bool = True
) -> str:
    """
    Format a list of menu categories for display.

    Args:
        categories: List of category dicts with keys: name, description (optional), item_count
        include_item_count: Whether to show item count per category
        numbered: Whether to use numbered list (True) or bullet points (False)
        plain_text: Whether to use plain text (True) or markdown with bold (False)

    Returns:
        Formatted string (plain text or markdown)

    Example (plain_text=True):
        1. Appetizers - Start your meal (12 items)
        2. Main Course - Traditional dishes (24 items)

    Example (plain_text=False):
        1. **Appetizers** - Start your meal (12 items)
        2. **Main Course** - Traditional dishes (24 items)
    """
    if not categories:
        return "No categories available."

    lines = []
    for idx, category in enumerate(categories, 1):
        name = category.get("name", "Unknown")
        description = category.get("description", "")
        item_count = category.get("item_count", 0)

        # Build line
        prefix = f"{idx}. " if numbered else "- "
        # Use plain text or markdown based on parameter
        name_formatted = name if plain_text else f"**{name}**"
        line = f"{prefix}{name_formatted}"

        if description:
            line += f" - {description}"

        if include_item_count and item_count is not None:
            line += f" ({item_count} items)" if item_count != 1 else f" ({item_count} item)"

        lines.append(line)

    return "\n".join(lines)


def format_menu_item_list(
    items: List[Dict[str, Any]],
    include_description: bool = False,
    include_price: bool = True,
    numbered: bool = True,
    max_description_length: Optional[int] = 100,
    plain_text: bool = True
) -> str:
    """
    Format a list of menu items for display.

    Args:
        items: List of item dicts with keys: name, description, price, dietary_info, spice_level, etc.
        include_description: Whether to show item descriptions (default False for cleaner display)
        include_price: Whether to show prices
        numbered: Whether to use numbered list (True) or bullet points (False)
        max_description_length: Maximum description length (truncate if longer)
        plain_text: Whether to use plain text (True) or markdown with bold (False)

    Returns:
        Formatted string (plain text or markdown)

    Example (plain_text=True, include_description=False):
        1. Butter Chicken (₹350)
        2. Paneer Tikka (₹300)

    Example (plain_text=False, include_description=True):
        1. **Butter Chicken** - Tender chicken in creamy sauce (₹350)
    """
    if not items:
        return "No items available."

    lines = []
    for idx, item in enumerate(items, 1):
        name = item.get("name", "Unknown Item")
        description = item.get("description", "")
        price = item.get("price")
        dietary_info = item.get("dietary_info", [])
        spice_level = item.get("spice_level")

        # Build line
        prefix = f"{idx}. " if numbered else "- "
        # Use plain text or markdown based on parameter
        name_formatted = name if plain_text else f"**{name}**"
        line = f"{prefix}{name_formatted}"

        # Add price (in parentheses for cleaner look)
        if include_price and price is not None:
            line += f" ({format_price(price)})"

        # Add description
        if include_description and description:
            if max_description_length and len(description) > max_description_length:
                description = description[:max_description_length].strip() + "..."
            line += f" - {description}"

        # Add dietary badges (only if description included for cleaner display)
        if include_description:
            badges = []
            if dietary_info:
                if isinstance(dietary_info, list):
                    badges.extend([d.replace("_", " ").title() for d in dietary_info])
                else:
                    badges.append(dietary_info.replace("_", " ").title())

            if spice_level and spice_level != "none":
                spice_text = {"mild": "Mild", "medium": "Medium Spice", "hot": "Hot"}.get(spice_level, "")
                if spice_text:
                    badges.append(spice_text)

            if badges:
                line += f" [{', '.join(badges)}]"

        lines.append(line)

    return "\n".join(lines)


def format_cart_display(
    items: List[Dict[str, Any]],
    subtotal: float | Decimal,
    tax: Optional[float | Decimal] = None,
    discount: Optional[float | Decimal] = None,
    total: Optional[float | Decimal] = None,
    plain_text: bool = True
) -> str:
    """
    Format cart contents with pricing breakdown.

    Args:
        items: List of cart items with keys: name, quantity, price, item_total
        subtotal: Cart subtotal before tax/discount
        tax: Tax amount (optional)
        discount: Discount amount (optional)
        total: Final total (optional, calculated if not provided)
        plain_text: Whether to use plain text (True) or markdown with bold (False)

    Returns:
        Formatted string (plain text or markdown)

    Example (plain_text=True):
        Your Cart:

        1. 2x Butter Chicken - ₹700.00
        2. 1x Naan - ₹40.00

        Subtotal: ₹740.00
        Tax: ₹111.00
        Total: ₹851.00

    Example (plain_text=False):
        **Your Cart:**

        1. 2x **Butter Chicken** - ₹700.00
    """
    if not items:
        return "Your cart is empty."

    # Header
    header = "Your Cart:" if plain_text else "**Your Cart:**"
    lines = [header, ""]

    # Format items
    for idx, item in enumerate(items, 1):
        quantity = item.get("quantity", 1)
        name = item.get("name", "Unknown Item")
        item_total = item.get("item_total") or (item.get("price", 0) * quantity)

        # Use plain text or markdown
        name_formatted = name if plain_text else f"**{name}**"
        lines.append(f"{idx}. {quantity}x {name_formatted} - {format_price(item_total)}")

    lines.append("")  # Empty line before totals

    # Pricing breakdown
    subtotal_label = "Subtotal:" if plain_text else "**Subtotal:**"
    lines.append(f"{subtotal_label} {format_price(subtotal)}")

    if tax is not None and tax > 0:
        tax_label = "Tax:" if plain_text else "**Tax:**"
        lines.append(f"{tax_label} {format_price(tax)}")

    if discount is not None and discount > 0:
        discount_label = "Discount:" if plain_text else "**Discount:**"
        lines.append(f"{discount_label} -{format_price(discount)}")

    # Calculate total if not provided
    if total is None:
        total = float(subtotal)
        if tax:
            total += float(tax)
        if discount:
            total -= float(discount)

    lines.append(f"**Total:** {format_price(total)}")

    return "\n".join(lines)


def format_order_summary(
    order_number: str,
    order_type: str,
    items: List[Dict[str, Any]],
    subtotal: float | Decimal,
    tax: Optional[float | Decimal] = None,
    discount: Optional[float | Decimal] = None,
    total: Optional[float | Decimal] = None,
    status: Optional[str] = None,
    estimated_time: Optional[str] = None,
    plain_text: bool = True
) -> str:
    """
    Format order summary for confirmation/tracking.

    Args:
        order_number: Order number (e.g., "ORD-20251023-AB12")
        order_type: Order type ("dine_in" or "takeout")
        items: List of order items
        subtotal: Order subtotal
        tax: Tax amount
        discount: Discount amount
        total: Final total
        status: Order status (optional)
        estimated_time: Estimated preparation/delivery time (optional)
        plain_text: Whether to use plain text (True) or markdown with bold (False)

    Returns:
        Formatted string (plain text or markdown)

    Example (plain_text=True):
        Order #ORD-20251023-AB12
        Type: Dine-in
        Status: Confirmed

        Items:
        1. 2x Butter Chicken - ₹700.00
        2. 1x Naan - ₹40.00

        Subtotal: ₹740.00
        Tax: ₹111.00
        Total: ₹851.00

    Example (plain_text=False):
        **Order #ORD-20251023-AB12**
        Type: Dine-in

        **Items:**
        1. 2x Butter Chicken - ₹700.00
    """
    from app.utils.order_utils import format_order_type_for_display

    # Header
    order_header = f"Order #{order_number}" if plain_text else f"**Order #{order_number}**"
    lines = [order_header]
    lines.append(f"Type: {format_order_type_for_display(order_type)}")

    if status:
        lines.append(f"Status: {status.replace('_', ' ').title()}")

    if estimated_time:
        lines.append(f"Estimated Time: {estimated_time}")

    lines.append("")  # Empty line

    # Items
    items_label = "Items:" if plain_text else "**Items:**"
    lines.append(items_label)
    for idx, item in enumerate(items, 1):
        quantity = item.get("quantity", 1)
        name = item.get("name", "Unknown Item")
        item_total = item.get("item_total") or (item.get("price", 0) * quantity)

        lines.append(f"{idx}. {quantity}x {name} - {format_price(item_total)}")

    lines.append("")  # Empty line

    # Pricing
    subtotal_label = "Subtotal:" if plain_text else "**Subtotal:**"
    lines.append(f"{subtotal_label} {format_price(subtotal)}")

    if tax is not None and tax > 0:
        tax_label = "Tax:" if plain_text else "**Tax:**"
        lines.append(f"{tax_label} {format_price(tax)}")

    if discount is not None and discount > 0:
        discount_label = "Discount:" if plain_text else "**Discount:**"
        lines.append(f"{discount_label} -{format_price(discount)}")

    if total is None:
        total = float(subtotal)
        if tax:
            total += float(tax)
        if discount:
            total -= float(discount)

    total_label = "Total:" if plain_text else "**Total:**"
    lines.append(f"{total_label} {format_price(total)}")

    return "\n".join(lines)


def format_option_list(
    options: List[str] | List[Dict[str, str]],
    header: Optional[str] = None,
    numbered: bool = True,
    include_descriptions: bool = True
) -> str:
    """
    Format a generic list of options for user selection.

    Args:
        options: List of strings or dicts with 'label' and 'description' keys
        header: Optional header text
        numbered: Whether to use numbered list (True) or bullet points (False)
        include_descriptions: Whether to show descriptions (if available)

    Returns:
        Formatted markdown string

    Example:
        Choose an option:

        1. Dine-in - Eat at the restaurant
        2. Takeout - Pick up your order
    """
    if not options:
        return "No options available."

    lines = []

    if header:
        lines.append(header)
        lines.append("")

    for idx, option in enumerate(options, 1):
        prefix = f"{idx}. " if numbered else "- "

        if isinstance(option, dict):
            label = option.get("label", "Unknown")
            description = option.get("description", "")

            line = f"{prefix}**{label}**"
            if include_descriptions and description:
                line += f" - {description}"

            lines.append(line)
        else:
            lines.append(f"{prefix}{option}")

    return "\n".join(lines)


def format_simple_list(
    items: List[str],
    numbered: bool = False
) -> str:
    """
    Format a simple list of strings.

    Args:
        items: List of string items
        numbered: Whether to use numbered list (True) or bullet points (False)

    Returns:
        Formatted string
    """
    if not items:
        return ""

    if numbered:
        return "\n".join([f"{idx}. {item}" for idx, item in enumerate(items, 1)])
    else:
        return "\n".join([f"- {item}" for item in items])


def format_introduction_with_options(
    intro_text: str,
    options: List[Dict[str, Any]] | List[str],
    closing_text: Optional[str] = None,
    format_type: Literal["categories", "items", "generic"] = "generic"
) -> str:
    """
    Format a complete message with introduction, options, and closing.

    Args:
        intro_text: Introduction text before the list
        options: List of options to display
        closing_text: Optional closing text after the list
        format_type: Type of formatting to use ("categories", "items", "generic")

    Returns:
        Complete formatted message
    """
    lines = [intro_text, ""]

    if format_type == "categories":
        lines.append(format_category_list(options))
    elif format_type == "items":
        lines.append(format_menu_item_list(options))
    else:
        lines.append(format_option_list(options))

    if closing_text:
        lines.append("")
        lines.append(closing_text)

    return "\n".join(lines)


__all__ = [
    "format_price",
    "format_category_list",
    "format_menu_item_list",
    "format_cart_display",
    "format_order_summary",
    "format_option_list",
    "format_simple_list",
    "format_introduction_with_options"
]

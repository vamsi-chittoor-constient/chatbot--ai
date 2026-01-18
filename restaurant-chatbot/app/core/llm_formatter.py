"""
LLM Formatter - Cheap Model for Natural Language Output
========================================================
Uses gpt-4o-mini (15x cheaper than GPT-4) to add personality to tool responses.

Cost: ~$0.00002 per call (vs $0.002 for GPT-4)
Speed: ~200ms
Quality: Natural, conversational, warm

This is used by event-sourced tools to format SQL query results
into human-friendly responses without expensive LLM calls.
"""
from typing import Dict, Any, Optional
import json
import os
from openai import OpenAI
import structlog

logger = structlog.get_logger(__name__)

# Singleton OpenAI client
_client: Optional[OpenAI] = None


def get_openai_client() -> OpenAI:
    """Get or create OpenAI client singleton."""
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set")
        _client = OpenAI(api_key=api_key)
    return _client


def format_with_personality(
    data: Dict[str, Any],
    context: str,
    fallback: str,
    use_emojis: bool = False
) -> str:
    """
    Format structured data into natural, conversational response.

    Args:
        data: Structured data from SQL query (dict with items, totals, etc)
        context: What the user asked for ("view cart", "search menu", etc)
        fallback: Fallback message if LLM call fails
        use_emojis: Whether to include emojis (default: False for professional tone)

    Returns:
        Natural language response formatted by gpt-4o-mini

    Cost: ~$0.00002 per call (150 tokens @ gpt-4o-mini pricing)
    """
    try:
        client = get_openai_client()

        emoji_instruction = "Use emojis sparingly for warmth." if use_emojis else "Do not use emojis."

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"""You're Kavya, a warm and helpful restaurant assistant.

Your job: Format the provided data into a natural, conversational response.

Style guidelines:
- Be warm, friendly, and concise
- Use natural language (not robotic)
- Keep it brief (1-2 sentences max)
- Sound helpful and enthusiastic
- {emoji_instruction}
- End with a helpful question or call-to-action

Examples:
- "Your cart has 2 pizzas and a coke. That's ₹650 total. Ready to checkout?"
- "I found 3 delicious pizzas on our menu! Which one would you like?"
- "Perfect! I've added 2 Margherita pizzas to your cart. Anything else?"
"""
                },
                {
                    "role": "user",
                    "content": f"""Context: {context}

Data:
{json.dumps(data, indent=2)}

Format this data into a warm, natural response."""
                }
            ],
            max_tokens=150,  # Keep responses concise
            temperature=0.7,  # Some creativity, not too much
        )

        formatted = response.choices[0].message.content.strip()

        logger.info(
            "llm_format_success",
            context=context,
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
            cost_usd=response.usage.total_tokens * 0.00000015  # gpt-4o-mini pricing
        )

        return formatted

    except Exception as e:
        logger.error("llm_format_failed", error=str(e), context=context)
        # Graceful fallback - return template-based message
        return fallback


def format_cart_view(cart_data: Dict[str, Any]) -> str:
    """
    Format cart data into natural language.

    Args:
        cart_data: {items: [...], total: 650, item_count: 3}

    Returns:
        Natural response like "You've got 2 pizzas and a coke! ₹650 total."
    """
    if not cart_data.get('items'):
        return format_with_personality(
            {"status": "empty"},
            "User viewing empty cart",
            "Your cart is empty. Browse our menu to get started!"
        )

    # Fallback template (if LLM fails)
    items_str = ", ".join([
        f"{item['quantity']}x {item['item_name']}"
        for item in cart_data['items']
    ])
    fallback = f"Your cart: {items_str}. Total: ₹{cart_data['total']:.2f}. Ready to checkout?"

    return format_with_personality(
        cart_data,
        "User viewing cart contents",
        fallback
    )


def format_item_added(item_name: str, quantity: int, cart_total: float, item_count: int) -> str:
    """
    Format "item added to cart" confirmation.

    Returns:
        Natural response like "Added 2 pizzas! You have 3 items now (₹650 total)."
    """
    fallback = f"Added {quantity}x {item_name} to your cart! Total: ₹{cart_total:.2f}"

    return format_with_personality(
        {
            "item_name": item_name,
            "quantity": quantity,
            "cart_total": cart_total,
            "item_count": item_count
        },
        "User added item to cart",
        fallback
    )


def format_menu_results(items: list, query: str = "", meal_period: str = "") -> str:
    """
    Format menu search results.

    Returns:
        Natural response like "I found 5 delicious pizzas! Which one would you like?"
    """
    if not items:
        fallback = f"No items found for '{query}'. Try a different search?"
        return format_with_personality(
            {"query": query, "count": 0},
            "No menu items found for search",
            fallback
        )

    # Create summary of items (first 3 as examples)
    item_names = [item['name'] for item in items[:3]]

    fallback = f"Found {len(items)} items. Browse the menu and let me know what you'd like!"

    return format_with_personality(
        {
            "count": len(items),
            "examples": item_names,
            "query": query,
            "meal_period": meal_period
        },
        "User searching menu",
        fallback
    )


def format_item_removed(item_name: str, remaining_items: int) -> str:
    """Format item removal confirmation."""
    fallback = f"Removed {item_name}. {remaining_items} items remaining."

    return format_with_personality(
        {"item_name": item_name, "remaining_items": remaining_items},
        "User removed item from cart",
        fallback
    )

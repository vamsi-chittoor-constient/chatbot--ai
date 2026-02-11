"""
Welcome Message Generator
=========================
Deterministic welcome message generation with time-based greetings and restaurant info.
"""

from datetime import datetime
from sqlalchemy import select
import structlog

logger = structlog.get_logger(__name__)


def get_ist_time() -> datetime:
    """
    Get current time in IST (India Standard Time).

    Returns:
        datetime: Current datetime in IST timezone
    """
    try:
        from app.utils.timezone import get_current_time
        return get_current_time()
    except Exception as e:
        logger.warning(f"Failed to get IST time, using system time: {e}")
        # Fallback to system time
        return datetime.now()


def get_time_based_greeting() -> str:
    """
    Get greeting based on current IST time.

    Returns:
        str: Time-appropriate greeting (Good morning/afternoon/evening/Hello)
    """
    current_time = get_ist_time()
    hour = current_time.hour

    if 5 <= hour < 12:
        return "Good morning"
    elif 12 <= hour < 17:
        return "Good afternoon"
    elif 17 <= hour < 21:
        return "Good evening"
    else:
        return "Hello"


async def get_restaurant_name() -> str:
    """
    Get restaurant name from database.

    Returns:
        str: Restaurant name from restaurant_config table, or fallback
    """
    try:
        from app.core.database import get_db_session
        from app.shared.models import Restaurant

        async with get_db_session() as session:
            # Query first restaurant from restaurant_config table
            result = await session.execute(
                select(Restaurant.name).limit(1)
            )
            restaurant_name = result.scalar_one_or_none()

            if restaurant_name:
                logger.debug("Retrieved restaurant name from database", name=restaurant_name)
                return restaurant_name

    except Exception as e:
        logger.warning(f"Failed to get restaurant name from database: {e}")

    # Fallback to default
    return "our restaurant"


def get_time_context() -> tuple[str, str, str]:
    """
    Get time-based context for personalized suggestions.

    Returns:
        tuple: (time_greeting, meal_suggestion, meal_period)
    """
    current_time = get_ist_time()
    hour = current_time.hour

    if 5 <= hour < 11:
        return "Good morning", "Perfect time for a hearty breakfast!", "Breakfast"
    elif 11 <= hour < 14:
        return "Good afternoon", "Looking for a delicious lunch?", "Lunch"
    elif 14 <= hour < 17:
        return "Good afternoon", "Time for a quick snack or coffee?", "All Day"
    elif 17 <= hour < 21:
        return "Good evening", "Ready for a wonderful dinner?", "Dinner"
    else:
        return "Hello", "Craving a late-night treat?", "All Day"


async def get_meal_suggestions(meal_period: str, limit: int = 3) -> list[dict]:
    """
    Get suggested menu items for the current meal period.

    Args:
        meal_period: 'Breakfast', 'Lunch', 'Dinner', or 'All Day'
        limit: Maximum number of suggestions

    Returns:
        List of suggested menu items
    """
    try:
        from app.core.preloader import get_menu_preloader
        preloader = get_menu_preloader()

        if preloader.is_loaded:
            return preloader.get_meal_suggestions(meal_period, limit)
    except Exception as e:
        logger.warning(f"Failed to get meal suggestions: {e}")

    return []


async def generate_welcome_message() -> str:
    """
    Generate the initial welcome message with time-based greeting, restaurant info,
    and meal-specific suggestions.

    This is deterministic and hardcoded as requested - only the initial welcome.
    The rest of the conversation flow remains AI-driven.

    Multi-tier identity system:
    - Users can browse anonymously or with device_id
    - Authentication only required for finalizing orders/bookings
    - No upfront mobile number request

    Returns:
        str: Formatted welcome message with meal suggestions
    """
    time_greeting, meal_context, meal_period = get_time_context()
    restaurant_name = await get_restaurant_name()

    # Get meal-specific suggestions
    suggestions = await get_meal_suggestions(meal_period, limit=3)

    # Build suggestion text
    suggestion_text = ""
    if suggestions:
        items = [f"**{s.get('name')}** (Rs.{s.get('price')})" for s in suggestions[:3]]
        if meal_period == "Breakfast":
            suggestion_text = f"\n\n🌅 **Popular for breakfast:** {', '.join(items)}"
        elif meal_period == "Lunch":
            suggestion_text = f"\n\n☀️ **Perfect for lunch:** {', '.join(items)}"
        elif meal_period == "Dinner":
            suggestion_text = f"\n\n🌙 **Tonight's favorites:** {', '.join(items)}"
        else:
            suggestion_text = f"\n\n⭐ **Popular right now:** {', '.join(items)}"

    # More conversational, warm welcome with time-aware context
    welcome_message = (
        f"{time_greeting}! Welcome to **{restaurant_name}**. "
        f"{meal_context}{suggestion_text}\n\n"
        "I'm your AI assistant and I can help you:\n"
        "- Browse our menu and get personalized recommendations\n"
        "- Place a takeaway order\n"
        "- Make a table reservation\n\n"
        "What would you like to do today?"
    )

    logger.info(
        "Generated welcome message",
        time_greeting=time_greeting,
        meal_context=meal_context,
        meal_period=meal_period,
        suggestions_count=len(suggestions),
        restaurant_name=restaurant_name
    )

    return welcome_message

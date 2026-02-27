"""
Time Utility Functions - Restaurant-Aware
==========================================
Helper functions for determining meal times based on restaurant-specific configuration.
Each restaurant can define their own meal periods dynamically.
"""

from datetime import datetime, time
from typing import Optional, List, Dict, Any
import structlog

logger = structlog.get_logger(__name__)


DEFAULT_MEAL_TIME_PERIODS = [
    {
        "id": "breakfast",
        "name": "Breakfast",
        "start_time": "00:00",  # Start at midnight to cover overnight hours
        "end_time": "11:00",
        "greeting": "Good morning"
    },
    {
        "id": "lunch",
        "name": "Lunch",
        "start_time": "11:00",
        "end_time": "16:00",
        "greeting": "Good afternoon"
    },
    {
        "id": "dinner",
        "name": "Dinner",
        "start_time": "16:00",  # Extended to cover evening hours (4 PM onwards)
        "end_time": "00:00",  # End at midnight to complete the 24-hour cycle
        "greeting": "Good evening"
    }
]


def parse_time_string(time_str: str) -> time:
    """
    Parse time string in HH:MM format to time object.

    Args:
        time_str: Time in "HH:MM" format (e.g., "14:30")

    Returns:
        datetime.time object
    """
    try:
        hour, minute = map(int, time_str.split(":"))
        return time(hour, minute)
    except Exception as e:
        logger.error(f"Failed to parse time string: {time_str}", error=str(e))
        # Default to midnight if parsing fails
        return time(0, 0)


async def get_restaurant_meal_time_config(restaurant_id: str) -> List[Dict[str, Any]]:
    """
    Fetch restaurant-specific meal time configuration from database.

    Args:
        restaurant_id: Restaurant identifier

    Returns:
        List of meal time period configurations
    """
    try:
        from app.core.database import get_db_session
        from app.shared.models import Restaurant
        from sqlalchemy import select

        async with get_db_session() as session:
            query = select(Restaurant).where(Restaurant.id == restaurant_id)
            result = await session.execute(query)
            restaurant = result.scalar_one_or_none()

            if restaurant and restaurant.settings:
                meal_periods = restaurant.settings.get("meal_time_periods")
                if meal_periods:
                    logger.debug(
                        "Loaded restaurant meal time config",
                        restaurant_id=restaurant_id,
                        periods=len(meal_periods)
                    )
                    return meal_periods

            logger.info(
                "No meal time config found, using defaults",
                restaurant_id=restaurant_id
            )
            return DEFAULT_MEAL_TIME_PERIODS

    except Exception as e:
        logger.error(
            "Failed to load restaurant meal time config, using defaults",
            restaurant_id=restaurant_id,
            error=str(e)
        )
        return DEFAULT_MEAL_TIME_PERIODS


def get_current_meal_time_sync(
    meal_periods: List[Dict[str, Any]],
    current_time: Optional[datetime] = None
) -> Optional[str]:
    """
    Determine the current meal time based on meal period configuration.

    This is a synchronous version that works with already-loaded config.

    Args:
        meal_periods: List of meal period configurations
        current_time: Optional datetime to check (defaults to now)

    Returns:
        Meal period ID (e.g., "breakfast", "lunch", "evening_snacks", "dinner")
        or None if no period matches
    """
    if current_time is None:
        current_time = datetime.now()

    current_time_only = current_time.time()

    for period in meal_periods:
        try:
            start_time = parse_time_string(period["start_time"])
            end_time = parse_time_string(period["end_time"])
            period_id = period["id"]

            # Handle periods that cross midnight (e.g., 23:00 - 06:00)
            if start_time < end_time:
                # Normal case: period within same day
                if start_time <= current_time_only < end_time:
                    return period_id
            else:
                # Crosses midnight
                if current_time_only >= start_time or current_time_only < end_time:
                    return period_id

        except Exception as e:
            logger.error(
                "Failed to process meal period",
                period=period,
                error=str(e)
            )
            continue

    # If no period matches, return last period as fallback (typically dinner)
    if meal_periods:
        return meal_periods[-1]["id"]

    return None


async def get_current_meal_time(restaurant_id: str) -> Optional[str]:
    """
    Determine the current meal time for a specific restaurant.

    Fetches restaurant-specific meal period configuration and determines
    which period the current time falls into.

    Args:
        restaurant_id: Restaurant identifier

    Returns:
        Meal period ID (e.g., "breakfast", "lunch", "evening_snacks", "dinner")
    """
    meal_periods = await get_restaurant_meal_time_config(restaurant_id)
    return get_current_meal_time_sync(meal_periods)


def is_item_available_for_time(
    item_availability_time: Optional[str],
    current_meal_time: Optional[str]
) -> bool:
    """
    Check if a menu item is available for the current meal time.

    Items are available if:
    - availability_time is None or empty (assumed always available)
    - availability_time is "all_day"
    - availability_time matches the current meal time
    - availability_time contains multiple values (comma-separated) that include current time

    Args:
        item_availability_time: The availability_time field from menu item
        current_meal_time: Current meal period ID (from get_current_meal_time)

    Returns:
        True if item is available, False otherwise
    """
    # If no availability_time set, item is always available
    if not item_availability_time or not item_availability_time.strip():
        return True

    # Normalize to lowercase for comparison
    item_availability_time = item_availability_time.lower().strip()

    # All-day items are always available (handle both "all_day" and "all day" formats)
    if item_availability_time in ("all_day", "all day"):
        return True

    # If no current meal time provided, assume available (fallback)
    if not current_meal_time:
        return True

    # Handle comma-separated availability times (e.g., "breakfast,lunch")
    available_times = [t.strip() for t in item_availability_time.split(",")]

    # If "all day" or "all_day" is in the list, item is always available
    if "all day" in available_times or "all_day" in available_times:
        return True

    return current_meal_time in available_times


def get_meal_time_display_info(
    meal_periods: List[Dict[str, Any]],
    meal_time_id: str
) -> Dict[str, str]:
    """
    Get display information for a meal time period.

    Args:
        meal_periods: List of meal period configurations
        meal_time_id: Meal period ID

    Returns:
        Dict with 'name' and 'greeting' keys
    """
    for period in meal_periods:
        if period["id"] == meal_time_id:
            return {
                "name": period.get("name", meal_time_id.replace("_", " ").title()),
                "greeting": period.get("greeting", "Hello")
            }

    # Fallback
    return {
        "name": meal_time_id.replace("_", " ").title(),
        "greeting": "Hello"
    }


async def get_meal_time_greeting(
    restaurant_id: str,
    meal_time_id: Optional[str] = None
) -> str:
    """
    Get the appropriate greeting for current meal time.

    Args:
        restaurant_id: Restaurant identifier
        meal_time_id: Optional meal time ID (will auto-detect if not provided)

    Returns:
        Greeting string (e.g., "Good morning", "Good evening")
    """
    meal_periods = await get_restaurant_meal_time_config(restaurant_id)

    if meal_time_id is None:
        meal_time_id = get_current_meal_time_sync(meal_periods)

    if meal_time_id:
        display_info = get_meal_time_display_info(meal_periods, meal_time_id)
        return display_info["greeting"]

    return "Hello"

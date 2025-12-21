"""
Timezone utilities for restaurant AI assistant
==============================================
Provides timezone-aware datetime functions using configured timezone
"""

from datetime import datetime, timezone as dt_timezone
from zoneinfo import ZoneInfo

from app.core.config import config


def get_app_timezone() -> ZoneInfo:
    """
    Get the application timezone (India Standard Time by default)
    """
    return ZoneInfo(config.TIMEZONE)


def get_current_time() -> datetime:
    """
    Get current time in application timezone (IST)
    """
    app_tz = get_app_timezone()
    utc_now = datetime.now(dt_timezone.utc)
    return utc_now.astimezone(app_tz)


def get_current_time_str() -> str:
    """
    Get current time as formatted string in IST
    """
    current_time = get_current_time()
    return current_time.strftime("%Y-%m-%d %H:%M:%S %Z")


def get_current_hour() -> int:
    """
    Get current hour in 24-hour format in IST
    """
    return get_current_time().hour


def get_greeting_based_on_time() -> str:
    """
    Get appropriate greeting based on current IST time
    """
    hour = get_current_hour()

    if 5 <= hour < 12:
        return "Good morning"
    elif 12 <= hour < 17:
        return "Good afternoon"
    elif 17 <= hour < 21:
        return "Good evening"
    else:
        return "Good night"


def format_datetime_for_display(dt: datetime) -> str:
    """
    Format datetime for user-friendly display in IST
    """
    if dt.tzinfo is None:
        # Assume UTC if no timezone info
        dt = dt.replace(tzinfo=dt_timezone.utc)

    ist_time = dt.astimezone(get_app_timezone())
    return ist_time.strftime("%d %B %Y, %I:%M %p IST")


def get_business_context() -> dict:
    """
    Get current business context including time-based information
    """
    current_time = get_current_time()
    hour = current_time.hour

    # Business hours: 9 AM to 11 PM IST
    is_open = 9 <= hour <= 23

    return {
        "current_time": get_current_time_str(),
        "current_hour": hour,
        "greeting": get_greeting_based_on_time(),
        "is_restaurant_open": is_open,
        "timezone": config.TIMEZONE,
        "day_of_week": current_time.strftime("%A"),
        "date": current_time.strftime("%d %B %Y")
    }

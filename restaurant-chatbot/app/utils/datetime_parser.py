"""
DateTime Parser Utility
=======================
Parse natural language date and time strings into datetime objects.

Supports:
- Relative dates: "today", "tomorrow", "next Friday"
- ISO dates: "2024-01-15"
- Natural dates: "January 15", "Jan 15"
- 12-hour time: "7pm", "7:30 PM"
- 24-hour time: "19:00", "19"
"""

from datetime import datetime, timedelta, time, date
import re
import structlog

logger = structlog.get_logger("utils.datetime_parser")


def parse_booking_datetime(date_str: str, time_str: str) -> datetime:
    """
    Parse date and time strings into timezone-aware datetime object.

    Args:
        date_str: Date string (e.g., "tomorrow", "2024-01-15", "next Friday")
        time_str: Time string (e.g., "7pm", "19:00")

    Returns:
        Timezone-aware datetime object

    Raises:
        ValueError: If date/time cannot be parsed

    Example:
        >>> parse_booking_datetime("tomorrow", "7pm")
        datetime(2024, 1, 16, 19, 0, tzinfo=...)
    """
    try:
        date_part = parse_date(date_str)
        time_part = parse_time(time_str)

        # Combine date and time
        booking_datetime = datetime.combine(date_part, time_part)

        # Add timezone
        from app.utils.timezone import get_app_timezone
        tz = get_app_timezone()
        booking_datetime = booking_datetime.replace(tzinfo=tz)

        logger.debug(
            "Parsed booking datetime",
            date_str=date_str,
            time_str=time_str,
            result=booking_datetime.isoformat()
        )

        return booking_datetime

    except Exception as e:
        logger.error(
            "Failed to parse booking datetime",
            date_str=date_str,
            time_str=time_str,
            error=str(e)
        )
        raise ValueError(f"Invalid date/time format: {date_str} {time_str}")


def parse_date(date_str: str) -> date:
    """
    Parse date string into date object.

    Supports:
    - Relative: "today", "tomorrow"
    - Day names: "next Friday", "coming Wednesday"
    - ISO format: "2024-01-15"
    - Natural: "January 15", "Jan 15"

    Args:
        date_str: Date string

    Returns:
        date object

    Raises:
        ValueError: If date cannot be parsed
    """
    date_lower = date_str.lower().strip()

    # Use IST timezone for relative dates
    from app.utils.timezone import get_current_time

    # Relative dates
    if "today" in date_lower:
        return get_current_time().date()

    if "tomorrow" in date_lower:
        return (get_current_time() + timedelta(days=1)).date()

    # Day names (Monday, Tuesday, etc.)
    day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    if any(day in date_lower for day in day_names):
        return parse_relative_day(date_str)

    # Try various date formats
    formats = [
        "%Y-%m-%d",       # 2024-01-15
        "%m/%d/%Y",       # 01/15/2024
        "%d/%m/%Y",       # 15/01/2024
        "%B %d",          # January 15
        "%b %d",          # Jan 15
        "%B %d, %Y",      # January 15, 2024
        "%b %d, %Y",      # Jan 15, 2024
    ]

    for fmt in formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt)
            date_obj = parsed_date.date()

            # If no year specified, assume current year in IST
            if parsed_date.year == 1900:
                current_year = get_current_time().year
                date_obj = date_obj.replace(year=current_year)

            return date_obj

        except ValueError:
            continue

    raise ValueError(f"Could not parse date: {date_str}")


def parse_time(time_str: str) -> time:
    """
    Parse time string into time object.

    Supports:
    - 12-hour: "7pm", "7:30 PM", "12:00 am"
    - 24-hour: "19:00", "19", "07:30"

    Args:
        time_str: Time string

    Returns:
        time object

    Raises:
        ValueError: If time cannot be parsed
    """
    time_lower = time_str.lower().strip()

    hour = None
    minute = 0

    # 12-hour format with AM/PM
    if "pm" in time_lower or "am" in time_lower:
        time_match = re.search(r'(\d+)(?::(\d+))?\s*(am|pm)', time_lower)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2) or 0)
            is_pm = time_match.group(3) == 'pm'

            # Convert to 24-hour format
            if hour == 12:
                hour = 0 if not is_pm else 12
            elif is_pm:
                hour += 12

    else:
        # 24-hour format or just number
        time_match = re.search(r'(\d+)(?::(\d+))?', time_lower)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2) or 0)

    if hour is None or hour < 0 or hour > 23 or minute < 0 or minute > 59:
        raise ValueError(f"Could not parse time: {time_str}")

    return time(hour, minute)


def parse_relative_day(date_str: str) -> date:
    """
    Parse relative day names like 'next Wednesday', 'coming Friday'.

    Args:
        date_str: String containing day name

    Returns:
        date object

    Raises:
        ValueError: If day name not found

    Example:
        >>> parse_relative_day("next Friday")
        date(2024, 1, 19)  # Next Friday from today
    """
    # Use IST timezone for relative days
    from app.utils.timezone import get_current_time

    date_lower = date_str.lower()
    today = get_current_time().date()
    current_weekday = today.weekday()  # Monday=0, Sunday=6

    # Map day names to weekday numbers
    day_mapping = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6
    }

    # Find which day is mentioned
    target_day = None
    for day_name, day_num in day_mapping.items():
        if day_name in date_lower:
            target_day = day_num
            break

    if target_day is None:
        raise ValueError(f"Could not identify day from: {date_str}")

    # Calculate days to add
    days_ahead = target_day - current_weekday

    # If the target day has passed this week, go to next week
    # Or if it explicitly says "next" or "coming" and it's the same day or later
    if days_ahead <= 0:
        days_ahead += 7
    elif "next" in date_lower and days_ahead < 7:
        days_ahead += 7

    target_date = today + timedelta(days=days_ahead)
    return target_date


def format_datetime_for_display(dt: datetime) -> str:
    """
    Format datetime for user-friendly display.

    Args:
        dt: datetime object

    Returns:
        Formatted string (e.g., "Friday, January 15 at 7:00 PM")
    """
    return dt.strftime("%A, %B %d at %I:%M %p")


def is_valid_booking_time(dt: datetime, min_advance_hours: int = 1) -> bool:
    """
    Check if booking time is valid (not in the past, meets minimum advance).

    Args:
        dt: Booking datetime
        min_advance_hours: Minimum hours in advance required

    Returns:
        True if valid, False otherwise
    """
    now = datetime.now(dt.tzinfo)
    min_time = now + timedelta(hours=min_advance_hours)

    return dt >= min_time

"""
Natural Language Time Parser
=============================
Converts vague time expressions like "evening", "lunch", "dinner" into
deterministic time ranges and suggestions.

This allows the agent to handle natural language time queries intelligently
without requiring users to specify exact times upfront.

Usage:
    >>> result = parse_natural_time("evening")
    >>> result["is_vague"]
    True
    >>> result["suggested_times"]
    ["18:00", "18:30", "19:00", "19:30", "20:00", "20:30", "21:00"]
    >>> result["default_time"]
    "19:00"  # 7 PM is most common dinner time
"""

from typing import Dict, Any, List, Optional
import structlog

logger = structlog.get_logger("utils.time_parser")


# Define time period mappings with restaurant context
TIME_PERIODS = {
    # Evening / Dinner
    "evening": {
        "start": "18:00",
        "end": "22:00",
        "default": "19:00",  # 7 PM is most popular
        "suggestions": ["18:00", "18:30", "19:00", "19:30", "20:00", "20:30", "21:00"],
        "display_name": "evening",
        "description": "Evening dining hours from 6 PM to 10 PM"
    },
    "dinner": {
        "start": "18:00",
        "end": "22:00",
        "default": "19:30",  # 7:30 PM is peak dinner
        "suggestions": ["18:00", "18:30", "19:00", "19:30", "20:00", "20:30", "21:00"],
        "display_name": "dinner",
        "description": "Dinner hours from 6 PM to 10 PM"
    },
    "dinner time": {
        "start": "18:00",
        "end": "22:00",
        "default": "19:30",
        "suggestions": ["18:00", "18:30", "19:00", "19:30", "20:00", "20:30", "21:00"],
        "display_name": "dinner time",
        "description": "Dinner hours from 6 PM to 10 PM"
    },

    # Lunch
    "lunch": {
        "start": "12:00",
        "end": "15:00",
        "default": "13:00",  # 1 PM is typical lunch
        "suggestions": ["12:00", "12:30", "13:00", "13:30", "14:00", "14:30"],
        "display_name": "lunch",
        "description": "Lunch hours from 12 PM to 3 PM"
    },
    "lunch time": {
        "start": "12:00",
        "end": "15:00",
        "default": "13:00",
        "suggestions": ["12:00", "12:30", "13:00", "13:30", "14:00", "14:30"],
        "display_name": "lunch time",
        "description": "Lunch hours from 12 PM to 3 PM"
    },

    # Breakfast / Morning
    "breakfast": {
        "start": "08:00",
        "end": "11:00",
        "default": "09:00",  # 9 AM typical breakfast
        "suggestions": ["08:00", "08:30", "09:00", "09:30", "10:00", "10:30"],
        "display_name": "breakfast",
        "description": "Breakfast hours from 8 AM to 11 AM"
    },
    "morning": {
        "start": "08:00",
        "end": "12:00",
        "default": "10:00",
        "suggestions": ["08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00", "11:30"],
        "display_name": "morning",
        "description": "Morning hours from 8 AM to 12 PM"
    },

    # Afternoon
    "afternoon": {
        "start": "14:00",
        "end": "17:00",
        "default": "15:00",  # 3 PM
        "suggestions": ["14:00", "14:30", "15:00", "15:30", "16:00", "16:30"],
        "display_name": "afternoon",
        "description": "Afternoon hours from 2 PM to 5 PM"
    },

    # Late night
    "late night": {
        "start": "21:00",
        "end": "23:00",
        "default": "21:30",
        "suggestions": ["21:00", "21:30", "22:00", "22:30"],
        "display_name": "late night",
        "description": "Late night hours from 9 PM to 11 PM"
    },
    "late": {
        "start": "21:00",
        "end": "23:00",
        "default": "21:30",
        "suggestions": ["21:00", "21:30", "22:00", "22:30"],
        "display_name": "late",
        "description": "Late hours from 9 PM to 11 PM"
    },

    # Brunch
    "brunch": {
        "start": "10:00",
        "end": "14:00",
        "default": "11:30",
        "suggestions": ["10:00", "10:30", "11:00", "11:30", "12:00", "12:30", "13:00", "13:30"],
        "display_name": "brunch",
        "description": "Brunch hours from 10 AM to 2 PM"
    }
}


def parse_natural_time(time_str: str) -> Dict[str, Any]:
    """
    Parse natural language time expression into deterministic time data.

    Args:
        time_str: Natural language time string (e.g., "evening", "lunch", "7pm")

    Returns:
        Dict containing:
        - is_vague (bool): True if this is a vague expression, False if specific
        - vague_term (str): The vague term identified (e.g., "evening")
        - time_range (dict): Start and end times in 24-hour format
        - default_time (str): Most common/recommended time for this period
        - suggested_times (list): List of specific times to suggest to user
        - display_name (str): User-friendly name for display
        - description (str): Description of the time period
        - original_input (str): Original input string

    Examples:
        >>> parse_natural_time("evening")
        {
            "is_vague": True,
            "vague_term": "evening",
            "time_range": {"start": "18:00", "end": "22:00"},
            "default_time": "19:00",
            "suggested_times": ["18:00", "18:30", "19:00", ...],
            "display_name": "evening",
            "description": "Evening dining hours from 6 PM to 10 PM",
            "original_input": "evening"
        }

        >>> parse_natural_time("7pm")
        {
            "is_vague": False,
            "specific_time": "19:00",
            "original_input": "7pm"
        }
    """
    time_lower = time_str.lower().strip()

    logger.debug("Parsing natural time", input=time_str)

    # Check if it's a vague time expression
    for term, data in TIME_PERIODS.items():
        if term in time_lower:
            logger.info(
                "Identified vague time expression",
                input=time_str,
                matched_term=term,
                default_time=data["default"]
            )

            return {
                "is_vague": True,
                "vague_term": term,
                "time_range": {
                    "start": data["start"],
                    "end": data["end"]
                },
                "default_time": data["default"],
                "suggested_times": data["suggestions"],
                "display_name": data["display_name"],
                "description": data["description"],
                "original_input": time_str
            }

    # Not a vague expression - assume it's a specific time
    # Let the existing parse_time function handle it
    logger.debug("Time appears to be specific", input=time_str)

    return {
        "is_vague": False,
        "specific_time": time_str,  # Return as-is for parse_time to handle
        "original_input": time_str
    }


def is_vague_time(time_str: str) -> bool:
    """
    Quick check if a time string is vague (needs conversion) or specific.

    Args:
        time_str: Time string to check

    Returns:
        True if vague (like "evening"), False if specific (like "7pm")

    Examples:
        >>> is_vague_time("evening")
        True
        >>> is_vague_time("7pm")
        False
        >>> is_vague_time("lunch")
        True
        >>> is_vague_time("19:00")
        False
    """
    time_lower = time_str.lower().strip()
    return any(term in time_lower for term in TIME_PERIODS.keys())


def get_suggested_times_display(time_str: str) -> Optional[str]:
    """
    Get user-friendly display of suggested times for a vague expression.

    Args:
        time_str: Vague time expression

    Returns:
        String suitable for display to user, or None if not vague

    Examples:
        >>> get_suggested_times_display("evening")
        "6:00 PM, 6:30 PM, 7:00 PM, 7:30 PM, 8:00 PM, 8:30 PM, 9:00 PM"

        >>> get_suggested_times_display("lunch")
        "12:00 PM, 12:30 PM, 1:00 PM, 1:30 PM, 2:00 PM, 2:30 PM"
    """
    result = parse_natural_time(time_str)

    if not result["is_vague"]:
        return None

    # Convert 24-hour times to 12-hour format for display
    suggested_times = result["suggested_times"]
    display_times = []

    for t in suggested_times:
        hour, minute = map(int, t.split(":"))

        # Convert to 12-hour format
        if hour == 0:
            display_hour = 12
            period = "AM"
        elif hour < 12:
            display_hour = hour
            period = "AM"
        elif hour == 12:
            display_hour = 12
            period = "PM"
        else:
            display_hour = hour - 12
            period = "PM"

        display_times.append(f"{display_hour}:{minute:02d} {period}")

    return ", ".join(display_times)


def get_time_range_for_search(time_str: str) -> Optional[Dict[str, str]]:
    """
    Get time range suitable for searching availability across all slots.

    Args:
        time_str: Vague time expression

    Returns:
        Dict with start and end times, or None if not vague

    Examples:
        >>> get_time_range_for_search("evening")
        {"start": "18:00", "end": "22:00"}

        >>> get_time_range_for_search("7pm")
        None
    """
    result = parse_natural_time(time_str)

    if not result["is_vague"]:
        return None

    return result["time_range"]


# For testing purposes
if __name__ == "__main__":

    print("Testing Natural Language Time Parser\n")
    print("=" * 60)

    test_cases = [
        "evening",
        "dinner",
        "lunch",
        "breakfast",
        "afternoon",
        "morning",
        "late night",
        "brunch",
        "7pm",  # specific time
        "19:00",  # specific time
    ]

    for test in test_cases:
        result = parse_natural_time(test)
        print(f"\nInput: '{test}'")
        print(f"Is Vague: {result['is_vague']}")

        if result["is_vague"]:
            print(f"Description: {result['description']}")
            print(f"Default Time: {result['default_time']}")
            print(f"Time Range: {result['time_range']['start']} - {result['time_range']['end']}")
            print(f"Suggestions: {', '.join(result['suggested_times'])}")
            print(f"Display: {get_suggested_times_display(test)}")
        else:
            print(f"Specific Time: {result['specific_time']}")

        print("-" * 60)

    print("\n\nQuick vague check tests:")
    print(f"is_vague_time('evening'): {is_vague_time('evening')}")
    print(f"is_vague_time('7pm'): {is_vague_time('7pm')}")
    print(f"is_vague_time('lunch time'): {is_vague_time('lunch time')}")

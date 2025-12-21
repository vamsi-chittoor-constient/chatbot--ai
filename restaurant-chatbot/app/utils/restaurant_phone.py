"""
Restaurant Phone Utility
=========================
Centralized utility for fetching and validating restaurant phone numbers.

This module provides a Redis-cached mechanism to fetch the restaurant phone
and validate customer phones against it to prevent contamination during entity extraction.

Restaurant info is loaded into Redis on application startup for fast access.
"""

import structlog
from typing import Optional

logger = structlog.get_logger(__name__)


async def get_restaurant_phone() -> Optional[str]:
    """
    Fetch restaurant phone number from Redis cache.

    Restaurant config is loaded into Redis on application startup,
    so this is a fast in-memory lookup (no database query).

    Returns:
        Restaurant phone number or None if not found

    IMPORTANT: This phone is for CUSTOMER REFERENCE ONLY.
    NEVER use this as contact_phone when creating bookings!
    """
    try:
        from app.services.restaurant_cache_service import get_cached_restaurant_phone

        phone = await get_cached_restaurant_phone()

        if phone:
            logger.debug("restaurant_phone_retrieved_from_redis", phone=phone)
            return phone
        else:
            logger.warning("restaurant_phone_not_found_in_redis_cache")
            return None

    except Exception as e:
        logger.error("failed_to_fetch_restaurant_phone_from_redis", error=str(e))
        return None


def normalize_phone(phone: str) -> str:
    """
    Normalize phone number for comparison.

    Removes:
    - Country codes (+91)
    - Dashes (-)
    - Spaces
    - Parentheses ()

    Args:
        phone: Phone number to normalize

    Returns:
        Normalized phone number (digits only)
    """
    if not phone:
        return ""

    return (phone
        .replace("+91", "")
        .replace("+", "")
        .replace("-", "")
        .replace(" ", "")
        .replace("(", "")
        .replace(")", "")
        .strip())


async def is_restaurant_phone(phone: str) -> bool:
    """
    Check if a phone number belongs to the restaurant.

    This function:
    1. Fetches restaurant phone from database (with caching)
    2. Normalizes both phones for comparison
    3. Checks against common test/placeholder numbers

    Args:
        phone: Phone number to validate

    Returns:
        True if phone matches restaurant phone or is invalid placeholder

    Example:
        >>> await is_restaurant_phone("9999999999")
        True  # Common test number

        >>> await is_restaurant_phone("9876543210")  # If this is restaurant phone in DB
        True  # Matches database restaurant phone

        >>> await is_restaurant_phone("8765432109")  # Customer phone
        False  # Different from restaurant phone
    """
    if not phone:
        return False

    # Common test/placeholder numbers that are NOT real customer phones
    invalid_phones = [
        "9999999999",
        "+91-XXX-XXX-XXXX",
        "1111111111",
        "0000000000",
        "1234567890",
        "0123456789",
    ]

    # Normalize phone for comparison
    normalized = normalize_phone(phone)

    # Check against known invalid/test phones
    for invalid in invalid_phones:
        invalid_normalized = normalize_phone(invalid)
        if normalized == invalid_normalized:
            logger.debug(
                "rejected_test_phone",
                phone=phone,
                reason="Matches test/placeholder number"
            )
            return True

    # Fetch and check against actual restaurant phone from database
    restaurant_phone = await get_restaurant_phone()

    if restaurant_phone:
        restaurant_normalized = normalize_phone(restaurant_phone)
        if normalized == restaurant_normalized:
            logger.warning(
                "rejected_restaurant_phone",
                phone=phone,
                restaurant_phone=restaurant_phone,
                reason="Cannot use restaurant phone as customer contact"
            )
            return True

    return False


async def clear_cache():
    """
    Clear the restaurant phone cache from Redis.

    Useful for testing or when restaurant info is updated.
    """
    try:
        from app.services.restaurant_cache_service import clear_restaurant_cache
        await clear_restaurant_cache()
        logger.info("restaurant_phone_cache_cleared")
    except Exception as e:
        logger.error("failed_to_clear_restaurant_cache", error=str(e))

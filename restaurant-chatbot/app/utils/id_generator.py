"""
Custom ID Generator
===================
Generates secure random IDs with custom prefixes for all database entities.

Format: {prefix}{6-alphanumeric}
- prefix: 3-letter identifier (e.g., usr, res, ord)
- 6-alphanumeric: Random 6-character string (A-Z, 0-9)

Examples:
- User IDs: usrK9X2M7, usrP3A8N1, usrH4J6L9
- Restaurant IDs: resA1B2C3, resX9Y8Z7
- Order IDs: ordM3N4P5, ordQ7R8S9

Security: Random IDs prevent enumeration attacks (IDOR vulnerability)
"""

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

logger = structlog.get_logger(__name__)


# Entity prefix mapping
ENTITY_PREFIXES = {
    # User Management
    "users": "usr",
    "user_preferences": "up",
    "user_devices": "udv",
    "session_tokens": "stk",

    # Restaurant Operations
    "restaurant_config": "res",
    "tables": "tbl",
    "menu_categories": "mct",
    "menu_items": "mit",

    # Booking System
    "bookings": "bkg",

    # Order Management
    "orders": "ord",
    "order_items": "oit",
    "abandoned_carts": "abc",
    "abandoned_bookings": "abb",

    # Payment Processing
    "payments": "pmt",
    "payment_orders": "pmo",
    "payment_transactions": "ptr",
    "webhook_events": "whe",
    "payment_retry_attempts": "pra",

    # Communication
    "sessions": "ses",
    "conversations": "cnv",
    "messages": "msg",
    "email_logs": "eml",

    # Analytics & Feedback
    "complaints": "cmp",
    "ratings": "rat",
    "feedback": "fdb",
    "waitlist": "wtl",

    # System Operations
    "agent_memory": "amm",
    "system_logs": "slg",
    "knowledge_base": "kbk",
    "message_templates": "mtm",
    "message_logs": "mlg",
    "otp_verification": "otp",
    "api_key_usage": "aku",

    # Customer Satisfaction
    "customer_feedback_details": "cfd",
    "satisfaction_metrics": "stm",
    "complaint_resolution_templates": "crt",

    # General Queries
    "faq": "faq",
    "restaurant_policies": "rpl",
    "query_analytics": "qan",
}


def format_id(prefix: str, random_suffix: str = None) -> str:
    """
    Format ID with prefix and random alphanumeric suffix.

    Args:
        prefix: 3-letter entity prefix
        random_suffix: 6-character random string (if None, will be generated)

    Returns:
        Formatted ID (e.g., usrK9X2M7)
    """
    if random_suffix is None:
        random_suffix = generate_random_suffix()
    return f"{prefix}{random_suffix}"


def generate_custom_id(table_name: str, prefix: str) -> str:
    """
    Generate a custom ID with the given prefix (backward compatibility).

    Args:
        table_name: Name of the table (for documentation purposes)
        prefix: Custom 3-letter prefix

    Returns:
        Formatted ID with random suffix (e.g., assK9X2M7)
    """
    return format_id(prefix)


def generate_random_suffix(length: int = 6) -> str:
    """
    Generate a random alphanumeric suffix.

    Uses uppercase letters (A-Z) and digits (0-9) for a total of 36 possible characters.
    With 6 characters, this gives 36^6 = 2,176,782,336 possible combinations.

    Args:
        length: Length of the random suffix (default: 6)

    Returns:
        Random alphanumeric string (e.g., "K9X2M7")
    """
    import random
    import string

    # Use uppercase letters and digits only (36 characters total)
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


async def generate_id(session: AsyncSession, table_name: str, max_retries: int = 5) -> str:
    """
    Generate secure random ID for a table with collision checking.

    Generates a random alphanumeric ID and checks for uniqueness in the database.
    If collision occurs, retries with a new random ID.

    Args:
        session: Database session
        table_name: Name of the table
        max_retries: Maximum number of retries on collision (default: 5)

    Returns:
        Unique random ID in format: {prefix}{6-alphanumeric}

    Raises:
        ValueError: If table_name is not in ENTITY_PREFIXES
        RuntimeError: If unable to generate unique ID after max_retries
    """
    if table_name not in ENTITY_PREFIXES:
        raise ValueError(f"Unknown table name: {table_name}. Add prefix to ENTITY_PREFIXES.")

    prefix = ENTITY_PREFIXES[table_name]

    for attempt in range(max_retries):
        try:
            # Generate random ID
            random_id = format_id(prefix)

            # Check if ID already exists
            query = text(f"SELECT COUNT(*) FROM {table_name} WHERE id = :id")
            result = await session.execute(query, {"id": random_id})
            count = result.scalar()

            if count == 0:
                # ID is unique
                logger.debug(
                    "Generated unique random ID",
                    table=table_name,
                    prefix=prefix,
                    id=random_id,
                    attempt=attempt + 1
                )
                return random_id
            else:
                # Collision detected, retry
                logger.warning(
                    "ID collision detected, retrying",
                    table=table_name,
                    id=random_id,
                    attempt=attempt + 1
                )

        except Exception as e:
            logger.error(
                "Error during ID generation",
                table=table_name,
                prefix=prefix,
                attempt=attempt + 1,
                error=str(e)
            )

    # If we reach here, all retries failed
    logger.error(
        "Failed to generate unique ID after maximum retries",
        table=table_name,
        prefix=prefix,
        max_retries=max_retries
    )
    raise RuntimeError(f"Unable to generate unique ID for {table_name} after {max_retries} attempts")


def create_id_generator(table_name: str):
    """
    Create an ID generator function for SQLAlchemy default parameter.

    This returns a callable that SQLAlchemy can use as a default value.
    Note: This is for synchronous context. For async, use generate_id directly.
    WARNING: This does NOT check for collisions - use only as fallback!

    Args:
        table_name: Name of the table

    Returns:
        Function that generates random IDs
    """
    def _generate():
        # Synchronous fallback - generates random ID without collision checking
        prefix = ENTITY_PREFIXES.get(table_name, "unk")
        random_suffix = generate_random_suffix()
        return format_id(prefix, random_suffix)

    return _generate


def get_prefix_for_table(table_name: str) -> str:
    """
    Get the 3-letter prefix for a table.

    Args:
        table_name: Name of the table

    Returns:
        3-letter prefix

    Raises:
        ValueError: If table not found
    """
    if table_name not in ENTITY_PREFIXES:
        raise ValueError(f"Unknown table: {table_name}")
    return ENTITY_PREFIXES[table_name]

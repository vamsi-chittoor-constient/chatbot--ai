"""
CrewAI Booking Tools
====================
Sync booking tools for CrewAI following the same pattern as food ordering.

Uses PostgreSQL for persistent storage (A24 schema):
- table_info: Restaurant table configuration
- table_booking_info: Reservation records

Tools:
- check_table_availability: Check table availability for date/time
"""
from crewai.tools import tool
from typing import Dict, List, Optional
import structlog
from datetime import datetime, timedelta

logger = structlog.get_logger(__name__)


# ============================================================================
# SYNCHRONOUS HELPER FUNCTIONS
# ============================================================================

def _get_available_tables(booking_datetime: datetime, party_size: int) -> List[Dict]:
    """Get available tables for given datetime and party size using sync DB (A24 schema)."""
    try:
        from app.core.db_pool import SyncDBConnection
        from psycopg2.extras import RealDictCursor

        # Extract date and time for A24 schema (separate columns)
        booking_date = booking_datetime.date()
        booking_time = booking_datetime.time()

        with SyncDBConnection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get tables that can accommodate party size and are not booked
                # A24 schema: table_info, table_booking_info with booking_date + booking_time
                cursor.execute("""
                    SELECT t.table_id, t.table_number, t.table_capacity, t.floor_location, t.table_type
                    FROM table_info t
                    WHERE t.table_capacity >= %s
                    AND t.is_active = TRUE
                    AND (t.is_deleted = FALSE OR t.is_deleted IS NULL)
                    AND NOT EXISTS (
                        SELECT 1 FROM table_booking_info b
                        WHERE b.table_id = t.table_id
                        AND b.booking_status NOT IN ('cancelled', 'completed')
                        AND (b.is_deleted = FALSE OR b.is_deleted IS NULL)
                        AND b.booking_date = %s
                        AND b.booking_time BETWEEN %s - INTERVAL '1 hour' AND %s + INTERVAL '1 hour'
                    )
                    ORDER BY t.table_capacity ASC
                    LIMIT 10
                """, (party_size, booking_date, booking_time, booking_time))

                rows = cursor.fetchall()

        if not rows:
            logger.info("no_tables_available", party_size=party_size, datetime=str(booking_datetime))
            return []

        return [
            {
                "id": str(row['table_id']),
                "table_number": row['table_number'],
                "capacity": row['table_capacity'],
                "location": row['floor_location'] or "Main Area",
                "table_type": row.get('table_type') or "standard"
            }
            for row in rows
        ]

    except Exception as e:
        # Handle encoding issues on Windows
        error_msg = str(e).encode('ascii', 'replace').decode('ascii')
        logger.error("get_available_tables_failed", error=error_msg)
        return []


def _parse_booking_datetime(date_str: str, time_str: str = None) -> Optional[datetime]:
    """Parse natural language date/time into datetime object."""
    from datetime import date
    import re

    today = date.today()
    target_date = today

    date_lower = date_str.lower().strip()

    # Parse date
    if "today" in date_lower:
        target_date = today
    elif "tomorrow" in date_lower or "tomm" in date_lower or "tmrw" in date_lower or "tmr" in date_lower:
        target_date = today + timedelta(days=1)
    elif "next" in date_lower:
        # "next friday", "next week", etc.
        days_map = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6
        }
        for day_name, day_num in days_map.items():
            if day_name in date_lower:
                days_ahead = day_num - today.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                target_date = today + timedelta(days=days_ahead)
                break
    else:
        # Try ISO format
        try:
            target_date = datetime.fromisoformat(date_str.split('T')[0]).date()
        except:
            pass

    # Parse time
    hour = 19  # Default 7 PM
    minute = 0

    if time_str:
        time_lower = time_str.lower().strip()

        # Handle "7pm", "7:30pm", "19:00"
        time_match = re.match(r'(\d{1,2}):?(\d{2})?\s*(am|pm)?', time_lower)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2) or 0)
            ampm = time_match.group(3)

            if ampm == "pm" and hour < 12:
                hour += 12
            elif ampm == "am" and hour == 12:
                hour = 0

        # Handle vague times
        if "lunch" in time_lower:
            hour, minute = 12, 30
        elif "dinner" in time_lower or "evening" in time_lower:
            hour, minute = 19, 0
        elif "morning" in time_lower or "breakfast" in time_lower:
            hour, minute = 9, 0

    try:
        return datetime(target_date.year, target_date.month, target_date.day, hour, minute)
    except:
        return None


# ============================================================================
# BOOKING TOOLS WITH @tool DECORATOR
# ============================================================================

@tool("check_table_availability")
def check_table_availability(date: str, time: str = "7pm", party_size: int = 2) -> str:
    """
    Check table availability for a reservation.

    Use this when customer asks about availability or wants to book a table.

    Args:
        date: Date for reservation (e.g., "tomorrow", "next Friday", "2024-12-15")
        time: Time for reservation (e.g., "7pm", "19:00", "dinner")
        party_size: Number of guests (default: 2)

    Returns:
        Available tables or message if none available.
    """
    try:
        # Parse datetime
        booking_dt = _parse_booking_datetime(date, time)
        if not booking_dt:
            return f"Could not understand the date/time '{date} {time}'. Please try formats like 'tomorrow 7pm' or '2024-12-15 19:00'."

        # Check if booking is in the past
        if booking_dt < datetime.now():
            return "Cannot check availability for past dates. Please choose a future date."

        # Get available tables
        tables = _get_available_tables(booking_dt, party_size)

        if not tables:
            return f"No tables available for {party_size} guests on {booking_dt.strftime('%A, %B %d at %I:%M %p')}. Would you like to try a different time?"

        # Format response
        table_list = [f"Table {t['table_number']} ({t['capacity']} seats, {t['location']})" for t in tables[:3]]
        return f"Tables available for {party_size} guests on {booking_dt.strftime('%A, %B %d at %I:%M %p')}: {', '.join(table_list)}"

    except Exception as e:
        logger.error("check_availability_error", error=str(e))
        return f"Error checking availability: {str(e)}"

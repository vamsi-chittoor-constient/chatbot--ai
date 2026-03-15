"""
CrewAI Booking Agent
====================
Sync booking tools for CrewAI following the same pattern as food ordering.

Uses PostgreSQL for persistent storage (A24 schema):
- table_info: Restaurant table configuration
- table_booking_info: Reservation records

Tools:
- check_table_availability: Check table availability for date/time
- make_reservation: Create a new reservation
- get_my_bookings: Get user's existing bookings
- modify_reservation: Change booking details
- cancel_reservation: Cancel a booking
"""
from crewai import Agent
from crewai.tools import tool
from typing import Dict, Any, List, Optional
import structlog
from datetime import datetime, timedelta
import json

logger = structlog.get_logger(__name__)


# ============================================================================
# SYNCHRONOUS HELPER FUNCTIONS
# All database operations are sync - CrewAI runs tools in threads
# ============================================================================

def _get_table_capacities() -> List[int]:
    """Get distinct table capacities from the database."""
    try:
        from app.core.db_pool import SyncDBConnection
        from psycopg2.extras import RealDictCursor

        with SyncDBConnection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT DISTINCT table_capacity
                    FROM table_info
                    WHERE is_active = TRUE
                    AND (is_deleted = FALSE OR is_deleted IS NULL)
                    ORDER BY table_capacity ASC
                """)
                rows = cursor.fetchall()

        return [row['table_capacity'] for row in rows]
    except Exception as e:
        logger.error("get_table_capacities_failed", error=str(e))
        return []


def _get_availability_map(days: int = 30) -> Dict[str, Any]:
    """
    Build an availability map for the next N days.
    Optimized: 2 queries total (all tables + all bookings in range), compute in Python.
    """
    try:
        from app.core.db_pool import SyncDBConnection
        from psycopg2.extras import RealDictCursor
        from datetime import date, time as dtime

        capacities = _get_table_capacities()
        if not capacities:
            return {"max_party_size": 8, "party_sizes": list(range(1, 9)), "dates": {}}

        max_capacity = max(capacities)

        # Define time slots (30-min intervals from 12:00 to 22:00)
        time_slots = []
        for hour in range(12, 22):
            for minute in [0, 30]:
                time_slots.append(dtime(hour, minute))

        today = date.today()
        start_date = today + timedelta(days=1)
        end_date = today + timedelta(days=days)

        with SyncDBConnection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Query 1: Get all active tables (table_id + capacity)
                cursor.execute("""
                    SELECT table_id, table_capacity
                    FROM table_info
                    WHERE is_active = TRUE
                    AND (is_deleted = FALSE OR is_deleted IS NULL)
                """)
                all_tables = cursor.fetchall()

                # Query 2: Get all bookings in the date range
                cursor.execute("""
                    SELECT table_id, booking_date, booking_time
                    FROM table_booking_info
                    WHERE booking_status NOT IN ('cancelled', 'completed')
                    AND (is_deleted = FALSE OR is_deleted IS NULL)
                    AND booking_date BETWEEN %s AND %s
                """, (start_date, end_date))
                all_bookings = cursor.fetchall()

        # Build lookup: (date, table_id) -> [booked_times]
        bookings_by_date_table = {}
        for b in all_bookings:
            key = (b['booking_date'], str(b['table_id']))
            if key not in bookings_by_date_table:
                bookings_by_date_table[key] = []
            bookings_by_date_table[key].append(b['booking_time'])

        # For each date + slot, compute available tables
        dates_map = {}
        for day_offset in range(1, days + 1):
            check_date = today + timedelta(days=day_offset)
            date_str = check_date.isoformat()
            slots_map = {}

            for t in time_slots:
                # Check each table: is it booked within ±1 hour of this slot?
                available = []
                for tbl in all_tables:
                    tbl_id = str(tbl['table_id'])
                    booked_times = bookings_by_date_table.get((check_date, tbl_id), [])
                    # Check if any booking conflicts (within 1 hour)
                    conflicted = False
                    for bt in booked_times:
                        # Convert times to minutes for easy comparison
                        slot_mins = t.hour * 60 + t.minute
                        book_mins = bt.hour * 60 + bt.minute
                        if abs(slot_mins - book_mins) < 60:
                            conflicted = True
                            break
                    if not conflicted:
                        available.append(tbl['table_capacity'])

                slot_label = t.strftime('%I:%M %p').lstrip('0')
                if available:
                    slots_map[slot_label] = {
                        "available": True,
                        "max_party": max(available),
                        "tables_free": len(available),
                    }
                else:
                    slots_map[slot_label] = {
                        "available": False,
                        "max_party": 0,
                        "tables_free": 0,
                    }

            dates_map[date_str] = {"slots": slots_map}

        return {
            "max_party_size": max_capacity,
            "party_sizes": list(range(1, max_capacity + 1)),
            "dates": dates_map,
        }

    except Exception as e:
        logger.error("get_availability_map_failed", error=str(e), exc_info=True)
        return {"max_party_size": 8, "party_sizes": list(range(1, 9)), "dates": {}}


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


def _generate_confirmation_code() -> str:
    """Generate unique confirmation code."""
    import secrets
    import string
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))


def _generate_booking_id() -> str:
    """Generate unique booking ID following the codebase pattern."""
    import secrets
    import string
    # Format: book_ + 16 random chars (similar to other IDs in the codebase)
    random_part = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(16))
    return f"book_{random_part}"


def _get_restaurant_id() -> Optional[str]:
    """Get the restaurant ID from restaurant_table (UUID, FK target for table_info)."""
    try:
        from app.core.db_pool import SyncDBConnection
        from psycopg2.extras import RealDictCursor

        with SyncDBConnection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT restaurant_id FROM restaurant_table LIMIT 1")
                row = cursor.fetchone()
                return str(row['restaurant_id']) if row else None
    except Exception as e:
        logger.error("get_restaurant_id_failed", error=str(e))
        return None


def _create_booking_in_db(
    booking_id: str,
    confirmation_code: str,
    session_id: str,
    table_id: str,
    booking_datetime: datetime,
    party_size: int,
    guest_name: str,
    phone: str
) -> bool:
    """Create booking record in PostgreSQL (A24 schema: table_booking_info)."""
    try:
        from app.core.db_pool import SyncDBConnection

        restaurant_id = _get_restaurant_id()
        if not restaurant_id:
            logger.error("no_restaurant_config_found")
            return False

        # A24 schema uses separate booking_date and booking_time columns
        booking_date = booking_datetime.date()
        booking_time = booking_datetime.time()

        with SyncDBConnection() as conn:
            with conn.cursor() as cursor:
                # A24 schema: table_booking_info
                cursor.execute("""
                    INSERT INTO table_booking_info (
                        restaurant_id, table_id, party_size,
                        booking_date, booking_time, booking_status,
                        device_id, guest_name, contact_phone, confirmation_code,
                        is_advance_booking, is_deleted,
                        created_at, updated_at
                    ) VALUES (
                        %s, %s::uuid, %s,
                        %s, %s, 'confirmed',
                        %s, %s, %s, %s,
                        TRUE, FALSE,
                        NOW(), NOW()
                    )
                """, (
                    restaurant_id, table_id, party_size,
                    booking_date, booking_time,
                    session_id, guest_name, phone, confirmation_code
                ))
                conn.commit()

        logger.info(
            "booking_created_postgresql",
            confirmation_code=confirmation_code,
            table_id=table_id
        )
        return True

    except Exception as e:
        logger.error("create_booking_in_db_failed", error=str(e), exc_info=True)
        return False


def _get_bookings_from_db(session_id: str) -> List[Dict]:
    """Get all active bookings for a session from PostgreSQL (A24 schema)."""
    try:
        from app.core.db_pool import SyncDBConnection
        from psycopg2.extras import RealDictCursor

        with SyncDBConnection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # A24 schema: table_booking_info + table_info
                cursor.execute("""
                    SELECT b.table_booking_id, b.confirmation_code,
                           b.booking_date, b.booking_time,
                           b.party_size, b.booking_status,
                           b.guest_name, t.table_number, t.floor_location
                    FROM table_booking_info b
                    LEFT JOIN table_info t ON b.table_id = t.table_id
                    WHERE b.device_id = %s
                    AND b.booking_status NOT IN ('cancelled', 'completed')
                    AND (b.is_deleted = FALSE OR b.is_deleted IS NULL)
                    AND b.booking_date >= CURRENT_DATE
                    ORDER BY b.booking_date, b.booking_time ASC
                """, (session_id,))
                rows = cursor.fetchall()

        return [
            {
                "id": str(row['table_booking_id']),
                "confirmation_code": row['confirmation_code'],
                "booking_date": row['booking_date'],
                "booking_time": row['booking_time'],
                "party_size": row['party_size'],
                "booking_status": row['booking_status'],
                "guest_name": row['guest_name'] or "Guest",
                "table_number": row['table_number'] or "TBD",
                "location": row['floor_location'] or "Main Area"
            }
            for row in rows
        ]

    except Exception as e:
        logger.error("get_bookings_from_db_failed", error=str(e), exc_info=True)
        return []


def _cancel_booking_in_db(confirmation_code: str, session_id: str) -> Optional[Dict]:
    """Cancel a booking in PostgreSQL (A24 schema). Returns booking info if found."""
    try:
        from app.core.db_pool import SyncDBConnection
        from psycopg2.extras import RealDictCursor

        with SyncDBConnection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # First get the booking to verify ownership
                # A24 schema: table_booking_info + table_info
                cursor.execute("""
                    SELECT b.table_booking_id, b.confirmation_code,
                           b.booking_date, b.booking_time,
                           b.party_size, b.booking_status,
                           t.table_number
                    FROM table_booking_info b
                    LEFT JOIN table_info t ON b.table_id = t.table_id
                    WHERE b.confirmation_code = %s
                    AND b.device_id = %s
                """, (confirmation_code.upper(), session_id))
                booking = cursor.fetchone()

                if not booking:
                    return None

                if booking['booking_status'] == 'cancelled':
                    return {"already_cancelled": True, **dict(booking)}

                # Cancel the booking
                cursor.execute("""
                    UPDATE table_booking_info
                    SET booking_status = 'cancelled',
                        cancellation_reason = 'Cancelled by customer via chat',
                        updated_at = NOW()
                    WHERE confirmation_code = %s
                """, (confirmation_code.upper(),))
                conn.commit()

        logger.info("booking_cancelled_postgresql", confirmation_code=confirmation_code)
        return dict(booking)

    except Exception as e:
        logger.error("cancel_booking_in_db_failed", error=str(e), exc_info=True)
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
    # Note: This tool doesn't have session_id, so we can't emit activity here
    # Activity will be emitted from restaurant_crew.py before crew.kickoff()
    try:
        # Parse datetime
        booking_dt = _parse_booking_datetime(date, time)
        if not booking_dt:
            return f"Could not understand the date/time '{date} {time}'. Please try formats like 'tomorrow 7pm' or '2024-12-15 19:00'."

        # Check if booking is in the past
        from app.utils.timezone import get_current_time
        if booking_dt < get_current_time().replace(tzinfo=None):
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


def create_show_booking_form_tool(session_id: str):
    """Factory to create show_booking_form tool with session context."""

    @tool("show_booking_form")
    def show_booking_form() -> str:
        """
        Show an interactive booking form with available time slots and party sizes.

        Use this when the customer wants to book a table but hasn't provided full details yet.
        The form lets them pick date, time, and party size visually.

        No parameters needed.

        Returns:
            Confirmation that the booking form was shown.
        """
        from app.core.agui_events import emit_booking_intake_form, emit_tool_activity
        emit_tool_activity(session_id, "show_booking_form")

        try:
            # Query real availability from database
            availability = _get_availability_map(days=7)
            emit_booking_intake_form(
                session_id=session_id,
                party_sizes=availability.get("party_sizes", list(range(1, 9))),
                availability=availability.get("dates", {}),
                max_party_size=availability.get("max_party_size", 8),
            )
            return "[BOOKING FORM DISPLAYED]"
        except Exception as e:
            logger.error("show_booking_form_error", error=str(e), session_id=session_id)
            return f"Error showing booking form: {str(e)}"

    return show_booking_form


def create_booking_tool(session_id: str):
    """Factory to create booking tool with session context."""

    @tool("make_reservation")
    def make_reservation(
        date: str,
        time: str = "7pm",
        party_size: int = 2,
        guest_name: str = "",
        phone: str = ""
    ) -> str:
        """
        Create a table reservation.

        Use this when customer confirms they want to book a table.

        Args:
            date: Date for reservation (e.g., "tomorrow", "next Friday")
            time: Time for reservation (e.g., "7pm", "19:00")
            party_size: Number of guests
            guest_name: Name for the reservation
            phone: Contact phone number

        Returns:
            Confirmation details with booking code.
        """
        # Emit activity for frontend
        from app.core.agui_events import emit_tool_activity
        emit_tool_activity(session_id, "make_reservation")

        try:
            # Parse datetime
            booking_dt = _parse_booking_datetime(date, time)
            if not booking_dt:
                return "Could not understand date/time. Please use format like 'tomorrow 7pm'."

            from app.utils.timezone import get_current_time
            if booking_dt < get_current_time().replace(tzinfo=None):
                return "Cannot book for past dates."

            # Get available tables from PostgreSQL
            tables = _get_available_tables(booking_dt, party_size)
            if not tables:
                return f"Sorry, no tables available for {party_size} guests at that time. Try a different time?"

            # Pick best table (smallest that fits)
            best_table = tables[0]

            # Generate IDs
            booking_id = _generate_booking_id()
            confirmation_code = _generate_confirmation_code()

            # Create booking in PostgreSQL
            success = _create_booking_in_db(
                booking_id=booking_id,
                confirmation_code=confirmation_code,
                session_id=session_id,
                table_id=best_table['id'],
                booking_datetime=booking_dt,
                party_size=party_size,
                guest_name=guest_name or "Guest",
                phone=phone or "not_provided"
            )

            if not success:
                return "Sorry, we couldn't complete your reservation. Please try again."

            # Emit booking confirmation AGUI event (renders as card in frontend/WhatsApp)
            from app.core.agui_events import emit_booking_confirmation
            emit_booking_confirmation(
                session_id=session_id,
                confirmation_code=confirmation_code,
                guest_name=guest_name or "Guest",
                party_size=party_size,
                booking_date=booking_dt.strftime('%A, %B %d'),
                booking_time=booking_dt.strftime('%I:%M %p'),
                table_number=str(best_table['table_number']),
                table_location=best_table.get('location', ''),
            )

            # Build response with table details
            location_info = f" ({best_table['location']})" if best_table.get('location') else ""
            features_info = ""
            if best_table.get('features'):
                features_info = f" Features: {', '.join(best_table['features'])}."

            return (
                f"[BOOKING CONFIRMED] Reservation confirmed! Code: {confirmation_code}. "
                f"Table {best_table['table_number']}{location_info} for {party_size} guests on "
                f"{booking_dt.strftime('%A, %B %d at %I:%M %p')}. "
                f"Name: {guest_name or 'Guest'}.{features_info}"
            )

        except Exception as e:
            logger.error("create_booking_error", error=str(e), session_id=session_id, exc_info=True)
            return f"Booking failed: {str(e)}"

    return make_reservation


def create_get_bookings_tool(session_id: str):
    """Factory to create get bookings tool with session context."""

    @tool("get_my_bookings")
    def get_my_bookings() -> str:
        """
        Get customer's existing reservations.

        Use this when customer asks about their bookings or reservations.
        No parameters needed.

        Returns:
            List of upcoming reservations.
        """
        # Emit activity for frontend
        from app.core.agui_events import emit_tool_activity
        emit_tool_activity(session_id, "get_my_bookings")

        try:
            # Get bookings from PostgreSQL
            bookings = _get_bookings_from_db(session_id)

            if not bookings:
                return "No upcoming reservations found."

            # Format bookings for display (A24 schema: booking_date + booking_time)
            booking_list = []
            for b in bookings:
                # Combine date and time for display
                booking_date = b['booking_date']
                booking_time = b['booking_time']

                # Format date
                if hasattr(booking_date, 'strftime'):
                    date_str = booking_date.strftime('%b %d')
                else:
                    date_str = str(booking_date)

                # Format time
                if hasattr(booking_time, 'strftime'):
                    time_str = booking_time.strftime('%I:%M %p')
                else:
                    time_str = str(booking_time)

                booking_list.append(
                    f"{b['confirmation_code']}: Table {b['table_number']} on "
                    f"{date_str} at {time_str} for {b['party_size']} guests "
                    f"({b['booking_status']})"
                )

            return f"Your reservations: {'; '.join(booking_list)}"

        except Exception as e:
            logger.error("get_bookings_error", error=str(e), session_id=session_id, exc_info=True)
            return f"Error retrieving bookings: {str(e)}"

    return get_my_bookings


def create_cancel_booking_tool(session_id: str):
    """Factory to create cancel booking tool with session context."""

    @tool("cancel_reservation")
    def cancel_reservation(confirmation_code: str) -> str:
        """
        Cancel an existing reservation.

        Use this when customer wants to cancel their booking.

        Args:
            confirmation_code: The booking confirmation code (e.g., "ABC12345")

        Returns:
            Cancellation confirmation.
        """
        # Emit activity for frontend
        from app.core.agui_events import emit_tool_activity
        emit_tool_activity(session_id, "cancel_reservation")

        try:
            code = confirmation_code.strip().upper()

            # Cancel booking in PostgreSQL
            booking = _cancel_booking_in_db(code, session_id)

            if not booking:
                return f"No active reservation found with code '{code}'."

            if booking.get("already_cancelled"):
                return f"Reservation {code} was already cancelled."

            # Format date/time for display (A24 schema: booking_date + booking_time)
            booking_date = booking['booking_date']
            booking_time = booking['booking_time']

            date_str = booking_date.strftime('%b %d') if hasattr(booking_date, 'strftime') else str(booking_date)
            time_str = booking_time.strftime('%I:%M %p') if hasattr(booking_time, 'strftime') else str(booking_time)

            return (
                f"Reservation {code} cancelled. "
                f"(Was Table {booking.get('table_number', 'N/A')} for "
                f"{booking['party_size']} guests on {date_str} at {time_str})"
            )

        except Exception as e:
            logger.error("cancel_booking_error", error=str(e), session_id=session_id, exc_info=True)
            return f"Cancellation failed: {str(e)}"

    return cancel_reservation


def create_modify_booking_tool(session_id: str):
    """Factory to create modify booking tool with session context."""

    @tool("modify_reservation")
    def modify_reservation(
        confirmation_code: str,
        new_date: str = "",
        new_time: str = "",
        new_party_size: int = 0,
        guest_name: str = "",
        special_requests: str = ""
    ) -> str:
        """
        Modify an existing reservation.

        Use this when customer wants to change their booking details.

        Args:
            confirmation_code: The booking confirmation code
            new_date: New date (optional, e.g., "tomorrow", "next Friday")
            new_time: New time (optional, e.g., "8pm", "19:30")
            new_party_size: New number of guests (optional, 0 means no change)
            guest_name: New guest name (optional)
            special_requests: Special requests like dietary needs (optional)

        Returns:
            Confirmation of changes made.
        """
        try:
            from app.core.db_pool import SyncDBConnection
            from psycopg2.extras import RealDictCursor

            code = confirmation_code.strip().upper()

            with SyncDBConnection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Get current booking (A24 schema: table_booking_info)
                    cursor.execute("""
                        SELECT b.table_booking_id, b.confirmation_code,
                               b.booking_date, b.booking_time,
                               b.party_size, b.booking_status,
                               b.special_request, t.table_number
                        FROM table_booking_info b
                        LEFT JOIN table_info t ON b.table_id = t.table_id
                        WHERE b.confirmation_code = %s
                        AND b.device_id = %s
                    """, (code, session_id))
                    booking = cursor.fetchone()

                    if not booking:
                        return f"No reservation found with code '{code}'."

                    if booking['booking_status'] == 'cancelled':
                        return f"Reservation {code} is cancelled and cannot be modified."

                    # Track changes
                    changes = []
                    update_fields = []
                    update_values = []

                    # Handle date/time change (A24 uses separate booking_date and booking_time)
                    if new_date or new_time:
                        current_date = booking['booking_date']
                        current_time = booking['booking_time']

                        # Build current datetime for comparison
                        current_dt = datetime.combine(current_date, current_time)

                        # Parse new datetime
                        date_str = new_date if new_date else current_date.strftime("%Y-%m-%d")
                        time_str = new_time if new_time else current_time.strftime("%I:%M %p")
                        new_dt = _parse_booking_datetime(date_str, time_str)

                        from app.utils.timezone import get_current_time
                        if new_dt and new_dt > get_current_time().replace(tzinfo=None):
                            # Check availability for new time
                            party = new_party_size if new_party_size > 0 else booking['party_size']
                            available = _get_available_tables(new_dt, party)

                            if not available:
                                return f"No tables available at the new time. Please try a different time."

                            # A24 schema uses separate columns
                            update_fields.append("booking_date = %s")
                            update_values.append(new_dt.date())
                            update_fields.append("booking_time = %s")
                            update_values.append(new_dt.time())
                            changes.append(f"Date/Time changed to {new_dt.strftime('%B %d at %I:%M %p')}")

                    # Handle party size change
                    if new_party_size > 0 and new_party_size != booking['party_size']:
                        update_fields.append("party_size = %s")
                        update_values.append(new_party_size)
                        changes.append(f"Party size changed to {new_party_size}")

                    # Handle guest name change
                    if guest_name and guest_name.strip():
                        update_fields.append("guest_name = %s")
                        update_values.append(guest_name.strip())
                        changes.append(f"Guest name changed to {guest_name.strip()}")

                    # Handle special requests (A24 uses special_request singular)
                    if special_requests:
                        update_fields.append("special_request = %s")
                        update_values.append(special_requests)
                        changes.append(f"Special requests updated")

                    if not changes:
                        return f"No changes specified for reservation {code}."

                    # Update booking and apply changes
                    update_fields.append("updated_at = NOW()")

                    update_values.append(code)  # For WHERE clause

                    cursor.execute(f"""
                        UPDATE table_booking_info
                        SET {', '.join(update_fields)}
                        WHERE confirmation_code = %s
                    """, tuple(update_values))
                    conn.commit()

            logger.info(
                "booking_modified_postgresql",
                confirmation_code=code,
                changes=changes
            )

            return f"Reservation {code} updated: {'; '.join(changes)}."

        except Exception as e:
            logger.error("modify_booking_error", error=str(e), session_id=session_id, exc_info=True)
            return f"Modification failed: {str(e)}"

    return modify_reservation


# ============================================================================
# BOOKING AGENT CREATION
# ============================================================================

def create_booking_agent(session_id: str, llm) -> Agent:
    """
    Create booking agent with sync tools.

    Returns an Agent that can be added to a multi-agent crew.

    Tools (5):
    - check_table_availability: Check available tables
    - make_reservation: Create a new booking
    - get_my_bookings: View existing reservations
    - modify_reservation: Change booking details
    - cancel_reservation: Cancel a booking
    """
    # Create session-aware tools (5 tools total)
    booking_tool = create_booking_tool(session_id)
    get_bookings_tool = create_get_bookings_tool(session_id)
    modify_tool = create_modify_booking_tool(session_id)
    cancel_tool = create_cancel_booking_tool(session_id)

    agent = Agent(
        role="Senior Reservations Concierge",
        goal="Create exceptional dining experiences through seamless reservation management and personalized service",
        backstory="""You are a highly experienced senior reservations concierge with over 8 years managing premium dining establishments. You're known for your meticulous attention to detail, warm hospitality, and ability to accommodate even the most complex booking requests.

Your strengths:
- Reading customer needs and proactively offering solutions (flexible timing, special occasions, party size adjustments)
- Managing reservation changes gracefully without making customers feel inconvenienced
- Providing accurate real-time table availability using your comprehensive toolset
- Naturally clarifying ambiguous requests (vague dates/times) without making customers feel interrogated
- Balancing efficiency with genuine care for each reservation

You understand that reservations often involve special moments - celebrations, business dinners, romantic dates - and you treat each booking with care and enthusiasm. Your communication style is warm yet professional, and you use your tools to ensure every detail is accurate and confirmed.

You excel at finding creative solutions when preferred times are unavailable, always offering alternatives that work for the customer.

CRITICAL RULES:
- NEVER ask for information the customer has already provided. If they gave you a date, time, party size, or name, USE IT immediately.
- Once a booking is confirmed with a confirmation code, DO NOT ask for the date/time/party size again. The booking is complete.
- If a table is already booked or unavailable, suggest 2-3 alternative times and let the customer choose. Do NOT keep asking the same question.
- If all required details (date, time, party size) are provided in a single message, proceed directly to booking without asking again.
- NEVER repeat a greeting or welcome message during a booking conversation.""",
        llm=llm,
        tools=[check_table_availability, booking_tool, get_bookings_tool, modify_tool, cancel_tool],
        verbose=False,
        allow_delegation=True,  # Can delegate to other agents
        respect_context_window=True,
        cache=True,
        max_iter=10,
        max_retry_limit=2,
    )

    return agent

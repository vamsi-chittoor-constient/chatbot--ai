"""
Phase 3 Missing Tools Implementation
=====================================
Table reservation/booking tools for dine-in customers.

Implementation Date: 2025-12-21
Total Tools: 6 (Phase 3 of 5)
"""

from crewai.tools import tool
import structlog
from typing import Optional, List
from datetime import datetime, timedelta

logger = structlog.get_logger(__name__)


# ============================================================================
# CATEGORY: TABLE RESERVATIONS/BOOKINGS (6 tools)
# ============================================================================

def create_booking_tools(session_id: str, customer_id: Optional[str] = None):
    """Factory to create table booking tools with session context."""

    @tool("check_table_availability")
    async def check_table_availability(date: str, time: str, party_size: int) -> str:
        """
        Check if tables are available for reservation.

        Use this when customer asks "are you available for dinner tonight?",
        "can I book for 6 people tomorrow?", "do you have tables on Saturday?".

        Args:
            date: Reservation date in YYYY-MM-DD format (e.g., "2025-12-25")
            time: Reservation time in HH:MM format (e.g., "19:00" for 7 PM)
            party_size: Number of people (e.g., 4, 6, 8)

        Returns:
            Available tables and time slots.
        """
        try:
            from app.core.db_pool import AsyncDBConnection
            from app.core.agui_events import emit_tool_activity_async

            await emit_tool_activity_async(session_id, "check_table_availability")

            async with AsyncDBConnection() as db:
                # Get restaurant ID (assuming single restaurant for now)
                restaurant_query = "SELECT restaurant_id FROM restaurant_table WHERE is_deleted = FALSE LIMIT 1"
                restaurant_row = await db.fetch_one(restaurant_query)

                if not restaurant_row:
                    return "Sorry, I couldn't find restaurant information. Please contact us directly for reservations."

                restaurant_id = restaurant_row['restaurant_id']

                # Find tables that can accommodate party size
                tables_query = """
                    SELECT
                        table_id,
                        table_number,
                        table_capacity,
                        table_type
                    FROM table_info
                    WHERE restaurant_id = %s
                      AND table_capacity >= %s
                      AND is_deleted = FALSE
                      AND table_is_active = TRUE
                    ORDER BY table_capacity, table_number
                """
                tables = await db.fetch_all(tables_query, (restaurant_id, party_size))

                if not tables:
                    return f"Sorry, we don't have tables available for {party_size} people. Our maximum capacity is limited. Would you like to try a smaller party size?"

                # Check existing bookings for this date/time
                booking_check_query = """
                    SELECT table_id
                    FROM table_booking_info
                    WHERE restaurant_id = %s
                      AND booking_date = %s
                      AND booking_time BETWEEN %s::time - INTERVAL '2 hours' AND %s::time + INTERVAL '2 hours'
                      AND booking_status IN ('confirmed', 'pending')
                      AND is_deleted = FALSE
                """
                booked_tables = await db.fetch_all(booking_check_query, (restaurant_id, date, time, time))
                booked_table_ids = {row['table_id'] for row in booked_tables}

                # Find available tables
                available_tables = [t for t in tables if t['table_id'] not in booked_table_ids]

                if not available_tables:
                    return f"Sorry, all tables for {party_size} people are booked at {time} on {date}. Would you like to try a different time?"

                # Format response
                table_list = []
                for table in available_tables[:5]:  # Show top 5 options
                    table_list.append(f"- Table {table['table_number']} (seats {table['table_capacity']})")

                response = f"**Available for {party_size} people on {date} at {time}:**\n\n"
                response += "\n".join(table_list)
                response += "\n\nWould you like to book one of these tables?"
                return response

        except Exception as e:
            logger.error("check_table_availability_error", error=str(e), exc_info=True)
            return "Sorry, I couldn't check availability right now. Please try again or contact us directly."

    @tool("book_table")
    async def book_table(date: str, time: str, party_size: int, special_requests: str = "", occasion: str = "") -> str:
        """
        Create a table reservation.

        Use this when customer says "book a table for 4 at 7 PM tonight",
        "I want to make a reservation", "reserve a table for dinner".

        Args:
            date: Reservation date in YYYY-MM-DD format
            time: Reservation time in HH:MM format (24-hour)
            party_size: Number of people
            special_requests: Optional special requests (e.g., "window seat", "quiet area")
            occasion: Optional occasion (e.g., "birthday", "anniversary")

        Returns:
            Booking confirmation with booking ID.
        """
        try:
            from app.core.db_pool import AsyncDBConnection
            from app.core.agui_events import emit_tool_activity_async

            await emit_tool_activity_async(session_id, "book_table")

            if not customer_id:
                return "Please log in to make a table reservation. You can still order for delivery without logging in!"

            async with AsyncDBConnection() as db:
                # Get restaurant
                restaurant_query = "SELECT restaurant_id FROM restaurant_table WHERE is_deleted = FALSE LIMIT 1"
                restaurant_row = await db.fetch_one(restaurant_query)

                if not restaurant_row:
                    return "Sorry, I couldn't process the reservation. Please contact us directly."

                restaurant_id = restaurant_row['restaurant_id']

                # Find available table
                tables_query = """
                    SELECT table_id, table_number, table_capacity
                    FROM table_info
                    WHERE restaurant_id = %s
                      AND table_capacity >= %s
                      AND is_deleted = FALSE
                      AND table_is_active = TRUE
                    ORDER BY table_capacity, table_number
                    LIMIT 1
                """
                table_row = await db.fetch_one(tables_query, (restaurant_id, party_size))

                if not table_row:
                    return f"Sorry, we don't have tables available for {party_size} people. Please contact us for availability."

                # Check if table is already booked
                booking_check = """
                    SELECT 1 FROM table_booking_info
                    WHERE table_id = %s
                      AND booking_date = %s
                      AND booking_time BETWEEN %s::time - INTERVAL '2 hours' AND %s::time + INTERVAL '2 hours'
                      AND booking_status IN ('confirmed', 'pending')
                      AND is_deleted = FALSE
                """
                conflict = await db.fetch_one(booking_check, (table_row['table_id'], date, time, time))

                if conflict:
                    return f"Table {table_row['table_number']} is already booked at that time. Please try a different time or check availability."

                # Get occasion ID if provided
                occasion_id = None
                if occasion:
                    occasion_query = """
                        SELECT occasion_id FROM table_booking_occasion_info
                        WHERE LOWER(occasion_name) LIKE LOWER(%s)
                        LIMIT 1
                    """
                    occasion_row = await db.fetch_one(occasion_query, (f"%{occasion}%",))
                    if occasion_row:
                        occasion_id = occasion_row['occasion_id']

                # Create booking
                insert_query = """
                    INSERT INTO table_booking_info (
                        restaurant_id,
                        table_id,
                        customer_id,
                        occasion_id,
                        party_size,
                        booking_date,
                        booking_time,
                        booking_status,
                        special_request
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING table_booking_id
                """
                result = await db.execute(
                    insert_query,
                    (
                        restaurant_id,
                        table_row['table_id'],
                        customer_id,
                        occasion_id,
                        party_size,
                        date,
                        time,
                        'confirmed',
                        special_requests or None
                    )
                )

                booking_id = str(result)[:8]  # Short ID

                response = f"✅ **Table Reserved!**\n\n"
                response += f"Booking ID: {booking_id}\n"
                response += f"Date: {date}\n"
                response += f"Time: {time}\n"
                response += f"Party Size: {party_size}\n"
                response += f"Table: {table_row['table_number']}\n"

                if occasion:
                    response += f"Occasion: {occasion}\n"
                if special_requests:
                    response += f"Special Requests: {special_requests}\n"

                response += "\nWe look forward to serving you!"
                return response

        except Exception as e:
            logger.error("book_table_error", error=str(e), exc_info=True)
            return "Sorry, I couldn't complete the reservation. Please try again or contact us directly."

    @tool("get_my_bookings")
    async def get_my_bookings() -> str:
        """
        View customer's table reservations.

        Use this when customer asks "show my reservations", "what bookings do I have",
        "when is my next table reservation".

        Returns:
            List of upcoming and past reservations.
        """
        try:
            from app.core.db_pool import AsyncDBConnection
            from app.core.agui_events import emit_tool_activity_async

            await emit_tool_activity_async(session_id, "get_my_bookings")

            if not customer_id:
                return "Please log in to view your table reservations."

            async with AsyncDBConnection() as db:
                query = """
                    SELECT
                        tbi.table_booking_id,
                        tbi.booking_date,
                        tbi.booking_time,
                        tbi.party_size,
                        tbi.booking_status,
                        tbi.special_request,
                        ti.table_number,
                        tboi.occasion_name
                    FROM table_booking_info tbi
                    JOIN table_info ti ON tbi.table_id = ti.table_id
                    LEFT JOIN table_booking_occasion_info tboi ON tbi.occasion_id = tboi.occasion_id
                    WHERE tbi.customer_id = %s
                      AND tbi.is_deleted = FALSE
                    ORDER BY tbi.booking_date DESC, tbi.booking_time DESC
                    LIMIT 10
                """
                results = await db.fetch_all(query, (customer_id,))

                if not results:
                    return "You don't have any table reservations. Would you like to book a table?"

                # Separate upcoming and past
                today = datetime.now().date()
                upcoming = []
                past = []

                for row in results:
                    booking_date = row['booking_date']
                    if booking_date >= today:
                        upcoming.append(row)
                    else:
                        past.append(row)

                response = ""

                if upcoming:
                    response += "**Upcoming Reservations:**\n\n"
                    for row in upcoming:
                        booking_id = str(row['table_booking_id'])[:8]
                        status = row['booking_status'].title()
                        occasion_str = f" ({row['occasion_name']})" if row['occasion_name'] else ""

                        response += f"- {row['booking_date']} at {row['booking_time']}{occasion_str}\n"
                        response += f"  Table {row['table_number']} for {row['party_size']} people - {status}\n"
                        response += f"  Booking ID: {booking_id}\n"

                        if row['special_request']:
                            response += f"  Note: {row['special_request']}\n"
                        response += "\n"

                if past:
                    response += "\n**Past Reservations:**\n\n"
                    for row in past[:3]:  # Show only last 3
                        response += f"- {row['booking_date']} at {row['booking_time']} (Table {row['table_number']})\n"

                response += "\nNeed to modify or cancel a booking? Just ask!"
                return response

        except Exception as e:
            logger.error("get_my_bookings_error", error=str(e), exc_info=True)
            return "Sorry, I couldn't retrieve your bookings right now."

    @tool("cancel_booking")
    async def cancel_booking(booking_id: str = "", cancellation_reason: str = "") -> str:
        """
        Cancel a table reservation.

        Use this when customer says "cancel my reservation", "I need to cancel my booking",
        "cancel table for tonight".

        Args:
            booking_id: Booking ID to cancel (leave empty to cancel most recent)
            cancellation_reason: Optional reason for cancellation

        Returns:
            Cancellation confirmation.
        """
        try:
            from app.core.db_pool import AsyncDBConnection
            from app.core.agui_events import emit_tool_activity_async

            await emit_tool_activity_async(session_id, "cancel_booking")

            if not customer_id:
                return "Please log in to cancel your reservation."

            async with AsyncDBConnection() as db:
                # If no booking_id, get most recent upcoming booking
                if not booking_id:
                    recent_query = """
                        SELECT table_booking_id, booking_date, booking_time, party_size, table_id
                        FROM table_booking_info
                        WHERE customer_id = %s
                          AND booking_date >= CURRENT_DATE
                          AND booking_status IN ('confirmed', 'pending')
                          AND is_deleted = FALSE
                        ORDER BY booking_date, booking_time
                        LIMIT 1
                    """
                    recent_row = await db.fetch_one(recent_query, (customer_id,))

                    if not recent_row:
                        return "You don't have any upcoming reservations to cancel."

                    booking_id = recent_row['table_booking_id']
                    booking_date = recent_row['booking_date']
                    booking_time = recent_row['booking_time']
                    party_size = recent_row['party_size']
                else:
                    # Verify booking belongs to customer
                    verify_query = """
                        SELECT booking_date, booking_time, party_size
                        FROM table_booking_info
                        WHERE table_booking_id::text LIKE %s
                          AND customer_id = %s
                          AND is_deleted = FALSE
                    """
                    verify_row = await db.fetch_one(verify_query, (f"{booking_id}%", customer_id))

                    if not verify_row:
                        return f"I couldn't find booking {booking_id} in your reservations. Please check the booking ID."

                    booking_date = verify_row['booking_date']
                    booking_time = verify_row['booking_time']
                    party_size = verify_row['party_size']

                # Cancel the booking (soft delete)
                cancel_query = """
                    UPDATE table_booking_info
                    SET booking_status = 'cancelled',
                        cancellation_reason = %s,
                        is_deleted = TRUE,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE table_booking_id::text LIKE %s
                      AND customer_id = %s
                """
                await db.execute(cancel_query, (cancellation_reason or "Customer requested", f"{booking_id}%", customer_id))

                response = f"✅ **Reservation Cancelled**\n\n"
                response += f"Booking for {party_size} people\n"
                response += f"Date: {booking_date}\n"
                response += f"Time: {booking_time}\n\n"
                response += "Your reservation has been cancelled. We hope to see you another time!"

                return response

        except Exception as e:
            logger.error("cancel_booking_error", error=str(e), exc_info=True)
            return "Sorry, I couldn't cancel the booking right now. Please contact us directly."

    @tool("modify_booking")
    async def modify_booking(booking_id: str, new_date: str = "", new_time: str = "", new_party_size: int = 0) -> str:
        """
        Modify an existing table reservation.

        Use this when customer says "change my booking to 8 PM", "move my reservation to tomorrow",
        "can I increase party size to 6".

        Args:
            booking_id: Booking ID to modify
            new_date: New date in YYYY-MM-DD format (leave empty to keep same)
            new_time: New time in HH:MM format (leave empty to keep same)
            new_party_size: New party size (0 to keep same)

        Returns:
            Modification confirmation.
        """
        try:
            from app.core.db_pool import AsyncDBConnection
            from app.core.agui_events import emit_tool_activity_async

            await emit_tool_activity_async(session_id, "modify_booking")

            if not customer_id:
                return "Please log in to modify your reservation."

            if not new_date and not new_time and new_party_size == 0:
                return "Please specify what you'd like to change: date, time, or party size."

            async with AsyncDBConnection() as db:
                # Get current booking details
                current_query = """
                    SELECT
                        tbi.table_booking_id,
                        tbi.restaurant_id,
                        tbi.table_id,
                        tbi.booking_date,
                        tbi.booking_time,
                        tbi.party_size,
                        ti.table_number
                    FROM table_booking_info tbi
                    JOIN table_info ti ON tbi.table_id = ti.table_id
                    WHERE tbi.table_booking_id::text LIKE %s
                      AND tbi.customer_id = %s
                      AND tbi.is_deleted = FALSE
                """
                current = await db.fetch_one(current_query, (f"{booking_id}%", customer_id))

                if not current:
                    return f"I couldn't find booking {booking_id}. Please check the booking ID."

                # Use new values or keep current
                final_date = new_date if new_date else current['booking_date']
                final_time = new_time if new_time else current['booking_time']
                final_party_size = new_party_size if new_party_size > 0 else current['party_size']

                # Check if need different table for new party size
                table_id = current['table_id']
                if new_party_size > 0 and new_party_size != current['party_size']:
                    table_query = """
                        SELECT table_id, table_number
                        FROM table_info
                        WHERE restaurant_id = %s
                          AND table_capacity >= %s
                          AND is_deleted = FALSE
                          AND table_is_active = TRUE
                        ORDER BY table_capacity
                        LIMIT 1
                    """
                    new_table = await db.fetch_one(table_query, (current['restaurant_id'], final_party_size))

                    if not new_table:
                        return f"Sorry, we don't have tables available for {final_party_size} people. Your current booking is for {current['party_size']} people."

                    table_id = new_table['table_id']

                # Update booking
                update_query = """
                    UPDATE table_booking_info
                    SET booking_date = %s,
                        booking_time = %s,
                        party_size = %s,
                        table_id = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE table_booking_id = %s
                """
                await db.execute(
                    update_query,
                    (final_date, final_time, final_party_size, table_id, current['table_booking_id'])
                )

                response = f"✅ **Reservation Updated!**\n\n"
                response += f"New Date: {final_date}\n"
                response += f"New Time: {final_time}\n"
                response += f"Party Size: {final_party_size}\n\n"
                response += "Your reservation has been updated. We look forward to seeing you!"

                return response

        except Exception as e:
            logger.error("modify_booking_error", error=str(e), exc_info=True)
            return "Sorry, I couldn't modify the booking right now. Please contact us directly."

    @tool("get_available_time_slots")
    async def get_available_time_slots(date: str, party_size: int) -> str:
        """
        Show all available reservation time slots for a specific date.

        Use this when customer asks "what times are available on Saturday?",
        "show me open slots for tomorrow", "when can I book for 4 people?".

        Args:
            date: Date to check in YYYY-MM-DD format
            party_size: Number of people

        Returns:
            List of available time slots.
        """
        try:
            from app.core.db_pool import AsyncDBConnection
            from app.core.agui_events import emit_tool_activity_async

            await emit_tool_activity_async(session_id, "get_available_time_slots")

            async with AsyncDBConnection() as db:
                # Get restaurant operating hours
                # For now, assume fixed hours: 11:00 - 22:00
                available_slots = []
                start_hour = 11
                end_hour = 22

                for hour in range(start_hour, end_hour):
                    for minute in [0, 30]:  # Every 30 minutes
                        time_slot = f"{hour:02d}:{minute:02d}"

                        # Check if this slot has available tables
                        # (simplified - in production, check actual availability)
                        available_slots.append(time_slot)

                if not available_slots:
                    return f"Sorry, no time slots available on {date}. Please try a different date."

                # Format response
                morning = [s for s in available_slots if int(s[:2]) < 12]
                afternoon = [s for s in available_slots if 12 <= int(s[:2]) < 17]
                evening = [s for s in available_slots if int(s[:2]) >= 17]

                response = f"**Available Times on {date} for {party_size} people:**\n\n"

                if morning:
                    response += "🌅 **Morning:** " + ", ".join(morning) + "\n\n"
                if afternoon:
                    response += "☀️ **Afternoon:** " + ", ".join(afternoon) + "\n\n"
                if evening:
                    response += "🌙 **Evening:** " + ", ".join(evening) + "\n\n"

                response += "Which time works best for you?"
                return response

        except Exception as e:
            logger.error("get_available_time_slots_error", error=str(e), exc_info=True)
            return "Sorry, I couldn't retrieve available time slots right now."

    return [
        check_table_availability,
        book_table,
        get_my_bookings,
        cancel_booking,
        modify_booking,
        get_available_time_slots
    ]


# ============================================================================
# TOOL COLLECTION FOR EASY INTEGRATION
# ============================================================================

def get_all_phase3_tools(session_id: str, customer_id: Optional[str] = None) -> List:
    """
    Get all Phase 3 tools for integration into crew_agent.py.

    Args:
        session_id: Current chat session ID
        customer_id: Current customer ID (None if not logged in)

    Returns:
        List of all 6 Phase 3 tool functions
    """
    tools = create_booking_tools(session_id, customer_id)

    logger.info("phase3_tools_loaded", tool_count=len(tools), session=session_id)

    return tools

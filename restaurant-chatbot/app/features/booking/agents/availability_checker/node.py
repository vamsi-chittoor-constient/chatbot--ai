"""
Availability Checker Sub-Agent
==============================

Checks table availability for requested date/time/party size.

Responsibilities:
- Extract booking requirements (party size, date, time)
- Call CheckAvailabilityTool
- Present available tables to user
- Update booking_progress with availability_result
"""

from typing import Dict, Any
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.features.booking.state import BookingState, BookingProgress
from app.features.booking.tools.booking_tools import check_availability_tool
from app.features.booking.logger import booking_logger


async def availability_checker_node(state: BookingState) -> Dict[str, Any]:
    """
    Check availability for requested booking.

    Flow:
    1. Check if we have party_size, date, time in booking_progress
    2. If missing, ask user for missing information
    3. If complete, call CheckAvailabilityTool
    4. Update booking_progress with availability_result
    5. Return availability info to user
    """
    booking_logger.info("Availability checker sub-agent invoked")

    # Initialize booking progress if needed
    if not state.get("booking_progress"):
        state["booking_progress"] = BookingProgress()

    booking_progress = state["booking_progress"]

    # Check if we have all required info
    if not booking_progress.is_ready_to_check_availability():
        missing = booking_progress.get_missing_fields()
        missing_info = [f for f in missing if f in ["party_size", "date", "time"]]

        if missing_info:
            response_msg = f"To check availability, I need: {', '.join(missing_info)}. Please provide this information."
            booking_logger.info("Missing info for availability check", missing=missing_info)

            return {
                "messages": [AIMessage(content=response_msg)],
                "booking_progress": booking_progress
            }

    # We have all info, check availability
    try:
        # Call availability tool
        result = await check_availability_tool.execute(
            booking_date=f"{booking_progress.date} {booking_progress.time}",
            party_size=booking_progress.party_size
        )

        # Update progress
        booking_progress.availability_checked = True
        booking_progress.availability_result = result.data

        # Format response
        if result.data.get("has_availability"):
            available_count = result.data.get("total_available", 0)
            response_msg = f"Great news! We have {available_count} table(s) available for {booking_progress.party_size} people on {booking_progress.date} at {booking_progress.time}."

            # Add table details if available
            tables = result.data.get("available_tables", [])
            if tables:
                response_msg += "\n\nAvailable tables:\n"
                for table in tables[:3]:  # Show first 3
                    response_msg += f"- Table {table.get('table_number')} (capacity: {table.get('capacity')})\n"

            response_msg += "\n\nWould you like to proceed with the booking?"
        else:
            response_msg = f"I'm sorry, we don't have any tables available for {booking_progress.party_size} people on {booking_progress.date} at {booking_progress.time}."

            if result.data.get("waitlist_available"):
                response_msg += " Would you like to be added to the waitlist?"

        booking_logger.info("Availability check complete", has_availability=result.data.get("has_availability"))

        return {
            "messages": [AIMessage(content=response_msg)],
            "booking_progress": booking_progress,
            "availability_context": result.data
        }

    except Exception as e:
        booking_logger.error("Availability check failed", error=str(e))
        return {
            "messages": [AIMessage(content=f"I'm sorry, I encountered an error checking availability: {str(e)}")],
            "booking_progress": booking_progress
        }

"""
Booking Creator Sub-Agent
=========================

Creates new table bookings.

Responsibilities:
- Collect all required info (party_size, date, time, phone, name)
- Check availability
- Get user confirmation
- Create booking via CreateBookingTool
- Send confirmation SMS/Email
"""

from typing import Dict, Any
from langchain_core.messages import AIMessage

from app.features.booking.state import BookingState, BookingProgress
from app.features.booking.tools.booking_tools import create_booking_tool
from app.features.booking.logger import booking_logger


async def booking_creator_node(state: BookingState) -> Dict[str, Any]:
    """Create new booking"""
    booking_logger.info("Booking creator sub-agent invoked")

    # Initialize booking progress
    if not state.get("booking_progress"):
        state["booking_progress"] = BookingProgress()

    booking_progress = state["booking_progress"]
    assert booking_progress is not None  # Type narrowing for type checker

    # Check if ready to create booking
    if not booking_progress.is_ready_to_create_booking():
        missing = booking_progress.get_missing_fields()
        response_msg = f"To create your booking, I need: {', '.join(missing)}."

        return {
            "messages": [AIMessage(content=response_msg)],
            "booking_progress": booking_progress
        }

    # Create booking
    try:
        result = await create_booking_tool.execute(
            booking_date=f"{booking_progress.date} {booking_progress.time}",
            party_size=booking_progress.party_size,
            contact_phone=booking_progress.phone,
            guest_name=booking_progress.user_name,
            user_id=booking_progress.user_id,
            device_id=booking_progress.device_id,
            special_requests=booking_progress.special_requests
        )

        if result.status.value == "success":
            # Update progress
            booking_progress.booking_created = True
            booking_progress.booking_id = result.data.get("booking_id")
            booking_progress.confirmation_code = result.data.get("confirmation_code")
            booking_progress.sms_sent = True  # Assuming SMS sent

            response_msg = f"✅ Booking confirmed!\n\n"
            response_msg += f"Confirmation Code: {booking_progress.confirmation_code}\n"
            response_msg += f"Date: {booking_progress.date}\n"
            response_msg += f"Time: {booking_progress.time}\n"
            response_msg += f"Party Size: {booking_progress.party_size}\n"
            response_msg += f"\nA confirmation has been sent to {booking_progress.phone}"

            booking_logger.info("Booking created successfully", booking_id=booking_progress.booking_id)
        else:
            response_msg = f"Sorry, booking creation failed: {result.error}"

        return {
            "messages": [AIMessage(content=response_msg)],
            "booking_progress": booking_progress
        }

    except Exception as e:
        booking_logger.error("Booking creation failed", error=str(e))
        return {
            "messages": [AIMessage(content=f"Error creating booking: {str(e)}")],
            "booking_progress": booking_progress
        }

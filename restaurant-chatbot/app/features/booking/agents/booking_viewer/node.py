"""Booking Viewer Sub-Agent - View existing bookings"""

from typing import Dict, Any
from langchain_core.messages import AIMessage
from app.features.booking.state import BookingState
from app.features.booking.tools.booking_tools import get_booking_tool
from app.features.booking.logger import booking_logger


async def booking_viewer_node(state: BookingState) -> Dict[str, Any]:
    """View bookings"""
    booking_logger.info("Booking viewer sub-agent invoked")

    booking_progress = state.get("booking_progress")
    user_id = booking_progress.user_id if booking_progress else state.get("user_id")
    phone = booking_progress.phone if booking_progress else state.get("user_phone")

    try:
        result = await get_booking_tool.execute(
            user_id=user_id,
            phone=phone
        )

        if result.data.get("found"):
            bookings = result.data.get("bookings", [])
            response_msg = f"You have {len(bookings)} booking(s):\n\n"
            for booking in bookings:
                response_msg += f"• {booking.get('booking_date')} - Party of {booking.get('party_size')}\n"
                response_msg += f"  Confirmation: {booking.get('confirmation_code')}\n\n"
        else:
            response_msg = "You don't have any upcoming bookings."

        return {"messages": [AIMessage(content=response_msg)]}

    except Exception as e:
        booking_logger.error("View bookings failed", error=str(e))
        return {"messages": [AIMessage(content=f"Error viewing bookings: {str(e)}")]}

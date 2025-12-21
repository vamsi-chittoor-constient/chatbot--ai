"""Booking Canceller Sub-Agent - Cancel bookings"""

from typing import Dict, Any
from langchain_core.messages import AIMessage
from app.features.booking.state import BookingState
from app.features.booking.tools.booking_tools import cancel_booking_tool
from app.features.booking.logger import booking_logger


async def booking_canceller_node(state: BookingState) -> Dict[str, Any]:
    """Cancel booking"""
    booking_logger.info("Booking canceller sub-agent invoked")

    booking_id = state.get("target_booking_id")
    if not booking_id:
        return {"messages": [AIMessage(content="Please provide your booking ID or confirmation code to cancel.")]}

    try:
        result = await cancel_booking_tool.execute(
            booking_id=booking_id,
            reason="User requested cancellation"
        )

        if result.data.get("success"):
            response_msg = f"✅ Booking cancelled successfully.\n\n"
            response_msg += f"Confirmation code: {result.data.get('confirmation_code')}\n"
            response_msg += "You will receive a cancellation confirmation."
        else:
            response_msg = f"Cancellation failed: {result.data.get('message')}"

        return {"messages": [AIMessage(content=response_msg)]}

    except Exception as e:
        booking_logger.error("Cancel booking failed", error=str(e))
        return {"messages": [AIMessage(content=f"Error cancelling booking: {str(e)}")]}

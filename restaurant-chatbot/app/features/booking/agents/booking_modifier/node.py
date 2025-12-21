"""Booking Modifier Sub-Agent - Modify existing bookings"""

from typing import Dict, Any
from langchain_core.messages import AIMessage
from app.features.booking.state import BookingState
from app.features.booking.tools.booking_tools import modify_booking_tool
from app.features.booking.logger import booking_logger


async def booking_modifier_node(state: BookingState) -> Dict[str, Any]:
    """Modify booking"""
    booking_logger.info("Booking modifier sub-agent invoked")

    booking_id = state.get("target_booking_id")
    if not booking_id:
        return {"messages": [AIMessage(content="Please provide your booking ID or confirmation code.")]}

    # Extract modifications from state
    modifications = state.get("modification_context", {})

    try:
        result = await modify_booking_tool.execute(
            booking_id=booking_id,
            **modifications
        )

        if result.data.get("success"):
            response_msg = f"✅ Booking modified successfully!\n\n"
            response_msg += f"Modified fields: {', '.join(result.data.get('modified_fields', []))}"
        else:
            response_msg = f"Modification failed: {result.data.get('message')}"

        return {"messages": [AIMessage(content=response_msg)]}

    except Exception as e:
        booking_logger.error("Modify booking failed", error=str(e))
        return {"messages": [AIMessage(content=f"Error modifying booking: {str(e)}")]}

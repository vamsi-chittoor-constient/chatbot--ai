"""
Booking Models
==============

Database models for booking feature, organized as one-file-per-table.

Models (3 tables):
- Booking: Main booking/reservation model
- Waitlist: Waitlist entries when tables unavailable
- AbandonedBooking: Abandoned booking recovery
"""

from app.features.booking.models.booking import Booking
from app.features.booking.models.waitlist import Waitlist
from app.features.booking.models.abandoned_booking import AbandonedBooking

__all__ = [
    "Booking",
    "Waitlist",
    "AbandonedBooking",
]

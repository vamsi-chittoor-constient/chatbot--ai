"""
MealSlotTiming Model
====================
Stores opening and closing times for each meal type (Breakfast, Lunch, Dinner).
Used to determine the current active meal slot based on time of day.
"""

from typing import Optional
from datetime import datetime, time
from uuid import UUID

from app.shared.models.base import (
    Base, func,
    DateTime, Boolean, Time,
    ForeignKey, Index,
    relationship, Mapped, mapped_column
)
from sqlalchemy.dialects.postgresql import UUID as UUID_TYPE
from sqlalchemy.sql import text


class MealSlotTiming(Base):
    """
    Meal slot timing configuration.

    Maps meal types to their operating hours:
    - Breakfast: 06:00 - 11:00
    - Lunch: 11:00 - 16:00
    - Dinner: 16:00 - 23:00
    - All Day: 00:00 - 23:59

    Used by GetCurrentMealSuggestionsTool to determine which meal slot
    is currently active based on the current time.
    """
    __tablename__ = "meal_slot_timing"

    meal_slot_timing_id: Mapped[UUID] = mapped_column(
        UUID_TYPE(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )
    # Note: entity_slot_config table exists in SQL schema but not as a Python model
    # FK constraint removed to allow SQLAlchemy create_all to work
    slot_config_id: Mapped[Optional[UUID]] = mapped_column(
        UUID_TYPE(as_uuid=True),
        nullable=True,
        comment="Optional link to entity slot configuration for booking integration"
    )
    meal_type_id: Mapped[Optional[UUID]] = mapped_column(
        UUID_TYPE(as_uuid=True),
        ForeignKey("meal_type.meal_type_id", ondelete="SET NULL"),
        nullable=True,
        comment="Reference to meal type (Breakfast/Lunch/Dinner/All Day)"
    )
    opening_time: Mapped[Optional[time]] = mapped_column(
        Time,
        nullable=True,
        comment="Meal slot start time (e.g., 06:00:00 for breakfast)"
    )
    closing_time: Mapped[Optional[time]] = mapped_column(
        Time,
        nullable=True,
        comment="Meal slot end time (e.g., 11:00:00 for breakfast)"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Audit Fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    created_by: Mapped[Optional[UUID]] = mapped_column(UUID_TYPE(as_uuid=True), nullable=True)
    updated_by: Mapped[Optional[UUID]] = mapped_column(UUID_TYPE(as_uuid=True), nullable=True)

    # Soft Delete
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    meal_type: Mapped[Optional["MealType"]] = relationship(
        "MealType",
        back_populates="slot_timings",
        foreign_keys=[meal_type_id]
    )

    __table_args__ = (
        Index(
            'idx_meal_slot_timing_active',
            'meal_type_id', 'opening_time', 'closing_time',
            postgresql_where=text('is_deleted = false AND is_active = true')
        ),
        Index(
            'idx_meal_slot_timing_time_range',
            'opening_time', 'closing_time',
            postgresql_where=text('is_deleted = false AND is_active = true')
        ),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<MealSlotTiming(id='{self.meal_slot_timing_id}', meal_type_id='{self.meal_type_id}', {self.opening_time}-{self.closing_time})>"


__all__ = ["MealSlotTiming"]

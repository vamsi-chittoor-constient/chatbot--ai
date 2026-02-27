"""
MenuItemAvailabilitySchedule Model
===================================
Time-based availability for menu items (Breakfast/Lunch/Dinner scheduling).
"""

from typing import Optional
from datetime import datetime, time
from uuid import UUID

from app.shared.models.base import (
    Base, func,
    String, DateTime, Boolean, Time,
    ForeignKey, Index, CheckConstraint,
    relationship, Mapped, mapped_column
)
from sqlalchemy.dialects.postgresql import UUID as UUID_TYPE
from sqlalchemy.sql import text


class MenuItemAvailabilitySchedule(Base):
    """
    Time-based availability for menu items.

    Supports:
    - Meal timing filtering (Breakfast, Lunch, Dinner, All Day)
    - Day-of-week scheduling (optional)
    - Time range restrictions (optional)

    Option B Implementation: Direct meal_type_id link for simplified queries.
    """
    __tablename__ = "menu_item_availability_schedule"

    schedule_id: Mapped[UUID] = mapped_column(
        UUID_TYPE(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )
    menu_item_id: Mapped[UUID] = mapped_column(
        UUID_TYPE(as_uuid=True),
        ForeignKey("menu_item.menu_item_id", ondelete="CASCADE"),
        nullable=False
    )
    meal_type_id: Mapped[Optional[UUID]] = mapped_column(
        UUID_TYPE(as_uuid=True),
        ForeignKey("meal_type.meal_type_id", ondelete="SET NULL"),
        nullable=True,
        comment="Direct link to meal type (Breakfast/Lunch/Dinner/All Day). Simplifies meal timing queries."
    )
    day_of_week: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="NULL = applies to all days"
    )
    time_from: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    time_to: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)

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
    menu_item: Mapped["MenuItem"] = relationship("MenuItem", back_populates="availability_schedules")
    meal_type: Mapped[Optional["MealType"]] = relationship("MealType", back_populates="availability_schedules")

    __table_args__ = (
        CheckConstraint(
            "day_of_week IN ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday') OR day_of_week IS NULL",
            name='check_day_of_week'
        ),
        Index('idx_availability_menu_item', 'menu_item_id', postgresql_where=text('is_deleted = false')),
        Index('idx_availability_meal_type', 'meal_type_id', postgresql_where=text('is_deleted = false')),
        Index('idx_availability_day_time', 'day_of_week', 'time_from', 'time_to', postgresql_where=text('is_deleted = false AND is_available = true')),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<MenuItemAvailabilitySchedule(item_id='{self.menu_item_id}', meal_type_id='{self.meal_type_id}', available={self.is_available})>"


__all__ = ["MenuItemAvailabilitySchedule"]

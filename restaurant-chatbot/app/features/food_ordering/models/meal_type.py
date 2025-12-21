"""
MealType Model
==============
Lookup table for meal periods (Breakfast, Lunch, Dinner, All Day).
"""

from typing import Optional, List
from datetime import datetime
from uuid import UUID

from app.shared.models.base import (
    Base, func,
    String, DateTime, Boolean, Integer,
    Index,
    relationship, Mapped, mapped_column
)
from sqlalchemy.dialects.postgresql import UUID as UUID_TYPE
from sqlalchemy.sql import text


class MealType(Base):
    """
    Meal period reference table.

    Contains: Breakfast, Lunch, Dinner, All Day
    """
    __tablename__ = "meal_type"

    meal_type_id: Mapped[UUID] = mapped_column(
        UUID_TYPE(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )
    meal_type_name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)

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
    availability_schedules: Mapped[List["MenuItemAvailabilitySchedule"]] = relationship(
        "MenuItemAvailabilitySchedule",
        back_populates="meal_type"
    )
    slot_timings: Mapped[List["MealSlotTiming"]] = relationship(
        "MealSlotTiming",
        back_populates="meal_type",
        foreign_keys="[MealSlotTiming.meal_type_id]"
    )

    __table_args__ = (
        Index('idx_meal_type_name', 'meal_type_name', postgresql_where=text('is_deleted = false')),
        Index('idx_meal_type_display_order', 'display_order', postgresql_where=text('is_deleted = false')),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<MealType(id='{self.meal_type_id}', name='{self.meal_type_name}')>"


__all__ = ["MealType"]

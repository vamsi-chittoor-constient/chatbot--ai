"""
Restaurant Models
=================

Database models for restaurant feature.

Models in this file:
- Restaurant
- Table
"""

from uuid import UUID

from app.shared.models.base import (
    Base, func, datetime, Optional, List,
    String, Text, DateTime, Boolean, JSON, Integer,
    ForeignKey, UniqueConstraint, Index, CheckConstraint,
    Decimal, Numeric, Date, Time, ARRAY, Vector,
    relationship, Mapped, mapped_column,
    UserStatus, BookingStatus, OrderStatus, PaymentStatus,
    MessageDirection, MessageChannel, ComplaintStatus
)
from sqlalchemy.dialects.postgresql import UUID as UUID_TYPE


class Restaurant(Base):
    """
    Restaurant configuration information.
    Matches actual restaurant_config table structure in database.
    """
    __tablename__ = "restaurant_config"

    id: Mapped[UUID] = mapped_column(UUID_TYPE(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    timezone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, server_default="'Asia/Kolkata'")
    currency: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, server_default="'INR'")
    tax_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True, server_default="0")
    service_charge_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True, server_default="0")
    opening_time: Mapped[Optional[Time]] = mapped_column(Time, nullable=True)
    closing_time: Mapped[Optional[Time]] = mapped_column(Time, nullable=True)
    is_open: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, server_default="true")
    settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True),
                                                          server_default=func.now(), nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True),
                                                          server_default=func.now(),
                                                          onupdate=func.now(), nullable=True)

    # Relationships
    # Note: In 3NF schema, categories are global lookup tables, not per-restaurant
    # bookings: Mapped[List["Booking"]] = relationship("Booking", back_populates="restaurant")
    tables: Mapped[List["Table"]] = relationship("Table", back_populates="restaurant")

    # New Menu Relationships (Actual DB Schema)
    # menu_sections: Mapped[List["MenuSection"]] = relationship("MenuSection", back_populates="restaurant")
    # menu_categories: Mapped[List["MenuCategory"]] = relationship("MenuCategory", back_populates="restaurant")
    # menu_sub_categories: Mapped[List["MenuSubCategory"]] = relationship("MenuSubCategory", back_populates="restaurant")
    # menu_items: Mapped[List["MenuItem"]] = relationship("MenuItem", back_populates="restaurant")

    __table_args__ = ({'extend_existing': True},)

    def __repr__(self) -> str:
        return f"<Restaurant(name='{self.name}')>"





class Table(Base):
    """
    Restaurant table information for booking management.
    """
    __tablename__ = "tables"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    restaurant_id: Mapped[UUID] = mapped_column(UUID_TYPE(as_uuid=True), ForeignKey("restaurant_config.id"))
    table_number: Mapped[str] = mapped_column(String(20), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    features: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now())

    # Relationships
    restaurant: Mapped["Restaurant"] = relationship("Restaurant", back_populates="tables")
    # bookings: Mapped[List["Booking"]] = relationship("Booking", back_populates="table")

    __table_args__ = (
        UniqueConstraint('restaurant_id', 'table_number', name='unique_table_per_restaurant'),
        Index('idx_tables_restaurant', 'restaurant_id'),
        Index('idx_tables_capacity', 'capacity'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<Table(number='{self.table_number}', capacity={self.capacity})>"





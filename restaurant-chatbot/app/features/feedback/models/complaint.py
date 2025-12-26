"""
Complaint Model
===============

Database model for complaint.
"""

from app.shared.models.base import (
    Base, func, datetime, Optional, List,
    String, Text, DateTime, Boolean, JSON, Integer,
    ForeignKey, UniqueConstraint, Index, CheckConstraint,
    Decimal, Numeric, Date, Time, ARRAY, Vector,
    relationship, Mapped, mapped_column,
    UserStatus, BookingStatus, OrderStatus, PaymentStatus,
    MessageDirection, MessageChannel, ComplaintStatus
)


class Complaint(Base):
    """
    Customer complaints and issue tracking.
    Integrates with sentiment analysis for prioritization.
    Supports SLA tracking with started_at and completed_at timestamps.
    """
    __tablename__ = "complaints"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(20))  # Removed ForeignKey for now
    order_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # Removed ForeignKey
    booking_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # Removed ForeignKey
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    ticket_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    priority: Mapped[str] = mapped_column(String(50), default="medium")
    sentiment_score: Mapped[Optional[float]] = mapped_column(Numeric(3, 2), nullable=True)
    sentiment_label: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    tone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    mood: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="open")
    resolution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(250), nullable=True)
    tags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Audit trail and lifecycle tracking
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now(),
                                               onupdate=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    # user: Mapped["User"] = relationship("User", back_populates="complaints")
    # order: Mapped[Optional["Order"]] = relationship("Order")
    # booking: Mapped[Optional["Booking"]] = relationship("Booking")

    __table_args__ = (
        Index('idx_complaints_user', 'user_id'),
        Index('idx_complaints_status', 'status'),
        Index('idx_complaints_priority', 'priority'),
        Index('idx_complaints_sentiment', 'sentiment_score'),
        Index('idx_complaints_date', 'created_at'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<Complaint(id='{self.id[:8]}...', title='{self.title[:30]}...', status={self.status})>"







__all__ = ["Complaint"]

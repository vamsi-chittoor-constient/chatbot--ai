"""
Feedback Model
==============

Database model for feedback.
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


class Feedback(Base):
    """
    General customer feedback table.
    Used for collecting user feedback on various aspects of the service.
    """
    __tablename__ = "feedback"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("users.id"), nullable=True)
    order_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("orders.id"), nullable=True)
    booking_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("bookings.id"), nullable=True)
    rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    review_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sentiment_score: Mapped[Optional[float]] = mapped_column(Numeric(3, 2), nullable=True)
    sentiment_label: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    feedback_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now())

    # Relationships
    # user: Mapped[Optional["User"]] = relationship("User", back_populates="feedbacks")
    # order: Mapped[Optional["Order"]] = relationship("Order")
    # booking: Mapped[Optional["Booking"]] = relationship("Booking")

    __table_args__ = (
        CheckConstraint('rating >= 1 AND rating <= 5', name='feedback_rating_check'),
        Index('idx_feedback_user', 'user_id'),
        Index('idx_feedback_order', 'order_id'),
        Index('idx_feedback_booking', 'booking_id'),
        Index('idx_feedback_type', 'feedback_type'),
        Index('idx_feedback_date', 'created_at'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<Feedback(id='{self.id[:8]}...', type='{self.feedback_type}', rating={self.rating})>"







__all__ = ["Feedback"]

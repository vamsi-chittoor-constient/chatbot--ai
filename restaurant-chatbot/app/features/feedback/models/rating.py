"""
Rating Model
============

Database model for rating.
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


class Rating(Base):
    """
    Customer ratings and feedback for orders and overall experience.
    """
    __tablename__ = "ratings"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(20), ForeignKey("users.id"))
    order_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("orders.id"),
                                                   nullable=True)
    booking_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("bookings.id"),
                                                     nullable=True)
    rating_type: Mapped[str] = mapped_column(String(50), nullable=False)  # food, service, ambiance, overall
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    max_rating: Mapped[int] = mapped_column(Integer, default=5)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sentiment_score: Mapped[Optional[float]] = mapped_column(Numeric(3, 2), nullable=True)
    sentiment_label: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now())

    # Relationships
    # user: Mapped["User"] = relationship("User", back_populates="ratings")
    # order: Mapped[Optional["Order"]] = relationship("Order")
    # booking: Mapped[Optional["Booking"]] = relationship("Booking")

    __table_args__ = (
        CheckConstraint('rating >= 1 AND rating <= max_rating', name='rating_range_check'),
        Index('idx_ratings_user', 'user_id'),
        Index('idx_ratings_type', 'rating_type'),
        Index('idx_ratings_rating', 'rating'),
        Index('idx_ratings_public', 'is_public'),
        Index('idx_ratings_date', 'created_at'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<Rating(user_id='{self.user_id[:8]}...', type='{self.rating_type}', rating={self.rating})>"







__all__ = ["Rating"]

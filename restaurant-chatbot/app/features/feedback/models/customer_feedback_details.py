"""
Customer Feedback Details Model
===============================

Database model for customer feedback details.
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


class CustomerFeedbackDetails(Base):
    """
    Customer feedback and satisfaction tracking for single restaurant.
    Used by CustomerSatisfactionAgent for comprehensive satisfaction tracking.
    """
    __tablename__ = "customer_feedback_details"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)

    # Basic feedback info (self-contained for single tenant)
    restaurant_id: Mapped[str] = mapped_column(String(20), ForeignKey("restaurant_config.id"))
    user_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("users.id"), nullable=True)
    order_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("orders.id"), nullable=True)

    # Overall feedback
    overall_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5 stars
    feedback_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Detailed ratings breakdown
    food_quality_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    service_speed_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    staff_friendliness_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cleanliness_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    value_for_money_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Specific feedback categories
    food_items_feedback: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    service_feedback: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    ambiance_feedback: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Improvement suggestions
    specific_complaints: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    improvement_suggestions: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    would_recommend: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    would_return: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now())

    __table_args__ = (
        CheckConstraint('food_quality_rating >= 1 AND food_quality_rating <= 5',
                       name='food_quality_rating_range'),
        CheckConstraint('service_speed_rating >= 1 AND service_speed_rating <= 5',
                       name='service_speed_rating_range'),
        CheckConstraint('staff_friendliness_rating >= 1 AND staff_friendliness_rating <= 5',
                       name='staff_friendliness_rating_range'),
        CheckConstraint('cleanliness_rating >= 1 AND cleanliness_rating <= 5',
                       name='cleanliness_rating_range'),
        CheckConstraint('value_for_money_rating >= 1 AND value_for_money_rating <= 5',
                       name='value_for_money_rating_range'),
        Index('idx_customer_feedback_details_restaurant_id', 'restaurant_id'),
        Index('idx_customer_feedback_details_user_id', 'user_id'),
        Index('idx_customer_feedback_details_would_recommend', 'would_recommend'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<CustomerFeedbackDetails(feedback_id='{self.feedback_id[:8]}...', would_recommend={self.would_recommend})>"







__all__ = ["CustomerFeedbackDetails"]

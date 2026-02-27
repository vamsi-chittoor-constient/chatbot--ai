"""
Satisfaction Metrics Model
==========================

Database model for satisfaction metrics.
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


class SatisfactionMetrics(Base):
    """
    Satisfaction metrics tracking for NPS, CSAT, CES scores.
    Used by CustomerSatisfactionAgent for analytics and reporting.
    """
    __tablename__ = "satisfaction_metrics"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("users.id"),
                                                  nullable=True)

    # Metric details
    metric_type: Mapped[str] = mapped_column(String(50), nullable=False)  # nps, csat, ces, overall_experience
    score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    max_score: Mapped[float] = mapped_column(Numeric(5, 2), default=10.00)

    # Context
    interaction_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # order, booking, support, general
    session_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reference_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    reference_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # order, booking, complaint

    # Categorization
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    subcategory: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Metadata
    collection_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    additional_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now())
    recorded_date: Mapped[datetime] = mapped_column(Date, server_default=func.current_date())

    # Relationships
    # user: Mapped[Optional["User"]] = relationship("User")

    __table_args__ = (
        Index('idx_satisfaction_metrics_user_id', 'user_id'),
        Index('idx_satisfaction_metrics_type', 'metric_type'),
        Index('idx_satisfaction_metrics_recorded_date', 'recorded_date'),
        Index('idx_satisfaction_metrics_interaction_type', 'interaction_type'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<SatisfactionMetrics(type='{self.metric_type}', score={self.score}, user_id='{self.user_id[:8] if self.user_id else None}...')>"







__all__ = ["SatisfactionMetrics"]

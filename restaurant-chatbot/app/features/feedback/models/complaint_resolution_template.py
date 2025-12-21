"""
Complaint Resolution Template Model
===================================

Database model for complaint resolution template.
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


class ComplaintResolutionTemplate(Base):
    """
    Template responses for complaint resolution.
    Used by CustomerSatisfactionAgent for consistent complaint handling.
    """
    __tablename__ = "complaint_resolution_templates"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)

    # Template details
    template_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    subcategory: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Template content
    response_template: Mapped[str] = mapped_column(Text, nullable=False)
    compensation_guidelines: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    escalation_criteria: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Usage tracking
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    success_rate: Mapped[float] = mapped_column(Numeric(5, 2), default=0.00)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now(),
                                               onupdate=func.now())

    __table_args__ = (
        Index('idx_complaint_resolution_templates_category', 'category'),
        Index('idx_complaint_resolution_templates_active', 'is_active'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<ComplaintResolutionTemplate(name='{self.template_name}', category='{self.category}')>"


# General Queries Agent Models




__all__ = ["ComplaintResolutionTemplate"]

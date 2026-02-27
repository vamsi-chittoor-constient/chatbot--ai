"""
Waitlist Model
==============

Waitlist for customers when tables are unavailable.
Alternative to immediate booking when restaurant is at capacity.
"""

from app.shared.models.base import (
    Base, func, datetime, Optional,
    String, DateTime, Integer,
    ForeignKey, Index,
    relationship, Mapped, mapped_column
)


class Waitlist(Base):
    """
    Waitlist for customers when tables are unavailable.
    Alternative to immediate booking when restaurant is at capacity.
    """
    __tablename__ = "waitlist"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("users.id"), nullable=True)
    requested_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    party_size: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    # user: Mapped[Optional["User"]] = relationship("User", back_populates="waitlist_entries")

    __table_args__ = (
        Index('idx_waitlist_user', 'user_id'),
        Index('idx_waitlist_datetime', 'requested_datetime'),
        Index('idx_waitlist_status', 'status'),
        Index('idx_waitlist_date', 'created_at'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<Waitlist(id='{self.id[:8]}...', party_size={self.party_size}, status='{self.status}')>"


__all__ = ["Waitlist"]

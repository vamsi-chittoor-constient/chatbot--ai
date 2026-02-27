"""
Communication Models
====================

Database models for communication feature.

Models in this file:
- Session
- Conversation
- Message
- MessageTemplate
- MessageLog
- EmailLog
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


class Session(Base):
    """
    User sessions for tracking anonymous and authenticated users.
    """
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("users.id"), nullable=True)
    session_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False),
                                               server_default=func.now())
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=False), nullable=True)
    last_activity: Mapped[datetime] = mapped_column(DateTime(timezone=False),
                                                   server_default=func.now())

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="sessions")
    conversations: Mapped[List["Conversation"]] = relationship("Conversation", back_populates="session")

    __table_args__ = (
        Index('idx_sessions_session_id', 'session_id'),
        Index('idx_sessions_user_id', 'user_id'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<Session(id='{self.id[:8]}...', session_id='{self.session_id[:8]}...')>"





class Conversation(Base):
    """
    User conversation sessions with AI agents.
    Tracks conversation context.
    """
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("sessions.id"), nullable=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("users.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active")  # Match DB column
    context: Mapped[dict] = mapped_column(JSON, default=dict)  # Match DB column name
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False),  # Match DB: timestamp without time zone
                                               server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=False),  # Match DB: timestamp without time zone
                                               server_default=func.now(),
                                               onupdate=func.now())

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="conversations")
    session: Mapped[Optional["Session"]] = relationship("Session", back_populates="conversations")
    messages: Mapped[List["Message"]] = relationship("Message", back_populates="conversation")

    __table_args__ = (
        Index('idx_conversations_user', 'user_id'),
        Index('idx_conversations_session', 'session_id'),
        Index('idx_conversations_status', 'status'),  # Updated to match actual DB column
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        user_id_str = self.user_id[:8] if self.user_id else 'None'
        return f"<Conversation(id='{self.id[:8]}...', user_id='{user_id_str}...')>"





class Message(Base):
    """
    Individual messages in conversations.
    Uses standard role-based message format.
    """
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(String(20), ForeignKey("conversations.id"))
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # user, assistant, system
    content: Mapped[str] = mapped_column(Text, nullable=False)
    agent_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    meta_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Use meta_data to avoid conflict with Base.metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now())

    # Relationships
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")

    __table_args__ = (
        Index('idx_messages_conversation', 'conversation_id'),
        Index('idx_messages_role', 'role'),
        Index('idx_messages_agent', 'agent_name'),
        Index('idx_messages_date', 'created_at'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"<Message(role={self.role}, agent={self.agent_name}, content='{content_preview}')>"


# Analytics & Feedback Models




class MessageTemplate(Base):
    """
    Reusable message templates for communication across different channels.
    Supports variable substitution for personalized messages.
    """
    __tablename__ = "message_templates"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    template_type: Mapped[str] = mapped_column(String(100), nullable=False)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    template_content: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[list] = mapped_column(JSON, default=list)  # List of variable names
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now(),
                                               onupdate=func.now())

    __table_args__ = (
        Index('idx_message_templates_type', 'template_type'),
        Index('idx_message_templates_channel', 'channel'),
        Index('idx_message_templates_active', 'is_active'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<MessageTemplate(name='{self.name}', type='{self.template_type}', channel='{self.channel}')>"





class MessageLog(Base):
    """
    Log of all messages sent through various channels (SMS, Email, WhatsApp).
    Tracks delivery status and retry attempts.
    """
    __tablename__ = "message_logs"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("users.id"), nullable=True)
    template_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("message_templates.id"), nullable=True)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    message_type: Mapped[str] = mapped_column(String(100), nullable=False)
    recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="queued")
    external_message_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    webhook_data: Mapped[dict] = mapped_column(JSON, default=dict)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now(),
                                               onupdate=func.now())

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="message_logs")
    template: Mapped[Optional["MessageTemplate"]] = relationship("MessageTemplate")

    __table_args__ = (
        Index('idx_message_logs_user', 'user_id'),
        Index('idx_message_logs_channel', 'channel'),
        Index('idx_message_logs_type', 'message_type'),
        Index('idx_message_logs_status', 'status'),
        Index('idx_message_logs_external', 'external_message_id'),
        Index('idx_message_logs_date', 'created_at'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<MessageLog(id='{self.id[:8]}...', channel='{self.channel}', status='{self.status}')>"





class EmailLog(Base):
    """
    Advanced email delivery tracking with bounce, engagement, and unsubscribe management.
    Phase 2 feature for comprehensive email analytics and deliverability monitoring.

    Tracks:
    - Delivery status and bounces
    - Email engagement (opens, clicks)
    - Unsubscribe management
    - Spam reports
    - SMTP provider responses
    """
    __tablename__ = "email_logs"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("users.id"), nullable=True)
    message_log_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("message_logs.id"), nullable=True)

    # Email details
    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    html_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    plain_text_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Delivery tracking
    status: Mapped[str] = mapped_column(String(50), default="queued", nullable=False)  # queued, sent, delivered, bounced, failed
    smtp_message_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    smtp_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    smtp_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Bounce handling (Phase 2)
    bounced: Mapped[bool] = mapped_column(Boolean, default=False)
    bounce_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # hard, soft, complaint
    bounce_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    bounced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Engagement tracking (Phase 2)
    opened: Mapped[bool] = mapped_column(Boolean, default=False)
    first_opened_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_opened_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    open_count: Mapped[int] = mapped_column(Integer, default=0)

    clicked: Mapped[bool] = mapped_column(Boolean, default=False)
    first_clicked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_clicked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    click_count: Mapped[int] = mapped_column(Integer, default=0)
    link_clicks: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)  # {"url": click_count}

    # Unsubscribe management (Phase 2)
    unsubscribed: Mapped[bool] = mapped_column(Boolean, default=False)
    unsubscribed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    unsubscribe_token: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)

    # Spam tracking (Phase 2)
    spam_reported: Mapped[bool] = mapped_column(Boolean, default=False)
    spam_reported_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Provider tracking
    provider: Mapped[str] = mapped_column(String(50), default="smtp", nullable=False)  # smtp, ses, sendgrid (future)
    provider_metadata: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    # Retry tracking
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Timestamps
    queued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now(),
                                               onupdate=func.now())

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User")
    message_log: Mapped[Optional["MessageLog"]] = relationship("MessageLog")

    __table_args__ = (
        Index('idx_email_logs_user_id', 'user_id'),
        Index('idx_email_logs_recipient', 'recipient_email'),
        Index('idx_email_logs_status', 'status'),
        Index('idx_email_logs_smtp_message_id', 'smtp_message_id'),
        Index('idx_email_logs_bounced', 'bounced'),
        Index('idx_email_logs_opened', 'opened'),
        Index('idx_email_logs_clicked', 'clicked'),
        Index('idx_email_logs_unsubscribed', 'unsubscribed'),
        Index('idx_email_logs_spam_reported', 'spam_reported'),
        Index('idx_email_logs_created_at', 'created_at'),
        Index('idx_email_logs_sent_at', 'sent_at'),
        Index('idx_email_logs_user_status', 'user_id', 'status'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<EmailLog(id='{self.id[:8]}...', recipient='{self.recipient_email}', status='{self.status}')>"





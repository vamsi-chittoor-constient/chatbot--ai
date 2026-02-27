"""
System Models
=============

Database models for system feature.

Models in this file:
- AgentMemory
- SystemLog
- KnowledgeBase
- FAQ
- RestaurantPolicy
- QueryAnalytics
- APIKeyUsage
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


class AgentMemory(Base):
    """
    Persistent storage for agent-specific memory across conversations.
    Supports both short-term and long-term memory with Redis backup.
    """
    __tablename__ = "agent_memory"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("users.id"), nullable=True)
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    memory_type: Mapped[str] = mapped_column(String(50), nullable=False)  # Match DB: varchar(50)
    memory_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    # expires_at column removed - doesn't exist in database
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False),  # Match DB: timestamp without time zone
                                               server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=False),  # Match DB: timestamp without time zone
                                               server_default=func.now(),
                                               onupdate=func.now())

    # Relationships
    user: Mapped["User"] = relationship("User")

    __table_args__ = (
        UniqueConstraint('user_id', 'agent_name', 'memory_type',
                        name='unique_agent_memory_per_user'),
        Index('idx_agent_memory_user', 'user_id'),
        Index('idx_agent_memory_agent', 'agent_name'),
        Index('idx_agent_memory_type', 'memory_type'),
        # Removed expires_at index - column doesn't exist in database
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        user_id_str = self.user_id[:8] if self.user_id else 'None'
        return f"<AgentMemory(user_id='{user_id_str}...', agent='{self.agent_name}', type='{self.memory_type}')>"





class SystemLog(Base):
    """
    System-wide logging for debugging and monitoring.
    Complements application logging with structured database storage.
    """
    __tablename__ = "system_logs"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    level: Mapped[str] = mapped_column(String(10), nullable=False)  # Match DB: varchar(10)
    service: Mapped[str] = mapped_column(String(100), nullable=False)  # Match DB column name
    message: Mapped[str] = mapped_column(Text, nullable=False)
    meta_data: Mapped[dict] = mapped_column(JSON, default=dict)  # Use meta_data to avoid conflict with Base.metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False),  # Match DB: timestamp without time zone
                                               server_default=func.now())

    __table_args__ = (
        Index('idx_system_logs_level', 'level'),
        Index('idx_system_logs_service', 'service'),  # Updated to match DB column
        Index('idx_system_logs_created_at', 'created_at'),  # Match DB index name
        # Removed user_id and session_id indices - columns don't exist
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<SystemLog(level='{self.level}', service='{self.service}')>"





class KnowledgeBase(Base):
    """
    Knowledge base for storing FAQs, policies, and other reference documents.
    Supports vector search for semantic similarity matching.
    """
    __tablename__ = "knowledge_base"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    document_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(1536), nullable=True)  # OpenAI embeddings
    meta_data: Mapped[dict] = mapped_column(JSON, default=dict)  # Use meta_data to avoid conflict with Base.metadata
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now(),
                                               onupdate=func.now())

    __table_args__ = (
        Index('idx_knowledge_base_type', 'document_type'),
        Index('idx_knowledge_base_category', 'category'),
        Index('idx_knowledge_base_active', 'is_active'),
        Index('idx_knowledge_base_date', 'created_at'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<KnowledgeBase(id='{self.id[:8]}...', title='{self.title[:30]}...')>"





class FAQ(Base):
    """
    Frequently Asked Questions for GeneralQueriesAgent.
    Supports vector search and usage analytics.
    """
    __tablename__ = "faq"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)

    # Question details
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    subcategory: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Question variations for better matching
    question_variations: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)

    # Metadata
    keywords: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    difficulty_level: Mapped[str] = mapped_column(String(20), default="easy")  # easy, medium, complex

    # Usage statistics
    question_count: Mapped[int] = mapped_column(Integer, default=0)
    last_asked: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    satisfaction_score: Mapped[float] = mapped_column(Numeric(3, 2), default=0.00)

    # Content management
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    display_order: Mapped[int] = mapped_column(Integer, default=100)
    status: Mapped[str] = mapped_column(String(20), default="active")

    # AI enhancement
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(1536), nullable=True)
    confidence_threshold: Mapped[float] = mapped_column(Numeric(3, 2), default=0.80)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now(),
                                               onupdate=func.now())

    __table_args__ = (
        Index('idx_faq_category', 'category'),
        Index('idx_faq_keywords', 'keywords', postgresql_using='gin'),
        Index('idx_faq_question_count', 'question_count'),
        Index('idx_faq_featured', 'is_featured', 'display_order'),
        Index('idx_faq_embedding', 'embedding', postgresql_using='hnsw',
              postgresql_with={'m': 16, 'ef_construction': 64}, postgresql_ops={'embedding': 'vector_cosine_ops'}),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<FAQ(category='{self.category}', question='{self.question[:50]}...')>"





class RestaurantPolicy(Base):
    """
    Restaurant policies for GeneralQueriesAgent.
    Manages booking, payment, dietary, and operational policies.
    """
    __tablename__ = "restaurant_policies"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)

    # Policy details
    policy_name: Mapped[str] = mapped_column(String(255), nullable=False)
    policy_category: Mapped[str] = mapped_column(String(100), nullable=False)
    policy_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Policy content
    short_description: Mapped[str] = mapped_column(Text, nullable=False)
    full_policy: Mapped[str] = mapped_column(Text, nullable=False)
    exceptions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    enforcement_level: Mapped[str] = mapped_column(String(20), default="strict")

    # Policy scope
    applies_to: Mapped[str] = mapped_column(String(50), default="all")
    effective_date: Mapped[datetime] = mapped_column(Date, server_default=func.current_date())
    expiry_date: Mapped[Optional[datetime]] = mapped_column(Date, nullable=True)

    # Legal and compliance
    legal_requirement: Mapped[bool] = mapped_column(Boolean, default=False)
    compliance_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Usage tracking
    reference_count: Mapped[int] = mapped_column(Integer, default=0)
    clarification_requests: Mapped[int] = mapped_column(Integer, default=0)

    # Status
    status: Mapped[str] = mapped_column(String(20), default="active")
    version: Mapped[str] = mapped_column(String(20), default="1.0")

    # Relationships
    related_policies: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String(20)), nullable=True)
    supersedes_policy_id: Mapped[Optional[str]] = mapped_column(String(20),
                                                               ForeignKey("restaurant_policies.id"),
                                                               nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now(),
                                               onupdate=func.now())
    last_reviewed: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Management
    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index('idx_restaurant_policies_category', 'policy_category'),
        Index('idx_restaurant_policies_status', 'status'),
        Index('idx_restaurant_policies_effective_date', 'effective_date'),
        Index('idx_restaurant_policies_applies_to', 'applies_to'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<RestaurantPolicy(name='{self.policy_name}', category='{self.policy_category}')>"





class QueryAnalytics(Base):
    """
    Query analytics for tracking user questions and agent performance.
    Used by GeneralQueriesAgent for continuous improvement.
    """
    __tablename__ = "query_analytics"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)

    # Query details
    user_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("users.id"),
                                                  nullable=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    query_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    query_intent: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Agent response
    agent_name: Mapped[str] = mapped_column(String(50), nullable=False)
    response_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 3), nullable=True)

    # Response details
    response_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    source_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # User feedback
    user_satisfied: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    required_escalation: Mapped[bool] = mapped_column(Boolean, default=False)
    escalated_to: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Performance metrics
    response_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    follow_up_questions: Mapped[int] = mapped_column(Integer, default=0)

    # Resolution
    fully_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    resolution_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now())
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User")

    __table_args__ = (
        Index('idx_query_analytics_user_id', 'user_id'),
        Index('idx_query_analytics_session_id', 'session_id'),
        Index('idx_query_analytics_agent_name', 'agent_name'),
        Index('idx_query_analytics_created_at', 'created_at'),
        Index('idx_query_analytics_query_category', 'query_category'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<QueryAnalytics(agent='{self.agent_name}', query='{self.query_text[:50]}...', resolved={self.fully_resolved})>"





class APIKeyUsage(Base):
    """
    API key usage tracking for analytics and rate limiting.
    Tracks every API request for each restaurant's API key.
    """
    __tablename__ = "api_key_usage"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)

    restaurant_id: Mapped[str] = mapped_column(String(20), ForeignKey("restaurant_config.id"),
                                               nullable=False, index=True)
    api_key_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    endpoint: Mapped[str] = mapped_column(String(255), nullable=False)
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    response_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    request_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                  server_default=func.now(),
                                                  index=True)

    __table_args__ = (
        Index('idx_api_key_usage_restaurant_id', 'restaurant_id'),
        Index('idx_api_key_usage_created_at', 'created_at'),
        Index('idx_api_key_usage_restaurant_date', 'restaurant_id', 'created_at'),
        Index('idx_api_key_usage_endpoint', 'endpoint'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<APIKeyUsage(restaurant_id='{self.restaurant_id}', endpoint='{self.endpoint}', status={self.status_code})>"


# Create all table indexes and constraints
def create_database_indexes():
    """
    Additional database indexes for performance optimization.
    These are created separately to maintain readability.
    """
    # Composite indexes for common query patterns
    composite_indexes = [
        # User activity patterns
        Index('idx_users_status_created', User.status, User.created_at),

        # Booking availability queries
        Index('idx_bookings_date_status', Booking.booking_date, Booking.status),
        Index('idx_bookings_restaurant_date', Booking.restaurant_id, Booking.booking_date),

        # Order processing queries
        Index('idx_orders_status_created', Order.status, Order.created_at),
        Index('idx_orders_user_status', Order.user_id, Order.status),

        # Menu search and filtering
        Index('idx_menu_items_available_price', MenuItem.is_available, MenuItem.price),
        Index('idx_menu_items_category_available', MenuItem.category_id, MenuItem.is_available),

        # Message processing patterns
        Index('idx_messages_conv_date', Message.conversation_id, Message.created_at),
        Index('idx_messages_channel_date', Message.channel, Message.created_at),

        # Analytics queries
        Index('idx_complaints_status_priority', Complaint.status, Complaint.priority),
        Index('idx_ratings_type_rating', Rating.rating_type, Rating.rating),

        # Memory management
        Index('idx_agent_memory_user_agent', AgentMemory.user_id, AgentMemory.agent_name),
    ]

    return composite_indexes


# Event listeners will be registered in database/connection.py after engine creation
# to avoid multiple registrations during imports


if __name__ == "__main__":
    # Test model definitions
    print("SQLAlchemy models defined successfully!")
    print(f"Total models: {len(Base.metadata.tables)}")
    print("Available tables:")
    for table_name in Base.metadata.tables.keys():
        print(f"  - {table_name}")



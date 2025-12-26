"""
Session-Aware Complaint Tools for CrewAI
=========================================
Sync wrapper functions for complaint management that are compatible with CrewAI.

Following the same factory pattern used in food_ordering/crew_agent.py:
- Factory functions return @tool decorated functions
- Closures capture session_id for session awareness
- Sync functions use DIRECT database operations (not async)
- Return plain Python dicts/strings (no complex objects)
"""
from crewai.tools import tool
from typing import Dict, Any, Optional
import structlog
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import uuid
from datetime import datetime, timezone
import os

logger = structlog.get_logger(__name__)


def get_sync_db_session():
    """Get synchronous database session for complaint operations."""
    # Convert async database URL to sync (asyncpg -> psycopg2)
    database_url = os.getenv("DATABASE_URL", "")
    if "asyncpg" in database_url:
        sync_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    else:
        sync_url = database_url

    engine = create_engine(sync_url, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)
    return Session()


def create_complaint_tool(session_id: str):
    """
    Factory function that creates session-aware create_complaint tool.

    Args:
        session_id: Customer's session ID for context

    Returns:
        CrewAI-compatible @tool function
    """

    @tool("create_complaint")
    def create_complaint_sync(
        user_id: str,
        description: str,
        category: str,
        priority: str = "medium",
        order_id: Optional[str] = None
    ) -> str:
        """
        Create a new customer complaint.

        Use this when customer expresses dissatisfaction or complains about:
        - Food quality (cold, wrong, bad taste)
        - Service issues (slow, rude, wrong order)
        - Cleanliness concerns
        - Wait time problems
        - Billing/payment issues

        Args:
            user_id: Customer's user ID from session context
            description: Detailed description of the complaint
            category: One of: food_quality, service, cleanliness, wait_time, billing, other
            priority: One of: low, medium, high, critical (default: medium)
            order_id: Optional order ID if complaint is about specific order

        Returns:
            Success message with complaint ticket ID

        Example:
            create_complaint(
                user_id="user_123",
                description="The burger was cold and fries were soggy",
                category="food_quality",
                priority="high"
            )
        """
        logger.info("creating_complaint", session_id=session_id, category=category, priority=priority)

        try:
            # Generate unique complaint ID
            complaint_id = f"CMPL-{uuid.uuid4().hex[:12]}"
            now = datetime.now(timezone.utc)

            # Create complaint using direct SQL (sync operation)
            db_session = get_sync_db_session()
            try:
                insert_query = text("""
                    INSERT INTO complaints (
                        id, user_id, description, category, priority, order_id,
                        status, created_at, updated_at
                    ) VALUES (
                        :id, :user_id, :description, :category, :priority, :order_id,
                        :status, :created_at, :updated_at
                    )
                """)

                db_session.execute(insert_query, {
                    "id": complaint_id,
                    "user_id": user_id,
                    "description": description,
                    "category": category,
                    "priority": priority,
                    "order_id": order_id,
                    "status": "open",
                    "created_at": now,
                    "updated_at": now
                })
                db_session.commit()

                ticket_id = complaint_id[:8]

                logger.info("complaint_created",
                           session_id=session_id,
                           complaint_id=complaint_id,
                           category=category,
                           priority=priority)

                return (
                    f"I'm so sorry about that! I've logged your complaint as #{ticket_id}. "
                    f"We take this very seriously and will address it immediately. "
                    f"Priority: {priority.upper()}. "
                    f"Would you like us to offer a replacement or refund?"
                )

            finally:
                db_session.close()

        except Exception as e:
            logger.error("complaint_tool_exception",
                        session_id=session_id,
                        error=str(e),
                        exc_info=True)
            return f"I apologize for the issue. I'm having trouble logging complaints right now. Please speak with our manager directly."

    return create_complaint_sync


def create_get_complaints_tool(session_id: str):
    """
    Factory function that creates session-aware get_user_complaints tool.

    Args:
        session_id: Customer's session ID for context

    Returns:
        CrewAI-compatible @tool function
    """

    @tool("get_user_complaints")
    def get_complaints_sync(
        user_id: str,
        status: Optional[str] = None,
        limit: int = 5
    ) -> str:
        """
        Get list of customer's complaints.

        Use this when customer asks to:
        - See their complaints
        - Check complaint status
        - View complaint history

        Args:
            user_id: Customer's user ID from session context
            status: Optional filter - open, in_progress, resolved, closed
            limit: Maximum complaints to retrieve (default: 5)

        Returns:
            Formatted list of complaints with status

        Example:
            get_user_complaints(user_id="user_123", status="open")
        """
        logger.info("fetching_complaints", session_id=session_id, user_id=user_id, status=status)

        try:
            db_session = get_sync_db_session()
            try:
                # Build query based on status filter
                if status:
                    query = text("""
                        SELECT id, category, status, created_at
                        FROM complaints
                        WHERE user_id = :user_id AND status = :status AND deleted_at IS NULL
                        ORDER BY created_at DESC
                        LIMIT :limit
                    """)
                    result = db_session.execute(query, {
                        "user_id": user_id,
                        "status": status,
                        "limit": limit
                    })
                else:
                    query = text("""
                        SELECT id, category, status, created_at
                        FROM complaints
                        WHERE user_id = :user_id AND deleted_at IS NULL
                        ORDER BY created_at DESC
                        LIMIT :limit
                    """)
                    result = db_session.execute(query, {
                        "user_id": user_id,
                        "limit": limit
                    })

                complaints = result.fetchall()

                if not complaints:
                    return "You don't have any complaints on record."

                # Format complaints
                lines = [f"Your complaints ({len(complaints)}):"]
                for idx, complaint in enumerate(complaints, 1):
                    complaint_id = complaint[0][:8]  # id
                    category = complaint[1].replace("_", " ").title()  # category
                    complaint_status = complaint[2].title()  # status

                    lines.append(
                        f"{idx}. Complaint #{complaint_id} - {category} ({complaint_status})"
                    )

                return "\n".join(lines)

            finally:
                db_session.close()

        except Exception as e:
            logger.error("get_complaints_exception",
                        session_id=session_id,
                        error=str(e),
                        exc_info=True)
            return "I'm having trouble fetching your complaints. Please try again later."

    return get_complaints_sync


def create_complaint_status_tool(session_id: str):
    """
    Factory function that creates session-aware complaint status check tool.

    Args:
        session_id: Customer's session ID for context

    Returns:
        CrewAI-compatible @tool function
    """

    @tool("check_complaint_status")
    def check_status_sync(complaint_id: str) -> str:
        """
        Check status of a specific complaint.

        Use this when customer asks about their complaint status.

        Args:
            complaint_id: The complaint ID to check

        Returns:
            Current status and resolution if available
        """
        logger.info("checking_complaint_status", session_id=session_id, complaint_id=complaint_id)

        try:
            db_session = get_sync_db_session()
            try:
                query = text("""
                    SELECT id, category, status, resolution, created_at
                    FROM complaints
                    WHERE id = :complaint_id AND deleted_at IS NULL
                    LIMIT 1
                """)

                result = db_session.execute(query, {"complaint_id": complaint_id})
                complaint = result.fetchone()

                if not complaint:
                    return f"I couldn't find complaint #{complaint_id[:8]}. Please check the ID."

                complaint_id_full = complaint[0]
                category = complaint[1].replace("_", " ").title()
                status = complaint[2].title()
                resolution = complaint[3]

                response = f"Complaint #{complaint_id_full[:8]} - {category}\n"
                response += f"Status: {status}\n"

                if resolution:
                    response += f"\nResolution: {resolution}"
                elif status == "Open":
                    response += "\nWe're reviewing your complaint and will respond soon."
                elif status == "In_Progress" or status == "In Progress":
                    response += "\nYour complaint is being actively addressed."

                return response

            finally:
                db_session.close()

        except Exception as e:
            logger.error("check_status_exception",
                        session_id=session_id,
                        error=str(e),
                        exc_info=True)
            return "I'm having trouble checking complaint status. Please try again."

    return check_status_sync


__all__ = [
    "create_complaint_tool",
    "create_get_complaints_tool",
    "create_complaint_status_tool"
]

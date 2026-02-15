"""
Session Event Tracking - Event Sourcing Pattern
================================================
Structured, SQL-based session state management.

Architecture:
- All user actions are discrete events (item_viewed, item_added, etc.)
- Events are logged to session_events table
- Current state is materialized in session_cart, session_state tables
- Context retrieval is via SQL queries (zero token cost!)
- No text-based context in LLM prompts

Benefits vs Text-Based Approach:
- Zero token cost for context (queries don't go in prompts)
- Exact state (SQL truth, not fuzzy text matching)
- Complete audit trail (event sourcing)
- Analytics-ready (structured data)
- Deterministic (same state + action = same result)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID
import json
import structlog

logger = structlog.get_logger(__name__)


# ============================================================================
# EVENT TYPES - All possible session events
# ============================================================================

class EventType:
    """Event type constants - all user actions as discrete events."""

    # Menu browsing
    MENU_VIEWED = "menu_viewed"
    ITEM_VIEWED = "item_viewed"
    CATEGORY_BROWSED = "category_browsed"
    SEARCH_PERFORMED = "search_performed"

    # Cart operations
    ITEM_ADDED = "item_added"
    ITEM_REMOVED = "item_removed"
    ITEM_QUANTITY_UPDATED = "item_quantity_updated"
    CART_CLEARED = "cart_cleared"
    SPECIAL_INSTRUCTIONS_SET = "special_instructions_set"

    # Checkout & payment
    CHECKOUT_STARTED = "checkout_started"
    ORDER_TYPE_SELECTED = "order_type_selected"  # dine_in / take_away
    ORDER_PLACED = "order_placed"
    PAYMENT_METHOD_SELECTED = "payment_method_selected"
    PAYMENT_INITIATED = "payment_initiated"
    PAYMENT_COMPLETED = "payment_completed"
    PAYMENT_FAILED = "payment_failed"

    # Order management
    ORDER_CANCELLED = "order_cancelled"
    ORDER_STATUS_CHECKED = "order_status_checked"
    RECEIPT_VIEWED = "receipt_viewed"

    # Complaints
    COMPLAINT_CREATED = "complaint_created"
    COMPLAINT_VIEWED = "complaint_viewed"

    # Booking
    BOOKING_REQUESTED = "booking_requested"
    BOOKING_CONFIRMED = "booking_confirmed"
    BOOKING_CANCELLED = "booking_cancelled"


# ============================================================================
# SESSION EVENT TRACKER
# ============================================================================

class SessionEventTracker:
    """
    Event sourcing manager for session state.

    All user actions are logged as events. Current state is derived from events.
    Context is retrieved via SQL queries, not text passed to LLM.
    """

    def __init__(self, session_id: str, user_id: Optional[UUID] = None):
        self.session_id = session_id
        self.user_id = user_id

    async def log_event(self, event_type: str, event_data: Dict[str, Any]) -> UUID:
        """
        Log an event to the session event log.

        Args:
            event_type: Type of event (from EventType constants)
            event_data: Event-specific data (flexible JSONB)

        Returns:
            UUID of created event
        """
        from app.core.db_pool import AsyncDBConnection

        async with AsyncDBConnection() as db:
            result = await db.fetchrow(
                """
                INSERT INTO session_events (session_id, user_id, event_type, event_data)
                VALUES ($1, $2, $3, $4)
                RETURNING event_id
                """,
                self.session_id,
                str(self.user_id) if self.user_id else None,
                event_type,
                json.dumps(event_data)
            )

            event_id = result['event_id']

            logger.info(
                "session_event_logged",
                session_id=self.session_id,
                event_type=event_type,
                event_id=str(event_id),
                data_keys=list(event_data.keys())
            )

            return event_id

    # ========================================================================
    # CART OPERATIONS - Update materialized cart state
    # ========================================================================

    async def add_to_cart(
        self,
        item_id: UUID,
        item_name: str,
        quantity: int,
        price: float,
        special_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add item to cart (or update quantity if exists).

        Process:
        1. Log event to session_events
        2. Update session_cart (materialized state)
        3. Update session_state (last mentioned item)
        4. Return cart summary
        """
        from app.core.db_pool import AsyncDBConnection

        # 1. Log event
        await self.log_event(EventType.ITEM_ADDED, {
            'item_id': str(item_id),
            'item_name': item_name,
            'quantity': quantity,
            'price': price,
            'special_instructions': special_instructions
        })

        # 2. Update cart (upsert)
        async with AsyncDBConnection() as db:
            await db.execute(
                """
                INSERT INTO session_cart (
                    session_id, item_id, item_name, quantity, price, special_instructions
                )
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (session_id, item_id)
                DO UPDATE SET
                    quantity = session_cart.quantity + EXCLUDED.quantity,
                    special_instructions = COALESCE(EXCLUDED.special_instructions, session_cart.special_instructions),
                    updated_at = NOW(),
                    is_active = TRUE
                """,
                self.session_id,
                str(item_id),
                item_name,
                quantity,
                price,
                special_instructions
            )

            # 3. Update session state (last mentioned item)
            # Use subquery to validate user_id exists in customer_profile_table (FK constraint)
            await db.execute(
                """
                INSERT INTO session_state (
                    session_id, user_id, last_mentioned_item_id, last_mentioned_item_name
                )
                VALUES (
                    $1,
                    (SELECT customer_id FROM customer_profile_table WHERE customer_id = $2::uuid),
                    $3, $4
                )
                ON CONFLICT (session_id)
                DO UPDATE SET
                    last_mentioned_item_id = EXCLUDED.last_mentioned_item_id,
                    last_mentioned_item_name = EXCLUDED.last_mentioned_item_name,
                    updated_at = NOW(),
                    last_activity_at = NOW()
                """,
                self.session_id,
                str(self.user_id) if self.user_id else None,
                str(item_id),
                item_name
            )

            # 4. Return cart summary
            return await self.get_cart_summary()

    async def remove_from_cart(self, item_id: UUID) -> Dict[str, Any]:
        """Remove item from cart (soft delete for audit trail)."""
        from app.core.db_pool import AsyncDBConnection

        async with AsyncDBConnection() as db:
            # Get item name for event log
            result = await db.fetchrow(
                """
                SELECT item_name, quantity, price
                FROM session_cart
                WHERE session_id = $1 AND item_id = $2 AND is_active = TRUE
                """,
                self.session_id,
                str(item_id)
            )

            if not result:
                return {"success": False, "message": "Item not in cart"}

            item_name = result['item_name']
            quantity = result['quantity']
            price = result['price']

            # Log event
            await self.log_event(EventType.ITEM_REMOVED, {
                'item_id': str(item_id),
                'item_name': item_name,
                'quantity': quantity,
                'price': price
            })

            # Soft delete from cart
            await db.execute(
                """
                UPDATE session_cart
                SET is_active = FALSE, updated_at = NOW()
                WHERE session_id = $1 AND item_id = $2
                """,
                self.session_id,
                str(item_id)
            )

            return await self.get_cart_summary()

    async def update_quantity(self, item_id: UUID, new_quantity: int) -> Dict[str, Any]:
        """Update item quantity in cart."""
        from app.core.db_pool import AsyncDBConnection

        async with AsyncDBConnection() as db:
            # Get current state for event log
            result = await db.fetchrow(
                """
                SELECT item_name, quantity, price
                FROM session_cart
                WHERE session_id = $1 AND item_id = $2 AND is_active = TRUE
                """,
                self.session_id,
                str(item_id)
            )

            if not result:
                return {"success": False, "message": "Item not in cart"}

            old_quantity = result['quantity']

            # Log event
            await self.log_event(EventType.ITEM_QUANTITY_UPDATED, {
                'item_id': str(item_id),
                'item_name': result['item_name'],
                'old_quantity': old_quantity,
                'new_quantity': new_quantity,
                'price': result['price']
            })

            # Update quantity
            await db.execute(
                """
                UPDATE session_cart
                SET quantity = $3, updated_at = NOW()
                WHERE session_id = $1 AND item_id = $2
                """,
                self.session_id,
                str(item_id),
                new_quantity
            )

            return await self.get_cart_summary()

    async def clear_cart(self) -> Dict[str, Any]:
        """Clear all items from cart."""
        from app.core.db_pool import AsyncDBConnection

        # Log event
        await self.log_event(EventType.CART_CLEARED, {})

        async with AsyncDBConnection() as db:
            # Soft delete all cart items
            await db.execute(
                """
                UPDATE session_cart
                SET is_active = FALSE, updated_at = NOW()
                WHERE session_id = $1 AND is_active = TRUE
                """,
                self.session_id
            )

            return {"success": True, "items": [], "total": 0.0, "item_count": 0}

    # ========================================================================
    # CONTEXT QUERIES - SQL-based state retrieval (zero token cost!)
    # ========================================================================

    async def get_cart_summary(self) -> Dict[str, Any]:
        """Get current cart state via SQL query."""
        from app.core.db_pool import AsyncDBConnection

        async with AsyncDBConnection() as db:
            items = await db.fetch(
                """
                SELECT * FROM get_session_cart($1)
                """,
                self.session_id
            )

            total = await db.fetchrow(
                """
                SELECT get_cart_total($1) as total
                """,
                self.session_id
            )

            return {
                "success": True,
                "items": [dict(item) for item in items],
                "total": float(total['total']) if total else 0.0,
                "item_count": len(items)
            }

    async def get_last_mentioned_item(self) -> Optional[Dict[str, Any]]:
        """Get last mentioned item from session state."""
        from app.core.db_pool import AsyncDBConnection

        async with AsyncDBConnection() as db:
            result = await db.fetchrow(
                """
                SELECT last_mentioned_item_id, last_mentioned_item_name
                FROM session_state
                WHERE session_id = $1
                """,
                self.session_id
            )

            if result and result['last_mentioned_item_id']:
                return {
                    'item_id': result['last_mentioned_item_id'],
                    'item_name': result['last_mentioned_item_name']
                }
            return None

    async def get_session_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent session events (for debugging/analytics)."""
        from app.core.db_pool import AsyncDBConnection

        async with AsyncDBConnection() as db:
            events = await db.fetch(
                """
                SELECT * FROM get_session_history($1, $2)
                """,
                self.session_id,
                limit
            )

            return [
                {
                    'event_type': event['event_type'],
                    'event_data': json.loads(event['event_data']) if isinstance(event['event_data'], str) else event['event_data'],
                    'timestamp': event['timestamp'].isoformat()
                }
                for event in events
            ]

    async def update_session_state(
        self,
        current_step: Optional[str] = None,
        awaiting_input_for: Optional[str] = None
    ):
        """Update conversation flow state."""
        from app.core.db_pool import AsyncDBConnection

        async with AsyncDBConnection() as db:
            await db.execute(
                """
                INSERT INTO session_state (session_id, user_id, current_step, awaiting_input_for)
                VALUES (
                    $1,
                    (SELECT customer_id FROM customer_profile_table WHERE customer_id = $2::uuid),
                    $3, $4
                )
                ON CONFLICT (session_id)
                DO UPDATE SET
                    current_step = COALESCE(EXCLUDED.current_step, session_state.current_step),
                    awaiting_input_for = COALESCE(EXCLUDED.awaiting_input_for, session_state.awaiting_input_for),
                    updated_at = NOW(),
                    last_activity_at = NOW()
                """,
                self.session_id,
                str(self.user_id) if self.user_id else None,
                current_step,
                awaiting_input_for
            )


# ============================================================================
# SYNC SESSION TRACKER (for CrewAI tools running in threads)
# ============================================================================

class SyncSessionEventTracker:
    """
    Synchronous version of session tracker for use in CrewAI tools.

    CrewAI tools run in threads and cannot use asyncpg (which is event-loop bound).
    This uses psycopg2 which is thread-safe.
    """

    def __init__(self, session_id: str, user_id: Optional[UUID] = None):
        self.session_id = session_id
        self.user_id = user_id

    def log_event(self, event_type: str, event_data: Dict[str, Any]) -> UUID:
        """Log an event using sync connection."""
        from app.core.db_pool import SyncDBConnection
        import uuid

        with SyncDBConnection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO session_events (session_id, user_id, event_type, event_data)
                    VALUES (%s, %s, %s, %s)
                    RETURNING event_id
                    """,
                    (
                        self.session_id,
                        str(self.user_id) if self.user_id else None,
                        event_type,
                        json.dumps(event_data)
                    )
                )
                event_id = cur.fetchone()[0]
                conn.commit()

        logger.info(
            "session_event_logged_sync",
            session_id=self.session_id,
            event_type=event_type,
            event_id=str(event_id)
        )
        return event_id

    def add_to_cart(
        self,
        item_id: UUID,
        item_name: str,
        quantity: int,
        price: float,
        special_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add item to cart using sync connection."""
        from app.core.db_pool import SyncDBConnection

        # Log event
        self.log_event(EventType.ITEM_ADDED, {
            'item_id': str(item_id),
            'item_name': item_name,
            'quantity': quantity,
            'price': price,
            'special_instructions': special_instructions
        })

        with SyncDBConnection() as conn:
            with conn.cursor() as cur:
                # Upsert cart item
                cur.execute(
                    """
                    INSERT INTO session_cart (
                        session_id, item_id, item_name, quantity, price, special_instructions
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (session_id, item_id)
                    DO UPDATE SET
                        quantity = session_cart.quantity + EXCLUDED.quantity,
                        special_instructions = COALESCE(EXCLUDED.special_instructions, session_cart.special_instructions),
                        updated_at = NOW(),
                        is_active = TRUE
                    """,
                    (
                        self.session_id,
                        str(item_id),
                        item_name,
                        quantity,
                        price,
                        special_instructions
                    )
                )

                # Update session state
                # Use subquery to validate user_id exists in customer_profile_table
                # (FK constraint requires it; auth users may not be in that table yet)
                valid_user_id = str(self.user_id) if self.user_id else None
                cur.execute(
                    """
                    INSERT INTO session_state (
                        session_id, user_id, last_mentioned_item_id, last_mentioned_item_name
                    )
                    VALUES (
                        %s,
                        (SELECT customer_id FROM customer_profile_table WHERE customer_id = %s::uuid),
                        %s, %s
                    )
                    ON CONFLICT (session_id)
                    DO UPDATE SET
                        last_mentioned_item_id = EXCLUDED.last_mentioned_item_id,
                        last_mentioned_item_name = EXCLUDED.last_mentioned_item_name,
                        updated_at = NOW(),
                        last_activity_at = NOW()
                    """,
                    (
                        self.session_id,
                        valid_user_id,
                        str(item_id),
                        item_name
                    )
                )
                conn.commit()

        return self.get_cart_summary()

    def remove_from_cart(self, item_id: UUID) -> Dict[str, Any]:
        """Remove item from cart using sync connection."""
        from app.core.db_pool import SyncDBConnection

        with SyncDBConnection() as conn:
            with conn.cursor() as cur:
                # Get item info for event log
                cur.execute(
                    """
                    SELECT item_name, quantity, price
                    FROM session_cart
                    WHERE session_id = %s AND item_id = %s AND is_active = TRUE
                    """,
                    (self.session_id, str(item_id))
                )
                result = cur.fetchone()

                if not result:
                    return {"success": False, "message": "Item not in cart"}

                item_name, quantity, price = result

                # Log event
                self.log_event(EventType.ITEM_REMOVED, {
                    'item_id': str(item_id),
                    'item_name': item_name,
                    'quantity': quantity,
                    'price': float(price)
                })

                # Soft delete
                cur.execute(
                    """
                    UPDATE session_cart
                    SET is_active = FALSE, updated_at = NOW()
                    WHERE session_id = %s AND item_id = %s
                    """,
                    (self.session_id, str(item_id))
                )
                conn.commit()

        return self.get_cart_summary()

    def get_cart_summary(self) -> Dict[str, Any]:
        """Get cart summary using sync connection."""
        from app.core.db_pool import SyncDBConnection

        with SyncDBConnection() as conn:
            with conn.cursor() as cur:
                # Get cart items
                cur.execute(
                    """
                    SELECT * FROM get_session_cart(%s)
                    """,
                    (self.session_id,)
                )
                columns = [desc[0] for desc in cur.description] if cur.description else []
                items = [dict(zip(columns, row)) for row in cur.fetchall()]

                # Get total
                cur.execute(
                    """
                    SELECT get_cart_total(%s) as total
                    """,
                    (self.session_id,)
                )
                total_row = cur.fetchone()
                total = float(total_row[0]) if total_row and total_row[0] else 0.0

        return {
            "success": True,
            "items": items,
            "total": total,
            "item_count": len(items)
        }

    def clear_cart(self) -> Dict[str, Any]:
        """Clear all items from cart using sync connection."""
        from app.core.db_pool import SyncDBConnection

        # Log event
        self.log_event(EventType.CART_CLEARED, {})

        with SyncDBConnection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE session_cart
                    SET is_active = FALSE, updated_at = NOW()
                    WHERE session_id = %s AND is_active = TRUE
                    """,
                    (self.session_id,)
                )
                conn.commit()

        return self.get_cart_summary()

    def get_last_search_results(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get the items from the last MENU_VIEWED event.

        Used to resolve ordinal references like "option 1", "first one", etc.
        Returns the items list from the most recent search/menu view.
        """
        from app.core.db_pool import SyncDBConnection

        with SyncDBConnection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT event_data
                    FROM session_events
                    WHERE session_id = %s AND event_type = %s
                    ORDER BY timestamp DESC
                    LIMIT 1
                    """,
                    (self.session_id, EventType.MENU_VIEWED)
                )
                result = cur.fetchone()

                if not result:
                    return None

                event_data = result[0]
                if isinstance(event_data, str):
                    event_data = json.loads(event_data)

                # Return items list if stored in event
                return event_data.get('items', None)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_session_tracker(session_id: str, user_id: Optional[UUID] = None) -> SessionEventTracker:
    """Get async session event tracker instance."""
    return SessionEventTracker(session_id, user_id)


def get_sync_session_tracker(session_id: str, user_id: Optional[UUID] = None) -> SyncSessionEventTracker:
    """Get sync session event tracker for use in CrewAI tools (threaded context)."""
    return SyncSessionEventTracker(session_id, user_id)

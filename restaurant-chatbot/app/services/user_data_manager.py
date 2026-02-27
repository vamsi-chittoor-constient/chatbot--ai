"""
User Data Manager
==================
Orchestrates multi-tier user data storage:

1. Session Cache (Redis) - Temporary data for active users
2. Persistent Storage (PostgreSQL) - Long-term user data
3. Cache Restoration - Load user data when they log back in

Flow:
- User logs in  Load preferences from DB  Store in session cache
- User interacts  Update session cache (fast)
- User logs out  Save important data to DB  Destroy session cache
- User logs back in  Restore from DB  New session cache
"""

from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.user_cache_service import get_user_cache_service
from app.services.inventory_cache_service import get_inventory_cache_service
from app.core.database import get_db_session
from app.shared.models import User

logger = structlog.get_logger(__name__)


class UserDataManager:
    """
    Manages user data across session cache and persistent storage.

    Responsibilities:
    - Session lifecycle management (login, logout)
    - Cache restoration from database
    - Persistent storage of important session data
    - User preferences management
    """

    def __init__(self):
        """Initialize user data manager"""
        self.cache_service = get_user_cache_service()
        self.inventory_cache = get_inventory_cache_service()

        # Cart restoration window (2 hours)
        self.cart_restoration_window_hours = 2

        logger.info("user_data_manager_initialized")

    # ========================================================================
    # USER LOGIN / LOGOUT FLOW
    # ========================================================================

    async def on_user_login(self, user_id: str, session: AsyncSession) -> Dict[str, Any]:
        """
        Called when user logs in.

        Loads user data from persistent storage and creates session cache.

        Args:
            user_id: User ID (e.g., usr000001)
            session: Database session

        Returns:
            User data loaded into session cache with cart_restoration info if applicable
        """
        try:
            # Load user preferences from database
            user_data = await self._load_user_data_from_db(user_id, session)

            # Check for abandoned cart (within 2 hours)
            abandoned_cart = await self._get_abandoned_cart(user_id, session)

            if abandoned_cart:
                # Check item availability for cart items
                cart_restoration_info = await self._check_cart_availability(
                    user_id,
                    abandoned_cart
                )
                user_data["cart_restoration"] = cart_restoration_info

            # Check for abandoned booking (within 7 days)
            abandoned_booking = await self._get_abandoned_booking(user_id, session)

            if abandoned_booking:
                user_data["booking_restoration"] = {
                    "has_abandoned_booking": True,
                    "booking_details": abandoned_booking,
                    "last_step_completed": abandoned_booking.get("last_step_completed"),
                    "booking_date": abandoned_booking.get("date") or abandoned_booking.get("booking_date")
                }

            # Create session cache with preloaded data
            await self.cache_service.create_session(user_id, user_data)

            logger.info(
                "user_logged_in",
                user_id=user_id,
                preferences_loaded=bool(user_data.get("preferences")),
                dietary_restrictions=len(user_data.get("dietary_restrictions", [])),
                has_abandoned_cart=bool(abandoned_cart),
                has_abandoned_booking=bool(abandoned_booking)
            )

            return user_data

        except Exception as e:
            logger.error(
                "user_login_error",
                user_id=user_id,
                error=str(e)
            )
            # Return empty dict on error, don't fail login
            return {}

    async def on_user_logout(self, user_id: str, session: AsyncSession):
        """
        Called when user logs out or session expires.

        Saves important session data to database, releases inventory, then destroys session cache.

        Args:
            user_id: User ID
            session: Database session
        """
        try:
            # Get cart and booking in progress from session cache
            cart = await self.cache_service.get_cart(user_id)
            booking = await self.cache_service.get_booking_in_progress(user_id)

            # Release ALL inventory reservations for this user
            if cart and cart.get("items"):
                for item in cart["items"]:
                    item_id = item.get("item_id")
                    if item_id:
                        await self.inventory_cache.release_reservation(item_id, user_id)
                        logger.debug(
                            "inventory_released_on_logout",
                            user_id=user_id,
                            item_id=item_id
                        )

            # Save to database if exists (with timestamp for 2-hour restoration window)
            if cart:
                await self._save_abandoned_cart_to_db(user_id, cart, session)

            if booking:
                await self._save_abandoned_booking_to_db(user_id, booking, session)

            # Destroy session cache
            await self.cache_service.destroy_session(user_id, save_to_persistent=False)

            logger.info(
                "user_logged_out",
                user_id=user_id,
                cart_saved=bool(cart),
                booking_saved=bool(booking),
                inventory_released=bool(cart)
            )

        except Exception as e:
            logger.error(
                "user_logout_error",
                user_id=user_id,
                error=str(e)
            )

    async def on_user_activity(self, user_id: str, query: Optional[str] = None):
        """
        Called on any user activity.

        Extends session TTL and optionally tracks query.

        Args:
            user_id: User ID
            query: Optional user query to track
        """
        try:
            # Extend session
            await self.cache_service.extend_session(user_id)

            # Track query if provided
            if query:
                await self.cache_service.add_recent_query(user_id, query)

        except Exception as e:
            logger.error(
                "user_activity_tracking_error",
                user_id=user_id,
                error=str(e)
            )

    # ========================================================================
    # LOAD FROM PERSISTENT STORAGE
    # ========================================================================

    async def _load_user_data_from_db(
        self,
        user_id: str,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """
        Load user data from database.

        Returns:
            Dictionary with user preferences, history summary, favorites
        """
        try:
            # Load user from database
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()

            if not user:
                logger.warning("user_not_found_in_db", user_id=user_id)
                return {}

            # Build user data dictionary
            user_data = {
                "user_id": user.id,
                "name": user.name,
                "phone": user.phone,
                "email": user.email,
                "preferences": user.preferences or {},
                "dietary_restrictions": user.dietary_restrictions or [],

                # TODO: Load additional data
                # "order_history_summary": await self._get_order_history_summary(user_id, session),
                # "favorite_dishes": await self._get_favorite_dishes(user_id, session),
                # "last_booking": await self._get_last_booking(user_id, session),
            }

            return user_data

        except Exception as e:
            logger.error(
                "load_user_data_error",
                user_id=user_id,
                error=str(e)
            )
            return {}

    async def _get_abandoned_cart(
        self,
        user_id: str,
        session: AsyncSession
    ) -> Optional[Dict]:
        """
        Get abandoned cart if exists and within 2-hour window.

        Args:
            user_id: User ID
            session: Database session

        Returns:
            Cart data if found and recent, None otherwise
        """
        try:
            from app.shared.models import AbandonedCart
            from sqlalchemy import select, and_

            # Query for abandoned cart that hasn't been restored and hasn't expired
            query = select(AbandonedCart).where(
                and_(
                    AbandonedCart.user_id == user_id,
                    AbandonedCart.restored == False,
                    AbandonedCart.expires_at > datetime.now()
                )
            ).order_by(AbandonedCart.created_at.desc())

            result = await session.execute(query)
            abandoned_cart = result.scalar_one_or_none()

            if not abandoned_cart:
                return None

            # Return the cart items data
            logger.info(
                "abandoned_cart_retrieved",
                user_id=user_id,
                cart_id=abandoned_cart.id,
                items_count=len(abandoned_cart.cart_items.get("items", [])),
                time_since_abandoned_hours=round(
                    (datetime.now() - abandoned_cart.created_at).total_seconds() / 3600, 2
                )
            )

            return abandoned_cart.cart_items

        except Exception as e:
            logger.error(
                "get_abandoned_cart_error",
                user_id=user_id,
                error=str(e)
            )
            return None

    async def _get_abandoned_booking(
        self,
        user_id: str,
        session: AsyncSession
    ) -> Optional[Dict]:
        """
        Get abandoned booking if exists and within 7-day window.

        Args:
            user_id: User ID
            session: Database session

        Returns:
            Booking data if found and within window, None otherwise
        """
        try:
            from app.features.booking.models import AbandonedBooking
            from sqlalchemy import select, and_

            # Query for abandoned booking that hasn't been restored and hasn't expired
            query = select(AbandonedBooking).where(
                and_(
                    AbandonedBooking.user_id == user_id,
                    AbandonedBooking.restored == False,
                    AbandonedBooking.expires_at > datetime.now()
                )
            ).order_by(AbandonedBooking.created_at.desc())

            result = await session.execute(query)
            abandoned_booking = result.scalar_one_or_none()

            if not abandoned_booking:
                return None

            # Return the booking details data
            logger.info(
                "abandoned_booking_retrieved",
                user_id=user_id,
                booking_id=abandoned_booking.id,
                last_step=abandoned_booking.last_step_completed,
                booking_date=abandoned_booking.booking_date.isoformat() if abandoned_booking.booking_date else None,
                time_since_abandoned_hours=round(
                    (datetime.now() - abandoned_booking.created_at).total_seconds() / 3600, 2
                )
            )

            return abandoned_booking.booking_details

        except Exception as e:
            logger.error(
                "get_abandoned_booking_error",
                user_id=user_id,
                error=str(e)
            )
            return None

    async def _check_cart_availability(
        self,
        user_id: str,
        cart_data: Dict
    ) -> Dict:
        """
        Check availability of items in abandoned cart.

        Args:
            user_id: User ID
            cart_data: Abandoned cart data

        Returns:
            Dictionary with available/unavailable items and messages
        """
        items = cart_data.get("items", [])
        available_items = []
        unavailable_items = []

        for item in items:
            item_id = item.get("item_id")
            quantity = item.get("quantity", 1)
            item_name = item.get("name", "Unknown item")

            # Check current availability
            is_available, available_qty = await self.inventory_cache.check_availability(
                item_id,
                quantity
            )

            if is_available:
                available_items.append({
                    **item,
                    "available_quantity": available_qty
                })
            else:
                unavailable_items.append({
                    **item,
                    "available_quantity": available_qty,
                    "requested_quantity": quantity
                })

        # Generate natural messages for agent
        messages = []
        if available_items:
            item_names = [item.get("name") for item in available_items]
            messages.append({
                "type": "available",
                "message": f"Good news! {', '.join(item_names)} {'is' if len(item_names) == 1 else 'are'} still available."
            })

        if unavailable_items:
            unavailable_names = []
            for item in unavailable_items:
                name = item.get("name")
                avail = item.get("available_quantity", 0)
                if avail == 0:
                    unavailable_names.append(f"{name} (out of stock)")
                else:
                    unavailable_names.append(f"{name} (only {avail} left, you wanted {item.get('requested_quantity')})")

            messages.append({
                "type": "unavailable",
                "message": f"Unfortunately, {', '.join(unavailable_names)}."
            })

        return {
            "has_abandoned_cart": True,
            "all_items_available": len(unavailable_items) == 0,
            "some_items_available": len(available_items) > 0,
            "available_items": available_items,
            "unavailable_items": unavailable_items,
            "messages": messages,
            "total_items": len(items)
        }

    # ========================================================================
    # SAVE TO PERSISTENT STORAGE
    # ========================================================================

    async def _save_abandoned_cart_to_db(
        self,
        user_id: str,
        cart_data: Dict,
        session: AsyncSession
    ):
        """
        Save abandoned cart to database with timestamp for 2-hour restoration window.

        Args:
            user_id: User ID
            cart_data: Cart data from session cache
            session: Database session
        """
        try:
            from app.shared.models import AbandonedCart, UserDevice
            from app.utils.id_generator import generate_id
            from sqlalchemy import select, and_

            # Get device_id from cart_data if available
            device_id = cart_data.get("device_id")

            # Calculate expiry time (2 hours from now)
            expires_at = datetime.now() + timedelta(hours=self.cart_restoration_window_hours)

            # Calculate total amount
            total_amount = sum(
                item.get("price", 0) * item.get("quantity", 1)
                for item in cart_data.get("items", [])
            )

            # Check if abandoned cart already exists for this user/device
            query = select(AbandonedCart).where(
                and_(
                    AbandonedCart.user_id == user_id,
                    AbandonedCart.restored == False
                )
            )
            if device_id:
                query = query.where(AbandonedCart.device_id == device_id)

            result = await session.execute(query)
            existing_cart = result.scalar_one_or_none()

            if existing_cart:
                # Update existing abandoned cart
                existing_cart.cart_items = cart_data
                existing_cart.total_amount = total_amount
                existing_cart.expires_at = expires_at
                existing_cart.created_at = datetime.now()  # Reset created time
                cart_id = existing_cart.id
            else:
                # Create new abandoned cart
                abandoned_cart = AbandonedCart(
                    id=await generate_id(session, "abandoned_carts"),
                    user_id=user_id,
                    device_id=device_id,
                    cart_items=cart_data,
                    total_amount=total_amount,
                    expires_at=expires_at,
                    restored=False
                )
                session.add(abandoned_cart)
                cart_id = abandoned_cart.id

            await session.commit()

            logger.info(
                "abandoned_cart_saved_to_db",
                user_id=user_id,
                cart_id=cart_id,
                items_count=len(cart_data.get("items", [])),
                total_amount=total_amount,
                expires_at=expires_at.isoformat(),
                restoration_window_hours=self.cart_restoration_window_hours
            )

        except Exception as e:
            await session.rollback()
            logger.error(
                "save_abandoned_cart_error",
                user_id=user_id,
                error=str(e)
            )

    async def _save_abandoned_booking_to_db(
        self,
        user_id: str,
        booking_data: Dict,
        session: AsyncSession
    ):
        """
        Save abandoned booking to database for later recovery.

        Args:
            user_id: User ID
            booking_data: Booking data from session cache
            session: Database session
        """
        try:
            from app.features.booking.models import AbandonedBooking
            from app.utils.id_generator import generate_id
            from sqlalchemy import select, and_
            from dateutil import parser

            # Get device_id from booking_data if available
            device_id = booking_data.get("device_id")

            # Calculate expiry time (7 days from now for bookings)
            expires_at = datetime.now() + timedelta(days=7)

            # Extract booking date if available
            booking_date = None
            booking_date_str = booking_data.get("date") or booking_data.get("booking_date")
            if booking_date_str:
                try:
                    if isinstance(booking_date_str, str):
                        parsed_date = parser.parse(booking_date_str)
                        booking_date = parsed_date.date()
                except Exception:
                    pass

            # Determine last step completed
            last_step = booking_data.get("last_step_completed", "unknown")

            # Check if abandoned booking already exists for this user/device
            query = select(AbandonedBooking).where(
                and_(
                    AbandonedBooking.user_id == user_id,
                    AbandonedBooking.restored == False
                )
            )
            if device_id:
                query = query.where(AbandonedBooking.device_id == device_id)

            result = await session.execute(query)
            existing_booking = result.scalar_one_or_none()

            if existing_booking:
                # Update existing abandoned booking
                existing_booking.booking_details = booking_data
                existing_booking.expires_at = expires_at
                existing_booking.last_step_completed = last_step
                existing_booking.booking_date = booking_date
                existing_booking.created_at = datetime.now()  # Reset created time
                booking_id = existing_booking.id
            else:
                # Create new abandoned booking
                abandoned_booking = AbandonedBooking(
                    id=await generate_id(session, "abandoned_bookings"),
                    user_id=user_id,
                    device_id=device_id,
                    booking_details=booking_data,
                    expires_at=expires_at,
                    last_step_completed=last_step,
                    booking_date=booking_date,
                    restored=False
                )
                session.add(abandoned_booking)
                booking_id = abandoned_booking.id

            await session.commit()

            logger.info(
                "abandoned_booking_saved_to_db",
                user_id=user_id,
                booking_id=booking_id,
                last_step_completed=last_step,
                booking_date=booking_date.isoformat() if booking_date else None,
                expires_at=expires_at.isoformat()
            )

        except Exception as e:
            await session.rollback()
            logger.error(
                "save_abandoned_booking_error",
                user_id=user_id,
                error=str(e)
            )

    # ========================================================================
    # USER CONTEXT HELPERS
    # ========================================================================

    async def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """
        Get complete user context for agents.

        Combines session cache data with fresh database lookups if needed.

        Args:
            user_id: User ID

        Returns:
            Complete user context dictionary
        """
        try:
            # Get from session cache first
            context = await self.cache_service.get_context(user_id)

            if context:
                return context

            # If not in cache, this might be a new session
            # Load from database (will happen on first request after login)
            async with get_db_session() as session:
                user_data = await self._load_user_data_from_db(user_id, session)
                await self.cache_service.create_session(user_id, user_data)
                return user_data

        except Exception as e:
            logger.error(
                "get_user_context_error",
                user_id=user_id,
                error=str(e)
            )
            return {}

    async def update_user_preferences(
        self,
        user_id: str,
        preferences: Dict,
        session: AsyncSession
    ):
        """
        Update user preferences in both cache and database.

        Args:
            user_id: User ID
            preferences: New preferences to merge
            session: Database session
        """
        try:
            # Update in database
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()

            if user:
                # Merge preferences
                existing_prefs = user.preferences or {}
                existing_prefs.update(preferences)
                user.preferences = existing_prefs
                await session.commit()

                # Update in session cache
                await self.cache_service.update_context(
                    user_id,
                    {"preferences": existing_prefs}
                )

                logger.info(
                    "user_preferences_updated",
                    user_id=user_id,
                    preferences_keys=list(preferences.keys())
                )

        except Exception as e:
            logger.error(
                "update_preferences_error",
                user_id=user_id,
                error=str(e)
            )

    # ========================================================================
    # STATISTICS
    # ========================================================================

    async def get_active_users_count(self) -> int:
        """Get count of currently active users."""
        return await self.cache_service.get_active_sessions_count()


# Global singleton instance
_user_data_manager_instance: Optional[UserDataManager] = None


def get_user_data_manager() -> UserDataManager:
    """
    Get or create the global user data manager instance.

    Returns:
        Global user data manager singleton
    """
    global _user_data_manager_instance

    if _user_data_manager_instance is None:
        _user_data_manager_instance = UserDataManager()

    return _user_data_manager_instance

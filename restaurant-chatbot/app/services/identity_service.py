"""
Multi-Layer Identity & Personalization Service
==============================================
Handles device recognition, session tokens, and user authentication
for seamless multi-tier user experience.

Tier 1: Anonymous (no device_id)
Tier 2: Recognized device (device_id, no auth) - soft personalization
Tier 3: Authenticated (session_token or recent OTP) - full personalization
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
import secrets
import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.models import User, UserDevice, SessionToken, UserPreferences
from app.core.database import get_db_session
from app.core.config import config
import structlog

logger = structlog.get_logger("services.identity")

# Load SECRET_KEY from config
SECRET_KEY = config.SECRET_KEY
JWT_ALGORITHM = "HS256"


class IdentityService:
    """
    Multi-tier user recognition service.

    Provides:
    - Device tracking and linking
    - Session token generation and validation
    - Personalization data loading per tier
    - User upgrade from anonymous  recognized  authenticated
    """

    def __init__(self):
        self.session_token_expiry_days = 30

    async def recognize_user(
        self,
        device_id: Optional[str] = None,
        session_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Recognize user from device_id or session_token.

        Args:
            device_id: Device identifier from frontend (localStorage)
            session_token: Long-lived session token (30-day)

        Returns:
            {
                "tier": 1 | 2 | 3,
                "user_id": str | None,
                "user_name": str | None,
                "device_id": str,
                "is_authenticated": bool,
                "personalization": {
                    "preferences": {...},
                    "recent_orders": [...],
                    "greeting": str,
                    "has_order_history": bool,
                    "favorite_items": [...]
                }
            }
        """

        # TIER 3: Check session token first (highest priority)
        if session_token:
            user_data = await self._recognize_by_token(session_token)
            if user_data:
                logger.info(
                    "User recognized by session token",
                    user_id=user_data["user_id"],
                    tier=3
                )
                return {
                    **user_data,
                    "tier": 3,
                    "is_authenticated": True
                }

        # TIER 2: Check device_id (medium priority)
        if device_id:
            device_data = await self._recognize_by_device(device_id)
            if device_data and device_data.get("user_id"):
                logger.info(
                    "User recognized by device",
                    user_id=device_data["user_id"],
                    device_id=device_id,
                    tier=2
                )
                return {
                    **device_data,
                    "tier": 2,
                    "is_authenticated": False  # Soft recognition, not authenticated
                }

            # Device exists but no user linked yet
            if device_data:
                return {
                    "tier": 1,
                    "device_id": device_id,
                    "user_id": None,
                    "user_name": None,
                    "is_authenticated": False,
                    "personalization": self._get_anonymous_personalization()
                }

        # TIER 1: Anonymous
        logger.info("Anonymous user", device_id=device_id)
        return {
            "tier": 1,
            "user_id": None,
            "user_name": None,
            "device_id": device_id,
            "is_authenticated": False,
            "personalization": self._get_anonymous_personalization()
        }

    async def _recognize_by_token(
        self,
        token: str
    ) -> Optional[Dict[str, Any]]:
        """
        Validate JWT session token and load user data.

        Uses hybrid approach:
        1. Decode JWT for stateless validation (fast)
        2. Check database for revocation status (security)
        3. Update usage stats (analytics)
        """
        try:
            # Step 1: Decode and validate JWT signature and expiry
            decoded_token = jwt.decode(
                token,
                SECRET_KEY,
                algorithms=[JWT_ALGORITHM],
                options={"verify_exp": True}  # Verify expiration
            )

            # Extract claims
            token_id = decoded_token.get("jti")
            user_id = decoded_token.get("user_id")
            device_id = decoded_token.get("device_id")

            if not all([token_id, user_id]):
                logger.warning("JWT missing required claims", token_id=token_id, user_id=user_id)
                return None

        except jwt.ExpiredSignatureError:
            logger.debug("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning("Invalid JWT token", error=str(e))
            return None

        # Step 2: Check database for revocation status
        async with get_db_session() as session:
            stmt = select(SessionToken).where(
                SessionToken.id == token_id,
                SessionToken.is_revoked == False
            )
            result = await session.execute(stmt)
            token_obj = result.scalar_one_or_none()

            if not token_obj:
                logger.debug("Session token not found or revoked", token_id=token_id)
                return None

            # Step 3: Update last used timestamp and usage count
            now = datetime.now(timezone.utc)
            token_obj.last_used_at = now
            token_obj.usage_count += 1

            # SLIDING WINDOW SESSION REFRESH
            # If token expires in less than 7 days, extend it by 30 days from now
            days_until_expiry = (token_obj.expires_at - now).days
            auto_renewed = False

            if days_until_expiry < 7:
                new_expiry = now + timedelta(days=self.session_token_expiry_days)
                old_expiry = token_obj.expires_at
                token_obj.expires_at = new_expiry
                auto_renewed = True

                logger.info(
                    "Session token auto-renewed via sliding window",
                    user_id=token_obj.user_id,
                    device_id=token_obj.device_id,
                    days_until_expiry=days_until_expiry,
                    old_expiry=old_expiry.isoformat(),
                    new_expiry=new_expiry.isoformat(),
                    usage_count=token_obj.usage_count
                )

            await session.commit()

            # Step 4: Load full user data
            user_stmt = select(User).where(User.id == user_id)
            user_result = await session.execute(user_stmt)
            user = user_result.scalar_one_or_none()

            if not user:
                logger.warning("User not found for valid JWT", user_id=user_id)
                return None

            logger.debug(
                "JWT session token validated",
                user_id=user.id,
                device_id=device_id,
                usage_count=token_obj.usage_count,
                auto_renewed=auto_renewed
            )

            return {
                "user_id": user.id,
                "user_name": user.full_name,
                "user_phone": user.phone_number,  # Standardized field name
                "user_email": user.email,  # Add email to identity data
                "phone_number": user.phone_number,  # Legacy field for backward compatibility
                "full_name": user.full_name,  # Add full_name for consistency
                "email": user.email,  # Add direct email field
                "device_id": device_id,
                "auto_renewed": auto_renewed,  # Flag indicating if token was extended
                "personalization": await self._get_full_personalization(user.id, session)
            }

    async def _recognize_by_device(
        self,
        device_id: str
    ) -> Optional[Dict[str, Any]]:
        """Load user data from device_id"""
        async with get_db_session() as session:
            stmt = select(UserDevice).where(
                UserDevice.device_id == device_id,
                UserDevice.is_active == True
            )
            result = await session.execute(stmt)
            device = result.scalar_one_or_none()

            if not device:
                # Create new device record
                try:
                    from app.utils.id_generator import generate_id
                    device_db_id = await generate_id(session, "user_devices")

                    device = UserDevice(
                        id=device_db_id,
                        device_id=device_id,
                        first_seen_at=datetime.now(timezone.utc),
                        last_seen_at=datetime.now(timezone.utc)
                    )
                    session.add(device)
                    await session.commit()

                    logger.info("New device registered", device_id=device_id)
                    return {"device_id": device_id, "user_id": None}
                except Exception as e:
                    # Handle race condition - device might have been created by another request
                    await session.rollback()
                    stmt = select(UserDevice).where(
                        UserDevice.device_id == device_id,
                        UserDevice.is_active == True
                    )
                    result = await session.execute(stmt)
                    device = result.scalar_one_or_none()
                    if not device:
                        # Really failed, re-raise
                        raise e
                    logger.debug("Device was created by concurrent request", device_id=device_id)

            # Update last seen
            device.last_seen_at = datetime.now(timezone.utc)
            await session.commit()

            if not device.user_id:
                logger.debug("Device found but not linked to user", device_id=device_id)
                return {"device_id": device_id, "user_id": None}

            # Load user data
            user_stmt = select(User).where(User.id == device.user_id)
            user_result = await session.execute(user_stmt)
            user = user_result.scalar_one_or_none()

            if not user:
                logger.warning("User not found for device", device_id=device_id, user_id=device.user_id)
                return {"device_id": device_id, "user_id": None}

            logger.debug("Device recognized", device_id=device_id, user_id=user.id)

            return {
                "user_id": user.id,
                "user_name": user.full_name,
                "user_phone": user.phone_number,  # Standardized field name
                "user_email": user.email,  # Add email to identity data
                "phone_number": user.phone_number,  # Legacy field for backward compatibility
                "device_id": device_id,
                "personalization": await self._get_partial_personalization(
                    user.id, device, session
                )
            }

    async def _get_full_personalization(
        self,
        user_id: str,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Full personalization for authenticated users (Tier 3)"""

        # Load user with preferences
        user_stmt = select(User).where(User.id == user_id)
        result = await session.execute(user_stmt)
        user = result.scalar_one_or_none()

        if not user:
            return self._get_anonymous_personalization()

        # Load user preferences
        prefs_stmt = select(UserPreferences).where(UserPreferences.user_id == user_id)
        prefs_result = await session.execute(prefs_stmt)
        prefs = prefs_result.scalar_one_or_none()

        preferences = {}
        if prefs:
            preferences = {
                "dietary_restrictions": prefs.dietary_restrictions or [],
                "allergies": prefs.allergies or [],
                "favorite_cuisines": prefs.favorite_cuisines or [],
                "spice_level": prefs.spice_level,
                "preferred_seating": prefs.preferred_seating
            }

        # Load recent orders (we'll implement this when integrating with order tools)
        # For now, return empty array
        recent_orders = []

        # Generate personalized greeting
        greeting = self._generate_greeting(user.full_name, has_history=len(recent_orders) > 0)

        return {
            "preferences": preferences,
            "recent_orders": recent_orders,
            "greeting": greeting,
            "has_order_history": len(recent_orders) > 0,
            "favorite_items": self._extract_favorite_items(recent_orders)
        }

    async def _get_partial_personalization(
        self,
        user_id: str,
        device: UserDevice,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Partial personalization for recognized devices (Tier 2)"""

        # Load basic user info
        user_stmt = select(User).where(User.id == user_id)
        result = await session.execute(user_stmt)
        user = result.scalar_one_or_none()

        # Load basic preferences only
        prefs_stmt = select(UserPreferences).where(UserPreferences.user_id == user_id)
        prefs_result = await session.execute(prefs_stmt)
        prefs = prefs_result.scalar_one_or_none()

        preferences = {}
        if prefs:
            preferences = {
                "dietary_restrictions": prefs.dietary_restrictions or [],
                "spice_level": prefs.spice_level
            }

        # Limited order history from device
        last_orders = device.last_order_items or {}
        recent_orders_list = last_orders.get("orders", [])[:2]  # Last 2 only

        return {
            "preferences": preferences,
            "recent_orders": recent_orders_list,
            "greeting": "Welcome back! Ready to order?",
            "has_order_history": len(recent_orders_list) > 0,
            "favorite_items": device.preferred_items or []
        }

    def _get_anonymous_personalization(self) -> Dict[str, Any]:
        """Default personalization for anonymous users (Tier 1)"""
        import random

        greetings = [
            "Hi! How can I help you today?",
            "Welcome! What can I get for you?",
            "Hello! Ready to explore our menu?",
            "Hi there! Looking for something delicious?"
        ]

        return {
            "preferences": {},
            "recent_orders": [],
            "greeting": random.choice(greetings),
            "has_order_history": False,
            "favorite_items": []
        }

    def _generate_greeting(self, name: Optional[str], has_history: bool) -> str:
        """Generate personalized greeting based on user context"""
        now = datetime.now()
        hour = now.hour

        # Time-based greeting
        if hour < 12:
            time_greeting = "Good morning"
        elif hour < 17:
            time_greeting = "Good afternoon"
        else:
            time_greeting = "Good evening"

        # Personalized based on name and history
        if name:
            if has_history:
                return f"{time_greeting}, {name}! Want your usual?"
            else:
                return f"{time_greeting}, {name}! What can I get for you today?"
        else:
            if has_history:
                return f"{time_greeting}! Ready for another order?"
            else:
                return f"{time_greeting}! Welcome to our restaurant!"

    def _extract_favorite_items(self, orders: list) -> list:
        """Extract frequently ordered items"""
        from collections import Counter

        item_counts = Counter()
        for order in orders:
            for item in order.get("items", []):
                item_counts[item.get("name")] += 1

        return [item for item, _ in item_counts.most_common(3)]

    async def link_device_to_user(
        self,
        device_id: str,
        user_id: str
    ) -> str:
        """
        Link device to user after authentication.
        Issues a new session token.

        Args:
            device_id: Device identifier
            user_id: Authenticated user ID

        Returns:
            session_token: New session token string
        """
        async with get_db_session() as session:
            # Update or create device record
            stmt = select(UserDevice).where(UserDevice.device_id == device_id)
            result = await session.execute(stmt)
            device = result.scalar_one_or_none()

            if device:
                device.user_id = user_id
                device.last_seen_at = datetime.now(timezone.utc)
            else:
                try:
                    from app.utils.id_generator import generate_id
                    device_db_id = await generate_id(session, "user_devices")

                    device = UserDevice(
                        id=device_db_id,
                        device_id=device_id,
                        user_id=user_id,
                        first_seen_at=datetime.now(timezone.utc),
                        last_seen_at=datetime.now(timezone.utc)
                    )
                    session.add(device)
                    await session.flush()  # Flush to catch duplicate key errors
                except Exception as e:
                    # Handle race condition - device might have been created by another request
                    await session.rollback()
                    stmt = select(UserDevice).where(UserDevice.device_id == device_id)
                    result = await session.execute(stmt)
                    device = result.scalar_one_or_none()
                    if not device:
                        # Really failed, re-raise
                        raise e
                    device.user_id = user_id
                    device.last_seen_at = datetime.now(timezone.utc)
                    logger.debug("Device was created by concurrent request, linked to user", device_id=device_id)

            # Issue JWT session token (30-day expiry)
            now = datetime.now(timezone.utc)
            expiry = now + timedelta(days=self.session_token_expiry_days)

            # Generate unique token ID for revocation support
            from app.utils.id_generator import generate_id
            token_db_id = await generate_id(session, "session_tokens")

            # Create JWT payload
            jwt_payload = {
                "jti": token_db_id,  # JWT ID (for revocation lookup)
                "user_id": user_id,
                "device_id": device_id,
                "iat": int(now.timestamp()),  # Issued at
                "exp": int(expiry.timestamp()),  # Expiration time
                "type": "session"  # Token type
            }

            # Sign JWT with SECRET_KEY
            jwt_token = jwt.encode(jwt_payload, SECRET_KEY, algorithm=JWT_ALGORITHM)

            # Store in database for revocation support
            session_token = SessionToken(
                id=token_db_id,
                token=jwt_token,  # Store the JWT
                user_id=user_id,
                device_id=device_id,
                issued_at=now,
                expires_at=expiry,
                last_used_at=now,
                usage_count=0
            )
            session.add(session_token)

            await session.commit()

            logger.info(
                "Device linked to user, JWT session token issued",
                device_id=device_id,
                user_id=user_id,
                expires_at=expiry.isoformat(),
                token_id=token_db_id
            )

            return jwt_token

    async def revoke_session_token(
        self,
        token: str,
        reason: str = "user_logout"
    ) -> bool:
        """
        Revoke a session token.

        Args:
            token: Session token to revoke
            reason: Reason for revocation

        Returns:
            True if token was revoked, False if not found
        """
        async with get_db_session() as session:
            stmt = select(SessionToken).where(SessionToken.token == token)
            result = await session.execute(stmt)
            token_obj = result.scalar_one_or_none()

            if not token_obj:
                return False

            token_obj.is_revoked = True
            token_obj.revoked_at = datetime.now(timezone.utc)
            token_obj.revoked_reason = reason

            await session.commit()

            logger.info(
                "Session token revoked",
                user_id=token_obj.user_id,
                reason=reason
            )

            return True

    async def cleanup_expired_tokens(self) -> int:
        """
        Clean up expired session tokens.
        Should be run periodically (daily cron job).

        Returns:
            Number of tokens cleaned up
        """
        async with get_db_session() as session:
            from sqlalchemy import delete

            stmt = delete(SessionToken).where(
                SessionToken.expires_at < datetime.now(timezone.utc),
                SessionToken.is_revoked == False
            )

            result = await session.execute(stmt)
            await session.commit()

            count = result.rowcount

            if count > 0:
                logger.info("Expired session tokens cleaned up", count=count)

            return count


# Global service instance
identity_service = IdentityService()

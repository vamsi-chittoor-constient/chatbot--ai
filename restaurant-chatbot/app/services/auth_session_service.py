"""
Auth Session Service
===================

Manages authentication session state persistence for security and rate limiting.

Features:
- Lockout state persistence (prevents bypass via browser refresh)
- OTP send count tracking per session
- OTP verification attempt tracking
- Phone number change audit trail
- Daily OTP rate limiting per phone number

This service ensures security measures cannot be bypassed by refreshing
the browser or opening new sessions.
"""

from datetime import datetime, timedelta, timezone, date
from typing import Optional, Dict, Any, List
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.database import get_db_session
from app.shared.models import AuthSession, OTPRateLimit
from app.utils.id_generator import generate_custom_id

logger = structlog.get_logger("services.auth_session")


class AuthSessionService:
    """Service for managing authentication session state and rate limiting."""

    # Rate limiting constants
    MAX_OTP_PER_SESSION = 3  # Max OTP sends per session
    MAX_OTP_PER_DAY = 10  # Max OTP sends per phone per day
    MAX_OTP_ATTEMPTS = 3  # Max verification attempts per OTP
    LOCKOUT_DURATION_MINUTES = 15  # Lockout duration after excessive failures
    SESSION_EXPIRY_HOURS = 24  # Auth session expires after 24 hours

    async def get_or_create_session(
        self,
        device_id: Optional[str] = None,
        user_id: Optional[str] = None,
        phone_number: Optional[str] = None
    ) -> AuthSession:
        """
        Get existing auth session or create new one.

        Args:
            device_id: Device fingerprint ID
            user_id: Authenticated user ID
            phone_number: Phone number being verified

        Returns:
            AuthSession: Existing or new auth session

        Raises:
            ValueError: If both device_id and user_id are None
        """
        if not device_id and not user_id:
            raise ValueError("Either device_id or user_id must be provided")

        async with get_db_session() as session:
            # Try to find existing active session
            query = select(AuthSession).where(
                and_(
                    or_(
                        AuthSession.device_id == device_id if device_id else False,
                        AuthSession.user_id == user_id if user_id else False
                    ),
                    or_(
                        AuthSession.expires_at.is_(None),
                        AuthSession.expires_at > datetime.now()
                    )
                )
            ).order_by(AuthSession.created_at.desc())

            result = await session.execute(query)
            auth_session = result.scalars().first()

            if auth_session:
                logger.info(
                    "auth_session_found",
                    session_id=auth_session.id,
                    device_id=device_id[:12] if device_id else None,
                    user_id=user_id[:8] if user_id else None
                )
                return auth_session

            # Create new session
            new_session = AuthSession(
                id=generate_custom_id("auth_session", "ass"),
                device_id=device_id,
                user_id=user_id,
                phone_number=phone_number,
                otp_send_count=0,
                otp_verification_attempts=0,
                phone_validation_attempts=0,
                previous_phone_numbers=[],
                expires_at=datetime.now() + timedelta(hours=self.SESSION_EXPIRY_HOURS)
            )

            session.add(new_session)
            await session.commit()
            await session.refresh(new_session)

            logger.info(
                "auth_session_created",
                session_id=new_session.id,
                device_id=device_id[:12] if device_id else None,
                user_id=user_id[:8] if user_id else None
            )

            return new_session

    async def is_locked(self, auth_session: AuthSession) -> bool:
        """
        Check if session is currently locked.

        Args:
            auth_session: Auth session to check

        Returns:
            bool: True if locked
        """
        if not auth_session.locked_until:
            return False

        now = datetime.now()
        is_locked = now < auth_session.locked_until

        if is_locked:
            logger.info(
                "auth_session_locked",
                session_id=auth_session.id,
                locked_until=auth_session.locked_until.isoformat(),
                reason=auth_session.lockout_reason
            )

        return is_locked

    async def apply_lockout(
        self,
        auth_session: AuthSession,
        reason: str,
        duration_minutes: Optional[int] = None
    ) -> None:
        """
        Apply lockout to auth session.

        Args:
            auth_session: Auth session to lock
            reason: Reason for lockout
            duration_minutes: Lockout duration (default: 15 minutes)
        """
        duration = duration_minutes or self.LOCKOUT_DURATION_MINUTES
        lockout_until = datetime.now() + timedelta(minutes=duration)

        async with get_db_session() as session:
            # Merge the auth_session into this session context
            auth_session = await session.merge(auth_session)

            auth_session.locked_until = lockout_until
            auth_session.lockout_reason = reason

            await session.commit()
            await session.refresh(auth_session)

            logger.warning(
                "auth_session_locked",
                session_id=auth_session.id,
                reason=reason,
                locked_until=lockout_until.isoformat(),
                duration_minutes=duration
            )

    async def increment_otp_send_count(self, auth_session: AuthSession) -> int:
        """
        Increment OTP send count for session.

        Args:
            auth_session: Auth session

        Returns:
            int: New send count

        Raises:
            ValueError: If max sends exceeded
        """
        async with get_db_session() as session:
            # Merge the auth_session into this session context
            auth_session = await session.merge(auth_session)

            if auth_session.otp_send_count >= self.MAX_OTP_PER_SESSION:
                raise ValueError(
                    f"Maximum OTP sends ({self.MAX_OTP_PER_SESSION}) exceeded for this session"
                )

            auth_session.otp_send_count += 1
            auth_session.last_otp_sent_at = datetime.now()

            await session.commit()
            await session.refresh(auth_session)

            logger.info(
                "otp_send_count_incremented",
                session_id=auth_session.id,
                send_count=auth_session.otp_send_count,
                max_sends=self.MAX_OTP_PER_SESSION
            )

            return auth_session.otp_send_count

    async def increment_otp_verification_attempts(self, auth_session: AuthSession) -> int:
        """
        Increment OTP verification attempt count.

        Args:
            auth_session: Auth session

        Returns:
            int: New attempt count
        """
        async with get_db_session() as session:
            # Merge the auth_session into this session context
            auth_session = await session.merge(auth_session)

            auth_session.otp_verification_attempts += 1

            # Check if lockout needed
            if (auth_session.otp_verification_attempts >= self.MAX_OTP_ATTEMPTS and
                auth_session.otp_send_count >= self.MAX_OTP_PER_SESSION):
                # Apply lockout
                auth_session.locked_until = datetime.now() + timedelta(
                    minutes=self.LOCKOUT_DURATION_MINUTES
                )
                auth_session.lockout_reason = "too_many_otp_failures"
                logger.warning(
                    "lockout_applied",
                    session_id=auth_session.id,
                    reason="too_many_otp_failures"
                )

            await session.commit()
            await session.refresh(auth_session)

            logger.info(
                "otp_verification_attempts_incremented",
                session_id=auth_session.id,
                attempts=auth_session.otp_verification_attempts,
                max_attempts=self.MAX_OTP_ATTEMPTS
            )

            return auth_session.otp_verification_attempts

    async def reset_otp_state(self, auth_session: AuthSession) -> None:
        """
        Reset OTP verification state (for resend).

        Args:
            auth_session: Auth session
        """
        async with get_db_session() as session:
            # Merge the auth_session into this session context
            auth_session = await session.merge(auth_session)

            auth_session.otp_verification_attempts = 0

            await session.commit()
            await session.refresh(auth_session)

            logger.info(
                "otp_state_reset",
                session_id=auth_session.id
            )

    async def track_phone_change(
        self,
        auth_session: AuthSession,
        old_phone: str,
        new_phone: str
    ) -> None:
        """
        Track phone number change for audit trail.

        Args:
            auth_session: Auth session
            old_phone: Previous phone number
            new_phone: New phone number
        """
        async with get_db_session() as session:
            # Merge the auth_session into this session context
            auth_session = await session.merge(auth_session)

            if old_phone not in (auth_session.previous_phone_numbers or []):
                if auth_session.previous_phone_numbers is None:
                    auth_session.previous_phone_numbers = []
                auth_session.previous_phone_numbers.append(old_phone)

            auth_session.phone_number = new_phone

            # Reset OTP state for new phone
            auth_session.otp_send_count = 0
            auth_session.otp_verification_attempts = 0
            auth_session.last_otp_sent_at = None

            await session.commit()
            await session.refresh(auth_session)

            logger.info(
                "phone_number_changed",
                session_id=auth_session.id,
                old_phone=old_phone[-4:],
                new_phone=new_phone[-4:],
                audit_trail_length=len(auth_session.previous_phone_numbers or [])
            )

    async def check_daily_otp_limit(self, phone_number: str) -> Dict[str, Any]:
        """
        Check if phone number has exceeded daily OTP limit.

        Args:
            phone_number: Phone number to check

        Returns:
            Dict with keys:
                - can_send: bool
                - send_count: int
                - max_sends: int
                - message: str
        """
        today = date.today()

        async with get_db_session() as session:
            # Find or create rate limit record for today
            query = select(OTPRateLimit).where(
                and_(
                    OTPRateLimit.phone_number == phone_number,
                    OTPRateLimit.date == today
                )
            )
            result = await session.execute(query)
            rate_limit = result.scalars().first()

            if not rate_limit:
                # No sends today yet
                return {
                    "can_send": True,
                    "send_count": 0,
                    "max_sends": self.MAX_OTP_PER_DAY,
                    "message": "No OTP sends today yet"
                }

            can_send = rate_limit.send_count < self.MAX_OTP_PER_DAY

            if not can_send:
                logger.warning(
                    "daily_otp_limit_exceeded",
                    phone_number=phone_number[-4:],
                    send_count=rate_limit.send_count,
                    max_sends=self.MAX_OTP_PER_DAY
                )

            return {
                "can_send": can_send,
                "send_count": rate_limit.send_count,
                "max_sends": self.MAX_OTP_PER_DAY,
                "message": (
                    f"Daily limit reached ({self.MAX_OTP_PER_DAY} sends). Try again tomorrow."
                    if not can_send
                    else f"{rate_limit.send_count} of {self.MAX_OTP_PER_DAY} sends used today"
                )
            }

    async def increment_daily_otp_count(self, phone_number: str) -> int:
        """
        Increment daily OTP send count for phone number.

        Args:
            phone_number: Phone number

        Returns:
            int: New send count for today

        Raises:
            ValueError: If daily limit exceeded
        """
        today = date.today()
        now = datetime.now()

        async with get_db_session() as session:
            # Find or create rate limit record
            query = select(OTPRateLimit).where(
                and_(
                    OTPRateLimit.phone_number == phone_number,
                    OTPRateLimit.date == today
                )
            )
            result = await session.execute(query)
            rate_limit = result.scalars().first()

            if rate_limit:
                # Check limit
                if rate_limit.send_count >= self.MAX_OTP_PER_DAY:
                    raise ValueError(
                        f"Daily OTP limit ({self.MAX_OTP_PER_DAY}) exceeded. Try again tomorrow."
                    )

                rate_limit.send_count += 1
                rate_limit.last_sent_at = now
            else:
                # Create new record
                rate_limit = OTPRateLimit(
                    id=generate_custom_id("otp_rate_limit", "orl"),
                    phone_number=phone_number,
                    date=today,
                    send_count=1,
                    first_sent_at=now,
                    last_sent_at=now
                )
                session.add(rate_limit)

            await session.commit()
            await session.refresh(rate_limit)

            logger.info(
                "daily_otp_count_incremented",
                phone_number=phone_number[-4:],
                send_count=rate_limit.send_count,
                max_sends=self.MAX_OTP_PER_DAY,
                date=today.isoformat()
            )

            return rate_limit.send_count

    async def get_session_state(self, auth_session: AuthSession) -> Dict[str, Any]:
        """
        Get current state of auth session for agent.

        Args:
            auth_session: Auth session

        Returns:
            Dict with session state information
        """
        is_locked = await self.is_locked(auth_session)

        return {
            "session_id": auth_session.id,
            "device_id": auth_session.device_id,
            "user_id": auth_session.user_id,
            "phone_number": auth_session.phone_number,
            "otp_send_count": auth_session.otp_send_count,
            "max_otp_sends": self.MAX_OTP_PER_SESSION,
            "can_send_otp": auth_session.otp_send_count < self.MAX_OTP_PER_SESSION,
            "otp_verification_attempts": auth_session.otp_verification_attempts,
            "max_otp_attempts": self.MAX_OTP_ATTEMPTS,
            "can_retry_otp": auth_session.otp_verification_attempts < self.MAX_OTP_ATTEMPTS,
            "last_otp_sent_at": auth_session.last_otp_sent_at.isoformat() if auth_session.last_otp_sent_at else None,
            "is_locked": is_locked,
            "locked_until": auth_session.locked_until.isoformat() if auth_session.locked_until else None,
            "lockout_reason": auth_session.lockout_reason,
            "previous_phone_numbers": auth_session.previous_phone_numbers or [],
            "created_at": auth_session.created_at.isoformat() if auth_session.created_at else None,
            "expires_at": auth_session.expires_at.isoformat() if auth_session.expires_at else None
        }


# Singleton instance
_auth_session_service: Optional[AuthSessionService] = None


def get_auth_session_service() -> AuthSessionService:
    """
    Get singleton auth session service instance.

    Returns:
        AuthSessionService: Singleton instance
    """
    global _auth_session_service
    if _auth_session_service is None:
        _auth_session_service = AuthSessionService()
    return _auth_session_service

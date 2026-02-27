"""
Authentication State Service
============================
Manages authentication state per session in Redis.

Tracks the authentication flow progress:
- Step 1: Collecting phone number
- Step 2: OTP sent, waiting for verification
- Step 3: Verified, collecting name (for new users)
- Step 4: Authenticated

This enables the auth gate in the main message processor to handle
authentication before passing control to the CrewAI agent.
"""

import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import structlog

from app.core.redis import get_sync_redis_client

logger = structlog.get_logger("services.auth_state")


class AuthStep(str, Enum):
    """Authentication flow steps"""
    COLLECT_PHONE = "collect_phone"       # Need phone number
    OTP_SENT = "otp_sent"                  # OTP sent, awaiting verification
    COLLECT_NAME = "collect_name"          # OTP verified, need name (new user)
    AUTHENTICATED = "authenticated"         # Fully authenticated


def _get_auth_key(session_id: str) -> str:
    """Get Redis key for auth state"""
    return f"auth_state:{session_id}"


def get_auth_state(session_id: str) -> Dict[str, Any]:
    """
    Get current authentication state for a session.

    Returns:
        Dict with:
        - step: Current auth step
        - phone: Phone number (if collected)
        - user_id: User ID (if authenticated)
        - user_name: User name (if known)
        - is_new_user: Whether this is a new registration
        - authenticated: Boolean if fully authenticated
    """
    redis = get_sync_redis_client()
    key = _get_auth_key(session_id)

    try:
        data = redis.get(key)
        if data:
            state = json.loads(data)
            logger.debug("auth_state_loaded", session_id=session_id, step=state.get("step"))
            return state
    except Exception as e:
        logger.warning("auth_state_load_failed", session_id=session_id, error=str(e))

    # Default state - need to collect phone
    return {
        "step": AuthStep.COLLECT_PHONE.value,
        "phone": None,
        "user_id": None,
        "user_name": None,
        "is_new_user": False,
        "authenticated": False,
        "otp_sent_at": None,
        "created_at": datetime.now().isoformat()
    }


def set_auth_state(session_id: str, state: Dict[str, Any], ttl_hours: int = 24) -> bool:
    """
    Save authentication state for a session.

    Args:
        session_id: Session identifier
        state: State dict to save
        ttl_hours: Time to live in hours (default 24)

    Returns:
        True if saved successfully
    """
    redis = get_sync_redis_client()
    key = _get_auth_key(session_id)

    try:
        state["updated_at"] = datetime.now().isoformat()
        redis.setex(key, timedelta(hours=ttl_hours), json.dumps(state))
        logger.debug("auth_state_saved", session_id=session_id, step=state.get("step"))
        return True
    except Exception as e:
        logger.error("auth_state_save_failed", session_id=session_id, error=str(e))
        return False


def update_auth_step(
    session_id: str,
    step: AuthStep,
    phone: Optional[str] = None,
    user_id: Optional[str] = None,
    user_name: Optional[str] = None,
    is_new_user: bool = False
) -> Dict[str, Any]:
    """
    Update authentication step for a session.

    Args:
        session_id: Session identifier
        step: New auth step
        phone: Phone number (optional)
        user_id: User ID (optional)
        user_name: User name (optional)
        is_new_user: Whether this is a new user registration

    Returns:
        Updated state dict
    """
    state = get_auth_state(session_id)

    state["step"] = step.value

    if phone:
        state["phone"] = phone
    if user_id:
        state["user_id"] = user_id
    if user_name:
        state["user_name"] = user_name

    state["is_new_user"] = is_new_user
    state["authenticated"] = (step == AuthStep.AUTHENTICATED)

    if step == AuthStep.OTP_SENT:
        state["otp_sent_at"] = datetime.now().isoformat()

    set_auth_state(session_id, state)

    logger.info(
        "auth_step_updated",
        session_id=session_id,
        step=step.value,
        phone=phone[-4:] if phone else None,
        authenticated=state["authenticated"]
    )

    return state


def mark_authenticated(
    session_id: str,
    user_id: str,
    user_name: Optional[str] = None,
    phone: Optional[str] = None,
    is_new_user: bool = False
) -> Dict[str, Any]:
    """
    Mark session as fully authenticated.

    Args:
        session_id: Session identifier
        user_id: Authenticated user ID
        user_name: User's name
        phone: User's phone number
        is_new_user: Whether this was a new registration

    Returns:
        Updated state dict
    """
    state = get_auth_state(session_id)

    state["step"] = AuthStep.AUTHENTICATED.value
    state["user_id"] = user_id
    state["user_name"] = user_name
    state["phone"] = phone
    state["is_new_user"] = is_new_user
    state["authenticated"] = True
    state["authenticated_at"] = datetime.now().isoformat()

    set_auth_state(session_id, state)

    logger.info(
        "session_authenticated",
        session_id=session_id,
        user_id=user_id,
        user_name=user_name,
        is_new_user=is_new_user
    )

    return state


def is_authenticated(session_id: str) -> bool:
    """Check if session is authenticated."""
    state = get_auth_state(session_id)
    return state.get("authenticated", False)


def clear_auth_state(session_id: str) -> bool:
    """Clear authentication state for a session (logout)."""
    redis = get_sync_redis_client()
    key = _get_auth_key(session_id)

    try:
        redis.delete(key)
        logger.info("auth_state_cleared", session_id=session_id)
        return True
    except Exception as e:
        logger.error("auth_state_clear_failed", session_id=session_id, error=str(e))
        return False


# Phone number validation helpers
def is_valid_phone(phone: str) -> bool:
    """
    Validate phone number format.
    Accepts formats like:
    - +919566070120
    - 9566070120
    - 91-9566070120
    """
    import re
    # Remove spaces, dashes
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)

    # Check if it's a valid phone number (10-15 digits, optionally starting with +)
    pattern = r'^\+?[1-9]\d{9,14}$'
    return bool(re.match(pattern, cleaned))


def normalize_phone(phone: str) -> str:
    """
    Normalize phone number to E.164 format.
    Adds +91 prefix if not present (assuming India).
    """
    import re
    # Remove all non-digit characters except +
    cleaned = re.sub(r'[^\d+]', '', phone)

    # If it doesn't start with +, assume India (+91)
    if not cleaned.startswith('+'):
        if cleaned.startswith('91') and len(cleaned) == 12:
            cleaned = '+' + cleaned
        elif len(cleaned) == 10:
            cleaned = '+91' + cleaned

    return cleaned

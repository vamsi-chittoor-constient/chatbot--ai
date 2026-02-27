"""
Security Utilities
HMAC signature validation for webhook requests
"""

import hmac
import hashlib
import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


def generate_hmac_signature(payload: str, secret: str) -> str:
    """
    Generate HMAC-SHA256 signature for payload

    Args:
        payload: Request body as string
        secret: Secret key for HMAC

    Returns:
        Hexadecimal signature string
    """
    signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    return signature


def verify_webhook_signature(payload: str, received_signature: Optional[str]) -> bool:
    """
    Verify HMAC signature from Petpooja webhook

    Args:
        payload: Raw request body as string
        received_signature: Signature from X-Signature header

    Returns:
        True if signature is valid, False otherwise

    Security:
        - Uses constant-time comparison to prevent timing attacks
        - Validates against configured WEBHOOK_SECRET
    """
    if not received_signature:
        logger.warning("Webhook signature missing")
        return False

    if not settings.WEBHOOK_SECRET:
        logger.error("WEBHOOK_SECRET not configured")
        return False

    try:
        # Generate expected signature
        expected_signature = generate_hmac_signature(payload, settings.WEBHOOK_SECRET)

        # Constant-time comparison to prevent timing attacks
        is_valid = hmac.compare_digest(expected_signature, received_signature)

        if not is_valid:
            logger.warning(f"Invalid webhook signature. Expected: {expected_signature[:10]}..., Got: {received_signature[:10]}...")

        return is_valid

    except Exception as e:
        logger.error(f"Signature verification error: {e}")
        return False


def verify_main_backend_token(token: Optional[str]) -> bool:
    """
    Verify authentication token from main backend

    Args:
        token: Bearer token from Authorization header

    Returns:
        True if token is valid, False otherwise
    """
    if not token:
        return False

    # Remove 'Bearer ' prefix if present
    token = token.replace("Bearer ", "")

    return token == settings.MAIN_BACKEND_API_TOKEN

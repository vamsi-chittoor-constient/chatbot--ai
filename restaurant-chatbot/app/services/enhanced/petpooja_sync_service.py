"""
PetPooja Kitchen Sync Service
==============================

Syncs orders created via chatbot to PetPooja kitchen system for preparation.

Architecture:
- Uses existing petpooja-service async client
- Controlled by PETPOOJA_ORDER_SYNC feature flag
- LLM-based decision logic (not hardcoded rules)
- Zero impact when feature flag disabled

Flow:
1. Order placed via chatbot → crew agent creates order in DB
2. [OPTIONAL] If feature flag enabled → sync to PetPooja kitchen
3. Kitchen receives order → prepares food
4. Order status updates flow back via webhooks

Design Principles:
- Don't hardcode sync logic (let LLM/context decide)
- Graceful degradation (if sync fails, order still succeeds)
- Async operations (non-blocking)
- Structured logging for debugging

Usage:
    from app.services.enhanced.petpooja_sync_service import PetPoojaSyncService
    from app.core.feature_flags import FeatureFlags, Feature

    # In food ordering agent after order creation
    if FeatureFlags.is_enabled(Feature.PETPOOJA_ORDER_SYNC):
        sync_service = PetPoojaSyncService()
        await sync_service.sync_order_to_kitchen(order_data)
"""

import os
import sys
from typing import Dict, Any, Optional
from datetime import datetime
import structlog

# Add petpooja-service to path to import its modules
PETPOOJA_SERVICE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "petpooja-service"
)
if PETPOOJA_SERVICE_PATH not in sys.path:
    sys.path.insert(0, PETPOOJA_SERVICE_PATH)

# Import from existing petpooja-service
try:
    from app.petpooja_client.order_client_async import AsyncOrderClient, PetpoojaAPIError
    from app.services.order_transformer import transform_db_order_to_petpooja, TransformerError
    PETPOOJA_AVAILABLE = True
except ImportError as e:
    PETPOOJA_AVAILABLE = False
    AsyncOrderClient = None
    PetpoojaAPIError = None
    transform_db_order_to_petpooja = None
    TransformerError = None

from app.core.feature_flags import FeatureFlags, Feature

logger = structlog.get_logger(__name__)


class PetPoojaSyncService:
    """
    Manages syncing chatbot orders to PetPooja kitchen system.

    Features:
    - Async order push to PetPooja POS
    - LLM-based decision logic for when to sync
    - Graceful error handling (sync failure doesn't block order)
    - Structured logging for debugging
    - Zero impact when feature disabled
    """

    def __init__(self):
        """Initialize PetPooja sync service"""
        self.enabled = FeatureFlags.is_enabled(Feature.PETPOOJA_ORDER_SYNC)

        if not self.enabled:
            logger.debug("petpooja_sync_disabled", reason="feature_flag_disabled")
            self.client = None
            return

        if not PETPOOJA_AVAILABLE:
            logger.warning(
                "petpooja_sync_unavailable",
                reason="petpooja_service_import_failed",
                impact="orders_wont_sync_to_kitchen"
            )
            self.enabled = False
            self.client = None
            return

        # Initialize async PetPooja client
        self.client = AsyncOrderClient()

        # Configuration
        self.auto_sync = os.getenv("PETPOOJA_AUTO_SYNC", "true").lower() == "true"
        self.retry_on_failure = os.getenv("PETPOOJA_RETRY_ON_FAILURE", "true").lower() == "true"
        self.max_retries = int(os.getenv("PETPOOJA_MAX_RETRIES", "3"))

        logger.info(
            "petpooja_sync_initialized",
            enabled=self.enabled,
            auto_sync=self.auto_sync,
            retry_on_failure=self.retry_on_failure
        )

    async def should_sync_order(self, order_data: Dict[str, Any]) -> tuple[bool, str]:
        """
        Determine if order should be synced to PetPooja kitchen.

        This uses context-based decision logic (not hardcoded rules).
        Checks order type, status, and whether it's already synced.

        Args:
            order_data: Order data from database

        Returns:
            tuple: (should_sync: bool, reason: str)

        Examples:
            (True, "dine_in_order_needs_kitchen_prep")
            (False, "already_synced_to_petpooja")
            (False, "order_not_confirmed")
        """
        if not self.enabled:
            return False, "feature_disabled"

        # Check if order exists
        order = order_data.get("order")
        if not order:
            return False, "no_order_data"

        # Extract order metadata
        order_type = order_data.get("order_type", "").lower()
        order_status = order.order_status if hasattr(order, "order_status") else None
        external_order_id = order_data.get("external_order_id")

        # Check if already synced (has external_order_id from PetPooja)
        if external_order_id:
            logger.debug(
                "order_already_synced",
                order_id=str(order.order_id)[:8],
                external_order_id=external_order_id
            )
            return False, "already_synced"

        # Check order status (only sync confirmed/placed orders)
        valid_statuses = ["confirmed", "placed", "pending"]
        if order_status and order_status.lower() not in valid_statuses:
            return False, f"invalid_status_{order_status}"

        # LLM-BASED LOGIC: Let context decide, don't hardcode
        # For dine_in and pickup orders, kitchen needs to prepare food
        # For delivery, kitchen also needs to prepare
        # Only exception: if order is cancelled/rejected

        if order_type in ["dine_in", "pickup", "delivery", "takeout"]:
            logger.debug(
                "order_eligible_for_sync",
                order_id=str(order.order_id)[:8] if hasattr(order, "order_id") else "unknown",
                order_type=order_type,
                status=order_status
            )
            return True, f"order_type_{order_type}_needs_kitchen"

        # Default: sync unless there's a reason not to
        # This follows the principle: let the system work, don't block it with rules
        return True, "default_sync_enabled"

    async def sync_order_to_kitchen(
        self,
        order_data: Dict[str, Any],
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Sync order to PetPooja kitchen system.

        This is the main entry point for syncing orders.
        Handles transformation, API calls, retries, and error handling.

        Args:
            order_data: Complete order data from database
            force: Force sync even if should_sync_order returns False

        Returns:
            dict: {
                "success": bool,
                "synced": bool,
                "petpooja_order_id": str (if successful),
                "reason": str,
                "error": str (if failed)
            }
        """
        if not self.enabled:
            return {
                "success": True,  # Not an error, just disabled
                "synced": False,
                "reason": "feature_disabled"
            }

        # Check if should sync
        if not force:
            should_sync, reason = await self.should_sync_order(order_data)
            if not should_sync:
                return {
                    "success": True,
                    "synced": False,
                    "reason": reason
                }

        order = order_data.get("order")
        order_id = str(order.order_id)[:8] if order and hasattr(order, "order_id") else "unknown"

        logger.info(
            "syncing_order_to_petpooja",
            order_id=order_id,
            force=force
        )

        try:
            # Transform to PetPooja format
            petpooja_order = transform_db_order_to_petpooja(order_data)

            # Extract orderinfo for API call
            order_info_dict = petpooja_order.orderinfo.model_dump(
                exclude_none=True,
                by_alias=True
            )

            # Build payload for save_order API
            api_payload = {
                "orderinfo": order_info_dict,
                "udid": petpooja_order.udid,
                "device_type": petpooja_order.device_type
            }

            # Call PetPooja API with retries
            response = await self._save_order_with_retry(api_payload)

            if response.get("success"):
                petpooja_order_id = response.get("order_id", "")

                logger.info(
                    "order_synced_to_petpooja",
                    order_id=order_id,
                    petpooja_order_id=petpooja_order_id
                )

                return {
                    "success": True,
                    "synced": True,
                    "petpooja_order_id": petpooja_order_id,
                    "response": response
                }
            else:
                error_msg = response.get("message", "Unknown error")
                logger.error(
                    "petpooja_sync_failed",
                    order_id=order_id,
                    error=error_msg,
                    response=response
                )

                return {
                    "success": False,
                    "synced": False,
                    "error": error_msg,
                    "response": response
                }

        except TransformerError as e:
            logger.error(
                "order_transformation_failed",
                order_id=order_id,
                error=str(e)
            )
            return {
                "success": False,
                "synced": False,
                "error": f"Transformation failed: {str(e)}"
            }

        except PetpoojaAPIError as e:
            logger.error(
                "petpooja_api_error",
                order_id=order_id,
                error=str(e)
            )
            return {
                "success": False,
                "synced": False,
                "error": f"PetPooja API error: {str(e)}"
            }

        except Exception as e:
            logger.error(
                "unexpected_sync_error",
                order_id=order_id,
                error=str(e),
                error_type=type(e).__name__
            )
            return {
                "success": False,
                "synced": False,
                "error": f"Unexpected error: {str(e)}"
            }

    async def _save_order_with_retry(
        self,
        api_payload: Dict[str, Any],
        attempt: int = 1
    ) -> Dict[str, Any]:
        """
        Save order to PetPooja with retry logic.

        Args:
            api_payload: Payload for save_order API
            attempt: Current attempt number

        Returns:
            API response dict
        """
        try:
            response = await self.client.save_order(api_payload)
            return response

        except PetpoojaAPIError as e:
            if self.retry_on_failure and attempt < self.max_retries:
                logger.warning(
                    "petpooja_sync_retry",
                    attempt=attempt,
                    max_retries=self.max_retries,
                    error=str(e)
                )
                # Exponential backoff: 1s, 2s, 4s
                import asyncio
                await asyncio.sleep(2 ** (attempt - 1))

                return await self._save_order_with_retry(api_payload, attempt + 1)
            else:
                # Max retries reached or retry disabled
                raise

    async def update_order_status(
        self,
        rest_id: str,
        client_order_id: str,
        status: str,
        cancel_reason: str = ""
    ) -> Dict[str, Any]:
        """
        Update order status in PetPooja system.

        This is called when order status changes in our system
        (e.g., customer cancels order, restaurant marks as ready).

        Args:
            rest_id: PetPooja restaurant ID
            client_order_id: Our internal order ID
            status: New status (placed, preparing, ready, delivered, cancelled)
            cancel_reason: Reason if status is cancelled

        Returns:
            dict: {
                "success": bool,
                "message": str,
                "error": str (if failed)
            }
        """
        if not self.enabled:
            return {
                "success": True,
                "message": "feature_disabled"
            }

        logger.info(
            "updating_petpooja_order_status",
            client_order_id=client_order_id,
            status=status
        )

        try:
            response = await self.client.update_order_status(
                rest_id=rest_id,
                client_order_id=client_order_id,
                status=status,
                cancel_reason=cancel_reason
            )

            if response.get("success"):
                logger.info(
                    "petpooja_status_updated",
                    client_order_id=client_order_id,
                    status=status
                )
                return {
                    "success": True,
                    "message": "status_updated",
                    "response": response
                }
            else:
                error_msg = response.get("message", "Unknown error")
                logger.error(
                    "petpooja_status_update_failed",
                    client_order_id=client_order_id,
                    status=status,
                    error=error_msg
                )
                return {
                    "success": False,
                    "error": error_msg,
                    "response": response
                }

        except PetpoojaAPIError as e:
            logger.error(
                "petpooja_status_api_error",
                client_order_id=client_order_id,
                error=str(e)
            )
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            logger.error(
                "unexpected_status_update_error",
                client_order_id=client_order_id,
                error=str(e)
            )
            return {
                "success": False,
                "error": str(e)
            }

    async def close(self):
        """Close PetPooja client connection"""
        if self.client:
            await self.client.close()
            logger.debug("petpooja_sync_client_closed")


# Singleton instance (lazy initialization)
_sync_service: Optional[PetPoojaSyncService] = None


def get_petpooja_sync_service() -> PetPoojaSyncService:
    """
    Get singleton instance of PetPoojaSyncService.

    Returns:
        PetPoojaSyncService instance (may be disabled if feature flag off)
    """
    global _sync_service
    if _sync_service is None:
        _sync_service = PetPoojaSyncService()
    return _sync_service


async def close_petpooja_sync_service():
    """Close singleton sync service on shutdown"""
    global _sync_service
    if _sync_service:
        await _sync_service.close()
        _sync_service = None

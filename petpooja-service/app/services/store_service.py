"""
Store Service - Handles restaurant store status operations (ASYNC VERSION)
"""

import logging
from typing import Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.schemas.webhook import StoreStatus
from app.core.db_session_async import AsyncSessionLocal
from app.models.branch_models import BranchInfoTable, BranchTimingPolicy
from app.models.other_models import RestaurantTable

logger = logging.getLogger(__name__)


class StoreServiceError(Exception):
    pass


async def get_store_status(restaurant_id: str) -> Dict[str, Any]:
    """
    Check restaurant store status - ASYNC VERSION

    Args:
        restaurant_id: PetPooja restaurant ID

    Returns:
        Dict with store status
    """
    async with AsyncSessionLocal() as db:
        try:
            # Find branch by PetPooja restaurant ID
            branch_result = await db.execute(
                select(BranchInfoTable).where(
                    BranchInfoTable.ext_petpooja_restaurant_id == restaurant_id,
                    BranchInfoTable.is_deleted == False
                )
            )
            branch = branch_result.scalar_one_or_none()

            if not branch:
                return {
                    "status": "success",
                    "store_status": StoreStatus.OPEN,
                    "http_code": 200,
                    "message": "Store is open (default)"
                }

            is_active = branch.is_active if branch.is_active is not None else True

            # Check restaurant timing policy
            restaurant_result = await db.execute(
                select(RestaurantTable).where(
                    RestaurantTable.branch_id == branch.branch_id,
                    RestaurantTable.is_deleted == False
                )
            )
            restaurant = restaurant_result.scalar_one_or_none()
            is_within_hours = True

            if restaurant:
                timing_result = await db.execute(
                    select(BranchTimingPolicy).where(
                        BranchTimingPolicy.restaurant_id == restaurant.restaurant_id,
                        BranchTimingPolicy.is_deleted == False
                    )
                )
                timing_policy = timing_result.scalar_one_or_none()

                if timing_policy:
                    is_within_hours = check_business_hours(timing_policy)

            is_open = is_active and is_within_hours
            store_status = StoreStatus.OPEN if is_open else StoreStatus.CLOSED

            return {
                "status": "success",
                "store_status": store_status,
                "http_code": 200,
                "message": f"Store is {StoreStatus.get_status_text(store_status).lower()}"
            }

        except Exception as e:
            logger.error(f"Error checking store status: {str(e)}")
            return {
                "status": "success",
                "store_status": StoreStatus.OPEN,
                "http_code": 200,
                "message": "Store is open (default on error)"
            }


def check_business_hours(timing_policy: BranchTimingPolicy) -> bool:
    current_time = datetime.now().time()

    start_time = timing_policy.food_ordering_start_time
    end_time = timing_policy.food_ordering_closing_time

    if start_time and end_time:
        if start_time > end_time:
            return current_time >= start_time or current_time <= end_time
        return start_time <= current_time <= end_time

    opening_time = timing_policy.opening_time
    closing_time = timing_policy.closing_time

    if opening_time and closing_time:
        if opening_time > closing_time:
            return current_time >= opening_time or current_time <= closing_time
        return opening_time <= current_time <= closing_time

    return True


async def update_store_status_from_webhook(
    restaurant_id: str, store_status: str, turn_on_time: str = "", reason: str = ""
) -> Dict[str, Any]:
    """
    Update restaurant store status from PetPooja webhook - ASYNC VERSION

    Args:
        restaurant_id: PetPooja restaurant ID
        store_status: "1" for Open, "0" for Closed
        turn_on_time: Next opening time (when closing)
        reason: Reason for closing

    Returns:
        Dict with update result
    """
    async with AsyncSessionLocal() as db:
        try:
            is_open = store_status == StoreStatus.OPEN
            status_text = StoreStatus.get_status_text(store_status)

            # Find branch by PetPooja restaurant ID
            branch_result = await db.execute(
                select(BranchInfoTable).where(
                    BranchInfoTable.ext_petpooja_restaurant_id == restaurant_id,
                    BranchInfoTable.is_deleted == False
                )
            )
            branch = branch_result.scalar_one_or_none()

            if not branch:
                return {
                    "status": "failed",
                    "store_status": store_status,
                    "message": f"Restaurant not found: {restaurant_id}"
                }

            # Update store status
            branch.is_active = is_open
            branch.updated_at = datetime.utcnow()
            await db.commit()

            logger.info(
                f"Store status updated - Restaurant: {restaurant_id}, "
                f"Status: {status_text}, Reason: {reason or 'N/A'}"
            )

            return {
                "status": "success",
                "store_status": store_status,
                "message": f"Store {status_text.lower()} successfully"
            }

        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating store status: {str(e)}")
            return {
                "status": "failed",
                "store_status": store_status,
                "message": f"Error: {str(e)}"
            }

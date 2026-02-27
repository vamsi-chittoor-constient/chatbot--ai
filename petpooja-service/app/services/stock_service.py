"""
Stock Service
Handles item/addon stock updates from PetPooja
"""

import logging
from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select

from app.core.db_session_async import AsyncSessionLocal
from app.models.menu_models import MenuItem, MenuItemAddonItem
from app.models.branch_models import BranchInfoTable

logger = logging.getLogger(__name__)


class StockServiceError(Exception):
    """Custom exception for stock service errors"""
    pass


async def process_stock_update(
    restaurant_id: str,
    in_stock: bool,
    item_type: str,
    item_ids_dict: dict,
    auto_turn_on_time: str = "",
    custom_turn_on_time: str = ""
) -> Dict[str, Any]:
    """
    Process stock update webhook from PetPooja

    Called when restaurant marks items/addons as available or unavailable

    Args:
        restaurant_id: Restaurant ID
        in_stock: True if marking as available, False if out of stock
        item_type: 'item' or 'addon'
        item_ids_dict: Dict of item/addon IDs
        auto_turn_on_time: Auto turn-on setting ('endofday', 'custom', or empty)
        custom_turn_on_time: Custom datetime to turn back on (ISO format)

    Returns:
        Dict containing result

    Example:
        {
            "code": "200",
            "status": "success",
            "message": "Stock status updated successfully"
        }
    """
    try:
        # Convert dict to list of IDs
        item_ids = list(item_ids_dict.values()) if isinstance(item_ids_dict, dict) else []

        if not item_ids:
            logger.warning(f"No items provided for stock update: {restaurant_id}")
            return {
                "code": "400",
                "status": "failed",
                "message": "No items provided for stock update"
            }

        # Validate autoTurnOnTime when marking out of stock
        if not in_stock and not auto_turn_on_time:
            logger.warning(f"autoTurnOnTime required when marking items out of stock: {restaurant_id}")
            return {
                "code": "400",
                "status": "failed",
                "message": "autoTurnOnTime is required when marking items out of stock"
            }

        logger.info(
            f"Stock update - Restaurant: {restaurant_id}, "
            f"Type: {item_type}, InStock: {in_stock}, "
            f"Items: {len(item_ids)}, AutoTurnOn: {auto_turn_on_time}"
        )

        # Update stock based on type
        if item_type == 'item':
            await update_item_stock(
                restaurant_id,
                item_ids,
                in_stock,
                auto_turn_on_time,
                custom_turn_on_time
            )
        elif item_type == 'addon':
            await update_addon_stock(
                restaurant_id,
                item_ids,
                in_stock,
                auto_turn_on_time,
                custom_turn_on_time
            )
        else:
            logger.error(f"Invalid item type: {item_type}")
            return {
                "code": "400",
                "status": "failed",
                "message": f"Invalid type. Must be 'item' or 'addon'"
            }

        logger.info(f"Stock update successful: {len(item_ids)} {item_type}s updated")

        return {
            "code": "200",
            "status": "success",
            "message": "Stock status updated successfully"
        }

    except Exception as e:
        logger.error(f"Error processing stock update: {str(e)}", exc_info=True)
        return {
            "code": "400",
            "status": "failed",
            "message": "Stock status not updated successfully"
        }


async def update_item_stock(
    restaurant_id: str,
    item_ids: List[str],
    in_stock: bool,
    auto_turn_on_time: str = "",
    custom_turn_on_time: str = ""
):
    """
    Update menu item stock status

    Args:
        restaurant_id: Restaurant ID (PetPooja restaurant ID)
        item_ids: List of PetPooja item IDs to update
        in_stock: Stock availability status
        auto_turn_on_time: Auto turn-on setting
        custom_turn_on_time: Custom turn-on datetime
    """
    logger.info(f"Updating {len(item_ids)} items for restaurant {restaurant_id}")

    # Get async database session
    async with AsyncSessionLocal() as db:
        # First, find the branch by PetPooja restaurant ID
        branch_result = await db.execute(
            select(BranchInfoTable).where(
                BranchInfoTable.ext_petpooja_restaurant_id == restaurant_id,
                BranchInfoTable.is_deleted == False
            )
        )
        branch = branch_result.scalar_one_or_none()

        if not branch:
            logger.warning(f"Branch not found for PetPooja restaurant ID: {restaurant_id}")
            return

        # Update all items with the given PetPooja IDs
        result = await db.execute(
            update(MenuItem)
            .where(
                MenuItem.ext_petpooja_item_id.in_(item_ids),
                MenuItem.restaurant_id == branch.branch_id,  # Match by branch_id
                MenuItem.is_deleted == False
            )
            .values(
                menu_item_in_stock=in_stock,
                updated_at=datetime.utcnow()
            )
        )

        await db.commit()

        items_updated = result.rowcount
        logger.info(
            f"Stock update complete: {items_updated}/{len(item_ids)} items updated - "
            f"{'Available' if in_stock else 'Out of Stock'}"
        )

        # Schedule auto turn-on if needed
        if not in_stock and auto_turn_on_time == 'custom' and custom_turn_on_time:
            for item_id in item_ids:
                await schedule_auto_turn_on(restaurant_id, item_id, custom_turn_on_time, 'item')


async def update_addon_stock(
    restaurant_id: str,
    addon_ids: List[str],
    in_stock: bool,
    auto_turn_on_time: str = "",
    custom_turn_on_time: str = ""
):
    """
    Update addon stock status

    Args:
        restaurant_id: Restaurant ID (PetPooja restaurant ID)
        addon_ids: List of PetPooja addon IDs to update
        in_stock: Stock availability status
        auto_turn_on_time: Auto turn-on setting
        custom_turn_on_time: Custom turn-on datetime
    """
    logger.info(f"Updating {len(addon_ids)} addons for restaurant {restaurant_id}")

    # Get async database session
    async with AsyncSessionLocal() as db:
        # First, find the branch by PetPooja restaurant ID
        branch_result = await db.execute(
            select(BranchInfoTable).where(
                BranchInfoTable.ext_petpooja_restaurant_id == restaurant_id,
                BranchInfoTable.is_deleted == False
            )
        )
        branch = branch_result.scalar_one_or_none()

        if not branch:
            logger.warning(f"Branch not found for PetPooja restaurant ID: {restaurant_id}")
            return

        # Update all addons with the given PetPooja IDs
        result = await db.execute(
            update(MenuItemAddonItem)
            .where(
                MenuItemAddonItem.ext_petpooja_addon_id.in_(addon_ids),
                MenuItemAddonItem.restaurant_id == branch.branch_id,  # Match by branch_id
                MenuItemAddonItem.is_deleted == False
            )
            .values(
                is_in_stock=in_stock,
                updated_at=datetime.utcnow()
            )
        )

        await db.commit()

        addons_updated = result.rowcount
        logger.info(
            f"Addon stock update complete: {addons_updated}/{len(addon_ids)} addons updated - "
            f"{'Available' if in_stock else 'Out of Stock'}"
        )

        # Schedule auto turn-on if needed
        if not in_stock and auto_turn_on_time == 'custom' and custom_turn_on_time:
            for addon_id in addon_ids:
                await schedule_auto_turn_on(restaurant_id, addon_id, custom_turn_on_time, 'addon')


async def schedule_auto_turn_on(
    restaurant_id: str,
    item_id: str,
    turn_on_time: str,
    item_type: str
):
    """
    Schedule automatic stock turn-on

    Args:
        restaurant_id: Restaurant ID
        item_id: Item/Addon ID
        turn_on_time: ISO datetime string when to turn back on
        item_type: 'item' or 'addon'
    """
    logger.info(
        f"Scheduling auto turn-on - "
        f"Restaurant: {restaurant_id}, "
        f"Type: {item_type}, "
        f"ID: {item_id}, "
        f"Time: {turn_on_time}"
    )

    # TODO: Store in database for background job processor
    # db.execute("""
    #     INSERT INTO scheduled_jobs
    #     (restaurant_id, item_id, type, scheduled_time, action, status, created_at)
    #     VALUES (%s, %s, %s, %s, %s, %s, %s)
    # """, (
    #     restaurant_id,
    #     item_id,
    #     item_type,
    #     turn_on_time,
    #     'turn_on_stock',
    #     'pending',
    #     datetime.now()
    # ))

    # TODO: Set up scheduled task (Celery, cron, etc.)
    # Example with Celery:
    # from tasks import turn_on_stock_task
    # turn_on_stock_task.apply_async(
    #     args=[restaurant_id, item_id, item_type],
    #     eta=datetime.fromisoformat(turn_on_time)
    # )

    logger.info(f"Auto turn-on scheduled successfully")

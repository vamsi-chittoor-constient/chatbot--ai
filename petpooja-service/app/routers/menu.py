"""
Menu Router
"""

import logging
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_session_async import get_db
from app.services.menu_service_async import fetch_and_sync_menu_by_restaurant_id, MenuServiceError
from app.schemas.menu import FetchMenuResponse, MenuSyncByRestaurantIdRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/menu", tags=["Menu"])


@router.post("/fetch", response_model=FetchMenuResponse)
async def fetch_menu(request: MenuSyncByRestaurantIdRequest, db: AsyncSession = Depends(get_db)) -> FetchMenuResponse:
    """
    Fetch menu from PetPooja using restaurant_id.

    Fetches PetPooja credentials from database, calls PetPooja API to get menu,
    and stores/updates menu data in database (create or update to prevent duplicates).

    Args:
        request: Request body containing restaurant_id (UUID)
        db: Async database session

    Returns:
        FetchMenuResponse with success status, message, menu data and store result
    """
    try:
        logger.info(f"Fetching menu for restaurant_id: {request.restaurant_id}")

        result = await fetch_and_sync_menu_by_restaurant_id(request.restaurant_id, db)

        return FetchMenuResponse(**result)

    except MenuServiceError as e:
        logger.error(f"Menu service error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch menu: {str(e)}"
        )

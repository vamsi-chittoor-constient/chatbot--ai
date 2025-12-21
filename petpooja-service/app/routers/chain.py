"""
Chain Router - Clean API
Only 2 endpoints for chain/restaurant management
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_session_async import get_db
from app.schemas.chain import ChainResponse, FetchMenuSyncResponse, FetchMenuSyncWithCredentialsRequest
from app.schemas.petpooja_chain import (
    StoreChainDetailsPetpoojaRequest,
    StoreChainDetailsPetpoojaResponse
)
from app.services.chain_service_async import (
    fetch_menu_from_petpooja_with_credentials_only_async,
    get_chain_by_name_async,
    ChainServiceError
)
from app.services.chain_store_async import store_menu_data_async

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/chain",
    tags=["Chain Management"]
)

@router.get("/fetch-chain", response_model=List[ChainResponse])
async def fetch_chain(name: str, db: AsyncSession = Depends(get_db)):
    """Fetch chain by name - ASYNC version."""
    chains = await get_chain_by_name_async(db, name)
    return chains
    

@router.post("/petpooja-sync")
async def sync_menu_with_credentials(request: FetchMenuSyncWithCredentialsRequest) -> FetchMenuSyncResponse:
    """
    Petpooja Sync API - Sync menu from PetPooja using custom credentials
    This endpoint accepts PetPooja credentials from frontend, fetches menu data,
    and returns it
    """
    try:
        logger.info(f"Syncing menu for restaurant {request.restaurant_id} with custom credentials")

        # Fetch menu from PetPooja using chain_service_async
        result = await fetch_menu_from_petpooja_with_credentials_only_async(
            restaurant_id=request.restaurant_id,
            app_key=request.app_key,
            app_secret=request.app_secret,
            access_token=request.access_token,
            sandbox_enabled=request.sandbox_enabled
        )

        return FetchMenuSyncResponse(**result)

    except ChainServiceError as e:
        logger.error(f"Menu service error during sync: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:
        logger.error(f"Unexpected error during menu sync: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync menu: {str(e)}"
        )


@router.post(
    "/store-menu",
    response_model=StoreChainDetailsPetpoojaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Store menu data in database",
    description="Store complete chain and menu data into database (finalpayload.json structure)"
)
async def store_menu_endpoint(
    request: StoreChainDetailsPetpoojaRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        logger.info(f"Storing menu data in database for chain: {request.chain_info.chain_name or 'Default Chain'}")

        # Store complete chain and menu data - ASYNC
        result = await store_menu_data_async(db, request)

        logger.info(f"Successfully stored menu data. Chain ID: {result['chain_id']}")

        return StoreChainDetailsPetpoojaResponse(**result)

    except Exception as e:
        logger.error(f"Error storing menu data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error storing menu data: {str(e)}"
        )

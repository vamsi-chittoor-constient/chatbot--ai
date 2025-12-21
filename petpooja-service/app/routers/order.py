"""Order Router - API endpoints for order operations"""

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.schemas.order_v2 import CreateOrderResponse, PushToPosRequest, UpdateOrderStatusRequest
from app.services.order_service_async import (
    OrderServiceError,
    fetch_order_from_database, update_integration_sync_status, push_order_to_petpooja,
    fetch_order_info_for_status_update, update_order_status_at_petpooja
)
from app.services.order_transformer import transform_db_order_to_petpooja
from app.core.db_session_async import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/orders", tags=["Orders"])


@router.post("/push-to-pos", response_model=CreateOrderResponse, status_code=status.HTTP_200_OK)
async def push_to_pos(
    request: PushToPosRequest,
    db: AsyncSession = Depends(get_db)
) -> CreateOrderResponse:
    """Push an existing order to PetPooja POS"""
    try:
        order_data = await fetch_order_from_database(request.order_id, request.restaurant_id, db)
        external_order_id = order_data.get("external_order_id", "")
        petpooja_credentials = order_data.get("petpooja_credentials", {})

        petpooja_order = transform_db_order_to_petpooja(order_data)
        petpooja_result = await push_order_to_petpooja(petpooja_order, petpooja_credentials)
        await update_integration_sync_status(request.order_id, "success", db)

        return CreateOrderResponse(
            success=True,
            message="Order pushed to PetPooja successfully",
            data={
                "order_id": str(request.order_id),
                "external_order_id": external_order_id,
                "petpooja_sync_status": "success",
                "petpooja_response": petpooja_result.get("data")
            }
        )

    except OrderServiceError as e:
        await update_integration_sync_status(request.order_id, "failed", db, str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        logger.error(f"Push to POS failed: {str(e)}")
        await update_integration_sync_status(request.order_id, "failed", db, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to push order to POS: {str(e)}"
        )


@router.post("/update-order-status", response_model=CreateOrderResponse, status_code=status.HTTP_200_OK)
async def update_order_status(
    request: UpdateOrderStatusRequest,
    db: AsyncSession = Depends(get_db)
) -> CreateOrderResponse:
    """Update order status at PetPooja POS. Status: -1=Cancelled, 0=Pending, 1=Accepted, 2=Food Ready, 3=Dispatched, 4=Delivered"""
    try:
        if request.status == "-1" and not request.cancel_reason:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="cancel_reason is required when status is -1"
            )

        order_info = await fetch_order_info_for_status_update(request.order_id, request.restaurant_id, db)

        result = await update_order_status_at_petpooja(
            rest_id=order_info.get("rest_id"),
            client_order_id=order_info.get("external_order_id"),
            status=request.status,
            cancel_reason=request.cancel_reason or "",
            credentials=order_info.get("credentials")
        )

        return CreateOrderResponse(
            success=True,
            message="Order status updated successfully",
            data={
                "order_id": str(request.order_id),
                "external_order_id": order_info.get("external_order_id"),
                "status": request.status,
                "petpooja_response": result.get("data")
            }
        )

    except OrderServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Update order status failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update order status: {str(e)}"
        )

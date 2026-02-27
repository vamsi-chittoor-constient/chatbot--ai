"""
Admin API Key Management Endpoints
Provides dynamic control over restaurant API keys
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_

import structlog

from app.core.database import get_db_session
from app.shared.models import Restaurant, APIKeyUsage
from app.utils.api_key_manager import get_api_key_manager

logger = structlog.get_logger(__name__)
router = APIRouter()


class APIKeyCreateRequest(BaseModel):
    """Request model for creating API key"""
    restaurant_id: str = Field(..., description="Restaurant ID")


class APIKeyResponse(BaseModel):
    """Response model for API key operations"""
    restaurant_id: str
    restaurant_name: str
    api_key: str
    created_at: datetime
    message: str


class APIKeyRegenerateRequest(BaseModel):
    """Request model for regenerating API key"""
    restaurant_id: str = Field(..., description="Restaurant ID")


class RestaurantInfo(BaseModel):
    """Restaurant information model"""
    restaurant_id: str
    restaurant_name: str
    api_key_prefix: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class APIKeyUsageStats(BaseModel):
    """API key usage statistics"""
    restaurant_id: str
    restaurant_name: str
    total_requests: int
    requests_today: int
    requests_this_week: int
    average_response_time_ms: float
    error_rate_percent: float
    last_used_at: Optional[datetime]


class APIKeyUsageDetail(BaseModel):
    """Detailed API usage record"""
    timestamp: datetime
    endpoint: str
    method: str
    status_code: int
    response_time_ms: Optional[int]
    ip_address: Optional[str]


@router.post("/api-keys", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(request: APIKeyCreateRequest):
    """
    Create new API key for restaurant.

    Permissions: Admin only
    """
    api_key_manager = get_api_key_manager()

    async with get_db_session() as session:
        try:
            query = select(Restaurant).where(Restaurant.id == request.restaurant_id)
            result = await session.execute(query)
            restaurant = result.scalar_one_or_none()

            if not restaurant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Restaurant with ID {request.restaurant_id} not found"
                )

            new_api_key = await api_key_manager.create_api_key_for_restaurant(
                request.restaurant_id,
                session
            )

            if not new_api_key:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create API key"
                )

            logger.info(
                "api_key_created_via_admin",
                restaurant_id=request.restaurant_id,
                restaurant_name=restaurant.name
            )

            return APIKeyResponse(
                restaurant_id=restaurant.id,
                restaurant_name=restaurant.name,
                api_key=new_api_key,
                created_at=datetime.now(),
                message="API key created successfully"
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error("create_api_key_error", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating API key: {str(e)}"
            )


@router.post("/api-keys/regenerate", response_model=APIKeyResponse)
async def regenerate_api_key(request: APIKeyRegenerateRequest):
    """
    Regenerate API key for restaurant (rotation).

    WARNING: This will invalidate the old API key immediately.
    Permissions: Admin only
    """
    api_key_manager = get_api_key_manager()

    async with get_db_session() as session:
        try:
            query = select(Restaurant).where(Restaurant.id == request.restaurant_id)
            result = await session.execute(query)
            restaurant = result.scalar_one_or_none()

            if not restaurant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Restaurant with ID {request.restaurant_id} not found"
                )

            new_api_key = await api_key_manager.regenerate_api_key(
                request.restaurant_id,
                session
            )

            if not new_api_key:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to regenerate API key"
                )

            logger.warning(
                "api_key_regenerated_via_admin",
                restaurant_id=request.restaurant_id,
                restaurant_name=restaurant.name
            )

            return APIKeyResponse(
                restaurant_id=restaurant.id,
                restaurant_name=restaurant.name,
                api_key=new_api_key,
                created_at=datetime.now(),
                message="API key regenerated successfully. Old key is now invalid."
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error("regenerate_api_key_error", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error regenerating API key: {str(e)}"
            )


@router.get("/restaurants", response_model=List[RestaurantInfo])
async def list_restaurants(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    List all restaurants with their API key prefixes.

    Permissions: Admin only
    """
    async with get_db_session() as session:
        try:
            query = (
                select(Restaurant)
                .offset(skip)
                .limit(limit)
                .order_by(Restaurant.created_at.desc())
            )

            result = await session.execute(query)
            restaurants = result.scalars().all()

            return [
                RestaurantInfo(
                    restaurant_id=r.id,
                    restaurant_name=r.name,
                    api_key_prefix=r.api_key[:15] + "..." if r.api_key else "None",
                    created_at=r.created_at,
                    updated_at=r.updated_at
                )
                for r in restaurants
            ]

        except Exception as e:
            logger.error("list_restaurants_error", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error listing restaurants: {str(e)}"
            )


@router.get("/api-keys/usage/{restaurant_id}", response_model=APIKeyUsageStats)
async def get_api_key_usage_stats(restaurant_id: str):
    """
    Get API key usage statistics for a restaurant.

    Permissions: Admin only or restaurant owner
    """
    async with get_db_session() as session:
        try:
            query = select(Restaurant).where(Restaurant.id == restaurant_id)
            result = await session.execute(query)
            restaurant = result.scalar_one_or_none()

            if not restaurant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Restaurant with ID {restaurant_id} not found"
                )

            total_requests_query = select(func.count(APIKeyUsage.id)).where(
                APIKeyUsage.restaurant_id == restaurant_id
            )
            total_requests = (await session.execute(total_requests_query)).scalar() or 0

            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            requests_today_query = select(func.count(APIKeyUsage.id)).where(
                and_(
                    APIKeyUsage.restaurant_id == restaurant_id,
                    APIKeyUsage.created_at >= today_start
                )
            )
            requests_today = (await session.execute(requests_today_query)).scalar() or 0

            week_start = datetime.now() - timedelta(days=7)
            requests_week_query = select(func.count(APIKeyUsage.id)).where(
                and_(
                    APIKeyUsage.restaurant_id == restaurant_id,
                    APIKeyUsage.created_at >= week_start
                )
            )
            requests_this_week = (await session.execute(requests_week_query)).scalar() or 0

            avg_response_time_query = select(func.avg(APIKeyUsage.response_time_ms)).where(
                APIKeyUsage.restaurant_id == restaurant_id
            )
            avg_response_time = (await session.execute(avg_response_time_query)).scalar() or 0.0

            error_count_query = select(func.count(APIKeyUsage.id)).where(
                and_(
                    APIKeyUsage.restaurant_id == restaurant_id,
                    APIKeyUsage.status_code >= 400
                )
            )
            error_count = (await session.execute(error_count_query)).scalar() or 0

            error_rate = (error_count / total_requests * 100) if total_requests > 0 else 0.0

            last_used_query = select(func.max(APIKeyUsage.created_at)).where(
                APIKeyUsage.restaurant_id == restaurant_id
            )
            last_used_at = (await session.execute(last_used_query)).scalar()

            return APIKeyUsageStats(
                restaurant_id=restaurant.id,
                restaurant_name=restaurant.name,
                total_requests=total_requests,
                requests_today=requests_today,
                requests_this_week=requests_this_week,
                average_response_time_ms=float(avg_response_time),
                error_rate_percent=float(error_rate),
                last_used_at=last_used_at
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error("get_usage_stats_error", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving usage stats: {str(e)}"
            )


@router.get("/api-keys/usage/{restaurant_id}/details", response_model=List[APIKeyUsageDetail])
async def get_api_key_usage_details(
    restaurant_id: str,
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0)
):
    """
    Get detailed API key usage logs for a restaurant.

    Permissions: Admin only or restaurant owner
    """
    async with get_db_session() as session:
        try:
            query = (
                select(APIKeyUsage)
                .where(APIKeyUsage.restaurant_id == restaurant_id)
                .order_by(APIKeyUsage.created_at.desc())
                .offset(skip)
                .limit(limit)
            )

            result = await session.execute(query)
            usage_records = result.scalars().all()

            return [
                APIKeyUsageDetail(
                    timestamp=record.created_at,
                    endpoint=record.endpoint,
                    method=record.method,
                    status_code=record.status_code,
                    response_time_ms=record.response_time_ms,
                    ip_address=record.ip_address
                )
                for record in usage_records
            ]

        except Exception as e:
            logger.error("get_usage_details_error", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving usage details: {str(e)}"
            )

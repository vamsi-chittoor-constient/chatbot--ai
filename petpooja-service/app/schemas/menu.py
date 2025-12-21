"""
Menu Schemas
Pydantic models for menu API requests/responses
"""

from typing import Dict, Any, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class MenuSyncByRestaurantIdRequest(BaseModel):
    """Request schema for syncing menu using restaurant_id (fetches credentials from DB)"""
    restaurant_id: UUID = Field(..., description="Restaurant UUID to fetch PetPooja credentials and sync menu")

    class Config:
        json_schema_extra = {
            "example": {
                "restaurant_id": "your-restaurant-uuid-here"
            }
        }


class FetchMenuResponse(BaseModel):
    """Response schema for basic menu fetch"""
    success: bool = Field(default=True)
    message: str = Field(default="Menu fetched successfully")
    data: Dict[str, Any] = Field(..., description="Menu data from PetPooja")
    store_result: Optional[Dict[str, Any]] = Field(None, description="Database storage result")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Menu fetched and stored successfully",
                "data": {
                    "items": [],
                    "categories": [],
                    "addons": [],
                    "taxes": []
                },
                "store_result": {
                    "success": True,
                    "message": "Menu stored successfully",
                    "counts": {
                        "items": 45,
                        "categories": 8
                    }
                }
            }
        }

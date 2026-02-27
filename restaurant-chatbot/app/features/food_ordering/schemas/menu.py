"""
Menu management Pydantic models for the Restaurant AI Assistant API.

Provides type-safe request/response models for menu categories, menu items,
pricing, availability, and menu-related operations with AI enhancements.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator, ConfigDict

from app.schemas.common import (
    BaseResponse, SuccessResponse, PaginatedResponse,
    CurrencyAmount, SortOrder, DateRangeFilter
)


# Menu Category Request Models
class MenuCategoryCreateRequest(BaseModel):
    """Request model for creating a new menu category"""
    restaurant_id: str = Field(..., description="Restaurant identifier")
    name: str = Field(..., min_length=1, max_length=255, description="Category name")
    description: Optional[str] = Field(None, max_length=1000, description="Category description")
    display_order: int = Field(default=0, ge=0, description="Display order for category")
    is_active: bool = Field(default=True, description="Whether category is active")

class MenuCategoryUpdateRequest(BaseModel):
    """Request model for updating menu category"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Updated category name")
    description: Optional[str] = Field(None, max_length=1000, description="Updated description")
    display_order: Optional[int] = Field(None, ge=0, description="Updated display order")
    is_active: Optional[bool] = Field(None, description="Updated active status")

class MenuCategorySearchRequest(BaseModel):
    """Request model for searching menu categories"""
    restaurant_id: str = Field(..., description="Restaurant identifier")
    query: Optional[str] = Field(None, min_length=1, description="Search query")
    is_active: Optional[bool] = Field(None, description="Filter by active status")

    # Pagination
    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=20, ge=1, le=100, description="Items per page")

    # Sorting
    sort_by: str = Field(default="display_order", description="Sort field")
    sort_order: SortOrder = Field(default=SortOrder.ASC, description="Sort order")


# Menu Item Request Models
class MenuItemCreateRequest(BaseModel):
    """Request model for creating a new menu item"""
    category_id: str = Field(..., description="Menu category identifier")
    name: str = Field(..., min_length=1, max_length=255, description="Item name")
    description: Optional[str] = Field(None, max_length=2000, description="Item description")
    price: Decimal = Field(..., gt=0, description="Item price")
    ingredients: Optional[List[str]] = Field(default_factory=list, description="List of ingredients")
    allergens: Optional[List[str]] = Field(default_factory=list, description="Allergen information")
    dietary_info: Optional[List[str]] = Field(default_factory=list, description="Dietary information")
    spice_level: Optional[str] = Field(None, description="Spice level (mild, medium, hot, extra_hot)")
    prep_time_minutes: Optional[int] = Field(None, ge=0, le=120, description="Preparation time in minutes")
    calories: Optional[int] = Field(None, ge=0, description="Calorie count")
    is_available: bool = Field(default=True, description="Item availability status")
    availability_schedule: Optional[Dict[str, Any]] = Field(None, description="Time-based availability schedule")
    is_popular: bool = Field(default=False, description="Popular item flag")
    is_seasonal: bool = Field(default=False, description="Seasonal item flag")
    image_url: Optional[str] = Field(None, max_length=500, description="Item image URL")

    @field_validator('ingredients', 'allergens', 'dietary_info')
    @classmethod
    def validate_string_lists(cls, v):
        """Validate string lists"""
        if v is None:
            return []
        # Remove empty strings and duplicates
        cleaned = list(set([item.strip() for item in v if item.strip()]))
        return cleaned

    @field_validator('spice_level')
    @classmethod
    def validate_spice_level(cls, v):
        """Validate spice level values"""
        if v is None:
            return v

        valid_levels = ['mild', 'medium', 'hot', 'extra_hot']
        if v.lower() not in valid_levels:
            raise ValueError(f'Spice level must be one of: {", ".join(valid_levels)}')

        return v.lower()

    @field_validator('price')
    @classmethod
    def validate_price(cls, v):
        """Validate price format"""
        return round(Decimal(str(v)), 2)

class MenuItemUpdateRequest(BaseModel):
    """Request model for updating menu item"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Updated item name")
    description: Optional[str] = Field(None, max_length=2000, description="Updated description")
    price: Optional[Decimal] = Field(None, gt=0, description="Updated price")
    ingredients: Optional[List[str]] = Field(None, description="Updated ingredients list")
    allergens: Optional[List[str]] = Field(None, description="Updated allergens list")
    dietary_info: Optional[List[str]] = Field(None, description="Updated dietary info")
    spice_level: Optional[str] = Field(None, description="Updated spice level")
    prep_time_minutes: Optional[int] = Field(None, ge=0, le=120, description="Updated prep time")
    calories: Optional[int] = Field(None, ge=0, description="Updated calorie count")
    is_available: Optional[bool] = Field(None, description="Updated availability")
    availability_schedule: Optional[Dict[str, Any]] = Field(None, description="Updated schedule")
    is_popular: Optional[bool] = Field(None, description="Updated popular status")
    is_seasonal: Optional[bool] = Field(None, description="Updated seasonal status")
    image_url: Optional[str] = Field(None, max_length=500, description="Updated image URL")

    @field_validator('ingredients', 'allergens', 'dietary_info')
    @classmethod
    def validate_string_lists(cls, v):
        """Validate string lists"""
        if v is None:
            return v
        # Remove empty strings and duplicates
        cleaned = list(set([item.strip() for item in v if item.strip()]))
        return cleaned

    @field_validator('spice_level')
    @classmethod
    def validate_spice_level(cls, v):
        """Validate spice level values"""
        if v is None:
            return v

        valid_levels = ['mild', 'medium', 'hot', 'extra_hot']
        if v.lower() not in valid_levels:
            raise ValueError(f'Spice level must be one of: {", ".join(valid_levels)}')

        return v.lower()

    @field_validator('price')
    @classmethod
    def validate_price(cls, v):
        """Validate price format"""
        if v is None:
            return v
        return round(Decimal(str(v)), 2)


class MenuItemSearchRequest(BaseModel):
    """Request model for searching menu items"""
    category_id: Optional[str] = Field(None, description="Filter by category")
    query: Optional[str] = Field(None, min_length=1, description="Search query")
    price_min: Optional[Decimal] = Field(None, ge=0, description="Minimum price filter")
    price_max: Optional[Decimal] = Field(None, ge=0, description="Maximum price filter")
    is_available: Optional[bool] = Field(None, description="Filter by availability")
    is_popular: Optional[bool] = Field(None, description="Filter by popular items")
    is_seasonal: Optional[bool] = Field(None, description="Filter by seasonal items")
    dietary_info: Optional[List[str]] = Field(None, description="Filter by dietary requirements")
    allergens_exclude: Optional[List[str]] = Field(None, description="Exclude items with allergens")
    spice_level: Optional[str] = Field(None, description="Filter by spice level")
    prep_time_max: Optional[int] = Field(None, ge=0, description="Maximum preparation time")

    # Pagination
    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=20, ge=1, le=100, description="Items per page")

    # Sorting
    sort_by: str = Field(default="name", description="Sort field")
    sort_order: SortOrder = Field(default=SortOrder.ASC, description="Sort order")

    @field_validator('dietary_info', 'allergens_exclude')
    @classmethod
    def validate_filter_lists(cls, v):
        """Validate filter lists"""
        if v is None:
            return v
        return [item.strip().lower() for item in v if item.strip()]


# Menu Response Models
class MenuCategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for menu category data"""
    id: str = Field(..., description="Category ID")
    restaurant_id: str = Field(..., description="Restaurant ID")
    name: str = Field(..., description="Category name")
    description: Optional[str] = Field(None, description="Category description")
    display_order: int = Field(..., description="Display order")
    is_active: bool = Field(..., description="Active status")
    item_count: Optional[int] = Field(None, description="Number of items in category")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")

class MenuItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for menu item data"""
    id: str = Field(..., description="Item ID")
    category_id: str = Field(..., description="Category ID")
    category_name: Optional[str] = Field(None, description="Category name")
    name: str = Field(..., description="Item name")
    description: Optional[str] = Field(None, description="Item description")
    price: Decimal = Field(..., description="Item price")
    ingredients: Optional[List[str]] = Field(default_factory=list, description="Ingredients list")
    allergens: Optional[List[str]] = Field(default_factory=list, description="Allergen information")
    dietary_info: Optional[List[str]] = Field(default_factory=list, description="Dietary information")
    spice_level: Optional[str] = Field(None, description="Spice level")
    prep_time_minutes: Optional[int] = Field(None, description="Preparation time")
    calories: Optional[int] = Field(None, description="Calorie count")
    is_available: bool = Field(..., description="Availability status")
    availability_schedule: Optional[Dict[str, Any]] = Field(None, description="Availability schedule")
    is_popular: bool = Field(..., description="Popular item flag")
    is_seasonal: bool = Field(..., description="Seasonal item flag")
    image_url: Optional[str] = Field(None, description="Item image URL")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

class MenuItemSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Condensed response model for menu item lists"""
    id: str = Field(..., description="Item ID")
    name: str = Field(..., description="Item name")
    price: Decimal = Field(..., description="Item price")
    is_available: bool = Field(..., description="Availability status")
    is_popular: bool = Field(..., description="Popular item flag")
    prep_time_minutes: Optional[int] = Field(None, description="Preparation time")
    spice_level: Optional[str] = Field(None, description="Spice level")

# ============================================================================
# LLM Agent Schemas (Customer-Facing)
# ============================================================================
# These schemas contain ONLY what customers need to see and what's needed
# for business logic (inventory). No internal metadata.

class MenuCategoryForLLM(BaseModel):
    """Lean category schema for LLM agents - customer-facing data only"""
    id: str = Field(..., description="Category ID")
    name: str = Field(..., description="Category name")
    description: Optional[str] = Field(None, description="Category description")
    item_count: int = Field(0, description="Number of available items")


class MenuItemForLLM(BaseModel):
    """Enhanced menu item schema for LLM agents with full hierarchy and relationships"""
    model_config = ConfigDict(from_attributes=True)

    # Core fields
    id: str = Field(..., description="Item ID")
    name: str = Field(..., description="Item name")
    description: Optional[str] = Field(None, description="Item description")
    price: Decimal = Field(..., description="Item price")
    serving_unit: Optional[str] = Field(None, description="Serving unit (pieces, grams, etc.)")

    # Category hierarchy (3 levels)
    section: Optional[str] = Field(None, description="Menu section (e.g., Vegetarian)")
    categories: List[str] = Field(default_factory=list, description="Menu categories (can be multiple)")
    subcategories: List[str] = Field(default_factory=list, description="Menu subcategories")

    # Cuisines and timings (many-to-many)
    cuisines: List[str] = Field(default_factory=list, description="Cuisine types")
    meal_timings: List[str] = Field(default_factory=list, description="Available meal times (Breakfast, Lunch, Dinner)")

    # Dietary and allergen info
    ingredients: List[str] = Field(default_factory=list, description="Ingredient list")
    allergens: List[str] = Field(default_factory=list, description="Allergen information")
    dietary_types: List[str] = Field(default_factory=list, description="Dietary tags (Vegetarian, Vegan, Gluten-Free)")

    # Attributes
    spice_level: Optional[str] = Field(None, description="Spice level (none, mild, medium, hot, extra_hot)")
    calories: Optional[int] = Field(None, description="Calorie count")
    prep_time_minutes: Optional[int] = Field(None, description="Preparation time")

    # Status flags
    is_available: bool = Field(True, description="Availability status (in stock)")
    is_recommended: bool = Field(False, description="Recommended/popular item flag")
    is_favorite: bool = Field(False, description="Favorite item flag")
    is_seasonal: bool = Field(False, description="Seasonal item flag")

    # Customization options
    allow_variation: bool = Field(False, description="Allows size variations")
    allow_addon: bool = Field(False, description="Allows add-ons")

    # Media
    image_url: Optional[str] = Field(None, description="Item image URL")

    @classmethod
    def from_enriched_view(cls, view_obj):
        """Create MenuItemForLLM from MenuItemEnrichedView model"""
        return cls(
            id=str(view_obj.menu_item_id),
            name=view_obj.menu_item_name,
            description=view_obj.menu_item_description,
            price=view_obj.menu_item_price,
            serving_unit=view_obj.menu_item_serving_unit,
            section=view_obj.section,
            categories=view_obj.categories or [],
            subcategories=view_obj.subcategories or [],
            cuisines=view_obj.cuisines or [],
            meal_timings=view_obj.meal_timings or [],
            ingredients=view_obj.ingredients or [],
            allergens=view_obj.allergens or [],
            dietary_types=view_obj.dietary_types or [],
            spice_level=view_obj.menu_item_spice_level,
            calories=view_obj.menu_item_calories,
            prep_time_minutes=view_obj.menu_item_minimum_preparation_time,
            is_available=view_obj.menu_item_in_stock,
            is_recommended=view_obj.menu_item_is_recommended,
            is_favorite=view_obj.menu_item_favorite,
            is_seasonal=view_obj.menu_item_is_seasonal,
            allow_variation=view_obj.menu_item_allow_variation,
            allow_addon=view_obj.menu_item_allow_addon,
            image_url=view_obj.menu_item_image_url
        )


class SubCategoryInfo(BaseModel):
    """Subcategory information with item count"""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Subcategory ID")
    name: str = Field(..., description="Subcategory name")
    description: Optional[str] = Field(None, description="Subcategory description")
    item_count: int = Field(0, description="Number of items in subcategory")


class CategoryWithSubCategories(BaseModel):
    """Category with subcategories for hierarchy navigation"""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Category ID")
    name: str = Field(..., description="Category name")
    description: Optional[str] = Field(None, description="Category description")
    item_count: int = Field(0, description="Total items in category")
    subcategories: List[SubCategoryInfo] = Field(default_factory=list, description="Subcategories under this category")


class MenuHierarchyResponse(BaseModel):
    """Complete 3-level menu hierarchy for navigation"""
    model_config = ConfigDict(from_attributes=True)

    section_id: str = Field(..., description="Section ID")
    section_name: str = Field(..., description="Section name")
    section_description: Optional[str] = Field(None, description="Section description")
    categories: List[CategoryWithSubCategories] = Field(default_factory=list, description="Categories in section")


class MenuCategoryListResponse(PaginatedResponse[MenuCategoryResponse]):
    """Paginated response for menu category lists"""
    pass


class MenuItemListResponse(PaginatedResponse[MenuItemResponse]):
    """Paginated response for menu item lists"""
    pass


class MenuItemSummaryListResponse(PaginatedResponse[MenuItemSummaryResponse]):
    """Paginated response for condensed menu item lists"""
    pass


class MenuStatsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for menu statistics"""
    total_categories: int = Field(..., description="Total number of categories")
    active_categories: int = Field(..., description="Number of active categories")
    total_items: int = Field(..., description="Total number of menu items")
    available_items: int = Field(..., description="Number of available items")
    popular_items: int = Field(..., description="Number of popular items")
    seasonal_items: int = Field(..., description="Number of seasonal items")
    average_price: Optional[Decimal] = Field(None, description="Average item price")
    price_range: Optional[Dict[str, Decimal]] = Field(None, description="Price range (min/max)")

class MenuCategoryCreateResponse(BaseResponse):
    """Response model for menu category creation"""
    category: MenuCategoryResponse = Field(..., description="Created category information")


class MenuCategoryUpdateResponse(BaseResponse):
    """Response model for menu category updates"""
    category: MenuCategoryResponse = Field(..., description="Updated category information")
    changes_made: List[str] = Field(..., description="List of fields that were updated")


class MenuItemCreateResponse(BaseResponse):
    """Response model for menu item creation"""
    item: MenuItemResponse = Field(..., description="Created item information")


class MenuItemUpdateResponse(BaseResponse):
    """Response model for menu item updates"""
    item: MenuItemResponse = Field(..., description="Updated item information")
    changes_made: List[str] = Field(..., description="List of fields that were updated")


class MenuBulkUpdateResponse(BaseResponse):
    """Response model for bulk menu operations"""
    items_updated: int = Field(..., description="Number of items updated")
    items_failed: int = Field(..., description="Number of items that failed to update")
    failed_items: List[str] = Field(default_factory=list, description="IDs of items that failed")
    changes_summary: Dict[str, int] = Field(..., description="Summary of changes made")


# Full Menu Response
class FullMenuResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Complete menu structure with categories and items"""
    restaurant_id: str = Field(..., description="Restaurant ID")
    categories: List[MenuCategoryResponse] = Field(..., description="Menu categories")
    items_by_category: Dict[str, List[MenuItemResponse]] = Field(..., description="Items grouped by category")
    stats: MenuStatsResponse = Field(..., description="Menu statistics")
    last_updated: Optional[datetime] = Field(None, description="Last menu update timestamp")


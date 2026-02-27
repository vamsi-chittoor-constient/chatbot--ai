"""
Menu Category Browsing Tools
=============================
Tools for browsing menu by categories - essential for structured menu navigation.
"""

from typing import Dict, Any, Optional
import structlog

from app.tools.base.tool_base import ToolBase, ToolResult, ToolStatus, ToolError
from app.core.database import get_db_session
from app.features.food_ordering.models import MenuCategory, MenuItem
from sqlalchemy import select, func
from app.utils.schema_tool_integration import (
    serialize_output_with_schema,
    safe_isoformat
)
from app.features.food_ordering.schemas.menu import (
    MenuCategoryResponse,
    MenuItemResponse,
    MenuItemSummaryResponse
)

logger = structlog.get_logger(__name__)


class GetMenuCategoriesListTool(ToolBase):
    """
    Get list of menu categories for browsing.
    Shows categories with item counts.
    """

    def __init__(self):
        super().__init__(
            name="get_menu_categories_list",
            description="Get list of menu categories for browsing",
            max_retries=1,
            timeout_seconds=10
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        return kwargs

    async def _execute_impl(self, **kwargs) -> ToolResult:
        try:
            restaurant_id = kwargs.get('restaurant_id')

            async with get_db_session() as session:
                # Get active categories
                categories_query = select(MenuCategory).where(
                    MenuCategory.is_deleted == False
                ).order_by(
                    MenuCategory.menu_category_rank,
                    MenuCategory.menu_category_name
                )

                categories_result = await session.execute(categories_query)
                categories = categories_result.scalars().all()

                # Get item counts per category (only available items)
                categories_data = []
                for category in categories:
                    # Count available items in this category
                    count_query = select(func.count(MenuItem.id)).where(
                        MenuItem.category_id == category.id,
                        MenuItem.is_available == True
                    )

                    count_result = await session.execute(count_query)
                    item_count = count_result.scalar() or 0

                    # Only include categories with items
                    if item_count > 0:
                        # Serialize category using schema
                        category_data = serialize_output_with_schema(
                            MenuCategoryResponse,
                            category,
                            self.name,
                            from_orm=True
                        )
                        # Add extra field
                        category_data['item_count'] = item_count
                        categories_data.append(category_data)

                logger.info(
                    "Retrieved menu categories",
                    category_count=len(categories_data)
                )

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={
                        "categories": categories_data,
                        "total_categories": len(categories_data),
                        "message": f"Found {len(categories_data)} menu categories"
                    }
                )

        except Exception as e:
            logger.error(f"Failed to get categories: {str(e)}")
            raise ToolError(f"Database error: {str(e)}", tool_name=self.name, retry_suggested=True)


class GetCategoryItemsTool(ToolBase):
    """
    Get all menu items in a specific category.
    Filters by meal time (breakfast/lunch/dinner/evening_snacks).
    Returns numbered list for easy selection.
    """

    def __init__(self):
        super().__init__(
            name="get_category_items",
            description="Get menu items in a specific category",
            max_retries=1,
            timeout_seconds=15
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        if not kwargs.get('category_name') and not kwargs.get('category_id'):
            raise ToolError("category_name or category_id is required", tool_name=self.name)
        return kwargs

    async def _execute_impl(self, **kwargs) -> ToolResult:
        try:
            category_name = kwargs.get('category_name')
            category_id = kwargs.get('category_id')
            filter_by_time = kwargs.get('filter_by_time', True)
            restaurant_id = kwargs.get('restaurant_id')

            async with get_db_session() as session:
                # Find category
                if category_id:
                    category_query = select(MenuCategory).where(MenuCategory.menu_category_id == category_id)
                else:
                    # Search by name (case-insensitive)
                    category_query = select(MenuCategory).where(
                        func.lower(MenuCategory.menu_category_name) == category_name.lower()
                    )

                category_result = await session.execute(category_query)
                category = category_result.scalar_one_or_none()

                if not category:
                    return ToolResult(
                        status=ToolStatus.FAILURE,
                        error=f"Category '{category_name or category_id}' not found"
                    )

                # Get items in category
                items_query = select(MenuItem).where(
                    MenuItem.category_id == category.id,
                    MenuItem.is_available == True
                ).order_by(MenuItem.name)

                items_result = await session.execute(items_query)
                items = items_result.scalars().all()

                # Apply time-based filtering if enabled
                filtered_items = []
                current_meal_time = None
                meal_time_display_name = None

                if filter_by_time and restaurant_id:
                    from app.utils.time_utils import (
                        get_current_meal_time,
                        is_item_available_for_time,
                        get_restaurant_meal_time_config,
                        get_meal_time_display_info
                    )

                    current_meal_time = await get_current_meal_time(restaurant_id)

                    if current_meal_time:
                        meal_periods = await get_restaurant_meal_time_config(restaurant_id)
                        display_info = get_meal_time_display_info(meal_periods, current_meal_time)
                        meal_time_display_name = display_info.get("name")

                    # Filter items
                    for item in items:
                        if is_item_available_for_time(item.availability_time, current_meal_time):
                            filtered_items.append(item)
                else:
                    filtered_items = items

                # Format items for display
                items_data = []
                for idx, item in enumerate(filtered_items, 1):
                    # Serialize item using schema
                    item_data = serialize_output_with_schema(
                        MenuItemSummaryResponse,
                        item,
                        self.name,
                        from_orm=True
                    )
                    # Add extra fields
                    item_data['number'] = idx
                    items_data.append(item_data)

                logger.info(
                    "Retrieved category items",
                    category=category.name,
                    total_items=len(items_data),
                    meal_time=current_meal_time
                )

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={
                        "category_name": category.name,
                        "category_description": category.description,
                        "items": items_data,
                        "item_count": len(items_data),
                        "current_meal_time": current_meal_time,
                        "meal_time_display_name": meal_time_display_name,
                        "filtered_by_time": filter_by_time,
                        "message": f"Found {len(items_data)} items in {category.name}"
                    }
                )

        except Exception as e:
            logger.error(f"Failed to get category items: {str(e)}")
            raise ToolError(f"Database error: {str(e)}", tool_name=self.name, retry_suggested=True)

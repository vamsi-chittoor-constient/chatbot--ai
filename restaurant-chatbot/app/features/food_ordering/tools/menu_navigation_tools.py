"""
Menu Navigation Tools
=====================

Conversational menu browsing tools with progressive refinement and context tracking.

Tools:
1. GetMenuHierarchyTool - Navigate sections/categories/subcategories
2. GetMenuItemsByFiltersTool - Multi-dimensional item filtering
3. GetCurrentMealSuggestionsTool - Smart time-based suggestions
4. RefineCurrentResultsTool - Context-aware progressive refinement
"""

from decimal import Decimal
from typing import Dict, Any, Optional, List, TYPE_CHECKING
from datetime import datetime, time as time_obj
from uuid import UUID

from app.tools.base.tool_base import ToolBase, ToolResult, ToolStatus, ToolError
from app.core.database import get_db_session
from app.features.food_ordering.models import (
    MenuItemEnrichedView,
    MenuSection,
    MenuCategory,
    MenuSubCategory,
    MealSlotTiming,
    MealType,
    MenuItemAvailabilitySchedule,
    MenuItem
)
from app.features.food_ordering.services.menu_cache import get_menu_cache_service
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import joinedload
from app.core.logging_config import get_logger
from app.utils.validation_decorators import validate_schema, require_tables
from app.utils.schema_tool_integration import serialize_output_with_schema, safe_isoformat
from app.features.food_ordering.schemas.menu import MenuItemForLLM

logger = get_logger(__name__)


def get_current_meal_time() -> str:
    """
    Determine current meal time based on time of day.

    Note: This is a synchronous fallback function using hardcoded times.
    For database-driven meal times, use get_current_meal_time_from_db().

    Returns:
        str: "breakfast", "lunch", or "dinner"
    """
    current_time = datetime.now().time()

    if time_obj(6, 0) <= current_time < time_obj(11, 0):
        return "breakfast"
    elif time_obj(11, 0) <= current_time < time_obj(16, 0):
        return "lunch"
    else:  # 4 PM onwards
        return "dinner"


async def get_current_meal_slot_from_db(session) -> Optional[Dict[str, Any]]:
    """
    Get current meal slot from meal_slot_timing table based on current time.

    Flow:
    1. Get current time
    2. Query meal_slot_timing where current_time is between opening_time and closing_time
    3. Return meal_type_id and timing info

    Args:
        session: Database session

    Returns:
        Dict with meal_type_id, meal_type_name, opening_time, closing_time
        or None if no matching slot found
    """
    current_time = datetime.now().time()

    # Query meal_slot_timing joined with meal_type
    query = (
        select(MealSlotTiming, MealType)
        .join(MealType, MealSlotTiming.meal_type_id == MealType.meal_type_id)
        .where(
            and_(
                MealSlotTiming.is_deleted == False,
                MealSlotTiming.is_active == True,
                MealSlotTiming.opening_time <= current_time,
                MealSlotTiming.closing_time >= current_time
            )
        )
    )

    result = await session.execute(query)
    row = result.first()

    if row:
        slot, meal_type = row
        return {
            'meal_type_id': slot.meal_type_id,
            'meal_type_name': meal_type.meal_type_name,
            'opening_time': slot.opening_time,
            'closing_time': slot.closing_time
        }

    # Fallback: Check for "All Day" meal type
    all_day_query = (
        select(MealSlotTiming, MealType)
        .join(MealType, MealSlotTiming.meal_type_id == MealType.meal_type_id)
        .where(
            and_(
                MealSlotTiming.is_deleted == False,
                MealSlotTiming.is_active == True,
                MealType.meal_type_name == 'All Day'
            )
        )
    )

    all_day_result = await session.execute(all_day_query)
    all_day_row = all_day_result.first()

    if all_day_row:
        slot, meal_type = all_day_row
        return {
            'meal_type_id': slot.meal_type_id,
            'meal_type_name': meal_type.meal_type_name,
            'opening_time': slot.opening_time,
            'closing_time': slot.closing_time
        }

    return None


async def get_menu_items_by_time_range(
    session,
    time_from: time_obj,
    time_to: time_obj,
    restaurant_id: Optional[UUID] = None,
    available_only: bool = True
) -> List[Any]:
    """
    Get menu items that are available within the given time range.

    Flow:
    1. Query menu_item_availability_schedule where time_from/time_to overlaps
    2. Join with MenuItem to get full item details

    Args:
        session: Database session
        time_from: Start time of the range
        time_to: End time of the range
        restaurant_id: Optional restaurant filter
        available_only: Filter by in-stock items

    Returns:
        List of MenuItem objects
    """
    current_time = datetime.now().time()

    # Query menu_item_availability_schedule where current time falls within range
    subquery = (
        select(MenuItemAvailabilitySchedule.menu_item_id)
        .where(
            and_(
                MenuItemAvailabilitySchedule.is_deleted == False,
                MenuItemAvailabilitySchedule.is_available == True,
                MenuItemAvailabilitySchedule.time_from <= current_time,
                MenuItemAvailabilitySchedule.time_to >= current_time
            )
        )
    ).subquery()

    # Items that have ANY availability schedule entry (used to find items WITHOUT schedules)
    all_scheduled_items = (
        select(MenuItemAvailabilitySchedule.menu_item_id)
        .where(MenuItemAvailabilitySchedule.is_deleted == False)
        .distinct()
    ).subquery()

    # Main query: items with matching time schedules OR items without any schedule (always available)
    query = (
        select(MenuItemEnrichedView)
        .where(
            and_(
                MenuItemEnrichedView.is_deleted == False,
                or_(
                    MenuItemEnrichedView.menu_item_id.in_(select(subquery.c.menu_item_id)),
                    ~MenuItemEnrichedView.menu_item_id.in_(select(all_scheduled_items.c.menu_item_id))
                )
            )
        )
    )

    if restaurant_id:
        query = query.where(MenuItemEnrichedView.restaurant_id == restaurant_id)

    if available_only:
        query = query.where(MenuItemEnrichedView.menu_item_in_stock == True)

    # Order by recommendation, popularity, then rank
    query = query.order_by(
        MenuItemEnrichedView.menu_item_is_recommended.desc(),
        MenuItemEnrichedView.menu_item_favorite.desc(),
        MenuItemEnrichedView.menu_item_rank
    )

    result = await session.execute(query)
    return result.scalars().all()


@validate_schema(MenuSection, MenuCategory, MenuSubCategory)
class GetMenuHierarchyTool(ToolBase):
    """
    Navigate menu hierarchy (sections, categories, subcategories).

    Enables conversational drilling down through menu structure:
    - Level 1: Sections (Veg/Non-Veg/Vegan)
    - Level 2: Categories (Breakfast, Main Course, Beverages)
    - Level 3: SubCategories (Dosas, Biryanis, Curries)

    Uses cached hierarchy for fast response.
    """

    def __init__(self):
        super().__init__(
            name="get_menu_hierarchy",
            description="Get menu hierarchy for navigation (sections/categories/subcategories)",
            max_retries=2,
            timeout_seconds=10
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        """Validate hierarchy request parameters"""
        level = kwargs.get('level', 'sections')
        if level not in ['sections', 'categories', 'subcategories']:
            raise ToolError(
                f"Invalid level '{level}'. Must be 'sections', 'categories', or 'subcategories'",
                tool_name=self.name
            )
        return kwargs

    async def _execute_impl(self, **kwargs) -> ToolResult:
        try:
            level = kwargs.get('level', 'sections')
            parent_id = kwargs.get('parent_id')
            include_item_counts = kwargs.get('include_item_counts', True)
            restaurant_id = kwargs.get('restaurant_id')

            # Safe UUID parsing for restaurant_id
            restaurant_uuid = UUID('00000000-0000-0000-0000-000000000001')  # Default
            if restaurant_id:
                try:
                    restaurant_uuid = UUID(restaurant_id) if isinstance(restaurant_id, str) else restaurant_id
                except (ValueError, AttributeError, TypeError):
                    logger.warning(f"Invalid restaurant_id provided: {restaurant_id}, using default")
                    restaurant_uuid = UUID('00000000-0000-0000-0000-000000000001')

            cache_service = get_menu_cache_service()

            # Get cached hierarchy
            hierarchy = await cache_service.get_or_load_hierarchy(
                restaurant_id=restaurant_uuid
            )

            if level == 'sections':
                # Return top-level sections
                result_items = []
                for section in hierarchy.get('sections', []):
                    item_count = sum(
                        cat.get('item_count', 0)
                        for cat in section.get('categories', [])
                    ) if include_item_counts else None

                    result_items.append({
                        'id': section['id'],
                        'name': section['name'],
                        'description': section.get('description'),
                        'item_count': item_count
                    })

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={
                        'level': 'sections',
                        'items': result_items,
                        'total': len(result_items)
                    }
                )

            elif level == 'categories':
                # Return categories in a section
                if not parent_id:
                    raise ToolError(
                        "parent_id (section_id) is required for categories level",
                        tool_name=self.name
                    )

                # Find section
                section = None
                for s in hierarchy.get('sections', []):
                    if s['id'] == parent_id:
                        section = s
                        break

                if not section:
                    return ToolResult(
                        status=ToolStatus.FAILURE,
                        error=f"Section '{parent_id}' not found"
                    )

                result_items = []
                for category in section.get('categories', []):
                    result_items.append({
                        'id': category['id'],
                        'name': category['name'],
                        'description': category.get('description'),
                        'item_count': category.get('item_count', 0)
                    })

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={
                        'level': 'categories',
                        'parent': section['name'],
                        'parent_id': parent_id,
                        'items': result_items,
                        'total': len(result_items)
                    }
                )

            else:  # subcategories
                # Return subcategories in a category
                if not parent_id:
                    raise ToolError(
                        "parent_id (category_id) is required for subcategories level",
                        tool_name=self.name
                    )

                # Find category across all sections
                category = None
                section_name = None
                for section in hierarchy.get('sections', []):
                    for cat in section.get('categories', []):
                        if cat['id'] == parent_id:
                            category = cat
                            section_name = section['name']
                            break
                    if category:
                        break

                if not category:
                    return ToolResult(
                        status=ToolStatus.FAILURE,
                        error=f"Category '{parent_id}' not found"
                    )

                result_items = []
                for subcat in category.get('subcategories', []):
                    result_items.append({
                        'id': subcat['id'],
                        'name': subcat['name'],
                        'description': subcat.get('description'),
                        'item_count': subcat.get('item_count', 0)
                    })

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={
                        'level': 'subcategories',
                        'parent': category['name'],
                        'parent_id': parent_id,
                        'section': section_name,
                        'items': result_items,
                        'total': len(result_items)
                    }
                )

        except Exception as e:
            logger.error(f"Failed to get menu hierarchy: {str(e)}")
            raise ToolError(f"Database error: {str(e)}", tool_name=self.name, retry_suggested=True)


@validate_schema(MenuItemEnrichedView)
class GetMenuItemsByFiltersTool(ToolBase):
    """
    Get menu items with multi-dimensional filtering.

    Supports filtering by:
    - Hierarchy: section, category, subcategory
    - Time: meal_timing
    - Price: min_price, max_price
    - Availability: available_only

    Returns items with breadcrumbs and suggested refinements.
    """

    def __init__(self):
        super().__init__(
            name="get_menu_items_by_filters",
            description="Get menu items with multi-dimensional filtering",
            max_retries=2,
            timeout_seconds=15
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        """Validate filter parameters"""
        limit = kwargs.get('limit', 20)
        if limit < 1 or limit > 100:
            raise ToolError(
                f"Limit must be between 1 and 100, got {limit}",
                tool_name=self.name
            )
        return kwargs

    async def _execute_impl(self, **kwargs) -> ToolResult:
        try:
            # Extract filters
            section_name = kwargs.get('section')
            category_name = kwargs.get('category')
            subcategory_name = kwargs.get('subcategory')
            meal_timing = kwargs.get('meal_timing')
            available_only = kwargs.get('available_only', True)
            min_price = kwargs.get('min_price')
            max_price = kwargs.get('max_price')
            limit = kwargs.get('limit', 20)
            offset = kwargs.get('offset', 0)
            restaurant_id = kwargs.get('restaurant_id')

            async with get_db_session() as session:
                # NEW: Safe UUID parsing for restaurant_id
                restaurant_uuid = None
                if restaurant_id:
                    try:
                        restaurant_uuid = UUID(restaurant_id) if isinstance(restaurant_id, str) else restaurant_id
                    except (ValueError, AttributeError, TypeError):
                        logger.warning(f"Invalid restaurant_id provided: {restaurant_id}, ignoring filter")
                        restaurant_uuid = None

                # NEW: Resolve category name to sub-category IDs if category_name is provided
                sub_category_ids_filter = None
                if category_name:
                    # Check if category_name is already a UUID
                    try:
                        UUID(category_name)
                        category_id = UUID(category_name)
                    except (ValueError, AttributeError):
                        # It's a name, look it up in menu_categories table
                        category_query = select(MenuCategory.menu_category_id).where(
                            and_(
                                func.lower(MenuCategory.menu_category_name) == func.lower(category_name),
                                MenuCategory.is_deleted == False
                            )
                        )

                        if restaurant_uuid:
                            category_query = category_query.where(MenuCategory.restaurant_id == restaurant_uuid)

                        category_result = await session.execute(category_query)
                        category_obj = category_result.scalar_one_or_none()

                        if not category_obj:
                            # Category not found, return empty result
                            logger.warning(f"Category '{category_name}' not found in database")
                            return ToolResult(
                                status=ToolStatus.SUCCESS,
                                data={
                                    'items': [],
                                    'total_count': 0,
                                    'returned_count': 0,
                                    'filters_applied': {'category': category_name},
                                    'breadcrumb': [category_name],
                                    'suggested_refinements': {},
                                    'has_more': False,
                                    'next_offset': None,
                                    'message': f"Category '{category_name}' not found"
                                }
                            )

                        category_id = category_obj

                    # Fetch ALL sub-category IDs for this category
                    sub_category_query = select(MenuSubCategory.menu_sub_category_id).where(
                        and_(
                            MenuSubCategory.category_id == category_id,
                            MenuSubCategory.is_deleted == False
                        )
                    )

                    sub_category_result = await session.execute(sub_category_query)
                    sub_category_ids_filter = [row[0] for row in sub_category_result.all()]

                    logger.info(
                        f"Resolved category '{category_name}' to {len(sub_category_ids_filter)} sub-categories",
                        category_id=str(category_id),
                        sub_category_count=len(sub_category_ids_filter)
                    )

                # Build query using MenuItem table directly (not enriched view)
                query = select(MenuItemEnrichedView).where(
                    MenuItemEnrichedView.is_deleted == False
                )

                if restaurant_uuid:
                    query = query.where(MenuItemEnrichedView.restaurant_id == restaurant_uuid)

                # Apply filters
                filters_applied = {}

                if available_only:
                    query = query.where(MenuItemEnrichedView.menu_item_in_stock == True)
                    filters_applied['available_only'] = True

                if section_name:
                    query = query.where(MenuItemEnrichedView.section == section_name)
                    filters_applied['section'] = section_name

                if category_name and 'category_id' in locals():
                    # NEW: Use resolved category_id for direct table lookup via mapping
                    from app.features.food_ordering.models.menu_item_category_mapping import MenuItemCategoryMapping

                    # Build conditions for query:
                    # Get ALL items in this category, including:
                    # 1. Items in sub-categories: menu_sub_category_id IN (sub_category_ids)
                    # 2. Items directly in category: menu_category_id = category_id AND menu_sub_category_id IS NULL

                    conditions = [MenuItemCategoryMapping.is_deleted == False]

                    if sub_category_ids_filter and len(sub_category_ids_filter) > 0:
                        # Category has sub-categories - get items from sub-categories OR directly in category
                        conditions.append(
                            or_(
                                MenuItemCategoryMapping.menu_sub_category_id.in_(sub_category_ids_filter),
                                and_(
                                    MenuItemCategoryMapping.menu_category_id == category_id,
                                    MenuItemCategoryMapping.menu_sub_category_id.is_(None)
                                )
                            )
                        )
                    else:
                        # Category has NO sub-categories - only get items directly in category
                        conditions.append(MenuItemCategoryMapping.menu_category_id == category_id)
                        conditions.append(MenuItemCategoryMapping.menu_sub_category_id.is_(None))

                    mapping_query = select(MenuItemCategoryMapping.menu_item_id).where(and_(*conditions))
                    mapping_result = await session.execute(mapping_query)
                    menu_item_ids = [row[0] for row in mapping_result.all()]

                    if menu_item_ids:
                        query = query.where(MenuItemEnrichedView.menu_item_id.in_(menu_item_ids))
                        filters_applied['category'] = category_name
                        logger.info(
                            f"Filtered by {len(menu_item_ids)} items from category '{category_name}'",
                            category_id=str(category_id),
                            sub_category_count=len(sub_category_ids_filter) if sub_category_ids_filter else 0
                        )
                    else:
                        # No items found in mapping, return empty
                        logger.warning(f"No items found in category '{category_name}' via mapping table")
                        return ToolResult(
                            status=ToolStatus.SUCCESS,
                            data={
                                'items': [],
                                'total_count': 0,
                                'returned_count': 0,
                                'filters_applied': {'category': category_name},
                                'breadcrumb': [category_name],
                                'suggested_refinements': {},
                                'has_more': False,
                                'next_offset': None,
                                'message': f"No items found in category '{category_name}'"
                            }
                        )
                elif category_name:
                    # Fallback if category_id wasn't resolved: Use enriched view array matching
                    query = query.where(MenuItemEnrichedView.categories.contains([category_name]))
                    filters_applied['category'] = category_name

                if subcategory_name:
                    # Subcategory is an ARRAY field, use contains
                    query = query.where(MenuItemEnrichedView.subcategories.contains([subcategory_name]))
                    filters_applied['subcategory'] = subcategory_name

                if meal_timing:
                    # Meal timings is an ARRAY field, use contains
                    # Capitalize first letter to match database format (e.g., "dinner" -> "Dinner")
                    # Also include "All Day" items and items with no meal timing restrictions
                    meal_timing_formatted = meal_timing.capitalize()
                    query = query.where(
                        or_(
                            MenuItemEnrichedView.meal_timings.contains([meal_timing_formatted]),
                            MenuItemEnrichedView.meal_timings.contains(['All Day']),
                            MenuItemEnrichedView.meal_timings.is_(None),
                            func.coalesce(func.array_length(MenuItemEnrichedView.meal_timings, 1), 0) == 0,
                        )
                    )
                    filters_applied['meal_timing'] = meal_timing

                if min_price is not None:
                    query = query.where(MenuItemEnrichedView.menu_item_price >= Decimal(str(min_price)))
                    filters_applied['min_price'] = min_price

                if max_price is not None:
                    query = query.where(MenuItemEnrichedView.menu_item_price <= Decimal(str(max_price)))
                    filters_applied['max_price'] = max_price

                # Order by rank, then name
                query = query.order_by(
                    MenuItemEnrichedView.menu_item_rank,
                    MenuItemEnrichedView.menu_item_name
                )

                # Get total count
                count_query = select(func.count()).select_from(query.subquery())
                total_result = await session.execute(count_query)
                total_count = total_result.scalar()

                # Apply pagination
                query = query.limit(limit).offset(offset)

                # Execute query
                result = await session.execute(query)
                items = result.scalars().all()

                # Convert to schema
                items_data = []
                for item in items:
                    item_dict = MenuItemForLLM.from_enriched_view(item).model_dump()
                    items_data.append(item_dict)

                # Build breadcrumb
                breadcrumb = []
                if section_name:
                    breadcrumb.append(section_name)
                if category_name:
                    breadcrumb.append(category_name)
                if subcategory_name:
                    breadcrumb.append(subcategory_name)

                # Get suggested refinements (unique subcategories if not already filtered)
                suggested_refinements = {}
                if not subcategory_name and items:
                    # Get unique subcategories from results
                    subcats = set()
                    for item in items:
                        if item.subcategories:
                            subcats.update(item.subcategories)
                    if subcats:
                        suggested_refinements['subcategories'] = sorted(list(subcats))

                # Price range in results
                if items:
                    prices = [float(item.menu_item_price) for item in items]
                    suggested_refinements['price_range'] = {
                        'min': min(prices),
                        'max': max(prices)
                    }

                logger.info(
                    "Retrieved items by filters",
                    filters=filters_applied,
                    total_count=total_count,
                    returned=len(items_data)
                )

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={
                        'items': items_data,
                        'total_count': total_count,
                        'returned_count': len(items_data),
                        'filters_applied': filters_applied,
                        'breadcrumb': breadcrumb,
                        'suggested_refinements': suggested_refinements,
                        'has_more': (offset + len(items_data)) < total_count,
                        'next_offset': offset + len(items_data) if (offset + len(items_data)) < total_count else None
                    }
                )

        except Exception as e:
            logger.error(f"Failed to get items by filters: {str(e)}")
            raise ToolError(f"Database error: {str(e)}", tool_name=self.name, retry_suggested=True)


@validate_schema(MenuItemEnrichedView)
class GetCurrentMealSuggestionsTool(ToolBase):
    """
    Get smart meal suggestions based on current time.

    Automatically detects meal time (breakfast/lunch/dinner) and returns
    curated items grouped by category with popular/recommended flags.

    Reduces decision fatigue for "show me the menu" requests.
    """

    def __init__(self):
        super().__init__(
            name="get_current_meal_suggestions",
            description="Get smart time-based meal suggestions",
            max_retries=2,
            timeout_seconds=15
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        """Validate suggestion parameters"""
        limit_per_category = kwargs.get('limit_per_category', 3)
        if limit_per_category < 1 or limit_per_category > 10:
            raise ToolError(
                f"limit_per_category must be between 1 and 10, got {limit_per_category}",
                tool_name=self.name
            )
        return kwargs

    async def _execute_impl(self, **kwargs) -> ToolResult:
        """
        Get meal suggestions using database-driven time-based filtering.

        Flow:
        1. Query meal_slot_timing to get current meal slot (opening_time, closing_time)
        2. Use those times to query menu_item_availability_schedule
        3. Fetch menu items where current time falls between time_from and time_to
        4. Group by category and return suggestions
        """
        try:
            meal_time_override = kwargs.get('meal_time_override')
            include_popular = kwargs.get('include_popular', True)
            include_recommended = kwargs.get('include_recommended', True)
            limit_per_category = kwargs.get('limit_per_category', 3)
            restaurant_id = kwargs.get('restaurant_id')

            async with get_db_session() as session:
                # Safe UUID parsing for restaurant_id
                restaurant_uuid = None
                if restaurant_id:
                    try:
                        restaurant_uuid = UUID(restaurant_id) if isinstance(restaurant_id, str) else restaurant_id
                    except (ValueError, AttributeError, TypeError):
                        logger.warning(f"Invalid restaurant_id provided: {restaurant_id}, ignoring filter")
                        restaurant_uuid = None
                # Step 1: Get current meal slot from meal_slot_timing table
                meal_slot = await get_current_meal_slot_from_db(session)

                if meal_slot:
                    meal_time = meal_slot['meal_type_name'].lower()
                    opening_time = meal_slot['opening_time']
                    closing_time = meal_slot['closing_time']

                    logger.info(
                        "Found meal slot from database",
                        meal_type=meal_time,
                        opening_time=str(opening_time),
                        closing_time=str(closing_time)
                    )
                else:
                    # Fallback to hardcoded if no slot found
                    meal_time = meal_time_override or get_current_meal_time()
                    opening_time = None
                    closing_time = None

                    logger.warning(
                        "No meal slot found in database, using fallback",
                        fallback_meal_time=meal_time
                    )

                # Override if explicitly provided
                if meal_time_override:
                    meal_time = meal_time_override

                # Step 2: Get menu items using meal_timings from enriched view
                # This correctly handles:
                # - Items with specific meal times (e.g., ['Breakfast', 'Lunch'])
                # - Items with 'All Day' meal timing
                # - Items with NO meal timing restrictions (NULL/empty = always available)
                meal_type_name = meal_time.capitalize()  # e.g., "Dinner", "Breakfast", "Lunch"

                # Step 3: Build main query using enriched view meal_timings array
                query = select(MenuItemEnrichedView).where(
                    and_(
                        MenuItemEnrichedView.is_deleted == False,
                        MenuItemEnrichedView.menu_item_in_stock == True,
                        or_(
                            # Items specifically available for current meal time
                            MenuItemEnrichedView.meal_timings.contains([meal_type_name]),
                            # Items available "All Day"
                            MenuItemEnrichedView.meal_timings.contains(['All Day']),
                            # Items with no meal timing restrictions (always available)
                            MenuItemEnrichedView.meal_timings.is_(None),
                            func.coalesce(func.array_length(MenuItemEnrichedView.meal_timings, 1), 0) == 0,
                        )
                    )
                )

                if restaurant_uuid:
                    query = query.where(MenuItemEnrichedView.restaurant_id == restaurant_uuid)

                # Prioritize popular/recommended
                if include_popular or include_recommended:
                    query = query.order_by(
                        MenuItemEnrichedView.menu_item_is_recommended.desc(),
                        MenuItemEnrichedView.menu_item_favorite.desc(),
                        MenuItemEnrichedView.menu_item_rank
                    )
                else:
                    query = query.order_by(MenuItemEnrichedView.menu_item_rank)

                # Execute query
                result = await session.execute(query)
                all_items = result.scalars().all()

                # Step 4: Group by category
                categories_dict = {}
                for item in all_items:
                    if not item.categories:
                        continue

                    # Use first category for grouping
                    category = item.categories[0]

                    if category not in categories_dict:
                        categories_dict[category] = []

                    # Limit items per category
                    if len(categories_dict[category]) < limit_per_category:
                        categories_dict[category].append(item)

                # Convert to response format
                categories_data = []
                for category_name, items in categories_dict.items():
                    items_data = []
                    for item in items:
                        item_dict = MenuItemForLLM.from_enriched_view(item).model_dump()
                        items_data.append(item_dict)

                    categories_data.append({
                        'name': category_name,
                        'items': items_data,
                        'total_in_category': len(items)
                    })

                # Sort categories by total item count (most popular first)
                categories_data.sort(key=lambda x: x['total_in_category'], reverse=True)

                # Prepare refinement prompt
                total_items = sum(len(cat['items']) for cat in categories_data)
                prompt_refinement = None
                if len(categories_data) > 1:
                    prompt_refinement = "Would you like to see a specific category, or filter by vegetarian/non-veg?"

                logger.info(
                    "Generated meal suggestions (time-based)",
                    meal_time=meal_time,
                    current_time=str(current_time),
                    categories=len(categories_data),
                    total_items=total_items
                )

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={
                        'meal_time': meal_time,
                        'current_time': str(current_time),
                        'time_slot': {
                            'opening_time': str(opening_time) if opening_time else None,
                            'closing_time': str(closing_time) if closing_time else None
                        },
                        'message': f"Here are our {meal_time} specials",
                        'categories': categories_data,
                        'total_categories': len(categories_data),
                        'total_items_shown': total_items,
                        'prompt_refinement': prompt_refinement
                    }
                )

        except Exception as e:
            logger.error(f"Failed to get meal suggestions: {str(e)}")
            raise ToolError(f"Database error: {str(e)}", tool_name=self.name, retry_suggested=True)


@validate_schema(MenuItemEnrichedView)
class RefineCurrentResultsTool(ToolBase):
    """
    Refine previous results with additional filters (context-aware).

    Combines previous filters with new ones for progressive refinement.
    Enables natural conversation flow:
    - "Show main courses" → "Only vegetarian" → "Under 200"

    Requires browsing_context from state.
    """

    def __init__(self):
        super().__init__(
            name="refine_current_results",
            description="Refine previous results with additional filters",
            max_retries=2,
            timeout_seconds=15
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        """Validate refinement parameters"""
        if not kwargs.get('additional_filters'):
            raise ToolError(
                "additional_filters is required",
                tool_name=self.name
            )
        if not kwargs.get('previous_filters'):
            raise ToolError(
                "previous_filters is required (from browsing context)",
                tool_name=self.name
            )
        return kwargs

    async def _execute_impl(self, **kwargs) -> ToolResult:
        try:
            additional_filters = kwargs.get('additional_filters', {})
            previous_filters = kwargs.get('previous_filters', {})
            limit = kwargs.get('limit', 20)
            offset = kwargs.get('offset', 0)
            restaurant_id = kwargs.get('restaurant_id')

            # Combine filters (additional filters override previous)
            combined_filters = {**previous_filters, **additional_filters}

            logger.info(
                "Refining results",
                previous_filters=previous_filters,
                additional_filters=additional_filters,
                combined_filters=combined_filters
            )

            # Use GetMenuItemsByFiltersTool to execute combined query
            get_items_tool = GetMenuItemsByFiltersTool()

            result = await get_items_tool.execute(
                section=combined_filters.get('section'),
                category=combined_filters.get('category'),
                subcategory=combined_filters.get('subcategory'),
                meal_timing=combined_filters.get('meal_timing'),
                available_only=combined_filters.get('available_only', True),
                min_price=combined_filters.get('min_price'),
                max_price=combined_filters.get('max_price'),
                limit=limit,
                offset=offset,
                restaurant_id=restaurant_id
            )

            if result.status != ToolStatus.SUCCESS:
                return result

            # Add refinement metadata
            result.data['refinement_applied'] = additional_filters
            result.data['all_filters'] = combined_filters

            logger.info(
                "Refinement completed",
                returned=result.data['returned_count'],
                total=result.data['total_count']
            )

            return result

        except Exception as e:
            logger.error(f"Failed to refine results: {str(e)}")
            raise ToolError(f"Refinement error: {str(e)}", tool_name=self.name, retry_suggested=True)


__all__ = [
    "GetMenuHierarchyTool",
    "GetMenuItemsByFiltersTool",
    "GetCurrentMealSuggestionsTool",
    "RefineCurrentResultsTool",
    "get_current_meal_time",
    "get_current_meal_slot_from_db",
    "get_menu_items_by_time_range"
]

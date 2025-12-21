"""
MCP Menu Tools
==============
Direct database-backed tools for menu operations.
No hallucinations - all data comes from PostgreSQL + ChromaDB.
"""

from typing import Dict, Any, List, Optional
from langchain_core.tools import tool
import structlog
from sqlalchemy import select, and_

from app.core.database import get_db_session
from app.features.food_ordering.models import MenuItem, MenuCategory, MenuItemCategoryMapping, MenuItemEnrichedView
from app.ai_services.vector_db_service import get_vector_db_service

logger = structlog.get_logger("mcp.menu_tools")


@tool
async def browse_menu(category: Optional[str] = None, restaurant_id: str = "rest_001") -> Dict[str, Any]:
    """
    Browse the restaurant menu, optionally filtered by category.

    Args:
        category: Optional category filter (e.g., "breakfast", "lunch", "dinner", "beverages")
        restaurant_id: Restaurant identifier

    Returns:
        Dict with menu items grouped by category
    """
    logger.info("browse_menu called", category=category, restaurant_id=restaurant_id)

    try:
        async with get_db_session() as session:
            # Build query
            query = select(
                MenuItem,
                MenuCategory.menu_category_name.label('category_name')
            ).join(
                MenuItemCategoryMapping,
                MenuItem.menu_item_id == MenuItemCategoryMapping.menu_item_id
            ).join(
                MenuCategory,
                MenuItemCategoryMapping.menu_category_id == MenuCategory.menu_category_id
            ).where(
                and_(
                    MenuItemCategoryMapping.is_primary == True,
                    MenuItem.menu_item_status == 'active',
                    MenuItem.deleted_at.is_(None),
                    MenuItem.menu_item_in_stock == True
                )
            )

            # Add category filter if specified
            if category:
                query = query.where(MenuCategory.menu_category_name.ilike(f"%{category}%"))

            result = await session.execute(query)
            rows = result.fetchall()

            # Group by category
            menu_by_category = {}
            for row in rows:
                item = row[0]
                cat_name = row[1] or "Other"

                if cat_name not in menu_by_category:
                    menu_by_category[cat_name] = []

                menu_by_category[cat_name].append({
                    "id": item.menu_item_id,
                    "name": item.menu_item_name,
                    "description": item.menu_item_description or "",
                    "price": float(item.menu_item_price),
                    "is_popular": item.menu_item_favorite or False,
                    "spice_level": item.menu_item_spice_level,
                    "dietary_info": []  # MenuItem doesn't have dietary_type field - it's a relationship
                })

            # Convert dictionary to list format expected by menu_browsing_agent
            # Format: [{category_name, items: [...]}, ...]
            menu_list = [
                {
                    "category_name": cat_name,
                    "items": items
                }
                for cat_name, items in menu_by_category.items()
            ]

            logger.info(
                "browse_menu success",
                categories_count=len(menu_list),
                total_items=len(rows)
            )

            return {
                "success": True,
                "menu": menu_list,  # Now returns list instead of dict
                "total_items": len(rows),
                "filter_applied": category
            }

    except Exception as e:
        logger.error("browse_menu failed", error=str(e), exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "menu": {}
        }


@tool
async def search_menu(
    query: str,
    restaurant_id: str = "rest_001",
    limit: int = 10
) -> Dict[str, Any]:
    """
    Semantic search for menu items using vector similarity.

    Args:
        query: Search query (e.g., "spicy chicken", "vegetarian options", "breakfast items")
        restaurant_id: Restaurant identifier
        limit: Maximum number of results

    Returns:
        Dict with matching menu items ranked by relevance
    """
    logger.info("search_menu called", query=query, limit=limit)

    try:
        # Get vector DB service
        vector_db = get_vector_db_service()

        # Perform semantic search
        results = await vector_db.semantic_search(query, limit=limit)

        # Fetch full details from database for each result
        menu_items = []
        async with get_db_session() as session:
            for result in results:
                item_id = result.get('id')
                if not item_id:
                    continue

                # Get full item details
                query_stmt = select(MenuItem).where(
                    and_(
                        MenuItem.menu_item_id == item_id,
                        MenuItem.menu_item_status == 'active',
                        MenuItem.deleted_at.is_(None)
                    )
                )
                db_result = await session.execute(query_stmt)
                item = db_result.scalar_one_or_none()

                if item:
                    menu_items.append({
                        "id": item.menu_item_id,
                        "name": item.menu_item_name,
                        "description": item.menu_item_description or "",
                        "price": float(item.menu_item_price),
                        "category": result.get('category', 'Other'),
                        "similarity_score": result.get('similarity_score', 0.0),
                        "is_available": item.menu_item_in_stock,
                        "spice_level": item.menu_item_spice_level,
                        "dietary_info": []  # MenuItem doesn't have dietary_type field - it's a relationship
                    })

        logger.info("search_menu success", query=query, results_count=len(menu_items))

        return {
            "success": True,
            "query": query,
            "results": menu_items,
            "count": len(menu_items)
        }

    except Exception as e:
        logger.error("search_menu failed", query=query, error=str(e), exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "query": query,
            "results": []
        }


@tool
async def get_menu_item(
    item_name: str,
    restaurant_id: str = "rest_001"
) -> Dict[str, Any]:
    """
    Get detailed information about a specific menu item.

    Args:
        item_name: Name of the menu item
        restaurant_id: Restaurant identifier

    Returns:
        Dict with item details
    """
    logger.info("get_menu_item called", item_name=item_name)

    try:
        async with get_db_session() as session:
            # Fuzzy search by name
            query = select(
                MenuItem,
                MenuCategory.menu_category_name.label('category_name')
            ).join(
                MenuItemCategoryMapping,
                MenuItem.menu_item_id == MenuItemCategoryMapping.menu_item_id,
                isouter=True
            ).join(
                MenuCategory,
                MenuItemCategoryMapping.menu_category_id == MenuCategory.menu_category_id,
                isouter=True
            ).where(
                and_(
                    MenuItem.menu_item_name.ilike(f"%{item_name}%"),
                    MenuItem.menu_item_status == 'active',
                    MenuItem.deleted_at.is_(None)
                )
            ).limit(1)

            result = await session.execute(query)
            row = result.first()

            if not row:
                return {
                    "success": False,
                    "error": f"Menu item '{item_name}' not found",
                    "item": None
                }

            item = row[0]
            category = row[1] or "Other"

            item_data = {
                "id": item.menu_item_id,
                "name": item.menu_item_name,
                "description": item.menu_item_description or "",
                "price": float(item.menu_item_price),
                "category": category,
                "is_available": item.menu_item_in_stock,
                "is_popular": item.menu_item_favorite or False,
                "spice_level": item.menu_item_spice_level,
                "dietary_info": [],  # MenuItem doesn't have dietary_type field - it's a relationship
                "allergens": []  # MenuItem doesn't have allergen_info field - it's a relationship
            }

            logger.info("get_menu_item success", item_name=item_name, found=item.menu_item_name)

            return {
                "success": True,
                "item": item_data
            }

    except Exception as e:
        logger.error("get_menu_item failed", item_name=item_name, error=str(e), exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "item": None
        }


# Export all menu tools
MENU_TOOLS = [browse_menu, search_menu, get_menu_item]

"""
Index Menu Items to Vector Database
=====================================
One-time migration script to index all existing menu items into ChromaDB.

Run this after installing ChromaDB:
    python scripts/index_menu_to_vector_db.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select
from app.core.database import get_db_session, db_manager
from app.features.food_ordering.models import MenuItem, MenuCategory, MenuItemCategoryMapping
from app.ai_services.vector_db_service import get_vector_db_service
import structlog

logger = structlog.get_logger("scripts.index_menu")


async def index_all_menu_items():
    """
    Load all menu items from PostgreSQL and index them in ChromaDB.
    """
    logger.info("Starting menu indexing to vector database")

    # Initialize database connection
    logger.info("Initializing database connection")
    db_manager.init_database()

    # Get vector DB service
    vector_db = get_vector_db_service()

    # Clear existing data for fresh start
    logger.info("Clearing existing vector collection")
    vector_db.clear_collection()

    # Fetch all menu items from database
    async with get_db_session() as session:
        # Join MenuItem with category to get category name
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
            MenuItemCategoryMapping.is_primary == True,
            MenuItem.menu_item_status == 'active',
            MenuItem.deleted_at.is_(None)
        )

        result = await session.execute(query)
        rows = result.fetchall()

        logger.info(
            "Fetched menu items from database",
            count=len(rows)
        )

        # Prepare items for bulk indexing
        items_to_index = []
        for row in rows:
            menu_item = row[0]  # MenuItem object
            category_name = row[1]  # category_name from join

            # Prepare item data
            item_data = {
                'id': str(menu_item.menu_item_id),
                'name': menu_item.menu_item_name,
                'description': menu_item.menu_item_description or '',
                'category': category_name or 'Uncategorized',
                'price': float(menu_item.menu_item_price),
                'metadata': {
                    'is_popular': menu_item.menu_item_favorite or False,
                    'is_available': menu_item.menu_item_in_stock or False,
                    'spice_level': menu_item.menu_item_spice_level or 'none'
                    # Note: dietary_info and allergens removed - ChromaDB only allows str/int/float/bool/None in metadata
                }
            }

            items_to_index.append(item_data)

            # Print sample for verification
            if len(items_to_index) <= 3:
                logger.info(
                    "Sample item",
                    name=item_data['name'],
                    category=item_data['category'],
                    price=item_data['price']
                )

        # Bulk index all items
        if items_to_index:
            logger.info(
                "Indexing items to vector database",
                count=len(items_to_index)
            )
            await vector_db.bulk_index_menu_items(items_to_index)

            # Get stats
            stats = vector_db.get_stats()
            logger.info(
                "Indexing complete",
                total_items=stats['total_items'],
                storage_type=stats['storage_type']
            )

            # Test search
            logger.info("Testing semantic search...")
            test_queries = [
                "something spicy",
                "chicken dish",
                "vegetarian options"
            ]

            for query in test_queries:
                results = await vector_db.semantic_search(query, limit=3)
                logger.info(
                    "Test search",
                    query=query,
                    results_count=len(results),
                    top_result=results[0]['name'] if results else None,
                    similarity=results[0]['similarity_score'] if results else 0
                )
        else:
            logger.warning("No menu items found to index")

    logger.info("Menu indexing completed successfully")


if __name__ == "__main__":
    asyncio.run(index_all_menu_items())

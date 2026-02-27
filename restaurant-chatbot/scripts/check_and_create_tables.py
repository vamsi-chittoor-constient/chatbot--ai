"""
Check and Create Database Tables
=================================
Simple script to check existing tables and create menu-related tables if needed.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import db_manager, get_db_session
from sqlalchemy import text
import structlog

logger = structlog.get_logger("check_tables")


async def main():
    """Check existing tables and create menu tables if needed."""

    # Initialize database
    logger.info("Initializing database connection")
    db_manager.init_database()

    # Check existing tables
    async with get_db_session() as session:
        result = await session.execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
        )
        tables = [row[0] for row in result]

        logger.info("Existing tables", count=len(tables))
        for table in tables:
            print(f"  - {table}")

        # Check if menu tables exist
        menu_tables = [
            'dietary_types', 'allergens', 'menu_sections', 'menu_categories',
            'menu_item', 'menu_item_category_mapping', 'menu_item_dietary_mapping',
            'menu_item_allergen_mapping'
        ]

        missing = [t for t in menu_tables if t not in tables]

        if missing:
            logger.warning("Missing menu tables", tables=missing)
            logger.info("You need to run database migrations or create tables manually")
            logger.info("Try running: python scripts/init_database.py")
            return 1
        else:
            logger.info("All required menu tables exist!")
            return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

"""
Run 3NF Menu Database Migration
================================

This script executes the database migration to:
1. Drop old menu tables (menu_categories, menu_items)
2. Create new 3NF schema (18 normalized tables)

Uses SQLAlchemy to connect and execute SQL migrations.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.core.database import get_db_session, db_manager
from app.core.logging_config import get_logger
import re

logger = get_logger(__name__)


async def run_migration():
    """Execute the 3NF migration scripts using psql."""
    import subprocess
    import os

    logger.info("=" * 60)
    logger.info("Starting 3NF Menu Database Migration")
    logger.info("=" * 60)

    # Read SQL migration files
    migrations_dir = project_root / "db_migrations"
    parts_dir = migrations_dir / "parts"

    drop_script_path = migrations_dir / "000_drop_old_menu_tables.sql"
    create_tables_path = parts_dir / "001_create_tables.sql"
    create_functions_path = parts_dir / "002_create_functions.sql"
    create_triggers_path = parts_dir / "003_create_triggers.sql"

    if not drop_script_path.exists():
        logger.error(f"Drop script not found: {drop_script_path}")
        return False

    if not create_tables_path.exists():
        logger.error(f"Create tables script not found: {create_tables_path}")
        return False

    if not create_functions_path.exists():
        logger.error(f"Create functions script not found: {create_functions_path}")
        return False

    if not create_triggers_path.exists():
        logger.error(f"Create triggers script not found: {create_triggers_path}")
        return False

    # Database connection details from config
    from app.core.config import settings

    # Set environment variable for password
    env = os.environ.copy()
    env['PGPASSWORD'] = settings.DB_PASSWORD

    db_host = settings.DB_HOST
    db_port = settings.DB_PORT
    db_name = settings.DB_NAME
    db_user = settings.DB_USER

    try:
        # Step 1: Drop old tables
        logger.info("\n" + "=" * 60)
        logger.info("STEP 1: Dropping old menu tables")
        logger.info("=" * 60)

        result = subprocess.run(
            ['psql', '-h', db_host, '-p', str(db_port), '-U', db_user, '-d', db_name, '-f', str(drop_script_path)],
            env=env,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            logger.error(f"Failed to drop tables: {result.stderr}")
            return False

        logger.info("✓ Old tables dropped successfully")

        # Step 2: Create tables
        logger.info("\n" + "=" * 60)
        logger.info("STEP 2: Creating tables")
        logger.info("=" * 60)

        result = subprocess.run(
            ['psql', '-h', db_host, '-p', str(db_port), '-U', db_user, '-d', db_name, '-f', str(create_tables_path)],
            env=env,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            logger.error(f"Failed to create tables: {result.stderr}")
            return False

        logger.info("✓ Tables created successfully")

        # Step 3: Create functions and views
        logger.info("\n" + "=" * 60)
        logger.info("STEP 3: Creating functions and materialized view")
        logger.info("=" * 60)

        result = subprocess.run(
            ['psql', '-h', db_host, '-p', str(db_port), '-U', db_user, '-d', db_name, '-f', str(create_functions_path)],
            env=env,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            logger.error(f"Failed to create functions: {result.stderr}")
            return False

        logger.info("✓ Functions and views created successfully")

        # Step 4: Create triggers
        logger.info("\n" + "=" * 60)
        logger.info("STEP 4: Creating triggers")
        logger.info("=" * 60)

        result = subprocess.run(
            ['psql', '-h', db_host, '-p', str(db_port), '-U', db_user, '-d', db_name, '-f', str(create_triggers_path)],
            env=env,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            logger.error(f"Failed to create triggers: {result.stderr}")
            return False

        logger.info("✓ Triggers created successfully")

        # Step 5: Verify tables created using psql
        logger.info("\n" + "=" * 60)
        logger.info("STEP 5: Verifying tables")
        logger.info("=" * 60)

        verify_query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN (
                'categories', 'menu_items', 'item_categories',
                'meal_timings', 'item_availability',
                'ingredients', 'item_ingredients',
                'dietary_tags', 'item_dietary_tags',
                'spice_levels', 'cooking_methods',
                'serving_units', 'item_servings',
                'inventory', 'item_variants',
                'item_recommendations', 'user_preferences', 'order_history'
            )
            ORDER BY table_name;
        """

        result = subprocess.run(
            ['psql', '-h', db_host, '-p', str(db_port), '-U', db_user, '-d', db_name, '-t', '-c', verify_query],
            env=env,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            tables = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
            logger.info(f"Tables created: {len(tables)}/18")
            for table in tables:
                logger.info(f"  ✓ {table}")

        # Check materialized view
        view_query = "SELECT matviewname FROM pg_matviews WHERE matviewname = 'menu_items_enriched';"
        result = subprocess.run(
            ['psql', '-h', db_host, '-p', str(db_port), '-U', db_user, '-d', db_name, '-t', '-c', view_query],
            env=env,
            capture_output=True,
            text=True
        )

        if result.returncode == 0 and result.stdout.strip():
            logger.info(f"  ✓ menu_items_enriched (materialized view)")

        logger.info("\n" + "=" * 60)
        logger.info("Migration completed successfully!")
        logger.info("=" * 60)
        logger.info("\nNext steps:")
        logger.info("1. Run data import: python scripts/import_menu_3nf.py")
        logger.info("2. Refresh materialized view: SELECT refresh_menu_cache();")
        logger.info("3. Update application code to use new models")

        return True

    except Exception as e:
        logger.error(f"Migration failed: {str(e)}", exc_info=True)
        return False


async def check_current_tables():
    """Check what menu tables currently exist."""

    logger.info("\n" + "=" * 60)
    logger.info("Checking current database state...")
    logger.info("=" * 60)

    # Initialize database if needed
    if not db_manager.is_initialized():
        db_manager.init_database()

    async with db_manager.engine.begin() as conn:
        try:
            # Check for old tables
            result = await conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND (table_name LIKE '%menu%' OR table_name LIKE '%categor%')
                ORDER BY table_name;
            """))

            tables = [row[0] for row in result.fetchall()]

            if tables:
                logger.info("Current menu-related tables:")
                for table in tables:
                    logger.info(f"  - {table}")
            else:
                logger.info("No menu-related tables found")

            return tables

        except Exception as e:
            logger.error(f"Failed to check tables: {str(e)}", exc_info=True)
            return []


async def main():
    """Main entry point."""

    print("\n" + "=" * 60)
    print("3NF Menu Database Migration Tool")
    print("=" * 60)

    # Check current state
    current_tables = await check_current_tables()

    # Confirm migration
    print("\n" + "=" * 60)
    print("WARNING: This will DROP all existing menu tables!")
    print("=" * 60)

    if current_tables:
        print("\nTables that will be DROPPED:")
        for table in current_tables:
            print(f"  ✗ {table}")

    print("\nNew 3NF tables that will be CREATED:")
    new_tables = [
        "categories", "menu_items", "item_categories",
        "meal_timings", "item_availability",
        "ingredients", "item_ingredients",
        "dietary_tags", "item_dietary_tags",
        "spice_levels", "cooking_methods",
        "serving_units", "item_servings",
        "inventory", "item_variants",
        "item_recommendations", "user_preferences", "order_history",
        "menu_items_enriched (materialized view)"
    ]
    for table in new_tables:
        print(f"  ✓ {table}")

    print("\n" + "=" * 60)
    print("\nProceeding with migration automatically...")
    print("=" * 60)

    # Run migration
    success = await run_migration()

    if success:
        print("\n" + "=" * 60)
        print("✓ Migration completed successfully!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("✗ Migration failed - check logs for details")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

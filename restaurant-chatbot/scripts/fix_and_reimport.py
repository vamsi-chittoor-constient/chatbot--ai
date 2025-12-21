#!/usr/bin/env python3
"""
Fix schema and re-import menu data
"""
import asyncio
import asyncpg

DB_CONFIG = {
    "host": "37.27.194.66",
    "port": 5430,
    "database": "restaurant_ai_dev",
    "user": "postgres",
    "password": "A24_rest!op"
}

async def fix_schema():
    """Extend item_id column and clear tables."""
    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        print("Dropping materialized view...")
        await conn.execute("DROP MATERIALIZED VIEW IF EXISTS menu_items_enriched CASCADE;")

        print("Extending item_id column length...")

        # Extend column in all tables that reference it
        tables_to_update = [
            "menu_items", "item_categories", "item_availability",
            "item_ingredients", "item_dietary_tags", "item_servings",
            "inventory", "item_variants", "item_recommendations"
        ]

        for table in tables_to_update:
            try:
                await conn.execute(f"ALTER TABLE {table} ALTER COLUMN item_id TYPE VARCHAR(50);")
                print(f"  ✓ Updated {table}")
            except Exception as e:
                print(f"  ⚠ Skipped {table}: {e}")

        print("✓ Schema updated")

        print("\nClearing existing data...")
        await conn.execute("TRUNCATE TABLE inventory CASCADE;")
        await conn.execute("TRUNCATE TABLE item_servings CASCADE;")
        await conn.execute("TRUNCATE TABLE item_dietary_tags CASCADE;")
        await conn.execute("TRUNCATE TABLE item_ingredients CASCADE;")
        await conn.execute("TRUNCATE TABLE item_availability CASCADE;")
        await conn.execute("TRUNCATE TABLE item_categories CASCADE;")
        await conn.execute("TRUNCATE TABLE menu_items CASCADE;")
        await conn.execute("TRUNCATE TABLE categories CASCADE;")
        await conn.execute("TRUNCATE TABLE ingredients CASCADE;")

        print("✓ Tables cleared")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(fix_schema())
    print("\nReady to re-import. Run: python scripts/import_menu_fixed.py")

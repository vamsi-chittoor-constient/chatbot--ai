#!/usr/bin/env python3
"""Diagnose table existence and schema issues"""
import asyncio
import asyncpg

DB_CONFIG = {
    "host": "37.27.194.66",
    "port": 5430,
    "database": "restaurant_ai_dev",
    "user": "postgres",
    "password": "A24_rest!op"
}

async def diagnose():
    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        print("=" * 70)
        print("DATABASE DIAGNOSTICS")
        print("=" * 70)

        # Current database
        current_db = await conn.fetchval("SELECT current_database()")
        print(f"\nCurrent database: {current_db}")

        # Current schema search path
        search_path = await conn.fetchval("SHOW search_path")
        print(f"Search path: {search_path}")

        # Check if item_categories exists in any schema
        print("\nSearching for 'item_categories' table...")
        result = await conn.fetch("""
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_name = 'item_categories'
        """)

        if result:
            for row in result:
                print(f"  Found: {row['table_schema']}.{row['table_name']}")
        else:
            print("  ❌ Table 'item_categories' NOT FOUND in any schema")

        # List all tables with 'item' in the name
        print("\nAll tables containing 'item':")
        tables = await conn.fetch("""
            SELECT schemaname, tablename
            FROM pg_tables
            WHERE tablename LIKE '%item%'
            AND schemaname NOT IN ('pg_catalog', 'information_schema')
            ORDER BY tablename
        """)

        for table in tables:
            print(f"  - {table['schemaname']}.{table['tablename']}")

        # Test query
        print("\nTesting queries...")

        try:
            count = await conn.fetchval("SELECT COUNT(*) FROM item_categories")
            print(f"  ✓ SELECT COUNT(*) FROM item_categories: {count} rows")
        except Exception as e:
            print(f"  ❌ SELECT COUNT(*) FROM item_categories: {e}")

        try:
            count = await conn.fetchval("SELECT COUNT(*) FROM public.item_categories")
            print(f"  ✓ SELECT COUNT(*) FROM public.item_categories: {count} rows")
        except Exception as e:
            print(f"  ❌ SELECT COUNT(*) FROM public.item_categories: {e}")

        # List all our 18 tables
        print("\nChecking all 18 expected tables:")
        expected_tables = [
            "spice_levels", "cooking_methods", "serving_units", "meal_timings",
            "ingredients", "dietary_tags", "categories", "menu_items",
            "item_categories", "item_availability", "item_ingredients",
            "item_dietary_tags", "item_servings", "inventory", "item_variants",
            "item_recommendations", "user_preferences", "order_history"
        ]

        for table in expected_tables:
            exists = await conn.fetchval(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = '{table}'
                )
            """)
            status = "✓" if exists else "❌ MISSING"
            print(f"  {table:<30} {status}")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(diagnose())

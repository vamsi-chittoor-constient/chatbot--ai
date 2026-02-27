#!/usr/bin/env python3
"""Analyze current restaurant and related tables for multi-tenant design"""
import asyncio
import asyncpg

DB_CONFIG = {
    "host": "37.27.194.66",
    "port": 5430,
    "database": "restaurant_ai_dev",
    "user": "postgres",
    "password": "A24_rest!op"
}

async def analyze():
    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        print("=" * 80)
        print("MULTI-TENANT ARCHITECTURE ANALYSIS")
        print("=" * 80)

        # Check restaurant_config table
        print("\n1. RESTAURANT_CONFIG TABLE:")
        restaurants = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'restaurant_config'
            ORDER BY ordinal_position
        """)

        for col in restaurants:
            print(f"  - {col['column_name']:<30} {col['data_type']:<20} nullable={col['is_nullable']}")

        # Check existing restaurants
        rest_count = await conn.fetchval("SELECT COUNT(*) FROM restaurant_config")
        print(f"\n  Current restaurants: {rest_count}")

        if rest_count > 0:
            sample = await conn.fetch("SELECT id, name, branch_name FROM restaurant_config LIMIT 3")
            for r in sample:
                print(f"    - {r['id']}: {r['name']} ({r['branch_name'] or 'Main'})")

        # Check current menu_items structure
        print("\n2. CURRENT MENU_ITEMS TABLE:")
        menu_cols = await conn.fetch("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'menu_items'
            ORDER BY ordinal_position
        """)

        for col in menu_cols:
            print(f"  - {col['column_name']:<30} {col['data_type']}")

        # Check if restaurant_id exists in menu tables
        print("\n3. CHECKING FOR EXISTING RESTAURANT_ID COLUMNS:")
        menu_related_tables = [
            'menu_items', 'categories', 'spice_levels', 'cooking_methods',
            'serving_units', 'meal_timings', 'ingredients', 'dietary_tags'
        ]

        for table in menu_related_tables:
            has_rest_id = await conn.fetchval(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns
                    WHERE table_name = '{table}' AND column_name = 'restaurant_id'
                )
            """)
            status = "✓ EXISTS" if has_rest_id else "✗ MISSING"
            print(f"  {table:<30} {status}")

        # Check foreign key relationships
        print("\n4. EXISTING FOREIGN KEY RELATIONSHIPS:")
        fks = await conn.fetch("""
            SELECT
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name IN ('menu_items', 'categories', 'item_categories')
            ORDER BY tc.table_name, kcu.column_name
        """)

        for fk in fks:
            print(f"  {fk['table_name']}.{fk['column_name']} -> {fk['foreign_table_name']}.{fk['foreign_column_name']}")

        print("\n" + "=" * 80)
        print("RECOMMENDATIONS FOR MULTI-TENANT ARCHITECTURE")
        print("=" * 80)

        print("""
1. ID FORMAT CHANGES:
   - menu_items.item_id: MIT + 6 random chars (e.g., MIT4A7B9C)
   - categories.category_id: MCT + 5 random chars (e.g., MCT2X9Y4)

2. ADD restaurant_id TO THESE TABLES:
   Core Tables:
   ✓ menu_items - FK to restaurant_config.id
   ✓ categories - FK to restaurant_config.id (categories can be per-restaurant)

   Lookup Tables (DECISION NEEDED):
   ? spice_levels - GLOBAL or PER-RESTAURANT?
   ? cooking_methods - GLOBAL or PER-RESTAURANT?
   ? serving_units - GLOBAL or PER-RESTAURANT?
   ? meal_timings - GLOBAL or PER-RESTAURANT?
   ? ingredients - GLOBAL or PER-RESTAURANT?
   ? dietary_tags - GLOBAL or PER-RESTAURANT?

3. RECOMMENDED APPROACH:
   Option A: GLOBAL LOOKUPS (recommended for consistency)
   - Keep lookup tables global (no restaurant_id)
   - Only add restaurant_id to: menu_items, categories
   - Junction tables inherit restaurant context from menu_items

   Option B: PER-RESTAURANT LOOKUPS
   - Add restaurant_id to ALL tables
   - Each restaurant has own spice levels, dietary tags, etc.
   - More flexible but more complex
        """)

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(analyze())

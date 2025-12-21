#!/usr/bin/env python3
"""Final verification of complete data import"""
import asyncio
import asyncpg

DB_CONFIG = {
    "host": "37.27.194.66",
    "port": 5430,
    "database": "restaurant_ai_dev",
    "user": "postgres",
    "password": "A24_rest!op"
}

async def verify():
    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        print("=" * 70)
        print("FINAL DATA VERIFICATION - ALL 18 TABLES")
        print("=" * 70)

        # Check all 18 tables
        tables = [
            ("spice_levels", "Lookup"),
            ("cooking_methods", "Lookup"),
            ("serving_units", "Lookup"),
            ("meal_timings", "Lookup"),
            ("ingredients", "Lookup"),
            ("dietary_tags", "Lookup"),
            ("categories", "Core"),
            ("menu_items", "Core"),
            ("item_categories", "Core/Junction"),
            ("item_availability", "Junction"),
            ("item_ingredients", "Junction"),
            ("item_dietary_tags", "Junction"),
            ("item_servings", "Junction"),
            ("inventory", "Operational"),
            ("item_variants", "Operational"),
            ("item_recommendations", "Operational"),
            ("user_preferences", "Operational"),
            ("order_history", "Operational"),
        ]

        print(f"\n{'Table':<30} {'Type':<15} {'Rows':<10} Status")
        print("-" * 70)

        for table, table_type in tables:
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
            status = "✓ HAS DATA" if count > 0 else "⚠ EMPTY"
            print(f"{table:<30} {table_type:<15} {count:<10} {status}")

        # Check menu_items columns
        print("\n" + "=" * 70)
        print("MENU_ITEMS COLUMN VERIFICATION")
        print("=" * 70)

        sample = await conn.fetchrow("""
            SELECT
                item_name, base_price, prep_time_minutes, calories,
                is_available, is_featured, is_seasonal,
                spice_level_id, cooking_method_id
            FROM menu_items
            WHERE prep_time_minutes IS NOT NULL
            LIMIT 1
        """)

        if sample:
            print(f"\nSample item: {sample['item_name']}")
            print(f"  Price: ₹{sample['base_price']}")
            print(f"  Prep time: {sample['prep_time_minutes']} minutes")
            print(f"  Calories: {sample['calories']}")
            print(f"  Available: {sample['is_available']}")
            print(f"  Featured: {sample['is_featured']}")
            print(f"  Seasonal: {sample['is_seasonal']}")
            print(f"  Has spice level: {sample['spice_level_id'] is not None}")
            print(f"  Has cooking method: {sample['cooking_method_id'] is not None}")

        # Check data completeness
        print("\n" + "=" * 70)
        print("DATA COMPLETENESS CHECK")
        print("=" * 70)

        stats = await conn.fetchrow("""
            SELECT
                COUNT(*) as total_items,
                COUNT(prep_time_minutes) as has_prep_time,
                COUNT(calories) as has_calories,
                COUNT(CASE WHEN is_seasonal THEN 1 END) as seasonal_items,
                COUNT(spice_level_id) as has_spice_level,
                COUNT(cooking_method_id) as has_cooking_method
            FROM menu_items
        """)

        print(f"\nTotal menu items: {stats['total_items']}")
        print(f"Items with prep time: {stats['has_prep_time']} ({stats['has_prep_time']/stats['total_items']*100:.1f}%)")
        print(f"Items with calories: {stats['has_calories']} ({stats['has_calories']/stats['total_items']*100:.1f}%)")
        print(f"Seasonal items: {stats['seasonal_items']}")
        print(f"Items with spice level: {stats['has_spice_level']} ({stats['has_spice_level']/stats['total_items']*100:.1f}%)")
        print(f"Items with cooking method: {stats['has_cooking_method']} ({stats['has_cooking_method']/stats['total_items']*100:.1f}%)")

        # Check relationships
        print("\n" + "=" * 70)
        print("RELATIONSHIP VERIFICATION")
        print("=" * 70)

        rel_stats = await conn.fetch("""
            SELECT
                (SELECT COUNT(*) FROM item_categories) as item_cat_links,
                (SELECT COUNT(*) FROM item_availability) as item_timing_links,
                (SELECT COUNT(*) FROM item_dietary_tags) as item_diet_links,
                (SELECT COUNT(*) FROM item_servings) as item_serving_links,
                (SELECT COUNT(*) FROM inventory) as item_inventory_links
        """)

        rel = rel_stats[0]
        print(f"\nItem-Category links: {rel['item_cat_links']}")
        print(f"Item-Timing links: {rel['item_timing_links']}")
        print(f"Item-DietaryTag links: {rel['item_diet_links']}")
        print(f"Item-Serving links: {rel['item_serving_links']}")
        print(f"Inventory records: {rel['item_inventory_links']}")

        print("\n" + "=" * 70)
        print("✓ VERIFICATION COMPLETE")
        print("=" * 70)

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(verify())

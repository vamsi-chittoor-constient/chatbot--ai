#!/usr/bin/env python3
"""
Comprehensive Data Quality Verification
========================================
Verify all aspects of the multi-tenant 3NF database
"""
import asyncio
import asyncpg

DB_CONFIG = {
    "host": "37.27.194.66",
    "port": 5430,
    "database": "restaurant_ai_dev",
    "user": "dev_explorer",
    "password": "restaurant24"
}

async def verify():
    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        print("=" * 80)
        print("COMPREHENSIVE DATA QUALITY VERIFICATION")
        print("=" * 80)

        # 1. ID FORMAT CHECK
        print("\n[1] ID FORMAT VERIFICATION")
        print("-" * 80)

        # Check menu items
        wrong_item_ids = await conn.fetch("""
            SELECT item_id, item_name
            FROM menu_items
            WHERE item_id NOT LIKE 'MIT%' OR LENGTH(item_id) != 9
            LIMIT 10
        """)

        if wrong_item_ids:
            print(f"  ❌ Found {len(wrong_item_ids)} items with wrong ID format:")
            for item in wrong_item_ids:
                print(f"     {item['item_id']} - {item['item_name']}")
        else:
            total_items = await conn.fetchval("SELECT COUNT(*) FROM menu_items")
            print(f"  ✓ All {total_items} menu items have correct MIT format (MIT + 6 chars)")

        # Check categories
        wrong_cat_ids = await conn.fetch("""
            SELECT category_id, category_name
            FROM categories
            WHERE category_id NOT LIKE 'MCT%' OR LENGTH(category_id) != 8
            LIMIT 10
        """)

        if wrong_cat_ids:
            print(f"  ❌ Found {len(wrong_cat_ids)} categories with wrong ID format:")
            for cat in wrong_cat_ids:
                print(f"     {cat['category_id']} - {cat['category_name']}")
        else:
            total_cats = await conn.fetchval("SELECT COUNT(*) FROM categories")
            print(f"  ✓ All {total_cats} categories have correct MCT format (MCT + 5 chars)")

        # 2. RESTAURANT LINKING
        print("\n[2] RESTAURANT LINKING VERIFICATION")
        print("-" * 80)

        items_no_rest = await conn.fetchval("""
            SELECT COUNT(*) FROM menu_items WHERE restaurant_id IS NULL
        """)
        cats_no_rest = await conn.fetchval("""
            SELECT COUNT(*) FROM categories WHERE restaurant_id IS NULL
        """)

        if items_no_rest > 0:
            print(f"  ❌ {items_no_rest} menu items have no restaurant_id")
        else:
            print(f"  ✓ All menu items linked to restaurants")

        if cats_no_rest > 0:
            print(f"  ❌ {cats_no_rest} categories have no restaurant_id")
        else:
            print(f"  ✓ All categories linked to restaurants")

        # Show restaurant distribution
        rest_dist = await conn.fetch("""
            SELECT r.id, r.name, COUNT(m.item_id) as item_count
            FROM restaurant_config r
            LEFT JOIN menu_items m ON r.id = m.restaurant_id
            GROUP BY r.id, r.name
        """)

        print(f"\n  Restaurant distribution:")
        for r in rest_dist:
            print(f"    {r['id']}: {r['name']} - {r['item_count']} items")

        # 3. DATA COMPLETENESS
        print("\n[3] DATA COMPLETENESS CHECK")
        print("-" * 80)

        completeness = await conn.fetchrow("""
            SELECT
                COUNT(*) as total_items,
                COUNT(item_name) as has_name,
                COUNT(base_price) as has_price,
                COUNT(restaurant_id) as has_restaurant,
                COUNT(prep_time_minutes) as has_prep_time,
                COUNT(calories) as has_calories,
                COUNT(spice_level_id) as has_spice,
                COUNT(cooking_method_id) as has_cooking_method
            FROM menu_items
        """)

        total = completeness['total_items']
        print(f"  Total items: {total}")
        print(f"  - Has name: {completeness['has_name']} ({completeness['has_name']/total*100:.1f}%)")
        print(f"  - Has price: {completeness['has_price']} ({completeness['has_price']/total*100:.1f}%)")
        print(f"  - Has restaurant: {completeness['has_restaurant']} ({completeness['has_restaurant']/total*100:.1f}%)")
        print(f"  - Has prep time: {completeness['has_prep_time']} ({completeness['has_prep_time']/total*100:.1f}%)")
        print(f"  - Has calories: {completeness['has_calories']} ({completeness['has_calories']/total*100:.1f}%)")
        print(f"  - Has spice level: {completeness['has_spice']} ({completeness['has_spice']/total*100:.1f}%)")
        print(f"  - Has cooking method: {completeness['has_cooking_method']} ({completeness['has_cooking_method']/total*100:.1f}%)")

        # 4. RELATIONSHIP INTEGRITY
        print("\n[4] RELATIONSHIP INTEGRITY CHECK")
        print("-" * 80)

        # Check item_categories links
        ic_count = await conn.fetchval("SELECT COUNT(*) FROM item_categories")
        orphan_ic = await conn.fetchval("""
            SELECT COUNT(*) FROM item_categories ic
            WHERE NOT EXISTS (SELECT 1 FROM menu_items m WHERE m.item_id = ic.item_id)
               OR NOT EXISTS (SELECT 1 FROM categories c WHERE c.category_id = ic.category_id)
        """)

        print(f"  item_categories: {ic_count} total")
        if orphan_ic > 0:
            print(f"    ❌ {orphan_ic} orphaned links")
        else:
            print(f"    ✓ All links valid")

        # Check item_availability
        ia_count = await conn.fetchval("SELECT COUNT(*) FROM item_availability")
        orphan_ia = await conn.fetchval("""
            SELECT COUNT(*) FROM item_availability ia
            WHERE NOT EXISTS (SELECT 1 FROM menu_items m WHERE m.item_id = ia.item_id)
        """)

        print(f"  item_availability: {ia_count} total")
        if orphan_ia > 0:
            print(f"    ❌ {orphan_ia} orphaned links")
        else:
            print(f"    ✓ All links valid")

        # Check inventory
        inv_count = await conn.fetchval("SELECT COUNT(*) FROM inventory")
        orphan_inv = await conn.fetchval("""
            SELECT COUNT(*) FROM inventory i
            WHERE NOT EXISTS (SELECT 1 FROM menu_items m WHERE m.item_id = i.item_id)
        """)

        print(f"  inventory: {inv_count} total")
        if orphan_inv > 0:
            print(f"    ❌ {orphan_inv} orphaned records")
        else:
            print(f"    ✓ All records valid")

        # 5. SAMPLE DATA REVIEW
        print("\n[5] SAMPLE DATA REVIEW")
        print("-" * 80)

        samples = await conn.fetch("""
            SELECT
                m.item_id,
                m.item_name,
                m.base_price,
                m.restaurant_id,
                m.prep_time_minutes,
                m.calories,
                ARRAY_AGG(DISTINCT c.category_name) as categories
            FROM menu_items m
            LEFT JOIN item_categories ic ON m.item_id = ic.item_id
            LEFT JOIN categories c ON ic.category_id = c.category_id
            GROUP BY m.item_id, m.item_name, m.base_price, m.restaurant_id, m.prep_time_minutes, m.calories
            LIMIT 10
        """)

        for s in samples:
            print(f"\n  {s['item_id']} - {s['item_name']}")
            print(f"    Price: ₹{s['base_price']} | Prep: {s['prep_time_minutes']}min | Cal: {s['calories']}")
            print(f"    Restaurant: {s['restaurant_id']}")
            print(f"    Categories: {s['categories']}")

        # 6. TABLE ROW COUNTS
        print("\n[6] TABLE ROW COUNTS (ALL 18 TABLES)")
        print("-" * 80)

        tables = [
            "spice_levels", "cooking_methods", "serving_units", "meal_timings",
            "ingredients", "dietary_tags", "categories", "menu_items",
            "item_categories", "item_availability", "item_ingredients",
            "item_dietary_tags", "item_servings", "inventory", "item_variants",
            "item_recommendations", "user_preferences", "order_history"
        ]

        for table in tables:
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
            status = "✓" if count > 0 else "○ EMPTY"
            print(f"  {table:<30} {count:>6} rows  {status}")

        # 7. UNIQUE CONSTRAINT CHECK
        print("\n[7] DUPLICATE CHECK")
        print("-" * 80)

        # Check for duplicate item IDs
        dup_items = await conn.fetchval("""
            SELECT COUNT(*) FROM (
                SELECT item_id, COUNT(*)
                FROM menu_items
                GROUP BY item_id
                HAVING COUNT(*) > 1
            ) AS dups
        """)

        # Check for duplicate category IDs
        dup_cats = await conn.fetchval("""
            SELECT COUNT(*) FROM (
                SELECT category_id, COUNT(*)
                FROM categories
                GROUP BY category_id
                HAVING COUNT(*) > 1
            ) AS dups
        """)

        if dup_items > 0:
            print(f"  ❌ Found {dup_items} duplicate item IDs")
        else:
            print(f"  ✓ No duplicate item IDs")

        if dup_cats > 0:
            print(f"  ❌ Found {dup_cats} duplicate category IDs")
        else:
            print(f"  ✓ No duplicate category IDs")

        # SUMMARY
        print("\n" + "=" * 80)
        print("VERIFICATION SUMMARY")
        print("=" * 80)

        issues = []
        if wrong_item_ids:
            issues.append(f"Wrong item ID format: {len(wrong_item_ids)}")
        if wrong_cat_ids:
            issues.append(f"Wrong category ID format: {len(wrong_cat_ids)}")
        if items_no_rest > 0:
            issues.append(f"Items without restaurant: {items_no_rest}")
        if cats_no_rest > 0:
            issues.append(f"Categories without restaurant: {cats_no_rest}")
        if orphan_ic > 0:
            issues.append(f"Orphaned item-category links: {orphan_ic}")
        if orphan_ia > 0:
            issues.append(f"Orphaned availability records: {orphan_ia}")
        if orphan_inv > 0:
            issues.append(f"Orphaned inventory records: {orphan_inv}")
        if dup_items > 0:
            issues.append(f"Duplicate item IDs: {dup_items}")
        if dup_cats > 0:
            issues.append(f"Duplicate category IDs: {dup_cats}")

        if issues:
            print("❌ ISSUES FOUND:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("✓ ALL CHECKS PASSED - DATA QUALITY EXCELLENT!")

        print("=" * 80)

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(verify())

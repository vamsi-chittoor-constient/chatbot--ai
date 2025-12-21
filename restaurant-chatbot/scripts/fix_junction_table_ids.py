#!/usr/bin/env python3
"""
Fix Junction Table IDs - Update all foreign key references
============================================================
The menu_items and categories tables have new IDs, but junction tables
still have old IDs. This script creates a mapping and updates all references.
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

async def fix_ids():
    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        print("=" * 80)
        print("FIXING JUNCTION TABLE IDs")
        print("=" * 80)

        # Step 1: Build mapping from old to new IDs
        print("\n[STEP 1] Building ID mapping...")

        # The problem: menu_items now has MIT IDs, but we don't have the old->new mapping
        # We need to recreate the mapping by looking at what exists

        # Check if we have old IDs in junction tables
        old_item_sample = await conn.fetchval("""
            SELECT item_id FROM item_categories
            WHERE item_id NOT LIKE 'MIT%'
            LIMIT 1
        """)

        old_cat_sample = await conn.fetchval("""
            SELECT category_id FROM item_categories
            WHERE category_id NOT LIKE 'MCT%'
            LIMIT 1
        """)

        if not old_item_sample and not old_cat_sample:
            print("  ✓ All IDs are already in new format!")
            return

        print(f"  Found old item IDs: {old_item_sample is not None}")
        print(f"  Found old category IDs: {old_cat_sample is not None}")

        # Get all current menu items (new IDs)
        current_items = await conn.fetch("SELECT item_id, item_name FROM menu_items")
        current_cats = await conn.fetch("SELECT category_id, category_name FROM categories")

        print(f"  Current items in menu_items: {len(current_items)}")
        print(f"  Current categories in categories: {len(current_cats)}")

        # Get old IDs from junction tables
        old_item_ids = await conn.fetch("""
            SELECT DISTINCT item_id FROM item_categories
            WHERE item_id NOT LIKE 'MIT%'
        """)

        old_cat_ids = await conn.fetch("""
            SELECT DISTINCT category_id FROM item_categories
            WHERE category_id NOT LIKE 'MCT%'
        """)

        print(f"  Old item IDs found: {len(old_item_ids)}")
        print(f"  Old category IDs found: {len(old_cat_ids)}")

        # The issue is we lost the mapping!
        # The previous script updated menu_items but didn't save the old->new mapping
        # We need to regenerate items from scratch OR restore from backup

        print("\n  ❌ PROBLEM: The old->new ID mapping was lost!")
        print("  The menu_items table was updated but junction tables weren't.")
        print()
        print("  SOLUTION OPTIONS:")
        print("  1. Restore from backup and re-run migration properly")
        print("  2. Manually recreate the mapping (risky)")
        print("  3. Drop and reimport all data with correct IDs")
        print()
        print("  RECOMMENDED: Option 3 - Fresh import with proper ID handling")

        # Let's check if we can salvage by name matching
        print("\n[STEP 2] Attempting name-based matching...")

        # Try to match by name
        matches = 0
        mismatches = []

        # Build name->new_id map
        item_name_map = {item['item_name'].lower(): item['item_id'] for item in current_items}

        # Check a sample
        sample_old = await conn.fetch("""
            SELECT ic.item_id as old_id, mi.name as item_name
            FROM item_categories ic
            JOIN (
                SELECT item_id, item_name as name FROM (
                    SELECT 'ITEM_CURD_VADAI_001' as item_id, 'Curd Vadai' as item_name
                    UNION ALL
                    SELECT 'ITEM_IDLY_003', 'Idly'
                    UNION ALL
                    SELECT 'ITEM_KHICHDI_004', 'Khichdi'
                ) x
            ) mi ON ic.item_id = mi.item_id
            WHERE ic.item_id NOT LIKE 'MIT%'
            LIMIT 5
        """)

        print(f"  This approach won't work without the original data.")
        print()
        print("=" * 80)
        print("RECOMMENDATION")
        print("=" * 80)
        print("""
The cleanest solution is to:
1. Drop all junction table data
2. Re-import from CSV with the NEW IDs already in menu_items
3. This will ensure all foreign keys are consistent

The alternative is to restore menu_items to OLD IDs, then re-run
the migration properly with correct UPDATE order.

Which would you prefer?
        """)

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(fix_ids())

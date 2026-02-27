#!/usr/bin/env python3
"""
Re-import Junction Data with New IDs
=====================================
Clears junction tables and re-imports from CSV using the NEW MIT/MCT IDs
"""
import asyncio
import asyncpg
import csv
from pathlib import Path
import re

DB_CONFIG = {
    "host": "37.27.194.66",
    "port": 5430,
    "database": "restaurant_ai_dev",
    "user": "dev_explorer",
    "password": "restaurant24"
}

MEAL_TIMING_MAP = {
    "breakfast": "breakfast", "lunch": "lunch", "dinner": "dinner",
    "snack": "snack", "all day": "all_day", "all_day": "all_day", "": "all_day"
}

def parse_array_field(field: str):
    """Parse PostgreSQL array notation"""
    if not field or field == "{}":
        return []
    clean = field.strip("{}").strip()
    if not clean:
        return []
    items = [item.strip().strip('"').strip("'") for item in clean.split(",")]
    return [item for item in items if item]

async def reimport():
    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        print("=" * 80)
        print("RE-IMPORTING JUNCTION DATA WITH NEW IDs")
        print("=" * 80)

        # Step 1: Build name->ID mappings from current tables
        print("\n[STEP 1] Building name->ID mappings...")

        items = await conn.fetch("SELECT item_id, item_name FROM menu_items")
        categories = await conn.fetch("SELECT category_id, category_name FROM categories")

        item_name_to_id = {item['item_name'].lower().strip(): item['item_id'] for item in items}
        cat_name_to_id = {cat['category_name'].lower().strip(): cat['category_id'] for cat in categories}

        print(f"  ✓ Mapped {len(item_name_to_id)} items")
        print(f"  ✓ Mapped {len(cat_name_to_id)} categories")

        # Load lookups
        meal_timings = {row['timing_name']: row['timing_id']
                       for row in await conn.fetch("SELECT timing_id, timing_name FROM meal_timings")}
        dietary_tags = {row['tag_name']: row['tag_id']
                       for row in await conn.fetch("SELECT tag_id, tag_name FROM dietary_tags")}
        serving_units = {row['unit_name']: row['unit_id']
                        for row in await conn.fetch("SELECT unit_id, unit_name FROM serving_units")}

        # Step 2: Clear junction tables
        print("\n[STEP 2] Clearing junction tables...")

        await conn.execute("TRUNCATE item_categories CASCADE")
        await conn.execute("TRUNCATE item_availability CASCADE")
        await conn.execute("TRUNCATE item_dietary_tags CASCADE")
        await conn.execute("TRUNCATE item_servings CASCADE")
        await conn.execute("UPDATE inventory SET total_stock = 100, reserved_stock = 0")

        print("  ✓ Cleared all junction tables")

        # Step 3: Re-import from CSV
        print("\n[STEP 3] Re-importing from CSV...")

        csv_file = Path("db_migrations/menu_items_final - Full_Menu_Details.csv")
        seen_items = set()
        stats = {"processed": 0, "item_categories": 0, "item_availability": 0,
                "item_dietary_tags": 0, "item_servings": 0, "skipped": 0}

        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                stats["processed"] += 1
                food_name = row["name"].strip()

                # Deduplication
                if food_name.lower() in seen_items:
                    stats["skipped"] += 1
                    continue
                seen_items.add(food_name.lower())

                # Get new item_id from mapping
                item_id = item_name_to_id.get(food_name.lower())
                if not item_id:
                    print(f"  ⚠ Skipping {food_name} - not found in menu_items")
                    continue

                # Link categories
                cuisine_categories = parse_array_field(row["cuisine_category"])
                for idx, cat_name in enumerate(cuisine_categories):
                    cat_id = cat_name_to_id.get(cat_name.lower().strip())
                    if cat_id:
                        await conn.execute("""
                            INSERT INTO item_categories (item_id, category_id, is_primary, display_order)
                            VALUES ($1, $2, $3, $4)
                            ON CONFLICT DO NOTHING
                        """, item_id, cat_id, idx == 0, idx)
                        stats["item_categories"] += 1

                # Link meal timing
                timing_name = MEAL_TIMING_MAP.get(row["meal_timing"].lower().strip(), "all_day")
                timing_id = meal_timings.get(timing_name)
                if timing_id:
                    await conn.execute("""
                        INSERT INTO item_availability (item_id, timing_id, day_of_week, is_available)
                        VALUES ($1, $2, $3, $4)
                        ON CONFLICT DO NOTHING
                    """, item_id, timing_id, -1, True)
                    stats["item_availability"] += 1

                # Link dietary tags
                dietary_info = parse_array_field(row.get("dietary_info", ""))
                for tag_name_raw in dietary_info:
                    tag_name = tag_name_raw.lower().replace(" ", "_")
                    tag_id = dietary_tags.get(tag_name)
                    if tag_id:
                        await conn.execute("""
                            INSERT INTO item_dietary_tags (item_id, tag_id)
                            VALUES ($1, $2)
                            ON CONFLICT DO NOTHING
                        """, item_id, tag_id)
                        stats["item_dietary_tags"] += 1

                # Add serving size
                serving_size = row.get("serving_size", "").strip()
                unit_name = row.get("serving_unit", "").strip().lower()
                if serving_size and unit_name:
                    try:
                        from decimal import Decimal
                        size = Decimal(serving_size)
                        unit_id = serving_units.get(unit_name)
                        if unit_id:
                            await conn.execute("""
                                INSERT INTO item_servings (item_id, serving_size, unit_id)
                                VALUES ($1, $2, $3)
                                ON CONFLICT DO NOTHING
                            """, item_id, size, unit_id)
                            stats["item_servings"] += 1
                    except:
                        pass

                if stats["processed"] % 50 == 0:
                    print(f"    Progress: {stats['processed']}/{820} rows...")

        print("\n" + "=" * 80)
        print("RE-IMPORT COMPLETE!")
        print("=" * 80)
        print(f"  CSV rows processed: {stats['processed']}")
        print(f"  Items skipped (duplicates): {stats['skipped']}")
        print(f"  item_categories created: {stats['item_categories']}")
        print(f"  item_availability created: {stats['item_availability']}")
        print(f"  item_dietary_tags created: {stats['item_dietary_tags']}")
        print(f"  item_servings created: {stats['item_servings']}")
        print("=" * 80)

        # Verify
        print("\n[VERIFICATION]")
        sample = await conn.fetch("""
            SELECT
                m.item_id,
                m.item_name,
                ARRAY_AGG(DISTINCT c.category_name) as categories
            FROM menu_items m
            LEFT JOIN item_categories ic ON m.item_id = ic.item_id
            LEFT JOIN categories c ON ic.category_id = c.category_id
            GROUP BY m.item_id, m.item_name
            LIMIT 5
        """)

        for s in sample:
            print(f"  {s['item_id']} - {s['item_name']}")
            print(f"    Categories: {s['categories']}")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(reimport())

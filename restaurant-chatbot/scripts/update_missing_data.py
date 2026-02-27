#!/usr/bin/env python3
"""
Update existing menu items with missing CSV data
"""
import asyncio
import csv
import re
from pathlib import Path
import asyncpg

DB_CONFIG = {
    "host": "37.27.194.66",
    "port": 5430,
    "database": "restaurant_ai_dev",
    "user": "postgres",
    "password": "A24_rest!op"
}

def generate_item_id(food_name: str, counter: int) -> str:
    """Generate unique item_id from food name."""
    clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', food_name)
    clean_name = '_'.join(clean_name.upper().split())
    return f"ITEM_{clean_name}_{counter:03d}"

async def update_data():
    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        print("Updating menu items with missing CSV data...")

        # Build item_id mapping from CSV
        csv_file = Path("db_migrations/menu_items_final - Full_Menu_Details.csv")

        updated_count = 0
        skipped_count = 0
        item_counter = 1
        seen_items = set()

        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                food_name = row["name"].strip()

                # Skip duplicates (same deduplication logic as import)
                if food_name.lower() in seen_items:
                    continue

                seen_items.add(food_name.lower())

                # Generate same item_id as import
                item_id = generate_item_id(food_name, item_counter)
                item_counter += 1

                # Extract missing data
                prep_time = int(row["prep_time_minutes"]) if row["prep_time_minutes"] else None
                calories = int(row["calories"]) if row["calories"] else None
                is_seasonal = row["is_seasonal"].lower() in ["t", "true", "yes", "1"]

                # Update database
                result = await conn.execute("""
                    UPDATE menu_items
                    SET prep_time_minutes = $2,
                        calories = $3,
                        is_seasonal = $4
                    WHERE item_id = $1
                """, item_id, prep_time, calories, is_seasonal)

                if result == "UPDATE 1":
                    updated_count += 1
                    if updated_count % 50 == 0:
                        print(f"  Updated {updated_count} items...")
                else:
                    skipped_count += 1

        print(f"\n✓ Update complete!")
        print(f"  Items updated: {updated_count}")
        print(f"  Items skipped: {skipped_count}")

        # Verify
        sample = await conn.fetchrow("""
            SELECT item_name, prep_time_minutes, calories, is_seasonal
            FROM menu_items
            WHERE prep_time_minutes IS NOT NULL
            LIMIT 1
        """)

        if sample:
            print(f"\nSample updated item:")
            print(f"  {sample['item_name']}: {sample['prep_time_minutes']}min, {sample['calories']}cal, seasonal={sample['is_seasonal']}")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(update_data())

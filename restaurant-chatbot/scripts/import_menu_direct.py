#!/usr/bin/env python3
"""
Direct Menu Data Import - No App Dependencies
==============================================
Imports menu data using direct database connection without app initialization.
"""

import asyncio
import csv
import re
from pathlib import Path
from decimal import Decimal
from typing import Dict, List, Set, Optional

import asyncpg


# Database connection
DB_CONFIG = {
    "host": "37.27.194.66",
    "port": 5430,
    "database": "restaurant_ai_dev",
    "user": "postgres",
    "password": "A24_rest!op"
}


# Mapping dictionaries
SPICE_LEVEL_MAP = {
    "none": "none", "mild": "mild", "medium": "medium",
    "hot": "hot", "very hot": "very_hot", "extreme": "extreme", "": "none"
}

COOKING_METHOD_MAP = {
    "steamed": "steamed", "boiled": "boiled", "grilled": "grilled",
    "baked": "baked", "roasted": "roasted", "fried": "fried",
    "deep fried": "deep_fried", "deep-fried": "deep_fried",
    "sauteed": "sauteed", "sautéed": "sauteed",
    "stir fried": "stir_fried", "stir-fried": "stir_fried", "": "steamed"
}

MEAL_TIMING_MAP = {
    "breakfast": "breakfast", "lunch": "lunch", "dinner": "dinner",
    "snack": "snack", "all day": "all_day", "all_day": "all_day", "": "all_day"
}


def parse_array_field(field: str) -> List[str]:
    """Parse PostgreSQL array notation: {tiffin,snacks} → ['tiffin', 'snacks']"""
    if not field or field == "{}":
        return []
    clean = field.strip("{}").strip()
    if not clean:
        return []
    items = [item.strip().strip('"').strip("'") for item in clean.split(",")]
    return [item for item in items if item]


def generate_item_id(food_name: str, counter: int) -> str:
    """Generate unique item_id from food name."""
    clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', food_name)
    clean_name = '_'.join(clean_name.upper().split())
    return f"ITEM_{clean_name}_{counter:03d}"


def generate_category_id(category_name: str) -> str:
    """Generate category_id from name."""
    clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', category_name)
    clean_name = '_'.join(clean_name.upper().split())
    return f"CAT_{clean_name}"


def parse_price(price_str: str) -> Decimal:
    """Parse price from various formats."""
    if not price_str:
        return Decimal("0.00")
    clean = re.sub(r'[₹\s,]', '', price_str)
    try:
        return Decimal(clean)
    except:
        print(f"Warning: Failed to parse price: {price_str}")
        return Decimal("0.00")


def extract_serving_info(serving_size: str) -> tuple[Optional[Decimal], str]:
    """Extract serving size and unit from text."""
    if not serving_size:
        return None, "plate"
    match = re.match(r'(\d+\.?\d*)\s*([a-zA-Z]+)', serving_size.strip())
    if match:
        size = Decimal(match.group(1))
        unit = match.group(2).lower()
        return size, unit
    return Decimal("1"), "plate"


async def run_import(csv_path: str):
    """Run the full import process."""
    print(f"Connecting to database at {DB_CONFIG['host']}:{DB_CONFIG['port']}...")

    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        print("Loading reference data...")

        # Load lookups
        spice_levels = {row['spice_level_name']: row['spice_level_id']
                       for row in await conn.fetch("SELECT spice_level_id, spice_level_name FROM spice_levels")}
        cooking_methods = {row['method_name']: row['cooking_method_id']
                          for row in await conn.fetch("SELECT cooking_method_id, method_name FROM cooking_methods")}
        meal_timings = {row['timing_name']: row['timing_id']
                       for row in await conn.fetch("SELECT timing_id, timing_name FROM meal_timings")}
        serving_units = {row['unit_name']: row['unit_id']
                        for row in await conn.fetch("SELECT unit_id, unit_name FROM serving_units")}
        dietary_tags = {row['tag_name']: row['tag_id']
                       for row in await conn.fetch("SELECT tag_id, tag_name FROM dietary_tags")}

        print(f"Loaded {len(spice_levels)} spice levels, {len(cooking_methods)} cooking methods, "
              f"{len(meal_timings)} meal timings, {len(serving_units)} serving units, "
              f"{len(dietary_tags)} dietary tags")

        # Caches
        categories = {}
        ingredients = {}
        seen_items = set()
        item_counter = 1

        # Stats
        stats = {"rows_processed": 0, "items_created": 0, "items_skipped": 0,
                "categories_created": 0, "ingredients_created": 0}

        # Read CSV
        csv_file = Path(csv_path)
        if not csv_file.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        print(f"\nReading CSV from {csv_path}...")

        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                try:
                    stats["rows_processed"] += 1

                    food_name = row["Food_Name"].strip()

                    # Deduplication
                    if food_name.lower() in seen_items:
                        stats["items_skipped"] += 1
                        continue

                    seen_items.add(food_name.lower())

                    # Generate IDs
                    item_id = generate_item_id(food_name, item_counter)
                    item_counter += 1

                    # Parse fields
                    price = parse_price(row["Price_INR"])
                    is_available = row["Availability"].lower() in ["yes", "y", "true", "available"]
                    is_featured = float(row.get("Popularity_Score", "0") or "0") >= 8.0
                    description = row["Description"].strip() or None

                    # Get lookups
                    spice_name = SPICE_LEVEL_MAP.get(row["Spice_Level"].lower().strip(), "none")
                    spice_id = spice_levels.get(spice_name)

                    cooking_name = COOKING_METHOD_MAP.get(row["Cooking_Method"].lower().strip(), "steamed")
                    cooking_id = cooking_methods.get(cooking_name)

                    # Insert menu item
                    await conn.execute("""
                        INSERT INTO menu_items (
                            item_id, item_name, description, base_price,
                            spice_level_id, cooking_method_id,
                            is_available, is_featured
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """, item_id, food_name, description, price,
                        spice_id, cooking_id, is_available, is_featured)

                    stats["items_created"] += 1

                    # Link categories
                    cuisine_categories = parse_array_field(row["Cuisine_Category"])
                    for idx, cat_name in enumerate(cuisine_categories):
                        if cat_name not in categories:
                            cat_id = generate_category_id(cat_name)
                            await conn.execute("""
                                INSERT INTO categories (category_id, category_name, display_order)
                                VALUES ($1, $2, $3)
                            """, cat_id, cat_name, len(categories) + 1)
                            categories[cat_name] = cat_id
                            stats["categories_created"] += 1

                        await conn.execute("""
                            INSERT INTO item_categories (item_id, category_id, is_primary, display_order)
                            VALUES ($1, $2, $3, $4)
                        """, item_id, categories[cat_name], idx == 0, idx)

                    # Link meal timing
                    timing_name = MEAL_TIMING_MAP.get(row["Meal_Timing"].lower().strip(), "all_day")
                    timing_id = meal_timings.get(timing_name)

                    if timing_id:
                        await conn.execute("""
                            INSERT INTO item_availability (item_id, timing_id, day_of_week, is_available)
                            VALUES ($1, $2, $3, $4)
                        """, item_id, timing_id, -1, True)

                    # Link ingredients (first 10)
                    main_ingredients = [ing.strip() for ing in row["Main_Ingredients"].split(",") if ing.strip()]
                    for idx, ing_name in enumerate(main_ingredients[:10]):
                        ing_lower = ing_name.lower()
                        if ing_lower not in ingredients:
                            result = await conn.fetchrow("""
                                INSERT INTO ingredients (ingredient_name)
                                VALUES ($1)
                                RETURNING ingredient_id
                            """, ing_lower)
                            ingredients[ing_lower] = result['ingredient_id']
                            stats["ingredients_created"] += 1

                        await conn.execute("""
                            INSERT INTO item_ingredients (item_id, ingredient_id, is_primary)
                            VALUES ($1, $2, $3)
                        """, item_id, ingredients[ing_lower], idx == 0)

                    # Link dietary tags
                    dietary_tags_list = [tag.strip().lower().replace(" ", "_")
                                        for tag in row.get("Dietary_Tags", "").split(",") if tag.strip()]
                    for tag_name in dietary_tags_list:
                        tag_id = dietary_tags.get(tag_name)
                        if tag_id:
                            await conn.execute("""
                                INSERT INTO item_dietary_tags (item_id, tag_id)
                                VALUES ($1, $2)
                            """, item_id, tag_id)

                    # Add serving size
                    serving_size, unit_name = extract_serving_info(row.get("Serving_Size", ""))
                    unit_id = serving_units.get(unit_name)

                    if serving_size and unit_id:
                        await conn.execute("""
                            INSERT INTO item_servings (item_id, serving_size, unit_id)
                            VALUES ($1, $2, $3)
                        """, item_id, serving_size, unit_id)

                    # Initialize inventory
                    await conn.execute("""
                        INSERT INTO inventory (item_id, total_stock, reserved_stock, low_stock_threshold)
                        VALUES ($1, $2, $3, $4)
                    """, item_id, 100, 0, 10)

                    # Progress update
                    if stats["items_created"] % 50 == 0:
                        print(f"Progress: {stats['items_created']} items created...")

                except Exception as e:
                    print(f"Error importing row {stats['rows_processed']} ({row.get('Food_Name', 'unknown')}): {e}")
                    continue

        print("\n" + "=" * 60)
        print("IMPORT SUMMARY")
        print("=" * 60)
        print(f"Rows processed:       {stats['rows_processed']}")
        print(f"Items created:        {stats['items_created']}")
        print(f"Items skipped (dupe): {stats['items_skipped']}")
        print(f"Categories created:   {stats['categories_created']}")
        print(f"Ingredients created:  {stats['ingredients_created']}")
        print("=" * 60)
        print("\n✓ Data imported successfully!")
        print("\nNext step: Refresh materialized view:")
        print("  PGPASSWORD='A24_rest!op' psql -h 37.27.194.66 -p 5430 -U postgres -d restaurant_ai_dev -c 'SELECT refresh_menu_cache();'")

    finally:
        await conn.close()


if __name__ == "__main__":
    csv_path = "db_migrations/menu_items_final - Full_Menu_Details.csv"
    asyncio.run(run_import(csv_path))

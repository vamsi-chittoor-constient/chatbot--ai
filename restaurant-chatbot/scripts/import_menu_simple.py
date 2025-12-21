#!/usr/bin/env python3
"""
Simple Menu Data Import Script - Direct Model Import
==================================================
Imports menu data without initializing the full application.
"""

import asyncio
import csv
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Optional
from decimal import Decimal
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Direct model imports (bypassing package __init__ to avoid app initialization)
import sys
import importlib.util

# Import database manager
sys_path_backup = sys.path.copy()
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import db_manager

# Direct module file imports (not through package)
def load_module_from_file(module_name, file_path):
    """Load a Python module directly from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Load model modules directly
base_path = Path(__file__).parent.parent
models_path = base_path / "app" / "features" / "food_ordering" / "models"

lookup_mod = load_module_from_file("lookup_tables", models_path / "lookup_tables.py")
core_mod = load_module_from_file("core_tables", models_path / "core_tables.py")
junction_mod = load_module_from_file("junction_tables", models_path / "junction_tables.py")
operational_mod = load_module_from_file("operational_tables", models_path / "operational_tables.py")

# Extract classes
SpiceLevel = lookup_mod.SpiceLevel
CookingMethod = lookup_mod.CookingMethod
ServingUnit = lookup_mod.ServingUnit
MealTiming = lookup_mod.MealTiming
Ingredient = lookup_mod.Ingredient
DietaryTag = lookup_mod.DietaryTag

Category = core_mod.Category
MenuItem = core_mod.MenuItem
ItemCategory = core_mod.ItemCategory

ItemAvailability = junction_mod.ItemAvailability
ItemIngredient = junction_mod.ItemIngredient
ItemDietaryTag = junction_mod.ItemDietaryTag
ItemServing = junction_mod.ItemServing

Inventory = operational_mod.Inventory

# Simple logger
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==========================================================================
# UTILITY FUNCTIONS (copied from original script)
# ==========================================================================

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
        logger.warning(f"Failed to parse price: {price_str}")
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


# ==========================================================================
# IMPORT LOGIC
# ==========================================================================

async def run_import(csv_path: str):
    """Run the full import process."""
    logger.info(f"Starting menu import from {csv_path}")

    async with db_manager.get_session() as session:
        # Load reference data
        logger.info("Loading reference data...")

        # Load lookups
        spice_levels = {row.spice_level_name: row.spice_level_id
                       for row in (await session.execute(select(SpiceLevel))).scalars()}
        cooking_methods = {row.method_name: row.cooking_method_id
                          for row in (await session.execute(select(CookingMethod))).scalars()}
        meal_timings = {row.timing_name: row.timing_id
                       for row in (await session.execute(select(MealTiming))).scalars()}
        serving_units = {row.unit_name: row.unit_id
                        for row in (await session.execute(select(ServingUnit))).scalars()}
        dietary_tags = {row.tag_name: row.tag_id
                       for row in (await session.execute(select(DietaryTag))).scalars()}

        logger.info(f"Loaded {len(spice_levels)} spice levels, {len(cooking_methods)} cooking methods, "
                   f"{len(meal_timings)} meal timings, {len(serving_units)} serving units, "
                   f"{len(dietary_tags)} dietary tags")

        # Caches
        categories = {}
        ingredients = {}
        seen_items = set()
        item_counter = 1

        # Stats
        stats = {"rows_processed": 0, "items_created": 0, "items_skipped": 0}

        # Read CSV
        csv_file = Path(csv_path)
        if not csv_file.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

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

                    # Get lookups
                    spice_name = SPICE_LEVEL_MAP.get(row["Spice_Level"].lower().strip(), "none")
                    spice_id = spice_levels.get(spice_name)

                    cooking_name = COOKING_METHOD_MAP.get(row["Cooking_Method"].lower().strip(), "steamed")
                    cooking_id = cooking_methods.get(cooking_name)

                    # Create menu item
                    menu_item = MenuItem(
                        item_id=item_id,
                        item_name=food_name,
                        description=row["Description"].strip() or None,
                        base_price=price,
                        spice_level_id=spice_id,
                        cooking_method_id=cooking_id,
                        is_available=is_available,
                        is_featured=is_featured
                    )
                    session.add(menu_item)
                    await session.flush()

                    stats["items_created"] += 1

                    # Link categories
                    cuisine_categories = parse_array_field(row["Cuisine_Category"])
                    for idx, cat_name in enumerate(cuisine_categories):
                        if cat_name not in categories:
                            cat_id = generate_category_id(cat_name)
                            category = Category(
                                category_id=cat_id,
                                category_name=cat_name,
                                display_order=len(categories) + 1
                            )
                            session.add(category)
                            await session.flush()
                            categories[cat_name] = cat_id

                        item_category = ItemCategory(
                            item_id=item_id,
                            category_id=categories[cat_name],
                            is_primary=(idx == 0),
                            display_order=idx
                        )
                        session.add(item_category)

                    # Link meal timing
                    timing_name = MEAL_TIMING_MAP.get(row["Meal_Timing"].lower().strip(), "all_day")
                    timing_id = meal_timings.get(timing_name)

                    if timing_id:
                        item_avail = ItemAvailability(
                            item_id=item_id,
                            timing_id=timing_id,
                            day_of_week=-1,
                            is_available=True
                        )
                        session.add(item_avail)

                    # Link ingredients (first 10)
                    main_ingredients = [ing.strip() for ing in row["Main_Ingredients"].split(",") if ing.strip()]
                    for idx, ing_name in enumerate(main_ingredients[:10]):
                        ing_lower = ing_name.lower()
                        if ing_lower not in ingredients:
                            ingredient = Ingredient(ingredient_name=ing_lower)
                            session.add(ingredient)
                            await session.flush()
                            ingredients[ing_lower] = ingredient.ingredient_id

                        item_ingredient = ItemIngredient(
                            item_id=item_id,
                            ingredient_id=ingredients[ing_lower],
                            is_primary=(idx == 0)
                        )
                        session.add(item_ingredient)

                    # Link dietary tags
                    dietary_tags_list = [tag.strip().lower().replace(" ", "_")
                                        for tag in row.get("Dietary_Tags", "").split(",") if tag.strip()]
                    for tag_name in dietary_tags_list:
                        tag_id = dietary_tags.get(tag_name)
                        if tag_id:
                            item_dietary_tag = ItemDietaryTag(
                                item_id=item_id,
                                tag_id=tag_id
                            )
                            session.add(item_dietary_tag)

                    # Add serving size
                    serving_size, unit_name = extract_serving_info(row.get("Serving_Size", ""))
                    unit_id = serving_units.get(unit_name)

                    if serving_size and unit_id:
                        item_serving = ItemServing(
                            item_id=item_id,
                            serving_size=serving_size,
                            unit_id=unit_id
                        )
                        session.add(item_serving)

                    # Initialize inventory
                    inventory = Inventory(
                        item_id=item_id,
                        total_stock=100,
                        reserved_stock=0,
                        low_stock_threshold=10
                    )
                    session.add(inventory)

                    # Commit in batches of 50
                    if stats["items_created"] % 50 == 0:
                        await session.commit()
                        logger.info(f"Batch committed - {stats['items_created']} items created")

                except Exception as e:
                    logger.error(f"Failed to import row: {row.get('Food_Name', 'unknown')} - {e}")
                    await session.rollback()

        # Final commit
        await session.commit()

        logger.info(f"\n{'=' * 60}")
        logger.info(f"IMPORT SUMMARY")
        logger.info(f"{'=' * 60}")
        logger.info(f"Rows processed:       {stats['rows_processed']}")
        logger.info(f"Items created:        {stats['items_created']}")
        logger.info(f"Items skipped (dupe): {stats['items_skipped']}")
        logger.info(f"Categories created:   {len(categories)}")
        logger.info(f"Ingredients created:  {len(ingredients)}")
        logger.info(f"{'=' * 60}")
        logger.info("\n✓ Data imported successfully!")


if __name__ == "__main__":
    csv_path = "db_migrations/menu_items_final - Full_Menu_Details.csv"
    asyncio.run(run_import(csv_path))

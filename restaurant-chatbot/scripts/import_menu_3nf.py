#!/usr/bin/env python3
"""
Menu Data Import Script - 3NF Schema
====================================
Transforms denormalized CSV data into normalized 3NF schema.

Handles:
- Deduplication of items (820 rows → ~365 unique items)
- Multi-category mappings
- Meal timing assignments
- Ingredient parsing and allergen detection
- Dietary tag inference
- Spice level mapping
- Serving size extraction
- Search keyword generation
- Embedding generation (optional - can be done async)

Usage:
    python scripts/import_menu_3nf.py [--generate-embeddings] [--dry-run]
"""

import asyncio
import csv
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
from decimal import Decimal
from datetime import datetime
import structlog

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import db_manager
from app.features.food_ordering.models import (
    Category, MenuItem, ItemCategory, MealTiming, ItemAvailability,
    Ingredient, ItemIngredient, DietaryTag, ItemDietaryTag,
    SpiceLevel, CookingMethod, ServingUnit, ItemServing, Inventory
)
from app.core.config import settings

logger = structlog.get_logger("scripts.import_menu_3nf")


# ================================================================================
# CSV FIELD MAPPINGS
# ================================================================================

CSV_COLUMNS = {
    "Food_Name": 0,
    "Description": 1,
    "Cuisine_Category": 2,  # Array like {tiffin,snacks}
    "Meal_Timing": 3,       # breakfast/lunch/dinner/snack/all_day
    "Spice_Level": 4,
    "Main_Ingredients": 5,
    "Allergens": 6,         # Comma-separated
    "Dietary_Tags": 7,      # vegan, vegetarian, etc.
    "Cooking_Method": 8,
    "Customizations": 9,
    "Serving_Size": 10,
    "Nutritional_Info": 11,
    "Price_INR": 12,
    "Availability": 13,     # yes/no
    "Popularity_Score": 14,
    "Pairing_Suggestions": 15,
    "Keywords": 16,         # For search
    "AI_Description": 17,
    "Additional_Notes": 18
}


# ================================================================================
# DATA MAPPING DICTIONARIES
# ================================================================================

SPICE_LEVEL_MAP = {
    "none": "none",
    "mild": "mild",
    "medium": "medium",
    "hot": "hot",
    "very hot": "very_hot",
    "extreme": "extreme",
    "": "none"
}

COOKING_METHOD_MAP = {
    "steamed": "steamed",
    "boiled": "boiled",
    "grilled": "grilled",
    "baked": "baked",
    "roasted": "roasted",
    "fried": "fried",
    "deep fried": "deep_fried",
    "deep-fried": "deep_fried",
    "sauteed": "sauteed",
    "sautéed": "sauteed",
    "stir fried": "stir_fried",
    "stir-fried": "stir_fried",
    "": "steamed"  # Default to steamed if not specified
}

MEAL_TIMING_MAP = {
    "breakfast": "breakfast",
    "lunch": "lunch",
    "dinner": "dinner",
    "snack": "snack",
    "all day": "all_day",
    "all_day": "all_day",
    "": "all_day"
}

# Common allergens to detect
ALLERGEN_KEYWORDS = {
    "nuts": ["nuts", "peanut", "almond", "cashew", "walnut"],
    "dairy": ["milk", "cheese", "butter", "cream", "paneer", "ghee"],
    "gluten": ["wheat", "flour", "maida", "bread"],
    "shellfish": ["shrimp", "prawn", "crab", "lobster"],
    "soy": ["soy", "tofu"],
    "egg": ["egg"],
    "sesame": ["sesame", "til"]
}

# Dietary tags inference rules
DIETARY_INFERENCE = {
    "vegan": {
        "exclude": ["milk", "cheese", "butter", "cream", "paneer", "ghee", "egg", "fish", "chicken", "mutton", "meat"],
        "include": []
    },
    "vegetarian": {
        "exclude": ["fish", "chicken", "mutton", "meat", "prawn", "crab"],
        "include": []
    },
    "gluten_free": {
        "exclude": ["wheat", "flour", "maida", "bread", "roti", "naan", "paratha"],
        "include": []
    },
    "dairy_free": {
        "exclude": ["milk", "cheese", "butter", "cream", "paneer", "ghee"],
        "include": []
    }
}


# ================================================================================
# UTILITY FUNCTIONS
# ================================================================================

def parse_array_field(field: str) -> List[str]:
    """
    Parse PostgreSQL array notation: {tiffin,snacks} → ['tiffin', 'snacks']
    """
    if not field or field == "{}":
        return []

    # Remove braces and split by comma
    clean = field.strip("{}").strip()
    if not clean:
        return []

    items = [item.strip().strip('"').strip("'") for item in clean.split(",")]
    return [item for item in items if item]


def generate_item_id(food_name: str, counter: int) -> str:
    """
    Generate unique item_id from food name.

    Example: "Masala Dosa" → "ITEM_MASALA_DOSA_001"
    """
    # Clean and normalize name
    clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', food_name)
    clean_name = '_'.join(clean_name.upper().split())
    return f"ITEM_{clean_name}_{counter:03d}"


def generate_category_id(category_name: str) -> str:
    """
    Generate category_id from name.

    Example: "South Indian Tiffin" → "CAT_SOUTH_INDIAN_TIFFIN"
    """
    clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', category_name)
    clean_name = '_'.join(clean_name.upper().split())
    return f"CAT_{clean_name}"


def extract_serving_info(serving_size: str) -> tuple[Optional[Decimal], str]:
    """
    Extract serving size and unit from text.

    Examples:
        "2 pcs" → (2, "pcs")
        "250ml" → (250, "ml")
        "1 plate" → (1, "plate")
    """
    if not serving_size:
        return None, "plate"

    # Try to extract number and unit
    match = re.match(r'(\d+\.?\d*)\s*([a-zA-Z]+)', serving_size.strip())
    if match:
        size = Decimal(match.group(1))
        unit = match.group(2).lower()
        return size, unit

    # Default to 1 plate if can't parse
    return Decimal("1"), "plate"


def parse_price(price_str: str) -> Decimal:
    """
    Parse price from various formats.

    Examples:
        "₹50" → 50.00
        "50.00" → 50.00
        "50" → 50.00
    """
    if not price_str:
        return Decimal("0.00")

    # Remove currency symbols and whitespace
    clean = re.sub(r'[₹\s,]', '', price_str)

    try:
        return Decimal(clean)
    except:
        logger.warning("Failed to parse price", price_str=price_str)
        return Decimal("0.00")


def infer_dietary_tags(ingredients: List[str], allergens: List[str]) -> Set[str]:
    """
    Infer dietary tags based on ingredients and allergens.
    """
    tags = set()
    all_text = ' '.join(ingredients + allergens).lower()

    for tag_name, rules in DIETARY_INFERENCE.items():
        # Check exclusions
        has_exclusion = any(exclude in all_text for exclude in rules["exclude"])

        if not has_exclusion:
            tags.add(tag_name)

    return tags


def detect_allergens(ingredients: List[str], allergen_text: str) -> Dict[str, List[str]]:
    """
    Detect allergens from ingredients and allergen field.

    Returns dict: {"nuts": ["cashew", "almond"], "dairy": ["milk"]}
    """
    all_text = ' '.join(ingredients + [allergen_text]).lower()
    detected = {}

    for allergen_type, keywords in ALLERGEN_KEYWORDS.items():
        found = [kw for kw in keywords if kw in all_text]
        if found:
            detected[allergen_type] = found

    return detected


def generate_search_keywords(row: Dict[str, str]) -> List[str]:
    """
    Generate search keywords for text-based fallback search.
    """
    keywords = set()

    # Food name words
    food_name = row.get("Food_Name", "")
    keywords.update(food_name.lower().split())

    # Description words (filter common words)
    desc = row.get("Description", "")
    desc_words = [w for w in desc.lower().split() if len(w) > 3]
    keywords.update(desc_words[:5])  # Limit to 5 important words

    # Keywords field
    kw_field = row.get("Keywords", "")
    keywords.update(kw_field.lower().split(","))

    # Cuisine categories
    cuisines = parse_array_field(row.get("Cuisine_Category", ""))
    keywords.update([c.lower() for c in cuisines])

    # Clean and return
    return sorted([kw.strip() for kw in keywords if kw.strip() and len(kw.strip()) > 2])


# ================================================================================
# DATABASE OPERATIONS
# ================================================================================

class MenuImporter:
    """Handles menu data import with deduplication and normalization."""

    def __init__(self, session: AsyncSession, dry_run: bool = False):
        self.session = session
        self.dry_run = dry_run

        # Caches for lookups
        self.categories: Dict[str, int] = {}
        self.spice_levels: Dict[str, int] = {}
        self.cooking_methods: Dict[str, int] = {}
        self.meal_timings: Dict[str, int] = {}
        self.serving_units: Dict[str, int] = {}
        self.dietary_tags: Dict[str, int] = {}
        self.ingredients: Dict[str, int] = {}

        # Deduplication
        self.seen_items: Set[str] = set()
        self.item_counter = 1

        # Statistics
        self.stats = {
            "rows_processed": 0,
            "items_created": 0,
            "items_skipped_duplicate": 0,
            "categories_created": 0,
            "ingredients_created": 0
        }

    async def load_reference_data(self):
        """Load existing reference data into caches."""
        logger.info("Loading reference data from database...")

        # Load spice levels
        result = await self.session.execute(select(SpiceLevel))
        for row in result.scalars():
            self.spice_levels[row.spice_level_name] = row.spice_level_id

        # Load cooking methods
        result = await self.session.execute(select(CookingMethod))
        for row in result.scalars():
            self.cooking_methods[row.method_name] = row.cooking_method_id

        # Load meal timings
        result = await self.session.execute(select(MealTiming))
        for row in result.scalars():
            self.meal_timings[row.timing_name] = row.timing_id

        # Load serving units
        result = await self.session.execute(select(ServingUnit))
        for row in result.scalars():
            self.serving_units[row.unit_name] = row.unit_id

        # Load dietary tags
        result = await self.session.execute(select(DietaryTag))
        for row in result.scalars():
            self.dietary_tags[row.tag_name] = row.tag_id

        # Load existing categories
        result = await self.session.execute(select(Category))
        for row in result.scalars():
            self.categories[row.category_name] = row.category_id

        # Load existing ingredients
        result = await self.session.execute(select(Ingredient))
        for row in result.scalars():
            self.ingredients[row.ingredient_name.lower()] = row.ingredient_id

        logger.info(
            "Reference data loaded",
            spice_levels=len(self.spice_levels),
            cooking_methods=len(self.cooking_methods),
            meal_timings=len(self.meal_timings),
            serving_units=len(self.serving_units),
            dietary_tags=len(self.dietary_tags),
            existing_categories=len(self.categories),
            existing_ingredients=len(self.ingredients)
        )

    async def get_or_create_category(self, category_name: str) -> str:
        """Get or create category, return category_id."""
        if category_name in self.categories:
            return self.categories[category_name]

        category_id = generate_category_id(category_name)

        if not self.dry_run:
            category = Category(
                category_id=category_id,
                category_name=category_name,
                display_order=len(self.categories) + 1
            )
            self.session.add(category)
            await self.session.flush()

        self.categories[category_name] = category_id
        self.stats["categories_created"] += 1

        logger.debug("Created category", name=category_name, id=category_id)
        return category_id

    async def get_or_create_ingredient(
        self,
        ingredient_name: str,
        is_allergen: bool = False,
        allergen_type: Optional[str] = None
    ) -> int:
        """Get or create ingredient, return ingredient_id."""
        name_lower = ingredient_name.lower().strip()

        if name_lower in self.ingredients:
            return self.ingredients[name_lower]

        if not self.dry_run:
            ingredient = Ingredient(
                ingredient_name=name_lower,
                is_allergen=is_allergen,
                allergen_type=allergen_type
            )
            self.session.add(ingredient)
            await self.session.flush()
            ingredient_id = ingredient.ingredient_id
        else:
            ingredient_id = len(self.ingredients) + 1

        self.ingredients[name_lower] = ingredient_id
        self.stats["ingredients_created"] += 1

        return ingredient_id

    async def import_row(self, row: Dict[str, str]):
        """Import a single CSV row into normalized tables."""
        self.stats["rows_processed"] += 1

        # Extract core fields
        food_name = row["Food_Name"].strip()
        description = row["Description"].strip()

        # Deduplication: Skip if we've seen this food name
        if food_name.lower() in self.seen_items:
            self.stats["items_skipped_duplicate"] += 1
            logger.debug("Skipping duplicate item", food_name=food_name)
            return

        self.seen_items.add(food_name.lower())

        # Generate item_id
        item_id = generate_item_id(food_name, self.item_counter)
        self.item_counter += 1

        # Parse fields
        price = parse_price(row["Price_INR"])
        is_available = row["Availability"].lower() in ["yes", "y", "true", "available"]
        is_featured = float(row.get("Popularity_Score", "0") or "0") >= 8.0

        # Get spice level
        spice_level_name = SPICE_LEVEL_MAP.get(row["Spice_Level"].lower().strip(), "none")
        spice_level_id = self.spice_levels.get(spice_level_name)

        # Get cooking method
        cooking_method_name = COOKING_METHOD_MAP.get(row["Cooking_Method"].lower().strip(), "steamed")
        cooking_method_id = self.cooking_methods.get(cooking_method_name)

        # Generate search keywords
        search_keywords = generate_search_keywords(row)

        # Create menu item
        if not self.dry_run:
            menu_item = MenuItem(
                item_id=item_id,
                item_name=food_name,
                description=description or None,
                base_price=price,
                spice_level_id=spice_level_id,
                cooking_method_id=cooking_method_id,
                search_keywords=search_keywords,
                is_available=is_available,
                is_featured=is_featured,
                embedding=None  # Generated later via async job
            )
            self.session.add(menu_item)
            await self.session.flush()

        self.stats["items_created"] += 1

        # Link to categories (many-to-many)
        cuisine_categories = parse_array_field(row["Cuisine_Category"])
        for idx, category_name in enumerate(cuisine_categories):
            category_id = await self.get_or_create_category(category_name)

            if not self.dry_run:
                item_category = ItemCategory(
                    item_id=item_id,
                    category_id=category_id,
                    is_primary=(idx == 0),  # First category is primary
                    display_order=idx
                )
                self.session.add(item_category)

        # Link to meal timings
        meal_timing_name = MEAL_TIMING_MAP.get(row["Meal_Timing"].lower().strip(), "all_day")
        timing_id = self.meal_timings.get(meal_timing_name)

        if timing_id and not self.dry_run:
            item_avail = ItemAvailability(
                item_id=item_id,
                timing_id=timing_id,
                day_of_week=None,  # Available all days
                is_available=True
            )
            self.session.add(item_avail)

        # Parse and link ingredients
        main_ingredients = [ing.strip() for ing in row["Main_Ingredients"].split(",") if ing.strip()]
        allergen_text = row.get("Allergens", "")
        detected_allergens = detect_allergens(main_ingredients, allergen_text)

        for idx, ingredient_name in enumerate(main_ingredients[:10]):  # Limit to 10
            # Check if this ingredient is an allergen
            is_allergen = False
            allergen_type = None
            for allrg_type, keywords in detected_allergens.items():
                if any(kw in ingredient_name.lower() for kw in keywords):
                    is_allergen = True
                    allergen_type = allrg_type
                    break

            ingredient_id = await self.get_or_create_ingredient(
                ingredient_name,
                is_allergen=is_allergen,
                allergen_type=allergen_type
            )

            if not self.dry_run:
                item_ingredient = ItemIngredient(
                    item_id=item_id,
                    ingredient_id=ingredient_id,
                    is_primary=(idx == 0)  # First ingredient is primary
                )
                self.session.add(item_ingredient)

        # Infer and link dietary tags
        dietary_tags_explicit = [tag.strip().lower().replace(" ", "_") for tag in row.get("Dietary_Tags", "").split(",") if tag.strip()]
        dietary_tags_inferred = infer_dietary_tags(main_ingredients, [allergen_text])
        all_dietary_tags = set(dietary_tags_explicit) | dietary_tags_inferred

        for tag_name in all_dietary_tags:
            tag_id = self.dietary_tags.get(tag_name)
            if tag_id and not self.dry_run:
                item_dietary_tag = ItemDietaryTag(
                    item_id=item_id,
                    tag_id=tag_id
                )
                self.session.add(item_dietary_tag)

        # Add serving size
        serving_size, unit_name = extract_serving_info(row.get("Serving_Size", ""))
        unit_id = self.serving_units.get(unit_name)

        if serving_size and unit_id and not self.dry_run:
            item_serving = ItemServing(
                item_id=item_id,
                serving_size=serving_size,
                unit_id=unit_id
            )
            self.session.add(item_serving)

        # Initialize inventory
        if not self.dry_run:
            inventory = Inventory(
                item_id=item_id,
                total_stock=100,  # Default stock
                reserved_stock=0,
                low_stock_threshold=10
            )
            self.session.add(inventory)

        logger.debug(
            "Imported item",
            item_id=item_id,
            food_name=food_name,
            categories=len(cuisine_categories),
            ingredients=len(main_ingredients)
        )

    async def run_import(self, csv_path: str):
        """Run the full import process."""
        logger.info("Starting menu import", csv_path=csv_path, dry_run=self.dry_run)

        # Load reference data
        await self.load_reference_data()

        # Read and process CSV
        csv_file = Path(csv_path)
        if not csv_file.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                try:
                    await self.import_row(row)

                    # Commit in batches of 50
                    if self.stats["items_created"] % 50 == 0 and not self.dry_run:
                        await self.session.commit()
                        logger.info("Batch committed", items_created=self.stats["items_created"])

                except Exception as e:
                    logger.error(
                        "Failed to import row",
                        food_name=row.get("Food_Name", "unknown"),
                        error=str(e),
                        exc_info=True
                    )
                    if not self.dry_run:
                        await self.session.rollback()

        # Final commit
        if not self.dry_run:
            await self.session.commit()

        logger.info("Import completed", **self.stats)

        return self.stats


# ================================================================================
# MAIN ENTRY POINT
# ================================================================================

async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Import menu data into 3NF schema")
    parser.add_argument(
        "--csv",
        default="db_migrations/menu_items_final - Full_Menu_Details.csv",
        help="Path to CSV file"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without writing to database"
    )
    args = parser.parse_args()

    logger.info("Menu import starting", csv_path=args.csv, dry_run=args.dry_run)

    try:
        async with db_manager.get_session() as session:
            importer = MenuImporter(session, dry_run=args.dry_run)
            stats = await importer.run_import(args.csv)

            print("\n" + "=" * 60)
            print("IMPORT SUMMARY")
            print("=" * 60)
            print(f"Rows processed:        {stats['rows_processed']}")
            print(f"Items created:         {stats['items_created']}")
            print(f"Items skipped (dupe):  {stats['items_skipped_duplicate']}")
            print(f"Categories created:    {stats['categories_created']}")
            print(f"Ingredients created:   {stats['ingredients_created']}")
            print("=" * 60)

            if not args.dry_run:
                print("\n✓ Data imported successfully!")
                print("\nNext steps:")
                print("1. Refresh materialized view:")
                print("   psql -c 'SELECT refresh_menu_cache();'")
                print("2. Generate embeddings (async):")
                print("   python scripts/generate_embeddings.py")

    except Exception as e:
        logger.error("Import failed", error=str(e), exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

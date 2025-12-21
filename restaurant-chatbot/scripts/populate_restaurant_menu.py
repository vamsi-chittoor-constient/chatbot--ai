"""
Restaurant Menu Population Script
==================================
Populates the database with realistic Indian restaurant menu data.

Creates:
- MenuSections (Veg, Non-Veg)
- MenuCategories (Breakfast, Main Course, Rice Dishes, Beverages, Desserts)
- MenuItem (50+ realistic Indian dishes)
- DietaryTypes (Vegetarian, Vegan, Gluten-Free, Dairy-Free)
- Allergens (Dairy, Nuts, Gluten, Soy, Eggs)
- All required mappings
"""

import asyncio
import sys
import io
from pathlib import Path
from decimal import Decimal
from typing import Dict, List, Any
from uuid import UUID, uuid4
import structlog

# Fix encoding issues on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_db_session, db_manager
from app.shared.models.base import Base
from app.shared.models.restaurant import Restaurant
from app.features.food_ordering.models.menu_section import MenuSection
from app.features.food_ordering.models.menu_category import MenuCategory
from app.features.food_ordering.models.menu_item import MenuItem
from app.features.food_ordering.models.menu_item_category_mapping import MenuItemCategoryMapping
from app.features.food_ordering.models.dietary_type import DietaryType
from app.features.food_ordering.models.allergen import Allergen
from app.features.food_ordering.models.menu_item_dietary_mapping import MenuItemDietaryMapping
from app.features.food_ordering.models.menu_item_allergen_mapping import MenuItemAllergenMapping
from sqlalchemy import select, delete

logger = structlog.get_logger("populate_menu")


# ============================================================================
# MENU DATA DEFINITIONS
# ============================================================================

DIETARY_TYPES = [
    {"name": "Vegetarian", "label": "VEG", "description": "Contains no meat, fish, or poultry"},
    {"name": "Vegan", "label": "VEGAN", "description": "Contains no animal products"},
    {"name": "Gluten-Free", "label": "GF", "description": "Contains no wheat, barley, or rye"},
    {"name": "Dairy-Free", "label": "DF", "description": "Contains no milk or dairy products"},
    {"name": "Non-Vegetarian", "label": "NON-VEG", "description": "Contains meat, fish, or poultry"}
]

ALLERGENS = [
    {"name": "Dairy", "description": "Contains milk, butter, ghee, paneer, or other dairy products"},
    {"name": "Nuts", "description": "Contains cashews, almonds, pistachios, or other tree nuts"},
    {"name": "Gluten", "description": "Contains wheat, barley, rye, or their derivatives"},
    {"name": "Soy", "description": "Contains soy products"},
    {"name": "Eggs", "description": "Contains eggs or egg products"},
    {"name": "Shellfish", "description": "Contains shrimp, crab, lobster, or other shellfish"},
    {"name": "Fish", "description": "Contains fish or fish products"}
]

SECTIONS = [
    {"name": "Vegetarian", "description": "Pure vegetarian dishes", "rank": 1},
    {"name": "Non-Vegetarian", "description": "Dishes with meat, fish, or poultry", "rank": 2}
]

# Categories will be created under sections
CATEGORIES = [
    {"section": "Vegetarian", "name": "South Indian Breakfast", "description": "Traditional South Indian breakfast items", "rank": 1},
    {"section": "Vegetarian", "name": "North Indian Breakfast", "description": "Traditional North Indian breakfast items", "rank": 2},
    {"section": "Vegetarian", "name": "Vegetarian Main Course", "description": "Vegetarian curries and gravies", "rank": 3},
    {"section": "Vegetarian", "name": "Rice & Biryani", "description": "Rice dishes and vegetarian biryani", "rank": 4},
    {"section": "Vegetarian", "name": "Breads", "description": "Indian breads and rotis", "rank": 5},
    {"section": "Vegetarian", "name": "Snacks & Starters", "description": "Vegetarian appetizers", "rank": 6},
    {"section": "Non-Vegetarian", "name": "Non-Veg Main Course", "description": "Chicken, mutton, and seafood curries", "rank": 7},
    {"section": "Non-Vegetarian", "name": "Non-Veg Biryani", "description": "Chicken, mutton, and seafood biryani", "rank": 8},
    {"section": "Non-Vegetarian", "name": "Tandoori & Kebabs", "description": "Grilled and tandoor-cooked items", "rank": 9},
    {"section": "Vegetarian", "name": "Beverages", "description": "Hot and cold beverages", "rank": 10},
    {"section": "Vegetarian", "name": "Desserts", "description": "Indian sweets and desserts", "rank": 11}
]

# Comprehensive menu items
MENU_ITEMS = [
    # SOUTH INDIAN BREAKFAST
    {
        "name": "Masala Dosa",
        "category": "South Indian Breakfast",
        "description": "Crispy rice crepe filled with spiced potato masala, served with sambar and chutneys",
        "price": Decimal("120.00"),
        "spice_level": "mild",
        "dietary": ["Vegetarian", "Vegan"],
        "allergens": [],
        "calories": 350,
        "serving_unit": "1 pc",
        "is_recommended": True,
        "preparation_time": 15
    },
    {
        "name": "Plain Dosa",
        "category": "South Indian Breakfast",
        "description": "Traditional crispy rice crepe served with sambar and chutneys",
        "price": Decimal("80.00"),
        "spice_level": "mild",
        "dietary": ["Vegetarian", "Vegan", "Gluten-Free"],
        "allergens": [],
        "calories": 250,
        "serving_unit": "1 pc",
        "preparation_time": 12
    },
    {
        "name": "Idli Sambar",
        "category": "South Indian Breakfast",
        "description": "Steamed rice cakes (3 pcs) served with sambar and chutneys",
        "price": Decimal("70.00"),
        "spice_level": "mild",
        "dietary": ["Vegetarian", "Vegan", "Gluten-Free"],
        "allergens": [],
        "calories": 200,
        "serving_unit": "3 pcs",
        "preparation_time": 10
    },
    {
        "name": "Medu Vada",
        "category": "South Indian Breakfast",
        "description": "Crispy lentil donuts (3 pcs) served with sambar and chutneys",
        "price": Decimal("75.00"),
        "spice_level": "mild",
        "dietary": ["Vegetarian", "Vegan", "Gluten-Free"],
        "allergens": [],
        "calories": 280,
        "serving_unit": "3 pcs",
        "preparation_time": 15
    },
    {
        "name": "Rava Dosa",
        "category": "South Indian Breakfast",
        "description": "Thin crispy semolina crepe with onions and green chilies",
        "price": Decimal("95.00"),
        "spice_level": "medium",
        "dietary": ["Vegetarian"],
        "allergens": ["Gluten"],
        "calories": 300,
        "serving_unit": "1 pc",
        "preparation_time": 15
    },
    {
        "name": "Uttapam",
        "category": "South Indian Breakfast",
        "description": "Thick rice pancake topped with onions, tomatoes, and green chilies",
        "price": Decimal("90.00"),
        "spice_level": "mild",
        "dietary": ["Vegetarian", "Vegan", "Gluten-Free"],
        "allergens": [],
        "calories": 320,
        "serving_unit": "1 pc",
        "preparation_time": 15
    },

    # NORTH INDIAN BREAKFAST
    {
        "name": "Poha",
        "category": "North Indian Breakfast",
        "description": "Flattened rice cooked with mustard seeds, curry leaves, peanuts, and turmeric",
        "price": Decimal("65.00"),
        "spice_level": "mild",
        "dietary": ["Vegetarian", "Vegan", "Gluten-Free"],
        "allergens": ["Nuts"],
        "calories": 250,
        "serving_unit": "1 plate",
        "preparation_time": 12
    },
    {
        "name": "Upma",
        "category": "North Indian Breakfast",
        "description": "Savory semolina porridge with vegetables and spices",
        "price": Decimal("60.00"),
        "spice_level": "mild",
        "dietary": ["Vegetarian", "Vegan"],
        "allergens": ["Gluten"],
        "calories": 220,
        "serving_unit": "1 plate",
        "preparation_time": 12
    },
    {
        "name": "Paratha with Curd",
        "category": "North Indian Breakfast",
        "description": "Whole wheat flatbread served with fresh yogurt and pickle",
        "price": Decimal("75.00"),
        "spice_level": "mild",
        "dietary": ["Vegetarian"],
        "allergens": ["Dairy", "Gluten"],
        "calories": 380,
        "serving_unit": "2 pcs",
        "preparation_time": 15
    },

    # VEGETARIAN MAIN COURSE
    {
        "name": "Paneer Butter Masala",
        "category": "Vegetarian Main Course",
        "description": "Cottage cheese cubes in rich tomato and butter gravy",
        "price": Decimal("195.00"),
        "spice_level": "mild",
        "dietary": ["Vegetarian"],
        "allergens": ["Dairy"],
        "calories": 450,
        "serving_unit": "1 bowl",
        "is_recommended": True,
        "preparation_time": 20
    },
    {
        "name": "Palak Paneer",
        "category": "Vegetarian Main Course",
        "description": "Cottage cheese in creamy spinach gravy",
        "price": Decimal("185.00"),
        "spice_level": "mild",
        "dietary": ["Vegetarian"],
        "allergens": ["Dairy"],
        "calories": 380,
        "serving_unit": "1 bowl",
        "preparation_time": 20
    },
    {
        "name": "Dal Tadka",
        "category": "Vegetarian Main Course",
        "description": "Yellow lentils tempered with garlic, cumin, and ghee",
        "price": Decimal("150.00"),
        "spice_level": "mild",
        "dietary": ["Vegetarian"],
        "allergens": ["Dairy"],
        "calories": 280,
        "serving_unit": "1 bowl",
        "preparation_time": 25
    },
    {
        "name": "Dal Makhani",
        "category": "Vegetarian Main Course",
        "description": "Black lentils slow-cooked with butter and cream",
        "price": Decimal("175.00"),
        "spice_level": "mild",
        "dietary": ["Vegetarian"],
        "allergens": ["Dairy"],
        "calories": 420,
        "serving_unit": "1 bowl",
        "is_recommended": True,
        "preparation_time": 30
    },
    {
        "name": "Chana Masala",
        "category": "Vegetarian Main Course",
        "description": "Chickpeas in spiced tomato-onion gravy",
        "price": Decimal("155.00"),
        "spice_level": "medium",
        "dietary": ["Vegetarian", "Vegan"],
        "allergens": [],
        "calories": 320,
        "serving_unit": "1 bowl",
        "preparation_time": 20
    },
    {
        "name": "Aloo Gobi",
        "category": "Vegetarian Main Course",
        "description": "Potato and cauliflower curry with aromatic spices",
        "price": Decimal("145.00"),
        "spice_level": "medium",
        "dietary": ["Vegetarian", "Vegan", "Gluten-Free"],
        "allergens": [],
        "calories": 260,
        "serving_unit": "1 bowl",
        "preparation_time": 20
    },
    {
        "name": "Baingan Bharta",
        "category": "Vegetarian Main Course",
        "description": "Smoky roasted eggplant mashed with spices and tomatoes",
        "price": Decimal("165.00"),
        "spice_level": "medium",
        "dietary": ["Vegetarian", "Vegan"],
        "allergens": [],
        "calories": 240,
        "serving_unit": "1 bowl",
        "preparation_time": 25
    },

    # RICE & BIRYANI (VEG)
    {
        "name": "Vegetable Biryani",
        "category": "Rice & Biryani",
        "description": "Fragrant basmati rice cooked with mixed vegetables and aromatic spices",
        "price": Decimal("180.00"),
        "spice_level": "medium",
        "dietary": ["Vegetarian"],
        "allergens": ["Dairy"],
        "calories": 450,
        "serving_unit": "1 plate",
        "is_recommended": True,
        "preparation_time": 30
    },
    {
        "name": "Paneer Biryani",
        "category": "Rice & Biryani",
        "description": "Aromatic rice layered with marinated paneer and spices",
        "price": Decimal("210.00"),
        "spice_level": "medium",
        "dietary": ["Vegetarian"],
        "allergens": ["Dairy", "Nuts"],
        "calories": 520,
        "serving_unit": "1 plate",
        "preparation_time": 35
    },
    {
        "name": "Jeera Rice",
        "category": "Rice & Biryani",
        "description": "Basmati rice tempered with cumin seeds and ghee",
        "price": Decimal("120.00"),
        "spice_level": "none",
        "dietary": ["Vegetarian", "Gluten-Free"],
        "allergens": ["Dairy"],
        "calories": 280,
        "serving_unit": "1 plate",
        "preparation_time": 15
    },
    {
        "name": "Curd Rice",
        "category": "Rice & Biryani",
        "description": "Cooked rice mixed with yogurt, tempered with mustard seeds and curry leaves",
        "price": Decimal("90.00"),
        "spice_level": "none",
        "dietary": ["Vegetarian", "Gluten-Free"],
        "allergens": ["Dairy"],
        "calories": 250,
        "serving_unit": "1 plate",
        "preparation_time": 10
    },

    # BREADS
    {
        "name": "Butter Naan",
        "category": "Breads",
        "description": "Soft leavened bread brushed with butter",
        "price": Decimal("50.00"),
        "spice_level": "none",
        "dietary": ["Vegetarian"],
        "allergens": ["Dairy", "Gluten"],
        "calories": 260,
        "serving_unit": "1 pc",
        "is_recommended": True,
        "preparation_time": 10
    },
    {
        "name": "Garlic Naan",
        "category": "Breads",
        "description": "Naan topped with garlic and fresh coriander",
        "price": Decimal("60.00"),
        "spice_level": "none",
        "dietary": ["Vegetarian"],
        "allergens": ["Dairy", "Gluten"],
        "calories": 280,
        "serving_unit": "1 pc",
        "preparation_time": 10
    },
    {
        "name": "Tandoori Roti",
        "category": "Breads",
        "description": "Whole wheat bread cooked in tandoor",
        "price": Decimal("35.00"),
        "spice_level": "none",
        "dietary": ["Vegetarian", "Vegan"],
        "allergens": ["Gluten"],
        "calories": 120,
        "serving_unit": "1 pc",
        "preparation_time": 8
    },
    {
        "name": "Laccha Paratha",
        "category": "Breads",
        "description": "Multi-layered whole wheat flatbread",
        "price": Decimal("55.00"),
        "spice_level": "none",
        "dietary": ["Vegetarian"],
        "allergens": ["Dairy", "Gluten"],
        "calories": 320,
        "serving_unit": "1 pc",
        "preparation_time": 12
    },

    # SNACKS & STARTERS (VEG)
    {
        "name": "Samosa",
        "category": "Snacks & Starters",
        "description": "Crispy pastry filled with spiced potatoes and peas (2 pcs)",
        "price": Decimal("50.00"),
        "spice_level": "mild",
        "dietary": ["Vegetarian", "Vegan"],
        "allergens": ["Gluten"],
        "calories": 280,
        "serving_unit": "2 pcs",
        "is_recommended": True,
        "preparation_time": 12
    },
    {
        "name": "Paneer Tikka",
        "category": "Snacks & Starters",
        "description": "Marinated cottage cheese cubes grilled in tandoor",
        "price": Decimal("185.00"),
        "spice_level": "medium",
        "dietary": ["Vegetarian"],
        "allergens": ["Dairy"],
        "calories": 320,
        "serving_unit": "6 pcs",
        "preparation_time": 20
    },
    {
        "name": "Gobi Manchurian",
        "category": "Snacks & Starters",
        "description": "Crispy cauliflower florets in spicy Indo-Chinese sauce",
        "price": Decimal("150.00"),
        "spice_level": "hot",
        "dietary": ["Vegetarian"],
        "allergens": ["Gluten", "Soy"],
        "calories": 340,
        "serving_unit": "1 bowl",
        "preparation_time": 18
    },

    # NON-VEG MAIN COURSE
    {
        "name": "Butter Chicken",
        "category": "Non-Veg Main Course",
        "description": "Tender chicken pieces in rich tomato and butter gravy",
        "price": Decimal("235.00"),
        "spice_level": "mild",
        "dietary": ["Non-Vegetarian"],
        "allergens": ["Dairy"],
        "calories": 520,
        "serving_unit": "1 bowl",
        "is_recommended": True,
        "is_favorite": True,
        "preparation_time": 25
    },
    {
        "name": "Chicken Tikka Masala",
        "category": "Non-Veg Main Course",
        "description": "Grilled chicken chunks in creamy tomato gravy",
        "price": Decimal("245.00"),
        "spice_level": "medium",
        "dietary": ["Non-Vegetarian"],
        "allergens": ["Dairy"],
        "calories": 480,
        "serving_unit": "1 bowl",
        "is_recommended": True,
        "preparation_time": 25
    },
    {
        "name": "Kadai Chicken",
        "category": "Non-Veg Main Course",
        "description": "Chicken cooked with bell peppers, onions, and aromatic spices in kadai",
        "price": Decimal("225.00"),
        "spice_level": "hot",
        "dietary": ["Non-Vegetarian"],
        "allergens": [],
        "calories": 420,
        "serving_unit": "1 bowl",
        "preparation_time": 25
    },
    {
        "name": "Chicken Curry",
        "category": "Non-Veg Main Course",
        "description": "Traditional chicken curry with aromatic spices",
        "price": Decimal("210.00"),
        "spice_level": "medium",
        "dietary": ["Non-Vegetarian"],
        "allergens": [],
        "calories": 380,
        "serving_unit": "1 bowl",
        "preparation_time": 25
    },
    {
        "name": "Mutton Rogan Josh",
        "category": "Non-Veg Main Course",
        "description": "Tender mutton in aromatic Kashmiri-style curry",
        "price": Decimal("295.00"),
        "spice_level": "medium",
        "dietary": ["Non-Vegetarian"],
        "allergens": ["Dairy"],
        "calories": 550,
        "serving_unit": "1 bowl",
        "preparation_time": 45
    },
    {
        "name": "Fish Curry",
        "category": "Non-Veg Main Course",
        "description": "Fresh fish cooked in tangy coconut-based curry",
        "price": Decimal("250.00"),
        "spice_level": "hot",
        "dietary": ["Non-Vegetarian"],
        "allergens": ["Fish"],
        "calories": 340,
        "serving_unit": "1 bowl",
        "preparation_time": 30
    },
    {
        "name": "Prawn Masala",
        "category": "Non-Veg Main Course",
        "description": "Juicy prawns in spicy tomato-onion gravy",
        "price": Decimal("320.00"),
        "spice_level": "hot",
        "dietary": ["Non-Vegetarian"],
        "allergens": ["Shellfish"],
        "calories": 380,
        "serving_unit": "1 bowl",
        "preparation_time": 25
    },

    # NON-VEG BIRYANI
    {
        "name": "Chicken Biryani",
        "category": "Non-Veg Biryani",
        "description": "Fragrant basmati rice layered with marinated chicken and aromatic spices",
        "price": Decimal("220.00"),
        "spice_level": "medium",
        "dietary": ["Non-Vegetarian"],
        "allergens": ["Dairy", "Nuts"],
        "calories": 580,
        "serving_unit": "1 plate",
        "is_recommended": True,
        "is_favorite": True,
        "preparation_time": 40
    },
    {
        "name": "Mutton Biryani",
        "category": "Non-Veg Biryani",
        "description": "Aromatic rice layered with tender mutton pieces and whole spices",
        "price": Decimal("280.00"),
        "spice_level": "medium",
        "dietary": ["Non-Vegetarian"],
        "allergens": ["Dairy", "Nuts"],
        "calories": 650,
        "serving_unit": "1 plate",
        "is_recommended": True,
        "preparation_time": 50
    },
    {
        "name": "Egg Biryani",
        "category": "Non-Veg Biryani",
        "description": "Flavorful rice cooked with boiled eggs and spices",
        "price": Decimal("160.00"),
        "spice_level": "medium",
        "dietary": ["Non-Vegetarian"],
        "allergens": ["Eggs", "Dairy"],
        "calories": 480,
        "serving_unit": "1 plate",
        "preparation_time": 30
    },

    # TANDOORI & KEBABS
    {
        "name": "Tandoori Chicken Half",
        "category": "Tandoori & Kebabs",
        "description": "Half chicken marinated in yogurt and spices, grilled in tandoor",
        "price": Decimal("280.00"),
        "spice_level": "medium",
        "dietary": ["Non-Vegetarian"],
        "allergens": ["Dairy"],
        "calories": 450,
        "serving_unit": "Half",
        "is_recommended": True,
        "preparation_time": 30
    },
    {
        "name": "Chicken Tikka",
        "category": "Tandoori & Kebabs",
        "description": "Boneless chicken chunks marinated and grilled",
        "price": Decimal("220.00"),
        "spice_level": "medium",
        "dietary": ["Non-Vegetarian"],
        "allergens": ["Dairy"],
        "calories": 380,
        "serving_unit": "8 pcs",
        "preparation_time": 25
    },
    {
        "name": "Seekh Kebab",
        "category": "Tandoori & Kebabs",
        "description": "Minced lamb flavored with spices, grilled on skewers",
        "price": Decimal("240.00"),
        "spice_level": "medium",
        "dietary": ["Non-Vegetarian"],
        "allergens": [],
        "calories": 420,
        "serving_unit": "4 pcs",
        "preparation_time": 25
    },

    # BEVERAGES
    {
        "name": "Masala Chai",
        "category": "Beverages",
        "description": "Traditional Indian tea with aromatic spices and milk",
        "price": Decimal("30.00"),
        "spice_level": "none",
        "dietary": ["Vegetarian"],
        "allergens": ["Dairy"],
        "calories": 80,
        "serving_unit": "1 cup",
        "preparation_time": 5
    },
    {
        "name": "Filter Coffee",
        "category": "Beverages",
        "description": "South Indian style filter coffee with milk",
        "price": Decimal("40.00"),
        "spice_level": "none",
        "dietary": ["Vegetarian"],
        "allergens": ["Dairy"],
        "calories": 70,
        "serving_unit": "1 cup",
        "preparation_time": 5
    },
    {
        "name": "Mango Lassi",
        "category": "Beverages",
        "description": "Sweet yogurt drink blended with fresh mango",
        "price": Decimal("75.00"),
        "spice_level": "none",
        "dietary": ["Vegetarian", "Gluten-Free"],
        "allergens": ["Dairy"],
        "calories": 180,
        "serving_unit": "1 glass",
        "is_recommended": True,
        "preparation_time": 5
    },
    {
        "name": "Sweet Lassi",
        "category": "Beverages",
        "description": "Traditional sweet yogurt drink",
        "price": Decimal("60.00"),
        "spice_level": "none",
        "dietary": ["Vegetarian", "Gluten-Free"],
        "allergens": ["Dairy"],
        "calories": 150,
        "serving_unit": "1 glass",
        "preparation_time": 5
    },
    {
        "name": "Salt Lassi",
        "category": "Beverages",
        "description": "Refreshing salted yogurt drink",
        "price": Decimal("60.00"),
        "spice_level": "none",
        "dietary": ["Vegetarian", "Gluten-Free"],
        "allergens": ["Dairy"],
        "calories": 120,
        "serving_unit": "1 glass",
        "preparation_time": 5
    },
    {
        "name": "Fresh Lime Soda",
        "category": "Beverages",
        "description": "Freshly squeezed lime with soda water (sweet/salt/mixed)",
        "price": Decimal("50.00"),
        "spice_level": "none",
        "dietary": ["Vegetarian", "Vegan", "Gluten-Free", "Dairy-Free"],
        "allergens": [],
        "calories": 80,
        "serving_unit": "1 glass",
        "preparation_time": 5
    },
    {
        "name": "Rose Milk",
        "category": "Beverages",
        "description": "Chilled milk flavored with rose syrup",
        "price": Decimal("55.00"),
        "spice_level": "none",
        "dietary": ["Vegetarian", "Gluten-Free"],
        "allergens": ["Dairy"],
        "calories": 160,
        "serving_unit": "1 glass",
        "preparation_time": 5
    },

    # DESSERTS
    {
        "name": "Gulab Jamun",
        "category": "Desserts",
        "description": "Soft milk dumplings soaked in rose-flavored sugar syrup (2 pcs)",
        "price": Decimal("70.00"),
        "spice_level": "none",
        "dietary": ["Vegetarian"],
        "allergens": ["Dairy", "Gluten"],
        "calories": 320,
        "serving_unit": "2 pcs",
        "is_recommended": True,
        "preparation_time": 5
    },
    {
        "name": "Rasmalai",
        "category": "Desserts",
        "description": "Cottage cheese dumplings in sweetened, thickened milk (2 pcs)",
        "price": Decimal("85.00"),
        "spice_level": "none",
        "dietary": ["Vegetarian", "Gluten-Free"],
        "allergens": ["Dairy", "Nuts"],
        "calories": 280,
        "serving_unit": "2 pcs",
        "preparation_time": 5
    },
    {
        "name": "Kheer",
        "category": "Desserts",
        "description": "Rice pudding cooked in milk with cardamom and nuts",
        "price": Decimal("75.00"),
        "spice_level": "none",
        "dietary": ["Vegetarian", "Gluten-Free"],
        "allergens": ["Dairy", "Nuts"],
        "calories": 240,
        "serving_unit": "1 bowl",
        "preparation_time": 5
    },
    {
        "name": "Gajar Halwa",
        "category": "Desserts",
        "description": "Grated carrot pudding cooked in milk and ghee with nuts",
        "price": Decimal("90.00"),
        "spice_level": "none",
        "dietary": ["Vegetarian", "Gluten-Free"],
        "allergens": ["Dairy", "Nuts"],
        "calories": 350,
        "serving_unit": "1 bowl",
        "preparation_time": 5
    },
    {
        "name": "Kulfi",
        "category": "Desserts",
        "description": "Traditional Indian ice cream flavored with cardamom and saffron",
        "price": Decimal("65.00"),
        "spice_level": "none",
        "dietary": ["Vegetarian", "Gluten-Free"],
        "allergens": ["Dairy", "Nuts"],
        "calories": 200,
        "serving_unit": "1 pc",
        "preparation_time": 5
    }
]


# ============================================================================
# POPULATION FUNCTIONS
# ============================================================================

async def clear_existing_data(session):
    """Clear existing menu data (for clean repopulation)."""
    logger.info("Clearing existing menu data...")

    # Delete in reverse dependency order (ignore if tables don't exist)
    try:
        await session.execute(delete(MenuItemAllergenMapping))
        await session.execute(delete(MenuItemDietaryMapping))
        await session.execute(delete(MenuItemCategoryMapping))
        await session.execute(delete(MenuItem))
        await session.execute(delete(MenuCategory))
        await session.execute(delete(MenuSection))
        await session.execute(delete(Allergen))
        await session.execute(delete(DietaryType))
        await session.commit()
        logger.info("Existing data cleared")
    except Exception as e:
        # Tables might not exist yet, rollback and continue
        await session.rollback()
        logger.warning("Could not clear data (tables may not exist)", error=str(e))
        logger.info("Continuing with population...")


async def get_or_create_restaurant(session) -> UUID:
    """Get or create default restaurant."""
    result = await session.execute(select(Restaurant.restaurant_id))
    row = result.first()

    if row:
        restaurant_id = row[0]
        logger.info("Using existing restaurant", restaurant_id=str(restaurant_id))
        return restaurant_id

    # Create default restaurant if none exists
    logger.warning("No restaurant found - creating default restaurant")
    restaurant = Restaurant(
        restaurant_id=uuid4(),
        restaurant_name="A24 Restaurant",
        restaurant_phone="+91 9876543210",
        restaurant_email="info@a24restaurant.com",
        restaurant_status="active"
    )
    session.add(restaurant)
    await session.commit()
    await session.refresh(restaurant)
    logger.info("Created default restaurant", restaurant_id=str(restaurant.restaurant_id))
    return restaurant.restaurant_id


async def populate_dietary_types(session, restaurant_id: UUID) -> Dict[str, UUID]:
    """Populate dietary types and return name->id mapping."""
    logger.info("Populating dietary types...")

    dietary_map = {}
    for dt in DIETARY_TYPES:
        dietary_type = DietaryType(
            dietary_type_id=uuid4(),
            dietary_type_name=dt["name"],
            dietary_type_label=dt["label"],
            dietary_type_description=dt["description"]
        )
        session.add(dietary_type)
        dietary_map[dt["name"]] = dietary_type.dietary_type_id

    await session.commit()
    logger.info("Dietary types created", count=len(dietary_map))
    return dietary_map


async def populate_allergens(session, restaurant_id: UUID) -> Dict[str, UUID]:
    """Populate allergens and return name->id mapping."""
    logger.info("Populating allergens...")

    allergen_map = {}
    for allergen_data in ALLERGENS:
        allergen = Allergen(
            allergen_id=uuid4(),
            allergen_name=allergen_data["name"],
            allergen_description=allergen_data["description"]
        )
        session.add(allergen)
        allergen_map[allergen_data["name"]] = allergen.allergen_id

    await session.commit()
    logger.info("Allergens created", count=len(allergen_map))
    return allergen_map


async def populate_sections_and_categories(session, restaurant_id: UUID) -> Dict[str, UUID]:
    """Populate sections and categories, return category name->id mapping."""
    logger.info("Populating sections and categories...")

    # Create sections first
    section_map = {}
    for section_data in SECTIONS:
        section = MenuSection(
            menu_section_id=uuid4(),
            restaurant_id=restaurant_id,
            section_name=section_data["name"],
            section_description=section_data["description"],
            section_status="active",
            section_rank=section_data["rank"]
        )
        session.add(section)
        section_map[section_data["name"]] = section.menu_section_id

    await session.commit()
    logger.info("Sections created", count=len(section_map))

    # Create categories
    category_map = {}
    for cat_data in CATEGORIES:
        section_id = section_map[cat_data["section"]]
        category = MenuCategory(
            menu_category_id=uuid4(),
            restaurant_id=restaurant_id,
            menu_section_id=section_id,
            menu_category_name=cat_data["name"],
            menu_category_description=cat_data["description"],
            menu_category_status="active",
            menu_category_rank=cat_data["rank"]
        )
        session.add(category)
        category_map[cat_data["name"]] = category.menu_category_id

    await session.commit()
    logger.info("Categories created", count=len(category_map))
    return category_map


async def populate_menu_items(
    session,
    restaurant_id: UUID,
    category_map: Dict[str, UUID],
    dietary_map: Dict[str, UUID],
    allergen_map: Dict[str, UUID]
):
    """Populate menu items with all mappings."""
    logger.info("Populating menu items...", total=len(MENU_ITEMS))

    items_created = 0
    for item_data in MENU_ITEMS:
        # Create menu item
        menu_item = MenuItem(
            menu_item_id=uuid4(),
            restaurant_id=restaurant_id,
            menu_item_name=item_data["name"],
            menu_item_description=item_data["description"],
            menu_item_price=item_data["price"],
            menu_item_spice_level=item_data["spice_level"],
            menu_item_status="active",
            menu_item_in_stock=True,
            menu_item_is_recommended=item_data.get("is_recommended", False),
            menu_item_favorite=item_data.get("is_favorite", False),
            menu_item_calories=item_data.get("calories"),
            menu_item_serving_unit=item_data.get("serving_unit"),
            menu_item_minimum_preparation_time=item_data.get("preparation_time")
        )
        session.add(menu_item)
        await session.flush()  # Get the ID

        # Create category mapping
        category_id = category_map[item_data["category"]]
        category_mapping = MenuItemCategoryMapping(
            mapping_id=uuid4(),
            restaurant_id=restaurant_id,
            menu_item_id=menu_item.menu_item_id,
            menu_category_id=category_id,
            is_primary=True,
            display_rank=0
        )
        session.add(category_mapping)

        # Create dietary mappings
        for dietary_name in item_data["dietary"]:
            if dietary_name in dietary_map:
                dietary_mapping = MenuItemDietaryMapping(
                    mapping_id=uuid4(),
                    restaurant_id=restaurant_id,
                    menu_item_id=menu_item.menu_item_id,
                    dietary_type_id=dietary_map[dietary_name]
                )
                session.add(dietary_mapping)

        # Create allergen mappings
        for allergen_name in item_data["allergens"]:
            if allergen_name in allergen_map:
                allergen_mapping = MenuItemAllergenMapping(
                    mapping_id=uuid4(),
                    restaurant_id=restaurant_id,
                    menu_item_id=menu_item.menu_item_id,
                    allergen_id=allergen_map[allergen_name]
                )
                session.add(allergen_mapping)

        items_created += 1
        if items_created % 10 == 0:
            logger.info("Progress", items_created=items_created, total=len(MENU_ITEMS))

    await session.commit()
    logger.info("Menu items created", total=items_created)


async def verify_population(session):
    """Verify the data was populated correctly."""
    logger.info("Verifying population...")

    # Count records
    from sqlalchemy import func as sql_func

    sections_count = await session.scalar(select(sql_func.count(MenuSection.menu_section_id)))
    categories_count = await session.scalar(select(sql_func.count(MenuCategory.menu_category_id)))
    items_count = await session.scalar(select(sql_func.count(MenuItem.menu_item_id)))
    dietary_count = await session.scalar(select(sql_func.count(DietaryType.dietary_type_id)))
    allergen_count = await session.scalar(select(sql_func.count(Allergen.allergen_id)))

    logger.info(
        "Population verification complete",
        sections=sections_count,
        categories=categories_count,
        menu_items=items_count,
        dietary_types=dietary_count,
        allergens=allergen_count
    )

    return {
        "sections": sections_count,
        "categories": categories_count,
        "menu_items": items_count,
        "dietary_types": dietary_count,
        "allergens": allergen_count
    }


# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Main population function."""
    try:
        logger.info("=" * 60)
        logger.info("RESTAURANT MENU POPULATION SCRIPT")
        logger.info("=" * 60)

        # Initialize database connection
        logger.info("Initializing database connection")
        db_manager.init_database()

        # NOTE: Skipping table creation - assuming tables already exist from migrations
        logger.info("Using existing database tables")

        async with get_db_session() as session:
            # Step 1: Get restaurant
            restaurant_id = await get_or_create_restaurant(session)

            # Step 2: Clear existing data
            await clear_existing_data(session)

            # Step 3: Populate lookup tables
            dietary_map = await populate_dietary_types(session, restaurant_id)
            allergen_map = await populate_allergens(session, restaurant_id)

            # Step 4: Populate sections and categories
            category_map = await populate_sections_and_categories(session, restaurant_id)

            # Step 5: Populate menu items with mappings
            await populate_menu_items(session, restaurant_id, category_map, dietary_map, allergen_map)

            # Step 6: Verify
            stats = await verify_population(session)

            logger.info("=" * 60)
            logger.info("POPULATION COMPLETE!")
            logger.info("=" * 60)
            logger.info("Summary", **stats)
            logger.info("Next step: Run 'python scripts/index_menu_to_vector_db.py' to enable semantic search")

            return 0

    except Exception as e:
        logger.error("Population failed", error=str(e), exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

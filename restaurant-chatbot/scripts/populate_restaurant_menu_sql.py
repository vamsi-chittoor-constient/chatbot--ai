"""
Populate Restaurant Menu Using Raw SQL
=======================================
Populates the database with realistic Indian restaurant menu items using direct SQL.
Bypasses ORM metadata issues by using raw INSERT statements.
"""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4, UUID
from decimal import Decimal
from typing import Dict, List, Any
import structlog

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import db_manager, get_db_session
from sqlalchemy import text

logger = structlog.get_logger()


# Dietary Types
DIETARY_TYPES = [
    {"name": "Vegetarian", "label": "🌱 Veg", "description": "Contains no meat, fish, or poultry"},
    {"name": "Vegan", "label": "🌿 Vegan", "description": "Contains no animal products"},
    {"name": "Gluten-Free", "label": "🌾 GF", "description": "Contains no gluten"},
    {"name": "Dairy-Free", "label": "🥛 DF", "description": "Contains no dairy products"},
    {"name": "Non-Vegetarian", "label": "🍗 Non-Veg", "description": "Contains meat, fish, or poultry"}
]

# Allergens
ALLERGENS = [
    {"name": "Dairy", "description": "Contains milk or milk products"},
    {"name": "Nuts", "description": "Contains tree nuts or peanuts"},
    {"name": "Gluten", "description": "Contains wheat, barley, or rye"},
    {"name": "Soy", "description": "Contains soy or soy products"},
    {"name": "Eggs", "description": "Contains eggs"},
    {"name": "Shellfish", "description": "Contains shellfish"},
    {"name": "Fish", "description": "Contains fish"}
]

# Sections
SECTIONS = [
    {"name": "Vegetarian", "description": "Vegetarian dishes", "rank": 1},
    {"name": "Non-Vegetarian", "description": "Non-vegetarian dishes", "rank": 2}
]

# Categories
CATEGORIES = [
    {"name": "South Indian Breakfast", "section": "Vegetarian", "description": "Traditional South Indian breakfast items", "rank": 1},
    {"name": "North Indian Breakfast", "section": "Vegetarian", "description": "North Indian breakfast specialties", "rank": 2},
    {"name": "Veg Main Course", "section": "Vegetarian", "description": "Vegetarian curries and gravies", "rank": 3},
    {"name": "Non-Veg Main Course", "section": "Non-Vegetarian", "description": "Chicken, mutton, and seafood curries", "rank": 4},
    {"name": "Rice & Biryani", "section": "Non-Vegetarian", "description": "Rice dishes and aromatic biryanis", "rank": 5},
    {"name": "Breads", "section": "Vegetarian", "description": "Indian breads and rotis", "rank": 6},
    {"name": "Snacks & Starters", "section": "Vegetarian", "description": "Appetizers and snacks", "rank": 7},
    {"name": "Tandoori & Kebabs", "section": "Non-Vegetarian", "description": "Grilled and tandoor specialties", "rank": 8},
    {"name": "Beverages", "section": "Vegetarian", "description": "Hot and cold beverages", "rank": 9},
    {"name": "Desserts", "section": "Vegetarian", "description": "Traditional Indian sweets", "rank": 10},
    {"name": "Veg Rice", "section": "Vegetarian", "description": "Vegetarian rice dishes", "rank": 11}
]

# Menu Items (50+ realistic dishes)
MENU_ITEMS = [
    # South Indian Breakfast
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
        "name": "Idli Sambar",
        "category": "South Indian Breakfast",
        "description": "Steamed rice cakes served with sambar and coconut chutney",
        "price": Decimal("80.00"),
        "spice_level": "mild",
        "dietary": ["Vegetarian", "Vegan", "Gluten-Free"],
        "allergens": [],
        "calories": 250,
        "serving_unit": "3 pcs",
        "is_recommended": True,
        "preparation_time": 10
    },
    {
        "name": "Medu Vada",
        "category": "South Indian Breakfast",
        "description": "Crispy lentil donuts served with sambar and chutneys",
        "price": Decimal("90.00"),
        "spice_level": "mild",
        "dietary": ["Vegetarian", "Vegan", "Gluten-Free"],
        "allergens": [],
        "calories": 280,
        "serving_unit": "2 pcs",
        "preparation_time": 12
    },

    # North Indian Breakfast
    {
        "name": "Chole Bhature",
        "category": "North Indian Breakfast",
        "description": "Spicy chickpea curry served with fluffy fried bread",
        "price": Decimal("140.00"),
        "spice_level": "medium",
        "dietary": ["Vegetarian"],
        "allergens": ["Gluten"],
        "calories": 480,
        "serving_unit": "2 pcs",
        "is_recommended": True,
        "preparation_time": 20
    },
    {
        "name": "Aloo Paratha",
        "category": "North Indian Breakfast",
        "description": "Whole wheat flatbread stuffed with spiced potatoes, served with yogurt and pickle",
        "price": Decimal("110.00"),
        "spice_level": "mild",
        "dietary": ["Vegetarian"],
        "allergens": ["Gluten", "Dairy"],
        "calories": 380,
        "serving_unit": "2 pcs",
        "preparation_time": 15
    },
    {
        "name": "Poha",
        "category": "North Indian Breakfast",
        "description": "Flattened rice cooked with onions, turmeric, and spices",
        "price": Decimal("70.00"),
        "spice_level": "mild",
        "dietary": ["Vegetarian", "Vegan", "Gluten-Free"],
        "allergens": [],
        "calories": 220,
        "serving_unit": "1 bowl",
        "preparation_time": 10
    },

    # Veg Main Course
    {
        "name": "Paneer Butter Masala",
        "category": "Veg Main Course",
        "description": "Cottage cheese cubes in rich tomato and butter gravy",
        "price": Decimal("220.00"),
        "spice_level": "mild",
        "dietary": ["Vegetarian"],
        "allergens": ["Dairy"],
        "calories": 450,
        "serving_unit": "1 bowl",
        "is_recommended": True,
        "is_favorite": True,
        "preparation_time": 20
    },
    {
        "name": "Dal Makhani",
        "category": "Veg Main Course",
        "description": "Black lentils slow-cooked with butter and cream",
        "price": Decimal("180.00"),
        "spice_level": "mild",
        "dietary": ["Vegetarian"],
        "allergens": ["Dairy"],
        "calories": 350,
        "serving_unit": "1 bowl",
        "is_recommended": True,
        "preparation_time": 25
    },
    {
        "name": "Palak Paneer",
        "category": "Veg Main Course",
        "description": "Cottage cheese in creamy spinach gravy",
        "price": Decimal("200.00"),
        "spice_level": "mild",
        "dietary": ["Vegetarian"],
        "allergens": ["Dairy"],
        "calories": 320,
        "serving_unit": "1 bowl",
        "preparation_time": 18
    },
    {
        "name": "Chana Masala",
        "category": "Veg Main Course",
        "description": "Chickpeas cooked in tangy tomato and onion gravy",
        "price": Decimal("160.00"),
        "spice_level": "medium",
        "dietary": ["Vegetarian", "Vegan"],
        "allergens": [],
        "calories": 280,
        "serving_unit": "1 bowl",
        "preparation_time": 15
    },
    {
        "name": "Kadai Paneer",
        "category": "Veg Main Course",
        "description": "Cottage cheese with bell peppers in spicy kadai gravy",
        "price": Decimal("210.00"),
        "spice_level": "medium",
        "dietary": ["Vegetarian"],
        "allergens": ["Dairy"],
        "calories": 380,
        "serving_unit": "1 bowl",
        "preparation_time": 20
    },

    # Non-Veg Main Course
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
        "description": "Grilled chicken in creamy tomato gravy",
        "price": Decimal("240.00"),
        "spice_level": "medium",
        "dietary": ["Non-Vegetarian"],
        "allergens": ["Dairy"],
        "calories": 480,
        "serving_unit": "1 bowl",
        "is_recommended": True,
        "preparation_time": 22
    },
    {
        "name": "Mutton Rogan Josh",
        "category": "Non-Veg Main Course",
        "description": "Aromatic mutton curry with Kashmiri spices",
        "price": Decimal("280.00"),
        "spice_level": "medium",
        "dietary": ["Non-Vegetarian"],
        "allergens": [],
        "calories": 550,
        "serving_unit": "1 bowl",
        "preparation_time": 35
    },
    {
        "name": "Fish Curry",
        "category": "Non-Veg Main Course",
        "description": "Fresh fish cooked in coconut-based curry",
        "price": Decimal("250.00"),
        "spice_level": "medium",
        "dietary": ["Non-Vegetarian", "Gluten-Free"],
        "allergens": ["Fish"],
        "calories": 380,
        "serving_unit": "1 bowl",
        "preparation_time": 20
    },
    {
        "name": "Prawn Masala",
        "category": "Non-Veg Main Course",
        "description": "Succulent prawns in spicy masala gravy",
        "price": Decimal("320.00"),
        "spice_level": "hot",
        "dietary": ["Non-Vegetarian"],
        "allergens": ["Shellfish"],
        "calories": 420,
        "serving_unit": "1 bowl",
        "preparation_time": 18
    },

    # Rice & Biryani
    {
        "name": "Chicken Biryani",
        "category": "Rice & Biryani",
        "description": "Fragrant basmati rice layered with spiced chicken",
        "price": Decimal("220.00"),
        "spice_level": "medium",
        "dietary": ["Non-Vegetarian"],
        "allergens": ["Dairy"],
        "calories": 650,
        "serving_unit": "1 plate",
        "is_recommended": True,
        "is_favorite": True,
        "preparation_time": 30
    },
    {
        "name": "Mutton Biryani",
        "category": "Rice & Biryani",
        "description": "Aromatic rice with tender mutton pieces",
        "price": Decimal("260.00"),
        "spice_level": "medium",
        "dietary": ["Non-Vegetarian"],
        "allergens": ["Dairy"],
        "calories": 720,
        "serving_unit": "1 plate",
        "is_favorite": True,
        "preparation_time": 35
    },
    {
        "name": "Egg Biryani",
        "category": "Rice & Biryani",
        "description": "Flavorful rice with boiled eggs",
        "price": Decimal("180.00"),
        "spice_level": "mild",
        "dietary": ["Non-Vegetarian"],
        "allergens": ["Eggs", "Dairy"],
        "calories": 520,
        "serving_unit": "1 plate",
        "preparation_time": 25
    },

    # Veg Rice
    {
        "name": "Veg Biryani",
        "category": "Veg Rice",
        "description": "Mixed vegetables with aromatic rice",
        "price": Decimal("160.00"),
        "spice_level": "mild",
        "dietary": ["Vegetarian"],
        "allergens": ["Dairy"],
        "calories": 480,
        "serving_unit": "1 plate",
        "preparation_time": 25
    },
    {
        "name": "Jeera Rice",
        "category": "Veg Rice",
        "description": "Basmati rice tempered with cumin seeds",
        "price": Decimal("120.00"),
        "spice_level": "none",
        "dietary": ["Vegetarian", "Vegan", "Gluten-Free"],
        "allergens": [],
        "calories": 280,
        "serving_unit": "1 bowl",
        "preparation_time": 15
    },
    {
        "name": "Veg Pulao",
        "category": "Veg Rice",
        "description": "Fragrant rice cooked with mixed vegetables",
        "price": Decimal("140.00"),
        "spice_level": "mild",
        "dietary": ["Vegetarian"],
        "allergens": [],
        "calories": 350,
        "serving_unit": "1 bowl",
        "preparation_time": 20
    },

    # Breads
    {
        "name": "Butter Naan",
        "category": "Breads",
        "description": "Soft leavened bread brushed with butter",
        "price": Decimal("50.00"),
        "spice_level": "none",
        "dietary": ["Vegetarian"],
        "allergens": ["Gluten", "Dairy"],
        "calories": 180,
        "serving_unit": "1 pc",
        "is_recommended": True,
        "preparation_time": 8
    },
    {
        "name": "Garlic Naan",
        "category": "Breads",
        "description": "Naan topped with fresh garlic and coriander",
        "price": Decimal("60.00"),
        "spice_level": "none",
        "dietary": ["Vegetarian"],
        "allergens": ["Gluten", "Dairy"],
        "calories": 200,
        "serving_unit": "1 pc",
        "is_recommended": True,
        "preparation_time": 10
    },
    {
        "name": "Tandoori Roti",
        "category": "Breads",
        "description": "Whole wheat flatbread from tandoor",
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
        "description": "Multi-layered whole wheat bread",
        "price": Decimal("55.00"),
        "spice_level": "none",
        "dietary": ["Vegetarian"],
        "allergens": ["Gluten", "Dairy"],
        "calories": 220,
        "serving_unit": "1 pc",
        "preparation_time": 12
    },

    # Snacks & Starters
    {
        "name": "Samosa",
        "category": "Snacks & Starters",
        "description": "Crispy pastry filled with spiced potatoes and peas",
        "price": Decimal("40.00"),
        "spice_level": "mild",
        "dietary": ["Vegetarian", "Vegan"],
        "allergens": ["Gluten"],
        "calories": 150,
        "serving_unit": "2 pcs",
        "is_recommended": True,
        "preparation_time": 15
    },
    {
        "name": "Paneer Tikka",
        "category": "Snacks & Starters",
        "description": "Grilled cottage cheese marinated in spices",
        "price": Decimal("180.00"),
        "spice_level": "medium",
        "dietary": ["Vegetarian"],
        "allergens": ["Dairy"],
        "calories": 320,
        "serving_unit": "6 pcs",
        "is_recommended": True,
        "preparation_time": 18
    },
    {
        "name": "Vegetable Pakora",
        "category": "Snacks & Starters",
        "description": "Mixed vegetable fritters",
        "price": Decimal("90.00"),
        "spice_level": "mild",
        "dietary": ["Vegetarian", "Vegan"],
        "allergens": ["Gluten"],
        "calories": 250,
        "serving_unit": "8 pcs",
        "preparation_time": 12
    },
    {
        "name": "Hara Bhara Kabab",
        "category": "Snacks & Starters",
        "description": "Spinach and peas patties",
        "price": Decimal("120.00"),
        "spice_level": "mild",
        "dietary": ["Vegetarian"],
        "allergens": ["Gluten"],
        "calories": 180,
        "serving_unit": "4 pcs",
        "preparation_time": 15
    },

    # Tandoori & Kebabs
    {
        "name": "Chicken Tikka",
        "category": "Tandoori & Kebabs",
        "description": "Boneless chicken marinated in yogurt and spices, grilled in tandoor",
        "price": Decimal("200.00"),
        "spice_level": "medium",
        "dietary": ["Non-Vegetarian"],
        "allergens": ["Dairy"],
        "calories": 380,
        "serving_unit": "6 pcs",
        "is_recommended": True,
        "preparation_time": 20
    },
    {
        "name": "Tandoori Chicken",
        "category": "Tandoori & Kebabs",
        "description": "Whole chicken marinated and grilled",
        "price": Decimal("280.00"),
        "spice_level": "hot",
        "dietary": ["Non-Vegetarian"],
        "allergens": ["Dairy"],
        "calories": 520,
        "serving_unit": "Half",
        "is_favorite": True,
        "preparation_time": 25
    },
    {
        "name": "Seekh Kebab",
        "category": "Tandoori & Kebabs",
        "description": "Minced mutton skewers with spices",
        "price": Decimal("220.00"),
        "spice_level": "medium",
        "dietary": ["Non-Vegetarian"],
        "allergens": [],
        "calories": 420,
        "serving_unit": "4 pcs",
        "preparation_time": 18
    },
    {
        "name": "Fish Tikka",
        "category": "Tandoori & Kebabs",
        "description": "Marinated fish grilled to perfection",
        "price": Decimal("240.00"),
        "spice_level": "medium",
        "dietary": ["Non-Vegetarian"],
        "allergens": ["Fish", "Dairy"],
        "calories": 350,
        "serving_unit": "6 pcs",
        "preparation_time": 16
    },

    # Beverages
    {
        "name": "Masala Chai",
        "category": "Beverages",
        "description": "Traditional Indian spiced tea",
        "price": Decimal("40.00"),
        "spice_level": "none",
        "dietary": ["Vegetarian"],
        "allergens": ["Dairy"],
        "calories": 80,
        "serving_unit": "1 cup",
        "is_recommended": True,
        "preparation_time": 5
    },
    {
        "name": "Lassi",
        "category": "Beverages",
        "description": "Creamy yogurt-based drink",
        "price": Decimal("60.00"),
        "spice_level": "none",
        "dietary": ["Vegetarian"],
        "allergens": ["Dairy"],
        "calories": 150,
        "serving_unit": "1 glass",
        "is_recommended": True,
        "preparation_time": 5
    },
    {
        "name": "Mango Lassi",
        "category": "Beverages",
        "description": "Sweet mango-flavored yogurt drink",
        "price": Decimal("80.00"),
        "spice_level": "none",
        "dietary": ["Vegetarian"],
        "allergens": ["Dairy"],
        "calories": 180,
        "serving_unit": "1 glass",
        "preparation_time": 5
    },
    {
        "name": "Filter Coffee",
        "category": "Beverages",
        "description": "South Indian style filtered coffee",
        "price": Decimal("50.00"),
        "spice_level": "none",
        "dietary": ["Vegetarian"],
        "allergens": ["Dairy"],
        "calories": 60,
        "serving_unit": "1 cup",
        "preparation_time": 5
    },
    {
        "name": "Fresh Lime Soda",
        "category": "Beverages",
        "description": "Refreshing lime juice with soda",
        "price": Decimal("50.00"),
        "spice_level": "none",
        "dietary": ["Vegetarian", "Vegan"],
        "allergens": [],
        "calories": 40,
        "serving_unit": "1 glass",
        "preparation_time": 3
    },

    # Desserts
    {
        "name": "Gulab Jamun",
        "category": "Desserts",
        "description": "Deep-fried milk dumplings in sugar syrup",
        "price": Decimal("80.00"),
        "spice_level": "none",
        "dietary": ["Vegetarian"],
        "allergens": ["Dairy", "Gluten"],
        "calories": 280,
        "serving_unit": "2 pcs",
        "is_recommended": True,
        "preparation_time": 10
    },
    {
        "name": "Rasmalai",
        "category": "Desserts",
        "description": "Cottage cheese patties in sweetened milk",
        "price": Decimal("100.00"),
        "spice_level": "none",
        "dietary": ["Vegetarian"],
        "allergens": ["Dairy"],
        "calories": 320,
        "serving_unit": "2 pcs",
        "is_recommended": True,
        "preparation_time": 12
    },
    {
        "name": "Kulfi",
        "category": "Desserts",
        "description": "Traditional Indian ice cream",
        "price": Decimal("70.00"),
        "spice_level": "none",
        "dietary": ["Vegetarian"],
        "allergens": ["Dairy", "Nuts"],
        "calories": 250,
        "serving_unit": "1 pc",
        "preparation_time": 5
    },
    {
        "name": "Gajar Halwa",
        "category": "Desserts",
        "description": "Carrot pudding with nuts and raisins",
        "price": Decimal("90.00"),
        "spice_level": "none",
        "dietary": ["Vegetarian"],
        "allergens": ["Dairy", "Nuts"],
        "calories": 350,
        "serving_unit": "1 bowl",
        "preparation_time": 15
    },
    {
        "name": "Jalebi",
        "category": "Desserts",
        "description": "Crispy sweet spirals in sugar syrup",
        "price": Decimal("60.00"),
        "spice_level": "none",
        "dietary": ["Vegetarian"],
        "allergens": ["Gluten"],
        "calories": 220,
        "serving_unit": "4 pcs",
        "preparation_time": 8
    }
]


async def get_or_create_restaurant(session) -> UUID:
    """Get existing restaurant or create default one."""
    result = await session.execute(
        text("SELECT restaurant_id FROM restaurant_table WHERE is_deleted = false LIMIT 1")
    )
    row = result.fetchone()

    if row:
        restaurant_id = row[0]
        logger.info("Found existing restaurant", restaurant_id=str(restaurant_id))
        return restaurant_id

    # Create default restaurant
    restaurant_id = uuid4()
    await session.execute(
        text("""
            INSERT INTO restaurant_table (
                restaurant_id, restaurant_name, restaurant_email,
                restaurant_phone, restaurant_address, restaurant_status
            ) VALUES (
                :id, 'Spice Garden Indian Restaurant', 'info@spicegarden.com',
                '+1-555-0123', '123 Main St, Food District', 'active'
            )
        """),
        {"id": restaurant_id}
    )
    await session.commit()
    logger.info("Created default restaurant", restaurant_id=str(restaurant_id))
    return restaurant_id


async def clear_existing_data(session):
    """Clear existing menu data."""
    logger.info("Clearing existing menu data...")

    tables = [
        "menu_item_allergen_mapping",
        "menu_item_dietary_mapping",
        "menu_item_category_mapping",
        "menu_item",
        "menu_categories",
        "menu_sections",
        "allergens",
        "dietary_types"
    ]

    for table in tables:
        try:
            await session.execute(text(f"DELETE FROM {table}"))
            await session.commit()
            logger.info(f"Cleared {table}")
        except Exception as e:
            logger.warning(f"Could not clear {table}", error=str(e))
            await session.rollback()


async def populate_dietary_types(session, restaurant_id: UUID) -> Dict[str, UUID]:
    """Populate dietary types using raw SQL."""
    logger.info("Populating dietary types...")

    dietary_map = {}
    for dt in DIETARY_TYPES:
        dt_id = uuid4()
        await session.execute(
            text("""
                INSERT INTO dietary_types (
                    dietary_type_id, dietary_type_name, dietary_type_label, dietary_type_description
                ) VALUES (:id, :name, :label, :description)
            """),
            {
                "id": dt_id,
                "name": dt["name"],
                "label": dt["label"],
                "description": dt["description"]
            }
        )
        dietary_map[dt["name"]] = dt_id

    await session.commit()
    logger.info("Dietary types created", count=len(dietary_map))
    return dietary_map


async def populate_allergens(session, restaurant_id: UUID) -> Dict[str, UUID]:
    """Populate allergens using raw SQL."""
    logger.info("Populating allergens...")

    allergen_map = {}
    for allergen_data in ALLERGENS:
        allergen_id = uuid4()
        await session.execute(
            text("""
                INSERT INTO allergens (
                    allergen_id, allergen_name, allergen_description
                ) VALUES (:id, :name, :description)
            """),
            {
                "id": allergen_id,
                "name": allergen_data["name"],
                "description": allergen_data["description"]
            }
        )
        allergen_map[allergen_data["name"]] = allergen_id

    await session.commit()
    logger.info("Allergens created", count=len(allergen_map))
    return allergen_map


async def populate_sections_and_categories(session, restaurant_id: UUID) -> Dict[str, UUID]:
    """Populate sections and categories using raw SQL."""
    logger.info("Populating sections and categories...")

    # Create sections first
    section_map = {}
    for section_data in SECTIONS:
        section_id = uuid4()
        await session.execute(
            text("""
                INSERT INTO menu_sections (
                    menu_section_id, restaurant_id, section_name,
                    section_description, section_status, section_rank
                ) VALUES (:id, :restaurant_id, :name, :description, 'active', :rank)
            """),
            {
                "id": section_id,
                "restaurant_id": restaurant_id,
                "name": section_data["name"],
                "description": section_data["description"],
                "rank": section_data["rank"]
            }
        )
        section_map[section_data["name"]] = section_id

    await session.commit()
    logger.info("Sections created", count=len(section_map))

    # Create categories
    category_map = {}
    for cat_data in CATEGORIES:
        section_id = section_map[cat_data["section"]]
        category_id = uuid4()
        await session.execute(
            text("""
                INSERT INTO menu_categories (
                    menu_category_id, restaurant_id, menu_section_id,
                    menu_category_name, menu_category_description,
                    menu_category_status, menu_category_rank
                ) VALUES (:id, :restaurant_id, :section_id, :name, :description, 'active', :rank)
            """),
            {
                "id": category_id,
                "restaurant_id": restaurant_id,
                "section_id": section_id,
                "name": cat_data["name"],
                "description": cat_data["description"],
                "rank": cat_data["rank"]
            }
        )
        category_map[cat_data["name"]] = category_id

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
    """Populate menu items with all mappings using raw SQL."""
    logger.info("Populating menu items...", total=len(MENU_ITEMS))

    for idx, item_data in enumerate(MENU_ITEMS, 1):
        menu_item_id = uuid4()
        category_id = category_map[item_data["category"]]

        # Insert menu item
        await session.execute(
            text("""
                INSERT INTO menu_item (
                    menu_item_id, restaurant_id, menu_item_name, menu_item_description,
                    menu_item_price, menu_item_spice_level, menu_item_calories,
                    menu_item_serving_unit, menu_item_minimum_preparation_time,
                    menu_item_is_recommended, menu_item_favorite,
                    menu_item_status, menu_item_in_stock
                ) VALUES (
                    :id, :restaurant_id, :name, :description, :price, :spice_level,
                    :calories, :serving_unit, :prep_time, :recommended, :favorite,
                    'active', true
                )
            """),
            {
                "id": menu_item_id,
                "restaurant_id": restaurant_id,
                "name": item_data["name"],
                "description": item_data["description"],
                "price": item_data["price"],
                "spice_level": item_data["spice_level"],
                "calories": item_data.get("calories"),
                "serving_unit": item_data.get("serving_unit"),
                "prep_time": item_data.get("preparation_time"),
                "recommended": item_data.get("is_recommended", False),
                "favorite": item_data.get("is_favorite", False)
            }
        )

        # Insert category mapping
        await session.execute(
            text("""
                INSERT INTO menu_item_category_mapping (
                    mapping_id, menu_item_id, menu_category_id, restaurant_id, is_primary
                ) VALUES (:mapping_id, :menu_item_id, :category_id, :restaurant_id, true)
            """),
            {
                "mapping_id": uuid4(),
                "menu_item_id": menu_item_id,
                "category_id": category_id,
                "restaurant_id": restaurant_id
            }
        )

        # Insert dietary mappings
        for dietary_name in item_data.get("dietary", []):
            if dietary_name in dietary_map:
                await session.execute(
                    text("""
                        INSERT INTO menu_item_dietary_mapping (
                            mapping_id, menu_item_id, dietary_type_id, restaurant_id
                        ) VALUES (:mapping_id, :menu_item_id, :dietary_id, :restaurant_id)
                    """),
                    {
                        "mapping_id": uuid4(),
                        "menu_item_id": menu_item_id,
                        "dietary_id": dietary_map[dietary_name],
                        "restaurant_id": restaurant_id
                    }
                )

        # Insert allergen mappings
        for allergen_name in item_data.get("allergens", []):
            if allergen_name in allergen_map:
                await session.execute(
                    text("""
                        INSERT INTO menu_item_allergen_mapping (
                            mapping_id, menu_item_id, allergen_id, restaurant_id
                        ) VALUES (:mapping_id, :menu_item_id, :allergen_id, :restaurant_id)
                    """),
                    {
                        "mapping_id": uuid4(),
                        "menu_item_id": menu_item_id,
                        "allergen_id": allergen_map[allergen_name],
                        "restaurant_id": restaurant_id
                    }
                )

        if idx % 10 == 0:
            logger.info(f"Created {idx}/{len(MENU_ITEMS)} menu items...")

    await session.commit()
    logger.info("All menu items created", total=len(MENU_ITEMS))


async def main():
    """Main execution function."""
    try:
        # Initialize database
        db_manager.init_database()
        logger.info("Database initialized")

        async with get_db_session() as session:
            # Get or create restaurant
            restaurant_id = await get_or_create_restaurant(session)

            # Clear existing data
            await clear_existing_data(session)

            # Populate lookup tables
            dietary_map = await populate_dietary_types(session, restaurant_id)
            allergen_map = await populate_allergens(session, restaurant_id)

            # Populate menu structure
            category_map = await populate_sections_and_categories(session, restaurant_id)

            # Populate menu items
            await populate_menu_items(session, restaurant_id, category_map, dietary_map, allergen_map)

            logger.info("=" * 60)
            logger.info("MENU POPULATION COMPLETED SUCCESSFULLY!")
            logger.info("=" * 60)
            logger.info(f"Restaurant ID: {restaurant_id}")
            logger.info(f"Dietary Types: {len(dietary_map)}")
            logger.info(f"Allergens: {len(allergen_map)}")
            logger.info(f"Categories: {len(category_map)}")
            logger.info(f"Menu Items: {len(MENU_ITEMS)}")

    except Exception as e:
        logger.error("Failed to populate menu", error=str(e), exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())

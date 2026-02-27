"""
Create Menu Tables
===================
Creates only the menu-related tables needed for the restaurant menu system.
Uses CREATE TABLE IF NOT EXISTS to avoid errors if tables already exist.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import db_manager, get_db_session
from sqlalchemy import text
import structlog

logger = structlog.get_logger("create_menu_tables")


# SQL to create menu tables
CREATE_TABLES_SQL = """
-- Dietary Types lookup table
CREATE TABLE IF NOT EXISTS dietary_types (
    dietary_type_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dietary_type_name VARCHAR(255),
    dietary_type_label VARCHAR(255),
    dietary_type_description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    updated_by UUID,
    deleted_at TIMESTAMP WITH TIME ZONE,
    is_deleted BOOLEAN DEFAULT FALSE
);

-- Allergens lookup table
CREATE TABLE IF NOT EXISTS allergens (
    allergen_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    allergen_name VARCHAR(255) NOT NULL,
    allergen_description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    updated_by UUID,
    deleted_at TIMESTAMP WITH TIME ZONE,
    is_deleted BOOLEAN DEFAULT FALSE
);

-- Menu Sections (Veg/Non-Veg)
CREATE TABLE IF NOT EXISTS menu_sections (
    menu_section_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID NOT NULL REFERENCES restaurant_table(restaurant_id) ON DELETE CASCADE,
    section_name VARCHAR(100) NOT NULL,
    section_description TEXT,
    section_status VARCHAR(20) NOT NULL DEFAULT 'active',
    section_rank INTEGER NOT NULL DEFAULT 0,
    section_image_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    updated_by UUID,
    deleted_at TIMESTAMP WITH TIME ZONE,
    is_deleted BOOLEAN DEFAULT FALSE
);

-- Menu Categories
CREATE TABLE IF NOT EXISTS menu_categories (
    menu_category_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID NOT NULL REFERENCES restaurant_table(restaurant_id) ON DELETE CASCADE,
    menu_section_id UUID NOT NULL REFERENCES menu_sections(menu_section_id) ON DELETE CASCADE,
    menu_category_name VARCHAR(100) NOT NULL,
    menu_category_description TEXT,
    menu_category_status VARCHAR(20) NOT NULL DEFAULT 'active',
    menu_category_rank INTEGER NOT NULL DEFAULT 0,
    menu_category_timings TEXT,
    menu_category_image_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    updated_by UUID,
    deleted_at TIMESTAMP WITH TIME ZONE,
    is_deleted BOOLEAN DEFAULT FALSE
);

-- Menu Items
CREATE TABLE IF NOT EXISTS menu_item (
    menu_item_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID NOT NULL REFERENCES restaurant_table(restaurant_id) ON DELETE CASCADE,
    menu_sub_category_id UUID,
    menu_item_name VARCHAR(200) NOT NULL,
    menu_item_description TEXT,
    menu_item_price NUMERIC(10, 2) NOT NULL,
    menu_item_quantity INTEGER,
    menu_item_status VARCHAR(20) NOT NULL DEFAULT 'active',
    menu_item_spice_level VARCHAR(20),
    menu_item_in_stock BOOLEAN DEFAULT TRUE,
    menu_item_is_recommended BOOLEAN DEFAULT FALSE,
    menu_item_favorite BOOLEAN DEFAULT FALSE,
    menu_item_minimum_preparation_time INTEGER,
    menu_item_allow_variation BOOLEAN DEFAULT FALSE,
    menu_item_allow_addon BOOLEAN DEFAULT FALSE,
    menu_item_is_combo BOOLEAN DEFAULT FALSE,
    menu_item_is_combo_parent BOOLEAN DEFAULT FALSE,
    menu_item_rank INTEGER NOT NULL DEFAULT 0,
    menu_item_ignore_taxes BOOLEAN DEFAULT FALSE,
    menu_item_ignore_discounts BOOLEAN DEFAULT FALSE,
    menu_item_timings TEXT,
    menu_item_tax_id UUID,
    menu_item_tax_cgst NUMERIC(5, 2),
    menu_item_tax_sgst NUMERIC(5, 2),
    menu_item_packaging_charges NUMERIC(10, 2),
    menu_item_attribute_id UUID,
    menu_item_addon_based_on VARCHAR(50),
    menu_item_markup_price NUMERIC(10, 2),
    menu_item_calories INTEGER,
    menu_item_is_seasonal BOOLEAN DEFAULT FALSE,
    menu_item_image_url VARCHAR(500),
    menu_item_serving_unit VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    updated_by UUID,
    deleted_at TIMESTAMP WITH TIME ZONE,
    is_deleted BOOLEAN DEFAULT FALSE,
    CONSTRAINT check_menu_item_status CHECK (menu_item_status IN ('active', 'inactive', 'discontinued')),
    CONSTRAINT check_spice_level CHECK (menu_item_spice_level IN ('none', 'mild', 'medium', 'hot', 'extra_hot') OR menu_item_spice_level IS NULL),
    CONSTRAINT check_price_positive CHECK (menu_item_price >= 0)
);

-- Menu Item Category Mapping (many-to-many)
CREATE TABLE IF NOT EXISTS menu_item_category_mapping (
    mapping_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID NOT NULL REFERENCES restaurant_table(restaurant_id) ON DELETE CASCADE,
    menu_item_id UUID NOT NULL REFERENCES menu_item(menu_item_id) ON DELETE CASCADE,
    menu_category_id UUID NOT NULL REFERENCES menu_categories(menu_category_id) ON DELETE CASCADE,
    menu_sub_category_id UUID,
    is_primary BOOLEAN DEFAULT FALSE,
    display_rank INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    updated_by UUID,
    deleted_at TIMESTAMP WITH TIME ZONE,
    is_deleted BOOLEAN DEFAULT FALSE
);

-- Menu Item Dietary Mapping
CREATE TABLE IF NOT EXISTS menu_item_dietary_mapping (
    mapping_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    menu_item_id UUID NOT NULL REFERENCES menu_item(menu_item_id) ON DELETE CASCADE,
    dietary_type_id UUID NOT NULL REFERENCES dietary_types(dietary_type_id) ON DELETE CASCADE,
    restaurant_id UUID NOT NULL REFERENCES restaurant_table(restaurant_id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    updated_by UUID,
    deleted_at TIMESTAMP WITH TIME ZONE,
    is_deleted BOOLEAN DEFAULT FALSE
);

-- Menu Item Allergen Mapping
CREATE TABLE IF NOT EXISTS menu_item_allergen_mapping (
    mapping_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    menu_item_id UUID NOT NULL REFERENCES menu_item(menu_item_id) ON DELETE CASCADE,
    allergen_id UUID NOT NULL REFERENCES allergens(allergen_id) ON DELETE CASCADE,
    restaurant_id UUID NOT NULL REFERENCES restaurant_table(restaurant_id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    updated_by UUID,
    deleted_at TIMESTAMP WITH TIME ZONE,
    is_deleted BOOLEAN DEFAULT FALSE
);
"""


async def main():
    """Create menu tables."""
    try:
        logger.info("=" * 60)
        logger.info("CREATE MENU TABLES")
        logger.info("=" * 60)

        # Initialize database
        logger.info("Initializing database connection")
        db_manager.init_database()

        # Execute table creation SQL
        logger.info("Creating menu tables (if not exist)...")
        async with get_db_session() as session:
            # Split and execute each statement
            for statement in CREATE_TABLES_SQL.strip().split(';'):
                statement = statement.strip()
                if statement:
                    await session.execute(text(statement))

            await session.commit()

        logger.info("=" * 60)
        logger.info("MENU TABLES CREATED SUCCESSFULLY!")
        logger.info("=" * 60)
        logger.info("Next step: Run 'python scripts/populate_restaurant_menu.py'")

        return 0

    except Exception as e:
        logger.error("Table creation failed", error=str(e), exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

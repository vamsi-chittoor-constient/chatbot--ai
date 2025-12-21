"""
Recreate Menu Tables with Correct Schema
==========================================
Drops old menu tables and creates new ones matching the current models.
"""

import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_db_session, db_manager
from sqlalchemy import text
import structlog

logger = structlog.get_logger()


async def main():
    """Drop old tables and create new ones."""
    db_manager.init_database()

    async with get_db_session() as session:
        logger.info("Dropping old menu tables...")

        # Drop tables in correct order (reverse of dependencies)
        drop_statements = [
            "DROP TABLE IF EXISTS menu_item_allergen_mapping CASCADE",
            "DROP TABLE IF EXISTS menu_item_dietary_mapping CASCADE",
            "DROP TABLE IF EXISTS menu_item_category_mapping CASCADE",
            "DROP TABLE IF EXISTS menu_item CASCADE",
            "DROP TABLE IF EXISTS menu_sub_categories CASCADE",
            "DROP TABLE IF EXISTS menu_categories CASCADE",
            "DROP TABLE IF EXISTS menu_sections CASCADE",
            "DROP TABLE IF EXISTS allergens CASCADE",
            "DROP TABLE IF EXISTS dietary_types CASCADE",
        ]

        for stmt in drop_statements:
            try:
                await session.execute(text(stmt))
                logger.info(f"Executed: {stmt}")
            except Exception as e:
                logger.warning(f"Failed to drop table", error=str(e))

        await session.commit()
        logger.info("Old tables dropped successfully")

        # Create new tables with correct schema
        logger.info("Creating new menu tables...")

        create_statements = [
            # Dietary Types
            """
            CREATE TABLE dietary_types (
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
            )
            """,

            # Allergens
            """
            CREATE TABLE allergens (
                allergen_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                allergen_name VARCHAR(255) NOT NULL,
                allergen_description TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                created_by UUID,
                updated_by UUID,
                deleted_at TIMESTAMP WITH TIME ZONE,
                is_deleted BOOLEAN DEFAULT FALSE
            )
            """,

            # Menu Sections
            """
            CREATE TABLE menu_sections (
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
                is_deleted BOOLEAN DEFAULT FALSE,
                CONSTRAINT check_section_status CHECK (section_status IN ('active', 'inactive'))
            )
            """,

            # Menu Categories
            """
            CREATE TABLE menu_categories (
                menu_category_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                restaurant_id UUID NOT NULL REFERENCES restaurant_table(restaurant_id) ON DELETE CASCADE,
                menu_section_id UUID REFERENCES menu_sections(menu_section_id) ON DELETE CASCADE,
                menu_category_name VARCHAR(100) NOT NULL,
                menu_category_description TEXT,
                menu_category_status VARCHAR(20) NOT NULL DEFAULT 'active',
                menu_category_rank INTEGER NOT NULL DEFAULT 0,
                menu_category_image_url TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                created_by UUID,
                updated_by UUID,
                deleted_at TIMESTAMP WITH TIME ZONE,
                is_deleted BOOLEAN DEFAULT FALSE,
                CONSTRAINT check_category_status CHECK (menu_category_status IN ('active', 'inactive'))
            )
            """,

            # Menu Items (complete schema matching model)
            """
            CREATE TABLE menu_item (
                menu_item_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                restaurant_id UUID NOT NULL REFERENCES restaurant_table(restaurant_id) ON DELETE CASCADE,
                menu_sub_category_id UUID,
                menu_item_name VARCHAR(200) NOT NULL,
                menu_item_description TEXT,
                menu_item_price NUMERIC(10, 2) NOT NULL,
                menu_item_quantity INTEGER,
                menu_item_status VARCHAR(20) DEFAULT 'active',
                menu_item_spice_level VARCHAR(20),
                menu_item_in_stock BOOLEAN DEFAULT TRUE,
                menu_item_is_recommended BOOLEAN DEFAULT FALSE,
                menu_item_favorite BOOLEAN DEFAULT FALSE,
                menu_item_minimum_preparation_time INTEGER,
                menu_item_allow_variation BOOLEAN DEFAULT FALSE,
                menu_item_allow_addon BOOLEAN DEFAULT FALSE,
                menu_item_is_combo BOOLEAN DEFAULT FALSE,
                menu_item_is_combo_parent BOOLEAN DEFAULT FALSE,
                menu_item_rank INTEGER DEFAULT 0,
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
                menu_item_dietary_type VARCHAR(255),
                menu_item_allergen_info VARCHAR(255),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                created_by UUID,
                updated_by UUID,
                deleted_at TIMESTAMP WITH TIME ZONE,
                is_deleted BOOLEAN DEFAULT FALSE,
                CONSTRAINT check_spice_level CHECK (
                    menu_item_spice_level IN ('none', 'mild', 'medium', 'hot', 'extra_hot')
                    OR menu_item_spice_level IS NULL
                ),
                CONSTRAINT check_item_status CHECK (
                    menu_item_status IN ('active', 'inactive', 'archived')
                )
            )
            """,

            # Menu Item Category Mapping
            """
            CREATE TABLE menu_item_category_mapping (
                mapping_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                menu_item_id UUID NOT NULL REFERENCES menu_item(menu_item_id) ON DELETE CASCADE,
                menu_category_id UUID NOT NULL REFERENCES menu_categories(menu_category_id) ON DELETE CASCADE,
                restaurant_id UUID NOT NULL REFERENCES restaurant_table(restaurant_id) ON DELETE CASCADE,
                is_primary BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                created_by UUID,
                updated_by UUID,
                deleted_at TIMESTAMP WITH TIME ZONE,
                is_deleted BOOLEAN DEFAULT FALSE,
                CONSTRAINT uq_menu_item_category UNIQUE (menu_item_id, menu_category_id)
            )
            """,

            # Menu Item Dietary Mapping
            """
            CREATE TABLE menu_item_dietary_mapping (
                mapping_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                menu_item_id UUID NOT NULL REFERENCES menu_item(menu_item_id) ON DELETE CASCADE,
                dietary_type_id UUID NOT NULL REFERENCES dietary_types(dietary_type_id) ON DELETE CASCADE,
                restaurant_id UUID NOT NULL REFERENCES restaurant_table(restaurant_id) ON DELETE CASCADE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                created_by UUID,
                updated_by UUID,
                deleted_at TIMESTAMP WITH TIME ZONE,
                is_deleted BOOLEAN DEFAULT FALSE,
                CONSTRAINT uq_menu_item_dietary UNIQUE (menu_item_id, dietary_type_id)
            )
            """,

            # Menu Item Allergen Mapping
            """
            CREATE TABLE menu_item_allergen_mapping (
                mapping_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                menu_item_id UUID NOT NULL REFERENCES menu_item(menu_item_id) ON DELETE CASCADE,
                allergen_id UUID NOT NULL REFERENCES allergens(allergen_id) ON DELETE CASCADE,
                restaurant_id UUID NOT NULL REFERENCES restaurant_table(restaurant_id) ON DELETE CASCADE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                created_by UUID,
                updated_by UUID,
                deleted_at TIMESTAMP WITH TIME ZONE,
                is_deleted BOOLEAN DEFAULT FALSE,
                CONSTRAINT uq_menu_item_allergen UNIQUE (menu_item_id, allergen_id)
            )
            """
        ]

        for stmt in create_statements:
            try:
                await session.execute(text(stmt))
                logger.info("Created table")
            except Exception as e:
                logger.error(f"Failed to create table", error=str(e))
                raise

        await session.commit()

        logger.info("=" * 60)
        logger.info("MENU TABLES RECREATED SUCCESSFULLY!")
        logger.info("=" * 60)
        logger.info("Tables created:")
        logger.info("  - dietary_types")
        logger.info("  - allergens")
        logger.info("  - menu_sections")
        logger.info("  - menu_categories")
        logger.info("  - menu_item")
        logger.info("  - menu_item_category_mapping")
        logger.info("  - menu_item_dietary_mapping")
        logger.info("  - menu_item_allergen_mapping")


if __name__ == "__main__":
    asyncio.run(main())

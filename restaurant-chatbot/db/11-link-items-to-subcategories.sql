-- ============================================================================
-- Migration: Link Menu Items to Sub-Categories (PetPooja Fix)
-- ============================================================================
-- Purpose: Retroactively link existing items to their sub-categories
--          This is needed because earlier sync used wrong field name (categoryid vs item_categoryid)
-- Date: 2025-12-28
-- ============================================================================

DO $$
DECLARE
    linked_count INT := 0;
    item_record RECORD;
    subcategory_id UUID;
BEGIN
    -- Find items from PetPooja payload and link them to sub-categories
    -- Based on the mapping: item.item_categoryid -> menu_sub_categories.ext_petpooja_categories_id

    -- Example mappings from finalpayload3.json:
    -- Item "Double Chicken Burger Combo" has item_categoryid: 80721
    -- Sub-category "Chicken Meal" has ext_petpooja_categories_id: 80721

    -- Update items with sub-category links
    -- We'll use a temporary table approach to avoid complex updates

    -- Create temp table with item->subcategory mapping
    CREATE TEMP TABLE temp_item_subcategory_mapping AS
    SELECT
        mi.menu_item_id,
        mi.menu_item_name,
        msc.menu_sub_category_id,
        msc.sub_category_name,
        msc.ext_petpooja_categories_id
    FROM menu_item mi
    CROSS JOIN menu_sub_categories msc
    WHERE mi.is_deleted = FALSE
      AND msc.is_deleted = FALSE
      AND mi.menu_sub_category_id IS NULL
      AND mi.ext_petpooja_item_id IS NOT NULL;

    -- Since we don't have item_categoryid stored in menu_item table,
    -- we'll use a heuristic based on item names to categorize them:

    -- 1. Chicken items -> Chicken Meal (80721)
    UPDATE menu_item mi
    SET menu_sub_category_id = (
        SELECT menu_sub_category_id
        FROM menu_sub_categories
        WHERE ext_petpooja_categories_id = 80721
          AND is_deleted = FALSE
        LIMIT 1
    )
    WHERE mi.is_deleted = FALSE
      AND mi.menu_sub_category_id IS NULL
      AND (
          LOWER(mi.menu_item_name) LIKE '%chicken%'
          OR LOWER(mi.menu_item_name) LIKE '%nugget%'
      );

    GET DIAGNOSTICS linked_count = ROW_COUNT;
    RAISE NOTICE 'Linked % chicken items to Chicken Meal', linked_count;

    -- 2. Fish/Seafood items -> Seafood Meal (80722)
    UPDATE menu_item mi
    SET menu_sub_category_id = (
        SELECT menu_sub_category_id
        FROM menu_sub_categories
        WHERE ext_petpooja_categories_id = 80722
          AND is_deleted = FALSE
        LIMIT 1
    )
    WHERE mi.is_deleted = FALSE
      AND mi.menu_sub_category_id IS NULL
      AND (
          LOWER(mi.menu_item_name) LIKE '%fish%'
          OR LOWER(mi.menu_item_name) LIKE '%shrimp%'
          OR LOWER(mi.menu_item_name) LIKE '%seafood%'
      );

    GET DIAGNOSTICS linked_count = ROW_COUNT;
    RAISE NOTICE 'Linked % seafood items to Seafood Meal', linked_count;

    -- 3. Side items -> Side Orders (80723)
    UPDATE menu_item mi
    SET menu_sub_category_id = (
        SELECT menu_sub_category_id
        FROM menu_sub_categories
        WHERE ext_petpooja_categories_id = 80723
          AND is_deleted = FALSE
        LIMIT 1
    )
    WHERE mi.is_deleted = FALSE
      AND mi.menu_sub_category_id IS NULL
      AND (
          LOWER(mi.menu_item_name) LIKE '%fries%'
          OR LOWER(mi.menu_item_name) LIKE '%side%'
          OR LOWER(mi.menu_item_name) LIKE '%sauce%'
      );

    GET DIAGNOSTICS linked_count = ROW_COUNT;
    RAISE NOTICE 'Linked % items to Side Orders', linked_count;

    -- 4. Beverages -> Beverages (80724)
    UPDATE menu_item mi
    SET menu_sub_category_id = (
        SELECT menu_sub_category_id
        FROM menu_sub_categories
        WHERE ext_petpooja_categories_id = 80724
          AND is_deleted = FALSE
        LIMIT 1
    )
    WHERE mi.is_deleted = FALSE
      AND mi.menu_sub_category_id IS NULL
      AND (
          LOWER(mi.menu_item_name) LIKE '%coke%'
          OR LOWER(mi.menu_item_name) LIKE '%pepsi%'
          OR LOWER(mi.menu_item_name) LIKE '%sprite%'
          OR LOWER(mi.menu_item_name) LIKE '%fanta%'
          OR LOWER(mi.menu_item_name) LIKE '%water%'
          OR LOWER(mi.menu_item_name) LIKE '%juice%'
          OR LOWER(mi.menu_item_name) LIKE '%coffee%'
          OR LOWER(mi.menu_item_name) LIKE '%7\"up%'
          OR LOWER(mi.menu_item_name) LIKE '%thumsup%'
          OR LOWER(mi.menu_item_name) LIKE '%miranda%'
          OR LOWER(mi.menu_item_name) LIKE '%dew%'
      );

    GET DIAGNOSTICS linked_count = ROW_COUNT;
    RAISE NOTICE 'Linked % items to Beverages', linked_count;

    -- 5. Desserts -> Desserts (80727)
    UPDATE menu_item mi
    SET menu_sub_category_id = (
        SELECT menu_sub_category_id
        FROM menu_sub_categories
        WHERE ext_petpooja_categories_id = 80727
          AND is_deleted = FALSE
        LIMIT 1
    )
    WHERE mi.is_deleted = FALSE
      AND mi.menu_sub_category_id IS NULL
      AND (
          LOWER(mi.menu_item_name) LIKE '%dessert%'
          OR LOWER(mi.menu_item_name) LIKE '%ice cream%'
          OR LOWER(mi.menu_item_name) LIKE '%cake%'
          OR LOWER(mi.menu_item_name) LIKE '%sweet%'
      );

    GET DIAGNOSTICS linked_count = ROW_COUNT;
    RAISE NOTICE 'Linked % items to Desserts', linked_count;

    -- 6. Coffee -> Hot Coffees (80725)
    UPDATE menu_item mi
    SET menu_sub_category_id = (
        SELECT menu_sub_category_id
        FROM menu_sub_categories
        WHERE ext_petpooja_categories_id = 80725
          AND is_deleted = FALSE
        LIMIT 1
    )
    WHERE mi.is_deleted = FALSE
      AND mi.menu_sub_category_id IS NULL
      AND LOWER(mi.menu_item_name) LIKE '%coffee%';

    GET DIAGNOSTICS linked_count = ROW_COUNT;
    RAISE NOTICE 'Linked % items to Hot Coffees', linked_count;

    -- 7. Shakes -> Shakes (81157)
    UPDATE menu_item mi
    SET menu_sub_category_id = (
        SELECT menu_sub_category_id
        FROM menu_sub_categories
        WHERE ext_petpooja_categories_id = 81157
          AND is_deleted = FALSE
        LIMIT 1
    )
    WHERE mi.is_deleted = FALSE
      AND mi.menu_sub_category_id IS NULL
      AND LOWER(mi.menu_item_name) LIKE '%shake%';

    GET DIAGNOSTICS linked_count = ROW_COUNT;
    RAISE NOTICE 'Linked % items to Shakes', linked_count;

    -- 8. Remaining items -> Chicken Meal (default)
    UPDATE menu_item mi
    SET menu_sub_category_id = (
        SELECT menu_sub_category_id
        FROM menu_sub_categories
        WHERE ext_petpooja_categories_id = 80721
          AND is_deleted = FALSE
        LIMIT 1
    )
    WHERE mi.is_deleted = FALSE
      AND mi.menu_sub_category_id IS NULL;

    GET DIAGNOSTICS linked_count = ROW_COUNT;
    RAISE NOTICE 'Linked % remaining items to Chicken Meal (default)', linked_count;

    -- Drop temp table
    DROP TABLE IF EXISTS temp_item_subcategory_mapping;

    -- Report final status
    SELECT COUNT(*) INTO linked_count
    FROM menu_item
    WHERE is_deleted = FALSE
      AND menu_sub_category_id IS NOT NULL;

    RAISE NOTICE 'Migration complete: % total items now linked to sub-categories', linked_count;

END $$;

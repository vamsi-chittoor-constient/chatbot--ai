-- ============================================================================
-- Migration: Populate Cuisine Mappings from Menu Item Names
-- ============================================================================
-- Purpose: Map menu items to cuisines based on item name patterns
-- Date: 2025-12-28
-- ============================================================================

DO $$
DECLARE
    v_continental_id UUID;
    v_chinese_id UUID;
    v_italian_id UUID;
    v_american_id UUID;
    v_south_indian_id UUID;
    v_north_indian_id UUID;
    v_street_food_id UUID;
    v_thai_id UUID;
    v_mexican_id UUID;
    v_japanese_id UUID;
    v_fast_food_id UUID;
    v_beverages_id UUID;
    v_desserts_id UUID;
    v_bakery_id UUID;
BEGIN
    -- Get cuisine IDs
    SELECT cuisine_id INTO v_continental_id FROM cuisines WHERE cuisine_name = 'Continental';
    SELECT cuisine_id INTO v_chinese_id FROM cuisines WHERE cuisine_name = 'Chinese';
    SELECT cuisine_id INTO v_italian_id FROM cuisines WHERE cuisine_name = 'Italian';
    SELECT cuisine_id INTO v_american_id FROM cuisines WHERE cuisine_name = 'American';
    SELECT cuisine_id INTO v_south_indian_id FROM cuisines WHERE cuisine_name = 'South Indian';
    SELECT cuisine_id INTO v_north_indian_id FROM cuisines WHERE cuisine_name = 'North Indian';
    SELECT cuisine_id INTO v_street_food_id FROM cuisines WHERE cuisine_name = 'Street Food';
    SELECT cuisine_id INTO v_thai_id FROM cuisines WHERE cuisine_name = 'Thai';
    SELECT cuisine_id INTO v_mexican_id FROM cuisines WHERE cuisine_name = 'Mexican';
    SELECT cuisine_id INTO v_japanese_id FROM cuisines WHERE cuisine_name = 'Japanese';
    SELECT cuisine_id INTO v_fast_food_id FROM cuisines WHERE cuisine_name = 'Fast Food';
    SELECT cuisine_id INTO v_beverages_id FROM cuisines WHERE cuisine_name = 'Beverages';
    SELECT cuisine_id INTO v_desserts_id FROM cuisines WHERE cuisine_name = 'Desserts';
    SELECT cuisine_id INTO v_bakery_id FROM cuisines WHERE cuisine_name = 'Bakery';

    RAISE NOTICE 'Populating cuisine mappings...';

    -- ========================================================================
    -- CONTINENTAL CUISINE
    -- ========================================================================
    INSERT INTO menu_item_cuisine_mapping (menu_item_id, cuisine_id, created_at, updated_at)
    SELECT DISTINCT mi.menu_item_id, v_continental_id, NOW(), NOW()
    FROM menu_item mi
    WHERE mi.is_deleted = FALSE
      AND mi.menu_item_in_stock = TRUE
      AND (
          mi.menu_item_name ILIKE '%burger%'
          OR mi.menu_item_name ILIKE '%sandwich%'
          OR mi.menu_item_name ILIKE '%fries%'
          OR mi.menu_item_name ILIKE '%steak%'
          OR mi.menu_item_name ILIKE '%grilled%'
      )
      AND NOT EXISTS (
          SELECT 1 FROM menu_item_cuisine_mapping micm
          WHERE micm.menu_item_id = mi.menu_item_id
            AND micm.cuisine_id = v_continental_id
            AND micm.is_deleted = FALSE
      );

    -- ========================================================================
    -- ITALIAN CUISINE
    -- ========================================================================
    INSERT INTO menu_item_cuisine_mapping (menu_item_id, cuisine_id, created_at, updated_at)
    SELECT DISTINCT mi.menu_item_id, v_italian_id, NOW(), NOW()
    FROM menu_item mi
    WHERE mi.is_deleted = FALSE
      AND mi.menu_item_in_stock = TRUE
      AND (
          mi.menu_item_name ILIKE '%pizza%'
          OR mi.menu_item_name ILIKE '%pasta%'
          OR mi.menu_item_name ILIKE '%margherita%'
          OR mi.menu_item_name ILIKE '%lasagna%'
          OR mi.menu_item_name ILIKE '%spaghetti%'
          OR mi.menu_item_name ILIKE '%penne%'
          OR mi.menu_item_name ILIKE '%ravioli%'
      )
      AND NOT EXISTS (
          SELECT 1 FROM menu_item_cuisine_mapping micm
          WHERE micm.menu_item_id = mi.menu_item_id
            AND micm.cuisine_id = v_italian_id
            AND micm.is_deleted = FALSE
      );

    -- ========================================================================
    -- CHINESE CUISINE
    -- ========================================================================
    INSERT INTO menu_item_cuisine_mapping (menu_item_id, cuisine_id, created_at, updated_at)
    SELECT DISTINCT mi.menu_item_id, v_chinese_id, NOW(), NOW()
    FROM menu_item mi
    WHERE mi.is_deleted = FALSE
      AND mi.menu_item_in_stock = TRUE
      AND (
          mi.menu_item_name ILIKE '%noodles%'
          OR mi.menu_item_name ILIKE '%fried rice%'
          OR mi.menu_item_name ILIKE '%manchurian%'
          OR mi.menu_item_name ILIKE '%schezwan%'
          OR mi.menu_item_name ILIKE '%szechuan%'
          OR mi.menu_item_name ILIKE '%chowmein%'
          OR mi.menu_item_name ILIKE '%hakka%'
          OR mi.menu_item_name ILIKE '%spring roll%'
          OR mi.menu_item_name ILIKE '%sweet and sour%'
          OR mi.menu_item_name ILIKE '%dim sum%'
      )
      AND NOT EXISTS (
          SELECT 1 FROM menu_item_cuisine_mapping micm
          WHERE micm.menu_item_id = mi.menu_item_id
            AND micm.cuisine_id = v_chinese_id
            AND micm.is_deleted = FALSE
      );

    -- ========================================================================
    -- SOUTH INDIAN CUISINE
    -- ========================================================================
    INSERT INTO menu_item_cuisine_mapping (menu_item_id, cuisine_id, created_at, updated_at)
    SELECT DISTINCT mi.menu_item_id, v_south_indian_id, NOW(), NOW()
    FROM menu_item mi
    WHERE mi.is_deleted = FALSE
      AND mi.menu_item_in_stock = TRUE
      AND (
          mi.menu_item_name ILIKE '%dosa%'
          OR mi.menu_item_name ILIKE '%idli%'
          OR mi.menu_item_name ILIKE '%vada%'
          OR mi.menu_item_name ILIKE '%uttapam%'
          OR mi.menu_item_name ILIKE '%appam%'
          OR mi.menu_item_name ILIKE '%pongal%'
          OR mi.menu_item_name ILIKE '%sambar%'
          OR mi.menu_item_name ILIKE '%rasam%'
      )
      AND NOT EXISTS (
          SELECT 1 FROM menu_item_cuisine_mapping micm
          WHERE micm.menu_item_id = mi.menu_item_id
            AND micm.cuisine_id = v_south_indian_id
            AND micm.is_deleted = FALSE
      );

    -- ========================================================================
    -- NORTH INDIAN CUISINE
    -- ========================================================================
    INSERT INTO menu_item_cuisine_mapping (menu_item_id, cuisine_id, created_at, updated_at)
    SELECT DISTINCT mi.menu_item_id, v_north_indian_id, NOW(), NOW()
    FROM menu_item mi
    WHERE mi.is_deleted = FALSE
      AND mi.menu_item_in_stock = TRUE
      AND (
          mi.menu_item_name ILIKE '%paneer%'
          OR mi.menu_item_name ILIKE '%butter chicken%'
          OR mi.menu_item_name ILIKE '%dal%'
          OR mi.menu_item_name ILIKE '%naan%'
          OR mi.menu_item_name ILIKE '%roti%'
          OR mi.menu_item_name ILIKE '%paratha%'
          OR mi.menu_item_name ILIKE '%tandoori%'
          OR mi.menu_item_name ILIKE '%biryani%'
          OR mi.menu_item_name ILIKE '%korma%'
      )
      AND NOT EXISTS (
          SELECT 1 FROM menu_item_cuisine_mapping micm
          WHERE micm.menu_item_id = mi.menu_item_id
            AND micm.cuisine_id = v_north_indian_id
            AND micm.is_deleted = FALSE
      );

    -- ========================================================================
    -- THAI CUISINE
    -- ========================================================================
    INSERT INTO menu_item_cuisine_mapping (menu_item_id, cuisine_id, created_at, updated_at)
    SELECT DISTINCT mi.menu_item_id, v_thai_id, NOW(), NOW()
    FROM menu_item mi
    WHERE mi.is_deleted = FALSE
      AND mi.menu_item_in_stock = TRUE
      AND (
          mi.menu_item_name ILIKE '%thai%'
          OR mi.menu_item_name ILIKE '%tom yum%'
          OR mi.menu_item_name ILIKE '%pad thai%'
          OR mi.menu_item_name ILIKE '%green curry%'
          OR mi.menu_item_name ILIKE '%red curry%'
      )
      AND NOT EXISTS (
          SELECT 1 FROM menu_item_cuisine_mapping micm
          WHERE micm.menu_item_id = mi.menu_item_id
            AND micm.cuisine_id = v_thai_id
            AND micm.is_deleted = FALSE
      );

    -- ========================================================================
    -- MEXICAN CUISINE
    -- ========================================================================
    INSERT INTO menu_item_cuisine_mapping (menu_item_id, cuisine_id, created_at, updated_at)
    SELECT DISTINCT mi.menu_item_id, v_mexican_id, NOW(), NOW()
    FROM menu_item mi
    WHERE mi.is_deleted = FALSE
      AND mi.menu_item_in_stock = TRUE
      AND (
          mi.menu_item_name ILIKE '%taco%'
          OR mi.menu_item_name ILIKE '%burrito%'
          OR mi.menu_item_name ILIKE '%quesadilla%'
          OR mi.menu_item_name ILIKE '%nachos%'
          OR mi.menu_item_name ILIKE '%fajita%'
      )
      AND NOT EXISTS (
          SELECT 1 FROM menu_item_cuisine_mapping micm
          WHERE micm.menu_item_id = mi.menu_item_id
            AND micm.cuisine_id = v_mexican_id
            AND micm.is_deleted = FALSE
      );

    -- ========================================================================
    -- JAPANESE CUISINE
    -- ========================================================================
    INSERT INTO menu_item_cuisine_mapping (menu_item_id, cuisine_id, created_at, updated_at)
    SELECT DISTINCT mi.menu_item_id, v_japanese_id, NOW(), NOW()
    FROM menu_item mi
    WHERE mi.is_deleted = FALSE
      AND mi.menu_item_in_stock = TRUE
      AND (
          mi.menu_item_name ILIKE '%sushi%'
          OR mi.menu_item_name ILIKE '%ramen%'
          OR mi.menu_item_name ILIKE '%tempura%'
          OR mi.menu_item_name ILIKE '%teriyaki%'
      )
      AND NOT EXISTS (
          SELECT 1 FROM menu_item_cuisine_mapping micm
          WHERE micm.menu_item_id = mi.menu_item_id
            AND micm.cuisine_id = v_japanese_id
            AND micm.is_deleted = FALSE
      );

    -- ========================================================================
    -- BEVERAGES
    -- ========================================================================
    INSERT INTO menu_item_cuisine_mapping (menu_item_id, cuisine_id, created_at, updated_at)
    SELECT DISTINCT mi.menu_item_id, v_beverages_id, NOW(), NOW()
    FROM menu_item mi
    WHERE mi.is_deleted = FALSE
      AND mi.menu_item_in_stock = TRUE
      AND (
          mi.menu_item_name ILIKE '%coffee%'
          OR mi.menu_item_name ILIKE '%tea%'
          OR mi.menu_item_name ILIKE '%juice%'
          OR mi.menu_item_name ILIKE '%shake%'
          OR mi.menu_item_name ILIKE '%smoothie%'
          OR mi.menu_item_name ILIKE '%soda%'
          OR mi.menu_item_name ILIKE '%water%'
          OR mi.menu_item_name ILIKE '%drink%'
          OR mi.menu_item_name ILIKE '%lemonade%'
          OR mi.menu_item_name ILIKE '%lassi%'
      )
      AND NOT EXISTS (
          SELECT 1 FROM menu_item_cuisine_mapping micm
          WHERE micm.menu_item_id = mi.menu_item_id
            AND micm.cuisine_id = v_beverages_id
            AND micm.is_deleted = FALSE
      );

    -- ========================================================================
    -- DESSERTS
    -- ========================================================================
    INSERT INTO menu_item_cuisine_mapping (menu_item_id, cuisine_id, created_at, updated_at)
    SELECT DISTINCT mi.menu_item_id, v_desserts_id, NOW(), NOW()
    FROM menu_item mi
    WHERE mi.is_deleted = FALSE
      AND mi.menu_item_in_stock = TRUE
      AND (
          mi.menu_item_name ILIKE '%cake%'
          OR mi.menu_item_name ILIKE '%ice cream%'
          OR mi.menu_item_name ILIKE '%pastry%'
          OR mi.menu_item_name ILIKE '%brownie%'
          OR mi.menu_item_name ILIKE '%cookie%'
          OR mi.menu_item_name ILIKE '%pudding%'
          OR mi.menu_item_name ILIKE '%mousse%'
          OR mi.menu_item_name ILIKE '%tart%'
          OR mi.menu_item_name ILIKE '%gulab jamun%'
          OR mi.menu_item_name ILIKE '%rasgulla%'
      )
      AND NOT EXISTS (
          SELECT 1 FROM menu_item_cuisine_mapping micm
          WHERE micm.menu_item_id = mi.menu_item_id
            AND micm.cuisine_id = v_desserts_id
            AND micm.is_deleted = FALSE
      );

    RAISE NOTICE 'Cuisine mappings populated successfully!';

END $$;

-- ============================================================================
-- Verification Queries
-- ============================================================================

-- Count items by cuisine
SELECT c.cuisine_name, COUNT(DISTINCT micm.menu_item_id) as item_count
FROM cuisines c
LEFT JOIN menu_item_cuisine_mapping micm ON c.cuisine_id = micm.cuisine_id
  AND micm.is_deleted = FALSE
WHERE c.is_deleted = FALSE
GROUP BY c.cuisine_name
ORDER BY item_count DESC, c.cuisine_name;

-- Sample items per cuisine (top 5)
SELECT c.cuisine_name, mi.menu_item_name
FROM menu_item_cuisine_mapping micm
JOIN cuisines c ON micm.cuisine_id = c.cuisine_id
JOIN menu_item mi ON micm.menu_item_id = mi.menu_item_id
WHERE micm.is_deleted = FALSE
  AND c.cuisine_name IN ('Italian', 'Chinese', 'Continental', 'South Indian')
ORDER BY c.cuisine_name, mi.menu_item_name
LIMIT 20;

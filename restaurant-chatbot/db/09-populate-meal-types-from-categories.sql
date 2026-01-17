-- ============================================================================
-- Migration: Populate Meal Types from Category Names
-- ============================================================================
-- Purpose: Assign meal periods to all menu items based on their categories
-- Date: 2025-12-28
-- ============================================================================

-- First, get the meal_type IDs
DO $$
DECLARE
    breakfast_id UUID;
    lunch_id UUID;
    dinner_id UUID;
    all_day_id UUID;
BEGIN
    -- Get meal_type UUIDs
    SELECT meal_type_id INTO breakfast_id FROM meal_type WHERE meal_type_name = 'Breakfast';
    SELECT meal_type_id INTO lunch_id FROM meal_type WHERE meal_type_name = 'Lunch';
    SELECT meal_type_id INTO dinner_id FROM meal_type WHERE meal_type_name = 'Dinner';
    SELECT meal_type_id INTO all_day_id FROM meal_type WHERE meal_type_name = 'All Day';

    -- ===========================================================================
    -- BREAKFAST ITEMS (6 AM - 11 AM)
    -- ===========================================================================
    -- Category: "tiffin" = Traditional South Indian breakfast items

    INSERT INTO menu_item_availability_schedule (
        schedule_id, menu_item_id, meal_type_id, day_of_week,
        time_from, time_to, is_available, created_at, updated_at
    )
    SELECT
        gen_random_uuid(),
        mi.menu_item_id,
        breakfast_id,
        'All',
        '06:00:00'::time,
        '11:00:00'::time,
        TRUE,
        NOW(),
        NOW()
    FROM menu_item mi
    JOIN menu_item_category_mapping micm ON mi.menu_item_id = micm.menu_item_id
    JOIN menu_categories mc ON micm.menu_category_id = mc.menu_category_id
    WHERE mc.menu_category_name ILIKE 'tiffin'
    AND mi.is_deleted = FALSE
    AND micm.is_deleted = FALSE
    AND mc.is_deleted = FALSE
    -- Don't insert duplicates
    AND NOT EXISTS (
        SELECT 1 FROM menu_item_availability_schedule mas
        WHERE mas.menu_item_id = mi.menu_item_id
        AND mas.meal_type_id = breakfast_id
        AND mas.is_deleted = FALSE
    );

    -- ===========================================================================
    -- LUNCH & DINNER ITEMS (11 AM - 10 PM)
    -- ===========================================================================
    -- Categories: "main course", "rice dishes", "starters"

    -- Insert LUNCH availability (11 AM - 4 PM)
    INSERT INTO menu_item_availability_schedule (
        schedule_id, menu_item_id, meal_type_id, day_of_week,
        time_from, time_to, is_available, created_at, updated_at
    )
    SELECT
        gen_random_uuid(),
        mi.menu_item_id,
        lunch_id,
        'All',
        '11:00:00'::time,
        '16:00:00'::time,
        TRUE,
        NOW(),
        NOW()
    FROM menu_item mi
    JOIN menu_item_category_mapping micm ON mi.menu_item_id = micm.menu_item_id
    JOIN menu_categories mc ON micm.menu_category_id = mc.menu_category_id
    WHERE mc.menu_category_name ILIKE ANY(ARRAY['main course', 'rice dishes', 'starters'])
    AND mi.is_deleted = FALSE
    AND micm.is_deleted = FALSE
    AND mc.is_deleted = FALSE
    AND NOT EXISTS (
        SELECT 1 FROM menu_item_availability_schedule mas
        WHERE mas.menu_item_id = mi.menu_item_id
        AND mas.meal_type_id = lunch_id
        AND mas.is_deleted = FALSE
    );

    -- Insert DINNER availability (4 PM - 10 PM)
    INSERT INTO menu_item_availability_schedule (
        schedule_id, menu_item_id, meal_type_id, day_of_week,
        time_from, time_to, is_available, created_at, updated_at
    )
    SELECT
        gen_random_uuid(),
        mi.menu_item_id,
        dinner_id,
        'All',
        '16:00:00'::time,
        '22:00:00'::time,
        TRUE,
        NOW(),
        NOW()
    FROM menu_item mi
    JOIN menu_item_category_mapping micm ON mi.menu_item_id = micm.menu_item_id
    JOIN menu_categories mc ON micm.menu_category_id = mc.menu_category_id
    WHERE mc.menu_category_name ILIKE ANY(ARRAY['main course', 'rice dishes', 'starters'])
    AND mi.is_deleted = FALSE
    AND micm.is_deleted = FALSE
    AND mc.is_deleted = FALSE
    AND NOT EXISTS (
        SELECT 1 FROM menu_item_availability_schedule mas
        WHERE mas.menu_item_id = mi.menu_item_id
        AND mas.meal_type_id = dinner_id
        AND mas.is_deleted = FALSE
    );

    -- ===========================================================================
    -- ALL DAY ITEMS (6 AM - 10 PM)
    -- ===========================================================================
    -- Categories: "snacks", "beverages", "desserts", "add-ons"

    INSERT INTO menu_item_availability_schedule (
        schedule_id, menu_item_id, meal_type_id, day_of_week,
        time_from, time_to, is_available, created_at, updated_at
    )
    SELECT
        gen_random_uuid(),
        mi.menu_item_id,
        all_day_id,
        'All',
        '06:00:00'::time,
        '22:00:00'::time,
        TRUE,
        NOW(),
        NOW()
    FROM menu_item mi
    JOIN menu_item_category_mapping micm ON mi.menu_item_id = micm.menu_item_id
    JOIN menu_categories mc ON micm.menu_category_id = mc.menu_category_id
    WHERE mc.menu_category_name ILIKE ANY(ARRAY['snacks', 'beverages', 'desserts', 'add-ons'])
    AND mi.is_deleted = FALSE
    AND micm.is_deleted = FALSE
    AND mc.is_deleted = FALSE
    AND NOT EXISTS (
        SELECT 1 FROM menu_item_availability_schedule mas
        WHERE mas.menu_item_id = mi.menu_item_id
        AND mas.meal_type_id = all_day_id
        AND mas.is_deleted = FALSE
    );

    -- Log results
    RAISE NOTICE 'Meal type population complete!';
    RAISE NOTICE 'Run verification queries to check results.';
END $$;

-- ============================================================================
-- Verification Queries
-- ============================================================================

-- Count items by meal type
SELECT mt.meal_type_name, COUNT(DISTINCT mas.menu_item_id) as item_count
FROM menu_item_availability_schedule mas
JOIN meal_type mt ON mas.meal_type_id = mt.meal_type_id
WHERE mas.is_deleted = FALSE
GROUP BY mt.meal_type_name
ORDER BY meal_type_name;

-- Sample items per category
SELECT mc.menu_category_name,
       COUNT(DISTINCT mi.menu_item_id) as total_items,
       COUNT(DISTINCT mas.menu_item_id) as items_with_meal_types
FROM menu_categories mc
LEFT JOIN menu_item_category_mapping micm ON mc.menu_category_id = micm.menu_category_id
LEFT JOIN menu_item mi ON micm.menu_item_id = mi.menu_item_id AND mi.is_deleted = FALSE
LEFT JOIN menu_item_availability_schedule mas ON mi.menu_item_id = mas.menu_item_id AND mas.is_deleted = FALSE
WHERE mc.is_deleted = FALSE
GROUP BY mc.menu_category_name
ORDER BY total_items DESC;

-- ============================================================================

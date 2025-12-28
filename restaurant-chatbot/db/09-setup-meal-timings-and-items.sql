-- ============================================================================
-- Migration: Setup Meal Timings and Assign Items to Meal Periods
-- ============================================================================
-- Purpose: Configure meal slot timings and intelligently assign menu items
-- Date: 2025-12-28
-- ============================================================================

-- Step 1: Get meal type IDs
DO $$
DECLARE
    breakfast_id UUID;
    lunch_id UUID;
    dinner_id UUID;
    all_day_id UUID;
    snacks_id UUID;
    slot_config UUID;
BEGIN
    -- Get meal type IDs
    SELECT meal_type_id INTO breakfast_id FROM meal_type WHERE meal_type_name = 'Breakfast' AND is_deleted = FALSE;
    SELECT meal_type_id INTO lunch_id FROM meal_type WHERE meal_type_name = 'Lunch' AND is_deleted = FALSE;
    SELECT meal_type_id INTO dinner_id FROM meal_type WHERE meal_type_name = 'Dinner' AND is_deleted = FALSE;
    SELECT meal_type_id INTO all_day_id FROM meal_type WHERE meal_type_name = 'All Day' AND is_deleted = FALSE;
    SELECT meal_type_id INTO snacks_id FROM meal_type WHERE meal_type_name = 'Snacks' AND is_deleted = FALSE;

    -- Get or create a default slot config (for the restaurant)
    SELECT slot_config_id INTO slot_config
    FROM entity_slot_config
    WHERE is_deleted = FALSE
    LIMIT 1;

    -- If no slot config exists, we'll create meal timings without it (slot_config_id can be NULL)

    -- Step 2: Setup meal timings (if not already exists)
    IF breakfast_id IS NOT NULL THEN
        INSERT INTO meal_slot_timing (meal_type_id, opening_time, closing_time, is_active, slot_config_id)
        VALUES (breakfast_id, '06:00:00', '11:00:00', TRUE, slot_config)
        ON CONFLICT DO NOTHING;
    END IF;

    IF lunch_id IS NOT NULL THEN
        INSERT INTO meal_slot_timing (meal_type_id, opening_time, closing_time, is_active, slot_config_id)
        VALUES (lunch_id, '11:00:00', '16:00:00', TRUE, slot_config)
        ON CONFLICT DO NOTHING;
    END IF;

    IF dinner_id IS NOT NULL THEN
        INSERT INTO meal_slot_timing (meal_type_id, opening_time, closing_time, is_active, slot_config_id)
        VALUES (dinner_id, '16:00:00', '23:00:00', TRUE, slot_config)
        ON CONFLICT DO NOTHING;
    END IF;

    -- Step 3: Assign items to meal periods based on item type
    -- Strategy: Most items available for Lunch & Dinner, Beverages all day

    -- Breakfast items (empty for now - no typical breakfast items in menu)
    -- Future: Add pancakes, eggs, etc. when available

    -- Lunch & Dinner: Burgers, Sandwiches, Main dishes
    INSERT INTO menu_item_availability_schedule (menu_item_id, meal_type_id, is_available, is_deleted)
    SELECT
        mi.menu_item_id,
        lunch_id,
        TRUE,
        FALSE
    FROM menu_item mi
    WHERE mi.is_deleted = FALSE
    AND mi.menu_item_status = 'active'
    AND (
        LOWER(mi.menu_item_name) LIKE '%burger%' OR
        LOWER(mi.menu_item_name) LIKE '%sandwich%' OR
        LOWER(mi.menu_item_name) LIKE '%chicken%' OR
        LOWER(mi.menu_item_name) LIKE '%fish%' OR
        LOWER(mi.menu_item_name) LIKE '%baik%' OR
        LOWER(mi.menu_item_name) LIKE '%shrimp%' OR
        LOWER(mi.menu_item_name) LIKE '%fries%' OR
        LOWER(mi.menu_item_name) LIKE '%nugget%' OR
        LOWER(mi.menu_item_name) LIKE '%salad%'
    )
    ON CONFLICT DO NOTHING;

    INSERT INTO menu_item_availability_schedule (menu_item_id, meal_type_id, is_available, is_deleted)
    SELECT
        mi.menu_item_id,
        dinner_id,
        TRUE,
        FALSE
    FROM menu_item mi
    WHERE mi.is_deleted = FALSE
    AND mi.menu_item_status = 'active'
    AND (
        LOWER(mi.menu_item_name) LIKE '%burger%' OR
        LOWER(mi.menu_item_name) LIKE '%sandwich%' OR
        LOWER(mi.menu_item_name) LIKE '%chicken%' OR
        LOWER(mi.menu_item_name) LIKE '%fish%' OR
        LOWER(mi.menu_item_name) LIKE '%baik%' OR
        LOWER(mi.menu_item_name) LIKE '%shrimp%' OR
        LOWER(mi.menu_item_name) LIKE '%fries%' OR
        LOWER(mi.menu_item_name) LIKE '%nugget%' OR
        LOWER(mi.menu_item_name) LIKE '%salad%'
    )
    ON CONFLICT DO NOTHING;

    -- All Day: Beverages, sides, sauces
    INSERT INTO menu_item_availability_schedule (menu_item_id, meal_type_id, is_available, is_deleted)
    SELECT
        mi.menu_item_id,
        all_day_id,
        TRUE,
        FALSE
    FROM menu_item mi
    WHERE mi.is_deleted = FALSE
    AND mi.menu_item_status = 'active'
    AND (
        LOWER(mi.menu_item_name) LIKE '%coke%' OR
        LOWER(mi.menu_item_name) LIKE '%pepsi%' OR
        LOWER(mi.menu_item_name) LIKE '%sprite%' OR
        LOWER(mi.menu_item_name) LIKE '%fanta%' OR
        LOWER(mi.menu_item_name) LIKE '%water%' OR
        LOWER(mi.menu_item_name) LIKE '%juice%' OR
        LOWER(mi.menu_item_name) LIKE '%coffee%' OR
        LOWER(mi.menu_item_name) LIKE '%sauce%' OR
        LOWER(mi.menu_item_name) LIKE '%ice%' OR
        LOWER(mi.menu_item_name) LIKE '%7"up%' OR
        LOWER(mi.menu_item_name) LIKE '%thumsup%' OR
        LOWER(mi.menu_item_name) LIKE '%miranda%' OR
        LOWER(mi.menu_item_name) LIKE '%dew%'
    )
    ON CONFLICT DO NOTHING;

    RAISE NOTICE 'Meal timings and item assignments completed successfully';
END $$;

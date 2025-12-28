-- ============================================================================
-- Migration: Parse PetPooja Category Timings and Map to Meal Types
-- ============================================================================
-- Purpose: Parse JSON timings from PetPooja and assign items to meal periods
-- Date: 2025-12-28
-- ============================================================================

DO $$
DECLARE
    breakfast_id UUID;
    lunch_id UUID;
    dinner_id UUID;
    all_day_id UUID;
    subcategory_record RECORD;
    timing_json JSONB;
    time_slot JSONB;
    start_time TIME;
    end_time TIME;
    assigned_meal_type UUID;
BEGIN
    -- Get meal type IDs
    SELECT meal_type_id INTO breakfast_id FROM meal_type WHERE meal_type_name = 'Breakfast' AND is_deleted = FALSE;
    SELECT meal_type_id INTO lunch_id FROM meal_type WHERE meal_type_name = 'Lunch' AND is_deleted = FALSE;
    SELECT meal_type_id INTO dinner_id FROM meal_type WHERE meal_type_name = 'Dinner' AND is_deleted = FALSE;
    SELECT meal_type_id INTO all_day_id FROM meal_type WHERE meal_type_name = 'All Day' AND is_deleted = FALSE;

    -- Loop through sub-categories with timing data
    FOR subcategory_record IN
        SELECT menu_sub_category_id, sub_category_name, sub_category_timings
        FROM menu_sub_categories
        WHERE is_deleted = FALSE
        AND sub_category_timings IS NOT NULL
        AND sub_category_timings != ''
        AND sub_category_timings != '[]'
    LOOP
        BEGIN
            -- Parse JSON timing data
            timing_json := subcategory_record.sub_category_timings::JSONB;

            -- Extract time slots (PetPooja format: array of schedule objects)
            FOR time_slot IN
                SELECT jsonb_array_elements(
                    (jsonb_array_elements(timing_json) -> 'schedule_time_slots')
                ) AS slot
            LOOP
                -- Get start and end times
                start_time := (time_slot ->> 'start_time')::TIME;
                end_time := (time_slot ->> 'end_time')::TIME;

                -- Map to meal type based on time ranges
                -- Breakfast: 05:00-11:00
                -- Lunch: 11:00-16:00
                -- Dinner: 16:00-23:59
                -- Default: All Day

                IF start_time >= '05:00' AND end_time <= '11:00' THEN
                    assigned_meal_type := breakfast_id;
                ELSIF start_time >= '11:00' AND end_time <= '16:00' THEN
                    assigned_meal_type := lunch_id;
                ELSIF start_time >= '16:00' OR end_time >= '16:00' THEN
                    assigned_meal_type := dinner_id;
                ELSE
                    assigned_meal_type := all_day_id;
                END IF;

                -- Assign all items in this sub-category to the meal type
                INSERT INTO menu_item_availability_schedule (menu_item_id, meal_type_id, is_available, is_deleted)
                SELECT
                    mi.menu_item_id,
                    assigned_meal_type,
                    TRUE,
                    FALSE
                FROM menu_item mi
                WHERE mi.menu_sub_category_id = subcategory_record.menu_sub_category_id
                AND mi.is_deleted = FALSE
                AND mi.menu_item_status = 'active'
                ON CONFLICT DO NOTHING;

                RAISE NOTICE 'Mapped sub-category % (%-%) to meal type',
                    subcategory_record.sub_category_name,
                    start_time,
                    end_time;
            END LOOP;

        EXCEPTION
            WHEN OTHERS THEN
                RAISE NOTICE 'Failed to parse timing for sub-category %: %',
                    subcategory_record.sub_category_name,
                    SQLERRM;
                CONTINUE;
        END;
    END LOOP;

    RAISE NOTICE 'PetPooja timing parsing completed';
END $$;

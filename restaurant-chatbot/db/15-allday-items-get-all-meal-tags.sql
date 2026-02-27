-- ============================================================================
-- Migration 15: Items with "All Day" tag (or no tags) get Breakfast+Lunch+Dinner
-- ============================================================================
-- Problem: Items tagged only as "All Day" or with no availability schedule
-- get excluded by meal period filters because they lack specific meal type tags.
--
-- Fix: For every item that has an "All Day" schedule entry OR has no schedule
-- entries at all, insert Breakfast, Lunch, and Dinner schedule rows.
-- This way any meal period filter naturally includes them.
-- ============================================================================

-- Meal type IDs (from meal_type table)
-- Breakfast: d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d
-- Lunch:     871a4f82-77b0-4209-9805-41364b6fcbf9
-- Dinner:    78f1d95f-fbda-414c-aa18-d1a5dc1f1be1
-- All Day:   00bc0862-4a2e-4cf4-b80c-12167bed1638

BEGIN;

-- Step 1: Find all menu items that have "All Day" schedule entries
-- and add Breakfast/Lunch/Dinner entries if they don't already have them.

-- Add Breakfast tag to items with "All Day" tag (if not already tagged)
INSERT INTO menu_item_availability_schedule
    (schedule_id, menu_item_id, day_of_week, time_from, time_to, is_available,
     created_at, updated_at, is_deleted, meal_type_id)
SELECT
    gen_random_uuid(),
    mas.menu_item_id,
    NULL,  -- all days
    '06:00:00', '11:00:00',  -- breakfast hours
    true,
    NOW(), NOW(), false,
    'd44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d'  -- Breakfast
FROM menu_item_availability_schedule mas
WHERE mas.meal_type_id = '00bc0862-4a2e-4cf4-b80c-12167bed1638'  -- All Day
  AND mas.is_deleted = false
  AND mas.menu_item_id NOT IN (
      SELECT menu_item_id FROM menu_item_availability_schedule
      WHERE meal_type_id = 'd44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d'
        AND is_deleted = false
  );

-- Add Lunch tag to items with "All Day" tag (if not already tagged)
INSERT INTO menu_item_availability_schedule
    (schedule_id, menu_item_id, day_of_week, time_from, time_to, is_available,
     created_at, updated_at, is_deleted, meal_type_id)
SELECT
    gen_random_uuid(),
    mas.menu_item_id,
    NULL,
    '11:00:00', '16:00:00',  -- lunch hours
    true,
    NOW(), NOW(), false,
    '871a4f82-77b0-4209-9805-41364b6fcbf9'  -- Lunch
FROM menu_item_availability_schedule mas
WHERE mas.meal_type_id = '00bc0862-4a2e-4cf4-b80c-12167bed1638'
  AND mas.is_deleted = false
  AND mas.menu_item_id NOT IN (
      SELECT menu_item_id FROM menu_item_availability_schedule
      WHERE meal_type_id = '871a4f82-77b0-4209-9805-41364b6fcbf9'
        AND is_deleted = false
  );

-- Add Dinner tag to items with "All Day" tag (if not already tagged)
INSERT INTO menu_item_availability_schedule
    (schedule_id, menu_item_id, day_of_week, time_from, time_to, is_available,
     created_at, updated_at, is_deleted, meal_type_id)
SELECT
    gen_random_uuid(),
    mas.menu_item_id,
    NULL,
    '16:00:00', '23:00:00',  -- dinner hours
    true,
    NOW(), NOW(), false,
    '78f1d95f-fbda-414c-aa18-d1a5dc1f1be1'  -- Dinner
FROM menu_item_availability_schedule mas
WHERE mas.meal_type_id = '00bc0862-4a2e-4cf4-b80c-12167bed1638'
  AND mas.is_deleted = false
  AND mas.menu_item_id NOT IN (
      SELECT menu_item_id FROM menu_item_availability_schedule
      WHERE meal_type_id = '78f1d95f-fbda-414c-aa18-d1a5dc1f1be1'
        AND is_deleted = false
  );

-- Step 2: Items with NO schedule entries at all — add all 4 meal type tags.
-- These items default to ["All Day"] in Python code but have no DB rows.

INSERT INTO menu_item_availability_schedule
    (schedule_id, menu_item_id, day_of_week, time_from, time_to, is_available,
     created_at, updated_at, is_deleted, meal_type_id)
SELECT
    gen_random_uuid(),
    mi.menu_item_id,
    NULL,
    mt.time_from,
    mt.time_to,
    true,
    NOW(), NOW(), false,
    mt.meal_type_id
FROM menu_item mi
CROSS JOIN (
    VALUES
        ('d44dfc25-0b6e-4c16-9bf5-3ec14c20ec3d'::uuid, '06:00:00'::time, '11:00:00'::time),
        ('871a4f82-77b0-4209-9805-41364b6fcbf9'::uuid, '11:00:00'::time, '16:00:00'::time),
        ('78f1d95f-fbda-414c-aa18-d1a5dc1f1be1'::uuid, '16:00:00'::time, '23:00:00'::time),
        ('00bc0862-4a2e-4cf4-b80c-12167bed1638'::uuid, '00:00:00'::time, '23:59:59'::time)
) AS mt(meal_type_id, time_from, time_to)
WHERE mi.is_deleted = false
  AND mi.menu_item_id NOT IN (
      SELECT DISTINCT menu_item_id
      FROM menu_item_availability_schedule
      WHERE is_deleted = false
  );

COMMIT;

-- ============================================================================
-- Verification: Check items now have all meal types
-- ============================================================================
-- SELECT mi.item_name, array_agg(DISTINCT mt.meal_type_name) as meal_types
-- FROM menu_item mi
-- LEFT JOIN menu_item_availability_schedule mas ON mi.menu_item_id = mas.menu_item_id AND mas.is_deleted = false
-- LEFT JOIN meal_type mt ON mas.meal_type_id = mt.meal_type_id
-- WHERE mi.is_deleted = false
-- GROUP BY mi.item_name
-- ORDER BY mi.item_name;

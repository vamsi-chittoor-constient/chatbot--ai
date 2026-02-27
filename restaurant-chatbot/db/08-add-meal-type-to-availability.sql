-- ============================================================================
-- Migration: Add meal_type_id to menu_item_availability_schedule
-- ============================================================================
-- Purpose: Enable meal-time based menu filtering
-- Date: 2025-12-28
-- ============================================================================

-- Add meal_type_id column to menu_item_availability_schedule
ALTER TABLE menu_item_availability_schedule
ADD COLUMN IF NOT EXISTS meal_type_id UUID;

-- Add foreign key constraint
ALTER TABLE menu_item_availability_schedule
ADD CONSTRAINT fk_availability_schedule_meal_type
FOREIGN KEY (meal_type_id) REFERENCES meal_type(meal_type_id)
ON DELETE SET NULL;

-- Add index for faster lookups
CREATE INDEX IF NOT EXISTS idx_availability_schedule_meal_type
ON menu_item_availability_schedule(meal_type_id)
WHERE meal_type_id IS NOT NULL AND is_deleted = FALSE;

-- ============================================================================
-- Verification Query
-- ============================================================================
-- Run this to verify the column was added:
-- SELECT column_name, data_type, is_nullable
-- FROM information_schema.columns
-- WHERE table_name = 'menu_item_availability_schedule'
-- AND column_name = 'meal_type_id';

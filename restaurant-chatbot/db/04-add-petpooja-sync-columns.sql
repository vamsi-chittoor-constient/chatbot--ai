-- ============================================================================
-- Migration: Add Petpooja Sync Tracking Columns
-- ============================================================================
-- Purpose: Enable Petpooja menu auto-sync by adding external ID tracking columns
-- Date: 2025-12-28
-- ============================================================================

-- Add ext_petpooja tracking columns to enable sync
-- These columns store Petpooja's IDs to match incoming sync data with existing records

-- 1. menu_categories - Track Petpooja group_category_id
ALTER TABLE menu_categories
ADD COLUMN IF NOT EXISTS ext_petpooja_group_category_id BIGINT;

-- 2. menu_item - Track Petpooja item_id
ALTER TABLE menu_item
ADD COLUMN IF NOT EXISTS ext_petpooja_item_id BIGINT;

-- 3. menu_item_addon_group - Track Petpooja addon_group_id
ALTER TABLE menu_item_addon_group
ADD COLUMN IF NOT EXISTS ext_petpooja_addon_group_id BIGINT;

-- 4. menu_item_addon_item - Track Petpooja addon_item_id
ALTER TABLE menu_item_addon_item
ADD COLUMN IF NOT EXISTS ext_petpooja_addon_item_id BIGINT;

-- 5. menu_item_attribute - Track Petpooja attributes_id
ALTER TABLE menu_item_attribute
ADD COLUMN IF NOT EXISTS ext_petpooja_attributes_id BIGINT;

-- 6. menu_item_variation - Track Petpooja variation_id
ALTER TABLE menu_item_variation
ADD COLUMN IF NOT EXISTS ext_petpooja_variation_id BIGINT;

-- 7. menu_sub_categories - Track Petpooja categories_id
ALTER TABLE menu_sub_categories
ADD COLUMN IF NOT EXISTS ext_petpooja_categories_id BIGINT;

-- 8. menu_sections - Track Petpooja parent_categories_id
-- Note: This is the only one that's NOT NULL in petpooja-service schema
-- But making it nullable for existing data
ALTER TABLE menu_sections
ADD COLUMN IF NOT EXISTS ext_petpooja_parent_categories_id BIGINT;

-- Add indexes for faster lookups during sync
CREATE INDEX IF NOT EXISTS idx_menu_categories_ext_petpooja_id
ON menu_categories(ext_petpooja_group_category_id)
WHERE ext_petpooja_group_category_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_menu_item_ext_petpooja_id
ON menu_item(ext_petpooja_item_id)
WHERE ext_petpooja_item_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_menu_sub_categories_ext_petpooja_id
ON menu_sub_categories(ext_petpooja_categories_id)
WHERE ext_petpooja_categories_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_menu_sections_ext_petpooja_id
ON menu_sections(ext_petpooja_parent_categories_id)
WHERE ext_petpooja_parent_categories_id IS NOT NULL;

-- ============================================================================
-- Verification Queries
-- ============================================================================
-- Run these to verify the columns were added:

-- SELECT column_name, data_type, is_nullable
-- FROM information_schema.columns
-- WHERE table_name IN ('menu_categories', 'menu_item', 'menu_sub_categories', 'menu_sections')
-- AND column_name LIKE 'ext_petpooja%'
-- ORDER BY table_name, column_name;

-- ============================================================================

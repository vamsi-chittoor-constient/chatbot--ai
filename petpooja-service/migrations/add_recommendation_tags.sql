-- Add recommendation_tags JSONB column to menu_item table
-- Stores LLM-generated food tags for the recommendation engine
-- e.g. ["spicy", "grilled", "indian", "chicken", "main_course", "comfort_food"]

ALTER TABLE menu_item
ADD COLUMN IF NOT EXISTS recommendation_tags JSONB;

-- Index for querying items by tag (GIN index on JSONB array)
CREATE INDEX IF NOT EXISTS idx_menu_item_recommendation_tags
ON menu_item USING GIN (recommendation_tags);

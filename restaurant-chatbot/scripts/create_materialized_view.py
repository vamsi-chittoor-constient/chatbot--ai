#!/usr/bin/env python3
"""Recreate materialized view"""
import asyncio
import asyncpg

DB_CONFIG = {
    "host": "37.27.194.66",
    "port": 5430,
    "database": "restaurant_ai_dev",
    "user": "postgres",
    "password": "A24_rest!op"
}

VIEW_SQL = """
CREATE MATERIALIZED VIEW menu_items_enriched AS
SELECT
    mi.item_id,
    mi.item_name,
    mi.description,
    mi.base_price,
    mi.is_available,
    mi.is_featured,
    mi.embedding,

    -- Categories (aggregated)
    ARRAY_AGG(DISTINCT c.category_name) FILTER (WHERE c.category_name IS NOT NULL) AS categories,

    -- Meal timings (aggregated)
    ARRAY_AGG(DISTINCT mt.timing_name) FILTER (WHERE mt.timing_name IS NOT NULL) AS meal_timings,

    -- Dietary tags (aggregated)
    ARRAY_AGG(DISTINCT dt.tag_display_name) FILTER (WHERE dt.tag_display_name IS NOT NULL) AS dietary_tags,

    -- Spice level
    sl.spice_level_name,
    sl.spice_scale,

    -- Cooking method
    cm.method_name AS cooking_method,
    cm.is_healthy AS is_healthy_cooking,

    -- Inventory
    i.available_stock,

    -- Serving info
    iss.serving_size,
    su.unit_name AS serving_unit

FROM menu_items mi
LEFT JOIN item_categories ic ON mi.item_id = ic.item_id
LEFT JOIN categories c ON ic.category_id = c.category_id AND c.deleted_at IS NULL
LEFT JOIN item_availability ia ON mi.item_id = ia.item_id AND ia.is_available = TRUE
LEFT JOIN meal_timings mt ON ia.timing_id = mt.timing_id AND mt.is_active = TRUE
LEFT JOIN item_dietary_tags idt ON mi.item_id = idt.item_id
LEFT JOIN dietary_tags dt ON idt.tag_id = dt.tag_id AND dt.is_active = TRUE
LEFT JOIN spice_levels sl ON mi.spice_level_id = sl.spice_level_id
LEFT JOIN cooking_methods cm ON mi.cooking_method_id = cm.cooking_method_id
LEFT JOIN inventory i ON mi.item_id = i.item_id
LEFT JOIN item_servings iss ON mi.item_id = iss.item_id
LEFT JOIN serving_units su ON iss.unit_id = su.unit_id

WHERE mi.deleted_at IS NULL

GROUP BY
    mi.item_id, mi.item_name, mi.description, mi.base_price,
    mi.is_available, mi.is_featured, mi.embedding,
    sl.spice_level_name, sl.spice_scale,
    cm.method_name, cm.is_healthy,
    i.available_stock,
    iss.serving_size, su.unit_name;
"""

INDEX_SQL = [
    "CREATE UNIQUE INDEX idx_menu_items_enriched_id ON menu_items_enriched(item_id);",
    "CREATE INDEX idx_menu_items_enriched_available ON menu_items_enriched(is_available);",
    "CREATE INDEX idx_menu_items_enriched_categories ON menu_items_enriched USING GIN(categories);",
    "CREATE INDEX idx_menu_items_enriched_timings ON menu_items_enriched USING GIN(meal_timings);",
    "CREATE INDEX idx_menu_items_enriched_dietary ON menu_items_enriched USING GIN(dietary_tags);",
    "CREATE INDEX idx_menu_items_enriched_price ON menu_items_enriched(base_price);"
]

async def create_view():
    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        print("Creating materialized view menu_items_enriched...")
        await conn.execute(VIEW_SQL)
        print("✓ View created")

        print("\nCreating indexes...")
        for idx_sql in INDEX_SQL:
            await conn.execute(idx_sql)
            print(f"  ✓ {idx_sql.split()[2]}")

        print("\nVerifying view...")
        count = await conn.fetchval("SELECT COUNT(*) FROM menu_items_enriched")
        print(f"✓ Materialized view contains {count} items")

        # Show sample
        print("\nSample items from view:")
        items = await conn.fetch("SELECT item_name, categories, meal_timings FROM menu_items_enriched LIMIT 5")
        for item in items:
            print(f"  - {item['item_name']:40} | Categories: {item['categories']} | Timings: {item['meal_timings']}")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_view())

#!/usr/bin/env python3
"""
Implement Multi-Tenant Architecture
====================================
1. Add restaurant_id to menu tables
2. Change ID formats (MIT+6 chars, MCT+5 chars)
3. Link existing data to default restaurant
"""
import asyncio
import asyncpg
import random
import string

DB_CONFIG = {
    "host": "37.27.194.66",
    "port": 5430,
    "database": "restaurant_ai_dev",
    "user": "dev_explorer",
    "password": "restaurant24"
}

def generate_menu_item_id() -> str:
    """Generate MIT + 6 random alphanumeric characters"""
    chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"MIT{chars}"

def generate_category_id() -> str:
    """Generate MCT + 5 random alphanumeric characters"""
    chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"MCT{chars}"

async def implement():
    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        print("=" * 80)
        print("MULTI-TENANT ARCHITECTURE IMPLEMENTATION")
        print("=" * 80)

        # Step 1: Check restaurants
        print("\n[STEP 1] Checking restaurant_config table...")
        restaurants = await conn.fetch("SELECT id, name, branch_name FROM restaurant_config")

        if not restaurants:
            print("  ⚠ No restaurants found - creating default...")
            default_rest_id = await conn.fetchval("""
                INSERT INTO restaurant_config (id, name, api_key, business_hours)
                VALUES ('REST001', 'Default Restaurant', 'default_api_key', '{}')
                RETURNING id
            """)
            print(f"  ✓ Created: {default_rest_id}")
        else:
            default_rest_id = restaurants[0]['id']
            print(f"  ✓ Found {len(restaurants)} restaurant(s), using: {default_rest_id}")

        # Step 2: Add restaurant_id columns
        print("\n[STEP 2] Adding restaurant_id columns...")

        # Check if columns exist
        has_rest_menu = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_name = 'menu_items' AND column_name = 'restaurant_id'
            )
        """)
        has_rest_cat = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_name = 'categories' AND column_name = 'restaurant_id'
            )
        """)

        if not has_rest_menu:
            await conn.execute("""
                ALTER TABLE menu_items
                ADD COLUMN restaurant_id VARCHAR(20) REFERENCES restaurant_config(id)
            """)
            print("  ✓ Added menu_items.restaurant_id")
        else:
            print("  ○ menu_items.restaurant_id exists")

        if not has_rest_cat:
            await conn.execute("""
                ALTER TABLE categories
                ADD COLUMN restaurant_id VARCHAR(20) REFERENCES restaurant_config(id)
            """)
            print("  ✓ Added categories.restaurant_id")
        else:
            print("  ○ categories.restaurant_id exists")

        # Step 3: Link existing data
        print(f"\n[STEP 3] Linking existing data to {default_rest_id}...")

        menu_updated = await conn.execute(f"""
            UPDATE menu_items SET restaurant_id = '{default_rest_id}'
            WHERE restaurant_id IS NULL
        """)
        cat_updated = await conn.execute(f"""
            UPDATE categories SET restaurant_id = '{default_rest_id}'
            WHERE restaurant_id IS NULL
        """)

        print(f"  ✓ Updated menu_items: {menu_updated}")
        print(f"  ✓ Updated categories: {cat_updated}")

        # Step 4: Change ID formats
        print("\n[STEP 4] Preparing ID format changes...")

        items = await conn.fetch("SELECT item_id FROM menu_items ORDER BY item_id")
        categories = await conn.fetch("SELECT category_id FROM categories ORDER BY category_id")

        print(f"  Items to update: {len(items)}")
        print(f"  Categories to update: {len(categories)}")

        # Generate new IDs
        item_id_map = {}
        for item in items:
            old_id = item['item_id']
            new_id = generate_menu_item_id()
            while new_id in item_id_map.values():
                new_id = generate_menu_item_id()
            item_id_map[old_id] = new_id

        cat_id_map = {}
        for cat in categories:
            old_id = cat['category_id']
            new_id = generate_category_id()
            while new_id in cat_id_map.values():
                new_id = generate_category_id()
            cat_id_map[old_id] = new_id

        print(f"\n  Sample item ID changes:")
        for old, new in list(item_id_map.items())[:3]:
            print(f"    {old} → {new}")

        print(f"\n  Sample category ID changes:")
        for old, new in list(cat_id_map.items())[:3]:
            print(f"    {old} → {new}")

        # Step 5: Update IDs
        print("\n[STEP 5] Updating IDs in database...")
        print("  This will update all foreign key references...")

        async with conn.transaction():
            # Update categories first (update parent table BEFORE child tables)
            print("  Updating category IDs...")
            for old_id, new_id in cat_id_map.items():
                # Update categories table FIRST
                await conn.execute(
                    "UPDATE categories SET category_id = $1 WHERE category_id = $2",
                    new_id, old_id
                )
                # Then update foreign key references
                await conn.execute(
                    "UPDATE item_categories SET category_id = $1 WHERE category_id = $2",
                    new_id, old_id
                )
            print(f"  ✓ Updated {len(cat_id_map)} categories")

            # Update menu items (parent table FIRST, then children)
            print("  Updating menu item IDs...")
            for idx, (old_id, new_id) in enumerate(item_id_map.items(), 1):
                # Update main table FIRST
                await conn.execute("UPDATE menu_items SET item_id = $1 WHERE item_id = $2", new_id, old_id)

                # Then update all foreign key references (junction tables)
                await conn.execute("UPDATE item_categories SET item_id = $1 WHERE item_id = $2", new_id, old_id)
                await conn.execute("UPDATE item_availability SET item_id = $1 WHERE item_id = $2", new_id, old_id)
                await conn.execute("UPDATE item_ingredients SET item_id = $1 WHERE item_id = $2", new_id, old_id)
                await conn.execute("UPDATE item_dietary_tags SET item_id = $1 WHERE item_id = $2", new_id, old_id)
                await conn.execute("UPDATE item_servings SET item_id = $1 WHERE item_id = $2", new_id, old_id)
                await conn.execute("UPDATE inventory SET item_id = $1 WHERE item_id = $2", new_id, old_id)
                await conn.execute("UPDATE item_variants SET item_id = $1 WHERE item_id = $2", new_id, old_id)
                await conn.execute("UPDATE item_recommendations SET item_id = $1 WHERE item_id = $2", new_id, old_id)
                await conn.execute("UPDATE item_recommendations SET recommended_item_id = $1 WHERE recommended_item_id = $2", new_id, old_id)

                if idx % 50 == 0:
                    print(f"    {idx}/{len(item_id_map)} items...")

            print(f"  ✓ Updated {len(item_id_map)} menu items")

        # Step 6: Verify
        print("\n[STEP 6] Verification...")

        sample_items = await conn.fetch("""
            SELECT item_id, item_name, restaurant_id
            FROM menu_items LIMIT 5
        """)
        sample_cats = await conn.fetch("""
            SELECT category_id, category_name, restaurant_id
            FROM categories LIMIT 5
        """)

        print("\n  Sample menu items:")
        for item in sample_items:
            print(f"    {item['item_id']} - {item['item_name']} (restaurant: {item['restaurant_id']})")

        print("\n  Sample categories:")
        for cat in sample_cats:
            print(f"    {cat['category_id']} - {cat['category_name']} (restaurant: {cat['restaurant_id']})")

        # Count totals
        total_items = await conn.fetchval("SELECT COUNT(*) FROM menu_items WHERE restaurant_id IS NOT NULL")
        total_cats = await conn.fetchval("SELECT COUNT(*) FROM categories WHERE restaurant_id IS NOT NULL")

        print("\n" + "=" * 80)
        print("✓ MULTI-TENANT IMPLEMENTATION COMPLETE!")
        print("=" * 80)
        print(f"  ✓ {total_items} menu items linked to restaurants")
        print(f"  ✓ {total_cats} categories linked to restaurants")
        print(f"  ✓ All IDs updated to new format (MIT+6, MCT+5)")
        print("=" * 80)

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(implement())

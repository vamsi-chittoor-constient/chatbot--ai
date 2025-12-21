#!/usr/bin/env python3
"""
Implement Multi-Tenant Architecture
====================================
1. Analyze current restaurant structure
2. Add restaurant_id to menu tables
3. Change ID formats (MIT+6 chars, MCT+5 chars)
4. Link existing data to default restaurant
"""
import asyncio
import asyncpg
import random
import string

DB_CONFIG = {
    "host": "37.27.194.66",
    "port": 5430,
    "database": "restaurant_ai_dev",
    "user": "postgres",
    "password": "A24_restiop"
}

def generate_menu_item_id() -> str:
    """Generate MIT + 6 random alphanumeric characters"""
    chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"MIT{chars}"

def generate_category_id() -> str:
    """Generate MCT + 5 random alphanumeric characters"""
    chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"MCT{chars}"

async def analyze_and_implement():
    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        print("=" * 80)
        print("MULTI-TENANT ARCHITECTURE IMPLEMENTATION")
        print("=" * 80)

        # Step 1: Analyze restaurants
        print("\n[STEP 1] Analyzing restaurant_config table...")
        restaurants = await conn.fetch("SELECT id, name, branch_name FROM restaurant_config")

        if not restaurants:
            print("  ⚠ No restaurants found!")
            print("  Creating default restaurant...")
            default_rest_id = await conn.fetchval("""
                INSERT INTO restaurant_config (id, name, api_key, business_hours)
                VALUES ('REST001', 'Default Restaurant', 'default_api_key', '{}')
                RETURNING id
            """)
            print(f"  ✓ Created default restaurant: {default_rest_id}")
        else:
            print(f"  Found {len(restaurants)} restaurant(s):")
            for r in restaurants:
                print(f"    - {r['id']}: {r['name']} ({r['branch_name'] or 'Main'})")
            default_rest_id = restaurants[0]['id']
            print(f"  Using {default_rest_id} as default for existing data")

        # Step 2: Check current schema
        print("\n[STEP 2] Checking current schema...")
        has_rest_id_menu = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_name = 'menu_items' AND column_name = 'restaurant_id'
            )
        """)
        has_rest_id_cat = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_name = 'categories' AND column_name = 'restaurant_id'
            )
        """)

        print(f"  menu_items.restaurant_id exists: {has_rest_id_menu}")
        print(f"  categories.restaurant_id exists: {has_rest_id_cat}")

        # Step 3: Add restaurant_id columns if needed
        print("\n[STEP 3] Adding restaurant_id columns...")

        if not has_rest_id_menu:
            await conn.execute("""
                ALTER TABLE menu_items
                ADD COLUMN restaurant_id VARCHAR(20) REFERENCES restaurant_config(id);
            """)
            print("  ✓ Added menu_items.restaurant_id")
        else:
            print("  ○ menu_items.restaurant_id already exists")

        if not has_rest_id_cat:
            await conn.execute("""
                ALTER TABLE categories
                ADD COLUMN restaurant_id VARCHAR(20) REFERENCES restaurant_config(id);
            """)
            print("  ✓ Added categories.restaurant_id")
        else:
            print("  ○ categories.restaurant_id already exists")

        # Step 4: Update existing data with default restaurant_id
        print(f"\n[STEP 4] Linking existing data to restaurant {default_rest_id}...")

        menu_updated = await conn.execute(f"""
            UPDATE menu_items
            SET restaurant_id = '{default_rest_id}'
            WHERE restaurant_id IS NULL
        """)
        print(f"  ✓ Updated menu_items: {menu_updated}")

        cat_updated = await conn.execute(f"""
            UPDATE categories
            SET restaurant_id = '{default_rest_id}'
            WHERE restaurant_id IS NULL
        """)
        print(f"  ✓ Updated categories: {cat_updated}")

        # Step 5: Change ID formats
        print("\n[STEP 5] Changing ID formats...")
        print("  This will:")
        print("    - Change menu_items IDs to MIT + 6 random chars")
        print("    - Change category IDs to MCT + 5 random chars")
        print("    - Update all foreign key references")

        # Get current items
        items = await conn.fetch("SELECT item_id FROM menu_items ORDER BY item_id")
        categories = await conn.fetch("SELECT category_id FROM categories ORDER BY category_id")

        print(f"\n  Found {len(items)} menu items to update")
        print(f"  Found {len(categories)} categories to update")

        # Create ID mapping for menu items
        item_id_map = {}
        for item in items:
            old_id = item['item_id']
            new_id = generate_menu_item_id()
            # Ensure uniqueness
            while new_id in item_id_map.values():
                new_id = generate_menu_item_id()
            item_id_map[old_id] = new_id

        # Create ID mapping for categories
        cat_id_map = {}
        for cat in categories:
            old_id = cat['category_id']
            new_id = generate_category_id()
            # Ensure uniqueness
            while new_id in cat_id_map.values():
                new_id = generate_category_id()
            cat_id_map[old_id] = new_id

        print(f"\n  Generated {len(item_id_map)} new menu item IDs")
        print(f"  Sample: {list(item_id_map.items())[:3]}")
        print(f"\n  Generated {len(cat_id_map)} new category IDs")
        print(f"  Sample: {list(cat_id_map.items())[:3]}")

        # Step 6: Perform ID updates (this is complex, need transaction)
        print("\n[STEP 6] Updating IDs (this may take a moment)...")
        print("  WARNING: This will update many foreign key references!")

        response = input("\n  Proceed with ID format change? (yes/no): ")
        if response.lower() != 'yes':
            print("  ○ Skipping ID format change")
            return

        # Use transaction for safety
        async with conn.transaction():
            # Temporarily disable foreign key checks would be ideal, but PostgreSQL doesn't support it
            # Instead, we need to update in correct order

            print("  Updating category IDs...")
            for old_id, new_id in cat_id_map.items():
                # Update item_categories junction table first
                await conn.execute("""
                    UPDATE item_categories SET category_id = $1 WHERE category_id = $2
                """, new_id, old_id)

                # Update categories table
                await conn.execute("""
                    UPDATE categories SET category_id = $1 WHERE category_id = $2
                """, new_id, old_id)

            print(f"  ✓ Updated {len(cat_id_map)} category IDs")

            print("  Updating menu item IDs...")
            for idx, (old_id, new_id) in enumerate(item_id_map.items(), 1):
                # Update all junction tables first
                await conn.execute("UPDATE item_categories SET item_id = $1 WHERE item_id = $2", new_id, old_id)
                await conn.execute("UPDATE item_availability SET item_id = $1 WHERE item_id = $2", new_id, old_id)
                await conn.execute("UPDATE item_ingredients SET item_id = $1 WHERE item_id = $2", new_id, old_id)
                await conn.execute("UPDATE item_dietary_tags SET item_id = $1 WHERE item_id = $2", new_id, old_id)
                await conn.execute("UPDATE item_servings SET item_id = $1 WHERE item_id = $2", new_id, old_id)
                await conn.execute("UPDATE inventory SET item_id = $1 WHERE item_id = $2", new_id, old_id)
                await conn.execute("UPDATE item_variants SET item_id = $1 WHERE item_id = $2", new_id, old_id)
                await conn.execute("UPDATE item_recommendations SET item_id = $1 WHERE item_id = $2", new_id, old_id)
                await conn.execute("UPDATE item_recommendations SET recommended_item_id = $1 WHERE recommended_item_id = $2", new_id, old_id)
                await conn.execute("UPDATE user_preferences SET favorite_item_ids = array_replace(favorite_item_ids, $2, $1) WHERE $2 = ANY(favorite_item_ids)", new_id, old_id)

                # Update menu_items table last
                await conn.execute("UPDATE menu_items SET item_id = $1 WHERE item_id = $2", new_id, old_id)

                if idx % 50 == 0:
                    print(f"    Progress: {idx}/{len(item_id_map)} items...")

            print(f"  ✓ Updated {len(item_id_map)} menu item IDs")

        print("\n" + "=" * 80)
        print("✓ MULTI-TENANT IMPLEMENTATION COMPLETE!")
        print("=" * 80)

        # Verify
        sample_items = await conn.fetch("""
            SELECT item_id, item_name, restaurant_id
            FROM menu_items
            LIMIT 5
        """)
        sample_cats = await conn.fetch("""
            SELECT category_id, category_name, restaurant_id
            FROM categories
            LIMIT 5
        """)

        print("\nSample menu items:")
        for item in sample_items:
            print(f"  {item['item_id']} - {item['item_name']} (restaurant: {item['restaurant_id']})")

        print("\nSample categories:")
        for cat in sample_cats:
            print(f"  {cat['category_id']} - {cat['category_name']} (restaurant: {cat['restaurant_id']})")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(analyze_and_implement())

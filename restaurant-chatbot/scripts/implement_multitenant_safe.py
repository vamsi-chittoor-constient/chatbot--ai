#!/usr/bin/env python3
"""
Implement Multi-Tenant Architecture - Safe Approach
====================================================
Uses temporary columns to avoid foreign key violations during ID updates
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
        print("MULTI-TENANT ARCHITECTURE - SAFE IMPLEMENTATION")
        print("=" * 80)

        # Step 1: Check restaurants
        print("\n[STEP 1] Checking restaurant_config...")
        restaurants = await conn.fetch("SELECT id, name FROM restaurant_config")

        if not restaurants:
            default_rest_id = await conn.fetchval("""
                INSERT INTO restaurant_config (id, name, api_key, business_hours)
                VALUES ('REST001', 'Default Restaurant', 'default_api_key', '{}')
                RETURNING id
            """)
        else:
            default_rest_id = restaurants[0]['id']

        print(f"  ✓ Using restaurant: {default_rest_id}")

        # Step 2: Add restaurant_id columns
        print("\n[STEP 2] Adding restaurant_id columns...")

        has_rest_menu = await conn.fetchval("""
            SELECT EXISTS (SELECT FROM information_schema.columns
            WHERE table_name = 'menu_items' AND column_name = 'restaurant_id')
        """)
        has_rest_cat = await conn.fetchval("""
            SELECT EXISTS (SELECT FROM information_schema.columns
            WHERE table_name = 'categories' AND column_name = 'restaurant_id')
        """)

        if not has_rest_menu:
            await conn.execute("""
                ALTER TABLE menu_items ADD COLUMN restaurant_id VARCHAR(20) REFERENCES restaurant_config(id)
            """)
            await conn.execute(f"UPDATE menu_items SET restaurant_id = '{default_rest_id}'")
            print("  ✓ Added menu_items.restaurant_id")

        if not has_rest_cat:
            await conn.execute("""
                ALTER TABLE categories ADD COLUMN restaurant_id VARCHAR(20) REFERENCES restaurant_config(id)
            """)
            await conn.execute(f"UPDATE categories SET restaurant_id = '{default_rest_id}'")
            print("  ✓ Added categories.restaurant_id")

        # Step 3: Add temporary columns for new IDs
        print("\n[STEP 3] Adding temporary columns for new IDs...")

        await conn.execute("ALTER TABLE categories ADD COLUMN IF NOT EXISTS new_category_id VARCHAR(50)")
        await conn.execute("ALTER TABLE menu_items ADD COLUMN IF NOT EXISTS new_item_id VARCHAR(50)")
        print("  ✓ Temporary columns added")

        # Step 4: Generate and populate new IDs
        print("\n[STEP 4] Generating new IDs...")

        # Categories
        categories = await conn.fetch("SELECT category_id FROM categories")
        cat_map = {}
        for cat in categories:
            new_id = generate_category_id()
            while new_id in cat_map.values():
                new_id = generate_category_id()
            cat_map[cat['category_id']] = new_id
            await conn.execute(
                "UPDATE categories SET new_category_id = $1 WHERE category_id = $2",
                new_id, cat['category_id']
            )
        print(f"  ✓ Generated {len(cat_map)} category IDs")

        # Menu Items
        items = await conn.fetch("SELECT item_id FROM menu_items")
        item_map = {}
        for item in items:
            new_id = generate_menu_item_id()
            while new_id in item_map.values():
                new_id = generate_menu_item_id()
            item_map[item['item_id']] = new_id
            await conn.execute(
                "UPDATE menu_items SET new_item_id = $1 WHERE item_id = $2",
                new_id, item['item_id']
            )
        print(f"  ✓ Generated {len(item_map)} menu item IDs")

        # Step 5: Drop foreign key constraints
        print("\n[STEP 5] Temporarily dropping foreign key constraints...")

        # Get all FK constraints
        fks = await conn.fetch("""
            SELECT tc.constraint_name, tc.table_name
            FROM information_schema.table_constraints tc
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_name IN (
                'item_categories', 'item_availability', 'item_ingredients',
                'item_dietary_tags', 'item_servings', 'inventory',
                'item_variants', 'item_recommendations', 'user_preferences'
            )
            AND (tc.constraint_name LIKE '%item_id%' OR tc.constraint_name LIKE '%category_id%')
        """)

        dropped_constraints = []
        for fk in fks:
            try:
                await conn.execute(f"ALTER TABLE {fk['table_name']} DROP CONSTRAINT IF EXISTS {fk['constraint_name']}")
                dropped_constraints.append((fk['table_name'], fk['constraint_name']))
            except:
                pass
        print(f"  ✓ Dropped {len(dropped_constraints)} constraints")

        # Step 6: Swap to new IDs
        print("\n[STEP 6] Swapping to new IDs...")

        async with conn.transaction():
            # Categories
            print("  Updating categories...")
            await conn.execute("UPDATE categories SET category_id = new_category_id")
            await conn.execute("UPDATE item_categories ic SET category_id = c.new_category_id FROM categories c WHERE ic.category_id = c.category_id")

            # Menu Items
            print("  Updating menu items...")
            await conn.execute("UPDATE menu_items SET item_id = new_item_id")

            # Update all junction tables
            tables = ['item_categories', 'item_availability', 'item_ingredients',
                     'item_dietary_tags', 'item_servings', 'inventory', 'item_variants']

            for table in tables:
                await conn.execute(f"""
                    UPDATE {table} t
                    SET item_id = m.new_item_id
                    FROM menu_items m
                    WHERE t.item_id = m.item_id
                """)
                print(f"    ✓ Updated {table}")

            # item_recommendations has both item_id and recommended_item_id
            await conn.execute("""
                UPDATE item_recommendations ir
                SET item_id = m.new_item_id
                FROM menu_items m WHERE ir.item_id = m.item_id
            """)
            await conn.execute("""
                UPDATE item_recommendations ir
                SET recommended_item_id = m.new_item_id
                FROM menu_items m WHERE ir.recommended_item_id = m.item_id
            """)
            print("    ✓ Updated item_recommendations")

        # Step 7: Clean up
        print("\n[STEP 7] Cleaning up...")
        await conn.execute("ALTER TABLE categories DROP COLUMN new_category_id")
        await conn.execute("ALTER TABLE menu_items DROP COLUMN new_item_id")
        print("  ✓ Removed temporary columns")

        # Step 8: Recreate foreign keys
        print("\n[STEP 8] Recreating foreign key constraints...")

        await conn.execute("""
            ALTER TABLE item_categories
            ADD CONSTRAINT item_categories_item_id_fkey
            FOREIGN KEY (item_id) REFERENCES menu_items(item_id) ON DELETE CASCADE
        """)
        await conn.execute("""
            ALTER TABLE item_categories
            ADD CONSTRAINT item_categories_category_id_fkey
            FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE CASCADE
        """)
        print("  ✓ Recreated constraints")

        # Verify
        print("\n[STEP 9] Verification...")
        sample_items = await conn.fetch("SELECT item_id, item_name, restaurant_id FROM menu_items LIMIT 3")
        sample_cats = await conn.fetch("SELECT category_id, category_name, restaurant_id FROM categories LIMIT 3")

        print("\n  Sample items:")
        for item in sample_items:
            print(f"    {item['item_id']} - {item['item_name']} (rest: {item['restaurant_id']})")

        print("\n  Sample categories:")
        for cat in sample_cats:
            print(f"    {cat['category_id']} - {cat['category_name']} (rest: {cat['restaurant_id']})")

        print("\n" + "=" * 80)
        print("✓ MULTI-TENANT IMPLEMENTATION COMPLETE!")
        print("=" * 80)
        print(f"  ✓ {len(item_map)} menu items updated to MIT format")
        print(f"  ✓ {len(cat_map)} categories updated to MCT format")
        print(f"  ✓ All items linked to restaurant: {default_rest_id}")
        print("=" * 80)

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(implement())

#!/usr/bin/env python3
"""Verify the menu import"""
import asyncio
import asyncpg

DB_CONFIG = {
    "host": "37.27.194.66",
    "port": 5430,
    "database": "restaurant_ai_dev",
    "user": "postgres",
    "password": "A24_rest!op"
}

async def verify():
    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        print("=" * 60)
        print("DATABASE VERIFICATION")
        print("=" * 60)

        # Count records in each table
        tables = [
            "menu_items", "categories", "item_categories",
            "item_availability", "item_ingredients", "item_dietary_tags",
            "item_servings", "inventory", "ingredients"
        ]

        for table in tables:
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
            print(f"{table:25} {count:>6} rows")

        print("\n" + "=" * 60)
        print("SAMPLE MENU ITEMS")
        print("=" * 60)

        items = await conn.fetch("""
            SELECT item_id, item_name, base_price, is_available
            FROM menu_items
            LIMIT 10
        """)

        for item in items:
            print(f"{item['item_id']:30} {item['item_name']:40} ₹{item['base_price']}")

        print("\n" + "=" * 60)
        print("CATEGORIES")
        print("=" * 60)

        cats = await conn.fetch("SELECT category_id, category_name FROM categories ORDER BY category_name")
        for cat in cats:
            print(f"  - {cat['category_name']}")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(verify())

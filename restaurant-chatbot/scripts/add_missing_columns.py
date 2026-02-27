#!/usr/bin/env python3
"""
Add missing CSV columns to menu_items table
"""
import asyncio
import asyncpg

DB_CONFIG = {
    "host": "37.27.194.66",
    "port": 5430,
    "database": "restaurant_ai_dev",
    "user": "postgres",
    "password": "A24_rest!op"
}

async def add_columns():
    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        print("Adding missing columns to menu_items table...")

        # Add prep_time_minutes
        await conn.execute("""
            ALTER TABLE menu_items
            ADD COLUMN IF NOT EXISTS prep_time_minutes INTEGER;
        """)
        print("✓ Added prep_time_minutes")

        # Add calories
        await conn.execute("""
            ALTER TABLE menu_items
            ADD COLUMN IF NOT EXISTS calories INTEGER;
        """)
        print("✓ Added calories")

        # Add is_seasonal
        await conn.execute("""
            ALTER TABLE menu_items
            ADD COLUMN IF NOT EXISTS is_seasonal BOOLEAN DEFAULT FALSE;
        """)
        print("✓ Added is_seasonal")

        print("\n✓ All columns added successfully!")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(add_columns())

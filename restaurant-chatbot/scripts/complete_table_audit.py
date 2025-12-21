#!/usr/bin/env python3
"""Complete audit of all 18 tables - rows and columns"""
import asyncio
import asyncpg

DB_CONFIG = {
    "host": "37.27.194.66",
    "port": 5430,
    "database": "restaurant_ai_dev",
    "user": "postgres",
    "password": "A24_rest!op"
}

async def audit():
    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        print("=" * 90)
        print("COMPLETE DATABASE AUDIT - ALL 18 FOOD ORDERING TABLES")
        print("=" * 90)

        # Define all 18 tables
        tables = [
            # Lookup Tables (6)
            "spice_levels",
            "cooking_methods",
            "serving_units",
            "meal_timings",
            "ingredients",
            "dietary_tags",
            # Core Tables (3)
            "categories",
            "menu_items",
            "item_categories",
            # Junction Tables (4)
            "item_availability",
            "item_ingredients",
            "item_dietary_tags",
            "item_servings",
            # Operational Tables (5)
            "inventory",
            "item_variants",
            "item_recommendations",
            "user_preferences",
            "order_history",
        ]

        print(f"\n{'#':<4} {'Table Name':<30} {'Rows':<10} {'Columns':<10}")
        print("-" * 90)

        total_rows = 0
        total_columns = 0

        for idx, table in enumerate(tables, 1):
            # Get row count
            row_count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")

            # Get column count
            col_count = await conn.fetchval(f"""
                SELECT COUNT(*)
                FROM information_schema.columns
                WHERE table_name = '{table}'
            """)

            total_rows += row_count
            total_columns += col_count

            status = "✓" if row_count > 0 else "○"
            print(f"{idx:<4} {table:<30} {row_count:<10} {col_count:<10} {status}")

        print("-" * 90)
        print(f"{'TOTAL:':<35} {total_rows:<10} {total_columns:<10}")
        print()

        # Detailed breakdown
        print("=" * 90)
        print("DETAILED TABLE BREAKDOWN")
        print("=" * 90)

        for table in tables:
            # Get columns
            columns = await conn.fetch(f"""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = '{table}'
                ORDER BY ordinal_position
            """)

            row_count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")

            print(f"\n{table.upper()} ({row_count} rows, {len(columns)} columns):")
            for col in columns:
                print(f"  - {col['column_name']:<30} {col['data_type']}")

        print("\n" + "=" * 90)
        print("SUMMARY")
        print("=" * 90)
        print(f"Total Tables: 18")
        print(f"Total Rows across all tables: {total_rows}")
        print(f"Total Columns across all tables: {total_columns}")
        print(f"Tables with data: {sum(1 for t in tables if await conn.fetchval(f'SELECT COUNT(*) FROM {t}') > 0)}/18")
        print("=" * 90)

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(audit())

"""Check all menu table schemas."""
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_db_session, db_manager
from sqlalchemy import text


async def main():
    db_manager.init_database()
    async with get_db_session() as session:
        tables = ['menu_item', 'menu_categories', 'menu_sections', 'dietary_types', 'allergens']

        for table_name in tables:
            result = await session.execute(
                text(f"""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_name = '{table_name}'
                    ORDER BY ordinal_position
                """)
            )

            print(f"\n{table_name} table structure:")
            print("-" * 60)
            rows = result.fetchall()
            if rows:
                for row in rows:
                    print(f"  {row[0]}: {row[1]}")
            else:
                print(f"  Table {table_name} does not exist")


if __name__ == "__main__":
    asyncio.run(main())

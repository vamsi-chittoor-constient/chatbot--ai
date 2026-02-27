"""Check table schema."""
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
        result = await session.execute(
            text("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'menu_categories'
                ORDER BY ordinal_position
            """)
        )

        print("\nmenu_categories table structure:")
        print("-" * 50)
        for row in result:
            print(f"{row[0]}: {row[1]}")


if __name__ == "__main__":
    asyncio.run(main())

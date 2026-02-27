"""
Database Migration Runner
=========================
Automatically runs SQL migrations from db/ directory on application startup.

Migration Strategy (Hybrid Approach):
- Docker handles: 01-schema.sql, 02-data.sql, 03-app-tables.sql (initial setup)
- App handles: 04+ migrations (incremental changes)

Features:
- Runs migrations in numerical order (04-*, 05-*, 06-*, etc.)
- Tracks which migrations have been run
- Idempotent - safe to run multiple times
- Skips already-run migrations and Docker-managed migrations (01-03)
"""
import os
from pathlib import Path
from typing import List, Tuple
import structlog

logger = structlog.get_logger(__name__)


async def run_migrations():
    """
    Run all pending SQL migrations from the db/ directory.

    Migrations are run in numerical order based on filename prefix.
    Already-run migrations are tracked in the schema_migrations table.
    """
    from app.core.db_pool import get_async_pool

    try:
        # Get database connection
        pool = await get_async_pool()

        async with pool.acquire() as conn:
            # Create migrations tracking table if it doesn't exist
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    migration_id SERIAL PRIMARY KEY,
                    migration_name VARCHAR(255) UNIQUE NOT NULL,
                    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Get list of already-run migrations
            rows = await conn.fetch("SELECT migration_name FROM schema_migrations")
            completed_migrations = {row['migration_name'] for row in rows}

            # Find all SQL migration files
            db_dir = Path(__file__).parent.parent.parent / "db"
            if not db_dir.exists():
                logger.warning("migrations_skipped", reason="db directory not found")
                return

            # Skip init.sql and Docker-managed migrations (01-03)
            # Docker handles initial schema setup, app handles incremental migrations (04+)
            migration_files = sorted([
                f for f in db_dir.glob("*.sql")
                if f.name not in ['init.sql', '01-schema.sql', '02-data.sql', '03-app-tables.sql', '06-setup-petpooja-integration.sql']
            ])

            if not migration_files:
                logger.info("no_migrations_found")
                return

            # Run pending migrations
            pending_count = 0
            for migration_file in migration_files:
                migration_name = migration_file.name

                # Skip if already run
                if migration_name in completed_migrations:
                    logger.debug("migration_skipped", migration=migration_name, reason="already_applied")
                    continue

                # Read and execute migration
                try:
                    migration_sql = migration_file.read_text(encoding='utf-8')

                    logger.info("migration_running", migration=migration_name)

                    # Execute the migration
                    await conn.execute(migration_sql)

                    # Record that migration was run
                    await conn.execute(
                        "INSERT INTO schema_migrations (migration_name) VALUES ($1)",
                        migration_name
                    )

                    pending_count += 1
                    logger.info("migration_completed", migration=migration_name)

                except Exception as e:
                    logger.error(
                        "migration_failed",
                        migration=migration_name,
                        error=str(e)
                    )
                    # Don't stop on error - log and continue
                    # Some migrations might fail if columns already exist, etc.
                    continue

            if pending_count > 0:
                logger.info("migrations_complete", total_applied=pending_count)
            else:
                logger.info("migrations_up_to_date", total_migrations=len(migration_files))

    except Exception as e:
        logger.error("migration_runner_failed", error=str(e))
        # Don't crash the app - migrations are important but not critical
        # The app can still run with the existing schema

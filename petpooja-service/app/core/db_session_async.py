"""
Database Session Management - ASYNC VERSION
High-concurrency async SQLAlchemy setup with PostgreSQL
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import text, event
from typing import AsyncGenerator
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Log database URL (mask password for security)
_db_url_display = f"postgresql+asyncpg://{settings.POSTGRES_USER}:****@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
logger.info(f"Async Database URL: {_db_url_display}")
print(f"[DB] Async connecting to: {_db_url_display}")

# Convert sync URL to async URL (asyncpg driver)
async_database_url = settings.DATABASE_URL.replace(
    "postgresql+psycopg://", "postgresql+asyncpg://"
).replace(
    "postgresql://", "postgresql+asyncpg://"
)

# Create async SQLAlchemy engine
engine = create_async_engine(
    async_database_url,
    pool_pre_ping=True,
    pool_size=settings.DB_ASYNC_POOL_SIZE,  # Configured async pool size
    max_overflow=settings.DB_ASYNC_MAX_OVERFLOW,  # Configured async overflow
    pool_timeout=settings.DB_ASYNC_POOL_TIMEOUT,
    pool_recycle=settings.DB_ASYNC_POOL_RECYCLE,  # Recycle connections after configured time
    echo=False,
    # Async-specific optimizations
    pool_use_lifo=True,  # LIFO for better connection reuse
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Don't expire objects after commit
    autocommit=False,
    autoflush=False,
)

# Create declarative base for models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Async database dependency for FastAPI endpoints

    Usage:
        @app.get("/endpoint")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Model))
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def _create_performance_indexes():
    """
    Create performance indexes for frequently queried columns.
    These indexes significantly improve query performance.
    """
    indexes = [
        # BranchInfoTable - frequently filtered by ext_petpooja_restaurant_id
        ("idx_branch_info_petpooja_rid", "branch_info_table", "ext_petpooja_restaurant_id"),
        ("idx_branch_info_chain_branch", "branch_info_table", "chain_id, branch_id"),

        # RestaurantTable - frequently filtered by chain_id + branch_id
        ("idx_restaurant_chain_branch", "restaurant_table", "chain_id, branch_id"),

        # IntegrationConfigTable - frequently filtered by restaurant_id + is_enabled
        ("idx_integration_config_rest_enabled", "integration_config_table", "restaurant_id, is_enabled"),

        # IntegrationCredentialsTable - frequently filtered by integration_config_id
        ("idx_integration_creds_config", "integration_credentials_table", "integration_config_id, is_deleted"),

        # Orders - frequently filtered by order_id
        ("idx_orders_order_id", "orders", "order_id"),
        ("idx_orders_external_ref", "orders", "order_external_reference_id"),
    ]

    async with engine.begin() as connection:
        for idx_name, table_name, columns in indexes:
            try:
                # Check if index exists
                check_sql = text(f"""
                    SELECT 1 FROM pg_indexes
                    WHERE indexname = :idx_name
                """)
                result = await connection.execute(check_sql, {"idx_name": idx_name})
                if not (await result.fetchone()):
                    create_sql = text(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name} ({columns})")
                    await connection.execute(create_sql)
                    logger.info(f"Created async index: {idx_name}")
                else:
                    logger.debug(f"Index already exists: {idx_name}")
            except Exception as e:
                # Non-critical - just log and continue
                logger.warning(f"Could not create index {idx_name}: {e}")


async def init_db_async():
    """
    Initialize database asynchronously (non-blocking)
    Creates all tables defined in models
    """
    try:
        # Import all models to ensure they're registered
        import app.models  # noqa: F401

        # Create all tables
        async with engine.begin() as conn:
            # Create tables if they don't exist
            await conn.run_sync(Base.metadata.create_all)

        # Create performance indexes
        await _create_performance_indexes()

        logger.info("Async database initialized successfully")
    except Exception as e:
        logger.error(f"Async database initialization failed: {e}")
        raise


async def warm_connection_pool():
    """
    Pre-warm the async connection pool by creating initial connections.
    This reduces latency on the first few requests.
    """
    try:
        # Create a few connections to warm up the pool
        connections = []
        for _ in range(min(5, engine.pool.size())):
            conn = await engine.connect()
            connections.append(conn)

        # Return connections to the pool
        for conn in connections:
            await conn.close()

        logger.info(f"Async connection pool warmed up with {len(connections)} connections")
    except Exception as e:
        logger.warning(f"Could not warm up async connection pool: {e}")


async def close_db():
    """
    Close database connections gracefully on shutdown
    """
    await engine.dispose()
    logger.info("Async database connections closed")


# Health check helper
async def check_db_health() -> bool:
    """
    Check if database is healthy

    Returns:
        True if database is accessible, False otherwise
    """
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False

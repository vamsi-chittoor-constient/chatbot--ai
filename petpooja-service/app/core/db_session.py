"""
Database Session Management
SQLAlchemy setup with PostgreSQL for ORM models
"""

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.core.config import settings

logger = logging.getLogger(__name__)

# Log database URL (mask password for security)
_db_url_display = f"postgresql://{settings.POSTGRES_USER}:****@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
logger.info(f"Database URL: {_db_url_display}")
print(f"[DB] Connecting to: {_db_url_display}")

# Create SQLAlchemy engine with optimized settings
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,  # Recycle connections after configured time
    echo=False,
    # Performance optimizations
    connect_args={
        "options": f"-c statement_timeout={settings.DB_STATEMENT_TIMEOUT}"  # Query timeout in milliseconds
    } if "postgresql" in settings.DATABASE_URL else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base for models
Base = declarative_base()

# Thread pool for running blocking DB operations
_db_executor = ThreadPoolExecutor(max_workers=settings.DB_EXECUTOR_MAX_WORKERS, thread_name_prefix="db_init")


def get_db() -> Generator[Session, None, None]:
    """
    Database dependency for FastAPI endpoints

    Usage:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _create_performance_indexes(connection):
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
    ]

    for idx_name, table_name, columns in indexes:
        try:
            # Check if index exists before creating
            check_sql = text(f"""
                SELECT 1 FROM pg_indexes
                WHERE indexname = :idx_name
            """)
            result = connection.execute(check_sql, {"idx_name": idx_name})
            if not result.fetchone():
                create_sql = text(f"CREATE INDEX CONCURRENTLY IF NOT EXISTS {idx_name} ON {table_name} ({columns})")
                # CONCURRENTLY doesn't work inside a transaction, so we need to use a separate connection
                connection.execute(text(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name} ({columns})"))
                logger.info(f"Created index: {idx_name}")
            else:
                logger.debug(f"Index already exists: {idx_name}")
        except Exception as e:
            # Non-critical - just log and continue
            logger.warning(f"Could not create index {idx_name}: {e}")


def _init_db_sync():
    """
    Synchronous database initialization (runs in thread pool)
    """
    try:
        # Import all models here to ensure they're registered with Base
        import app.models  # noqa: F401 - Imports all models via __init__.py
        from sqlalchemy.exc import ProgrammingError

        # Use create_all with checkfirst, but handle duplicate index errors
        try:
            Base.metadata.create_all(bind=engine, checkfirst=True)
        except ProgrammingError as pe:
            # Ignore duplicate index/relation errors as they already exist
            if "already exists" in str(pe):
                logger.warning(f"Some database objects already exist: {pe}")
            else:
                raise

        # Create performance indexes
        try:
            with engine.connect() as connection:
                _create_performance_indexes(connection)
                connection.commit()
        except Exception as e:
            logger.warning(f"Could not create performance indexes: {e}")

        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


def init_db():
    """
    Initialize database (non-blocking version)
    Creates all tables defined in models
    """
    _init_db_sync()


async def init_db_async():
    """
    Initialize database asynchronously (non-blocking)
    Runs the blocking init_db in a thread pool to avoid blocking the event loop
    """
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(_db_executor, _init_db_sync)


def warm_connection_pool():
    """
    Pre-warm the connection pool by creating initial connections.
    This reduces latency on the first few requests.
    """
    try:
        # Create a few connections to warm up the pool
        connections = []
        for _ in range(min(3, engine.pool.size())):
            conn = engine.connect()
            connections.append(conn)

        # Return connections to the pool
        for conn in connections:
            conn.close()

        logger.info(f"Connection pool warmed up with {len(connections)} connections")
    except Exception as e:
        logger.warning(f"Could not warm up connection pool: {e}")

"""
Database Connection Management
==============================

Centralized database connection pooling and session management
for all features.

Features:
- Production-ready connection pooling
- Async session management
- Connection health checks
- Automatic connection recycling
- pgvector extension support
- Table creation and management
- Event listener registration for custom IDs
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker, AsyncEngine
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import text
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional, Any, Dict
import os

from app.core.logging_config import get_logger
from app.core.config import config

logger = get_logger(__name__)

# Create the declarative base for all models
Base = declarative_base()


class DatabaseManager:
    """
    Centralized database connection manager with production-ready pooling.

    All features use this shared connection pool to avoid connection exhaustion.
    """

    def __init__(self):
        self.engine: Optional[AsyncEngine] = None
        self.async_session_maker: Optional[async_sessionmaker[AsyncSession]] = None
        self._initialized = False
        self._event_listeners_registered = False

    def _build_connection_string(self, database_url: Optional[str] = None) -> str:
        """
        Build PostgreSQL connection string from configuration.

        Args:
            database_url: Optional database URL override

        Returns:
            str: PostgreSQL connection string for asyncpg
        """
        if database_url:
            return database_url

        # Try environment variable first
        env_url = os.getenv("DATABASE_URL")
        if env_url:
            return env_url

        # Build from config
        connection_string = (
            f"postgresql+asyncpg://{config.DB_USER}:{config.DB_PASSWORD}"
            f"@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}"
        )

        logger.debug("Database connection string built from config")
        return connection_string

    def init_database(
        self,
        database_url: Optional[str] = None,
        pool_size: int = 50,
        max_overflow: int = 100,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
        echo: bool = False
    ):
        """
        Initialize database with connection pooling.

        Args:
            database_url: Database connection string (from env/config if not provided)
            pool_size: Base number of connections to maintain
            max_overflow: Additional connections when pool is exhausted
            pool_timeout: Seconds to wait for available connection
            pool_recycle: Recycle connections after this many seconds
            echo: Enable SQL query logging (debug only)
        """
        if self._initialized:
            logger.warning("Database already initialized")
            return

        # Get database URL
        connection_string = self._build_connection_string(database_url)

        logger.info(
            "Initializing database connection pool",
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout
        )

        # Create async engine with connection pooling
        self.engine = create_async_engine(
            connection_string,
            pool_size=pool_size,              # Base pool size
            max_overflow=max_overflow,         # Additional connections
            pool_timeout=pool_timeout,         # Wait time for connection
            pool_recycle=pool_recycle,         # Recycle connections hourly
            pool_pre_ping=True,                # Test connections before use
            echo=echo,                         # SQL logging (False in prod)
            echo_pool=False,                   # Pool logging
            future=True,                       # Use SQLAlchemy 2.0 style
            connect_args={
                "server_settings": {
                    "jit": "off"  # Disable JIT for better performance with short queries
                }
            }
        )

        # Create session factory
        self.async_session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,            # Keep objects usable after commit
            autoflush=True,
            autocommit=False
        )

        self._initialized = True
        logger.info("Database connection pool initialized successfully")

    def is_initialized(self) -> bool:
        """Check if database is initialized."""
        return self._initialized

    async def test_connection(self) -> bool:
        """
        Test database connection.

        Returns:
            bool: True if connection is successful

        Raises:
            Exception: If connection test fails
        """
        if not self.engine:
            raise Exception("Database engine not initialized")

        try:
            async with self.engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                result.fetchone()

            logger.info("Database connection test successful")
            return True

        except Exception as e:
            logger.error(f"Database connection test failed: {str(e)}")
            raise

    async def enable_pgvector(self) -> None:
        """
        Enable pgvector extension in the database.

        Raises:
            Exception: If pgvector extension cannot be enabled
        """
        if not self.engine:
            raise Exception("Database engine not initialized")

        try:
            async with self.engine.begin() as conn:
                # Check if pgvector is already enabled
                result = await conn.execute(text(
                    "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"
                ))
                exists = result.fetchone()

                if exists and not exists[0]:
                    # Enable pgvector extension
                    await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                    logger.info("pgvector extension enabled")
                else:
                    logger.info("pgvector extension already enabled")

        except Exception as e:
            logger.error(f"Failed to enable pgvector extension: {str(e)}")
            raise

    async def register_event_listeners(self) -> None:
        """
        Register event listeners for custom ID generation.

        This should be called once after importing all models.
        """
        if self._event_listeners_registered:
            logger.debug("Event listeners already registered")
            return

        try:
            # Import all models from shared models to ensure they're registered
            from app.shared import models  # noqa: F401
            from app.utils.model_events import register_id_generators

            register_id_generators(Base)
            self._event_listeners_registered = True
            logger.info("ID generation event listeners registered")

        except Exception as e:
            logger.error(f"Failed to register event listeners: {str(e)}")
            raise

    async def create_all_tables(self) -> None:
        """
        Create all database tables defined in models.

        Raises:
            Exception: If table creation fails
        """
        if not self.engine:
            raise Exception("Database engine not initialized")

        try:
            # Import all models from shared models to ensure they're registered
            from app.shared import models  # noqa: F401

            # Register event listeners if not already done
            if not self._event_listeners_registered:
                await self.register_event_listeners()

            async with self.engine.begin() as conn:
                # Create all tables
                await conn.run_sync(Base.metadata.create_all)

            logger.info("All database tables created successfully")

        except Exception as e:
            logger.error(f"Failed to create database tables: {str(e)}")
            raise

    async def drop_all_tables(self) -> None:
        """
        Drop all database tables. USE WITH CAUTION!

        Raises:
            Exception: If table dropping fails
        """
        if not self.engine:
            raise Exception("Database engine not initialized")

        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)

            logger.warning("All database tables dropped")

        except Exception as e:
            logger.error(f"Failed to drop database tables: {str(e)}")
            raise

    async def execute_raw_sql(self, sql: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Execute raw SQL query.

        Args:
            sql: SQL query to execute
            params: Query parameters

        Returns:
            Any: Query result

        Raises:
            Exception: If query execution fails
        """
        if not self.engine:
            raise Exception("Database engine not initialized")

        try:
            async with self.engine.begin() as conn:
                result = await conn.execute(text(sql), params or {})
                return result.fetchall()

        except Exception as e:
            logger.error(f"Raw SQL execution failed: {str(e)}")
            raise

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get database session from the pool.

        Usage:
            async with db_manager.get_session() as session:
                result = await session.execute(query)

        Yields:
            AsyncSession: Database session
        """
        if not self._initialized or not self.async_session_maker:
            raise RuntimeError(
                "Database not initialized. Call init_database() first."
            )

        async with self.async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Database session error: {str(e)}")
                raise
            finally:
                await session.close()

    async def close(self):
        """Close database connections and cleanup"""
        if self.engine:
            logger.info("Closing database connections")
            await self.engine.dispose()
            self._initialized = False
            logger.info("Database connections closed")


# Global database manager instance
db_manager = DatabaseManager()


# Convenience function for getting sessions
@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Convenience function to get database session.

    Usage:
        from app.core.database import get_db_session

        async with get_db_session() as session:
            result = await session.execute(query)
    """
    async with db_manager.get_session() as session:
        yield session

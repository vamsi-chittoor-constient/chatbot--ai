"""
Database Connection Pool
========================
Reuse connections instead of creating new ones per request.

Before: ~50ms per connection (TCP handshake + auth + SSL)
After:  ~0.1ms (grab from pool)

This is a 500x speedup for database access!
"""
import asyncpg
import psycopg2
from psycopg2 import pool
from typing import Optional
import structlog
import os

logger = structlog.get_logger(__name__)

# ============================================================================
# ASYNC POOL (for asyncpg - used in async contexts)
# ============================================================================

_async_pool: Optional[asyncpg.Pool] = None


async def get_async_pool() -> asyncpg.Pool:
    """
    Get or create async connection pool.

    Pool maintains 5-20 connections ready to use.
    Connections are returned to pool after use, not closed.
    """
    global _async_pool

    if _async_pool is None:
        _async_pool = await asyncpg.create_pool(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5432)),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', '123456'),
            database=os.getenv('DB_NAME', 'restaurant_ai_dev'),
            min_size=5,      # Always keep 5 connections ready
            max_size=20,     # Scale up to 20 under load
            command_timeout=30,
        )
        logger.info("async_db_pool_created", min_size=5, max_size=20)

    return _async_pool


async def close_async_pool():
    """Close pool on shutdown."""
    global _async_pool
    if _async_pool:
        await _async_pool.close()
        _async_pool = None
        logger.info("async_db_pool_closed")


# ============================================================================
# SYNC POOL (for psycopg2 - used in CrewAI tools which run in threads)
# ============================================================================

_sync_pool: Optional[pool.ThreadedConnectionPool] = None


def get_sync_pool() -> pool.ThreadedConnectionPool:
    """
    Get or create sync connection pool for threaded contexts.

    CrewAI runs tools in threads, so we need thread-safe pooling.
    """
    global _sync_pool

    if _sync_pool is None:
        _sync_pool = pool.ThreadedConnectionPool(
            minconn=5,
            maxconn=20,
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5432)),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', '123456'),
            database=os.getenv('DB_NAME', 'restaurant_ai_dev'),
        )
        logger.info("sync_db_pool_created", min_size=5, max_size=20)

    return _sync_pool


def close_sync_pool():
    """Close pool on shutdown."""
    global _sync_pool
    if _sync_pool:
        _sync_pool.closeall()
        _sync_pool = None
        logger.info("sync_db_pool_closed")


# ============================================================================
# CONTEXT MANAGERS (Beautiful syntax for getting/returning connections)
# ============================================================================

class AsyncDBConnection:
    """
    Async context manager for pooled connections.

    Usage:
        async with AsyncDBConnection() as conn:
            rows = await conn.fetch("SELECT * FROM menu_item")
    """
    def __init__(self):
        self.conn = None
        self.pool = None

    async def __aenter__(self):
        self.pool = await get_async_pool()
        self.conn = await self.pool.acquire()
        return self.conn

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            await self.pool.release(self.conn)


class SyncDBConnection:
    """
    Sync context manager for pooled connections.

    Usage:
        with SyncDBConnection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM menu_item")
    """
    def __init__(self):
        self.conn = None
        self.pool = None

    def __enter__(self):
        self.pool = get_sync_pool()
        self.conn = self.pool.getconn()
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.pool.putconn(self.conn)

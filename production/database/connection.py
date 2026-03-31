import os
import asyncpg
import logging

logger = logging.getLogger(__name__)

_pool = None

async def get_db_pool():
    """
    Get or create the asyncpg connection pool.
    Provides a scalable, singleton pool for database connections.
    """
    global _pool
    if _pool is None:
        dsn = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/crm")
        try:
            # Optimal pool settings should be configured here (min_size, max_size)
            _pool = await asyncpg.create_pool(
                dsn,
                min_size=1,
                max_size=20,
                command_timeout=60
            )
            logger.info("Database connection pool created successfully.")
        except Exception as e:
            logger.error(f"Failed to create database connection pool: {e}")
            raise
    return _pool

async def close_db_pool():
    """Gracefully close the database connection pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("Database connection pool closed.")

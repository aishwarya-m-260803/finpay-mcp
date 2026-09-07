"""
Database connection management for FinPay MCP Server.

Provides an asyncpg connection pool with lazy initialisation
and clean shutdown.
"""

import os
from typing import Any, Optional

import asyncpg

_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    """Return the shared connection pool, creating it on first call."""
    global _pool
    if _pool is None:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise RuntimeError(
                "DATABASE_URL environment variable is not set. "
                "Copy .env.example to .env and fill in your credentials."
            )
        _pool = await asyncpg.create_pool(database_url, min_size=1, max_size=5)
    return _pool


async def close_pool() -> None:
    """Gracefully close the connection pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


async def check_connection() -> dict[str, Any]:
    """Run a lightweight query to verify database connectivity.

    Returns a dict with connection status and database version.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        version = await conn.fetchval("SELECT version()")
        table_count = await conn.fetchval(
            "SELECT count(*) FROM information_schema.tables "
            "WHERE table_schema = 'public'"
        )
    return {
        "status": "connected",
        "postgres_version": version,
        "public_tables": table_count,
    }


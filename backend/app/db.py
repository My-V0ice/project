from __future__ import annotations

import asyncpg

from app.core.config import DB_CONFIG


db_pool: asyncpg.Pool | None = None


async def connect_db() -> asyncpg.Pool:
    global db_pool
    if db_pool is None:
        db_pool = await asyncpg.create_pool(**DB_CONFIG)
    return db_pool


async def close_db() -> None:
    global db_pool
    if db_pool is not None:
        await db_pool.close()
        db_pool = None


def get_db_pool() -> asyncpg.Pool:
    if db_pool is None:
        raise RuntimeError("Database pool is not initialized")
    return db_pool

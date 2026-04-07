from fastapi import APIRouter

from app.db import get_db_pool


router = APIRouter(tags=["system"])


@router.get("/health")
async def health() -> dict[str, str]:
    pool = get_db_pool()
    async with pool.acquire() as connection:
        await connection.fetchval("SELECT 1")
    return {"status": "ok", "database": "connected"}

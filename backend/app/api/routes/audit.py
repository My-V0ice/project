from typing import Any

from fastapi import APIRouter, Depends

from app.db import get_db_pool
from app.deps import require_roles


router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/logs")
async def get_audit_logs(
    current_user: dict[str, Any] = Depends(require_roles("superadmin", "auditor")),
) -> list[dict[str, Any]]:
    pool = get_db_pool()
    async with pool.acquire() as connection:
        records = await connection.fetch(
            """
            SELECT a.id, a.actor_user_id, a.actor_role, a.action, a.entity_type, a.entity_id,
                   a.details, a.created_at, u.email AS actor_email, u.full_name AS actor_name
            FROM audit_logs a
            LEFT JOIN users u ON u.id = a.actor_user_id
            ORDER BY a.id DESC
            LIMIT 200
            """
        )
        return [dict(record) for record in records]

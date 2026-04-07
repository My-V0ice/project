import json
from typing import Any

import asyncpg


async def add_audit_log(
    connection: asyncpg.Connection,
    *,
    actor: dict[str, Any] | None,
    action: str,
    entity_type: str,
    entity_id: int | None,
    details: dict[str, Any] | None = None,
) -> None:
    await connection.execute(
        """
        INSERT INTO audit_logs (actor_user_id, actor_role, action, entity_type, entity_id, details)
        VALUES ($1, $2, $3, $4, $5, $6::jsonb)
        """,
        actor["id"] if actor else None,
        actor["role"] if actor else "system",
        action,
        entity_type,
        entity_id,
        json.dumps(details or {}, ensure_ascii=False),
    )

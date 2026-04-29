from typing import Any

from fastapi import APIRouter, Body, Depends

from app.db import get_db_pool
from app.deps import get_current_user, require_roles

from app.domain.constants import AWARD_CATEGORIES, ROLE_LABELS


router = APIRouter(prefix="/reference", tags=["reference"])


@router.get("/roles")
async def list_roles() -> list[dict[str, str]]:
    return [{"value": key, "label": label} for key, label in ROLE_LABELS.items()]


@router.get("/award-categories")
async def list_award_categories() -> list[str]:
    return AWARD_CATEGORIES


@router.get("/brand-settings")
async def get_brand_settings(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    pool = get_db_pool()
    async with pool.acquire() as connection:
        record = await connection.fetchrow(
            "SELECT * FROM brand_settings WHERE brand_name = $1",
            current_user["brand_name"],
        )
        if not record:
            record = await connection.fetchrow("SELECT * FROM brand_settings ORDER BY id ASC LIMIT 1")
    return dict(record) if record else {}


@router.put("/brand-settings")
async def update_brand_settings(
    payload: dict[str, Any] = Body(...),
    current_user: dict[str, Any] = Depends(require_roles("superadmin")),
) -> dict[str, Any]:
    allowed_fields = {
        "primary_color",
        "secondary_color",
        "font_family",
        "logo_svg",
        "page_margin_mm",
        "grid_step_mm",
        "locked",
    }
    updates = {key: value for key, value in payload.items() if key in allowed_fields}
    if not updates:
        return await get_brand_settings(current_user)

    assignments = []
    values: list[Any] = []
    for index, (key, value) in enumerate(updates.items(), start=1):
        assignments.append(f"{key} = ${index}")
        values.append(value)
    values.append(current_user["brand_name"])
    pool = get_db_pool()
    async with pool.acquire() as connection:
        record = await connection.fetchrow(
            f"""
            UPDATE brand_settings
            SET {', '.join(assignments)}, updated_at = CURRENT_TIMESTAMP
            WHERE brand_name = ${len(values)}
            RETURNING *
            """,
            *values,
        )
        if not record:
            await connection.execute(
                """
                INSERT INTO brand_settings (brand_name)
                VALUES ($1)
                """,
                current_user["brand_name"],
            )
            record = await connection.fetchrow(
                f"""
                UPDATE brand_settings
                SET {', '.join(assignments)}, updated_at = CURRENT_TIMESTAMP
                WHERE brand_name = ${len(values)}
                RETURNING *
                """,
                *values,
            )
    return dict(record)


@router.get("/email-logs")
async def list_email_logs(
    current_user: dict[str, Any] = Depends(require_roles("superadmin", "auditor")),
) -> list[dict[str, Any]]:
    pool = get_db_pool()
    async with pool.acquire() as connection:
        records = await connection.fetch(
            """
            SELECT el.*, d.number AS document_number
            FROM email_logs el
            LEFT JOIN documents d ON d.id = el.document_id
            ORDER BY el.id DESC
            LIMIT 100
            """
        )
    return [dict(record) for record in records]


@router.get("/consent-history")
async def list_consent_history(
    current_user: dict[str, Any] = Depends(require_roles("superadmin", "auditor")),
) -> list[dict[str, Any]]:
    pool = get_db_pool()
    async with pool.acquire() as connection:
        records = await connection.fetch(
            """
            SELECT ch.*, u.email, u.full_name
            FROM consent_history ch
            JOIN users u ON u.id = ch.user_id
            ORDER BY ch.id DESC
            LIMIT 100
            """
        )
    return [dict(record) for record in records]

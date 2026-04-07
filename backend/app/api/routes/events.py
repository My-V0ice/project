from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from app.db import get_db_pool
from app.deps import get_current_user, require_roles
from app.schemas.events import EventCreate, ParticipantImport
from app.services.audit import add_audit_log
from app.utils.users import mask_email, mask_name


router = APIRouter(tags=["events"])


@router.get("/events")
async def get_events(current_user: dict[str, Any] = Depends(get_current_user)) -> list[dict[str, Any]]:
    pool = get_db_pool()
    async with pool.acquire() as connection:
        records = await connection.fetch(
            """
            SELECT e.*,
                   COUNT(DISTINCT p.id) AS participants_count,
                   COUNT(DISTINCT d.id) AS documents_count
            FROM events e
            LEFT JOIN participants p ON p.event_id = e.id
            LEFT JOIN documents d ON d.event_id = e.id
            GROUP BY e.id
            ORDER BY e.start_date DESC, e.id DESC
            """
        )
        return [dict(record) for record in records]


@router.post("/events", status_code=201)
async def create_event(
    payload: EventCreate,
    current_user: dict[str, Any] = Depends(require_roles("superadmin", "division_admin")),
) -> dict[str, Any]:
    pool = get_db_pool()
    async with pool.acquire() as connection:
        record = await connection.fetchrow(
            """
            INSERT INTO events (
                title, organizer, start_date, end_date, event_type, description,
                contact_email, brand_name, division_name, created_by, status
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, 'draft')
            RETURNING *
            """,
            payload.title,
            payload.organizer,
            payload.start_date,
            payload.end_date,
            payload.event_type,
            payload.description,
            payload.contact_email,
            payload.brand_name,
            payload.division_name,
            current_user["id"],
        )
        await add_audit_log(
            connection,
            actor=current_user,
            action="event.created",
            entity_type="event",
            entity_id=record["id"],
            details={"title": payload.title},
        )
        return dict(record)


@router.get("/events/{event_id}/participants")
async def get_event_participants(
    event_id: int,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> list[dict[str, Any]]:
    pool = get_db_pool()
    async with pool.acquire() as connection:
        records = await connection.fetch(
            """
            SELECT p.*,
                   COUNT(d.id) AS documents_count
            FROM participants p
            LEFT JOIN documents d ON d.participant_id = p.id
            WHERE p.event_id = $1
            GROUP BY p.id
            ORDER BY p.id DESC
            """,
            event_id,
        )

    items = []
    for record in records:
        item = dict(record)
        if current_user["role"] == "reviewer":
            item["full_name"] = mask_name(item["full_name"])
            item["email"] = mask_email(item["email"])
            item["achievement"] = "Скрыто по роли"
            item["personal_link_token"] = None
        items.append(item)
    return items


@router.post("/events/{event_id}/participants/import", status_code=201)
async def import_participants(
    event_id: int,
    payload: ParticipantImport,
    current_user: dict[str, Any] = Depends(require_roles("superadmin", "division_admin")),
) -> dict[str, Any]:
    pool = get_db_pool()
    async with pool.acquire() as connection:
        event_exists = await connection.fetchval("SELECT id FROM events WHERE id = $1", event_id)
        if not event_exists:
            raise HTTPException(status_code=404, detail="Мероприятие не найдено")

        inserted = 0
        for participant in payload.participants:
            await connection.execute(
                """
                INSERT INTO participants (
                    event_id, full_name, email, status, achievement, hours, award_category, personal_link_token
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                event_id,
                participant.full_name,
                participant.email,
                participant.status,
                participant.achievement,
                participant.hours,
                participant.award_category,
                uuid4().hex,
            )
            inserted += 1

        await add_audit_log(
            connection,
            actor=current_user,
            action="participants.imported",
            entity_type="event",
            entity_id=event_id,
            details={"count": inserted},
        )
        return {"inserted": inserted}

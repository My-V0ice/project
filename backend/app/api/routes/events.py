from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from app.db import get_db_pool
from app.deps import get_current_user, require_roles
from app.domain.constants import AWARD_CATEGORIES, ROLE_LABELS
from app.schemas.events import EventCreate, ParticipantAssignUsers
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


@router.get("/users/registered")
async def list_registered_users(
    current_user: dict[str, Any] = Depends(require_roles("superadmin", "division_admin")),
) -> list[dict[str, Any]]:
    pool = get_db_pool()
    async with pool.acquire() as connection:
        records = await connection.fetch(
            """
            SELECT id, email, full_name, role, brand_name, division_name
            FROM users
            ORDER BY full_name ASC, id ASC
            """
        )
        return [
            {
                **dict(record),
                "role_label": ROLE_LABELS.get(record["role"], record["role"]),
            }
            for record in records
        ]


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
            item["achievement"] = "Hidden by role"
            item["personal_link_token"] = None
        items.append(item)
    return items


@router.post("/events/{event_id}/participants/add-users", status_code=201)
async def add_registered_users_to_event(
    event_id: int,
    payload: ParticipantAssignUsers,
    current_user: dict[str, Any] = Depends(require_roles("superadmin", "division_admin")),
) -> dict[str, Any]:
    pool = get_db_pool()
    async with pool.acquire() as connection:
        event_exists = await connection.fetchval("SELECT id FROM events WHERE id = $1", event_id)
        if not event_exists:
            raise HTTPException(status_code=404, detail="Event not found")

        users = await connection.fetch(
            """
            SELECT id, full_name, email
            FROM users
            WHERE id = ANY($1::int[])
            """,
            payload.user_ids,
        )
        user_by_id = {user["id"]: user for user in users}

        missing_user_ids = [user_id for user_id in payload.user_ids if user_id not in user_by_id]
        if len(missing_user_ids) == len(payload.user_ids):
            raise HTTPException(status_code=400, detail="No registered users were found")

        existing_email_records = await connection.fetch(
            """
            SELECT email
            FROM participants
            WHERE event_id = $1 AND email = ANY($2::varchar[])
            """,
            event_id,
            [user["email"] for user in users],
        )
        existing_email_values = {record["email"] for record in existing_email_records}

        inserted = 0
        skipped_existing = 0
        for user_id in payload.user_ids:
            user = user_by_id.get(user_id)
            if not user:
                continue
            if user["email"] in existing_email_values:
                skipped_existing += 1
                continue

            await connection.execute(
                """
                INSERT INTO participants (
                    event_id, full_name, email, status, achievement, hours, award_category, personal_link_token
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                event_id,
                user["full_name"],
                user["email"],
                payload.status,
                payload.achievement,
                payload.hours,
                payload.award_category or (AWARD_CATEGORIES[0] if AWARD_CATEGORIES else ""),
                uuid4().hex,
            )
            inserted += 1
            existing_email_values.add(user["email"])

        await add_audit_log(
            connection,
            actor=current_user,
            action="participants.added_from_registered_users",
            entity_type="event",
            entity_id=event_id,
            details={
                "requested": len(payload.user_ids),
                "inserted": inserted,
                "skipped_existing": skipped_existing,
                "missing_user_ids": missing_user_ids,
            },
        )

        return {
            "requested": len(payload.user_ids),
            "inserted": inserted,
            "skipped_existing": skipped_existing,
            "missing_user_ids": missing_user_ids,
        }

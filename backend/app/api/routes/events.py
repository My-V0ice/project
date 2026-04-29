from typing import Any
from uuid import uuid4
import json

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.db import get_db_pool
from app.deps import get_current_user, require_roles
from app.domain.constants import AWARD_CATEGORIES, ROLE_LABELS
from app.schemas.events import EventCreate, ParticipantAssignUsers
from app.services.audit import add_audit_log
from app.services.participant_import import guess_mapping, parse_participant_file
from app.utils.users import mask_email, mask_name


router = APIRouter(tags=["events"])


def normalize_import_row(raw: dict[str, str], mapping: dict[str, str]) -> tuple[dict[str, Any], list[str]]:
    def value(field: str, default: str = "") -> str:
        source = mapping.get(field, "")
        return str(raw.get(source, default) or default).strip()

    normalized = {
        "full_name": value("full_name"),
        "email": value("email").lower(),
        "status": value("status", "Подтвержден"),
        "achievement": value("achievement"),
        "hours": 0,
        "award_category": value("award_category", AWARD_CATEGORIES[0]),
    }
    errors = []
    if len(normalized["full_name"]) < 3:
        errors.append("ФИО короче 3 символов")
    if "@" not in normalized["email"] or "." not in normalized["email"]:
        errors.append("Некорректный email")
    try:
        normalized["hours"] = int(value("hours", "0") or 0)
        if normalized["hours"] < 0 or normalized["hours"] > 1000:
            errors.append("Часы должны быть от 0 до 1000")
    except ValueError:
        errors.append("Часы должны быть числом")
    if normalized["award_category"] not in AWARD_CATEGORIES:
        errors.append("Неизвестная категория награды")
    return normalized, errors


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


@router.post("/events/{event_id}/participants/import/preview", status_code=201)
async def preview_participant_import(
    event_id: int,
    file: UploadFile = File(...),
    current_user: dict[str, Any] = Depends(require_roles("superadmin", "division_admin")),
) -> dict[str, Any]:
    content = await file.read()
    headers, rows = parse_participant_file(file.filename or "participants.csv", content)
    mapping = guess_mapping(headers)
    pool = get_db_pool()
    async with pool.acquire() as connection:
        event_exists = await connection.fetchval("SELECT id FROM events WHERE id = $1", event_id)
        if not event_exists:
            raise HTTPException(status_code=404, detail="Мероприятие не найдено")

        normalized_rows = []
        rows_valid = 0
        for index, row in enumerate(rows, start=2):
            normalized, errors = normalize_import_row(row, mapping)
            if not errors:
                rows_valid += 1
            normalized_rows.append((index, row, normalized, errors))

        batch_id = await connection.fetchval(
            """
            INSERT INTO participant_import_batches (
                event_id, uploaded_by, filename, field_mapping, rows_total, rows_valid, rows_failed, status
            )
            VALUES ($1, $2, $3, $4::jsonb, $5, $6, $7, 'preview')
            RETURNING id
            """,
            event_id,
            current_user["id"],
            file.filename or "participants.csv",
            json.dumps(mapping, ensure_ascii=False),
            len(rows),
            rows_valid,
            len(rows) - rows_valid,
        )
        for row_number, raw, normalized, errors in normalized_rows:
            await connection.execute(
                """
                INSERT INTO participant_import_rows (batch_id, row_number, raw_data, normalized_data, errors)
                VALUES ($1, $2, $3::jsonb, $4::jsonb, $5::jsonb)
                """,
                batch_id,
                row_number,
                json.dumps(raw, ensure_ascii=False),
                json.dumps(normalized, ensure_ascii=False),
                json.dumps(errors, ensure_ascii=False),
            )

        await add_audit_log(
            connection,
            actor=current_user,
            action="participants.import_previewed",
            entity_type="event",
            entity_id=event_id,
            details={"batch_id": batch_id, "rows_total": len(rows), "rows_valid": rows_valid},
        )

    return {
        "batch_id": batch_id,
        "headers": headers,
        "mapping": mapping,
        "rows_total": len(rows),
        "rows_valid": rows_valid,
        "rows_failed": len(rows) - rows_valid,
        "sample": [
            {"row_number": row_number, "data": normalized, "errors": errors}
            for row_number, _, normalized, errors in normalized_rows[:10]
        ],
    }


@router.post("/events/{event_id}/participants/import/{batch_id}/commit")
async def commit_participant_import(
    event_id: int,
    batch_id: int,
    current_user: dict[str, Any] = Depends(require_roles("superadmin", "division_admin")),
) -> dict[str, Any]:
    pool = get_db_pool()
    async with pool.acquire() as connection:
        batch = await connection.fetchrow(
            "SELECT * FROM participant_import_batches WHERE id = $1 AND event_id = $2",
            batch_id,
            event_id,
        )
        if not batch:
            raise HTTPException(status_code=404, detail="Пакет импорта не найден")
        rows = await connection.fetch(
            """
            SELECT *
            FROM participant_import_rows
            WHERE batch_id = $1 AND jsonb_array_length(errors) = 0
            ORDER BY row_number ASC
            """,
            batch_id,
        )
        existing_email_records = await connection.fetch(
            "SELECT email FROM participants WHERE event_id = $1",
            event_id,
        )
        existing_emails = {record["email"].lower() for record in existing_email_records}
        imported = 0
        skipped_existing = 0
        for row in rows:
            data = row["normalized_data"]
            if isinstance(data, str):
                data = json.loads(data)
            else:
                data = dict(data)
            if data["email"].lower() in existing_emails:
                skipped_existing += 1
                continue
            participant_id = await connection.fetchval(
                """
                INSERT INTO participants (
                    event_id, full_name, email, status, achievement, hours, award_category, personal_link_token
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id
                """,
                event_id,
                data["full_name"],
                data["email"],
                data["status"],
                data["achievement"],
                data["hours"],
                data["award_category"],
                uuid4().hex,
            )
            await connection.execute(
                "UPDATE participant_import_rows SET imported_participant_id = $1 WHERE id = $2",
                participant_id,
                row["id"],
            )
            existing_emails.add(data["email"].lower())
            imported += 1
        await connection.execute(
            """
            UPDATE participant_import_batches
            SET rows_imported = $1, status = 'committed'
            WHERE id = $2
            """,
            imported,
            batch_id,
        )
        await add_audit_log(
            connection,
            actor=current_user,
            action="participants.import_committed",
            entity_type="event",
            entity_id=event_id,
            details={"batch_id": batch_id, "imported": imported, "skipped_existing": skipped_existing},
        )
    return {"imported": imported, "skipped_existing": skipped_existing, "batch_id": batch_id}

from datetime import datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from app.core.config import FRONTEND_URL
from app.db import get_db_pool
from app.deps import get_current_user, require_roles
from app.schemas.documents import ConsentUpdate, IssueDocumentsRequest, TemplateCreate
from app.services.audit import add_audit_log
from app.services.document_assets import ensure_document_assets


router = APIRouter(tags=["documents"])


@router.get("/templates")
async def get_templates(current_user: dict[str, Any] = Depends(get_current_user)) -> list[dict[str, Any]]:
    pool = get_db_pool()
    async with pool.acquire() as connection:
        records = await connection.fetch(
            """
            SELECT t.*,
                   COALESCE(COUNT(d.id), 0) AS documents_generated
            FROM templates t
            LEFT JOIN documents d ON d.template_id = t.id
            GROUP BY t.id
            ORDER BY t.id DESC
            """
        )
        return [dict(record) for record in records]


@router.post("/templates", status_code=201)
async def create_template(
    payload: TemplateCreate,
    current_user: dict[str, Any] = Depends(require_roles("superadmin", "division_admin")),
) -> dict[str, Any]:
    pool = get_db_pool()
    async with pool.acquire() as connection:
        record = await connection.fetchrow(
            """
            INSERT INTO templates (
                name, orientation, description, allowed_fields, brand_book_locked,
                brand_name, created_by, layout_config
            )
            VALUES ($1, $2, $3, $4::jsonb, TRUE, $5, $6, $7::jsonb)
            RETURNING *
            """,
            payload.name,
            payload.orientation,
            payload.description,
            payload.allowed_fields,
            current_user["brand_name"],
            current_user["id"],
            {
                "fonts_locked": True,
                "colors_locked": True,
                "logos_locked": True,
                "grid_locked": True,
                "page": "A4",
            },
        )
        await add_audit_log(
            connection,
            actor=current_user,
            action="template.created",
            entity_type="template",
            entity_id=record["id"],
            details={"name": payload.name},
        )
        return dict(record)


@router.get("/documents")
async def get_documents() -> list[dict[str, Any]]:
    pool = get_db_pool()
    async with pool.acquire() as connection:
        records = await connection.fetch(
            """
            SELECT d.*, p.full_name, p.email, p.status AS participant_status, p.award_category,
                   p.personal_link_token, e.title AS event_title, t.name AS template_name
            FROM documents d
            JOIN participants p ON p.id = d.participant_id
            JOIN events e ON e.id = d.event_id
            JOIN templates t ON t.id = d.template_id
            ORDER BY d.id DESC
            """
        )

    return [dict(record) for record in records]


@router.get("/documents/id/{document_id}")
async def get_document_by_id(
    document_id: int,
) -> dict[str, Any]:
    pool = get_db_pool()
    async with pool.acquire() as connection:
        record = await connection.fetchrow(
            """
            SELECT d.*, p.full_name, p.email, p.status AS participant_status, p.award_category,
                   p.personal_link_token, e.title AS event_title, t.name AS template_name
            FROM documents d
            JOIN participants p ON p.id = d.participant_id
            JOIN events e ON e.id = d.event_id
            JOIN templates t ON t.id = d.template_id
            WHERE d.id = $1
            """,
            document_id,
        )
        if not record:
            raise HTTPException(status_code=404, detail="Документ не найден")

    item = dict(record)
    ensure_document_assets(item["number"])
    return item


@router.get("/templates/{template_id}")
async def get_template_by_id(
    template_id: int,
) -> dict[str, Any]:
    pool = get_db_pool()
    async with pool.acquire() as connection:
        record = await connection.fetchrow(
            """
            SELECT t.*,
                   COALESCE(COUNT(d.id), 0) AS documents_generated
            FROM templates t
            LEFT JOIN documents d ON d.template_id = t.id
            WHERE t.id = $1
            GROUP BY t.id
            """,
            template_id,
        )
        if not record:
            raise HTTPException(status_code=404, detail="Шаблон не найден")
        return dict(record)


@router.post("/documents/issue", status_code=201)
async def issue_documents(
    payload: IssueDocumentsRequest,
    current_user: dict[str, Any] = Depends(require_roles("superadmin", "division_admin")),
) -> dict[str, Any]:
    pool = get_db_pool()
    async with pool.acquire() as connection:
        event_record = await connection.fetchrow("SELECT id, title FROM events WHERE id = $1", payload.event_id)
        if not event_record:
            raise HTTPException(status_code=404, detail="Мероприятие не найдено")

        template_record = await connection.fetchrow("SELECT id, name FROM templates WHERE id = $1", payload.template_id)
        if not template_record:
            raise HTTPException(status_code=404, detail="Шаблон не найден")

        participants = await connection.fetch(
            "SELECT * FROM participants WHERE event_id = $1 ORDER BY id",
            payload.event_id,
        )
        if not participants:
            raise HTTPException(status_code=400, detail="Для мероприятия нет участников")

        issued_count = 0
        for participant in participants:
            existing = await connection.fetchval(
                "SELECT id FROM documents WHERE event_id = $1 AND participant_id = $2",
                payload.event_id,
                participant["id"],
            )
            if existing:
                continue

            verification_code = uuid4().hex[:12]
            document_number = f"TOGU-{datetime.now().year}-{participant['id']:05d}"
            await connection.execute(
                """
                INSERT INTO documents (
                    event_id, participant_id, template_id, number, verification_code, qr_link,
                    pdf_url, archive_url, image_url, signature_status, signature_type,
                    signatory_name, signatory_position, issued_by, issued_at, status, email_sent_at
                )
                VALUES (
                    $1, $2, $3, $4, $5, $6,
                    $7, $8, $9, $10, $11,
                    $12, $13, $14, CURRENT_TIMESTAMP, $15, $16
                )
                """,
                payload.event_id,
                participant["id"],
                payload.template_id,
                document_number,
                verification_code,
                f"{FRONTEND_URL}/verify/{verification_code}",
                f"/documents/{document_number}.pdf",
                f"/documents/{document_number}.pdfa",
                f"/documents/{document_number}.png",
                "Подписан УКЭП" if payload.signature_type == "УКЭП" else "Подписан",
                payload.signature_type,
                payload.signatory_name,
                payload.signatory_position,
                current_user["id"],
                "delivered" if payload.send_email else "issued",
                datetime.now() if payload.send_email else None,
            )
            ensure_document_assets(document_number)
            issued_count += 1

        await connection.execute("UPDATE events SET status = 'completed' WHERE id = $1", payload.event_id)
        await add_audit_log(
            connection,
            actor=current_user,
            action="documents.issued",
            entity_type="event",
            entity_id=payload.event_id,
            details={"count": issued_count, "template_id": payload.template_id, "send_email": payload.send_email},
        )
        return {"issued": issued_count, "event_title": event_record["title"], "template_name": template_record["name"]}


@router.get("/documents/{verification_code}/verify")
async def verify_document(verification_code: str) -> dict[str, Any]:
    pool = get_db_pool()
    async with pool.acquire() as connection:
        record = await connection.fetchrow(
            """
            SELECT d.number, d.qr_link, d.signature_status, d.signature_type, d.issued_at, d.status,
                   d.signatory_name, d.signatory_position,
                   p.full_name, p.status AS participant_status, p.award_category, p.hours,
                   e.title AS event_title, e.start_date, e.end_date,
                   t.name AS template_name
            FROM documents d
            JOIN participants p ON p.id = d.participant_id
            JOIN events e ON e.id = d.event_id
            JOIN templates t ON t.id = d.template_id
            WHERE d.verification_code = $1
            """,
            verification_code,
        )
        if not record:
            raise HTTPException(status_code=404, detail="Документ не найден")
        return dict(record)


@router.get("/recipient/documents")
async def recipient_documents(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    pool = get_db_pool()
    async with pool.acquire() as connection:
        records = await connection.fetch(
            """
            SELECT d.id, d.number, d.status, d.qr_link, d.pdf_url, d.archive_url, d.image_url,
                   d.signature_status, d.signature_type, d.signatory_name, d.signatory_position,
                   d.issued_at, d.email_sent_at,
                   p.personal_link_token, p.status AS participant_status, p.award_category, p.hours,
                   e.title AS event_title, e.start_date, e.end_date
            FROM documents d
            JOIN participants p ON p.id = d.participant_id
            JOIN events e ON e.id = d.event_id
            WHERE p.email = $1
            ORDER BY d.id DESC
            """,
            current_user["email"],
        )
        return {"consent_to_processing": current_user["consent_to_processing"], "documents": [dict(record) for record in records]}


@router.get("/recipient/link/{token}")
async def recipient_link_documents(token: str) -> dict[str, Any]:
    pool = get_db_pool()
    async with pool.acquire() as connection:
        records = await connection.fetch(
            """
            SELECT d.id, d.number, d.status, d.qr_link, d.pdf_url, d.archive_url, d.image_url,
                   d.signature_status, d.signature_type, d.signatory_name, d.signatory_position,
                   d.issued_at, d.email_sent_at,
                   p.full_name, p.email, p.status AS participant_status, p.award_category, p.hours,
                   e.title AS event_title, e.start_date, e.end_date
            FROM participants p
            JOIN documents d ON d.participant_id = p.id
            JOIN events e ON e.id = d.event_id
            WHERE p.personal_link_token = $1
            ORDER BY d.id DESC
            """,
            token,
        )
        if not records:
            raise HTTPException(status_code=404, detail="Персональная ссылка не найдена")
        return {"documents": [dict(record) for record in records]}


@router.put("/recipient/consent")
async def update_consent(
    payload: ConsentUpdate,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    pool = get_db_pool()
    async with pool.acquire() as connection:
        await connection.execute(
            "UPDATE users SET consent_to_processing = $1 WHERE id = $2",
            payload.consent_to_processing,
            current_user["id"],
        )
        await add_audit_log(
            connection,
            actor=current_user,
            action="recipient.consent_updated",
            entity_type="user",
            entity_id=current_user["id"],
            details={"consent_to_processing": payload.consent_to_processing},
        )
        return {"consent_to_processing": payload.consent_to_processing}

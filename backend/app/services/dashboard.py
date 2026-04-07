from typing import Any

from app.db import get_db_pool
from app.utils.users import mask_email, mask_name


async def build_dashboard_summary(current_user: dict[str, Any]) -> dict[str, Any]:
    pool = get_db_pool()
    async with pool.acquire() as connection:
        stats = await connection.fetchrow(
            """
            SELECT
                (SELECT COUNT(*) FROM events) AS events_count,
                (SELECT COUNT(*) FROM participants) AS participants_count,
                (SELECT COUNT(*) FROM templates) AS templates_count,
                (SELECT COUNT(*) FROM documents) AS documents_count,
                (SELECT COUNT(*) FROM documents WHERE status = 'issued') AS issued_count,
                (SELECT COUNT(*) FROM audit_logs) AS audit_count
            """
        )

        upcoming_events = await connection.fetch(
            """
            SELECT id, title, organizer, start_date, end_date, event_type, brand_name, division_name, created_at
            FROM events
            ORDER BY start_date DESC, id DESC
            LIMIT 5
            """
        )

        recent_documents = await connection.fetch(
            """
            SELECT d.id, d.number, d.status, d.signature_type, d.issued_at,
                   p.full_name, p.email, e.title AS event_title
            FROM documents d
            JOIN participants p ON p.id = d.participant_id
            JOIN events e ON e.id = d.event_id
            ORDER BY d.id DESC
            LIMIT 5
            """
        )

    return {
        "current_user": current_user,
        "capabilities": {
            "can_manage_settings": current_user["role"] == "superadmin",
            "can_manage_events": current_user["role"] in {"superadmin", "division_admin"},
            "can_issue_documents": current_user["role"] in {"superadmin", "division_admin"},
            "can_review_registry": current_user["role"] in {"superadmin", "division_admin", "reviewer"},
            "can_view_audit": current_user["role"] in {"superadmin", "auditor"},
            "can_view_recipient_area": True,
        },
        "stats": {
            "events": stats["events_count"],
            "participants": stats["participants_count"],
            "templates": stats["templates_count"],
            "documents": stats["documents_count"],
            "issued_documents": stats["issued_count"],
            "audit_entries": stats["audit_count"],
        },
        "upcoming_events": [dict(record) for record in upcoming_events],
        "recent_documents": [
            {
                "id": record["id"],
                "number": record["number"],
                "status": record["status"],
                "signature_type": record["signature_type"],
                "issued_at": record["issued_at"],
                "participant_name": mask_name(record["full_name"]) if current_user["role"] == "reviewer" else record["full_name"],
                "participant_email": mask_email(record["email"]) if current_user["role"] == "reviewer" else record["email"],
                "event_title": record["event_title"],
            }
            for record in recent_documents
        ],
        "brand_requirements": {
            "colors_locked": True,
            "fonts_locked": True,
            "logos_locked": True,
            "grid_locked": True,
            "compliance_notes": [
                "Шаблоны должны соответствовать брендбуку ТОГУ.",
                "Персональные данные обрабатываются в рамках 152-ФЗ.",
                "Изменение фирменных параметров вне разрешенных полей запрещено.",
            ],
        },
    }

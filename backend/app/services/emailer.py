from __future__ import annotations

from email.message import EmailMessage
import smtplib
from typing import Any

import asyncpg

from app.core.config import SMTP_CONFIG


async def log_email(
    connection: asyncpg.Connection,
    *,
    document_id: int | None,
    recipient_email: str,
    subject: str,
    body: str,
    status: str,
    error_message: str = "",
) -> None:
    await connection.execute(
        """
        INSERT INTO email_logs (document_id, recipient_email, subject, body, status, error_message)
        VALUES ($1, $2, $3, $4, $5, $6)
        """,
        document_id,
        recipient_email,
        subject,
        body,
        status,
        error_message,
    )


async def send_document_email(connection: asyncpg.Connection, document: dict[str, Any]) -> str:
    subject = f"Документ ТОГУ {document['number']}"
    body = (
        f"Здравствуйте, {document['full_name']}!\n\n"
        f"Ваш документ по мероприятию «{document['event_title']}» выпущен.\n"
        f"Проверка подлинности: {document['qr_link']}\n"
    )

    if not SMTP_CONFIG["host"]:
        await log_email(
            connection,
            document_id=document["id"],
            recipient_email=document["email"],
            subject=subject,
            body=body,
            status="logged",
            error_message="SMTP_HOST не задан, письмо не отправлено",
        )
        return "logged"

    message = EmailMessage()
    message["From"] = SMTP_CONFIG["from_email"]
    message["To"] = document["email"]
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP(SMTP_CONFIG["host"], SMTP_CONFIG["port"], timeout=20) as smtp:
            if SMTP_CONFIG["use_tls"]:
                smtp.starttls()
            if SMTP_CONFIG["user"]:
                smtp.login(SMTP_CONFIG["user"], SMTP_CONFIG["password"])
            smtp.send_message(message)
        await log_email(
            connection,
            document_id=document["id"],
            recipient_email=document["email"],
            subject=subject,
            body=body,
            status="sent",
        )
        return "sent"
    except Exception as exc:
        await log_email(
            connection,
            document_id=document["id"],
            recipient_email=document["email"],
            subject=subject,
            body=body,
            status="failed",
            error_message=str(exc),
        )
        return "failed"

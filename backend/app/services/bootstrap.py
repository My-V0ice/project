from datetime import datetime
from uuid import uuid4

import asyncpg

from app.core.config import FRONTEND_URL
from app.db import get_db_pool
from app.services.audit import add_audit_log


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(30) NOT NULL DEFAULT 'division_admin',
    brand_name VARCHAR(150) NOT NULL DEFAULT 'ТОГУ',
    division_name VARCHAR(150) NOT NULL DEFAULT 'Цифровая кафедра',
    consent_to_processing BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name VARCHAR(150) NOT NULL DEFAULT 'Новый пользователь';
ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(30) NOT NULL DEFAULT 'division_admin';
ALTER TABLE users ADD COLUMN IF NOT EXISTS brand_name VARCHAR(150) NOT NULL DEFAULT 'ТОГУ';
ALTER TABLE users ADD COLUMN IF NOT EXISTS division_name VARCHAR(150) NOT NULL DEFAULT 'Цифровая кафедра';
ALTER TABLE users ADD COLUMN IF NOT EXISTS consent_to_processing BOOLEAN NOT NULL DEFAULT TRUE;

CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    organizer VARCHAR(200) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    event_type VARCHAR(120) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    contact_email VARCHAR(255) NOT NULL,
    brand_name VARCHAR(150) NOT NULL,
    division_name VARCHAR(150) NOT NULL,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'draft',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS participants (
    id SERIAL PRIMARY KEY,
    event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(255) NOT NULL,
    status VARCHAR(120) NOT NULL,
    achievement TEXT NOT NULL DEFAULT '',
    hours INTEGER NOT NULL DEFAULT 0,
    award_category VARCHAR(50) NOT NULL,
    personal_link_token VARCHAR(64) UNIQUE NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    orientation VARCHAR(20) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    allowed_fields JSONB NOT NULL DEFAULT '[]'::jsonb,
    brand_book_locked BOOLEAN NOT NULL DEFAULT TRUE,
    brand_name VARCHAR(150) NOT NULL,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    layout_config JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    participant_id INTEGER NOT NULL REFERENCES participants(id) ON DELETE CASCADE,
    template_id INTEGER NOT NULL REFERENCES templates(id) ON DELETE RESTRICT,
    number VARCHAR(50) UNIQUE NOT NULL,
    verification_code VARCHAR(64) UNIQUE NOT NULL,
    qr_link TEXT NOT NULL,
    pdf_url TEXT NOT NULL,
    archive_url TEXT NOT NULL,
    image_url TEXT NOT NULL,
    signature_status VARCHAR(120) NOT NULL,
    signature_type VARCHAR(50) NOT NULL,
    signatory_name VARCHAR(150) NOT NULL,
    signatory_position VARCHAR(150) NOT NULL,
    issued_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    issued_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    email_sent_at TIMESTAMP NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'issued'
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    actor_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    actor_role VARCHAR(30) NOT NULL,
    action VARCHAR(120) NOT NULL,
    entity_type VARCHAR(60) NOT NULL,
    entity_id INTEGER NULL,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


async def create_schema(connection: asyncpg.Connection) -> None:
    await connection.execute(SCHEMA_SQL)


async def seed_initial_data() -> None:
    pool = get_db_pool()
    async with pool.acquire() as connection:
        event_count = await connection.fetchval("SELECT COUNT(*) FROM events")
        if event_count:
            return

        event_id = await connection.fetchval(
            """
            INSERT INTO events (
                title, organizer, start_date, end_date, event_type, description,
                contact_email, brand_name, division_name, created_by, status
            )
            VALUES (
                'Форум студенческих инициатив',
                'ТОГУ',
                CURRENT_DATE - 5,
                CURRENT_DATE - 4,
                'Форум',
                'Пилотное мероприятие для демонстрации выпуска документов.',
                'events@togu.example',
                'ТОГУ',
                'Управление молодежной политики',
                NULL,
                'completed'
            )
            RETURNING id
            """
        )

        template_id = await connection.fetchval(
            """
            INSERT INTO templates (
                name, orientation, description, allowed_fields, brand_book_locked,
                brand_name, created_by, layout_config
            )
            VALUES (
                'Сертификат участника ТОГУ',
                'landscape',
                'Базовый шаблон по брендбуку ТОГУ.',
                $1::jsonb,
                TRUE,
                'ТОГУ',
                NULL,
                $2::jsonb
            )
            RETURNING id
            """,
            [
                "full_name",
                "status",
                "event_title",
                "event_date",
                "hours",
                "document_number",
                "qr_link",
                "signatory_name",
                "signatory_position",
            ],
            {
                "colors": {"primary": "#9d2235", "secondary": "#f6efe7"},
                "fonts": ["Montserrat", "PT Sans"],
                "page": "A4",
                "grid": "brand-locked",
            },
        )

        participants = [
            ("Иванова Мария Сергеевна", "maria@example.com", "Подтвержден", "Активное участие в программе", 12, "Участник"),
            ("Петров Артем Игоревич", "artem@example.com", "Подтвержден", "Лучший проект секции", 16, "Победитель"),
            ("Смирнова Елена Андреевна", "elena@example.com", "Подтвержден", "Организация волонтерской команды", 24, "Волонтер"),
        ]

        for full_name, email, status_name, achievement, hours, award_category in participants:
            participant_id = await connection.fetchval(
                """
                INSERT INTO participants (
                    event_id, full_name, email, status, achievement, hours, award_category, personal_link_token
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id
                """,
                event_id,
                full_name,
                email,
                status_name,
                achievement,
                hours,
                award_category,
                uuid4().hex,
            )

            document_number = f"TOGU-{datetime.now().year}-{participant_id:05d}"
            verification_code = uuid4().hex[:12]
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
                    $12, $13, NULL, CURRENT_TIMESTAMP, 'issued', CURRENT_TIMESTAMP
                )
                """,
                event_id,
                participant_id,
                template_id,
                document_number,
                verification_code,
                f"{FRONTEND_URL}/verify/{verification_code}",
                f"/documents/{document_number}.pdf",
                f"/documents/{document_number}.pdfa",
                f"/documents/{document_number}.png",
                "Подписан УКЭП",
                "УКЭП",
                "Дирекция форума",
                "Руководитель проекта",
            )

        await add_audit_log(
            connection,
            actor=None,
            action="seed.initialized",
            entity_type="system",
            entity_id=None,
            details={"message": "Созданы демонстрационные данные для панели управления"},
        )

from datetime import datetime
import json
from uuid import uuid4

import asyncpg

from app.core.config import FRONTEND_URL
from app.core.security import get_password_hash
from app.db import get_db_pool
from app.services.audit import add_audit_log
from app.services.document_assets import ensure_document_assets


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
        user_count = await connection.fetchval("SELECT COUNT(*) FROM users")
        if not user_count:
            demo_password_hash = get_password_hash("password123")
            demo_users = [
                ("admin@togu.example", "Системный администратор", "superadmin"),
                ("manager@togu.example", "Администратор подразделения", "division_admin"),
                ("recipient@togu.example", "Основной получатель", "recipient"),
                ("reviewer@togu.example", "Проверяющий реестра", "reviewer"),
                ("auditor@togu.example", "Аудитор системы", "auditor"),
            ]
            for idx in range(1, 16):
                demo_users.append((f"user{idx}@togu.example", f"Тестовый пользователь {idx}", "recipient"))

            for email, full_name, role in demo_users:
                await connection.execute(
                    """
                    INSERT INTO users (
                        email, full_name, hashed_password, role, brand_name, division_name, consent_to_processing
                    )
                    VALUES ($1, $2, $3, $4, 'ТОГУ', 'Цифровая кафедра', TRUE)
                    ON CONFLICT (email) DO NOTHING
                    """,
                    email,
                    full_name,
                    demo_password_hash,
                    role,
                )

        created_by = await connection.fetchval("SELECT id FROM users WHERE email = 'admin@togu.example'")
        if not created_by:
            created_by = await connection.fetchval("SELECT id FROM users ORDER BY id ASC LIMIT 1")

        event_count = await connection.fetchval("SELECT COUNT(*) FROM events")
        if not event_count:
            events = [
                ("Форум студенческих инициатив", 40, "Форум", "Управление молодежной политики"),
                ("Школа проектного управления", 32, "Практикум", "Инженерная школа"),
                ("Олимпиада по цифровым технологиям", 26, "Олимпиада", "Институт математики"),
                ("Научно-исследовательская конференция", 20, "Конференция", "Научный отдел"),
                ("Школа волонтеров ТОГУ", 15, "Школа", "Центр волонтерства"),
                ("Хакатон ИТ-решений", 8, "Хакатон", "Цифровая кафедра"),
            ]
            for title, day_shift, event_type, division in events:
                await connection.execute(
                    """
                    INSERT INTO events (
                        title, organizer, start_date, end_date, event_type, description,
                        contact_email, brand_name, division_name, created_by, status
                    )
                    VALUES ($1, 'ТОГУ', CURRENT_DATE - $2::int, CURRENT_DATE - ($2::int - 1), $3, $4, $5, 'ТОГУ', $6, $7, 'completed')
                    """,
                    title,
                    day_shift,
                    event_type,
                    f"Мероприятие «{title}» в рамках учебной и научной деятельности.",
                    "events@togu.example",
                    division,
                    created_by,
                )

        template_count = await connection.fetchval("SELECT COUNT(*) FROM templates")
        if not template_count:
            allowed_fields = json.dumps(
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
                ]
            )
            layout = json.dumps(
                {
                    "colors": {"primary": "#9d2235", "secondary": "#f6efe7"},
                    "fonts": ["Montserrat", "PT Sans"],
                    "page": "A4",
                    "grid": "brand-locked",
                }
            )
            templates = [
                ("Сертификат участника ТОГУ", "landscape", "Стандартный сертификат участника."),
                ("Диплом победителя ТОГУ", "portrait", "Официальный шаблон диплома победителя."),
                ("Благодарственное письмо ТОГУ", "landscape", "Шаблон благодарственного письма."),
                ("Сертификат волонтера ТОГУ", "portrait", "Сертификат для волонтеров мероприятий."),
                ("Сертификат спикера ТОГУ", "landscape", "Сертификат для докладчиков и спикеров."),
            ]
            for name, orientation, description in templates:
                await connection.execute(
                    """
                    INSERT INTO templates (
                        name, orientation, description, allowed_fields, brand_book_locked,
                        brand_name, created_by, layout_config
                    )
                    VALUES ($1, $2, $3, $4::jsonb, TRUE, 'ТОГУ', $5, $6::jsonb)
                    """,
                    name,
                    orientation,
                    description,
                    allowed_fields,
                    created_by,
                    layout,
                )

        document_count = await connection.fetchval("SELECT COUNT(*) FROM documents")
        if not document_count:
            events = await connection.fetch("SELECT id, title FROM events ORDER BY id ASC")
            templates = await connection.fetch("SELECT id FROM templates ORDER BY id ASC")

            participants_pool = [
                ("Иван Иванов", "ivan.ivanov@togu.example"),
                ("Мария Петрова", "maria.petrova@togu.example"),
                ("Алексей Смирнов", "alexey.smirnov@togu.example"),
                ("Елена Соколова", "elena.sokolova@togu.example"),
                ("Дмитрий Кузнецов", "dmitriy.kuznetsov@togu.example"),
                ("Ольга Васильева", "olga.vasilieva@togu.example"),
                ("Сергей Николаев", "sergey.nikolaev@togu.example"),
                ("Наталья Орлова", "natalya.orlova@togu.example"),
                ("Артем Морозов", "artem.morozov@togu.example"),
                ("Алина Федорова", "alina.fedorova@togu.example"),
                ("Виктор Громов", "viktor.gromov@togu.example"),
                ("Юлия Крылова", "yulia.krylova@togu.example"),
                ("Кирилл Лебедев", "kirill.lebedev@togu.example"),
                ("Татьяна Борисова", "tatyana.borisova@togu.example"),
                ("Павел Ефимов", "pavel.efimov@togu.example"),
                ("Анна Макарова", "anna.makarova@togu.example"),
                ("Владимир Ковалев", "vladimir.kovalev@togu.example"),
                ("Ксения Жукова", "kseniya.zhukova@togu.example"),
                ("Роман Белов", "roman.belov@togu.example"),
                ("Светлана Тихонова", "svetlana.tikhonova@togu.example"),
            ]
            categories = ["Участник", "Призер", "Победитель", "Спикер", "Волонтер"]

            if events and templates:
                for event_index, event in enumerate(events):
                    for row in range(12):
                        person = participants_pool[(event_index * 12 + row) % len(participants_pool)]
                        full_name = person[0]
                        email = person[1].replace("@", f"+e{event_index + 1}r{row + 1}@")
                        award_category = categories[(event_index + row) % len(categories)]
                        hours = 8 + (row % 10)
                        achievement = f"Активное участие в мероприятии «{event['title']}»."

                        participant_id = await connection.fetchval(
                            """
                            INSERT INTO participants (
                                event_id, full_name, email, status, achievement, hours, award_category, personal_link_token
                            )
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                            RETURNING id
                            """,
                            event["id"],
                            full_name,
                            email,
                            "Подтвержден",
                            achievement,
                            hours,
                            award_category,
                            uuid4().hex,
                        )

                        template_id = templates[(event_index + row) % len(templates)]["id"]
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
                                $12, $13, $14, CURRENT_TIMESTAMP - ($15::int || ' days')::interval, 'issued', CURRENT_TIMESTAMP
                            )
                            """,
                            event["id"],
                            participant_id,
                            template_id,
                            document_number,
                            verification_code,
                            f"{FRONTEND_URL}/verify/{verification_code}",
                            f"/documents/{document_number}.pdf",
                            f"/documents/{document_number}.pdfa",
                            f"/documents/{document_number}.png",
                            "Подписан",
                            "УКЭП",
                            "Администрация ТОГУ",
                            "Руководитель проекта",
                            created_by,
                            (event_index + row + 1),
                        )
                        ensure_document_assets(document_number)

        await add_audit_log(
            connection,
            actor=None,
            action="seed.initialized",
            entity_type="system",
            entity_id=None,
            details={"message": "Демо-данные расширены: пользователи, шаблоны, мероприятия и документы"},
        )

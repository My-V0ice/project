from typing import Any

import asyncpg

from app.domain.constants import ROLE_LABELS


def normalize_user(record: asyncpg.Record) -> dict[str, Any]:
    return {
        "id": record["id"],
        "email": record["email"],
        "full_name": record["full_name"],
        "role": record["role"],
        "role_label": ROLE_LABELS[record["role"]],
        "brand_name": record["brand_name"],
        "division_name": record["division_name"],
        "consent_to_processing": record["consent_to_processing"],
    }


def mask_name(full_name: str) -> str:
    parts = [part for part in full_name.split() if part]
    if not parts:
        return "Скрыто"
    return " ".join(f"{part[0]}." for part in parts[:-1]) + f" {parts[-1][:1]}."


def mask_email(email: str) -> str:
    local_part, _, domain = email.partition("@")
    hidden = (local_part[:2] + "***") if local_part else "***"
    return f"{hidden}@{domain}" if domain else hidden

from fastapi import APIRouter

from app.domain.constants import AWARD_CATEGORIES, ROLE_LABELS


router = APIRouter(prefix="/reference", tags=["reference"])


@router.get("/roles")
async def list_roles() -> list[dict[str, str]]:
    return [{"value": key, "label": label} for key, label in ROLE_LABELS.items()]


@router.get("/award-categories")
async def list_award_categories() -> list[str]:
    return AWARD_CATEGORIES

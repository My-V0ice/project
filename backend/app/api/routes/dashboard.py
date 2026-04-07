from typing import Any

from fastapi import APIRouter, Depends

from app.deps import get_current_user
from app.services.dashboard import build_dashboard_summary


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
async def dashboard_summary(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    return await build_dashboard_summary(current_user)

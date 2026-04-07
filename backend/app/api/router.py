from fastapi import APIRouter

from app.api.routes import audit, auth, dashboard, documents, events, reference, system


api_router = APIRouter()
api_router.include_router(system.router)
api_router.include_router(auth.router)
api_router.include_router(reference.router)
api_router.include_router(dashboard.router)
api_router.include_router(events.router)
api_router.include_router(documents.router)
api_router.include_router(audit.router)

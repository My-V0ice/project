import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import DB_CONFIG
from app.db import close_db, connect_db
from app.services.bootstrap import create_schema, seed_initial_data
from app.services.document_assets import ensure_documents_dir


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="TOGU Documents API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.mount("/documents", StaticFiles(directory=ensure_documents_dir()), name="documents")


@app.on_event("startup")
async def startup() -> None:
    logger.info("Подключение к БД %s:%s/%s", DB_CONFIG["host"], DB_CONFIG["port"], DB_CONFIG["database"])
    pool = await connect_db()
    async with pool.acquire() as connection:
        await create_schema(connection)
    await seed_initial_data()
    logger.info("База данных готова")


@app.on_event("shutdown")
async def shutdown() -> None:
    await close_db()


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": str(exc), "type": type(exc).__name__})

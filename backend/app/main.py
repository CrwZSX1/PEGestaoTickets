"""
app/main.py
Ponto de entrada da aplicação FastAPI.

Inicializa a base de dados no startup, regista as rotas e configura CORS.
Os jobs do APScheduler (IMAP poller + SLA checker) também arrancam no lifespan.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routes.auth import router as auth_router
from app.routes.categories import router as categories_router
from app.routes.reports import router as reports_router
from app.routes.tickets import router as tickets_router
from app.routes.users import router as users_router
from app.services.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ─────────────────────────────────────────────────────────────
    import app.models  # noqa: F401 — regista os modelos em Base.metadata
    init_db()
    start_scheduler()

    yield

    # ── Shutdown ────────────────────────────────────────────────────────────
    stop_scheduler()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Sistema de helpdesk com workflow, SLA e ingestão de email.",
    lifespan=lifespan,
)

# ── CORS ────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Rotas ───────────────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(categories_router)
app.include_router(tickets_router)
app.include_router(reports_router)


@app.get("/", tags=["Root"])
def root():
    return {
        "message": f"Bem-vindo ao {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs",
    }


@app.get("/health", tags=["Root"])
def health_check():
    return {"status": "online", "version": settings.app_version}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.debug)

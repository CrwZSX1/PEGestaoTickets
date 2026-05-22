"""
app/main.py
Ponto de entrada da aplicação FastAPI
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import init_db


# ── Lifespan (startup / shutdown) ──────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Executa tarefas de inicialização antes de aceitar requests
    e tarefas de encerramento quando a app termina.
    """
    # Startup — importar todos os modelos antes de create_all()
    import app.models  # noqa: F401
    init_db()

    yield  # A aplicação está a correr

    # Shutdown (adicionar limpezas aqui se necessário)


# ── Aplicação FastAPI ──────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Sistema de gestão de tickets de helpdesk",
    lifespan=lifespan,
)

# ── CORS ───────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Rotas ──────────────────────────────────────────────────────────────────
from app.routes.tickets import router as tickets_router
app.include_router(tickets_router)

# A descommentar nas próximas fases:
# from app.routes.auth import router as auth_router
# from app.routes.users import router as users_router
# from app.routes.reports import router as reports_router
# app.include_router(auth_router,    prefix="/auth",    tags=["Auth"])
# app.include_router(users_router,   prefix="/users",   tags=["Utilizadores"])
# app.include_router(reports_router, prefix="/reports", tags=["Relatórios"])


# ── Endpoints base ─────────────────────────────────────────────────────────
@app.get("/", tags=["Root"])
def root():
    """Rota raiz — confirma que a API está online."""
    return {
        "message": f"Bem-vindo ao {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health", tags=["Root"])
def health_check():
    """Health-check para monitorização e orquestração de containers."""
    return {
        "status": "online",
        "app": settings.app_name,
        "version": settings.app_version,
    }


# ── Execução direta ────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
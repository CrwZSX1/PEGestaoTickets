"""
app/database.py
Configuração do banco de dados SQLAlchemy + SQLite.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

# ── Engine ─────────────────────────────────────────────────────────────────
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    echo=settings.debug,
)

# ── Session factory ────────────────────────────────────────────────────────
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ── Base declarativa ───────────────────────────────────────────────────────
Base = declarative_base()


def init_db() -> None:
    """
    Cria todas as tabelas declaradas em Base.metadata.

    Importante: os modelos têm que ter sido importados antes desta chamada
    (caso contrário Base.metadata estará vazio). O `app.main.lifespan`
    importa `app.models` explicitamente antes de chamar esta função.
    """
    Base.metadata.create_all(bind=engine)


def get_db():
    """
    Dependência FastAPI que cria uma sessão por request.

    Uso:
        from fastapi import Depends
        from app.database import get_db

        @app.get("/")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

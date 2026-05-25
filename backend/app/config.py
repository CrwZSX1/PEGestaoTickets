"""
app/config.py
Configurações da aplicação carregadas a partir de variáveis de ambiente.

Todos os atributos estão em snake_case lowercase para coincidir com o uso
nos restantes módulos (settings.app_name, settings.secret_key, ...).
"""
import os
from dotenv import load_dotenv

load_dotenv()


def _as_bool(v: str | None, default: bool = False) -> bool:
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")


def _as_int(v: str | None, default: int) -> int:
    try:
        return int(v) if v is not None else default
    except ValueError:
        return default


class Settings:
    """Configurações gerais da aplicação."""

    # ── Aplicação ──────────────────────────────────────────────────────────
    app_name: str = "Helpdesk — Sistema de Gestão de Tickets"
    app_version: str = "1.0.0"
    debug: bool = _as_bool(os.getenv("DEBUG"), default=False)

    # ── Base de dados ──────────────────────────────────────────────────────
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./helpdesk.db")

    # ── JWT ────────────────────────────────────────────────────────────────
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-key-CHANGE-ME-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = _as_int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"), default=60 * 24
    )

    # ── SMTP (envio de email) ──────────────────────────────────────────────
    smtp_server: str = os.getenv("SMTP_SERVER", "localhost")
    smtp_port: int = _as_int(os.getenv("SMTP_PORT"), default=1025)  # Mailpit
    smtp_user: str = os.getenv("SMTP_USER", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    smtp_from: str = os.getenv("SMTP_FROM", "helpdesk@localhost")

    # ── IMAP (ingestão de email) ───────────────────────────────────────────
    imap_server: str = os.getenv("IMAP_SERVER", "localhost")
    imap_port: int = _as_int(os.getenv("IMAP_PORT"), default=1143)  # Mailpit
    imap_user: str = os.getenv("IMAP_USER", "")
    imap_password: str = os.getenv("IMAP_PASSWORD", "")
    imap_mailbox: str = os.getenv("IMAP_MAILBOX", "INBOX")
    imap_enabled: bool = _as_bool(os.getenv("IMAP_ENABLED"), default=False)

    # ── APScheduler ────────────────────────────────────────────────────────
    imap_polling_minutes: int = _as_int(os.getenv("IMAP_POLLING_MINUTES"), default=2)
    sla_check_minutes: int = _as_int(os.getenv("SLA_CHECK_MINUTES"), default=5)
    scheduler_enabled: bool = _as_bool(os.getenv("SCHEDULER_ENABLED"), default=True)

    # ── CORS / Frontend ────────────────────────────────────────────────────
    cors_origins: list[str] = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://localhost:8080,http://127.0.0.1:5500",
    ).split(",")
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:5173")

    # ── Utilizador genérico para tickets criados por email externo ────────
    email_fallback_user_email: str = os.getenv(
        "EMAIL_FALLBACK_USER_EMAIL", "external@helpdesk.local"
    )


settings = Settings()

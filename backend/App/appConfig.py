"""
backend/app/config.py
Configurações da aplicação FastAPI
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Configurações gerais da aplicação"""
    
    # Aplicação
    APP_NAME = "Helpdesk - Sistema de Gestão de Tickets"
    APP_VERSION = "1.0.0"
    DEBUG = os.getenv("DEBUG", "False") == "True"
    
    # Banco de dados
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./helpdesk.db")
    
    # JWT
    SECRET_KEY = os.getenv("SECRET_KEY", "sua-chave-secreta-mude-em-producao")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS = 24
    
    # Email (SMTP para envio)
    SMTP_SERVER = os.getenv("SMTP_SERVER", "localhost")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 1025))  # Mailpit padrão
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM = os.getenv("SMTP_FROM", "noreply@helpdesk.local")
    
    # Email (IMAP para recebimento)
    IMAP_SERVER = os.getenv("IMAP_SERVER", "localhost")
    IMAP_PORT = int(os.getenv("IMAP_PORT", 1143))  # Mailpit padrão
    IMAP_USER = os.getenv("IMAP_USER", "")
    IMAP_PASSWORD = os.getenv("IMAP_PASSWORD", "")
    IMAP_MAILBOX = os.getenv("IMAP_MAILBOX", "INBOX")
    
    # APScheduler
    IMAP_POLLING_MINUTES = 2  # Verificar emails a cada 2 minutos
    SLA_CHECK_MINUTES = 5     # Verificar SLA a cada 5 minutos
    
    # CORS
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    
    # Frontend URL
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

settings = Settings()
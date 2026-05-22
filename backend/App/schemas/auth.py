"""
app/schemas/auth.py
Schemas para autenticação e gestão de utilizadores.
"""
import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.user import UserRole

# Regex permissivo — aceita domínios .local típicos de redes internas
_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def _validate_email(v: str) -> str:
    v = v.strip().lower()
    if not _EMAIL_RE.match(v):
        raise ValueError("Formato de email inválido")
    return v


# ── User ────────────────────────────────────────────────────────────────────
class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: str
    role: UserRole
    active: bool
    created_at: datetime


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str
    password: str = Field(min_length=6, max_length=100)
    role: UserRole = UserRole.user

    @field_validator("email")
    @classmethod
    def _email_ok(cls, v: str) -> str:
        return _validate_email(v)


class UserRoleUpdate(BaseModel):
    role: UserRole


class UserActiveUpdate(BaseModel):
    active: bool


# ── Auth ────────────────────────────────────────────────────────────────────
class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
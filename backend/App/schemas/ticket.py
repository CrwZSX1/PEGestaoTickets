"""
app/schemas/ticket.py
Schemas Pydantic para validação de input/output dos endpoints de tickets
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.sla_policy import Priority
from app.models.ticket import TicketSource, TicketStatus


# ── Utilizador resumido (para embeber em respostas) ─────────────────────────
class UserSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: str


# ── Categoria resumida ───────────────────────────────────────────────────────
class CategorySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


# ── SLA status calculado on-the-fly ─────────────────────────────────────────
class SlaStatus(BaseModel):
    status: str          # "ok" | "warning" | "breached"
    deadline: Optional[datetime]
    breached: bool


# ── Comment schemas ──────────────────────────────────────────────────────────
class CommentCreate(BaseModel):
    body: str
    is_internal: bool = False


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    body: str
    is_internal: bool
    created_at: datetime
    author: UserSummary


# ── TicketHistory schemas ────────────────────────────────────────────────────
class HistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    field: str
    old_value: Optional[str]
    new_value: Optional[str]
    changed_at: datetime
    changed_by: Optional[UserSummary]


# ── Ticket CREATE ─────────────────────────────────────────────────────────────
class TicketCreate(BaseModel):
    title: str
    description: str
    priority: Priority = Priority.medium
    category_id: Optional[int] = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("O título não pode estar vazio")
        return v.strip()

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("A descrição não pode estar vazia")
        return v.strip()


# ── Ticket UPDATE (campos opcionais) ─────────────────────────────────────────
class TicketUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[Priority] = None
    category_id: Optional[int] = None


# ── Ticket STATUS transition ──────────────────────────────────────────────────
class TicketStatusUpdate(BaseModel):
    status: TicketStatus


# ── Ticket ASSIGN ─────────────────────────────────────────────────────────────
class TicketAssign(BaseModel):
    assignee_id: Optional[int] = None   # None = desatribuir


# ── Ticket OUT (resumo para listagem) ────────────────────────────────────────
class TicketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    status: TicketStatus
    priority: Priority
    source: TicketSource
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]
    sla_deadline: Optional[datetime]
    sla_breached: bool
    sla_status: Optional[str] = None  # "ok" | "warning" | "breached" — preenchido on-the-fly
    category: Optional[CategorySummary]
    creator: UserSummary
    assignee: Optional[UserSummary]


# ── Ticket DETAIL (com comentários e histórico) ───────────────────────────────
class TicketDetail(TicketOut):
    description: str
    comments: list[CommentOut] = []
    history: list[HistoryOut] = []


# ── Listagem paginada ─────────────────────────────────────────────────────────
class TicketPage(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[TicketOut]
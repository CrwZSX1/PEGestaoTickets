"""
app/models/ticket.py
Modelo central — um pedido de suporte (ticket).

Inclui o enum de estados, a fonte (web/email) e o mapa de transições
válidas usado pela API para validar mudanças de estado.
"""
import enum
from datetime import datetime

from sqlalchemy import (
    Boolean, DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.sla_policy import Priority


# ── Enums ──────────────────────────────────────────────────────────────────
class TicketStatus(str, enum.Enum):
    open            = "open"
    in_progress     = "in_progress"
    awaiting_reply  = "awaiting_reply"
    resolved        = "resolved"
    closed          = "closed"


class TicketSource(str, enum.Enum):
    web   = "web"
    email = "email"


# ── Workflow ───────────────────────────────────────────────────────────────
# Aberto → Em Curso → Aguarda Resposta → Resolvido → Fechado
# Permitimos também retroceder (resolved→in_progress, etc.) para corrigir enganos.
VALID_TRANSITIONS: dict[TicketStatus, list[TicketStatus]] = {
    TicketStatus.open: [
        TicketStatus.in_progress,
        TicketStatus.awaiting_reply,
        TicketStatus.resolved,
    ],
    TicketStatus.in_progress: [
        TicketStatus.awaiting_reply,
        TicketStatus.resolved,
        TicketStatus.open,
    ],
    TicketStatus.awaiting_reply: [
        TicketStatus.in_progress,
        TicketStatus.resolved,
        TicketStatus.open,
    ],
    TicketStatus.resolved: [
        TicketStatus.closed,
        TicketStatus.in_progress,  # reabrir
    ],
    TicketStatus.closed: [
        TicketStatus.in_progress,  # reabrir
    ],
}


# ── Modelo ─────────────────────────────────────────────────────────────────
class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[TicketStatus] = mapped_column(
        SAEnum(TicketStatus), default=TicketStatus.open, nullable=False, index=True,
    )
    priority: Mapped[Priority] = mapped_column(
        SAEnum(Priority), default=Priority.medium, nullable=False, index=True,
    )
    source: Mapped[TicketSource] = mapped_column(
        SAEnum(TicketSource), default=TicketSource.web, nullable=False,
    )

    # FKs
    category_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True,
    )
    creator_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True,
    )
    assignee_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True,
    )
    sla_policy_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("sla_policies.id", ondelete="SET NULL"), nullable=True,
    )

    # SLA
    sla_deadline: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sla_breached: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # ── Relações ────────────────────────────────────────────────────────────
    creator: Mapped["User"] = relationship(   # type: ignore[name-defined]
        "User", foreign_keys=[creator_id], back_populates="created_tickets"
    )
    assignee: Mapped["User | None"] = relationship(  # type: ignore[name-defined]
        "User", foreign_keys=[assignee_id], back_populates="assigned_tickets"
    )
    category: Mapped["Category | None"] = relationship(  # type: ignore[name-defined]
        "Category", back_populates="tickets"
    )
    sla_policy: Mapped["SlaPolicy | None"] = relationship(  # type: ignore[name-defined]
        "SlaPolicy", back_populates="tickets"
    )
    comments: Mapped[list["Comment"]] = relationship(    # type: ignore[name-defined]
        "Comment", back_populates="ticket",
        cascade="all, delete-orphan", order_by="Comment.created_at",
    )
    history: Mapped[list["TicketHistory"]] = relationship(  # type: ignore[name-defined]
        "TicketHistory", back_populates="ticket",
        cascade="all, delete-orphan", order_by="TicketHistory.changed_at",
    )

    def __repr__(self) -> str:
        return (
            f"<Ticket id={self.id} status={self.status} "
            f"priority={self.priority} title={self.title!r}>"
        )

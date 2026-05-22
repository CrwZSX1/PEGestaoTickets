"""
app/models/ticket_history.py
Registo de auditoria — cada alteração a um ticket gera uma entrada aqui
"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TicketHistory(Base):
    __tablename__ = "ticket_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticket_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Campo alterado (ex: "status", "assignee_id", "priority")
    field: Mapped[str] = mapped_column(String(100), nullable=False)
    old_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    new_value: Mapped[str | None] = mapped_column(String(255), nullable=True)

    changed_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # ── Relações ────────────────────────────────────────────────────────────
    ticket: Mapped["Ticket"] = relationship(      # type: ignore[name-defined]
        "Ticket", back_populates="history"
    )
    changed_by: Mapped["User | None"] = relationship(  # type: ignore[name-defined]
        "User", back_populates="history_entries"
    )

    def __repr__(self) -> str:
        return (
            f"<TicketHistory ticket={self.ticket_id} "
            f"field={self.field!r} {self.old_value!r} → {self.new_value!r}>"
        )

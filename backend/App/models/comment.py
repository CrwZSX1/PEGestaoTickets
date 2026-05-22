"""
app/models/comment.py
Comentários de ticket — podem ser internos (só técnicos) ou visíveis ao cliente
"""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticket_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_internal: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False,
        comment="True = nota interna (só admins/técnicos vêem)"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # ── Relações ────────────────────────────────────────────────────────────
    ticket: Mapped["Ticket"] = relationship(  # type: ignore[name-defined]
        "Ticket", back_populates="comments"
    )
    author: Mapped["User"] = relationship(    # type: ignore[name-defined]
        "User", back_populates="comments"
    )

    def __repr__(self) -> str:
        return (
            f"<Comment id={self.id} ticket_id={self.ticket_id} "
            f"internal={self.is_internal}>"
        )

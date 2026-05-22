"""
app/models/user.py
Modelo de utilizador com três perfis: admin, tech, user
"""
import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(str, enum.Enum):
    admin = "admin"
    tech  = "tech"
    user  = "user"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.user, nullable=False
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # ── Relações ────────────────────────────────────────────────────────────
    created_tickets: Mapped[list["Ticket"]] = relationship(   # type: ignore[name-defined]
        "Ticket", foreign_keys="Ticket.creator_id", back_populates="creator"
    )
    assigned_tickets: Mapped[list["Ticket"]] = relationship(  # type: ignore[name-defined]
        "Ticket", foreign_keys="Ticket.assignee_id", back_populates="assignee"
    )
    comments: Mapped[list["Comment"]] = relationship(         # type: ignore[name-defined]
        "Comment", back_populates="author"
    )
    history_entries: Mapped[list["TicketHistory"]] = relationship(  # type: ignore[name-defined]
        "TicketHistory", back_populates="changed_by"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role}>"

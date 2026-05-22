"""
app/models/category.py
Categorias de tickets (Hardware, Software, Rede, Acesso, Outro)
"""
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    default_sla_hours: Mapped[int] = mapped_column(Integer, default=24, nullable=False)

    # Técnico padrão para atribuição automática (round-robin por categoria)
    auto_assign_to_user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # ── Relações ────────────────────────────────────────────────────────────
    tickets: Mapped[list["Ticket"]] = relationship(  # type: ignore[name-defined]
        "Ticket", back_populates="category"
    )
    auto_assign_user: Mapped["User"] = relationship(  # type: ignore[name-defined]
        "User", foreign_keys=[auto_assign_to_user_id]
    )

    def __repr__(self) -> str:
        return f"<Category id={self.id} name={self.name!r}>"

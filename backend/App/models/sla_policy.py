"""
app/models/sla_policy.py
Políticas de SLA por prioridade (horas de resposta e resolução)
"""
import enum

from sqlalchemy import Enum as SAEnum, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Priority(str, enum.Enum):
    low      = "low"
    medium   = "medium"
    high     = "high"
    critical = "critical"


class SlaPolicy(Base):
    __tablename__ = "sla_policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    priority: Mapped[Priority] = mapped_column(
        SAEnum(Priority), unique=True, nullable=False
    )
    response_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    resolution_hours: Mapped[int] = mapped_column(Integer, nullable=False)

    # ── Relações ────────────────────────────────────────────────────────────
    tickets: Mapped[list["Ticket"]] = relationship(  # type: ignore[name-defined]
        "Ticket", back_populates="sla_policy"
    )

    def __repr__(self) -> str:
        return (
            f"<SlaPolicy priority={self.priority} "
            f"response={self.response_hours}h resolution={self.resolution_hours}h>"
        )

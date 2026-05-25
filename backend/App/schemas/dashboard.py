"""
app/schemas/dashboard.py
Schemas para o dashboard administrativo.
"""
from pydantic import BaseModel


class DashboardCards(BaseModel):
    open_tickets: int
    resolved_last_30d: int
    sla_breaches_last_30d: int
    avg_resolution_hours: float | None


class DailyStat(BaseModel):
    date: str          # YYYY-MM-DD
    created: int
    resolved: int


class CategoryStat(BaseModel):
    category: str
    count: int


class TechStat(BaseModel):
    user_id: int
    name: str
    resolved: int
    avg_resolution_hours: float | None
    sla_compliance_pct: float | None


class DashboardResponse(BaseModel):
    cards: DashboardCards
    daily: list[DailyStat]
    by_category: list[CategoryStat]
    top_techs: list[TechStat]

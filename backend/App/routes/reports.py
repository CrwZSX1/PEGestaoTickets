"""
app/routes/reports.py
Endpoints para o dashboard administrativo e exportação CSV.

  GET /reports/dashboard           — métricas dos últimos 30 dias
  GET /reports/monthly?month=YYYY-MM — CSV com todos os tickets do mês
"""
import csv
import io
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import case, func
from sqlalchemy.orm import Session, joinedload

from app.auth import require_admin
from app.database import get_db
from app.models.category import Category
from app.models.ticket import Ticket, TicketStatus
from app.models.user import User, UserRole
from app.schemas.dashboard import (
    CategoryStat, DailyStat, DashboardCards, DashboardResponse, TechStat,
)

router = APIRouter(prefix="/reports", tags=["Relatórios"])


def _seconds_to_hours(seconds: float | None) -> float | None:
    if seconds is None:
        return None
    return round(seconds / 3600.0, 1)


# ═══════════════════════════════════════════════════════════════════════════
# GET /reports/dashboard
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)

    # ── Cards ──────────────────────────────────────────────────────────────
    open_tickets = db.query(func.count(Ticket.id)).filter(
        Ticket.status.in_([
            TicketStatus.open, TicketStatus.in_progress, TicketStatus.awaiting_reply,
        ])
    ).scalar() or 0

    resolved_last = db.query(func.count(Ticket.id)).filter(
        Ticket.resolved_at >= since,
    ).scalar() or 0

    sla_breaches = db.query(func.count(Ticket.id)).filter(
        Ticket.sla_breached == True,
        Ticket.created_at >= since,
    ).scalar() or 0

    # Tempo médio de resolução em segundos sobre os resolvidos no período
    resolved_rows = db.query(Ticket.created_at, Ticket.resolved_at).filter(
        Ticket.resolved_at.isnot(None),
        Ticket.resolved_at >= since,
    ).all()
    if resolved_rows:
        total_sec = sum(
            (r.resolved_at - r.created_at).total_seconds() for r in resolved_rows
        )
        avg_hours = _seconds_to_hours(total_sec / len(resolved_rows))
    else:
        avg_hours = None

    cards = DashboardCards(
        open_tickets=open_tickets,
        resolved_last_30d=resolved_last,
        sla_breaches_last_30d=sla_breaches,
        avg_resolution_hours=avg_hours,
    )

    # ── Série diária criados vs resolvidos ─────────────────────────────────
    daily_map: dict[str, dict[str, int]] = {}
    for d in range(days):
        day = (now - timedelta(days=days - 1 - d)).date().isoformat()
        daily_map[day] = {"created": 0, "resolved": 0}

    created_rows = db.query(
        func.date(Ticket.created_at).label("d"),
        func.count(Ticket.id),
    ).filter(Ticket.created_at >= since).group_by("d").all()
    for d, n in created_rows:
        key = str(d)
        if key in daily_map:
            daily_map[key]["created"] = n

    resolved_day_rows = db.query(
        func.date(Ticket.resolved_at).label("d"),
        func.count(Ticket.id),
    ).filter(Ticket.resolved_at >= since).group_by("d").all()
    for d, n in resolved_day_rows:
        key = str(d)
        if key in daily_map:
            daily_map[key]["resolved"] = n

    daily = [
        DailyStat(date=day, created=v["created"], resolved=v["resolved"])
        for day, v in daily_map.items()
    ]

    # ── Distribuição por categoria ─────────────────────────────────────────
    cat_rows = (
        db.query(Category.name, func.count(Ticket.id))
        .join(Ticket, Ticket.category_id == Category.id)
        .filter(Ticket.created_at >= since)
        .group_by(Category.name)
        .all()
    )
    by_category = [CategoryStat(category=n or "—", count=c) for n, c in cat_rows]

    # ── Top técnicos ───────────────────────────────────────────────────────
    techs = db.query(User).filter(
        User.role.in_([UserRole.tech, UserRole.admin]),
        User.active == True,
    ).all()

    tech_stats: list[TechStat] = []
    for tech in techs:
        resolved_q = db.query(Ticket).filter(
            Ticket.assignee_id == tech.id,
            Ticket.resolved_at.isnot(None),
            Ticket.resolved_at >= since,
        )
        resolved_list = resolved_q.all()
        n_resolved = len(resolved_list)
        if n_resolved == 0:
            continue

        total_sec = sum(
            (t.resolved_at - t.created_at).total_seconds() for t in resolved_list
        )
        avg_h = _seconds_to_hours(total_sec / n_resolved)

        # SLA compliance: % dos resolvidos que NÃO foram breached
        n_breached = sum(1 for t in resolved_list if t.sla_breached)
        compliance = round((1 - n_breached / n_resolved) * 100, 1)

        tech_stats.append(TechStat(
            user_id=tech.id, name=tech.name,
            resolved=n_resolved,
            avg_resolution_hours=avg_h,
            sla_compliance_pct=compliance,
        ))

    tech_stats.sort(key=lambda t: t.resolved, reverse=True)

    return DashboardResponse(
        cards=cards,
        daily=daily,
        by_category=by_category,
        top_techs=tech_stats[:10],
    )


# ═══════════════════════════════════════════════════════════════════════════
# GET /reports/monthly — CSV
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/monthly")
def monthly_csv(
    month: str = Query(..., description="Formato YYYY-MM, ex: 2026-05"),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    try:
        year_s, month_s = month.split("-")
        year, mon = int(year_s), int(month_s)
        start = datetime(year, mon, 1, tzinfo=timezone.utc)
        if mon == 12:
            end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            end = datetime(year, mon + 1, 1, tzinfo=timezone.utc)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="Mês inválido. Usa o formato YYYY-MM.")

    tickets = (
        db.query(Ticket)
        .options(
            joinedload(Ticket.creator),
            joinedload(Ticket.assignee),
            joinedload(Ticket.category),
        )
        .filter(Ticket.created_at >= start, Ticket.created_at < end)
        .order_by(Ticket.created_at)
        .all()
    )

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "id", "titulo", "estado", "prioridade", "categoria",
        "tecnico", "criador", "fonte",
        "criado_em", "resolvido_em", "sla_violado",
    ])
    for t in tickets:
        writer.writerow([
            t.id,
            t.title,
            t.status.value,
            t.priority.value,
            t.category.name if t.category else "",
            t.assignee.name if t.assignee else "",
            t.creator.name if t.creator else "",
            t.source.value,
            t.created_at.isoformat(),
            t.resolved_at.isoformat() if t.resolved_at else "",
            "sim" if t.sla_breached else "não",
        ])

    buffer.seek(0)
    filename = f"helpdesk-{month}.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

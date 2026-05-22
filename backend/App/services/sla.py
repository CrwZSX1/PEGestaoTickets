"""
app/services/sla.py
Helpers para cálculo de estado de SLA em tempo real.
"""
from datetime import datetime, timezone

from app.models.ticket import Ticket, TicketStatus

# Estados em que o SLA ainda "conta"
ACTIVE_STATUSES = {
    TicketStatus.open,
    TicketStatus.in_progress,
    TicketStatus.awaiting_reply,
}


def compute_sla_status(ticket: Ticket) -> str:
    """
    Devolve uma das strings: "ok" | "warning" | "breached" | "done"

    - breached: deadline ultrapassado e ticket ainda activo
    - warning:  >= 75% do tempo de resolução já decorreu
    - ok:       dentro do prazo
    - done:     ticket resolvido/fechado (SLA já não conta)
    """
    if ticket.status in (TicketStatus.resolved, TicketStatus.closed):
        return "done"

    if ticket.sla_deadline is None:
        return "ok"

    deadline = ticket.sla_deadline
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)

    created = ticket.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)

    if now >= deadline:
        return "breached"

    total = (deadline - created).total_seconds()
    if total <= 0:
        return "ok"

    elapsed = (now - created).total_seconds()
    pct = elapsed / total

    if pct >= 0.75:
        return "warning"
    return "ok"


def enrich_ticket_with_sla(ticket: Ticket) -> Ticket:
    """Anexa o atributo computado `sla_status` ao ticket (para serialização)."""
    ticket.sla_status = compute_sla_status(ticket)  # type: ignore[attr-defined]
    return ticket


def enrich_tickets_with_sla(tickets: list[Ticket]) -> list[Ticket]:
    for t in tickets:
        enrich_ticket_with_sla(t)
    return tickets
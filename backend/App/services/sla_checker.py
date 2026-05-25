"""
app/services/sla_checker.py
Job periódico que marca tickets com SLA violado e notifica.
"""
import logging
from datetime import datetime, timezone

from app.database import SessionLocal
from app.models.ticket import Ticket, TicketStatus
from app.services.email import notify_sla_breached

logger = logging.getLogger(__name__)


def check_sla_once() -> int:
    """
    Marca como `sla_breached=True` todos os tickets cuja `sla_deadline`
    está no passado e que ainda estão activos. Envia notificação por email.
    Devolve o nº de tickets marcados nesta execução.
    """
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)

        tickets = db.query(Ticket).filter(
            Ticket.sla_deadline.isnot(None),
            Ticket.sla_deadline < now,
            Ticket.sla_breached == False,
            Ticket.status.in_([
                TicketStatus.open,
                TicketStatus.in_progress,
                TicketStatus.awaiting_reply,
            ]),
        ).all()

        for t in tickets:
            t.sla_breached = True
            db.flush()
            try:
                notify_sla_breached(t, db)
            except Exception as e:
                logger.error("Falha ao notificar SLA breach do ticket %s: %s", t.id, e)

        if tickets:
            db.commit()
            logger.info("SLA checker: %d tickets marcados como breached", len(tickets))
        return len(tickets)
    except Exception:
        db.rollback()
        logger.exception("SLA checker: erro inesperado")
        return 0
    finally:
        db.close()

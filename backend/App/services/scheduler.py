"""
app/services/scheduler.py
Configuração do APScheduler com dois jobs:
  - IMAP polling (criar tickets de emails recebidos)
  - SLA checker  (marcar tickets em atraso e notificar)
"""
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.config import settings
from app.services.imap_poller import poll_inbox_once
from app.services.sla_checker import check_sla_once

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def start_scheduler() -> BackgroundScheduler | None:
    """Inicia o scheduler com os dois jobs principais."""
    global _scheduler
    if not settings.scheduler_enabled:
        logger.info("Scheduler desactivado por configuração.")
        return None

    if _scheduler is not None:
        return _scheduler

    sched = BackgroundScheduler(timezone="UTC")

    if settings.imap_enabled:
        sched.add_job(
            poll_inbox_once,
            "interval",
            minutes=settings.imap_polling_minutes,
            id="imap_poller",
            next_run_time=None,  # corre só após o primeiro intervalo
        )
        logger.info("Scheduler: IMAP polling activo (a cada %s min)",
                    settings.imap_polling_minutes)

    sched.add_job(
        check_sla_once,
        "interval",
        minutes=settings.sla_check_minutes,
        id="sla_checker",
    )
    logger.info("Scheduler: SLA checker activo (a cada %s min)",
                settings.sla_check_minutes)

    sched.start()
    _scheduler = sched
    return sched


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None

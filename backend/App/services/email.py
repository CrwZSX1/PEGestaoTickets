"""
app/services/email.py
Envio de email via SMTP (stdlib smtplib).

Em desenvolvimento aponta para Mailpit (localhost:1025).
Os templates são ficheiros .html em /backend/email_templates com
placeholders no estilo `{key}` substituídos por str.format().
"""
import logging
import smtplib
from email.message import EmailMessage
from pathlib import Path
from typing import Iterable

from app.config import settings

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent.parent.parent / "email_templates"


def _load_template(name: str) -> str:
    """Carrega o template <name>.html e devolve o seu conteúdo."""
    path = TEMPLATES_DIR / f"{name}.html"
    if not path.exists():
        logger.warning("Template de email não encontrado: %s", path)
        return "<html><body>{subject}<br/><br/>{body}</body></html>"
    return path.read_text(encoding="utf-8")


def render(template_name: str, **context) -> str:
    """Renderiza um template HTML substituindo placeholders."""
    tpl = _load_template(template_name)
    # str.format escapa chavetas duplas; mantemos compatibilidade simples
    try:
        return tpl.format(**context)
    except KeyError as e:
        logger.warning("Placeholder em falta no template %s: %s", template_name, e)
        return tpl


def send_email(
    to: str | Iterable[str],
    subject: str,
    html_body: str,
) -> bool:
    """
    Envia um email HTML via SMTP configurado. Devolve True em sucesso, False em falha.

    Não levanta excepção — o objectivo é nunca quebrar um endpoint por
    causa de uma falha no servidor de email.
    """
    recipients = [to] if isinstance(to, str) else list(to)
    if not recipients:
        return False

    msg = EmailMessage()
    msg["From"] = settings.smtp_from
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.set_content("Este email contém conteúdo HTML. Por favor usa um cliente compatível.")
    msg.add_alternative(html_body, subtype="html")

    try:
        with smtplib.SMTP(settings.smtp_server, settings.smtp_port, timeout=10) as s:
            if settings.smtp_user:
                s.starttls()
                s.login(settings.smtp_user, settings.smtp_password)
            s.send_message(msg)
        logger.info("Email enviado: to=%s subject=%r", recipients, subject)
        return True
    except Exception as e:
        logger.error("Falha ao enviar email para %s: %s", recipients, e)
        return False


# ── Notificações de alto nível ─────────────────────────────────────────────
def notify_ticket_created(ticket, db) -> None:
    if not ticket.assignee:
        return
    html = render(
        "ticket_assigned",
        ticket_id=ticket.id,
        title=ticket.title,
        description=ticket.description[:300],
        priority=ticket.priority.value,
        frontend_url=settings.frontend_url,
    )
    send_email(ticket.assignee.email, f"[#{ticket.id}] Novo ticket atribuído: {ticket.title}", html)


def notify_ticket_assigned(ticket, db) -> None:
    if not ticket.assignee:
        return
    html = render(
        "ticket_assigned",
        ticket_id=ticket.id,
        title=ticket.title,
        description=ticket.description[:300],
        priority=ticket.priority.value,
        frontend_url=settings.frontend_url,
    )
    send_email(ticket.assignee.email, f"[#{ticket.id}] Ticket atribuído: {ticket.title}", html)


def notify_external_comment(ticket, comment, db) -> None:
    if comment.is_internal:
        return
    if not ticket.creator:
        return
    # Evita auto-notificação se o autor for o próprio criador
    if comment.user_id == ticket.creator_id:
        return
    html = render(
        "ticket_comment",
        ticket_id=ticket.id,
        title=ticket.title,
        author=comment.author.name if comment.author else "Equipa",
        body=comment.body,
        frontend_url=settings.frontend_url,
    )
    send_email(ticket.creator.email, f"[#{ticket.id}] Nova resposta: {ticket.title}", html)


def notify_ticket_resolved(ticket, db) -> None:
    if not ticket.creator:
        return
    html = render(
        "ticket_resolved",
        ticket_id=ticket.id,
        title=ticket.title,
        frontend_url=settings.frontend_url,
    )
    send_email(ticket.creator.email, f"[#{ticket.id}] Ticket resolvido: {ticket.title}", html)


def notify_sla_breached(ticket, db) -> None:
    """Envia email ao técnico atribuído (se houver) e a todos os admins."""
    from app.models.user import User, UserRole

    recipients: list[str] = []
    if ticket.assignee:
        recipients.append(ticket.assignee.email)

    admins = db.query(User).filter(User.role == UserRole.admin, User.active == True).all()
    recipients.extend([a.email for a in admins])

    if not recipients:
        return

    html = render(
        "sla_breached",
        ticket_id=ticket.id,
        title=ticket.title,
        priority=ticket.priority.value,
        deadline=ticket.sla_deadline.isoformat() if ticket.sla_deadline else "—",
        frontend_url=settings.frontend_url,
    )
    send_email(set(recipients), f"[#{ticket.id}] ⚠️ SLA violado: {ticket.title}", html)
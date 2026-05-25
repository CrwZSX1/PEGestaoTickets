"""
app/services/imap_poller.py
Polling de uma caixa IMAP para criar tickets automaticamente.

Estratégia:
  - Liga ao servidor IMAP (Mailpit em dev)
  - Busca emails UNSEEN na inbox
  - Para cada um: parse de subject/body/from, cria ticket, marca como lido
  - Não levanta excepções para não quebrar o scheduler
"""
import email
import imaplib
import logging
from datetime import datetime, timedelta, timezone
from email.header import decode_header
from email.message import Message

from app.config import settings
from app.database import SessionLocal
from app.models.sla_policy import Priority, SlaPolicy
from app.models.ticket import Ticket, TicketSource, TicketStatus
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)


def _decode_header(value: str | None) -> str:
    if not value:
        return ""
    parts = decode_header(value)
    out = []
    for raw, enc in parts:
        if isinstance(raw, bytes):
            out.append(raw.decode(enc or "utf-8", errors="replace"))
        else:
            out.append(raw)
    return "".join(out).strip()


def _extract_body(msg: Message) -> str:
    """Devolve a parte text/plain do email, ou um fallback do text/html."""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = str(part.get("Content-Disposition", ""))
            if ctype == "text/plain" and "attachment" not in disp:
                try:
                    return part.get_payload(decode=True).decode(
                        part.get_content_charset() or "utf-8", errors="replace"
                    ).strip()
                except Exception:
                    continue
        # fallback: text/html convertido cruamente
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                try:
                    html = part.get_payload(decode=True).decode(
                        part.get_content_charset() or "utf-8", errors="replace"
                    )
                    return _strip_html(html)
                except Exception:
                    continue
        return ""
    else:
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                return payload.decode(msg.get_content_charset() or "utf-8", errors="replace").strip()
        except Exception:
            pass
        return ""


def _strip_html(html: str) -> str:
    """Remoção naïve de tags HTML — suficiente para emails de suporte."""
    import re
    text = re.sub(r"<\s*br\s*/?>", "\n", html, flags=re.I)
    text = re.sub(r"</p\s*>", "\n\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _resolve_creator(db, from_email: str) -> User:
    """
    Identifica o criador do ticket a partir do remetente:
    - Se o email corresponde a um utilizador → usar esse
    - Senão usar o utilizador genérico configurado
    - Como último recurso, qualquer admin
    """
    if from_email:
        user = db.query(User).filter(User.email == from_email).first()
        if user:
            return user

    fallback = db.query(User).filter(
        User.email == settings.email_fallback_user_email
    ).first()
    if fallback:
        return fallback

    return db.query(User).filter(User.role == UserRole.admin).first()


def _set_sla(ticket: Ticket, db) -> None:
    policy = db.query(SlaPolicy).filter(SlaPolicy.priority == ticket.priority).first()
    if policy:
        ticket.sla_policy_id = policy.id
        ticket.sla_deadline = datetime.now(timezone.utc) + timedelta(
            hours=policy.resolution_hours
        )


# ═══════════════════════════════════════════════════════════════════════════
# Função principal — chamada pelo scheduler
# ═══════════════════════════════════════════════════════════════════════════

def poll_inbox_once() -> int:
    """
    Executa um ciclo de polling. Devolve o nº de tickets criados.
    Nunca levanta excepção — qualquer erro é apenas registado.
    """
    if not settings.imap_enabled:
        return 0

    created = 0
    db = SessionLocal()
    try:
        try:
            imap = imaplib.IMAP4(settings.imap_server, settings.imap_port)
        except Exception as e:
            logger.error("IMAP: falha ao ligar a %s:%s — %s",
                         settings.imap_server, settings.imap_port, e)
            return 0

        try:
            if settings.imap_user:
                imap.login(settings.imap_user, settings.imap_password)
            imap.select(settings.imap_mailbox)

            typ, data = imap.search(None, "UNSEEN")
            if typ != "OK":
                logger.warning("IMAP: search devolveu %s", typ)
                return 0

            for num in data[0].split():
                typ, msg_data = imap.fetch(num, "(RFC822)")
                if typ != "OK" or not msg_data or not msg_data[0]:
                    continue
                raw = msg_data[0][1]
                if not isinstance(raw, (bytes, bytearray)):
                    continue
                msg = email.message_from_bytes(raw)

                subject = _decode_header(msg.get("Subject")) or "(sem assunto)"
                from_addr = email.utils.parseaddr(msg.get("From", ""))[1].lower()
                body_text = _extract_body(msg) or "(corpo vazio)"

                creator = _resolve_creator(db, from_addr)
                if not creator:
                    logger.warning("IMAP: sem creator possível, ignorando email %r", subject)
                    imap.store(num, "+FLAGS", "\\Seen")
                    continue

                ticket = Ticket(
                    title=subject[:255],
                    description=body_text[:5000],
                    status=TicketStatus.open,
                    priority=Priority.medium,
                    source=TicketSource.email,
                    creator_id=creator.id,
                )
                _set_sla(ticket, db)
                db.add(ticket)
                db.commit()
                created += 1
                logger.info("IMAP: ticket criado #%s a partir de email de %s", ticket.id, from_addr)

                # Marca o email como lido (Mailpit não suporta MOVE)
                imap.store(num, "+FLAGS", "\\Seen")

        finally:
            try:
                imap.logout()
            except Exception:
                pass
    except Exception as e:
        logger.exception("IMAP: erro inesperado durante polling: %s", e)
    finally:
        db.close()

    return created

"""
app/routes/tickets.py
Endpoints de tickets: CRUD, transições de estado, atribuição e comentários

Endpoints:
  GET    /tickets                     — listar (filtros + paginação)
  POST   /tickets                     — criar ticket (web)
  GET    /tickets/{id}                — detalhe com comentários e histórico
  PUT    /tickets/{id}                — editar título/descrição/prioridade/categoria
  PUT    /tickets/{id}/status         — transição de estado (validada)
  PUT    /tickets/{id}/assign         — atribuir/desatribuir técnico
  POST   /tickets/{id}/comments       — adicionar comentário
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.auth import get_current_user, require_admin, require_admin_tech
from app.database import get_db
from app.models.sla_policy import Priority, SlaPolicy
from app.models.ticket import VALID_TRANSITIONS, Ticket, TicketSource, TicketStatus
from app.models.comment import Comment
from app.models.ticket_history import TicketHistory
from app.models.user import User, UserRole
from app.schemas.ticket import (
    CommentCreate, CommentOut,
    TicketAssign, TicketCreate, TicketDetail, TicketOut,
    TicketPage, TicketStatusUpdate, TicketUpdate,
)

router = APIRouter(prefix="/tickets", tags=["Tickets"])


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _record_history(
    db: Session,
    ticket_id: int,
    user_id: int,
    field: str,
    old_value,
    new_value,
) -> None:
    """Regista uma entrada no histórico de alterações do ticket."""
    if str(old_value) == str(new_value):
        return
    db.add(TicketHistory(
        ticket_id=ticket_id,
        user_id=user_id,
        field=field,
        old_value=str(old_value) if old_value is not None else None,
        new_value=str(new_value) if new_value is not None else None,
    ))


def _set_sla_deadline(ticket: Ticket, db: Session) -> None:
    """Calcula e define o prazo de SLA com base na prioridade do ticket."""
    policy = db.query(SlaPolicy).filter(
        SlaPolicy.priority == ticket.priority
    ).first()
    if policy:
        ticket.sla_policy_id = policy.id
        ticket.sla_deadline = datetime.now(timezone.utc) + timedelta(
            hours=policy.resolution_hours
        )


def _can_see_internal(user: User) -> bool:
    return user.role in (UserRole.admin, UserRole.tech)


def _filter_comments(comments: list, user: User) -> list:
    """Remove comentários internos para utilizadores normais."""
    if _can_see_internal(user):
        return comments
    return [c for c in comments if not c.is_internal]


def _get_ticket_or_404(ticket_id: int, db: Session) -> Ticket:
    ticket = (
        db.query(Ticket)
        .options(
            joinedload(Ticket.creator),
            joinedload(Ticket.assignee),
            joinedload(Ticket.category),
            joinedload(Ticket.sla_policy),
            joinedload(Ticket.comments).joinedload(Comment.author),
            joinedload(Ticket.history).joinedload(TicketHistory.changed_by),
        )
        .filter(Ticket.id == ticket_id)
        .first()
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket não encontrado")
    return ticket


def _check_ticket_access(ticket: Ticket, user: User) -> None:
    """
    Regras de acesso:
    - Admin: vê tudo
    - Tech: vê todos os tickets
    - User: só vê os seus próprios tickets
    """
    if user.role == UserRole.user and ticket.creator_id != user.id:
        raise HTTPException(status_code=403, detail="Sem acesso a este ticket")


# ═══════════════════════════════════════════════════════════════════════════════
# GET /tickets — Listagem com filtros e paginação
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("", response_model=TicketPage)
def list_tickets(
    # Filtros
    status_filter: Optional[TicketStatus] = Query(None, alias="status"),
    priority: Optional[Priority] = Query(None),
    category_id: Optional[int] = Query(None),
    assignee_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None, description="Pesquisa em título e descrição"),
    # Paginação
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    # Auth
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Ticket).options(
        joinedload(Ticket.creator),
        joinedload(Ticket.assignee),
        joinedload(Ticket.category),
    )

    # Utilizadores normais só vêem os seus tickets
    if current_user.role == UserRole.user:
        q = q.filter(Ticket.creator_id == current_user.id)

    # Aplicar filtros
    if status_filter:
        q = q.filter(Ticket.status == status_filter)
    if priority:
        q = q.filter(Ticket.priority == priority)
    if category_id:
        q = q.filter(Ticket.category_id == category_id)
    if assignee_id:
        q = q.filter(Ticket.assignee_id == assignee_id)
    if search:
        term = f"%{search}%"
        q = q.filter(
            Ticket.title.ilike(term) | Ticket.description.ilike(term)
        )

    total = q.count()
    items = (
        q.order_by(Ticket.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return TicketPage(total=total, page=page, page_size=page_size, items=items)


# ═══════════════════════════════════════════════════════════════════════════════
# POST /tickets — Criar ticket (web)
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
def create_ticket(
    body: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = Ticket(
        title=body.title,
        description=body.description,
        priority=body.priority,
        category_id=body.category_id,
        source=TicketSource.web,
        creator_id=current_user.id,
        status=TicketStatus.open,
    )

    # Definir prazo de SLA
    _set_sla_deadline(ticket, db)

    # Atribuição automática por categoria
    if body.category_id:
        from app.models.category import Category
        cat = db.query(Category).filter(Category.id == body.category_id).first()
        if cat and cat.auto_assign_to_user_id:
            ticket.assignee_id = cat.auto_assign_to_user_id

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    # Recarregar com relações
    return _get_ticket_or_404(ticket.id, db)


# ═══════════════════════════════════════════════════════════════════════════════
# GET /tickets/{id} — Detalhe com comentários e histórico
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/{ticket_id}", response_model=TicketDetail)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = _get_ticket_or_404(ticket_id, db)
    _check_ticket_access(ticket, current_user)

    # Filtrar comentários internos para utilizadores normais
    ticket.comments = _filter_comments(ticket.comments, current_user)
    return ticket


# ═══════════════════════════════════════════════════════════════════════════════
# PUT /tickets/{id} — Editar campos básicos
# ═══════════════════════════════════════════════════════════════════════════════

@router.put("/{ticket_id}", response_model=TicketOut)
def update_ticket(
    ticket_id: int,
    body: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = _get_ticket_or_404(ticket_id, db)
    _check_ticket_access(ticket, current_user)

    # Utilizadores só editam os seus próprios tickets em aberto
    if current_user.role == UserRole.user and ticket.status != TicketStatus.open:
        raise HTTPException(
            status_code=403,
            detail="Só é possível editar tickets em estado 'Aberto'",
        )

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        old = getattr(ticket, field)
        setattr(ticket, field, value)
        _record_history(db, ticket.id, current_user.id, field, old, value)

    # Recalcular SLA se prioridade mudou
    if "priority" in update_data:
        _set_sla_deadline(ticket, db)

    db.commit()
    return _get_ticket_or_404(ticket_id, db)


# ═══════════════════════════════════════════════════════════════════════════════
# PUT /tickets/{id}/status — Transição de estado (validada)
# ═══════════════════════════════════════════════════════════════════════════════

@router.put("/{ticket_id}/status", response_model=TicketOut)
def update_ticket_status(
    ticket_id: int,
    body: TicketStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_tech),
):
    ticket = _get_ticket_or_404(ticket_id, db)

    if body.status == ticket.status:
        raise HTTPException(status_code=400, detail="O ticket já está nesse estado")

    allowed = VALID_TRANSITIONS.get(ticket.status, [])
    if body.status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Transição inválida: {ticket.status} → {body.status}. "
                f"Transições permitidas: {[s.value for s in allowed]}"
            ),
        )

    old_status = ticket.status
    ticket.status = body.status

    # Marcar data de resolução
    if body.status == TicketStatus.resolved:
        ticket.resolved_at = datetime.now(timezone.utc)
    elif body.status == TicketStatus.open:
        ticket.resolved_at = None

    _record_history(db, ticket.id, current_user.id, "status", old_status, body.status)
    db.commit()
    return _get_ticket_or_404(ticket_id, db)


# ═══════════════════════════════════════════════════════════════════════════════
# PUT /tickets/{id}/assign — Atribuir/desatribuir técnico
# ═══════════════════════════════════════════════════════════════════════════════

@router.put("/{ticket_id}/assign", response_model=TicketOut)
def assign_ticket(
    ticket_id: int,
    body: TicketAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_tech),
):
    ticket = _get_ticket_or_404(ticket_id, db)

    # Validar que o assignee existe e é tech/admin
    if body.assignee_id is not None:
        assignee = db.query(User).filter(
            User.id == body.assignee_id,
            User.active == True,
        ).first()
        if not assignee:
            raise HTTPException(status_code=404, detail="Utilizador não encontrado")
        if assignee.role == UserRole.user:
            raise HTTPException(
                status_code=400,
                detail="Só é possível atribuir tickets a técnicos ou admins",
            )

    old_assignee = ticket.assignee_id
    ticket.assignee_id = body.assignee_id

    _record_history(db, ticket.id, current_user.id, "assignee_id", old_assignee, body.assignee_id)
    db.commit()
    return _get_ticket_or_404(ticket_id, db)


# ═══════════════════════════════════════════════════════════════════════════════
# POST /tickets/{id}/comments — Adicionar comentário
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/{ticket_id}/comments",
    response_model=CommentOut,
    status_code=status.HTTP_201_CREATED,
)
def add_comment(
    ticket_id: int,
    body: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = _get_ticket_or_404(ticket_id, db)
    _check_ticket_access(ticket, current_user)

    # Utilizadores não podem criar notas internas
    if body.is_internal and current_user.role == UserRole.user:
        raise HTTPException(
            status_code=403,
            detail="Utilizadores não podem criar comentários internos",
        )

    # Não comentar em tickets fechados (excepto admins)
    if ticket.status == TicketStatus.closed and current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=400,
            detail="Não é possível comentar num ticket fechado",
        )

    comment = Comment(
        ticket_id=ticket_id,
        user_id=current_user.id,
        body=body.body,
        is_internal=body.is_internal,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    # Carregar relação author
    db.refresh(comment)
    comment.author  # trigger lazy load
    return comment
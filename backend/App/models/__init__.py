"""
app/models/__init__.py
Importa todos os modelos para que sejam registados em Base.metadata.

A importação deste módulo é o passo prévio obrigatório a init_db().
"""
from .user import User, UserRole                           # noqa: F401
from .category import Category                             # noqa: F401
from .sla_policy import SlaPolicy, Priority                # noqa: F401
from .ticket import Ticket, TicketStatus, TicketSource, VALID_TRANSITIONS  # noqa: F401
from .comment import Comment                               # noqa: F401
from .ticket_history import TicketHistory                  # noqa: F401

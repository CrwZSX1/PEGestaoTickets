"""
app/models/__init__.py
Importa todos os modelos para que sejam registados no Base.metadata.
Basta importar este módulo antes de chamar init_db().
"""
from .user import User          # noqa: F401
from .category import Category  # noqa: F401
from .sla_policy import SlaPolicy  # noqa: F401
from .ticket import Ticket      # noqa: F401
from .comment import Comment    # noqa: F401
from .ticket_history import TicketHistory  # noqa: F401

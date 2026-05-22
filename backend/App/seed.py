"""
app/seed.py
Popula a base de dados com dados de exemplo.

Uso:
    python -m app.seed          # apenas se a BD estiver vazia
    python -m app.seed --reset  # apaga TODOS os dados antes
"""
import sys
from datetime import datetime, timedelta, timezone

from app.auth import hash_password
from app.database import SessionLocal, engine, init_db
from app.models import (  # noqa: F401 — regista todos os modelos
    Category, Comment, SlaPolicy, Ticket, TicketHistory, User,
)
from app.models.sla_policy import Priority
from app.models.ticket import TicketSource, TicketStatus
from app.models.user import UserRole


def seed(reset: bool = False) -> None:
    init_db()
    db = SessionLocal()

    try:
        if reset:
            print("⚠️  Reset: a apagar todos os dados...")
            # Apagar respeitando FKs
            db.query(TicketHistory).delete()
            db.query(Comment).delete()
            db.query(Ticket).delete()
            db.query(Category).delete()
            db.query(SlaPolicy).delete()
            db.query(User).delete()
            db.commit()

        if db.query(User).count() > 0:
            print("ℹ️  Base de dados já contém dados. Use --reset para limpar primeiro.")
            return

        now = datetime.now(timezone.utc)

        # ── 1. Utilizadores (emails únicos!) ────────────────────────────────
        admin = User(
            name="Admin Sistema",
            email="admin@helpdesk.local",
            hashed_password=hash_password("admin123"),
            role=UserRole.admin,
        )
        tech1 = User(
            name="Técnico Eliúde",
            email="tech.eliude@helpdesk.local",
            hashed_password=hash_password("tech123"),
            role=UserRole.tech,
        )
        tech2 = User(
            name="Técnico Davi",
            email="tech.davi@helpdesk.local",
            hashed_password=hash_password("tech123"),
            role=UserRole.tech,
        )
        user1 = User(
            name="Utilizador Eliúde",
            email="user.eliude@helpdesk.local",
            hashed_password=hash_password("user123"),
            role=UserRole.user,
        )
        user2 = User(
            name="Utilizador Davi",
            email="user.davi@helpdesk.local",
            hashed_password=hash_password("user123"),
            role=UserRole.user,
        )
        external = User(
            name="Utilizador Externo (email)",
            email="external@helpdesk.local",
            hashed_password=hash_password("external123"),
            role=UserRole.user,
        )
        db.add_all([admin, tech1, tech2, user1, user2, external])
        db.flush()

        # ── 2. Políticas de SLA ─────────────────────────────────────────────
        sla_low      = SlaPolicy(priority=Priority.low,      response_hours=48, resolution_hours=120)
        sla_medium   = SlaPolicy(priority=Priority.medium,   response_hours=24, resolution_hours=72)
        sla_high     = SlaPolicy(priority=Priority.high,     response_hours=8,  resolution_hours=24)
        sla_critical = SlaPolicy(priority=Priority.critical, response_hours=2,  resolution_hours=8)
        db.add_all([sla_low, sla_medium, sla_high, sla_critical])
        db.flush()

        # ── 3. Categorias ───────────────────────────────────────────────────
        cat_hw     = Category(name="Hardware", default_sla_hours=24, auto_assign_to_user_id=tech1.id)
        cat_sw     = Category(name="Software", default_sla_hours=24, auto_assign_to_user_id=tech2.id)
        cat_net    = Category(name="Rede",     default_sla_hours=8,  auto_assign_to_user_id=tech1.id)
        cat_access = Category(name="Acesso",   default_sla_hours=4,  auto_assign_to_user_id=tech2.id)
        cat_other  = Category(name="Outro",    default_sla_hours=48)
        db.add_all([cat_hw, cat_sw, cat_net, cat_access, cat_other])
        db.flush()

        # ── 4. Tickets de exemplo ───────────────────────────────────────────
        tickets_data = [
            dict(title="Ecrã não liga",
                 description="O monitor do posto 3 não liga desde esta manhã.",
                 status=TicketStatus.open, priority=Priority.high,
                 source=TicketSource.web, category_id=cat_hw.id,
                 creator_id=user1.id, assignee_id=tech1.id,
                 sla_policy_id=sla_high.id, sla_deadline=now + timedelta(hours=24)),

            dict(title="Excel não abre ficheiros .xlsx",
                 description="Ao abrir qualquer ficheiro Excel aparece erro de compatibilidade.",
                 status=TicketStatus.in_progress, priority=Priority.medium,
                 source=TicketSource.web, category_id=cat_sw.id,
                 creator_id=user1.id, assignee_id=tech2.id,
                 sla_policy_id=sla_medium.id, sla_deadline=now + timedelta(hours=72)),

            dict(title="VPN não conecta fora do escritório",
                 description="Desde a atualização do Windows, a VPN falha com erro 800.",
                 status=TicketStatus.awaiting_reply, priority=Priority.high,
                 source=TicketSource.email, category_id=cat_net.id,
                 creator_id=user2.id, assignee_id=tech1.id,
                 sla_policy_id=sla_high.id,
                 sla_deadline=now - timedelta(hours=2),
                 sla_breached=True),

            dict(title="Pedido de acesso ao sistema contabilidade",
                 description="Novo colaborador precisa de acesso ao ERP.",
                 status=TicketStatus.open, priority=Priority.low,
                 source=TicketSource.web, category_id=cat_access.id,
                 creator_id=user2.id, assignee_id=None,
                 sla_policy_id=sla_low.id, sla_deadline=now + timedelta(hours=120)),

            dict(title="Impressora do piso 2 offline",
                 description="A impressora HP LaserJet aparece offline na rede.",
                 status=TicketStatus.resolved, priority=Priority.medium,
                 source=TicketSource.web, category_id=cat_hw.id,
                 creator_id=user1.id, assignee_id=tech1.id,
                 sla_policy_id=sla_medium.id,
                 sla_deadline=now + timedelta(hours=48),
                 resolved_at=now - timedelta(hours=5)),

            dict(title="Portal de clientes em baixo",
                 description="Cliente enviou email a dizer que o portal de clientes está em baixo.",
                 status=TicketStatus.in_progress, priority=Priority.critical,
                 source=TicketSource.email, category_id=cat_net.id,
                 creator_id=external.id, assignee_id=tech2.id,
                 sla_policy_id=sla_critical.id, sla_deadline=now + timedelta(hours=8)),

            dict(title="Instalação de software de design",
                 description="Necessito do Adobe Illustrator instalado no meu posto.",
                 status=TicketStatus.closed, priority=Priority.low,
                 source=TicketSource.web, category_id=cat_sw.id,
                 creator_id=user2.id, assignee_id=tech2.id,
                 sla_policy_id=sla_low.id,
                 sla_deadline=now - timedelta(hours=50),
                 resolved_at=now - timedelta(hours=60)),

            dict(title="Password esquecida — sistema RH",
                 description="Não consigo fazer login no sistema de RH após férias.",
                 status=TicketStatus.open, priority=Priority.medium,
                 source=TicketSource.web, category_id=cat_access.id,
                 creator_id=user1.id, assignee_id=None,
                 sla_policy_id=sla_medium.id, sla_deadline=now + timedelta(hours=72)),

            dict(title="Teclado com teclas coladas",
                 description="O teclado do posto 7 tem várias teclas que não funcionam.",
                 status=TicketStatus.open, priority=Priority.low,
                 source=TicketSource.web, category_id=cat_hw.id,
                 creator_id=user2.id, assignee_id=None,
                 sla_policy_id=sla_low.id, sla_deadline=now + timedelta(hours=120)),

            dict(title="Dúvida sobre política BYOD",
                 description="Onde posso consultar as políticas de uso de dispositivos pessoais?",
                 status=TicketStatus.resolved, priority=Priority.low,
                 source=TicketSource.email, category_id=cat_other.id,
                 creator_id=user1.id, assignee_id=admin.id,
                 sla_policy_id=sla_low.id,
                 sla_deadline=now + timedelta(hours=100),
                 resolved_at=now - timedelta(hours=10)),
        ]

        tickets = []
        for data in tickets_data:
            t = Ticket(**data)
            # Se o ticket tem resolved_at no passado, recuamos o created_at para
            # garantir created_at < resolved_at (caso contrário as métricas dão valores negativos)
            if data.get("resolved_at") is not None:
                t.created_at = data["resolved_at"] - timedelta(hours=20)
            db.add(t)
            tickets.append(t)
        db.flush()

        # ── 5. Comentários de exemplo ───────────────────────────────────────
        comments = [
            Comment(ticket_id=tickets[0].id, user_id=tech1.id,
                    body="Vou verificar o cabo de alimentação e o monitor.", is_internal=False),
            Comment(ticket_id=tickets[0].id, user_id=tech1.id,
                    body="Nota interna: possível falha no PSU. Verificar stock.", is_internal=True),
            Comment(ticket_id=tickets[1].id, user_id=tech2.id,
                    body="Problema identificado: versão do Office desatualizada. A atualizar.",
                    is_internal=False),
            Comment(ticket_id=tickets[2].id, user_id=user2.id,
                    body="Continua a falhar mesmo após reiniciar. Log de erro em anexo.",
                    is_internal=False),
            Comment(ticket_id=tickets[5].id, user_id=tech2.id,
                    body="A investigar — servidor de aplicação responde mas BD em timeout.",
                    is_internal=True),
        ]
        db.add_all(comments)

        # ── 6. Histórico ────────────────────────────────────────────────────
        histories = [
            TicketHistory(ticket_id=tickets[1].id, user_id=tech2.id,
                          field="status", old_value="open", new_value="in_progress"),
            TicketHistory(ticket_id=tickets[2].id, user_id=tech1.id,
                          field="status", old_value="in_progress", new_value="awaiting_reply"),
            TicketHistory(ticket_id=tickets[4].id, user_id=tech1.id,
                          field="status", old_value="in_progress", new_value="resolved"),
            TicketHistory(ticket_id=tickets[6].id, user_id=tech2.id,
                          field="status", old_value="resolved", new_value="closed"),
        ]
        db.add_all(histories)

        db.commit()
        print("✅ Seed concluído com sucesso!")
        print(f"   • {db.query(User).count()} utilizadores")
        print(f"   • {db.query(Category).count()} categorias")
        print(f"   • {db.query(SlaPolicy).count()} políticas de SLA")
        print(f"   • {db.query(Ticket).count()} tickets")
        print(f"   • {db.query(Comment).count()} comentários")
        print(f"   • {db.query(TicketHistory).count()} entradas de histórico")
        print()
        print("🔑 Credenciais:")
        print("   admin@helpdesk.local       / admin123")
        print("   tech.eliude@helpdesk.local / tech123")
        print("   user.eliude@helpdesk.local / user123")

    except Exception as e:
        db.rollback()
        print(f"❌ Erro durante o seed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    reset = "--reset" in sys.argv
    seed(reset=reset)
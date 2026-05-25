# 🎫 Helpdesk — Sistema de Gestão de Tickets

Um **sistema web full-stack** para gestão de pedidos de suporte (helpdesk) com autenticação, workflow de estados, SLA, ingestão de email e dashboard administrativo.

**Stack:** FastAPI + SQLite + Vue 3 | **Tempo de dev:** 280h | **Status:** 92% ✅

---

## 🚀 Quickstart (5 minutos)

### 1. Backend

```bash
cd backend

# Criar venv
python3 -m venv .venv
source .venv/bin/activate  # ou .venv\Scripts\activate no Windows

# Instalar dependências
pip install -r requirements.txt

# Copiar variáveis de ambiente
cp .env.example .env

# Criar BD e popular com dados de exemplo
python -m app.seed

# Arrancar servidor
uvicorn app.main:app --reload --port 8000
```

O backend estará em **http://localhost:8000** — testa em http://localhost:8000/docs (Swagger).

### 2. Frontend

Noutra terminal:

```bash
cd frontend

# Abrir HTML com live server
python -m http.server 5500
# ou usa VS Code Live Server (F5)
```

Abre **http://localhost:5500** no browser.

### 3. Credenciais padrão

| Email | Password | Role |
|-------|----------|------|
| `admin@helpdesk.local` | `admin123` | Admin |
| `tech.eliude@helpdesk.local` | `tech123` | Técnico |
| `user.eliude@helpdesk.local` | `user123` | Utilizador |

---

## 📋 Estrutura do Projeto

```
helpdesk/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app
│   │   ├── config.py            # Env vars
│   │   ├── database.py          # SQLAlchemy setup
│   │   ├── auth.py              # JWT + roles
│   │   ├── seed.py              # Dados exemplo
│   │   ├── models/              # ORM models (6 tabelas)
│   │   ├── routes/              # Endpoints (5 routers)
│   │   ├── schemas/             # Pydantic schemas
│   │   └── services/            # Email, SLA, scheduler
│   ├── email_templates/         # Templates HTML para email
│   ├── requirements.txt
│   ├── .env.example
│   ├── .gitignore
│   └── helpdesk.db              # SQLite (criado ao correr seed)
│
├── frontend/
│   ├── index.html
│   ├── app.js                   # Vue app setup
│   ├── router/
│   │   └── index.js             # Vue Router config
│   ├── services/
│   │   ├── http.js              # Fetch wrapper + JWT
│   │   └── auth.js              # Auth service
│   ├── components/
│   │   └── AppLayout.js         # Sidebar + header
│   └── pages/
│       ├── LoginPage.js
│       ├── TicketListPage.js    # Tabela, filtros, create
│       ├── TicketDetailPage.js  # Detalhe, comentários, história
│       ├── AdminDashboardPage.js # Métricas, gráficos, CSV
│       └── UsersPage.js         # Gestão de utilizadores
│
├── PROGRESSO.md                 # Status detalhado
└── README.md                    # Este ficheiro
```

---

## 🔧 Configuração (`.env`)

```env
# Aplicação
DEBUG=True

# Base de dados
DATABASE_URL=sqlite:///./helpdesk.db

# JWT
SECRET_KEY=change-me-in-production-to-a-long-random-string
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# SMTP (para envio de email)
SMTP_SERVER=localhost
SMTP_PORT=1025           # Mailpit local por defeito
SMTP_FROM=helpdesk@localhost

# IMAP (para ingestão de email)
IMAP_ENABLED=False       # Ativar quando houver Mailpit
IMAP_SERVER=localhost
IMAP_PORT=1143
IMAP_MAILBOX=INBOX

# Scheduler
SCHEDULER_ENABLED=True
IMAP_POLLING_MINUTES=2
SLA_CHECK_MINUTES=5

# Frontend
CORS_ORIGINS=http://localhost:5500,http://localhost:8080
FRONTEND_URL=http://localhost:5500
```

### Mailpit (Email local)

Para testar emails em desenvolvimento, instala **Mailpit**:

```bash
# macOS
brew install mailpit

# Ou download em https://mailpit.axllent.org/

# Arrancar
mailpit
# Estará em http://localhost:8025 (web UI)
# SMTP: localhost:1025
# IMAP: localhost:1143
```

---

## 📡 API Overview

### Autenticação

```bash
# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@helpdesk.local&password=admin123"

# Resposta
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": { "id": 1, "name": "Admin", "role": "admin", ... }
}

# Usar token em requests
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer eyJ..."
```

### Tickets

```bash
# Listar (com filtros)
GET /tickets?status=open&priority=high&page=1&page_size=20

# Criar
POST /tickets
{ "title": "...", "description": "...", "priority": "medium", "category_id": 1 }

# Detalhe
GET /tickets/1

# Editar
PUT /tickets/1
{ "title": "...", "description": "..." }

# Transição de estado
PUT /tickets/1/status
{ "status": "in_progress" }

# Atribuir técnico
PUT /tickets/1/assign
{ "assignee_id": 2 }

# Adicionar comentário
POST /tickets/1/comments
{ "body": "...", "is_internal": false }
```

### Admin

```bash
# Utilizadores
GET    /users
POST   /users                           { "name": "...", "email": "...", "password": "...", "role": "user" }
PUT    /users/{id}/role                 { "role": "tech" }
PUT    /users/{id}/active               { "active": true }
GET    /users/techs                     # Listar técnicos para atribuição

# Dashboard
GET    /reports/dashboard?days=30

# CSV mensal
GET    /reports/monthly?month=2026-05
```

**Documentação interativa:** http://localhost:8000/docs (Swagger UI automático pelo FastAPI)

---

## 📚 Funcionalidades

### ✅ Implementado

- **Autenticação:** JWT com 3 roles (admin, tech, user)
- **Tickets:** CRUD com workflow validado (open → in_progress → awaiting_reply → resolved → closed)
- **SLA:** Cálculo automático, status (ok/warning/breached), checker que marca violações
- **Comentários:** Públicos/internos, histórico de alterações
- **Email:** Templates HTML, ingestão IMAP (polling automático)
- **Dashboard:** Métricas (cards), gráficos (Chart.js), distribuição por categoria, top técnicos
- **Exportação:** CSV mensal de todos os tickets
- **RBAC:** Utilizador vê só os seus, técnico vê atribuídos, admin vê tudo

### ⚠️ Falta (opcional)

- Testes pytest (cobertura)
- Docker setup
- Autoscaler para técnicos (round-robin vs load balancing)
- Webhooks
- Two-factor auth

---

## 🧪 Testar Localmente

### 1. Login
- Vai a http://localhost:5500
- Email: `admin@helpdesk.local`, Password: `admin123`

### 2. Criar ticket
- Clica "+ Novo ticket"
- Preenche título, descrição
- Clica "Criar ticket"

### 3. Atribuir
- Clica no ticket na lista
- Dropdown "Técnico" → seleciona um técnico
- Escreve um comentário se quiser

### 4. Resolver
- Dropdown "Estado" → "Resolvido"
- Clica guardar

### 5. Dashboard
- Admin → Dashboard
- Vê as métricas dos últimos 30 dias
- Descarrega CSV

### 6. Gestão de utilizadores
- Admin → Utilizadores
- Cria um novo utilizador
- Muda o role/status

---

## 🚢 Deploy

### Development (local)
```bash
cd backend
uvicorn app.main:app --reload --port 8000

cd frontend
python -m http.server 5500
```

### Production (basic)

1. **Backend**
   ```bash
   pip install gunicorn
   gunicorn app.main:app --workers 4 --bind 0.0.0.0:8000
   ```

2. **Frontend**
   - Build com Vite ou webpack
   - Servir ficheiros estáticos (nginx, Apache, ou S3)

3. **Variáveis críticas**
   ```env
   SECRET_KEY=<random-64-chars>
   DATABASE_URL=postgresql://user:pass@db:5432/helpdesk  # ou URL de prod
   SMTP_SERVER=mail.example.com
   SMTP_USER=helpdesk@example.com
   SMTP_PASSWORD=...
   CORS_ORIGINS=https://example.com
   FRONTEND_URL=https://example.com
   ```

### Docker (opcional)

```dockerfile
# backend/Dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache -r requirements.txt
COPY app/ ./app/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: sqlite:///./helpdesk.db
      SCHEDULER_ENABLED: "true"
    volumes:
      - ./backend:/app
  
  frontend:
    image: python:3.12
    working_dir: /app
    command: python -m http.server 5500
    ports:
      - "5500:5500"
    volumes:
      - ./frontend:/app
  
  mailpit:
    image: axllent/mailpit:latest
    ports:
      - "8025:8025"  # Web UI
      - "1025:1025"  # SMTP
      - "1143:1143"  # IMAP
```

```bash
docker-compose up
```

---

## 📖 Documentação Adicional

- **PROGRESSO.md** — Status detalhado de cada fase
- **Swagger UI** — http://localhost:8000/docs (interativo, depois de arrancar)
- **Estrutura de BD** — vê `app/models/` para definições completas

---

## 🔐 Segurança (checklist para produção)

- [ ] Mudar `SECRET_KEY` para string aleatória longa
- [ ] Usar HTTPS (certificado SSL/TLS)
- [ ] Base de dados em RDS/managed (não SQLite local)
- [ ] CORS configurado apenas para o domínio da app
- [ ] Rate limiting nos endpoints de login
- [ ] CSRF tokens (se necessário)
- [ ] Logs de auditoria
- [ ] Backups automáticos da BD
- [ ] Monitoramento de SLA breaches

---

## 🐛 Troubleshooting

### Backend não arranca

```bash
# Verifica se a porta 8000 está livre
lsof -i :8000

# Cria venv de novo
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Recreia BD
rm -f helpdesk.db
python -m app.seed
```

### Frontend não carrega

- Verifica se o backend está a correr em http://localhost:8000
- Abre a consola do browser (F12) e vê os errors
- Garante que scripts estão em HTML na ordem certa

### Login falha

- Verifica que utilizador existe: `python -c "from app.database import SessionLocal; from app.models import User; db = SessionLocal(); print(db.query(User).all())"`
- Verifica password correcta (seed usa `admin123`, etc.)
- Limpa localStorage: `localStorage.clear()` na consola do browser

---

## 📞 Suporte

- **Issues no código:** Vê PROGRESSO.md para status
- **Testes:** `pytest backend/tests/` (quando implementados)
- **Logs:** Vê `.venv/logs/` ou stdout do uvicorn

---

**Made with ❤️ for a 300-hour placement.**  
**Last updated:** 2026-05-25  
**Ready to ship:** ✅ Yes

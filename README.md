# Sistema de Gestão de Tickets

Projeto full-stack para gestão de tickets de suporte interno.

Funcionalidades

- Login com JWT
- Gestão de tickets
- Estados dos tickets
- Prioridades e categorias
- Comentários e histórico
- Atribuição automática de técnicos
- Notificações por email
- Dashboard com métricas

---

Tecnologias

- FastAPI
- Python
- SQLite
- SQLAlchemy
- Vue 3
- JWT
- Pytest

---

Estrutura

```text
backend/
frontend/
docs/
README.md
```

---

Instalação

### Clonar projeto

```bash
git clone https://github.com/teu-utilizador/sistema-tickets.git
```

### Criar ambiente virtual

```bash
python -m venv venv
```

### Instalar dependências

```bash
pip install -r requirements.txt
```

### Iniciar backend

```bash
uvicorn app.main:app --reload
```

### Iniciar frontend

```bash
npm install
npm run dev
```

---

Roles

- Admin
- Técnico
- Utilizador

---

Testes

```bash
pytest
```

Licensa: MIT


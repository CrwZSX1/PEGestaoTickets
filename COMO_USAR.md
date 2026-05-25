# 🚀 COMO USAR A APLICAÇÃO HELPDESK

## Início Rápido (5 Minutos)

### 1️⃣ Arrancar Backend

```bash
cd /home/claude/helpdesk/backend
./venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Verificar se está rodando:**
```bash
curl http://localhost:8000/health
# Response: {"status":"online","version":"1.0.0"}
```

### 2️⃣ Arrancar Frontend (em outro terminal)

```bash
cd /home/claude/helpdesk/frontend
python -m http.server 5500
```

### 3️⃣ Abrir no Browser

Vai a: **http://localhost:5500**

---

## 🔐 Fazer Login

### Credenciais Disponíveis

#### Admin (Acesso Total)
- **Email:** admin@helpdesk.local
- **Password:** admin123
- **Acesso a:** Tudo (tickets, users, dashboard, relatórios)

#### Técnico (Gestão de Tickets)
- **Email:** tech.eliude@helpdesk.local
- **Password:** tech123
- **Acesso a:** Tickets atribuídos + dashboard

#### Utilizador Normal (Criar Tickets)
- **Email:** user.eliude@helpdesk.local
- **Password:** user123
- **Acesso a:** Seus próprios tickets

---

## 📋 Funcionalidades Principais

### ✅ 1. VER LISTA DE TICKETS

**Onde?** Página principal após login

**O que pode fazer:**
- Ver todos os tickets (se admin) ou seus tickets (se user)
- Filtrar por:
  - Estado (Aberto, Em curso, Aguarda resposta, Resolvido, Fechado)
  - Prioridade (Baixa, Média, Alta, Crítica)
  - Categoria (Hardware, Software, Rede, Acesso, etc.)
- Ver SLA status com indicadores:
  - 🟢 Verde: SLA OK (< 75% tempo decorrido)
  - 🟡 Amarelo: Aviso (75-100%)
  - 🔴 Vermelho: Violado (deadline passou)
  - ⚪ Branco: Resolvido/Fechado
- Paginar entre tickets

---

### ✅ 2. CRIAR NOVO TICKET

**Como?**
1. Clica em "+ Novo ticket" (canto superior direito)
2. Preenche o formulário:
   - **Título:** Descrição breve do problema
   - **Descrição:** Detalhes completos
   - **Prioridade:** Baixa/Média/Alta/Crítica
   - **Categoria:** Hardware/Software/Rede/Acesso/Outro
3. Clica "Criar ticket"

**O que acontece?**
- Ticket é criado automaticamente
- Um técnico é atribuído (round-robin por categoria)
- Email enviado ao técnico atribuído
- SLA deadline calculado automaticamente
- Ticket aparece na lista

---

### ✅ 3. VER DETALHE DO TICKET

**Como?**
1. Clica num ticket da lista

**O que vê?**
- Informações completas do ticket
- Estado atual
- Prioridade e SLA
- Quem criou e quem está atribuído
- **Comentários:**
  - Públicos (visíveis para todos)
  - Internos (só técnicos e admin)
- **Histórico:** Todas as alterações feitas
- **Ações** (dependendo do seu perfil):
  - Mudar estado
  - Atribuir a outro técnico
  - Adicionar comentário

---

### ✅ 4. TRANSIÇÃO DE ESTADOS

**Estados possíveis:**
```
Aberto
  ↓
Em Curso (ou Aguarda Resposta)
  ↓
Resolvido
  ↓
Fechado
```

**Como mudar?**
1. Abre o detalhe do ticket
2. Dropdown "Estado" mostra opções disponíveis
3. Seleciona novo estado
4. Clica guardar
5. Histórico é atualizado automaticamente

---

### ✅ 5. ADICIONAR COMENTÁRIO

**Como?**
1. Abre detalhe do ticket
2. Secção "Novo comentário"
3. Escreve o comentário
4. Marca "Nota interna" se for só para técnicos
5. Clica "Comentar"

**O que acontece?**
- Comentário aparece na lista
- Email enviado ao técnico/criador (se público)
- Tempo registado

---

### ✅ 6. DASHBOARD ADMIN

**Como aceder?**
1. Menu superior: "Dashboard" (só para admin)

**O que vê?**
- **4 Cards com métricas (últimos 30 dias):**
  - 📊 Tickets abertos
  - ✅ Tickets resolvidos
  - ⚠️ Violações de SLA
  - ⏱️ Tempo médio de resolução

- **Gráficos:**
  - Linha: Criados vs Resolvidos por dia
  - Pizza: Distribuição por categoria

- **Top Técnicos:**
  - Ranking por tickets resolvidos
  - % SLA compliance

- **Exportação:**
  - CSV mensal de todos os tickets

---

### ✅ 7. GESTÃO DE UTILIZADORES

**Como aceder?**
1. Menu: "Admin" → "Utilizadores" (só admin)

**O que pode fazer:**
- Ver lista de todos os utilizadores
- **Criar novo utilizador:**
  - Clica "+ Novo utilizador"
  - Preenche: Nome, Email, Password, Perfil
  - Clica "Criar"

- **Mudar perfil:**
  - Dropdown "Perfil" → seleciona Admin/Técnico/Utilizador

- **Ativar/Desativar:**
  - Toggle "Ativo" → ativa ou desativa conta

---

## 🎮 Exemplos de Uso

### Cenário 1: Utilizador Normal Cria Ticket

```
1. Faz login com user.eliude@helpdesk.local
2. Clica "+ Novo ticket"
3. Preenche: "Monitor não liga", "Hardware", "Alta"
4. Clica "Criar"
5. ✅ Ticket #15 criado
   - Técnico Eliúde é atribuído automaticamente
   - Email enviado a tech.eliude@helpdesk.local
   - Deadline: 24 horas
```

### Cenário 2: Técnico Resolve Ticket

```
1. Técnico faz login com tech.eliude@helpdesk.local
2. Vê lista de tickets atribuídos
3. Clica num ticket
4. Dropdown Estado: "Em curso"
5. Adiciona comentário: "A reboot resolveu"
6. Dropdown Estado: "Resolvido"
7. ✅ Ticket resolvido
   - Email enviado ao criador
   - SLA verificado (passou ou não)
   - Histórico atualizado
```

### Cenário 3: Admin Vê Dashboard

```
1. Admin faz login
2. Clica "Dashboard"
3. Vê:
   - 7 tickets abertos
   - 3 resolvidos (30d)
   - 1 SLA violado
   - 20h tempo médio
   - Gráficos com tendências
   - Top técnico: Eliúde (100% SLA)
4. Clica "Descarregar CSV"
   - Arquivo com todos os tickets do mês
```

---

## 📞 API DOCUMENTATION

### Testar API com Swagger

1. Vai a: **http://localhost:8000/docs**
2. Swagger UI abre com todos os endpoints
3. Clica "Try it out" para testar endpoints
4. Autoriza com JWT token (obtém fazendo login)

### Endpoints principais

```
POST   /auth/login              → Fazer login
GET    /auth/me                 → Perfil atual
GET    /tickets                 → Listar tickets
POST   /tickets                 → Criar ticket
GET    /tickets/{id}            → Detalhe do ticket
PUT    /tickets/{id}/status     → Mudar estado
POST   /tickets/{id}/comments   → Adicionar comentário
GET    /reports/dashboard       → Dashboard
GET    /users                   → Listar utilizadores
POST   /users                   → Criar utilizador
```

---

## 🔧 TROUBLESHOOTING

### Backend não arranca

```bash
# Verifica se a porta 8000 está livre
lsof -i :8000

# Se houver processo, mata-o
kill -9 <PID>

# Recria venv do zero
rm -rf venv
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

### Frontend não carrega

```bash
# Verifica se backend está online
curl http://localhost:8000/health

# Limpa cache do browser
Ctrl+Shift+Delete (windows/linux)
Cmd+Shift+Delete (mac)

# Verifica consola do browser (F12)
```

### Login falha

```bash
# Verifica se credenciais existem na BD
python -m app.seed --reset   # (cuidado: apaga dados!)

# Credenciais default:
# admin@helpdesk.local / admin123
```

### Email não é enviado

```bash
# IMAP/SMTP desativados por default em .env
# Para testar, ativa Mailpit:
brew install mailpit  # ou download em mailpit.axllent.org

# Depois:
IMAP_ENABLED=True SMTP_SERVER=localhost:1025 ...
```

---

## 📚 DOCUMENTAÇÃO ADICIONAL

- `README.md` - Setup e overview
- `PROGRESSO.md` - Status do projeto
- `DIAGRAMA_COMPLETO.txt` - Arquitetura completa
- `DIAGRAMA_VISUAL_ARVORE.txt` - Estrutura visual

---

## ✅ VERIFICAÇÃO RÁPIDA

```bash
# Backend rodando?
curl -s http://localhost:8000/health | grep "online"

# Frontend rodando?
curl -s http://localhost:5500 | grep -c "<!DOCTYPE"

# BD tem dados?
sqlite3 backend/helpdesk.db "SELECT COUNT(*) FROM tickets;"

# Pode fazer login?
curl -s -X POST http://localhost:8000/auth/login \
  -d "username=admin@helpdesk.local&password=admin123" | grep "access_token"
```

Se tudo retorna ✅, aplicação está pronta para usar!


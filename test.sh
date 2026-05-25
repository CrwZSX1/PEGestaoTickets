#!/bin/bash
# test.sh — Script de teste rápido do projeto

set -e

echo "🧪 Teste de Integridade do Projeto Helpdesk"
echo "==========================================="
echo ""

# 1. Verificar estrutura
echo "✅ 1. Verificando estrutura..."
[ -d "backend/app" ] && echo "   ✓ backend/app/" || (echo "   ✗ FALTA backend/app/"; exit 1)
[ -d "frontend/pages" ] && echo "   ✓ frontend/pages/" || (echo "   ✗ FALTA frontend/pages/"; exit 1)
[ -f "README.md" ] && echo "   ✓ README.md" || (echo "   ✗ FALTA README.md"; exit 1)
[ -f "PROGRESSO.md" ] && echo "   ✓ PROGRESSO.md" || (echo "   ✗ FALTA PROGRESSO.md"; exit 1)
echo ""

# 2. Verificar backend
echo "✅ 2. Verificando backend..."
cd backend
[ -d ".venv" ] || (echo "   ⚠️  Venv não existe, criando..."; python3 -m venv .venv; .venv/bin/pip install -q -r requirements.txt)
.venv/bin/python -c "import app.models; from app.database import init_db; init_db(); print('   ✓ Database init OK')"
.venv/bin/python -c "import app.auth; import app.main; print('   ✓ Backend imports OK')"
cd ..
echo ""

# 3. Verificar frontend
echo "✅ 3. Verificando frontend..."
[ -f "frontend/index.html" ] && echo "   ✓ index.html" || (echo "   ✗ FALTA index.html"; exit 1)
[ -f "frontend/app.js" ] && echo "   ✓ app.js" || (echo "   ✗ FALTA app.js"; exit 1)
[ -f "frontend/pages/LoginPage.js" ] && echo "   ✓ LoginPage.js" || (echo "   ✗ FALTA LoginPage.js"; exit 1)
[ -f "frontend/pages/TicketListPage.js" ] && echo "   ✓ TicketListPage.js" || (echo "   ✗ FALTA TicketListPage.js"; exit 1)
[ -f "frontend/pages/TicketDetailPage.js" ] && echo "   ✓ TicketDetailPage.js" || (echo "   ✗ FALTA TicketDetailPage.js"; exit 1)
[ -f "frontend/pages/AdminDashboardPage.js" ] && echo "   ✓ AdminDashboardPage.js" || (echo "   ✗ FALTA AdminDashboardPage.js"; exit 1)
[ -f "frontend/pages/UsersPage.js" ] && echo "   ✓ UsersPage.js" || (echo "   ✗ FALTA UsersPage.js"; exit 1)
echo ""

# 4. Verificar ficheiros críticos
echo "✅ 4. Verificando ficheiros críticos..."
CRITICAL_FILES=(
    "backend/app/config.py"
    "backend/app/database.py"
    "backend/app/main.py"
    "backend/app/auth.py"
    "backend/app/seed.py"
    "backend/app/models/ticket.py"
    "backend/app/routes/auth.py"
    "backend/app/routes/tickets.py"
    "backend/app/services/email.py"
    "backend/app/services/scheduler.py"
    "backend/email_templates/ticket_assigned.html"
    "backend/requirements.txt"
    "frontend/router/index.js"
    "frontend/services/http.js"
)

for file in "${CRITICAL_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✓ $file"
    else
        echo "   ✗ FALTA $file"
        exit 1
    fi
done
echo ""

# 5. Contagem de linhas
echo "✅ 5. Estatísticas..."
BACKEND_LINES=$(find backend/app -name "*.py" -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $1}')
FRONTEND_LINES=$(find frontend -name "*.js" -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $1}')
echo "   Backend: ~$BACKEND_LINES linhas de Python"
echo "   Frontend: ~$FRONTEND_LINES linhas de JavaScript"
echo ""

# 6. Informação de deploy
echo "✅ 6. Pronto para deploy!"
echo ""
echo "Para arrancar:"
echo ""
echo "  Backend:"
echo "    cd backend"
echo "    python -m app.seed"
echo "    uvicorn app.main:app --reload"
echo ""
echo "  Frontend (noutra terminal):"
echo "    cd frontend"
echo "    python -m http.server 5500"
echo ""
echo "Credenciais:"
echo "  admin@helpdesk.local / admin123"
echo "  tech.eliude@helpdesk.local / tech123"
echo "  user.eliude@helpdesk.local / user123"
echo ""
echo "URL:"
echo "  Frontend: http://localhost:5500"
echo "  API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "✅ Tudo OK! Projeto pronto para entrega."

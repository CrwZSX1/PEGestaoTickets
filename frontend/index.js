/**
 * frontend/router/index.js
 * Configuração do Vue Router com guardas de rota:
 *  - Redireciona para /login se sem token
 *  - Bloqueia rotas por role
 *  - Redireciona para dashboard se já autenticado e tentar aceder ao login
 */

// As pages são registadas depois de carregarem os seus scripts.
// O router usa lazy-ish components via função — os globals já estão disponíveis.

const routes = [
  {
    path: '/',
    redirect: '/tickets',
  },
  {
    path: '/login',
    name: 'login',
    component: { template: '<login-page />' },
    meta: { public: true },
  },
  {
    path: '/tickets',
    name: 'tickets',
    component: { template: '<div><router-view /></div>' },
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'ticket-list',
        component: { template: '<ticket-list-page />' },
      },
      {
        path: ':id',
        name: 'ticket-detail',
        component: { template: '<ticket-detail-page />' },
        props: true,
      },
    ],
  },
  {
    path: '/admin',
    name: 'admin',
    meta: { requiresAuth: true, roles: ['admin'] },
    children: [
      {
        path: 'dashboard',
        name: 'admin-dashboard',
        component: { template: '<dashboard-page />' },
      },
      {
        path: 'users',
        name: 'admin-users',
        component: { template: '<users-page />' },
      },
    ],
  },
  {
    // 404
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: { template: `
      <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;gap:16px;color:var(--text-secondary)">
        <div style="font-size:64px;font-weight:300;color:var(--text-muted)">404</div>
        <div style="font-size:16px">Página não encontrada</div>
        <a href="#/tickets" style="color:var(--accent);text-decoration:none;font-size:13px">← Voltar aos tickets</a>
      </div>
    ` },
  },
];

const router = VueRouter.createRouter({
  history: VueRouter.createWebHashHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
});

// ── Guardas de rota ────────────────────────────────────────────────────────
router.beforeEach((to, from, next) => {
  const loggedIn = authService.isLoggedIn();
  const user     = authService.currentUser();

  // Rota pública — se já autenticado, redirecionar para tickets
  if (to.meta.public) {
    return loggedIn ? next({ name: 'ticket-list' }) : next();
  }

  // Rota protegida — sem sessão → login
  if (to.meta.requiresAuth && !loggedIn) {
    return next({ name: 'login', query: { redirect: to.fullPath } });
  }

  // Verificação de role
  if (to.meta.roles && user && !to.meta.roles.includes(user.role)) {
    return next({ name: 'ticket-list' }); // redirecionar sem acesso
  }

  next();
});
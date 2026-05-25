/**
 * frontend/router/index.js
 * Configuração do Vue Router com guardas de rota.
 *
 * Estrutura:
 *  /login            -> LoginPage (sem layout)
 *  /                 -> AppLayout (com sidebar/header)
 *    /tickets        -> TicketListPage
 *    /tickets/:id    -> TicketDetailPage
 *    /admin/dashboard-> AdminDashboardPage   (admin)
 *    /admin/users    -> UsersPage            (admin)
 */

const routes = [
  {
    path: '/login',
    name: 'login',
    component: { template: '<login-page />' },
    meta: { public: true },
  },
  {
    path: '/',
    component: { template: '<app-layout />' },
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: '/tickets' },
      {
        path: 'tickets',
        name: 'ticket-list',
        component: { template: '<ticket-list-page />' },
      },
      {
        path: 'tickets/:id',
        name: 'ticket-detail',
        component: { template: '<ticket-detail-page />' },
        props: true,
      },
      {
        path: 'admin/dashboard',
        name: 'admin-dashboard',
        component: { template: '<admin-dashboard-page />' },
        meta: { roles: ['admin'] },
      },
      {
        path: 'admin/users',
        name: 'admin-users',
        component: { template: '<users-page />' },
        meta: { roles: ['admin'] },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: {
      template: `
        <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100vh;gap:16px;color:var(--text-secondary)">
          <div style="font-size:64px;font-weight:300;color:var(--text-muted)">404</div>
          <div style="font-size:16px">Página não encontrada</div>
          <a href="#/tickets" style="color:var(--accent);text-decoration:none;font-size:13px">← Voltar aos tickets</a>
        </div>
      `,
    },
  },
];

const router = VueRouter.createRouter({
  history: VueRouter.createWebHashHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
});

router.beforeEach((to, from, next) => {
  const loggedIn = authService.isLoggedIn();
  const user = authService.currentUser();

  if (to.meta.public) {
    return loggedIn ? next({ name: 'ticket-list' }) : next();
  }

  if (to.meta.requiresAuth && !loggedIn) {
    return next({ name: 'login', query: { redirect: to.fullPath } });
  }

  for (const record of to.matched) {
    if (record.meta?.roles && user && !record.meta.roles.includes(user.role)) {
      return next({ name: 'ticket-list' });
    }
  }

  next();
});

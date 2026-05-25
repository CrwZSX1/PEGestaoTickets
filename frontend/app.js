/**
 * frontend/app.js
 * Ponto de entrada — cria a Vue app, regista componentes globais e arranca.
 */

const app = Vue.createApp({});

// Componentes globais — usados nos templates do router
app.component('app-layout',           AppLayout);
app.component('login-page',           LoginPage);
app.component('ticket-list-page',     TicketListPage);
app.component('ticket-detail-page',   TicketDetailPage);
app.component('admin-dashboard-page', AdminDashboardPage);
app.component('users-page',           UsersPage);

app.use(router);
app.mount('#app');

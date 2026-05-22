/**
 * frontend/components/AppLayout.js
 * Layout base da aplicação:
 *  - Sidebar com menu por role
 *  - Header com nome do utilizador e logout
 *  - Área de conteúdo com router-view e animação de página
 */

const AppLayout = {
  name: 'AppLayout',
  template: `
    <div class="layout" :class="{ 'sidebar-collapsed': sidebarCollapsed }">

      <!-- ── Sidebar ──────────────────────────────────────────────────── -->
      <aside class="sidebar">
        <div class="sidebar-logo">
          <span class="logo-mark">HD</span>
          <span class="logo-text" v-show="!sidebarCollapsed">Helpdesk</span>
        </div>

        <nav class="sidebar-nav">
          <div class="nav-section">
            <span class="nav-label" v-show="!sidebarCollapsed">Geral</span>
            <router-link to="/tickets" class="nav-item" active-class="nav-item--active">
              <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M3 5h14M3 10h14M3 15h8" stroke-linecap="round"/>
              </svg>
              <span v-show="!sidebarCollapsed">Tickets</span>
            </router-link>
          </div>

          <div class="nav-section" v-if="isAdminOrTech">
            <span class="nav-label" v-show="!sidebarCollapsed">Gestão</span>
            <router-link v-if="isAdmin" to="/admin/dashboard" class="nav-item" active-class="nav-item--active">
              <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5">
                <rect x="2" y="2" width="7" height="7" rx="1.5"/>
                <rect x="11" y="2" width="7" height="7" rx="1.5"/>
                <rect x="2" y="11" width="7" height="7" rx="1.5"/>
                <rect x="11" y="11" width="7" height="7" rx="1.5"/>
              </svg>
              <span v-show="!sidebarCollapsed">Dashboard</span>
            </router-link>
            <router-link v-if="isAdmin" to="/admin/users" class="nav-item" active-class="nav-item--active">
              <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5">
                <circle cx="8" cy="7" r="3"/>
                <path d="M2 17c0-3.314 2.686-6 6-6h4c3.314 0 6 2.686 6 6" stroke-linecap="round"/>
              </svg>
              <span v-show="!sidebarCollapsed">Utilizadores</span>
            </router-link>
          </div>
        </nav>

        <!-- Colapsar sidebar -->
        <button class="sidebar-toggle" @click="sidebarCollapsed = !sidebarCollapsed" :title="sidebarCollapsed ? 'Expandir' : 'Colapsar'">
          <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" style="width:16px;height:16px;transition:transform .2s" :style="sidebarCollapsed ? 'transform:rotate(180deg)' : ''">
            <path d="M12 4L6 10l6 6" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </aside>

      <!-- ── Main ─────────────────────────────────────────────────────── -->
      <div class="main">

        <!-- Header -->
        <header class="header">
          <div class="header-left">
            <h1 class="page-title">{{ pageTitle }}</h1>
          </div>
          <div class="header-right">
            <div class="user-pill">
              <div class="user-avatar">{{ userInitials }}</div>
              <div class="user-info" v-if="user">
                <span class="user-name">{{ user.name }}</span>
                <span class="user-role">{{ roleLabel }}</span>
              </div>
            </div>
            <button class="btn btn-ghost" style="padding:0 10px;height:32px" @click="logout" title="Sair">
              <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" style="width:16px;height:16px">
                <path d="M7 3H4a1 1 0 00-1 1v12a1 1 0 001 1h3M13 7l4 3-4 3M17 10H7" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
          </div>
        </header>

        <!-- Content -->
        <main class="content">
          <router-view v-slot="{ Component }">
            <transition name="page" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </main>
      </div>

      <!-- Toast notifications -->
      <div class="toast-wrap">
        <div v-for="t in toasts" :key="t.id" class="toast" :class="t.type">
          {{ t.message }}
        </div>
      </div>
    </div>
  `,

  setup() {
    const route  = VueRouter.useRoute();
    const router = VueRouter.useRouter();
    const { ref, computed } = Vue;

    const sidebarCollapsed = ref(false);
    const toasts = ref([]);

    const user = computed(() => authService.currentUser());
    const isAdmin      = computed(() => authService.isAdmin());
    const isAdminOrTech= computed(() => authService.isAdminOrTech());

    const userInitials = computed(() => {
      if (!user.value) return '?';
      return user.value.name.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase();
    });

    const roleLabel = computed(() => {
      const map = { admin: 'Administrador', tech: 'Técnico', user: 'Utilizador' };
      return user.value ? (map[user.value.role] || user.value.role) : '';
    });

    const pageTitle = computed(() => {
      const map = {
        'ticket-list':    'Tickets',
        'ticket-detail':  'Detalhe do Ticket',
        'admin-dashboard':'Dashboard',
        'admin-users':    'Utilizadores',
      };
      return map[route.name] || 'Helpdesk';
    });

    function logout() {
      authService.logout();
      router.push({ name: 'login' });
    }

    // Toast global via evento
    function showToast(message, type = 'info') {
      const id = Date.now();
      toasts.value.push({ id, message, type });
      setTimeout(() => {
        toasts.value = toasts.value.filter(t => t.id !== id);
      }, 3500);
    }

    window.addEventListener('hd:toast', e => showToast(e.detail.message, e.detail.type));

    return { sidebarCollapsed, user, userInitials, roleLabel, pageTitle, isAdmin, isAdminOrTech, toasts, logout };
  },
};

// Utilitário global para disparar toasts de qualquer parte da app
window.hdToast = (message, type = 'info') => {
  window.dispatchEvent(new CustomEvent('hd:toast', { detail: { message, type } }));
};
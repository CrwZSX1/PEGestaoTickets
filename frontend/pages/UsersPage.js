/**
 * frontend/pages/UsersPage.js
 * Gestão de utilizadores — criar, editar role e status (admin only).
 */

const UsersPage = {
  name: 'UsersPage',
  template: `
    <div class="users-page">
      <div class="toolbar">
        <h2 style="font-size:18px;font-weight:500">Utilizadores</h2>
        <button class="btn btn-primary" @click="openCreate">+ Novo utilizador</button>
      </div>

      <div class="card" style="padding:0;overflow:hidden">
        <div v-if="loading" class="loading-center">
          <span class="spinner"></span> A carregar utilizadores...
        </div>

        <div v-else-if="users.length === 0" class="loading-center">Nenhum utilizador encontrado.</div>

        <table v-else class="users-table">
          <thead>
            <tr>
              <th>Nome</th>
              <th>Email</th>
              <th>Perfil</th>
              <th>Status</th>
              <th>Criado</th>
              <th>Ações</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in users" :key="u.id">
              <td class="title-cell">{{ u.name }}</td>
              <td class="mono" style="font-size:12px">{{ u.email }}</td>
              <td>
                <select :value="u.role" @change="changeRole(u, $event.target.value)" class="input" style="width:120px;height:32px;font-size:12px">
                  <option value="admin">Admin</option>
                  <option value="tech">Técnico</option>
                  <option value="user">Utilizador</option>
                </select>
              </td>
              <td>
                <label class="checkbox" style="margin:0">
                  <input type="checkbox" :checked="u.active" @change="toggleActive(u)" />
                  <span>{{ u.active ? 'Ativo' : 'Inativo' }}</span>
                </label>
              </td>
              <td class="muted" style="font-size:12px">{{ formatDate(u.created_at) }}</td>
              <td>
                <button v-if="u.id !== currentUser.id && !u.active" class="btn btn-ghost" @click="toggleActive(u)" style="font-size:11px">
                  Reactivar
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Drawer de novo utilizador -->
      <div v-if="showCreate" class="drawer-backdrop" @click.self="showCreate = false">
        <div class="drawer">
          <div class="drawer-header">
            <h3>Novo utilizador</h3>
            <button class="btn btn-ghost" @click="showCreate = false" style="padding:0 10px;height:32px">✕</button>
          </div>
          <form @submit.prevent="submitCreate" class="drawer-body">
            <div class="field">
              <label>Nome</label>
              <input v-model="newUser.name" class="input" required minlength="2" maxlength="120" />
            </div>
            <div class="field">
              <label>Email</label>
              <input v-model="newUser.email" class="input" type="email" required />
            </div>
            <div class="field">
              <label>Password</label>
              <input v-model="newUser.password" class="input" type="password" required minlength="6" />
            </div>
            <div class="field">
              <label>Perfil</label>
              <select v-model="newUser.role" class="input">
                <option value="admin">Admin</option>
                <option value="tech">Técnico</option>
                <option value="user">Utilizador</option>
              </select>
            </div>
            <div v-if="createError" class="api-error">{{ createError }}</div>
            <div class="drawer-footer">
              <button type="button" class="btn btn-ghost" @click="showCreate = false">Cancelar</button>
              <button type="submit" class="btn btn-primary" :disabled="creating">
                {{ creating ? 'A criar...' : 'Criar utilizador' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  `,

  setup() {
    const { ref, reactive, computed, onMounted } = Vue;

    const loading = ref(true);
    const users = ref([]);
    const showCreate = ref(false);
    const creating = ref(false);
    const createError = ref('');
    const currentUser = computed(() => authService.currentUser());

    const newUser = reactive({
      name: '', email: '', password: '', role: 'user',
    });

    async function load() {
      loading.value = true;
      try {
        users.value = await http.get('/users');
      } catch (e) {
        window.hdToast(e.message || 'Erro ao carregar utilizadores', 'error');
      } finally {
        loading.value = false;
      }
    }

    async function changeRole(user, newRole) {
      try {
        const updated = await http.put(`/users/${user.id}/role`, { role: newRole });
        const idx = users.value.findIndex(u => u.id === user.id);
        if (idx >= 0) users.value[idx] = updated;
        window.hdToast('Perfil actualizado', 'success');
      } catch (e) {
        window.hdToast(e.message || 'Erro ao mudar perfil', 'error');
        load();
      }
    }

    async function toggleActive(user) {
      const newActive = !user.active;
      if (!newActive && user.id === currentUser.value.id) {
        window.hdToast('Não podes desactivar a tua própria conta', 'error');
        return;
      }
      try {
        const updated = await http.put(`/users/${user.id}/active`, { active: newActive });
        const idx = users.value.findIndex(u => u.id === user.id);
        if (idx >= 0) users.value[idx] = updated;
        window.hdToast(newActive ? 'Utilizador reactivado' : 'Utilizador desactivado', 'success');
      } catch (e) {
        window.hdToast(e.message || 'Erro ao mudar status', 'error');
        load();
      }
    }

    function openCreate() {
      newUser.name = ''; newUser.email = ''; newUser.password = ''; newUser.role = 'user';
      createError.value = '';
      showCreate.value = true;
    }

    async function submitCreate() {
      creating.value = true; createError.value = '';
      try {
        await http.post('/users', { ...newUser });
        window.hdToast(`Utilizador ${newUser.name} criado`, 'success');
        showCreate.value = false;
        await load();
      } catch (e) {
        createError.value = e.message || 'Erro ao criar utilizador';
      } finally {
        creating.value = false;
      }
    }

    function formatDate(iso) {
      if (!iso) return '—';
      return new Date(iso).toLocaleString('pt-PT', { dateStyle: 'short', timeStyle: 'short' });
    }

    onMounted(load);

    return {
      loading, users, showCreate, creating, createError, currentUser,
      newUser, changeRole, toggleActive, openCreate, submitCreate, formatDate,
    };
  },
};

const _usersStyle = document.createElement('style');
_usersStyle.textContent = `
  .users-page { display:flex; flex-direction:column; gap:16px; }
  .toolbar { display:flex; justify-content:space-between; align-items:center; gap:16px; }

  .users-table { width:100%; border-collapse:collapse; font-size:13px; }
  .users-table th {
    text-align:left; padding:12px 16px; font-weight:500;
    color:var(--text-secondary); font-size:11px; text-transform:uppercase;
    letter-spacing:.06em; border-bottom:1px solid var(--border);
    background:var(--bg-elevated);
  }
  .users-table td { padding:14px 16px; border-bottom:1px solid var(--border); }
  .users-table tr:last-child td { border-bottom:none; }
  .title-cell { font-weight:500; color:var(--text-primary); }
  .mono { font-family:var(--font-mono); color:var(--text-secondary); }
  .muted { color:var(--text-muted); }

  /* Reutilizar estilos de drawer */
  .drawer-backdrop {
    position:fixed; inset:0; background:#0007; z-index:100;
    display:flex; justify-content:flex-end;
    animation:fadeIn 200ms ease;
  }
  .drawer {
    width:520px; max-width:90vw; height:100%; background:var(--bg-surface);
    border-left:1px solid var(--border); display:flex; flex-direction:column;
    animation:slideIn 240ms cubic-bezier(.2,.7,.1,1);
  }
  .drawer-header {
    display:flex; justify-content:space-between; align-items:center;
    padding:20px 24px; border-bottom:1px solid var(--border);
  }
  .drawer-header h3 { font-size:16px; font-weight:500; }
  .drawer-body { padding:24px; display:flex; flex-direction:column; gap:18px; overflow-y:auto; flex:1; }
  .drawer-footer { display:flex; justify-content:flex-end; gap:8px; margin-top:auto; padding-top:8px; }

  .api-error {
    padding:10px 12px; border-radius:var(--radius-sm);
    background:#ff5c721a; border:1px solid #ff5c7250;
    color:var(--danger); font-size:12px;
  }

  @keyframes fadeIn { from{opacity:0;} to{opacity:1;} }
  @keyframes slideIn { from{transform:translateX(40px);opacity:0;} to{transform:none;opacity:1;} }
`;
document.head.appendChild(_usersStyle);

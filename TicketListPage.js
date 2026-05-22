/**
 * frontend/pages/TicketListPage.js
 * Lista de tickets com filtros, paginação, indicador de SLA e drawer de criação.
 */

const TicketListPage = {
  name: 'TicketListPage',
  template: `
    <div class="tickets-page">

      <!-- Toolbar -->
      <div class="toolbar">
        <div class="filters">
          <input v-model="filters.search" @input="debouncedSearch" placeholder="Pesquisar..."
                 class="input" style="width:240px;height:36px" />

          <select v-model="filters.status" @change="reload" class="input" style="width:160px;height:36px">
            <option value="">Estado: todos</option>
            <option value="open">Aberto</option>
            <option value="in_progress">Em curso</option>
            <option value="awaiting_reply">Aguarda resposta</option>
            <option value="resolved">Resolvido</option>
            <option value="closed">Fechado</option>
          </select>

          <select v-model="filters.priority" @change="reload" class="input" style="width:150px;height:36px">
            <option value="">Prioridade: todas</option>
            <option value="low">Baixa</option>
            <option value="medium">Média</option>
            <option value="high">Alta</option>
            <option value="critical">Crítica</option>
          </select>

          <select v-model="filters.category_id" @change="reload" class="input" style="width:160px;height:36px">
            <option value="">Categoria: todas</option>
            <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
        </div>

        <button class="btn btn-primary" @click="openCreate">+ Novo ticket</button>
      </div>

      <!-- Tabela -->
      <div class="card" style="padding:0;overflow:hidden">
        <div v-if="loading" class="loading-center">
          <span class="spinner"></span> A carregar tickets...
        </div>

        <div v-else-if="tickets.length === 0" class="loading-center" style="flex-direction:column">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="width:40px;height:40px;opacity:.3">
            <path d="M3 5h18M3 12h18M3 19h18"/>
          </svg>
          <div>Nenhum ticket encontrado</div>
        </div>

        <table v-else class="tickets-table">
          <thead>
            <tr>
              <th>SLA</th>
              <th>ID</th>
              <th>Título</th>
              <th>Estado</th>
              <th>Prioridade</th>
              <th>Categoria</th>
              <th>Técnico</th>
              <th>Criado</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="t in tickets" :key="t.id" @click="open(t.id)" class="row">
              <td>
                <span class="sla-dot" :class="'sla-' + (t.sla_status || 'ok')"
                      :title="slaTooltip(t)"></span>
              </td>
              <td class="mono">#{{ t.id }}</td>
              <td class="title-cell">{{ t.title }}</td>
              <td><span class="badge" :class="'badge-' + t.status">{{ statusLabel(t.status) }}</span></td>
              <td><span class="badge" :class="'badge-' + t.priority">{{ priorityLabel(t.priority) }}</span></td>
              <td>{{ t.category?.name || '—' }}</td>
              <td>{{ t.assignee?.name || '—' }}</td>
              <td class="muted">{{ formatDate(t.created_at) }}</td>
            </tr>
          </tbody>
        </table>

        <!-- Paginação -->
        <div v-if="tickets.length > 0" class="pagination">
          <span class="page-info">
            {{ ((page - 1) * pageSize) + 1 }}–{{ Math.min(page * pageSize, total) }} de {{ total }}
          </span>
          <div class="page-controls">
            <button class="btn btn-ghost" :disabled="page === 1" @click="goPage(page - 1)">← Anterior</button>
            <span class="page-num">{{ page }} / {{ totalPages }}</span>
            <button class="btn btn-ghost" :disabled="page >= totalPages" @click="goPage(page + 1)">Seguinte →</button>
          </div>
        </div>
      </div>

      <!-- Drawer de criação -->
      <div v-if="showCreate" class="drawer-backdrop" @click.self="showCreate = false">
        <div class="drawer">
          <div class="drawer-header">
            <h3>Novo ticket</h3>
            <button class="btn btn-ghost" @click="showCreate = false" style="padding:0 10px;height:32px">✕</button>
          </div>
          <form @submit.prevent="submitCreate" class="drawer-body">
            <div class="field">
              <label>Título</label>
              <input v-model="newTicket.title" class="input" required maxlength="255" placeholder="Resumo curto do problema" />
            </div>
            <div class="field">
              <label>Descrição</label>
              <textarea v-model="newTicket.description" class="input" rows="6" required
                placeholder="Descreve o problema com detalhe"></textarea>
            </div>
            <div class="row-2">
              <div class="field">
                <label>Prioridade</label>
                <select v-model="newTicket.priority" class="input">
                  <option value="low">Baixa</option>
                  <option value="medium">Média</option>
                  <option value="high">Alta</option>
                  <option value="critical">Crítica</option>
                </select>
              </div>
              <div class="field">
                <label>Categoria</label>
                <select v-model="newTicket.category_id" class="input">
                  <option :value="null">— Sem categoria —</option>
                  <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
                </select>
              </div>
            </div>
            <div v-if="createError" class="api-error">{{ createError }}</div>
            <div class="drawer-footer">
              <button type="button" class="btn btn-ghost" @click="showCreate = false">Cancelar</button>
              <button type="submit" class="btn btn-primary" :disabled="creating">
                <span v-if="creating" class="spinner" style="width:14px;height:14px;border-width:2px"></span>
                {{ creating ? 'A criar...' : 'Criar ticket' }}
              </button>
            </div>
          </form>
        </div>
      </div>

    </div>
  `,

  setup() {
    const router = VueRouter.useRouter();
    const { ref, reactive, computed, onMounted } = Vue;

    const loading = ref(true);
    const tickets = ref([]);
    const categories = ref([]);
    const total = ref(0);
    const page = ref(1);
    const pageSize = ref(20);

    const filters = reactive({
      search: '', status: '', priority: '', category_id: '',
    });

    const showCreate = ref(false);
    const creating = ref(false);
    const createError = ref('');
    const newTicket = reactive({
      title: '', description: '', priority: 'medium', category_id: null,
    });

    const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)));

    async function reload() {
      loading.value = true;
      try {
        const qs = new URLSearchParams({
          page: page.value, page_size: pageSize.value,
        });
        if (filters.search)      qs.append('search', filters.search);
        if (filters.status)      qs.append('status', filters.status);
        if (filters.priority)    qs.append('priority', filters.priority);
        if (filters.category_id) qs.append('category_id', filters.category_id);

        const data = await http.get(`/tickets?${qs.toString()}`);
        tickets.value = data.items;
        total.value = data.total;
      } catch (e) {
        window.hdToast(e.message || 'Erro ao carregar tickets', 'error');
      } finally {
        loading.value = false;
      }
    }

    async function loadCategories() {
      try {
        categories.value = await http.get('/categories');
      } catch (e) { /* silencioso */ }
    }

    function goPage(p) {
      if (p < 1 || p > totalPages.value) return;
      page.value = p;
      reload();
    }

    function open(id) {
      router.push({ name: 'ticket-detail', params: { id } });
    }

    function openCreate() {
      newTicket.title = '';
      newTicket.description = '';
      newTicket.priority = 'medium';
      newTicket.category_id = null;
      createError.value = '';
      showCreate.value = true;
    }

    async function submitCreate() {
      creating.value = true; createError.value = '';
      try {
        const payload = { ...newTicket };
        if (!payload.category_id) delete payload.category_id;
        const created = await http.post('/tickets', payload);
        window.hdToast(`Ticket #${created.id} criado`, 'success');
        showCreate.value = false;
        page.value = 1;
        await reload();
      } catch (e) {
        createError.value = e.message || 'Erro ao criar ticket';
      } finally {
        creating.value = false;
      }
    }

    // Debounce para a pesquisa
    let searchTimer = null;
    function debouncedSearch() {
      clearTimeout(searchTimer);
      searchTimer = setTimeout(() => { page.value = 1; reload(); }, 350);
    }

    // ── Helpers de visualização ───────────────────────────────────────────
    const statusMap = {
      open: 'Aberto', in_progress: 'Em curso',
      awaiting_reply: 'Aguarda resposta', resolved: 'Resolvido', closed: 'Fechado',
    };
    const priorityMap = {
      low: 'Baixa', medium: 'Média', high: 'Alta', critical: 'Crítica',
    };
    const statusLabel = s => statusMap[s] || s;
    const priorityLabel = p => priorityMap[p] || p;

    function formatDate(iso) {
      if (!iso) return '—';
      const d = new Date(iso);
      return d.toLocaleString('pt-PT', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
    }

    function slaTooltip(t) {
      if (!t.sla_deadline) return 'Sem SLA definido';
      const d = new Date(t.sla_deadline);
      const status = t.sla_status || 'ok';
      const label = { ok: 'Dentro do prazo', warning: 'Próximo do limite', breached: 'SLA violado', done: 'Resolvido' }[status];
      return `${label} — prazo: ${d.toLocaleString('pt-PT')}`;
    }

    onMounted(async () => {
      await Promise.all([loadCategories(), reload()]);
    });

    return {
      loading, tickets, categories, total, page, pageSize, totalPages,
      filters, showCreate, creating, createError, newTicket,
      reload, goPage, open, openCreate, submitCreate, debouncedSearch,
      statusLabel, priorityLabel, formatDate, slaTooltip,
    };
  },
};

// ── CSS ────────────────────────────────────────────────────────────────────
const _ticketsStyle = document.createElement('style');
_ticketsStyle.textContent = `
  .tickets-page { display:flex; flex-direction:column; gap:16px; }
  .toolbar { display:flex; justify-content:space-between; align-items:center; gap:16px; flex-wrap:wrap; }
  .filters { display:flex; gap:8px; flex-wrap:wrap; }

  .tickets-table { width:100%; border-collapse:collapse; font-size:13px; }
  .tickets-table th {
    text-align:left; padding:12px 16px; font-weight:500;
    color:var(--text-secondary); font-size:11px; text-transform:uppercase;
    letter-spacing:.06em; border-bottom:1px solid var(--border);
    background:var(--bg-elevated);
  }
  .tickets-table td { padding:14px 16px; border-bottom:1px solid var(--border); }
  .tickets-table tr.row { cursor:pointer; transition:background var(--transition); }
  .tickets-table tr.row:hover { background:var(--bg-hover); }
  .tickets-table tr:last-child td { border-bottom:none; }
  .title-cell { font-weight:500; color:var(--text-primary); max-width:340px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
  .mono { font-family:var(--font-mono); color:var(--text-secondary); font-size:12px; }
  .muted { color:var(--text-muted); font-size:12px; }

  .pagination {
    display:flex; justify-content:space-between; align-items:center;
    padding:14px 16px; border-top:1px solid var(--border);
  }
  .page-info { color:var(--text-muted); font-size:12px; }
  .page-controls { display:flex; align-items:center; gap:8px; }
  .page-num { font-size:12px; color:var(--text-secondary); padding:0 8px; }

  /* Drawer */
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
  .row-2 { display:grid; grid-template-columns:1fr 1fr; gap:16px; }

  .api-error {
    padding:10px 12px; border-radius:var(--radius-sm);
    background:#ff5c721a; border:1px solid #ff5c7250;
    color:var(--danger); font-size:12px;
  }

  @keyframes fadeIn { from{opacity:0;} to{opacity:1;} }
  @keyframes slideIn { from{transform:translateX(40px);opacity:0;} to{transform:none;opacity:1;} }
`;
document.head.appendChild(_ticketsStyle);
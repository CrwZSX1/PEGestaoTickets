/**
 * frontend/pages/TicketDetailPage.js
 * Página de detalhe de um ticket — informação completa, comentários, histórico
 * e ações condicionais por role.
 */

const TicketDetailPage = {
  name: 'TicketDetailPage',
  template: `
    <div class="detail-page">
      <div v-if="loading" class="loading-center"><span class="spinner"></span> A carregar...</div>

      <div v-else-if="!ticket" class="loading-center">Ticket não encontrado.</div>

      <div v-else class="detail-grid">

        <!-- ── Coluna principal ─────────────────────────────────────────── -->
        <div class="detail-main">
          <div class="card detail-header">
            <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
              <span class="mono" style="color:var(--text-muted)">#{{ ticket.id }}</span>
              <span class="badge" :class="'badge-' + ticket.status">{{ statusLabel(ticket.status) }}</span>
              <span class="badge" :class="'badge-' + ticket.priority">{{ priorityLabel(ticket.priority) }}</span>
              <span class="sla-pill" :class="'sla-pill-' + (ticket.sla_status || 'ok')">
                <span class="sla-dot" :class="'sla-' + (ticket.sla_status || 'ok')"></span>
                {{ slaLabel(ticket.sla_status) }}
              </span>
            </div>
            <h2 style="font-size:20px;font-weight:500;margin-top:12px;letter-spacing:-.3px">{{ ticket.title }}</h2>
            <p class="description">{{ ticket.description }}</p>
          </div>

          <!-- ── Comentários ────────────────────────────────────────────── -->
          <div class="card">
            <h3 class="section-title">Comentários ({{ ticket.comments.length }})</h3>

            <div v-if="ticket.comments.length === 0" class="muted" style="padding:8px 0">Sem comentários ainda.</div>

            <div v-for="c in ticket.comments" :key="c.id" class="comment" :class="{ 'internal': c.is_internal }">
              <div class="comment-head">
                <div class="comment-author">
                  <div class="user-avatar small">{{ initials(c.author.name) }}</div>
                  <span class="comment-name">{{ c.author.name }}</span>
                  <span v-if="c.is_internal" class="badge badge-internal">Nota interna</span>
                </div>
                <span class="muted" style="font-size:11px">{{ formatDate(c.created_at) }}</span>
              </div>
              <p class="comment-body">{{ c.body }}</p>
            </div>

            <!-- Formulário de novo comentário -->
            <div v-if="canComment" class="comment-form">
              <textarea v-model="newComment.body" class="input" rows="3"
                placeholder="Escreve uma resposta..."></textarea>
              <div class="comment-form-actions">
                <label v-if="isAdminOrTech" class="checkbox">
                  <input type="checkbox" v-model="newComment.is_internal" />
                  <span>Nota interna (só técnicos vêem)</span>
                </label>
                <button class="btn btn-primary" :disabled="!newComment.body.trim() || posting" @click="postComment">
                  {{ posting ? 'A enviar...' : 'Comentar' }}
                </button>
              </div>
            </div>
          </div>

          <!-- ── Histórico ──────────────────────────────────────────────── -->
          <div v-if="ticket.history.length" class="card">
            <h3 class="section-title">Histórico de alterações</h3>
            <ul class="history">
              <li v-for="h in ticket.history" :key="h.id">
                <span class="muted" style="font-size:11px">{{ formatDate(h.changed_at) }}</span>
                <strong>{{ h.changed_by?.name || 'Sistema' }}</strong>
                alterou <em>{{ h.field }}</em>
                de <code>{{ h.old_value || '—' }}</code>
                para <code>{{ h.new_value || '—' }}</code>
              </li>
            </ul>
          </div>
        </div>

        <!-- ── Coluna lateral (info + ações) ────────────────────────────── -->
        <aside class="detail-side">
          <div class="card">
            <h3 class="section-title">Informação</h3>
            <dl class="info-list">
              <dt>Criado por</dt><dd>{{ ticket.creator.name }}</dd>
              <dt>Atribuído a</dt><dd>{{ ticket.assignee?.name || '—' }}</dd>
              <dt>Categoria</dt><dd>{{ ticket.category?.name || '—' }}</dd>
              <dt>Fonte</dt><dd>{{ ticket.source === 'web' ? 'Web' : 'Email' }}</dd>
              <dt>Criado em</dt><dd>{{ formatDate(ticket.created_at) }}</dd>
              <dt>Prazo SLA</dt><dd>{{ formatDate(ticket.sla_deadline) }}</dd>
              <dt v-if="ticket.resolved_at">Resolvido em</dt>
              <dd v-if="ticket.resolved_at">{{ formatDate(ticket.resolved_at) }}</dd>
            </dl>
          </div>

          <!-- Ações para admin/tech -->
          <div v-if="isAdminOrTech" class="card">
            <h3 class="section-title">Ações</h3>

            <div class="field">
              <label>Estado</label>
              <select :value="ticket.status" @change="changeStatus($event.target.value)" class="input">
                <option v-for="opt in nextStates" :key="opt" :value="opt">{{ statusLabel(opt) }}</option>
              </select>
            </div>

            <div class="field" style="margin-top:12px">
              <label>Técnico</label>
              <select :value="ticket.assignee?.id || ''" @change="changeAssignee($event.target.value || null)" class="input">
                <option value="">— Não atribuído —</option>
                <option v-for="t in techs" :key="t.id" :value="t.id">{{ t.name }}</option>
              </select>
            </div>
          </div>

          <button class="btn btn-ghost" @click="back" style="justify-content:center">← Voltar à lista</button>
        </aside>

      </div>
    </div>
  `,

  props: ['id'],

  setup(props) {
    const router = VueRouter.useRouter();
    const route  = VueRouter.useRoute();
    const { ref, reactive, computed, onMounted } = Vue;

    const loading = ref(true);
    const ticket  = ref(null);
    const techs   = ref([]);
    const posting = ref(false);

    const newComment = reactive({ body: '', is_internal: false });

    const user = computed(() => authService.currentUser());
    const isAdminOrTech = computed(() => authService.isAdminOrTech());
    const canComment = computed(() => {
      if (!ticket.value) return false;
      // user só comenta se for criador e o ticket não estiver fechado
      if (!isAdminOrTech.value) {
        return user.value?.id === ticket.value.creator.id && ticket.value.status !== 'closed';
      }
      // admin/tech podem sempre comentar excepto em fechados (admin pode em fechado)
      if (ticket.value.status === 'closed') {
        return user.value?.role === 'admin';
      }
      return true;
    });

    // Próximas transições válidas (mesma tabela do backend)
    const VALID = {
      open: ['open', 'in_progress', 'awaiting_reply', 'resolved'],
      in_progress: ['in_progress', 'awaiting_reply', 'resolved', 'open'],
      awaiting_reply: ['awaiting_reply', 'in_progress', 'resolved', 'open'],
      resolved: ['resolved', 'closed', 'in_progress'],
      closed: ['closed', 'in_progress'],
    };
    const nextStates = computed(() => ticket.value ? VALID[ticket.value.status] : []);

    async function load() {
      loading.value = true;
      try {
        const id = props.id || route.params.id;
        ticket.value = await http.get(`/tickets/${id}`);
      } catch (e) {
        window.hdToast(e.message || 'Erro ao carregar ticket', 'error');
        ticket.value = null;
      } finally {
        loading.value = false;
      }
    }

    async function loadTechs() {
      if (!isAdminOrTech.value) return;
      try {
        techs.value = await http.get('/users/techs');
      } catch (_) { /* utilizador normal não acede */ }
    }

    async function changeStatus(status) {
      if (status === ticket.value.status) return;
      try {
        await http.put(`/tickets/${ticket.value.id}/status`, { status });
        window.hdToast('Estado atualizado', 'success');
        await load();
      } catch (e) {
        window.hdToast(e.message || 'Erro ao mudar estado', 'error');
      }
    }

    async function changeAssignee(assignee_id) {
      try {
        await http.put(`/tickets/${ticket.value.id}/assign`, {
          assignee_id: assignee_id ? Number(assignee_id) : null,
        });
        window.hdToast('Atribuição actualizada', 'success');
        await load();
      } catch (e) {
        window.hdToast(e.message || 'Erro ao atribuir', 'error');
      }
    }

    async function postComment() {
      if (!newComment.body.trim()) return;
      posting.value = true;
      try {
        await http.post(`/tickets/${ticket.value.id}/comments`, {
          body: newComment.body.trim(),
          is_internal: !!newComment.is_internal,
        });
        newComment.body = ''; newComment.is_internal = false;
        await load();
        window.hdToast('Comentário enviado', 'success');
      } catch (e) {
        window.hdToast(e.message || 'Erro ao comentar', 'error');
      } finally {
        posting.value = false;
      }
    }

    function back() { router.push({ name: 'ticket-list' }); }

    // Helpers
    const statusMap = {
      open: 'Aberto', in_progress: 'Em curso', awaiting_reply: 'Aguarda resposta',
      resolved: 'Resolvido', closed: 'Fechado',
    };
    const priorityMap = { low: 'Baixa', medium: 'Média', high: 'Alta', critical: 'Crítica' };
    const slaMap = { ok: 'SLA ok', warning: 'SLA em risco', breached: 'SLA violado', done: 'Resolvido' };
    const statusLabel = s => statusMap[s] || s;
    const priorityLabel = p => priorityMap[p] || p;
    const slaLabel = s => slaMap[s] || 'SLA';
    function formatDate(iso) {
      if (!iso) return '—';
      return new Date(iso).toLocaleString('pt-PT', { dateStyle: 'short', timeStyle: 'short' });
    }
    function initials(name) { return name.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase(); }

    onMounted(async () => {
      await Promise.all([load(), loadTechs()]);
    });

    Vue.watch(() => route.params.id, () => load());

    return {
      loading, ticket, techs, posting, newComment,
      user, isAdminOrTech, canComment, nextStates,
      changeStatus, changeAssignee, postComment, back,
      statusLabel, priorityLabel, slaLabel, formatDate, initials,
    };
  },
};

const _detailStyle = document.createElement('style');
_detailStyle.textContent = `
  .detail-page { display:flex; flex-direction:column; gap:16px; }
  .detail-grid { display:grid; grid-template-columns: 1fr 320px; gap:16px; }
  @media (max-width:900px) { .detail-grid { grid-template-columns: 1fr; } }

  .detail-main { display:flex; flex-direction:column; gap:16px; }
  .detail-side { display:flex; flex-direction:column; gap:16px; }
  .detail-header .description {
    margin-top:14px; padding:14px; background:var(--bg-elevated);
    border:1px solid var(--border); border-radius:var(--radius-sm);
    white-space:pre-wrap; line-height:1.6; font-size:13px;
  }

  .section-title {
    font-size:11px; text-transform:uppercase; letter-spacing:.06em;
    font-weight:500; color:var(--text-secondary); margin-bottom:14px;
  }

  .sla-pill {
    display:inline-flex; align-items:center; gap:6px;
    padding:2px 10px; border-radius:99px; font-size:11px; font-weight:500;
    border:1px solid;
  }
  .sla-pill-ok       { border-color:var(--success); color:var(--success); }
  .sla-pill-warning  { border-color:var(--warning); color:var(--warning); }
  .sla-pill-breached { border-color:var(--danger);  color:var(--danger); }
  .sla-pill-done     { border-color:var(--text-muted); color:var(--text-muted); }

  .comment {
    padding:14px 0; border-bottom:1px solid var(--border);
  }
  .comment:last-of-type { border-bottom:none; }
  .comment.internal { background:#ffb34708; border-radius:6px; padding:14px; border:1px dashed #ffb34740; margin-bottom:8px; }
  .comment-head { display:flex; justify-content:space-between; align-items:center; }
  .comment-author { display:flex; align-items:center; gap:8px; }
  .user-avatar.small { width:24px; height:24px; font-size:10px; }
  .comment-name { font-weight:500; font-size:13px; }
  .badge-internal { background:#ffb34720; color:var(--warning); }
  .comment-body { margin-top:8px; white-space:pre-wrap; line-height:1.6; font-size:13px; }

  .comment-form { margin-top:16px; padding-top:16px; border-top:1px solid var(--border); }
  .comment-form-actions { display:flex; justify-content:space-between; align-items:center; margin-top:10px; gap:12px; }
  .checkbox { display:flex; align-items:center; gap:6px; font-size:12px; color:var(--text-secondary); cursor:pointer; }
  .checkbox input { accent-color:var(--accent); }

  .info-list { display:grid; grid-template-columns: max-content 1fr; gap:8px 14px; font-size:13px; }
  .info-list dt { color:var(--text-muted); font-size:12px; }
  .info-list dd { color:var(--text-primary); }

  .history { list-style:none; display:flex; flex-direction:column; gap:10px; font-size:12px; color:var(--text-secondary); }
  .history li { padding:8px 12px; background:var(--bg-elevated); border-radius:var(--radius-sm); border:1px solid var(--border); }
  .history code { font-family:var(--font-mono); padding:1px 6px; background:var(--bg-base); border-radius:3px; color:var(--accent); }
  .history em { font-style:normal; color:var(--text-primary); }
`;
document.head.appendChild(_detailStyle);

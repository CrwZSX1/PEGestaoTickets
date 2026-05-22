/**
 * frontend/pages/AdminDashboardPage.js
 * Dashboard administrativo — cards, gráficos e exportação CSV.
 */

const AdminDashboardPage = {
  name: 'AdminDashboardPage',
  template: `
    <div class="dashboard">
      <div v-if="loading" class="loading-center"><span class="spinner"></span> A carregar dashboard...</div>

      <template v-else-if="data">
        <!-- ── Cards ──────────────────────────────────────────────────── -->
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon" style="color:var(--info);background:#5b9cf618">
              <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" style="width:20px;height:20px"><path d="M3 5h14M3 10h14M3 15h8" stroke-linecap="round"/></svg>
            </div>
            <div class="stat-body">
              <div class="stat-value">{{ data.cards.open_tickets }}</div>
              <div class="stat-label">Tickets abertos</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon" style="color:var(--success);background:#4cd98a18">
              <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" style="width:20px;height:20px"><path d="M4 10l4 4 8-8" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </div>
            <div class="stat-body">
              <div class="stat-value">{{ data.cards.resolved_last_30d }}</div>
              <div class="stat-label">Resolvidos (30d)</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon" style="color:var(--danger);background:#ff5c7218">
              <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" style="width:20px;height:20px"><circle cx="10" cy="10" r="8"/><path d="M10 6v4M10 14h.01" stroke-linecap="round"/></svg>
            </div>
            <div class="stat-body">
              <div class="stat-value">{{ data.cards.sla_breaches_last_30d }}</div>
              <div class="stat-label">Violações SLA (30d)</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon" style="color:var(--warning);background:#ffb34718">
              <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" style="width:20px;height:20px"><circle cx="10" cy="10" r="8"/><path d="M10 6v4l3 2" stroke-linecap="round"/></svg>
            </div>
            <div class="stat-body">
              <div class="stat-value">{{ data.cards.avg_resolution_hours ?? '—' }}<span style="font-size:13px;color:var(--text-muted)"> h</span></div>
              <div class="stat-label">Tempo médio resolução</div>
            </div>
          </div>
        </div>

        <!-- ── Gráficos ───────────────────────────────────────────────── -->
        <div class="charts-row">
          <div class="card">
            <h3 class="section-title">Tickets criados vs resolvidos (últimos 30 dias)</h3>
            <canvas ref="dailyCanvas" height="100"></canvas>
          </div>
          <div class="card">
            <h3 class="section-title">Distribuição por categoria</h3>
            <canvas ref="catCanvas" height="100"></canvas>
          </div>
        </div>

        <!-- ── Top técnicos ────────────────────────────────────────────── -->
        <div class="card" style="padding:0">
          <h3 class="section-title" style="padding:20px 24px 0">Top técnicos</h3>
          <table class="tickets-table" v-if="data.top_techs.length">
            <thead>
              <tr><th>Técnico</th><th>Resolvidos</th><th>Tempo médio</th><th>SLA cumprido</th></tr>
            </thead>
            <tbody>
              <tr v-for="t in data.top_techs" :key="t.user_id">
                <td class="title-cell">{{ t.name }}</td>
                <td>{{ t.resolved }}</td>
                <td>{{ t.avg_resolution_hours ?? '—' }} h</td>
                <td>
                  <span class="badge" :class="t.sla_compliance_pct >= 90 ? 'badge-resolved' : (t.sla_compliance_pct >= 70 ? 'badge-awaiting_reply' : 'badge-critical')">
                    {{ t.sla_compliance_pct ?? '—' }}%
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-else class="loading-center">Sem dados de técnicos no período.</div>
        </div>

        <!-- ── Exportação ──────────────────────────────────────────────── -->
        <div class="card export-card">
          <div>
            <h3 style="font-size:14px;font-weight:500">Relatório mensal CSV</h3>
            <p class="muted" style="font-size:12px;margin-top:4px">Exporta todos os tickets do mês escolhido.</p>
          </div>
          <div style="display:flex;gap:8px;align-items:center">
            <input type="month" v-model="exportMonth" class="input" style="width:170px;height:36px" />
            <button class="btn btn-primary" @click="downloadCsv">Descarregar CSV</button>
          </div>
        </div>
      </template>
    </div>
  `,

  setup() {
    const { ref, onMounted, nextTick, onBeforeUnmount } = Vue;
    const loading = ref(true);
    const data    = ref(null);
    const dailyCanvas = ref(null);
    const catCanvas   = ref(null);
    const exportMonth = ref(new Date().toISOString().slice(0, 7));  // YYYY-MM

    let dailyChart = null, catChart = null;

    async function load() {
      loading.value = true;
      try {
        data.value = await http.get('/reports/dashboard?days=30');
        await nextTick();
        renderCharts();
      } catch (e) {
        window.hdToast(e.message || 'Erro ao carregar dashboard', 'error');
      } finally {
        loading.value = false;
      }
    }

    function renderCharts() {
      if (!window.Chart) return;
      if (dailyChart) dailyChart.destroy();
      if (catChart)   catChart.destroy();

      const d = data.value;
      const labels = d.daily.map(x => x.date.slice(5)); // MM-DD
      dailyChart = new Chart(dailyCanvas.value, {
        type: 'line',
        data: {
          labels,
          datasets: [
            { label: 'Criados',   data: d.daily.map(x => x.created),   borderColor: '#5b9cf6', backgroundColor: '#5b9cf622', tension: .3, fill: true },
            { label: 'Resolvidos',data: d.daily.map(x => x.resolved), borderColor: '#4cd98a', backgroundColor: '#4cd98a22', tension: .3, fill: true },
          ],
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: { legend: { labels: { color: '#8b92a8' } } },
          scales: {
            x: { ticks: { color: '#555f7a' }, grid: { color: '#2a304555' } },
            y: { ticks: { color: '#555f7a', stepSize: 1 }, grid: { color: '#2a304555' }, beginAtZero: true },
          },
        },
      });

      const colors = ['#00d4aa', '#5b9cf6', '#ffb347', '#ff5c72', '#ff8c42', '#8b92a8'];
      catChart = new Chart(catCanvas.value, {
        type: 'doughnut',
        data: {
          labels: d.by_category.map(c => c.category),
          datasets: [{ data: d.by_category.map(c => c.count), backgroundColor: colors, borderColor: '#181c26', borderWidth: 2 }],
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: { legend: { position: 'right', labels: { color: '#8b92a8', font: { size: 11 } } } },
        },
      });
    }

    async function downloadCsv() {
      try {
        await http.download(`/reports/monthly?month=${exportMonth.value}`, `helpdesk-${exportMonth.value}.csv`);
        window.hdToast('CSV descarregado', 'success');
      } catch (e) {
        window.hdToast(e.message || 'Erro ao descarregar', 'error');
      }
    }

    onMounted(load);
    onBeforeUnmount(() => {
      if (dailyChart) dailyChart.destroy();
      if (catChart) catChart.destroy();
    });

    return { loading, data, dailyCanvas, catCanvas, exportMonth, downloadCsv };
  },
};

const _adminDashStyle = document.createElement('style');
_adminDashStyle.textContent = `
  .dashboard { display:flex; flex-direction:column; gap:16px; }
  .stats-grid {
    display:grid; grid-template-columns:repeat(auto-fill,minmax(200px,1fr)); gap:14px;
  }
  .stat-card {
    background:var(--bg-surface); border:1px solid var(--border);
    border-radius:var(--radius-lg); padding:18px;
    display:flex; align-items:center; gap:14px;
  }
  .stat-icon { width:42px; height:42px; border-radius:var(--radius-md); display:flex; align-items:center; justify-content:center; flex-shrink:0; }
  .stat-value { font-size:22px; font-weight:600; letter-spacing:-.5px; }
  .stat-label { font-size:11px; color:var(--text-muted); margin-top:2px; text-transform:uppercase; letter-spacing:.04em; }

  .charts-row { display:grid; grid-template-columns: 1.6fr 1fr; gap:16px; }
  @media (max-width:900px) { .charts-row { grid-template-columns: 1fr; } }

  .export-card {
    display:flex; justify-content:space-between; align-items:center; gap:16px; flex-wrap:wrap;
  }
`;
document.head.appendChild(_adminDashStyle);

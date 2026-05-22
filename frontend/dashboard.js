/**
 * frontend/pages/DashboardPage.js
 * Dashboard Admin (placeholder Fase 5 — dados reais na Fase 9)
 * Mostra cards de métricas e aviso de "em construção"
 */

const DashboardPage = {
  name: 'DashboardPage',
  template: `
    <div class="dashboard">

      <!-- Stats cards (placeholder) -->
      <div class="stats-grid">
        <div class="stat-card" v-for="s in stats" :key="s.label">
          <div class="stat-icon" :style="{ color: s.color, background: s.color + '18' }">
            <span v-html="s.icon"></span>
          </div>
          <div class="stat-body">
            <div class="stat-value">—</div>
            <div class="stat-label">{{ s.label }}</div>
          </div>
        </div>
      </div>

      <!-- Placeholder -->
      <div class="card" style="display:flex;align-items:center;justify-content:center;gap:16px;padding:60px;color:var(--text-muted)">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="width:32px;height:32px;opacity:.5">
          <path d="M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z" stroke-linejoin="round"/>
        </svg>
        <div>
          <div style="font-size:15px;color:var(--text-secondary);font-weight:500">Dashboard</div>
          <div style="font-size:13px;margin-top:4px">Gráficos e métricas disponíveis na Fase 9</div>
        </div>
      </div>
    </div>
  `,

  setup() {
    const stats = [
      { label: 'Tickets abertos',      color: 'var(--info)',    icon: '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" style="width:20px;height:20px"><path d="M3 5h14M3 10h14M3 15h8" stroke-linecap="round"/></svg>' },
      { label: 'Resolvidos este mês',  color: 'var(--success)', icon: '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" style="width:20px;height:20px"><path d="M4 10l4 4 8-8" stroke-linecap="round" stroke-linejoin="round"/></svg>' },
      { label: 'Violações de SLA',     color: 'var(--danger)',  icon: '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" style="width:20px;height:20px"><circle cx="10" cy="10" r="8"/><path d="M10 6v4M10 14h.01" stroke-linecap="round"/></svg>' },
      { label: 'Tempo médio resolução',color: 'var(--warning)', icon: '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" style="width:20px;height:20px"><circle cx="10" cy="10" r="8"/><path d="M10 6v4l3 2" stroke-linecap="round"/></svg>' },
    ];
    return { stats };
  },
};

const _dashStyle = document.createElement('style');
_dashStyle.textContent = `
  .dashboard { display: flex; flex-direction: column; gap: 24px; }
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 16px;
  }
  .stat-card {
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 20px;
    display: flex; align-items: center; gap: 16px;
    transition: border-color var(--transition);
  }
  .stat-card:hover { border-color: var(--border-strong); }
  .stat-icon {
    width: 44px; height: 44px; border-radius: var(--radius-md);
    display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  }
  .stat-value { font-size: 24px; font-weight: 600; letter-spacing: -.5px; }
  .stat-label { font-size: 12px; color: var(--text-muted); margin-top: 2px; }
`;
document.head.appendChild(_dashStyle);
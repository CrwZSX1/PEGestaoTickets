/**
 * frontend/pages/LoginPage.js
 * Página de login:
 *  - Validação de campos
 *  - Chama authService.login()
 *  - Armazena token em localStorage
 *  - Redireciona para /tickets ou para a rota original (query.redirect)
 */

const LoginPage = {
  name: 'LoginPage',
  template: `
    <div class="login-shell">
      <div class="login-card">

        <div class="login-header">
          <div class="login-logo">
            <span class="logo-mark">HD</span>
          </div>
          <h1 class="login-title">Helpdesk</h1>
          <p class="login-sub">Sistema de gestão de tickets</p>
        </div>

        <form class="login-form" @submit.prevent="submit" novalidate>
          <div class="field">
            <label for="email">Email</label>
            <input
              id="email"
              v-model.trim="form.email"
              type="email"
              class="input"
              :class="{ 'input-error': errors.email }"
              placeholder="utilizador@helpdesk.local"
              autocomplete="email"
              @input="errors.email = ''"
            />
            <span v-if="errors.email" class="field-error">{{ errors.email }}</span>
          </div>

          <div class="field">
            <label for="password">Password</label>
            <div class="input-wrap">
              <input
                id="password"
                v-model="form.password"
                :type="showPw ? 'text' : 'password'"
                class="input"
                :class="{ 'input-error': errors.password }"
                placeholder="••••••••"
                autocomplete="current-password"
                @input="errors.password = ''"
              />
              <button type="button" class="pw-toggle" @click="showPw = !showPw" :title="showPw ? 'Ocultar' : 'Mostrar'">
                <svg v-if="!showPw" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M2 10s3-6 8-6 8 6 8 6-3 6-8 6-8-6-8-6z" stroke-linejoin="round"/>
                  <circle cx="10" cy="10" r="2.5"/>
                </svg>
                <svg v-else viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M3 3l14 14M12.3 12.4A2.5 2.5 0 017.6 7.6M6.5 5.1C4.1 6.4 2 10 2 10s3 6 8 6c1.6 0 3-.5 4.2-1.3M9 4.1c.3 0 .7-.1 1-.1 5 0 8 6 8 6s-.9 1.7-2.5 3.2" stroke-linecap="round"/>
                </svg>
              </button>
            </div>
            <span v-if="errors.password" class="field-error">{{ errors.password }}</span>
          </div>

          <div v-if="apiError" class="api-error">
            <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" style="width:14px;height:14px;flex-shrink:0">
              <circle cx="10" cy="10" r="8"/>
              <path d="M10 6v4M10 14h.01" stroke-linecap="round"/>
            </svg>
            {{ apiError }}
          </div>

          <button type="submit" class="btn btn-primary login-submit" :disabled="loading">
            <span v-if="loading" class="spinner" style="width:16px;height:16px;border-width:2px"></span>
            <span>{{ loading ? 'A entrar...' : 'Entrar' }}</span>
          </button>
        </form>

        <div class="login-hint">
          <span>Dev:</span>
          <code @click="fillAdmin" title="Clicar para preencher">admin@helpdesk.local</code>
          <span>/</span>
          <code>admin123</code>
        </div>
      </div>

      <!-- Background decoration -->
      <div class="login-bg" aria-hidden="true">
        <div class="bg-orb bg-orb-1"></div>
        <div class="bg-orb bg-orb-2"></div>
        <div class="bg-grid"></div>
      </div>
    </div>
  `,

  setup() {
    const router = VueRouter.useRouter();
    const route  = VueRouter.useRoute();
    const { ref, reactive } = Vue;

    const form = reactive({ email: '', password: '' });
    const errors = reactive({ email: '', password: '' });
    const apiError = ref('');
    const loading  = ref(false);
    const showPw   = ref(false);

    function validate() {
      let ok = true;
      if (!form.email) { errors.email = 'Email obrigatório'; ok = false; }
      else if (!/\S+@\S+\.\S+/.test(form.email)) { errors.email = 'Email inválido'; ok = false; }
      if (!form.password) { errors.password = 'Password obrigatória'; ok = false; }
      return ok;
    }

    async function submit() {
      apiError.value = '';
      if (!validate()) return;
      loading.value = true;
      try {
        await authService.login(form.email, form.password);
        const redirect = route.query.redirect || '/tickets';
        router.push(redirect);
      } catch (err) {
        apiError.value = err.message || 'Erro ao fazer login';
      } finally {
        loading.value = false;
      }
    }

    function fillAdmin() {
      form.email    = 'admin@helpdesk.local';
      form.password = 'admin123';
    }

    return { form, errors, apiError, loading, showPw, submit, fillAdmin };
  },
};

// CSS da página de login (injectado uma vez)
const _loginStyle = document.createElement('style');
_loginStyle.textContent = `
  .login-shell {
    min-height: 100vh;
    display: flex; align-items: center; justify-content: center;
    padding: 24px;
    position: relative; overflow: hidden;
  }

  .login-bg { position: fixed; inset: 0; pointer-events: none; z-index: 0; }
  .bg-orb {
    position: absolute; border-radius: 50%;
    filter: blur(80px); opacity: .18;
  }
  .bg-orb-1 { width: 500px; height: 500px; background: var(--accent); top: -120px; left: -100px; }
  .bg-orb-2 { width: 400px; height: 400px; background: #5b9cf6;   bottom: -80px; right: -60px; }
  .bg-grid {
    position: absolute; inset: 0;
    background-image: linear-gradient(var(--border) 1px, transparent 1px),
                      linear-gradient(90deg, var(--border) 1px, transparent 1px);
    background-size: 40px 40px;
    opacity: .35;
  }

  .login-card {
    position: relative; z-index: 1;
    width: 100%; max-width: 400px;
    background: var(--bg-surface);
    border: 1px solid var(--border-strong);
    border-radius: var(--radius-lg);
    padding: 40px 36px 32px;
    box-shadow: 0 24px 64px #00000055;
    animation: cardIn 320ms cubic-bezier(.22,.68,0,1.2);
  }
  @keyframes cardIn { from { opacity: 0; transform: translateY(20px) scale(.97); } to { opacity: 1; transform: none; } }

  .login-header { text-align: center; margin-bottom: 32px; }
  .login-logo {
    width: 52px; height: 52px; border-radius: 14px;
    background: var(--accent-dim); border: 1px solid var(--accent)40;
    display: flex; align-items: center; justify-content: center;
    margin: 0 auto 16px;
  }
  .login-logo .logo-mark { font-size: 18px; font-weight: 600; color: var(--accent); letter-spacing: -.5px; }
  .login-title { font-size: 22px; font-weight: 600; letter-spacing: -.5px; }
  .login-sub { font-size: 13px; color: var(--text-muted); margin-top: 4px; }

  .login-form { display: flex; flex-direction: column; gap: 18px; }

  .input-wrap { position: relative; }
  .input-wrap .input { padding-right: 40px; }
  .pw-toggle {
    position: absolute; right: 10px; top: 50%; transform: translateY(-50%);
    background: none; border: none; cursor: pointer; color: var(--text-muted);
    padding: 4px; display: flex;
  }
  .pw-toggle svg { width: 16px; height: 16px; }
  .pw-toggle:hover { color: var(--text-secondary); }

  .input-error { border-color: var(--danger) !important; }
  .field-error { font-size: 11px; color: var(--danger); }

  .api-error {
    display: flex; align-items: center; gap: 8px;
    padding: 10px 12px; border-radius: var(--radius-sm);
    background: var(--danger)12; border: 1px solid var(--danger)30;
    color: var(--danger); font-size: 12px;
  }

  .login-submit { width: 100%; justify-content: center; height: 42px; font-size: 14px; margin-top: 4px; }

  .login-hint {
    margin-top: 20px; text-align: center;
    font-size: 11px; color: var(--text-muted);
    display: flex; align-items: center; justify-content: center; gap: 6px;
  }
  .login-hint code {
    background: var(--bg-elevated); padding: 2px 6px; border-radius: 4px;
    font-family: var(--font-mono); font-size: 11px; cursor: pointer;
    color: var(--text-secondary);
  }
  .login-hint code:hover { color: var(--accent); }
`;
document.head.appendChild(_loginStyle);
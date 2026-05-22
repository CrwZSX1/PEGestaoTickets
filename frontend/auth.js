/**
 * frontend/services/auth.js
 * Serviço de autenticação:
 *  - login / logout
 *  - estado reactivo do utilizador actual
 *  - helpers de role
 */

const authService = (() => {
  // Estado reactivo partilhado (Vue.reactive exposto globalmente após Vue carregar)
  // Inicializado em app.js após Vue estar disponível
  let _state = null;

  function getState() {
    if (!_state) {
      _state = Vue.reactive({
        user: _loadUser(),
        token: localStorage.getItem('hd_token') || null,
      });
    }
    return _state;
  }

  function _loadUser() {
    try {
      const raw = localStorage.getItem('hd_user');
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  }

  async function login(email, password) {
    // FastAPI OAuth2 espera form-data no endpoint /auth/login
    const formData = new URLSearchParams({ username: email, password });

    const res = await fetch('http://localhost:8000/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData,
    });

    const data = await res.json();

    if (!res.ok) {
      throw { message: data?.detail || 'Credenciais inválidas' };
    }

    const { access_token, user } = data;

    localStorage.setItem('hd_token', access_token);
    localStorage.setItem('hd_user', JSON.stringify(user));

    const state = getState();
    state.token = access_token;
    state.user  = user;

    return user;
  }

  function logout() {
    localStorage.removeItem('hd_token');
    localStorage.removeItem('hd_user');
    const state = getState();
    state.token = null;
    state.user  = null;
  }

  function isLoggedIn() {
    return !!getState().token;
  }

  function currentUser() {
    return getState().user;
  }

  function hasRole(...roles) {
    const user = currentUser();
    return user ? roles.includes(user.role) : false;
  }

  const isAdmin      = () => hasRole('admin');
  const isTech       = () => hasRole('tech');
  const isAdminOrTech= () => hasRole('admin', 'tech');

  // Escutar evento de 401 do http.js
  window.addEventListener('hd:unauthorized', logout);

  return { getState, login, logout, isLoggedIn, currentUser, hasRole, isAdmin, isTech, isAdminOrTech };
})();
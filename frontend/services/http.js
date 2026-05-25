/**
 * frontend/services/http.js
 * Wrapper sobre fetch com:
 *  - Injecção automática do token JWT
 *  - Tratamento de 401 (redireciona para login)
 *  - JSON parse automático
 *  - Erros estruturados
 */

const API_BASE = 'http://localhost:8000';

const http = (() => {
  async function request(method, path, body = null, options = {}) {
    const token = localStorage.getItem('hd_token');

    const headers = {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      ...options.headers,
    };

    const config = {
      method,
      headers,
      ...(body ? { body: JSON.stringify(body) } : {}),
    };

    let res;
    try {
      res = await fetch(`${API_BASE}${path}`, config);
    } catch (err) {
      throw { message: 'Sem ligação ao servidor. Verifica se o backend está a correr.' };
    }

    // Token expirado ou inválido → limpar sessão e redirecionar
    if (res.status === 401) {
      localStorage.removeItem('hd_token');
      localStorage.removeItem('hd_user');
      // O router guard vai apanhar a ausência de token
      window.dispatchEvent(new CustomEvent('hd:unauthorized'));
      throw { message: 'Sessão expirada. Por favor faz login novamente.' };
    }

    // Tentar parsear JSON
    let data;
    const contentType = res.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
      data = await res.json();
    } else {
      data = await res.text();
    }

    if (!res.ok) {
      // FastAPI devolve { detail: "..." } nos erros
      const message = data?.detail
        || (typeof data === 'string' ? data : `Erro ${res.status}`);
      throw { status: res.status, message };
    }

    return data;
  }

  return {
    get:    (path, opts)        => request('GET',    path, null, opts),
    post:   (path, body, opts)  => request('POST',   path, body, opts),
    put:    (path, body, opts)  => request('PUT',    path, body, opts),
    patch:  (path, body, opts)  => request('PATCH',  path, body, opts),
    delete: (path, opts)        => request('DELETE', path, null, opts),

    // Download de ficheiros (ex: CSV de relatórios)
    async download(path, filename) {
      const token = localStorage.getItem('hd_token');
      const res = await fetch(`${API_BASE}${path}`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {},
      });
      if (!res.ok) throw { message: `Erro ${res.status} ao descarregar ficheiro` };
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = filename; a.click();
      URL.revokeObjectURL(url);
    },
  };
})();
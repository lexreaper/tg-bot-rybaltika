/* Shared by the public Mini App and the staff-only loyalty editor. */
(() => {
  'use strict';
  const config = window.APP_CONFIG || {};
  const base = (config.apiBaseUrl || '').replace(/\/$/, '');
  const escape = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  class ApiError extends Error {
    constructor(message, status) { super(message); this.name = 'ApiError'; this.status = status; }
  }
  function imageUrl(value) {
    if (!value) return '';
    try {
      const url = new URL(value, base ? `${base}/` : location.origin);
      return ['https:', 'http:'].includes(url.protocol) ? url.href : '';
    } catch { return ''; }
  }
  async function request(path, signal, options = {}) {
    const local = new AbortController();
    let timeout = false;
    const abort = () => local.abort();
    signal?.addEventListener('abort', abort, {once:true});
    if (signal?.aborted) local.abort();
    const timer = setTimeout(() => { timeout = true; local.abort(); }, config.requestTimeoutMs || 10000);
    try {
      const response = await fetch(`${base}${path}`, {
        signal:local.signal, cache:'no-store', credentials:'omit',
        method:options.method || 'GET',
        headers:{Accept:'application/json', ...(options.body ? {'Content-Type':'application/json'} : {}), ...options.headers},
        ...(options.body ? {body:JSON.stringify(options.body)} : {}),
      });
      if (!response.ok) {
        const messages = {401:'Неверный ключ доступа. Войдите снова.',403:'Недостаточно прав для изменения страницы.',404:'Этой страницы больше нет.',409:'Кто-то уже изменил страницу. Загрузите актуальную версию перед сохранением.',422:'Проверьте заполнение полей: сервер отклонил данные.'};
        throw new ApiError(messages[response.status] || 'Сервер временно недоступен. Попробуйте позже.', response.status);
      }
      if(response.status === 204) return null;
      try { return await response.json(); }
      catch { throw new ApiError('Сервер вернул некорректный ответ. Попробуйте позже.'); }
    } catch (error) {
      if (timeout) throw new ApiError('Сервер отвечает слишком долго. Попробуйте ещё раз.');
      if (error.name === 'AbortError' || error instanceof ApiError) throw error;
      throw new ApiError('Не удалось получить данные. Проверьте соединение и попробуйте ещё раз.');
    } finally { clearTimeout(timer); signal?.removeEventListener('abort', abort); }
  }
  window.RybaltikaAPI = {escape, ApiError, request, imageUrl};
})();

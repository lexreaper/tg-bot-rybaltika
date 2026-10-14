(() => {
  'use strict';
  const root = document.querySelector('#app');
  const config = window.APP_CONFIG || {};
  const base = (config.apiBaseUrl || '').replace(/\/$/, '');
  const tg = window.Telegram?.WebApp;
  let controller, generation = 0, parentCategory = null;
  const queries = new Map(), scrolls = new Map();
  let currentHash = location.hash || '#/';
  const escape = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  const money = value => new Intl.NumberFormat('ru-RU', {style:'currency',currency:'RUB',maximumFractionDigits:2}).format(Number(value));
  const countLabel = n => `${n} ${n % 10 === 1 && n % 100 !== 11 ? 'блюдо' : n % 10 >= 2 && n % 10 <= 4 && !(n % 100 >= 12 && n % 100 <= 14) ? 'блюда' : 'блюд'}`;
  function imageUrl(value) {
    if (!value) return '';
    try { const url = new URL(value, base ? `${base}/` : location.origin); return ['https:', 'http:'].includes(url.protocol) ? url.href : ''; } catch { return ''; }
  }
  const placeholder = '<div class="no-photo-label"><span aria-hidden="true">≈</span>Фото скоро появится</div>';
  function photo(item, lazy = true) {
    const url = imageUrl(item.image_url);
    return url ? `<img src="${escape(url)}" alt="${escape(item.name)}" ${lazy ? 'loading="lazy"' : ''}>` : placeholder;
  }
  function attachImageFallbacks() {
    root.querySelectorAll('img').forEach(img => {
      const fallback = () => {
        if (img.closest('.category')) { img.closest('.category').classList.add('no-photo'); img.remove(); }
        else img.parentElement.innerHTML = placeholder;
      };
      img.addEventListener('error', fallback, {once:true});
      if (img.complete && !img.naturalWidth) fallback();
    });
  }
  class ApiError extends Error { constructor(message, status) { super(message); this.status = status; } }
  async function request(path, signal) {
    const local = new AbortController();
    let timeout = false;
    const abort = () => local.abort();
    signal?.addEventListener('abort', abort, {once:true});
    if (signal?.aborted) local.abort();
    const timer = setTimeout(() => { timeout = true; local.abort(); }, config.requestTimeoutMs || 10000);
    try {
      const response = await fetch(`${base}${path}`, {signal:local.signal,headers:{Accept:'application/json'},cache:'no-store'});
      if (!response.ok) throw new ApiError(response.status === 404 ? 'Этой страницы меню больше нет.' : 'Сервер временно недоступен.', response.status);
      return await response.json();
    } catch (error) {
      if (timeout) throw new ApiError('Сервер отвечает слишком долго. Попробуйте ещё раз.');
      if (error.name === 'AbortError' || error instanceof ApiError) throw error;
      throw new ApiError('Не удалось получить меню. Проверьте соединение и попробуйте ещё раз.');
    } finally { clearTimeout(timer); signal?.removeEventListener('abort', abort); }
  }
  function validateCategories(data) {
    if (!Array.isArray(data) || data.some(c => !Number.isInteger(c.id) || c.id < 1 || typeof c.name !== 'string' || !Number.isInteger(c.dish_count) || c.dish_count < 0)) throw new ApiError('Сервер вернул некорректные категории.');
    return data;
  }
  function validateDish(d) {
    if (!d || !Number.isInteger(d.id) || d.id < 1 || !Number.isInteger(d.category_id) || d.category_id < 1 || typeof d.name !== 'string' || !['string','number'].includes(typeof d.price) || String(d.price).trim() === '' || !Number.isFinite(Number(d.price)) || Number(d.price) < 0 || !(d.description === null || typeof d.description === 'string') || !(d.image_url === null || typeof d.image_url === 'string')) throw new ApiError('Сервер вернул некорректные данные блюда.');
    return d;
  }
  function loading() {
    root.setAttribute('aria-busy','true');
    root.innerHTML = '<div role="status"><span class="sr-only">Загружаем меню</span><div class="loading-title"></div><div class="category-grid"><div class="skeleton"></div><div class="skeleton"></div><div class="skeleton"></div></div></div>';
  }
  function categoriesPage(categories) {
    root.innerHTML = `<section class="intro"><div class="eyebrow">Просто. Свежо. Со вкусом.</div><h1>Хороший вкус<br>начинается здесь.</h1><p>Любимая рыба, свежие продукты и немного вдохновения. Выберите что-то своё.</p></section><div class="section-heading"><h2>Наше меню</h2><span class="count">${categories.length} разделов</span></div><div class="category-grid">${categories.map((c,i) => `<a class="category ${imageUrl(c.image_url) ? '' : 'no-photo'}" href="#/category/${c.id}">${imageUrl(c.image_url) ? photo(c) : `<span class="category-symbol" aria-hidden="true">${['≈','✳','◡','◌','∿'][i%5]}</span>`}<div class="category-info"><div><h3>${escape(c.name)}</h3><small>${countLabel(c.dish_count)}</small></div><span class="round-arrow" aria-hidden="true">↗</span></div></a>`).join('')}</div>${categories.length ? '' : '<div class="state"><h2>Меню скоро появится</h2><p>Мы ещё заполняем разделы. Загляните чуть позже.</p></div>'}`;
  }
  function dishCard(d) {
    return `<a class="dish" href="#/dish/${d.id}"><div class="dish-photo">${photo(d)}</div><div class="dish-body"><h2>${escape(d.name)}</h2><p class="dish-description">${escape(d.description || 'Состав уточняйте у официанта.')}</p><div class="dish-bottom"><strong>${money(d.price)}</strong><span aria-hidden="true">↗</span></div></div></a>`;
  }
  function listPage(categories, id, dishes) {
    const category = categories.find(c => c.id === id);
    if (!category) throw new ApiError('Категория не найдена.',404);
    parentCategory = id;
    root.innerHTML = `<a class="back" href="#/">← Все категории</a><section class="intro"><div class="eyebrow">Из нашего меню</div><h1>${escape(category.name)}</h1><p>Выберите блюдо, чтобы узнать состав и цену.</p></section><nav class="category-nav" aria-label="Категории">${categories.map(c => `<a class="chip ${c.id===id?'active':''}" ${c.id===id?'aria-current="page"':''} href="#/category/${c.id}">${escape(c.name)}</a>`).join('')}</nav><label class="search"><span aria-hidden="true">⌕</span><span class="sr-only">Найти блюдо в категории</span><input type="search" placeholder="Найти блюдо в категории" autocomplete="off" value="${escape(queries.get(id)||'')}"></label><div class="section-heading"><h2>Блюда</h2><span id="result-count" class="count" role="status"></span></div><div id="dishes" class="dish-grid"></div>`;
    const input = root.querySelector('input');
    const render = () => {
      queries.set(id,input.value);
      const q=input.value.trim().toLocaleLowerCase('ru');
      const filtered=dishes.filter(d => `${d.name} ${d.description||''}`.toLocaleLowerCase('ru').includes(q));
      root.querySelector('#result-count').textContent=countLabel(filtered.length);
      root.querySelector('#dishes').innerHTML=filtered.length ? filtered.map(dishCard).join('') : `<div class="state"><h2>${q?'Ничего не нашлось':'Пока нет блюд'}</h2><p>${q?'Попробуйте другое название или ингредиент.':'Блюда этой категории временно недоступны. Выберите другой раздел.'}</p></div>`;
      attachImageFallbacks();
    };
    input.addEventListener('input',render);render();
  }
  function detailPage(d) {
    parentCategory=d.category_id;
    root.innerHTML=`<a class="back" href="#/category/${d.category_id}">← К блюдам категории</a><article class="detail"><div class="detail-photo">${photo(d,false)}</div><div class="detail-copy"><div class="eyebrow">Из нашего меню</div><h1>${escape(d.name)}</h1><p class="price">${money(d.price)}</p><section class="ingredients"><h2>Состав</h2><p>${escape(d.description || 'Состав пока не указан. Уточните его у официанта.')}</p><p class="note">Если у вас есть пищевая аллергия, пожалуйста, уточните состав у официанта.</p></section><a class="primary" href="#/category/${d.category_id}">← Вернуться к блюдам</a></div></article>`;
  }
  function back() { location.hash = location.hash.startsWith('#/dish/') && parentCategory ? `#/category/${parentCategory}` : '#/'; }
  function setupTelegram() {
    if (!tg) return;
    const theme = () => {
      document.documentElement.dataset.theme = tg.colorScheme || 'light';
      const dark = tg.colorScheme === 'dark';
      if (tg.isVersionAtLeast?.('6.1')) { tg.setHeaderColor(dark?'#1c221e':'#f5f2eb'); tg.setBackgroundColor(dark?'#1c221e':'#f5f2eb'); }
    };
    const safeArea = () => {
      for (const side of ['top','bottom']) document.documentElement.style.setProperty(`--safe-${side}`, `${(tg.safeAreaInset?.[side]||0)+(tg.contentSafeAreaInset?.[side]||0)}px`);
    };
    tg.ready(); tg.expand(); theme(); safeArea();
    tg.onEvent?.('themeChanged',theme);
    tg.onEvent?.('safeAreaChanged',safeArea); tg.onEvent?.('contentSafeAreaChanged',safeArea);
    if(tg.isVersionAtLeast?.('6.1')) tg.BackButton?.onClick(back);
  }
  async function route() {
    const ticket=++generation;
    controller?.abort();controller=new AbortController();
    const signal=controller.signal;
    const hash=location.hash||'#/';
    if(hash!==currentHash) { scrolls.set(currentHash,window.scrollY); currentHash=hash; }
    let match;
    if(tg?.isVersionAtLeast?.('6.1')) hash==='#/' ? tg.BackButton?.hide() : tg.BackButton?.show();
    loading();
    try {
      if(hash==='#/' || hash==='#') {
        const categories=validateCategories(await request('/menu/categories',signal));
        if(ticket!==generation)return;
        categoriesPage(categories);
      }
      else if((match=hash.match(/^#\/category\/([1-9]\d*)$/))) {
        const id=Number(match[1]);
        const [categories,dishes]=await Promise.all([request('/menu/categories',signal),request(`/menu?category_id=${id}`,signal)]);
        if(!Array.isArray(dishes)) throw new ApiError('Сервер вернул некорректный список блюд.');
        if(ticket!==generation)return;
        listPage(validateCategories(categories),id,dishes.map(validateDish));
      } else if((match=hash.match(/^#\/dish\/([1-9]\d*)$/))) {
        const dish=validateDish(await request(`/menu/dishes/${match[1]}`,signal));
        if(ticket!==generation)return;
        detailPage(dish);
      }
      else throw new ApiError('Такой страницы меню нет.',404);
      if(ticket!==generation)return;
      attachImageFallbacks();
      document.title=`${root.querySelector('h1')?.innerText.replace(/\s+/g,' ')||'Меню'} · Рыбалтика`;
      root.focus({preventScroll:true});
      window.scrollTo(0,scrolls.get(hash)||0);
    } catch(error) {
      if(error.name==='AbortError' || ticket!==generation)return;
      const missing=error.status===404;
      root.innerHTML=`<section class="state" role="alert"><div class="state-icon" aria-hidden="true">${missing?'∅':'≈'}</div><h1>${missing?'Не нашли в меню':'Не удалось загрузить меню'}</h1><p>${escape(error.message)}</p>${missing?'<a class="primary" href="#/">К категориям</a>':'<button class="primary" id="retry">Попробовать снова</button>'}<p><a class="back" href="#/">← Все категории</a></p></section>`;
      root.querySelector('#retry')?.addEventListener('click',route);
    } finally { if(ticket===generation)root.setAttribute('aria-busy','false'); }
  }
  setupTelegram();
  window.addEventListener('hashchange',route);
  request('/app-config').then(data=>{document.querySelector('#demo').hidden=!data.demo_mode;}).catch(()=>{});
  route();
})();

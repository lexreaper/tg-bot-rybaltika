(() => {
  'use strict';
  const root = document.querySelector('#editor');
  const {request,escape,ApiError}=window.RybaltikaAPI;
  const {paragraphs}=window.RybaltikaContent;
  let key='', version=0, dirty=false, saving=false;
  const headers=()=>({'X-Admin-Token':key});
  function validate(page) {
    if(!page || !Number.isInteger(page.version) || page.version<0 || typeof page.title!=='string' || typeof page.body!=='string' || typeof page.summary!=='string' || typeof page.is_published!=='boolean') throw new ApiError('Сервер вернул некорректную страницу редактора.');
    return page;
  }
  function login(message='') {
    key='';dirty=false;
    root.innerHTML=`<section class="editor-panel login-panel"><div class="eyebrow">Для сотрудников</div><h1>Редактор лояльности</h1><p>Введите ключ доступа, чтобы изменить информацию о программе.</p><form id="login"><label class="editor-field"><span>Ключ доступа</span><input type="password" name="token" required minlength="24" autocomplete="off" spellcheck="false"></label><button class="primary" type="submit">Войти в редактор</button><p class="field-help">Ключ хранится только в памяти этой страницы.</p><p class="editor-status" role="alert">${escape(message)}</p></form></section>`;
    root.querySelector('form').addEventListener('submit',async event=>{
      event.preventDefault();
      const form=event.currentTarget;
      key=form.elements.token.value.trim();
      const button=form.querySelector('button');button.disabled=true;
      try { render(validate(await request('/admin/loyalty',null,{headers:headers()}))); }
      catch(error) {
        const message=error.status===503 ? 'Редактор недоступен. Администратору нужно настроить CONTENT_ADMIN_TOKEN на сервере и проверить соединение с базой.' : error.message;
        login(message);
      }
    });
  }
  function render(page) {
    version=page.version;dirty=false;
    root.innerHTML=`<section class="editor-heading"><div><div class="eyebrow">Контент / Лояльность</div><h1>Информация для гостей</h1><p>Текст страницы программы лояльности.</p></div><button type="button" class="secondary" id="logout">Выйти</button></section><div class="editor-layout"><form id="loyalty-form" class="editor-panel"><h2>Содержимое страницы</h2><label class="editor-field"><span>Заголовок <small>до 120 символов</small></span><input name="title" required maxlength="120" value="${escape(page.title)}"></label><label class="editor-field"><span>Короткое описание <small>до 300 символов</small></span><textarea name="summary" maxlength="300" rows="3">${escape(page.summary)}</textarea></label><label class="editor-field"><span>Основной текст <small>до 10 000 символов</small></span><textarea name="body" required maxlength="10000" rows="10">${escape(page.body)}</textarea><p class="field-help">Пишите обычным текстом. Пустая строка начинает новый абзац.</p></label><label class="publish-control"><input type="checkbox" name="is_published" ${page.is_published?'checked':''}><span>Показывать посетителям<small>При выключении страница скрывается, но текст сохраняется.</small></span></label><div class="editor-actions"><button type="submit" class="primary" id="save">Сохранить изменения</button><button type="button" class="secondary" id="reload">Загрузить актуальную версию</button></div><p class="editor-status" id="save-status" role="status" aria-live="polite"></p><p class="version-note">Версия ${page.version}. После сохранения обновите раздел «Лояльность» в приложении.</p></form><aside class="editor-panel editor-preview" aria-label="Предпросмотр"><h2>Предпросмотр страницы</h2><div id="preview"></div><p class="admin-preview-note">Предпросмотр обновляется при вводе. Посетители увидят изменения только после сохранения.</p></aside></div>`;
    const form=root.querySelector('form');
    const preview=()=>{
      const fields=form.elements;
      root.querySelector('#preview').innerHTML=`<span class="status-tag preview-state">${fields.is_published.checked?'Опубликовано после сохранения':'Скрыто после сохранения'}</span><h3>${escape(fields.title.value || 'Заголовок страницы')}</h3><p class="preview-summary">${escape(fields.summary.value)}</p><div class="content-text preview-body">${paragraphs(fields.body.value || 'Здесь появится текст страницы.')}</div>`;
    };
    form.addEventListener('input',()=>{dirty=true;root.querySelector('#save-status').textContent='Есть несохранённые изменения.';preview();});
    preview();
    root.querySelector('#logout').addEventListener('click',()=>{
      if(dirty && !confirm('Выйти без сохранения изменений?')) return;
      login();
    });
    root.querySelector('#reload').addEventListener('click',async()=>{
      if(dirty && !confirm('Заменить несохранённый текст актуальной версией с сервера?')) return;
      try { render(validate(await request('/admin/loyalty',null,{headers:headers()}))); }
      catch(error) { showError(error); }
    });
    form.addEventListener('submit',async event=>{
      event.preventDefault();if(saving)return;
      const fields=form.elements;
      const payload={title:fields.title.value.trim(),summary:fields.summary.value.trim(),body:fields.body.value.trim(),is_published:fields.is_published.checked,expected_version:version};
      if(!payload.title || !payload.body) {root.querySelector('#save-status').textContent='Заполните заголовок и основной текст.';return;}
      saving=true;
      root.querySelector('#save').disabled=true;root.querySelector('#reload').disabled=true;root.querySelector('#logout').disabled=true;
      for(const name of ['title','summary','body','is_published'])fields[name].disabled=true;
      root.querySelector('#save-status').textContent='Сохраняем…';
      try {
        const saved=validate(await request('/admin/loyalty',null,{method:'PUT',headers:headers(),body:payload}));
        render(saved);
        root.querySelector('#save-status').textContent=saved.is_published?'Сохранено. Изменения опубликованы.':'Сохранено. Страница скрыта от посетителей.';
      } catch(error) {showError(error);}
      finally {
        saving=false;
        root.querySelectorAll('button,input,textarea').forEach(field=>{field.disabled=false;});
      }
    });
  }
  function showError(error) {
    const message=error.status===401 ? 'Доступ истёк или ключ изменён. Скопируйте несохранённый текст, затем выйдите и войдите с актуальным ключом.' : error.message;
    root.querySelector('#save-status').textContent=message;
  }
  window.addEventListener('beforeunload',event=>{if(dirty){event.preventDefault();event.returnValue='';}});
  login();
})();

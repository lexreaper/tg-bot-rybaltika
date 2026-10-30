/* Sprint 2 public pages. Content is always supplied by REST, never by these views. */
(() => {
  'use strict';
  const {escape, ApiError, imageUrl} = window.RybaltikaAPI;
  const text = value => typeof value === 'string';
  const optionalText = value => value == null || text(value);
  function validDate(value) {
    if(!text(value) || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
    const parsed = new Date(`${value}T12:00:00Z`);
    return Number.isFinite(parsed.getTime()) && parsed.toISOString().slice(0,10) === value;
  }
  function validateEvents(data) {
    if(!Array.isArray(data) || data.some(e => !e || !Number.isInteger(e.id) || e.id<1 || !text(e.title) || !e.title.trim() || !optionalText(e.description) || !validDate(e.date) || !optionalText(e.image_url))) throw new ApiError('Сервер вернул некорректные данные афиши.');
    return data;
  }
  function validateVacancies(data) {
    if(!Array.isArray(data) || data.some(v => !v || !Number.isInteger(v.id) || v.id<1 || !text(v.position) || !v.position.trim() || !optionalText(v.description) || !optionalText(v.salary))) throw new ApiError('Сервер вернул некорректные данные вакансий.');
    return data;
  }
  function validateLoyalty(data) {
    if(data === null) return data;
    if(!data || !text(data.title) || !data.title.trim() || !optionalText(data.summary) || !text(data.body) || !data.body.trim()) throw new ApiError('Сервер вернул некорректное содержимое страницы.');
    return data;
  }
  function paragraphs(value) {
    return String(value || '').trim().split(/\n\s*\n/).filter(Boolean).map(p=>`<p>${escape(p).replace(/\n/g,'<br>')}</p>`).join('');
  }
  const fullDate = value => new Intl.DateTimeFormat('ru-RU',{day:'numeric',month:'long',year:'numeric',timeZone:'UTC'}).format(new Date(`${value}T12:00:00Z`));
  function header(kicker, title, description) {
    return `<section class="intro content-intro"><div class="eyebrow">${kicker}</div><h1>${title}</h1><p>${description}</p></section>`;
  }
  function empty(title, message, icon='≈') {
    return `<section class="state empty-state"><div class="state-icon" aria-hidden="true">${icon}</div><h2>${title}</h2><p>${message}</p><a class="text-link" href="#/">Посмотреть меню <span aria-hidden="true">↗</span></a></section>`;
  }
  function create({root, photo}) {
    function events(data) {
      const items = validateEvents(data);
      root.innerHTML = header('События в Рыбалтике','Афиша','Вечера, ради которых хочется собраться вместе.') +
        (items.length ? `<div class="section-heading"><h2>Ближайшие встречи</h2><span class="count">${items.length} в афише</span></div><div class="event-grid">${items.map((e,i)=>{
          const date = new Date(`${e.date}T12:00:00Z`);
          return `<article class="event-card ${i===0?'event-featured':''}" aria-labelledby="event-${e.id}"><div class="event-photo">${photo({name:e.title,image_url:e.image_url},i!==0)}<div class="date-tile" aria-hidden="true"><strong>${date.getUTCDate()}</strong><span>${new Intl.DateTimeFormat('ru-RU',{month:'short',timeZone:'UTC'}).format(date).replace('.','')}</span></div></div><div class="event-copy"><time class="event-date" datetime="${escape(e.date)}">${fullDate(e.date)}</time><h2 id="event-${e.id}">${escape(e.title)}</h2><div class="content-text">${paragraphs(e.description || 'Описание мероприятия появится позже.')}</div></div></article>`;
        }).join('')}</div>` : empty('Скоро новые встречи','Пока в афише нет опубликованных мероприятий. Загляните чуть позже.','◷'));
    }
    function vacancies(data) {
      const items = validateVacancies(data);
      root.innerHTML = header('Работа в ресторане','Вакансии','Хорошая кухня начинается с людей. Найдите свою роль в нашей команде.') +
        (items.length ? `<div class="section-heading"><h2>Открытые позиции</h2><span class="count">${items.length} в команде</span></div><div class="vacancy-list">${items.map((v,i)=>`<article class="vacancy-card" aria-labelledby="vacancy-${v.id}"><div class="vacancy-top"><span class="vacancy-index" aria-hidden="true">${String(i+1).padStart(2,'0')}</span><span class="status-tag">Открыта</span></div><h2 id="vacancy-${v.id}">${escape(v.position)}</h2><div class="content-text">${paragraphs(v.description || 'Описание позиции уточняется.')}</div><div class="salary-block"><span>Ориентировочная оплата</span><strong>${escape(v.salary?.trim() || 'Оплата уточняется')}</strong></div></article>`).join('')}</div>` : empty('Сейчас нет открытых вакансий','Когда появятся новые позиции, мы опубликуем их здесь.','✳'));
    }
    function loyalty(data) {
      const page = validateLoyalty(data);
      if(!page) {
        root.innerHTML=header('Для наших гостей','Программа лояльности','Здесь будет актуальная информация о программе.') + empty('Информация скоро появится','Мы готовим подробности. Следите за обновлениями.','♡');
        return;
      }
      root.innerHTML=header('Для наших гостей',escape(page.title),escape(page.summary || 'Информация о программе для гостей Рыбалтики.')) +
        `<article class="loyalty-sheet"><div class="loyalty-art" aria-hidden="true"><span>≈</span><p>РЫБАЛТИКА</p><i>С хорошим вкусом.</i></div><div class="loyalty-copy"><div class="eyebrow">О программе</div><div class="content-text loyalty-text">${paragraphs(page.body)}</div><a class="text-link" href="#/">К нашему меню <span aria-hidden="true">↗</span></a></div></article>`;
    }
    return {events,vacancies,loyalty};
  }
  window.RybaltikaContent={create,validateEvents,validateVacancies,validateLoyalty,paragraphs};
})();

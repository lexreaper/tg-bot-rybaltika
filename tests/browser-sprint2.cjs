// Start run_demo.py with CONTENT_ADMIN_TOKEN, then npm run test:browser:sprint2.
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const origin=process.env.TEST_BASE_URL || 'http://127.0.0.1:8000';
const key=process.env.TEST_ADMIN_TOKEN;
(async()=>{
  assert(key,'Set TEST_ADMIN_TOKEN to the same local key as CONTENT_ADMIN_TOKEN on the test server.');
  const options={headless:true};
  if(process.env.CHROMIUM_EXECUTABLE)options.executablePath=process.env.CHROMIUM_EXECUTABLE;
  if(process.env.CHROMIUM_ARGS)options.args=JSON.parse(process.env.CHROMIUM_ARGS);
  const browser=await chromium.launch(options);
  const auth={'X-Admin-Token':key};
  let original,checks=0;
  const pass=label=>{checks++;console.log('PASS '+label);};
  const errors=[];
  const context=await browser.newContext({viewport:{width:390,height:844}});
  await context.route('https://telegram.org/**',r=>r.abort());
  const page=await context.newPage();page.on('pageerror',error=>errors.push(error.message));
  const go=async(hash,selector)=>{await page.goto(origin+'/?qa='+Math.random()+hash);await page.locator(selector).first().waitFor();};
  const shots=[];
  const capture=async(name)=>{
    shots.push({name,html:await page.locator('.app-shell').innerHTML()});
    if(process.env.QA_SNAPSHOT_DIR)await page.screenshot({path:`${process.env.QA_SNAPSHOT_DIR}/${name}.png`,fullPage:true});
  };
  try {
    await go('#/','.category');
    await page.getByRole('link',{name:'Афиша',exact:true}).click();
    await page.locator('.event-card').first().waitFor();
    const events=await (await page.request.get(origin+'/events')).json();
    assert.equal(await page.locator('.event-card').count(),events.length);
    assert.equal(await page.locator('time').first().getAttribute('datetime'),events[0].date);
    assert.equal(await page.locator('.main-nav [aria-current=page]').textContent(),'Афиша');
    await page.locator('.event-photo img').first().evaluate(img=>img.decode());
    pass('events from real API with photo, title, description and calendar date');
    await capture('events');
    assert.equal(await page.getByRole('button',{name:/брони/i}).count(),0);
    assert.equal(await page.getByRole('link',{name:/брони/i}).count(),0);pass('no booking controls');
    await page.getByRole('link',{name:'Вакансии',exact:true}).click();await page.locator('.vacancy-card').first().waitFor();
    assert.equal(await page.locator('.vacancy-card').count(),3);
    await page.getByText('Оплата уточняется',{exact:true}).waitFor();pass('positions with descriptions, known and unknown salaries');
    await capture('vacancies');
    await page.getByRole('link',{name:'Лояльность',exact:true}).click();await page.locator('.loyalty-sheet').waitFor();
    assert.equal(await page.locator('.loyalty-sheet input,.loyalty-sheet button').count(),0);pass('loyalty information without account, points or accrual controls');
    await capture('loyalty');
    for(const [hash,endpoint,title] of [
      ['#/events','/events','Скоро новые встречи'],
      ['#/vacancies','/vacancies','Сейчас нет открытых вакансий'],
      ['#/loyalty','/loyalty','Информация скоро появится'],
    ]) {
      await page.route('**'+endpoint,r=>r.fulfill({json:endpoint==='/loyalty'?null:[]}));
      await go(hash,'.empty-state');await page.getByText(title,{exact:true}).waitFor();
      await page.unroute('**'+endpoint);pass('empty state '+endpoint);
    }
    for(const [hash,endpoint,selector] of [['#/events','/events','.event-card'],['#/vacancies','/vacancies','.vacancy-card'],['#/loyalty','/loyalty','.loyalty-sheet']]) {
      await page.route('**'+endpoint,r=>r.fulfill({status:503,json:{detail:'unavailable'}}));
      await go(hash,'#retry');await page.unroute('**'+endpoint);
      await page.locator('#retry').click();await page.locator(selector).first().waitFor();pass('error and retry '+endpoint);
    }
    await page.route('**/events',r=>r.fulfill({json:[{id:9,title:'Без фото',description:'Описание',date:'2026-11-01',image_url:'/missing-event.jpg'}]}));
    await go('#/events','.event-card');await page.locator('.event-photo .no-photo-label').waitFor();pass('broken event photo fallback');
    await page.unroute('**/events');
    await page.route('**/vacancies',r=>r.fulfill({json:[{id:9,position:'<img src=x onerror=alert(1)>',description:'<script>alert(1)</script>',salary:'   '}]}));
    await go('#/vacancies','.vacancy-card');
    assert.equal(await page.locator('.vacancy-card h2').textContent(),'<img src=x onerror=alert(1)>');
    assert.equal(await page.locator('.vacancy-card img,.vacancy-card script').count(),0);
    await page.getByText('Оплата уточняется',{exact:true}).waitFor();pass('vacancy text escaped and whitespace salary treated as unknown');
    await page.unroute('**/vacancies');
    await page.route('**/events',r=>r.fulfill({json:[{id:1,title:'Invalid date',date:'2026-02-31',description:'',image_url:null}]}));
    await go('#/events','#retry');pass('invalid calendar date produces an error instead of a wrong date');await page.unroute('**/events');
    await page.route('**/menu/categories',r=>r.fulfill({status:503,json:{}}));
    await go('#/events','.event-card');await page.unroute('**/menu/categories');pass('new sections load independently of the menu endpoint');
    await page.route('**/assets/config.js',r=>r.fulfill({contentType:'application/javascript',body:"window.APP_CONFIG={apiBaseUrl:'',endpoints:{events:'/team/events'}}"}));
    await page.route('**/team/events',r=>r.fulfill({json:events}));
    await go('#/events','.event-card');pass('configurable team API endpoint');
    await page.unroute('**/assets/config.js');await page.unroute('**/team/events');
    const editor=await context.newPage();editor.on('pageerror',e=>errors.push(e.message));
    await editor.goto(origin+'/admin');await editor.getByLabel('Ключ доступа',{exact:true}).fill('wrong-key-for-test-0123456789');
    await editor.getByRole('button',{name:'Войти в редактор'}).click();await editor.getByText('Неверный ключ доступа. Войдите снова.').waitFor();pass('editor rejects invalid access');
    await editor.getByLabel('Ключ доступа',{exact:true}).fill(key);await editor.getByRole('button',{name:'Войти в редактор'}).click();await editor.locator('#loyalty-form').waitFor();
    original=await (await editor.request.get(origin+'/admin/loyalty',{headers:auth})).json();
    await editor.locator('[name=title]').fill('Обновление из редактора');
    await editor.locator('[name=body]').fill('Первый абзац.\n\n<script>alert(1)</script>');
    assert.equal(await editor.locator('#preview script').count(),0);
    await editor.getByRole('button',{name:'Сохранить изменения'}).click();await editor.getByText('Сохранено. Изменения опубликованы.',{exact:true}).waitFor();
    await go('#/loyalty','.loyalty-sheet');
    assert.equal(await page.locator('h1').textContent(),'Обновление из редактора');
    assert.equal(await page.locator('.loyalty-text script').count(),0);
    assert.match(await page.locator('.loyalty-text').textContent(),/<script>alert\(1\)<\/script>/);pass('editor preview and saved public content escaped and persisted');
    await editor.locator('[name=body]').fill('Не потерять текст при сбое');
    await editor.route('**/admin/loyalty',r=>r.request().method()==='PUT'?r.fulfill({status:503,json:{}}):r.continue());
    await editor.getByRole('button',{name:'Сохранить изменения'}).click();await editor.getByText('Сервер временно недоступен. Попробуйте позже.',{exact:true}).waitFor();
    assert.equal(await editor.locator('[name=body]').inputValue(),'Не потерять текст при сбое');
    await editor.unroute('**/admin/loyalty');await editor.getByRole('button',{name:'Сохранить изменения'}).click();
    await editor.getByText('Сохранено. Изменения опубликованы.',{exact:true}).waitFor();pass('save error retains input and retry succeeds');
    await editor.locator('[name=is_published]').uncheck();await editor.getByRole('button',{name:'Сохранить изменения'}).click();
    await editor.getByText('Сохранено. Страница скрыта от посетителей.',{exact:true}).waitFor();
    await go('#/loyalty','.empty-state');pass('unpublishing hides loyalty information');
    // Restore the demonstration text; no fixture is embedded in the public frontend.
    let current=await (await editor.request.get(origin+'/admin/loyalty',{headers:auth})).json();
    await editor.request.put(origin+'/admin/loyalty',{headers:auth,data:{title:original.title,summary:original.summary,body:original.body,is_published:original.is_published,expected_version:current.version}});
    await editor.getByRole('button',{name:'Загрузить актуальную версию'}).click();await editor.locator('[name=title]').filter({visible:true}).waitFor();
    for(const width of [320,390,1280]) {
      await page.setViewportSize({width,height:844});
      for(const [hash,selector] of [['#/events','.event-card'],['#/vacancies','.vacancy-card'],['#/loyalty','.loyalty-sheet']]) {
        await go(hash,selector);assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`overflow at ${width} ${hash}`);
      }
      await editor.setViewportSize({width,height:844});assert(await editor.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`editor overflow at ${width}`);
    }
    pass('public pages and editor fit 320, 390 and 1280 px');
    assert.deepEqual(errors,[]);pass('no uncaught browser errors');
    if(process.env.QA_SNAPSHOT_DIR)fs.writeFileSync(`${process.env.QA_SNAPSHOT_DIR}/sprint2-screens.json`,JSON.stringify(shots));
    console.log(`${checks} Sprint 2 browser checks passed`);
  } finally {
    if(original) {
      const current=await (await context.request.get(origin+'/admin/loyalty',{headers:auth})).json();
      await context.request.put(origin+'/admin/loyalty',{headers:auth,data:{title:original.title,summary:original.summary,body:original.body,is_published:original.is_published,expected_version:current.version}});
    }
    await browser.close();
  }
})().catch(error=>{console.error(error);process.exit(1);});

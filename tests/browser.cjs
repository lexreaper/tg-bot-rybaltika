// Start python run_demo.py first, then: npm install; npx playwright install chromium; npm run test:browser
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const origin = process.env.TEST_BASE_URL || 'http://127.0.0.1:8000';
(async () => {
  const options = {headless:true};
  if(process.env.CHROMIUM_EXECUTABLE) options.executablePath=process.env.CHROMIUM_EXECUTABLE;
  if(process.env.CHROMIUM_ARGS) options.args=JSON.parse(process.env.CHROMIUM_ARGS);
  const browser=await chromium.launch(options);
  let checks=0;
  function pass(label) {checks++;console.log(`PASS ${label}`);}
  try {
    const page=await browser.newPage({viewport:{width:390,height:844}});
    const errors=[]; page.on('pageerror',e=>errors.push(e.message));
    // The regular browser suite should work without Telegram's CDN.
    await page.route('https://telegram.org/**',r=>r.abort());
    const go=async(hash,selector)=>{await page.goto(origin+'/?qa='+Math.random()+hash);await page.locator(selector).first().waitFor();};
    await go('#/','.category');
    assert.equal(await page.locator('.category').count(),5);pass('five categories from actual API');
    const snapshots=[];
    const capture=async(name)=>{
      snapshots.push({name,html:await page.locator('.app-shell').innerHTML()});
      if(process.env.QA_SNAPSHOT_DIR) await page.screenshot({path:`${process.env.QA_SNAPSHOT_DIR}/${name}.png`,fullPage:true});
    };
    await capture('categories');
    await page.locator('a[href="#/category/1"]').first().click();
    await page.locator('.dish').first().waitFor();
    assert.equal(await page.locator('.dish').count(),3);pass('category filters dishes');
    await capture('dishes');
    await page.getByRole('searchbox').fill('лосось');
    assert.equal(await page.locator('.dish').count(),2);pass('search matches name and ingredients');
    await page.getByRole('searchbox').fill('несуществующее');
    await page.getByText('Ничего не нашлось').waitFor();pass('empty search state');
    await page.getByRole('searchbox').fill('гриле');
    await page.locator('.dish').click();
    await page.locator('.detail').waitFor();
    assert.match(await page.locator('.price').textContent(),/890/);
    assert.match(await page.locator('.ingredients').textContent(),/Филе лосося/);
    await page.locator('.detail-photo img').evaluate(img=>img.decode());pass('detail photo, composition and price');
    await capture('detail');
    await page.getByRole('link',{name:'Вернуться к блюдам',exact:false}).click();
    await page.getByRole('searchbox').waitFor();
    assert.equal(await page.getByRole('searchbox').inputValue(),'гриле');pass('back preserves search');
    await page.getByRole('searchbox').fill('');
    await page.locator('a[href="#/dish/3"]').click();
    await page.locator('.detail-photo .no-photo-label').waitFor();pass('missing photo fallback');
    await go('#/dish/99999','.state');
    assert.match(await page.locator('h1').textContent(),/Не нашли/);pass('404 state');
    await page.route('**/menu/categories',r=>r.fulfill({status:503,contentType:'application/json',body:'{"detail":"error"}'}));
    await go('#/','#retry');
    await page.unroute('**/menu/categories');
    await page.locator('#retry').click();
    await page.locator('.category').first().waitFor();pass('server failure and retry');
    await page.route('**/menu?category_id=1',r=>r.fulfill({json:[]}));
    await go('#/category/1','.state');
    await page.getByText('Пока нет блюд').waitFor();pass('empty category');
    await page.unroute('**/menu?category_id=1');
    await page.route('**/menu/categories',r=>r.fulfill({json:[]}));
    await go('#/','.state');
    await page.getByText('Меню скоро появится').waitFor();pass('empty menu');
    await page.unroute('**/menu/categories');
    await page.route('**/menu/categories',r=>r.fulfill({json:{unexpected:true}}));
    await go('#/','#retry');pass('invalid response is handled');
    await page.unroute('**/menu/categories');
    await page.route('**/assets/salmon.jpg',r=>r.abort());
    await go('#/dish/1','.detail');
    await page.locator('.detail-photo .no-photo-label').waitFor();pass('broken image fallback');
    await page.unroute('**/assets/salmon.jpg');
    await page.route('**/menu/dishes/1',r=>r.fulfill({json:{id:1,category_id:1,name:'<img src=x onerror=alert(1)>',description:'<script>alert(1)</script>',price:'20.10',image_url:null,is_available:true}}));
    await go('#/dish/1','.detail');
    assert.equal(await page.locator('h1').textContent(),'<img src=x onerror=alert(1)>');
    assert.equal(await page.locator('h1 img').count(),0);pass('API text is escaped');
    await page.unroute('**/menu/dishes/1');
    await go('#/','.category');
    await page.evaluate(()=>{window.APP_CONFIG.requestTimeoutMs=30;});
    await page.route('**/menu?category_id=1',async r=>{await new Promise(resolve=>setTimeout(resolve,150));try{await r.continue();}catch{}});
    await page.locator('a[href="#/category/1"]').first().click();
    await page.locator('#retry').waitFor();
    assert.match(await page.locator('.state').textContent(),/слишком долго/);pass('request timeout');
    await page.unroute('**/menu?category_id=1');
    await page.evaluate(()=>{window.APP_CONFIG.requestTimeoutMs=10000;});
    await page.route('**/menu?category_id=1',async r=>{await new Promise(resolve=>setTimeout(resolve,200));try{await r.continue();}catch{}});
    await page.evaluate(()=>{location.hash='#/';});await page.locator('.category').first().waitFor();
    await page.evaluate(()=>{location.hash='#/category/1';});
    await page.locator('[aria-busy="true"]').waitFor();
    await page.evaluate(()=>{location.hash='#/category/2';});
    await page.locator('.dish').first().waitFor();
    assert.match(await page.locator('h1').textContent(),/Салаты/);pass('rapid navigation ignores obsolete response');
    await page.unroute('**/menu?category_id=1');
    for(const width of [320,390,1280]) {
      await page.setViewportSize({width,height:844});
      for(const [hash,selector] of [['#/','.category'],['#/category/1','.dish'],['#/dish/1','.detail']]) {
        await go(hash,selector);
        assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`overflow ${width} ${hash}`);
      }
    }
    pass('three screens fit 320, 390 and 1280 px');
    // Telegram integration contract: stub SDK; does not replace a real device test.
    const telegram=await browser.newPage({viewport:{width:390,height:844}});
    await telegram.route('https://telegram.org/**',r=>r.abort());
    await telegram.addInitScript(()=>{
      window.tgCalls={};window.tgEvents={};
      window.Telegram={WebApp:{colorScheme:'dark',safeAreaInset:{top:10,bottom:10},contentSafeAreaInset:{top:5,bottom:5},isVersionAtLeast:()=>true,ready:()=>window.tgCalls.ready=true,expand:()=>window.tgCalls.expand=true,setHeaderColor:()=>{},setBackgroundColor:()=>{},onEvent:(name,fn)=>window.tgEvents[name]=fn,BackButton:{onClick:fn=>window.tgBack=fn,show:()=>window.tgCalls.back=true,hide:()=>window.tgCalls.back=false}}};
    });
    await telegram.goto(origin+'/#/dish/1');await telegram.locator('.detail').waitFor();
    assert.equal(await telegram.evaluate(()=>document.documentElement.dataset.theme),'dark');
    assert.deepEqual(await telegram.evaluate(()=>window.tgCalls),{ready:true,expand:true,back:true});
    await telegram.evaluate(()=>window.tgBack());await telegram.locator('.dish').first().waitFor();
    await telegram.evaluate(()=>window.tgBack());await telegram.locator('.category').first().waitFor();
    assert.equal(await telegram.evaluate(()=>window.tgCalls.back),false);pass('Telegram ready, expand, theme and BackButton (SDK stub)');
    assert.deepEqual(errors,[]);pass('no uncaught browser errors');
    if(process.env.QA_SNAPSHOT_DIR) fs.writeFileSync(`${process.env.QA_SNAPSHOT_DIR}/screens.json`,JSON.stringify(snapshots));
    console.log(`${checks} browser checks passed`);
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});

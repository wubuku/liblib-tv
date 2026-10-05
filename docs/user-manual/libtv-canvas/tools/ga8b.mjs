import { launch, open, closePromos } from './lib.mjs';
import { resolve } from 'node:path';
const B='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const E=(n)=>resolve('tools','.evidence',n);
const CLIP={x:150,y:38,width:250,height:300};
// ⭐ 顶栏画布按钮按**位置**取，不靠文字正则（缺陷 493：读不到就换判据，别放弃）
const 顶栏 = ()=>page.evaluate(()=>{
  const b=[...document.querySelectorAll('button')].find(x=>{const r=x.getBoundingClientRect();
    return r.x>160&&r.x<180&&r.y<20&&r.width>40&&r.width<120;});
  return b?{text:b.innerText.trim(), box:[b.getBoundingClientRect().x,b.getBoundingClientRect().y,b.getBoundingClientRect().width,b.getBoundingClientRect().height].map(Math.round), aria:b.getAttribute('aria-label')}:null;});
const pid = ()=>page.evaluate(()=>(location.search.match(/projectId=(\w+)/)||[])[1]);
try {
  await open(page,B); await closePromos(page);
  T('主画布顶栏:', await 顶栏());

  // 建一张叫 GA-同步测试
  await page.getByRole('button',{name:/^画布/}).first().click(); await page.waitForTimeout(900);
  await page.locator('button[aria-label="新建画布"]').click(); await page.waitForTimeout(900);
  await page.locator('input[aria-label="画布名称"]').fill('GA-同步测试');
  await page.keyboard.press('Enter'); await page.waitForTimeout(2500);
  T('创建后 pid:', await pid());
  T('创建后顶栏（未刷新）:', await 顶栏());

  // 刷新后再读
  await page.reload({waitUntil:'domcontentloaded'}); await page.waitForTimeout(3000); await closePromos(page);
  T('刷新后 pid:', await pid());
  T('刷新后顶栏:', await 顶栏());

  // 打开下拉截图
  await page.getByRole('button',{name:/^GA-|^画布|^999/}).first().click(); await page.waitForTimeout(1000);
  T('下拉开?', await page.evaluate(()=>!!document.querySelector('button[aria-label="新建画布"]')));
  T('列表前6:', await page.evaluate(()=>[...document.querySelectorAll('[aria-label^="切换到画布"]')].slice(0,6).map(e=>e.getAttribute('aria-label').replace('切换到画布 ',''))));
  await page.screenshot({path:E('ga8-4-自定义名列表.png'), clip:CLIP});
  console.log('  拍 ga8-4-自定义名列表.png');
} finally { await browser.close(); }

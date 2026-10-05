import { launch, open, closePromos } from './lib.mjs';
const B='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const net=[]; page.on('request', r=>{ const u=r.url(); if(/create-with-space|project\/(create|update|delete)/.test(u)) net.push(r.method()+' '+u.replace('https://api.liblib.tv','')); });
async function 开下拉(){ await open(page,B); await closePromos(page);
  await page.getByRole('button',{name:/^画布 \d+$/}).first().click(); await page.waitForTimeout(900); }
async function 状态(tag){ const s=await page.evaluate(()=>({
  行数:document.querySelectorAll('[aria-label^="切换到画布"]').length,
  inp:document.querySelector('input[aria-label="画布名称"]')?.value ?? null,
  顶栏:[...document.querySelectorAll('button')].find(b=>/^画布 \d+$/.test((b.innerText||'').trim()))?.innerText.trim(),
  pid:(location.search.match(/projectId=(\w+)/)||[])[1]})); T(tag,s); return s; }
try {
  // A. 改名 + Enter
  await 开下拉();
  await page.locator('button[aria-label="新建画布"]').click(); await page.waitForTimeout(900);
  await page.locator('input[aria-label="画布名称"]').fill('GA改名Enter');
  await page.keyboard.press('Enter');
  await page.waitForTimeout(2500);
  await 状态('A 改名+Enter:');
  T('A 网络:', net.splice(0));

  // B. 清空名字 + 点空白
  await 开下拉();
  await page.locator('button[aria-label="新建画布"]').click(); await page.waitForTimeout(900);
  await page.locator('input[aria-label="画布名称"]').fill('');
  await page.mouse.click(700, 500);
  await page.waitForTimeout(2500);
  await 状态('B 清空+点空白:');
  T('B 网络:', net.splice(0));

  // C. 只按一次空格(一个空格)+ Enter
  await 开下拉();
  await page.locator('button[aria-label="新建画布"]').click(); await page.waitForTimeout(900);
  await page.locator('input[aria-label="画布名称"]').fill('   ');
  await page.keyboard.press('Enter');
  await page.waitForTimeout(2500);
  await 状态('C 三空格+Enter:');
  T('C 网络:', net.splice(0));

  // D. 只输入数字，看会不会被格式化成 画布 N
  await 开下拉();
  await page.locator('button[aria-label="新建画布"]').click(); await page.waitForTimeout(900);
  await page.locator('input[aria-label="画布名称"]').fill('999');
  await page.keyboard.press('Enter');
  await page.waitForTimeout(2500);
  await 状态('D 输入 999 + Enter:');
  T('D 网络:', net.splice(0));

  // 汇总所有画布名
  await 开下拉();
  const 名单 = await page.evaluate(()=>[...document.querySelectorAll('[aria-label^="切换到画布"]')].map(e=>e.getAttribute('aria-label').replace('切换到画布 ','')));
  T('名单前8:', 名单.slice(0,8)); T('总行数:', 名单.length);
} finally { await browser.close(); }

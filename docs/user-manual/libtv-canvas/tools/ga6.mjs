import { launch, open, closePromos } from './lib.mjs';
const B='https://www.liblib.tv/canvas?spaceId=10354929&projectId=';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
try {
  // 1) 画布 65 是否真存在
  await open(page, B+'890cdef6150d4fc9a49fa7eed9915f90');
  await closePromos(page);
  T('画布 65 节点数:', await page.locator('.react-flow__node').count());
  T('画布 65 顶栏:', await page.evaluate(()=>[...document.querySelectorAll('button')].find(b=>/^画布 \d+$/.test((b.innerText||'').trim()))?.innerText.trim()));

  // 2) 回到主画布看列表
  await open(page, B+'34226ef170f248248c74f85290228f6b');
  await closePromos(page);
  T('主画布节点数:', await page.locator('.react-flow__node').count());
  await page.getByRole('button', { name: /^画布 \d+$/ }).first().click();
  await page.waitForTimeout(1000);
  const L = await page.evaluate(()=>{
    const rows=[...document.querySelectorAll('[aria-label^="切换到画布"]')].map(e=>e.getAttribute('aria-label').replace('切换到画布 ',''));
    return {n:rows.length, 前6:rows.slice(0,6), 后3:rows.slice(-3)};
  });
  T('主画布下拉:', L);

  // 3) 点加号 → 挂网络监听 → 不做任何操作，直接点面板外
  const net=[]; page.on('request', r=>{ const u=r.url(); if(/\/api\/.*(canvas|project)/.test(u)) net.push(r.method()+' '+u.replace(/https:\/\/www\.liblib\.tv/,'')); });
  const before = await page.evaluate(()=>document.querySelectorAll('[aria-label^="切换到画布"]').length);
  await page.locator('button[aria-label="新建画布"]').click();
  await page.waitForTimeout(1500);
  const mid = await page.evaluate(()=>({行数:document.querySelectorAll('[aria-label^="切换到画布"]').length,
    inp:document.querySelector('input[aria-label="画布名称"]')?.value, 顶栏:location.search}));
  T('点加号后(未确认):', mid);
  T('此刻网络请求:', net);
  // 点浮层外（画布空白处）
  await page.mouse.click(700, 500);
  await page.waitForTimeout(2000);
  const after = await page.evaluate(()=>({行数:document.querySelectorAll('[aria-label^="切换到画布"]').length,
    inp:!!document.querySelector('input[aria-label="画布名称"]'), 顶栏:location.search,
    popover:!!document.querySelector('.mantine-Popover-dropdown')}));
  T('点空白处后:', after);
  T('累计网络请求:', net);
} finally { await browser.close(); }

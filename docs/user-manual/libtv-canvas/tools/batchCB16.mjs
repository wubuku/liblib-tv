// Batch CB-16：⭐ 上一条读数把话说反了，得纠正：
//   CB14/CB15 的「刷新后没有 CB12临时文件夹」**不是「没落盘」** ——
//   CB15 建完新文件夹之后，抽屉里 **CB12临时文件夹 和 CB15临时文件夹 同时出现**。
//   真相是：**子文件夹默认折叠**，只有「新建子文件夹」会让父级展开；
//   而「管理」弹窗**只列根级文件夹**。两条路径都看不到 = 折叠 + 只列根级，不是不存在。
//   ⭐ 又一次：**「没找到」和「不存在」长得一模一样** —— 得先找到那个让它显形的手势。
//
// 这一步只做清理：删掉**本轮自己建的** CB12 / CB15 两个文件夹。
// ⛔ 三道防线（沿用 CB13）：认行用「从 更多操作 按钮向上走到 innerText 恰好等于该名字」；
//    点删除后**先读确认框文字**，对不上就按取消。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const MINE = ['CB12临时文件夹', 'CB15临时文件夹'];

const { browser, page } = await launch();
await open(page, URL_);
await closePromos(page);
const out = {};

await page.evaluate(async () => {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  for (let i = 0; i < 6; i += 1) {
    const hit = [...document.querySelectorAll('button, [role="button"]')].find((b) => (b.innerText || '').trim() === '知道了');
    if (hit) { hit.click(); await sleep(500); }
    if (!(document.body.innerText || '').includes('已升级为 TV Director')) return;
  }
});
await page.waitForTimeout(800);

const inDrawer = (fnBody) => page.evaluate(`(() => {
  const d = [...document.querySelectorAll('.mantine-Drawer-content')]
    .filter((x) => { const r = x.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
    .find((x) => [...x.querySelectorAll('button')].some((b) => ['画布','资产'].includes((b.innerText||'').trim())));
  if (!d) return { __err: 'asset drawer not found' };
  ${fnBody}
})()`);

await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const has = [...document.querySelectorAll('.mantine-Drawer-content')].filter(vis)
    .some((d) => [...d.querySelectorAll('button')].some((b) => ['画布', '资产'].includes((b.innerText || '').trim())));
  if (has) return;
  const c = [...document.querySelectorAll('[aria-label="资产管理"]')].filter(vis)
    .map((el) => ({ el, r: el.getBoundingClientRect() })).filter((o) => o.r.x < 100).sort((a, b) => a.r.x - b.r.x);
  c[0]?.el.click();
});
await page.waitForTimeout(1600);
await inDrawer(`[...d.querySelectorAll('button')].find((b)=>(b.innerText||'').trim()==='资产')?.click(); return 1;`);
await page.waitForTimeout(1600);

// —— 展开父级：悬停「待分类资产」行，再点行内最左的可点元素（展开箭头） ——
out.expand = await inDrawer(`
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const more = [...d.querySelectorAll('[aria-label="更多操作"]')].filter(vis)[0];
  if (!more) return { ok:false, why:'没有行' };
  let row = more;
  while (row && row !== d && (row.innerText||'').trim() !== '待分类资产') row = row.parentElement;
  if (!row) return { ok:false, why:'走不到待分类资产行' };
  const cands = [...row.querySelectorAll('button,[role="button"],svg')].filter(vis)
    .map((k) => ({ k, r: k.getBoundingClientRect() })).sort((a,b)=>a.r.x-b.r.x);
  if (!cands.length) return { ok:false, why:'行内无箭头' };
  cands[0].k.dispatchEvent(new MouseEvent('mouseover', { bubbles: true }));
  cands[0].k.click();
  return { ok:true, arrowX: Math.round(cands[0].r.x) };`);
await page.waitForTimeout(1500);
out.t1 = await inDrawer(`return (d.innerText||'').replace(/\\s+/g,' ').slice(0,300);`);

// 逐个删
out.deletions = [];
for (const name of MINE) {
  const step = { name };
  const raw = await inDrawer(`return (d.innerText||'');`);
  const present = typeof raw === 'string' ? raw.includes(name) : false;
  step.present = present;
  if (!present) { out.deletions.push(step); continue; }

  step.opened = await inDrawer(`
    const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    const more = [...d.querySelectorAll('[aria-label="更多操作"]')].filter(vis);
    let hit = null;
    for (const m of more) {
      let row = m;
      while (row && row !== d && (row.innerText||'').trim() !== ${JSON.stringify(name)}) row = row.parentElement;
      if (row) { hit = m; break; }
    }
    if (!hit) return { ok:false, why:'找不到那一行的更多操作' };
    hit.click();
    return { ok:true };`);
  await page.waitForTimeout(900);

  step.delClicked = await page.evaluate(() => {
    const it = [...document.querySelectorAll('.mantine-Menu-item, [role="menuitem"]')]
      .find((el) => (el.innerText || '').trim() === '删除');
    if (!it) return { ok: false, why: '菜单里没有删除' };
    it.click();
    return { ok: true };
  });
  await page.waitForTimeout(1200);

  step.dialog = await page.evaluate(() => {
    const dlg = [...document.querySelectorAll('.mantine-Modal-content, [role="dialog"]')]
      .filter((el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
      .find((el) => /确定删除/.test(el.innerText || ''));
    if (!dlg) return { ok: false, why: '没弹确认框' };
    return { ok: true, text: (dlg.innerText || '').replace(/\s+/g, ' ').slice(0, 140) };
  });
  step.dialogNamesTarget = !!step.dialog?.ok && step.dialog.text.includes(name);

  if (step.dialogNamesTarget) {
    await page.evaluate((n) => {
      const dlg = [...document.querySelectorAll('.mantine-Modal-content, [role="dialog"]')]
        .filter((el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
        .find((el) => (el.innerText || '').includes(n) && /确定删除/.test(el.innerText || ''));
      if (!dlg) return;
      [...dlg.querySelectorAll('button')].find((b) => (b.innerText || '').trim() === '删除')?.click();
    }, name);
    await page.waitForTimeout(1600);
    step.confirmed = true;
  } else {
    await page.evaluate(() => {
      const dlg = [...document.querySelectorAll('.mantine-Modal-content, [role="dialog"]')]
        .filter((el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
        .find((el) => /确定删除/.test(el.innerText || ''));
      if (!dlg) return;
      [...dlg.querySelectorAll('button')].find((b) => (b.innerText || '').trim() === '取消')?.click();
    });
    await page.waitForTimeout(900);
    step.confirmed = false;
    step.aborted = true;
  }
  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(500);
  const raw2 = await inDrawer(`return (d.innerText||'').replace(/\\s+/g,' ').slice(0,300);`);
  step.afterText = raw2;
  step.gone = typeof raw2 === 'string' ? !raw2.includes(name) : null;
  out.deletions.push(step);
}

out.final = await inDrawer(`return (d.innerText||'').replace(/\\s+/g,' ').slice(0,300);`);
await shot(page, 'M-294-资产页-清理之后.png', { clip: { x: 0, y: 80, width: 700, height: 420 } });
await writeFile(resolve(HERE, '.evidence/cb16-cleanup.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify({ expand: out.expand, t1: out.t1, deletions: out.deletions, final: out.final }, null, 2));
await browser.close();

// Batch CC-9：重拍一张**干净**的结果图（上一张右半被 TV Director 侧栏挡住了）。
//   点卡片 → 关掉侧栏 → **自证侧栏不在了** → 拍新节点 → 按名字删掉 → 复核计数复原。
// ⭐ 截图前必须自证遮挡物不在画面里，否则图会骗人（BV11 的教训）。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;

const { browser, page } = await launch();
await open(page, URL_);
await closePromos(page);
const out = {};

const inDrawer = (fnBody) => page.evaluate(`(() => {
  const d = [...document.querySelectorAll('.mantine-Drawer-content')]
    .filter((x) => { const r = x.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
    .find((x) => [...x.querySelectorAll('button')].some((b) => ['画布','资产'].includes((b.innerText||'').trim())));
  if (!d) return { __err: 'asset drawer not found' };
  ${fnBody}
})()`);

// —— 0. 基线 ——
const countNow = () => inDrawer(`const m=((d.innerText||'').match(/共 (\\d+) 节点/)||[])[1]; return m?Number(m):null;`);
await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const c = [...document.querySelectorAll('[aria-label="资产管理"]')].filter(vis)
    .map((el) => ({ el, r: el.getBoundingClientRect() })).filter((o) => o.r.x < 100).sort((a, b) => a.r.x - b.r.x);
  c[0]?.el.click();
});
await page.waitForTimeout(1800);
out.count0 = await countNow();
await page.keyboard.press('Escape');
await page.waitForTimeout(800);

// —— 1. 进特效广场点一张 ——
await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  [...document.querySelectorAll('[aria-label="素材库"]')].filter(vis)[0]?.click();
});
await page.waitForTimeout(1700);
await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const hit = [...document.querySelectorAll('*')].filter((e) => vis(e) && (e.innerText || '').trim() === '特效库');
  let el = hit[hit.length - 1];
  let btn = null;
  for (let i = 0; i < 5 && el && !btn; i += 1) { if (el.tagName === 'BUTTON' || el.getAttribute('role') === 'button') btn = el; el = el.parentElement; }
  (btn || hit[hit.length - 1]?.parentElement)?.click();
});
await page.waitForTimeout(3000);
const cb = await page.evaluate(() => {
  const m = [...document.querySelectorAll('.mantine-Modal-content')].find((el) => (el.innerText || '').includes('特效广场'));
  const cards = [...m.querySelectorAll('div')].filter((el) => { const c = el.className?.toString?.() || ''; return /rounded-xl/.test(c) && /flex-col/.test(c) && /p-2/.test(c); });
  const r = cards[0].getBoundingClientRect();
  return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
});
await page.mouse.move(cb[0] + cb[2] / 2, cb[1] + 90, { steps: 10 });
await page.waitForTimeout(700);
await page.mouse.click(cb[0] + cb[2] / 2, cb[1] + 90);
await page.waitForTimeout(2500);

// —— 2. 关掉 TV Director 侧栏，并**自证** ——
out.closedSide = await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const d = [...document.querySelectorAll('.mantine-Drawer-content')].filter(vis)
    .find((x) => (x.innerText || '').includes('让 TV Director 辅助你的无限创意'));
  if (!d) return { alreadyGone: true };
  const btn = [...d.querySelectorAll('button,[role="button"]')].filter(vis)
    .map((b) => ({ b, r: b.getBoundingClientRect() })).filter((o) => o.r.x > 400)
    .sort((a, b) => a.r.x - b.r.x)[0];
  if (btn) btn.b.click();
  return { clicked: !!btn };
});
await page.waitForTimeout(1200);
out.sideGone = await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  return ![...document.querySelectorAll('.mantine-Drawer-content')].filter(vis)
    .some((x) => (x.innerText || '').includes('让 TV Director 辅助你的无限创意'));
});
out.promosGone = await page.evaluate(() => !(document.body.innerText || '').includes('已升级为 TV Director'));

// —— 3. 拍新节点 ——
out.newNode = await page.evaluate(() => {
  const n = [...document.querySelectorAll('.react-flow__node')]
    .map((e) => ({ id: e.getAttribute('data-id'), t: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40),
      box: (() => { const r = e.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })() }))
    .filter((o) => /素材/.test(o.t));
  return n;
});
await shot(page, 'M-298-特效卡片-点一下就进了画布.png', { clip: { x: 0, y: 0, width: 1440, height: 810 } });

// —— 4. 清理 ——
await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const c = [...document.querySelectorAll('[aria-label="资产管理"]')].filter(vis)
    .map((el) => ({ el, r: el.getBoundingClientRect() })).filter((o) => o.r.x < 100).sort((a, b) => a.r.x - b.r.x);
  c[0]?.el.click();
});
await page.waitForTimeout(1800);
out.count1 = await countNow();
const rows = await inDrawer(`
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const rs = [];
  for (const b of d.querySelectorAll('[aria-label^="定位到节点"]')) {
    const r = b.getBoundingClientRect();
    if (!vis(b) || r.width < 100) continue;
    const name = (b.getAttribute('aria-label') || '').replace('定位到节点 ', '').trim();
    if (!name || rs.some((x) => Math.abs(x.y - r.y) < 10)) continue;
    rs.push({ name, y: Math.round(r.y) });
  }
  return rs;`);
out.rows = rows.map((r) => r.name);
const mine = rows.find((r) => r.name.startsWith('素材-'));
out.mine = mine;
if (mine) {
  await page.mouse.move(120, mine.y + 14, { steps: 10 });
  await page.waitForTimeout(700);
  await page.evaluate((y) => {
    const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    const m = [...document.querySelectorAll('[aria-label="更多操作"]')].filter(vis).find((x) => Math.abs(x.getBoundingClientRect().y - y) < 8);
    if (m) m.click();
  }, mine.y);
  await page.waitForTimeout(900);
  out.del = await page.evaluate(() => {
    const it = [...document.querySelectorAll('.mantine-Menu-item, [role="menuitem"]')].find((el) => (el.innerText || '').trim() === '删除');
    if (!it) return { ok: false };
    it.click();
    return { ok: true };
  });
  await page.waitForTimeout(1800);
}
out.count2 = await countNow();
out.rowsAfter = (await inDrawer(`
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const rs = [];
  for (const b of d.querySelectorAll('[aria-label^="定位到节点"]')) {
    const r = b.getBoundingClientRect();
    if (!vis(b) || r.width < 100) continue;
    const name = (b.getAttribute('aria-label') || '').replace('定位到节点 ', '').trim();
    if (!name || rs.some((x) => Math.abs(x.y - r.y) < 10)) continue;
    rs.push({ name, y: Math.round(r.y) });
  }
  return rs;`)).map((r) => r.name);

await writeFile(resolve(HERE, '.evidence/cc9-shot.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify({ count0: out.count0, count1: out.count1, count2: out.count2, sideGone: out.sideGone, promosGone: out.promosGone, newNode: out.newNode, rows: out.rows, mine: out.mine, del: out.del, rowsAfter: out.rowsAfter }, null, 2));
await browser.close();

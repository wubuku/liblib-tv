// 批次 95 · 收尾清账：a 轮崩在 `canvas-context-menu` 为 null 上，
// 两个自建文本节点（`node_ce47a7tnzq` / `node_tjf3grfajp`）很可能留在共享画布上。
//
// 🔴 **崩溃原因**：a 轮的 P3 让节点进入了**编辑态**（`contenteditable` + `ProseMirror`
//     出现了），收尾时右键落在编辑器里 ⇒ 右键菜单**弹不出来** ⇒ `querySelectorAll` 拿到 null。
// ⇒ 修法：**先 Esc 退出编辑态**，再逐个「点一下选中 → 等 → 右键 → **先确认菜单存在** → 再点删除」。
//     上一版没有「确认菜单存在」这一步，所以一崩就整段丢。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString(), targets: ['node_ce47a7tnzq', 'node_tjf3grfajp'] };

const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const selN = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const nodeN = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]);
const credits = async () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-commerce-entry"]'); return e ? e.getAttribute('aria-label') : null; });
const zoomPct = async () => p.evaluate(() => { const e = document.querySelector('button[aria-label^="Zoom options"]'); return e ? Number((e.getAttribute('aria-label').match(/(\d+)%/) || [])[1]) : null; });
const setZoom = async (t0) => { for (let t = 1; t <= 3; t++) { if (await zoomPct() === t0) return true;
  await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(800);
  const has = await p.evaluate(() => !!document.querySelector('input[data-testid="canvas-zoom-percent-input"]'));
  if (!has) { await p.keyboard.press('Escape'); await p.waitForTimeout(500); continue; }
  await p.evaluate((v) => { const i = document.querySelector('input[data-testid="canvas-zoom-percent-input"]');
    Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(i, String(v));
    i.dispatchEvent(new Event('input', { bubbles: true })); i.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
    i.dispatchEvent(new Event('change', { bubbles: true })); i.blur(); }, t0);
  await p.waitForTimeout(1500); await p.keyboard.press('Escape'); await p.waitForTimeout(800); return true; } return false; };
const rightClick = async (x, y) => { await p.mouse.move(x, y); await p.waitForTimeout(200);
  await p.mouse.down({ button: 'right' }); await p.waitForTimeout(260); await p.mouse.up({ button: 'right' });
  await p.waitForTimeout(1300);
  return p.evaluate(() => !!document.querySelector('[data-testid="canvas-context-menu"]')); };
const scan = (id) => p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
  const r = n.getBoundingClientRect();
  for (let fx = 0.05; fx <= 0.95; fx += 0.05) for (let fy = 0.05; fy <= 0.95; fy += 0.05) {
    const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
    if (x < 0 || y < 0 || x > 1280 || y > 720) continue;
    const el = document.elementFromPoint(x, y);
    if (el && el.closest('.react-flow__node') === n) return { x, y }; }
  return null; }, id);

out.start = { nodes: await nodeN(), sel: await selN(), credits: await credits(), zoom: await zoomPct() };
log('起点：', JSON.stringify(out.start));

// 先把可能残留的编辑态退掉
for (let k = 0; k < 3; k++) {
  const ed = await p.evaluate(() => document.querySelectorAll('[contenteditable="true"],.ProseMirror').length);
  if (!ed) break;
  await p.keyboard.press('Escape'); await p.waitForTimeout(600);
  log('退出编辑态，剩余 contenteditable/ProseMirror =', await p.evaluate(() => document.querySelectorAll('[contenteditable="true"],.ProseMirror').length));
}
await setZoom(60);

out.results = [];
for (const id of out.targets) {
  const rec = { id };
  if (!(await ids()).includes(id)) { rec.gone = true; out.results.push(rec); log(id, '已不在'); continue; }
  let done = false;
  for (let attempt = 1; attempt <= 3 && !done; attempt++) {
    const pt = await scan(id);
    if (!pt) { log(`  ${id} 找不到落点`); await p.keyboard.press('Meta+0'); await p.waitForTimeout(1600); continue; }
    await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1000);
    const who = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
    if (who[0] !== id) { log(`  选中的是 ${JSON.stringify(who)}`); await p.keyboard.press('Escape'); await p.waitForTimeout(500); continue; }
    const menuOpen = await rightClick(pt.x, pt.y);
    if (!menuOpen) { log('  右键菜单没出来（可能还在编辑态）⇒ Esc 后重试');
      await p.keyboard.press('Escape'); await p.waitForTimeout(700); continue; }
    const clicked = await p.evaluate(() => { const m = document.querySelector('[data-testid="canvas-context-menu"]');
      if (!m) return false; const it = Array.from(m.querySelectorAll('[role="menuitem"]'))
        .find((x) => /^删除/.test(x.innerText.replace(/\s+/g, ' ').trim()) && x.getAttribute('aria-disabled') !== 'true');
      if (it) { it.click(); return true; } return false; });
    await p.waitForTimeout(1700);
    const still = (await ids()).includes(id);
    rec.attempt = attempt; rec.menuOpen = menuOpen; rec.clicked = clicked; rec.still = still;
    if (!still) { rec.deleted = true; done = true; log(`  ${id} ✅ 已删除（第 ${attempt} 次尝试）`); }
    else log(`  ${id} 点完还在（第 ${attempt} 次）`);
  }
  if (!done) rec.deleted = false;
  out.results.push(rec);
}

if (await selN() !== '0') { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
await setZoom(60);
const left = (await ids()).filter((x) => out.targets.includes(x));
out.end = { nodes: await nodeN(), sel: await selN(), zoom: await zoomPct(), credits: await credits(), leftover: left };
log('终态：', JSON.stringify(out.end), '｜缩放归位', (await zoomPct()) === 60 ? '✅' : '🔴');
log(left.length ? `🔴 仍有残留：${left.join(' ')}` : '✅ 两个自建节点都已删净');
writeFileSync(new URL('./_tmp-b95-clean.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();

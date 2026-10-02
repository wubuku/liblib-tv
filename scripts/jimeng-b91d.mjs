// 批次 91 · D：拿到对照组 —— **能**发起连线的节点，选中态下手柄长什么样。
//
// c 轮已确认导演台**选中态**下 source 手柄仍是 `pe=none / op=0`（屏上 14×28@24% ⇒ canvas 60×120）。
// 但那还不能下结论，因为**未选中态下所有类型都是 pe=none / op=0**（c 轮 P3-a 实测）。
// ⇒ 缺的是**选中态的对照**：找一个真的有 ⊕ 的类型（音频），选中后读它的手柄。
//
// ⇒ **P4**：若 音频选中态 pe=auto（op≠0），而 导演台选中态 pe=none
//   ⇒ 「能不能从它发起连线」的正确判据是**手柄的 pe/opacity**，
//     **不是**批次 69 用的「有没有 `aria^="Create connected node` 的 ⊕ 钮」——
//     导演台有手柄但不可交互，所以「用 ⊕ 钮数来判」这次碰巧对了，**理由却是错的**。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
const edgeN = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) edges?/) || [])[1]);
const selN = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const credits = async () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-commerce-entry"]'); return e ? e.getAttribute('aria-label') : null; });
const zoomPct = async () => p.evaluate(() => { const e = document.querySelector('button[aria-label^="Zoom options"]'); return e ? Number((e.getAttribute('aria-label').match(/(\d+)%/) || [])[1]) : null; });
const readScale = async () => { const rd = () => p.evaluate(() => { const vp = document.querySelector('.react-flow__viewport');
    const m = (vp ? (vp.style.transform || '') : '').match(/scale\(([-\d.]+)\)/); return m ? Number(m[1]) : null; });
  const a = await rd(); await p.waitForTimeout(500); const c = await rd(); return a !== null && a === c ? a : null; };
const setZoom = async (t0) => { for (let t = 1; t <= 3; t++) { if (await zoomPct() === t0) return true;
  await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(800);
  const has = await p.evaluate(() => !!document.querySelector('input[data-testid="canvas-zoom-percent-input"]'));
  if (!has) { await p.keyboard.press('Escape'); await p.waitForTimeout(500); continue; }
  await p.evaluate((v) => { const i = document.querySelector('input[data-testid="canvas-zoom-percent-input"]');
    Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(i, String(v));
    i.dispatchEvent(new Event('input', { bubbles: true })); i.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
    i.dispatchEvent(new Event('change', { bubbles: true })); i.blur(); }, t0);
  await p.waitForTimeout(1300); await p.keyboard.press('Escape'); await p.waitForTimeout(700);
  if (await zoomPct() === t0) return true; }
  return false; };

// 起点归位
if (await selN() !== '0') { await p.keyboard.press('Escape'); await p.waitForTimeout(700); }
await setZoom(60);
out.start = { edges: await edgeN(), sel: await selN(), credits: await credits(), zoom: await zoomPct(),
  nodes: await p.evaluate(() => document.querySelectorAll('.react-flow__node').length) };
log('起点：', JSON.stringify(out.start));

// 在当前缩放下，找出「完全在视口内 且 有可用落点」的一个节点，按类型分组
const cands = await p.evaluate(() => {
  const out2 = [];
  for (const n of document.querySelectorAll('.react-flow__node')) {
    const r = n.getBoundingClientRect();
    if (!(r.left >= 0 && r.top >= 0 && r.right <= 1280 && r.bottom <= 720)) continue;
    const hits = [];
    for (let fx = 0.15; fx <= 0.85; fx += 0.1) for (let fy = 0.15; fy <= 0.85; fy += 0.1) {
      const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
      const el = document.elementFromPoint(x, y);
      if (el && el.closest('.react-flow__node') === n) hits.push({ x, y });
    }
    if (!hits.length) continue;
    out2.push({ id: n.getAttribute('data-id'), aria: (n.getAttribute('aria-label') || '').slice(0, 24),
      type: (String(n.className || '').match(/react-flow__node-([a-z]+)/) || [])[1] || '?',
      pt: hits[Math.floor(hits.length / 2)], hits: hits.length });
  }
  return out2;
});
out.cands = cands;
log('可点候选：' + cands.map((c) => `${c.type}:${c.aria}(${c.hits})`).join('、'));

// 音频优先（批次 71 记它 before/after ⊕ 都有）
const order = ['audio', 'image', 'video', 'text', 'external'];
const pickByType = (t) => cands.find((c) => c.type === t);
const targets = [];
for (const t of order) { const c = pickByType(t); if (c && targets.length < 2) targets.push(c); }
log('本轮对比：' + targets.map((t) => `${t.type}=${t.aria}`).join(' vs '));

out.rows = [];
for (const c of targets) {
  await p.mouse.click(c.pt.x, c.pt.y); await p.waitForTimeout(1100);
  const ids = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
  if (ids[0] !== c.id) { log(`  ⚠️ ${c.type} 点选未生效（${JSON.stringify(ids)}）`); await p.keyboard.press('Escape'); await p.waitForTimeout(700); continue; }
  const scale = await readScale();
  const h = await p.evaluate(({ i, sc }) => {
    const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); const r = {};
    for (const k of ['source', 'target']) { const e = n.querySelector(`[data-testid="flow-node-${k}-handle"]`);
      if (!e) { r[k] = null; continue; } const q = e.getBoundingClientRect(); const cs = getComputedStyle(e);
      r[k] = { box: `${Math.round(q.width)}×${Math.round(q.height)}`, pe: cs.pointerEvents, op: cs.opacity,
        canvas: sc ? `${Math.round(q.width / sc)}×${Math.round(q.height / sc)}` : null,
        center: [Math.round(q.x + q.width / 2), Math.round(q.y + q.height / 2)] }; }
    r.plus = Array.from(n.querySelectorAll('[data-testid$="connection-menu-button"]')).map((e) => e.getAttribute('aria-label'));
    return r; }, { i: c.id, sc: scale });
  const row = { type: c.type, aria: c.aria, id: c.id, scale, handles: h };
  out.rows.push(row);
  log(`\n  ── ${c.type}（${c.aria}）选中态 scale=${scale}`);
  for (const k of ['source', 'target']) log(`     ${k}: ${h[k] ? `${h[k].box} pe=${h[k].pe} op=${h[k].op} canvas=${h[k].canvas}` : '（无）'}`);
  log(`     ⊕ ${h.plus.length} 个：${JSON.stringify(h.plus)}`);

  // 若 source 手柄可交互 → 拖到空白松手（不建线）
  if (h.source && h.source.pe === 'auto') {
    const blank = await p.evaluate(() => { const r = document.querySelector('.react-flow__pane'); if (!r) return null;
      const q = r.getBoundingClientRect();
      for (let fx = 0.06; fx <= 0.94; fx += 0.06) for (let fy = 0.06; fy <= 0.94; fy += 0.06) {
        const x = Math.round(q.x + q.width * fx), y = Math.round(q.y + q.height * fy);
        const el = document.elementFromPoint(x, y);
        if (el && !el.closest('.react-flow__node') && !el.closest('button')) return { x, y }; }
      return null; });
    if (blank) {
      const [sx, sy] = h.source.center;
      await p.mouse.move(sx, sy); await p.mouse.down(); await p.waitForTimeout(350);
      await p.mouse.move(Math.round((sx + blank.x) / 2), Math.round((sy + blank.y) / 2), { steps: 14 }); await p.waitForTimeout(600);
      const mid = { edges: await edgeN(), menu: await p.evaluate(() => { const m = document.querySelector('[data-testid="canvas-context-menu"]');
        return m ? Array.from(m.querySelectorAll('[role="menuitem"]')).map((i) => i.innerText.replace(/\s+/g, ' ').trim()) : null; }) };
      await p.mouse.up(); await p.waitForTimeout(1300);
      const after = { edges: await edgeN(), menu: await p.evaluate(() => { const m = document.querySelector('[data-testid="canvas-context-menu"]');
        return m ? Array.from(m.querySelectorAll('[role="menuitem"]')).map((i) => i.innerText.replace(/\s+/g, ' ').trim()) : null; }) };
      row.drag = { from: [sx, sy], blank, mid, after };
      log(`     拖到一半：edges=${mid.edges}｜菜单=${JSON.stringify(mid.menu)}`);
      log(`     空白松手：edges=${after.edges}｜菜单=${JSON.stringify(after.menu)}`);
      if (after.menu && after.menu.length) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); }
    }
  }
  await p.keyboard.press('Escape'); await p.waitForTimeout(800);
}

out.verdict = out.rows.map((r) => ({ type: r.type, srcPe: r.handles.source?.pe ?? '(无)', srcOp: r.handles.source?.op ?? '-',
  plus: r.handles.plus.length, dragMenu: r.drag ? (r.drag.after.menu ? r.drag.after.menu.length : 0) : null }));
log('\n判定汇总：' + JSON.stringify(out.verdict));

await p.keyboard.press('Escape'); await p.waitForTimeout(600);
for (let k = 0; k < 3 && await zoomPct() !== 60; k++) await setZoom(60);
const z1 = await zoomPct(); await p.waitForTimeout(900); const z2 = await zoomPct();
out.end = { edges: await edgeN(), sel: await selN(), zoom: z2, zoomStable: z1 === z2, credits: await credits() };
log('终态：', JSON.stringify(out.end), '｜缩放归位', z2 === 60 ? '✅' : '🔴', '｜edges 未变 =', out.end.edges === out.start.edges);
writeFileSync(new URL('./_tmp-b91d.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();

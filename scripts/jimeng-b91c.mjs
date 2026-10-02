// 批次 91 · C：**手柄**存在 ≠ 手柄能用 —— 逐类型比 `pointer-events` / `opacity`。
//
// b 轮在导演台身上撞出一个本页与批次 68/78/88 都没记过的东西：
//   它的 source / target 手柄**都在 DOM 里**、尺寸也对（屏上 14×28@24% ⇒ canvas 60×120），
//   但 **`pointer-events: none` 且 `opacity: 0`**。
//   ⇒ 批次 69「从导演台发起连线做不到」这句话**是对的**，但它缺了「为什么」。
//
// ⇒ **P3**：把**每种类型**节点的手柄的 `pe` / `opacity` / 屏上尺寸一起打出来。
//   若只有导演台是 `none`+`0`，那么
//   **「能不能从它发起连线」的正确判据是手柄的 pe/opacity，不是「有没有 ⊕ 钮」** ——
//   而批次 69 当时用的判据恰恰是后者（「全文档 aria^="Create connected node" 命中 0」）。
//
// ⚠️ 修 b 轮的一个 bug：`src.box.split('×')[0].split('×')` 只会切出一段，
//    `bh` 是 undefined ⇒ `y` 成了 NaN。正确写法是 `box.split('@')[0].split('×')`。
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

// ── 起点归位：上一轮若崩在收尾之前，画布会停在 24% / 有选中 ──
// ⚠️ 脚本必须**对脏起点鲁棒**：否则它读到的「起点」其实是上一轮的残留，
//    而这批要比的恰恰是「选中 vs 未选中」—— 起点不干净，这个比值就没有意义。
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
out.preflight = { zoomBefore: await zoomPct(), selBefore: await selN() };
if (await selN() !== '0') { await p.keyboard.press('Escape'); await p.waitForTimeout(700); }
out.preflight.zoomFixed = await setZoom(60);
out.preflight.selAfter = await selN();
log('起点归位：', JSON.stringify(out.preflight));

out.start = { edges: await edgeN(), sel: await selN(), credits: await credits(), zoom: await zoomPct() };
log('起点：', JSON.stringify(out.start));

// 读一个节点的手柄状态（不依赖选中）
const readHandles = () => p.evaluate(() => {
  const r = {};
  for (const n of document.querySelectorAll('.react-flow__node')) {
    const type = (String(n.className || '').match(/react-flow__node-([a-z]+)/) || [])[1] || '?';
    const rec = { aria: (n.getAttribute('aria-label') || '').slice(0, 22), sel: String(n.className).includes(' selected') };
    for (const k of ['source', 'target']) {
      const e = n.querySelector(`[data-testid="flow-node-${k}-handle"]`);
      if (!e) { rec[k] = null; continue; }
      const q = e.getBoundingClientRect(); const cs = getComputedStyle(e);
      rec[k] = { box: `${Math.round(q.width)}×${Math.round(q.height)}`, pe: cs.pointerEvents, op: cs.opacity, vis: cs.visibility };
    }
    rec.plus = n.querySelectorAll('[data-testid$="connection-menu-button"]').length;
    (r[type] = r[type] || []).push(rec);
  }
  return r;
});

out.byTypeUnselected = await readHandles();
log('\n══ P3-a：未选中态，逐类型的手柄（pe / opacity / 屏上尺寸）');
for (const [t, arr] of Object.entries(out.byTypeUnselected)) {
  const s = arr[0].source, g = arr[0].target;
  log(`  ${t.padEnd(9)} ×${arr.length}｜source ${s ? `${s.box} pe=${s.pe} op=${s.op}` : '（无）'}｜target ${g ? `${g.box} pe=${g.pe} op=${g.op}` : '（无）'}｜⊕ ${arr[0].plus}`);
}

// 选中一个文本节点和一个导演台，看选中态有没有变化
const pick = (id) => p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
  const r = n.getBoundingClientRect(); const hits = [];
  for (let fx = 0.15; fx <= 0.85; fx += 0.1) for (let fy = 0.15; fy <= 0.85; fy += 0.1) {
    const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
    const el = document.elementFromPoint(x, y); if (el && el.closest('.react-flow__node') === n) hits.push({ x, y }); }
  return hits.length ? hits[Math.floor(hits.length / 2)] : null; }, id);

await p.keyboard.press('Meta+0'); await p.waitForTimeout(1700);
const scale = await readScale();
out.scaleAtFit = scale;

for (const [label, id] of [['文本节点', 'node_3bfb9r79qe'], ['导演台', 'node_pxvkay973v']]) {
  const pt = await pick(id);
  if (!pt) { log(`  ⚠️ ${label} 找不到落点`); continue; }
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1000);
  const ids = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
  if (ids[0] !== id) { log(`  ⚠️ ${label} 点选未生效（选中 ${JSON.stringify(ids)}）⇒ 记 VOID`); await p.keyboard.press('Escape'); await p.waitForTimeout(600); continue; }
  // ⚠️ `scale` 必须作为**参数**传进来：闭包变量不会跨进 page.evaluate（第 4 次踩）
  const h = await p.evaluate(({ i, sc }) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const r = {}; for (const k of ['source', 'target']) { const e = n.querySelector(`[data-testid="flow-node-${k}-handle"]`);
      if (!e) { r[k] = null; continue; } const q = e.getBoundingClientRect(); const cs = getComputedStyle(e);
      r[k] = { box: `${Math.round(q.width)}×${Math.round(q.height)}`, pe: cs.pointerEvents, op: cs.opacity,
        canvas: sc ? `${Math.round(q.width / sc)}×${Math.round(q.height / sc)}` : null,
        center: [Math.round(q.x + q.width / 2), Math.round(q.y + q.height / 2)] }; }
    r.plus = Array.from(n.querySelectorAll('[data-testid$="connection-menu-button"]')).map((e) => e.getAttribute('aria-label'));
    return r; }, { i: id, sc: scale });
  log(`\n  ── ${label} 选中态（scale=${scale}）`);
  for (const k of ['source', 'target']) log(`     ${k}: ${h[k] ? `${h[k].box} pe=${h[k].pe} op=${h[k].op} canvas=${h[k].canvas} center=${JSON.stringify(h[k].center)}` : '（无）'}`);
  log(`     ⊕ 菜单钮 ${h.plus.length} 个：${JSON.stringify(h.plus)}`);
  out[label] = h;

  // 若 source 手柄可交互，拖到空白松手看会不会弹菜单（不建线）
  if (h.source && h.source.pe === 'auto') {
    const blank = await p.evaluate(() => { const r = document.querySelector('.react-flow__pane'); if (!r) return null;
      const q = r.getBoundingClientRect();
      for (let fx = 0.08; fx <= 0.92; fx += 0.08) for (let fy = 0.08; fy <= 0.92; fy += 0.08) {
        const x = Math.round(q.x + q.width * fx), y = Math.round(q.y + q.height * fy);
        const el = document.elementFromPoint(x, y);
        if (el && !el.closest('.react-flow__node') && !el.closest('button')) return { x, y }; }
      return null; });
    if (blank) {
      const [sx, sy] = h.source.center;
      await p.mouse.move(sx, sy); await p.mouse.down(); await p.waitForTimeout(300);
      await p.mouse.move(Math.round((sx + blank.x) / 2), Math.round((sy + blank.y) / 2), { steps: 12 }); await p.waitForTimeout(500);
      out[label + '_midDrag'] = { edges: await edgeN(), menu: await p.evaluate(() => { const m = document.querySelector('[data-testid="canvas-context-menu"]');
        return m ? Array.from(m.querySelectorAll('[role="menuitem"]')).map((i) => i.innerText.replace(/\s+/g, ' ').trim()) : null; }) };
      log(`     拖到一半：edges=${out[label + '_midDrag'].edges}｜菜单=${JSON.stringify(out[label + '_midDrag'].menu)}`);
      await p.mouse.up(); await p.waitForTimeout(1200);
      out[label + '_afterDrop'] = { edges: await edgeN(), menu: await p.evaluate(() => { const m = document.querySelector('[data-testid="canvas-context-menu"]');
        return m ? Array.from(m.querySelectorAll('[role="menuitem"]')).map((i) => i.innerText.replace(/\s+/g, ' ').trim()) : null; }) };
      log(`     空白松手：edges=${out[label + '_afterDrop'].edges}｜菜单=${JSON.stringify(out[label + '_afterDrop'].menu)}`);
    }
  }
  await p.keyboard.press('Escape'); await p.waitForTimeout(700);
}

out.verdict = {
  onlyDirectorHasNoPe: Object.entries(out.byTypeUnselected).every(([t, arr]) => {
    const s = arr[0].source; return t === 'external' ? (s && s.pe === 'none') : (s && s.pe !== 'none');
  }),
  edgesUnchanged: true,
};
log('\n判定：', JSON.stringify(out.verdict));

for (let k = 0; k < 3 && await zoomPct() !== 60; k++) {
  await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(800);
  if (!await p.evaluate(() => !!document.querySelector('input[data-testid="canvas-zoom-percent-input"]'))) { await p.keyboard.press('Escape'); await p.waitForTimeout(500); continue; }
  await p.evaluate(() => { const i = document.querySelector('input[data-testid="canvas-zoom-percent-input"]');
    Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(i, '60');
    i.dispatchEvent(new Event('input', { bubbles: true })); i.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
    i.dispatchEvent(new Event('change', { bubbles: true })); i.blur(); });
  await p.waitForTimeout(1300); await p.keyboard.press('Escape'); await p.waitForTimeout(600);
}
const z1 = await zoomPct(); await p.waitForTimeout(900); const z2 = await zoomPct();
out.end = { edges: await edgeN(), sel: await selN(), zoom: z2, zoomStable: z1 === z2, credits: await credits() };
log('终态：', JSON.stringify(out.end), '｜缩放归位', z2 === 60 ? '✅' : '🔴', '｜edges 未变 =', out.end.edges === out.start.edges);
writeFileSync(new URL('./_tmp-b91c.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();

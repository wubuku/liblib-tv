// 批次 94 · A：把「时间线只有 1 个连接手柄」从**观察**升级成**契约**。
//
// 本页第 41 行写「连接手柄只有 **1** 个（主体节点是 2 个），方向性更强」——
// **没说清两件事**：
//   ① 留下的是哪一个（入边 target 还是出边 source）？
//   ② 少掉的那个是**被隐藏**（在 DOM 里、`opacity:0`）还是**结构上就没有**？
//
// 🔑 **弹药来自批次 91**：20+ 节点清点里，`flow-node-source-handle` 比
//     `flow-node-target-handle` **少一个**，唯一缺的就是时间线节点。
//     批次 91 还钉了「手柄元素本体 `pe` 恒为 `none`，热区在 `::before`」——
//     所以「能不能拖」要读伪元素，不能读元素本体。
//
// ⇒ **可证伪预测 P1a**：两个时间线节点（`时间线 1` 基线 + `时间线 2` 别人建的）
//   都**只有 target**、**没有 source 元素**（不是隐藏）。
// ⇒ **P1b**：留下的那个 target 的 `::before` 是 `pe: auto`（真的能当落点）。
// ⇒ **P1c**：选中的时间线**只有 before ⊕**、没有 after ⊕（批次 71 的说法在今天仍成立）。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
const selN = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const credits = async () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-commerce-entry"]'); return e ? e.getAttribute('aria-label') : null; });
const zoomPct = async () => p.evaluate(() => { const e = document.querySelector('button[aria-label^="Zoom options"]'); return e ? Number((e.getAttribute('aria-label').match(/(\d+)%/) || [])[1]) : null; });
const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const setZoom = async (t0) => { for (let t = 1; t <= 3; t++) { if (await zoomPct() === t0) return true;
  await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(800);
  const has = await p.evaluate(() => !!document.querySelector('input[data-testid="canvas-zoom-percent-input"]'));
  if (!has) { await p.keyboard.press('Escape'); await p.waitForTimeout(500); continue; }
  await p.evaluate((v) => { const i = document.querySelector('input[data-testid="canvas-zoom-percent-input"]');
    Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(i, String(v));
    i.dispatchEvent(new Event('input', { bubbles: true })); i.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
    i.dispatchEvent(new Event('change', { bubbles: true })); i.blur(); }, t0);
  await p.waitForTimeout(1500); await p.keyboard.press('Escape'); await p.waitForTimeout(800);
  const a = await zoomPct(); await p.waitForTimeout(900); const c = await zoomPct();
  if (a === t0 && a === c) return true; } return false; };
const scaleNow = async () => { const rd = () => p.evaluate(() => { const vp = document.querySelector('.react-flow__viewport');
    const m = (vp ? (vp.style.transform || '') : '').match(/scale\(([-\d.]+)\)/); return m ? Number(m[1]) : null; });
  const a = await rd(); await p.waitForTimeout(500); const c = await rd(); return a !== null && a === c ? a : null; };
const probe = (id) => p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return { gone: true };
  const r = n.getBoundingClientRect();
  const inVp = r.left >= 0 && r.top >= 0 && r.right <= 1280 && r.bottom <= 720;
  let pt = null;
  for (let fx = 0.03; fx <= 0.97 && !pt; fx += 0.03) for (let fy = 0.03; fy <= 0.97 && !pt; fy += 0.03) {
    const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
    if (x < 0 || y < 0 || x > 1280 || y > 720) continue;
    const el = document.elementFromPoint(x, y);
    if (el && el.closest('.react-flow__node') === n) pt = { x, y }; }
  return { pt, inVp, box: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}` }; }, id);

/** 一个节点的手柄/⊕ 全量读数（伪元素一起读 —— 批次 91 的教训） */
const readNode = (id, sc) => p.evaluate(({ i, s }) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return { gone: true };
  const r = {};
  for (const k of ['source', 'target']) {
    const e = n.querySelector(`[data-testid="flow-node-${k}-handle"]`);
    if (!e) { r[k] = null; continue; }        // ← 「结构上就没有」与「隐藏」在这里分道
    const q = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    const bef = getComputedStyle(e, '::before');
    r[k] = { box: `${Math.round(q.width)}×${Math.round(q.height)}`, elPe: cs.pointerEvents, elOp: cs.opacity,
      beforePe: bef.pointerEvents, beforeSize: `${bef.width}×${bef.height}`,
      canvas: s ? `${Math.round(q.width / s)}×${Math.round(q.height / s)}` : null,
      center: [Math.round(q.x + q.width / 2), Math.round(q.y + q.height / 2)] };
  }
  r.plus = Array.from(n.querySelectorAll('[data-testid$="connection-menu-button"]')).map((e) => e.getAttribute('aria-label'));
  r.sel = String(n.className).includes(' selected');
  return r;
}, { i: id, s: sc });

out.start = { nodes: (await ids()).length, sel: await selN(), credits: await credits(), zoom: await zoomPct() };
log('起点：', JSON.stringify(out.start));

// 画布上的时间线节点清单
out.timelines = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node'))
  .filter((n) => /timeline/.test(String(n.className || '')))
  .map((n) => ({ id: n.getAttribute('data-id'), aria: n.getAttribute('aria-label') })));
log('时间线节点：', JSON.stringify(out.timelines));

// ── 未选中态：逐个读 ──
let sc = await scaleNow();
out.unselected = {};
for (const t of out.timelines) { out.unselected[t.id] = await readNode(t.id, sc);
  log(`  ${t.aria}｜source=${out.unselected[t.id].source ? '有' : '🔴 无元素'}｜target=${out.unselected[t.id].target ? out.unselected[t.id].target.box : '无'}｜⊕ ${out.unselected[t.id].plus.length}`); }

// ── 选中态：逐个选（前置断言） ──
out.selected = {};
for (const t of out.timelines) {
  let ok = false;
  for (const z of [await zoomPct(), 100, 200, 400, 800]) { if (!await setZoom(z)) continue;
    const pr = await probe(t.id); if (!pr.pt) continue;
    await p.mouse.click(pr.pt.x, pr.pt.y); await p.waitForTimeout(1100);
    const s = await selN(); const who = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
    if (s === '1' && who[0] === t.id) { ok = true; log(`  选中 ${t.aria} @${await zoomPct()}%（视口内=${pr.inVp}）`); break; }
    await p.keyboard.press('Escape'); await p.waitForTimeout(500); }
  if (!ok) { out.selected[t.id] = { VOID: '选不中' }; log(`  ⚠️ ${t.aria} 选不中 ⇒ 记 VOID`); await p.keyboard.press('Escape'); continue; }
  sc = await scaleNow();
  out.selected[t.id] = await readNode(t.id, sc);
  const r = out.selected[t.id];
  log(`     source=${r.source ? `${r.source.box} elPe=${r.source.elPe} ::before pe=${r.source.beforePe} ${r.source.beforeSize} canvas=${r.source.canvas}` : '🔴 结构上无'}`);
  log(`     target=${r.target ? `${r.target.box} elPe=${r.target.elPe} ::before pe=${r.target.beforePe} ${r.target.beforeSize} canvas=${r.target.canvas}` : '无'}`);
  log(`     ⊕ ${r.plus.length} 个：${JSON.stringify(r.plus)}`);
  await p.keyboard.press('Escape'); await p.waitForTimeout(700);
}

out.verdict = {};
for (const t of out.timelines) {
  const s = out.selected[t.id] || out.unselected[t.id];
  if (!s || s.VOID || s.gone) { out.verdict[t.id] = 'VOID'; continue; }
  out.verdict[t.id] = { noSourceElement: s.source === null, targetPresent: !!s.target,
    targetBeforePe: s.target?.beforePe, plus: s.plus, plusOnlyBefore: s.plus.length === 1 && /before/.test(s.plus[0] || '') };
}
log('\n判定：', JSON.stringify(out.verdict));

if (await selN() !== '0') { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
await setZoom(60);
out.end = { nodes: (await ids()).length, sel: await selN(), zoom: await zoomPct(), credits: await credits() };
log('终态：', JSON.stringify(out.end), '｜缩放归位', (await zoomPct()) === 60 ? '✅' : '🔴');
writeFileSync(new URL('./_tmp-b94a.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();

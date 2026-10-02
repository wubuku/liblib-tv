// 批次 82 · K：测前置的**第三层**——「选中与否」和「焦点在不在画布」是**两件事**。
//
// j 轮三格前置都成立了（selected:true、selCount:1），G / V / F 却**全部零变化**。
// 逐条看日志，`focusWhere` 全是 **`BODY`** —— 点标题行把「选中」做出来了，
// 但**焦点没落在画布上**，落到 body 去了。
// ⇒ 页面写「G 必须先选中节点才会给提示」，我这次**选中后仍然一个提示都没有**。
//    这不是推翻页面，是**我的前置只做了一半**：批次 77 早就记过
//    「节点选中 ≠ 焦点在画布」，我这轮又只满足了前一半。
//
// 🔑 **正解是框选**：mousedown 起点落在 `.react-flow__pane` 上、mouseup 也在 pane，
//    于是**焦点天然留在画布**，同时矩形罩住的节点被选中。
//    一举同时满足「1 选中」+「焦点在画布」——页面第 219 行推荐的也是框选。
//
// 本轮四格，全部用**当场读的 scale** 换算坐标：
//   G@B'  框选 1 个 → 按 G     （判定：选中后到底给不给「此快捷键当前不可用」）
//   F@B'  框选 1 个 → 按 F     （判定：文本节点上开不开全屏编辑器）
//   V@B'  框选 1 个 → 按 V     （判定：切不切工具）
//   F@A   0 选中 + 画布焦点 → 按 F（判定：页面声称的「完全静默」）
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport, keyGuard, pressLetter } from './jimeng-safe-keys.mjs';
const LEDGER = new URL('./jimeng-ephemeral-ledger.json', import.meta.url);
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
const mine = [];
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
const selCount = () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const zoomLabel = () => p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'));
const zoomPct = async () => { const l = await zoomLabel(); return l ? Number((l.match(/(\d+)%/) || [])[1]) : null; };
const dockBtn = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]');
  return e ? { aria: e.getAttribute('aria-label'), pressed: e.getAttribute('aria-pressed') } : null; });
const toast = () => p.evaluate(() => { const c = Array.from(document.querySelectorAll('div,span'))
    .filter((x) => /此快捷键当前不可用/.test((x.innerText || '').trim()) && x.children.length <= 2);
  const e = c.sort((a, b2) => b2.getBoundingClientRect().width - a.getBoundingClientRect().width)[0];
  if (!e) return null; const r = e.getBoundingClientRect();
  return { box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`, text: (e.innerText || '').trim() }; });
const visCount = () => p.evaluate(() => { let n = 0;
  for (const e of document.querySelectorAll('*')) { const r = e.getBoundingClientRect(); if (r.width > 0 && r.height > 0) n++; } return n; });
const fsDialog = () => p.evaluate(() => { const e = document.querySelector('[text-editor-fullscreen-dialog]'); if (!e) return null;
  const r = e.getBoundingClientRect(); return `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`; });
/** Agent 抽屉：🔴 关闭态 = 匹配 1 个 / 有面积 1 个；打开态 = 19~20 个。j 轮把这两个数写反了。 */
const agentState = () => p.evaluate(() => { const els = Array.from(document.querySelectorAll('[data-testid^="canvas-agent-"]'));
  return { total: els.length, withArea: els.filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; }).length,
    pmAnywhere: document.querySelectorAll('.ProseMirror[contenteditable="true"]').length,
    pmInNode: document.querySelectorAll('.react-flow__node .ProseMirror[contenteditable="true"]').length }; });
const readScale = async () => { const rd = () => p.evaluate(() => { const vp = document.querySelector('.react-flow__viewport');
    const m = (vp ? (vp.style.transform || '') : '').match(/scale\(([-\d.]+)\)/); return m ? Number(m[1]) : null; });
  const a = await rd(); await p.waitForTimeout(500); const c = await rd(); return { scale: a, stable: a !== null && a === c }; };
const setZoom = async (target) => { for (let t = 1; t <= 3; t++) {
    if (await zoomPct() === target) return { ok: true, how: 'already' };
    await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(800);
    const seen = await p.evaluate(() => { const i = document.querySelector('input[data-testid="canvas-zoom-percent-input"]'); return i ? i.value : null; });
    if (seen === null) { await p.keyboard.press('Escape'); await p.waitForTimeout(500); continue; }
    await p.evaluate((v) => { const i = document.querySelector('input[data-testid="canvas-zoom-percent-input"]');
      Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(i, String(v));
      i.dispatchEvent(new Event('input', { bubbles: true })); i.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
      i.dispatchEvent(new Event('change', { bubbles: true })); i.blur(); }, target);
    await p.waitForTimeout(1300); await p.keyboard.press('Escape'); await p.waitForTimeout(600);
    const a = await zoomPct(); await p.waitForTimeout(900); const c = await zoomPct();
    if (a === c && a === target) return { ok: true, how: 'input', pct: a }; }
  return { ok: false, pct: await zoomPct() }; };
const clickPane = async () => { const e = await p.evaluate(() => { const pane = document.querySelector('.react-flow__pane'); if (!pane) return null;
    for (let y = 110; y < 660; y += 20) for (let x = 210; x < 1240; x += 28) { const h = document.elementFromPoint(x, y); if (h && pane.contains(h)) return { x, y }; }
    return null; });
  if (!e) return null; await p.mouse.click(e.x, e.y); await p.waitForTimeout(650); return e; };

/** 🔑 框选：起落点都在 `.react-flow__pane` 上 ⇒ 焦点留在画布，同时选中目标节点。 */
const marqueeSelect = async (id) => {
  const sc = await readScale();
  const geo = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return null;
    const r = n.getBoundingClientRect(); return { x: r.x, y: r.y, w: r.width, h: r.height }; }, id);
  if (!geo) return { ok: false, why: '节点不在' };
  const pad = Math.max(40, Math.round(30 * sc.scale));
  const x0 = Math.round(geo.x - pad), y0 = Math.round(geo.y - pad);
  const x1 = Math.round(geo.x + geo.w + pad), y1 = Math.round(geo.y + geo.h + pad);
  const startOk = await p.evaluate(([x, y]) => { const pane = document.querySelector('.react-flow__pane');
    const h = document.elementFromPoint(x, y); return !!(pane && h && pane.contains(h)); }, [x0, y0]);
  if (!startOk) return { ok: false, why: `起点 ${x0},${y0} 不在 pane 上`, geo, pad };
  await p.mouse.move(x0, y0); await p.mouse.down();
  for (let k = 1; k <= 6; k++) { await p.mouse.move(Math.round(x0 + (x1 - x0) * k / 6), Math.round(y0 + (y1 - y0) * k / 6)); await p.waitForTimeout(70); }
  await p.mouse.up(); await p.waitForTimeout(900);
  const sel = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); return /(^|\s)selected(\s|$)/.test(n.className); }, id);
  const g = await keyGuard(p);
  return { ok: sel, from: `${x0},${y0}`, to: `${x1},${y1}`, pad, scale: sc.scale, selected: sel,
    selCount: await selCount(), focusWhere: g.where, focusOnCanvas: /Canvas|react-flow/i.test(g.where),
    agent: await agentState() };
};

try {
  out.zoom = await setZoom(60); log('缩放', JSON.stringify(out.zoom));
  out.agentBefore = await agentState(); log('Agent 前置', JSON.stringify(out.agentBefore));
  // 🔴 j 轮的教训：关闭态是 withArea=1，不是 0。判据写反会把「关」按成「开」。
  if (out.agentBefore.withArea > 5) { await p.keyboard.press('Meta+Slash'); await p.waitForTimeout(1400);
    out.agentClosed = await agentState(); log('强制关', JSON.stringify(out.agentClosed)); }

  const pre = await ids();
  const rail = await p.evaluate(() => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
    .find((x) => /^文本$/.test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
    const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  for (let k = 0; k < 2; k++) { await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(3200); }
  const made = (await ids()).filter((x) => !pre.includes(x));
  log('新建', made.length, made.join(' '), '缩放=', await zoomPct());
  if (made.length < 2) throw new Error('新建不足：' + made.length);
  mine.push(...made);

  out.keys = {};
  const runKey = async (name, id, letter, waits) => {
    const rec = {};
    try {
      await clickPane();
      if (id) { const m = await marqueeSelect(id); rec.pre = m;
        if (!m.ok) rec.void = '框选前置不成立'; else if (!m.focusOnCanvas) rec.void = '框选后焦点不在画布'; }
      else { const g = await keyGuard(p); rec.pre = { ok: true, selCount: await selCount(), focusWhere: g.where, focusOnCanvas: /Canvas|react-flow/i.test(g.where), agent: await agentState() }; }
      if (!rec.void) {
        const g = await keyGuard(p); rec.guardSafe = g.safe; rec.preFocus = g.where;
        rec.before = { sel: await selCount(), vis: await visCount(), zoom: await zoomLabel(), dock: await dockBtn(), fs: await fsDialog(), agent: (await agentState()).withArea };
        await pressLetter(p, letter);
        for (const d of waits) { await p.waitForTimeout(d); const t = await toast(); if (t) { rec.toast = t; rec.toastAfterMs = d; break; } }
        if (!rec.toast) rec.toast = null; rec.sampledToMs = waits.reduce((a, x) => a + x, 0);
        rec.after = { sel: await selCount(), vis: await visCount(), zoom: await zoomLabel(), dock: await dockBtn(), fs: await fsDialog(), agent: (await agentState()).withArea };
        rec.changed = Object.fromEntries(Object.keys(rec.before)
          .map((k) => [k, JSON.stringify(rec.before[k]) === JSON.stringify(rec.after[k]) ? '同' : `${JSON.stringify(rec.before[k])}→${JSON.stringify(rec.after[k])}`])
          .filter(([, v]) => v !== '同'));
      }
    } catch (e) { rec.error = e.message; }
    out.keys[name] = rec; log(`${name} →`, JSON.stringify(rec));
  };
  await runKey("G@B'", made[0], 'g', [300, 700, 1500]);
  await runKey("F@B'", made[0], 'f', [400, 900]);
  await p.keyboard.press('Escape'); await p.waitForTimeout(1000);
  out.fsAfterEsc = await fsDialog();
  await runKey("V@B'", made[1], 'v', [500]);
  await runKey('F@A', null, 'f', [300, 700, 1500]);
} catch (e) { out.error = e.message; console.error('ABORT:', e.message); }
finally {
  for (let i = 0; i < 2; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(400); }
  out.zoomFinal = await setZoom(60);
  out.end = { status: await status(), zoom: await zoomLabel(), agent: await agentState(), leftover: (await ids()).filter((x) => mine.includes(x)) };
  log('终态', JSON.stringify(out.end));
  try { const led = JSON.parse(readFileSync(LEDGER, 'utf8'));
    const add = mine.filter((x) => !led.ids.includes(x));
    if (add.length) { led.ids = [...new Set([...led.ids, ...add])].sort();
      led.per_batch = { ...(led.per_batch || {}), 82: [...new Set([...(led.per_batch?.['82'] || []), ...mine])] };
      writeFileSync(LEDGER, JSON.stringify(led, null, 1)); } } catch {}
  writeFileSync(new URL('./_tmp-b82k.json', import.meta.url), JSON.stringify(out, null, 1));
  await b.close();
}

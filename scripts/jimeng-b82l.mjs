// 批次 82 · L：补最后两格 —— 「**恰好 1 个**文本节点 + 焦点在画布」下的 F。
//
// k 轮用 pad=40 框选，**罩住了 3 个节点**（我建的 2 个 + 一个基线节点），
// 于是 F 零反应。页面第 139 行写的是「**文本** → F → `text-editor-fullscreen-dialog` 1280×720」，
// 那是**单选**场景。⇒ k 轮的「F 静默」不能直接用来推翻页面，
//    得先排除「多选导致 F 不工作」这个混淆变量。
//
// 本轮把 pad 收到最小（只包住目标节点四角，起落点仍须在 `.react-flow__pane` 上），
// 断言 `selCount === 1`，然后按 F、看全屏编辑器。
// 顺带做**反向对照**：同一个节点先单选按 F（应有全屏编辑器），
// 再**再加选一个**按 F（若无 ⇒ 多选是 F 的隐藏前置）。
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
const toast = () => p.evaluate(() => { const c = Array.from(document.querySelectorAll('div,span'))
    .filter((x) => /此快捷键当前不可用/.test((x.innerText || '').trim()) && x.children.length <= 2);
  const e = c.sort((a, b2) => b2.getBoundingClientRect().width - a.getBoundingClientRect().width)[0];
  if (!e) return null; const r = e.getBoundingClientRect();
  return { box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`, text: (e.innerText || '').trim() }; });
const visCount = () => p.evaluate(() => { let n = 0;
  for (const e of document.querySelectorAll('*')) { const r = e.getBoundingClientRect(); if (r.width > 0 && r.height > 0) n++; } return n; });
const fsDialog = () => p.evaluate(() => { const e = document.querySelector('[text-editor-fullscreen-dialog]');
  if (!e) return null; const r = e.getBoundingClientRect();
  const close = e.querySelector('[aria-label*="full-screen"], [aria-label*="Close"]');
  const cr = close ? close.getBoundingClientRect() : null;
  return { box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
    title: (e.querySelector('h1,h2,h3,[class*="itle"]') || {}).innerText || null,
    closeAria: close ? close.getAttribute('aria-label') : null,
    closeBox: cr ? `${Math.round(cr.width)}x${Math.round(cr.height)}@${Math.round(cr.x)},${Math.round(cr.y)}` : null }; });
const agentState = () => p.evaluate(() => { const els = Array.from(document.querySelectorAll('[data-testid^="canvas-agent-"]'));
  return { withArea: els.filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; }).length,
    pmAnywhere: document.querySelectorAll('.ProseMirror[contenteditable="true"]').length }; });
const readScale = async () => { const rd = () => p.evaluate(() => { const vp = document.querySelector('.react-flow__viewport');
    const m = (vp ? (vp.style.transform || '') : '').match(/scale\(([-\d.]+)\)/); return m ? Number(m[1]) : null; });
  const a = await rd(); await p.waitForTimeout(500); const c = await rd(); return { scale: a, stable: a !== null && a === c }; };
const setZoom = async (target) => { for (let t = 1; t <= 3; t++) {
    if (await zoomPct() === target) return { ok: true, how: 'already' };
    await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(800);
    if (!await p.evaluate(() => !!document.querySelector('input[data-testid="canvas-zoom-percent-input"]'))) {
      await p.keyboard.press('Escape'); await p.waitForTimeout(500); continue; }
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

/** 框选，pad 由调用方给；起落点必须落在 pane 上。 */
const marquee = async (id, padPx) => {
  const sc = await readScale();
  const geo = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return null;
    const r = n.getBoundingClientRect(); return { x: r.x, y: r.y, w: r.width, h: r.height }; }, id);
  if (!geo) return { ok: false, why: '节点不在' };
  const pad = Math.round(padPx);
  const x0 = Math.round(geo.x - pad), y0 = Math.round(geo.y - pad);
  const x1 = Math.round(geo.x + geo.w + pad), y1 = Math.round(geo.y + geo.h + pad);
  const startOk = await p.evaluate(([x, y]) => { const pane = document.querySelector('.react-flow__pane');
    const h = document.elementFromPoint(x, y); return !!(pane && h && pane.contains(h)); }, [x0, y0]);
  if (!startOk) return { ok: false, why: `起点 ${x0},${y0} 不在 pane 上`, geo };
  await p.mouse.move(x0, y0); await p.mouse.down();
  for (let k = 1; k <= 6; k++) { await p.mouse.move(Math.round(x0 + (x1 - x0) * k / 6), Math.round(y0 + (y1 - y0) * k / 6)); await p.waitForTimeout(70); }
  await p.mouse.up(); await p.waitForTimeout(900);
  const g = await keyGuard(p);
  return { ok: true, from: `${x0},${y0}`, to: `${x1},${y1}`, pad, scale: sc.scale,
    selCount: await selCount(), focusWhere: g.where, focusOnCanvas: /Canvas|react-flow/i.test(g.where) };
};

try {
  out.zoom = await setZoom(60); log('缩放', JSON.stringify(out.zoom));
  const ab = await agentState();
  if (ab.withArea > 5) { await p.keyboard.press('Meta+Slash'); await p.waitForTimeout(1400); log('关抽屉', JSON.stringify(await agentState())); }

  const pre = await ids();
  const rail = await p.evaluate(() => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
    .find((x) => /^文本$/.test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
    const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(3400);
  const made = (await ids()).filter((x) => !pre.includes(x));
  log('新建', made.length, made.join(' '), '缩放=', await zoomPct());
  if (made.length < 1) throw new Error('新建失败');
  mine.push(...made);
  const one = made[0];

  // pad 逐步收紧，直到 selCount 恰好 = 1
  out.padSearch = [];
  let got = null;
  for (const pad of [24, 14, 8, 4, 2]) {
    await clickPane();
    const m = await marquee(one, pad);
    const sc = m.ok ? Number(m.selCount) : -1;
    out.padSearch.push({ pad, ...m });
    log(`  pad=${pad}`, JSON.stringify(m));
    if (m.ok && m.focusOnCanvas && sc === 1) { got = { pad, m }; break; }
  }
  out.singleSelect = got;
  if (!got) { out.verdict = '没能框出恰好 1 个选中'; }

  out.keys = {};
  if (got) {
    // ① 单选 + 焦点在画布 → F
    {
      const rec = { pre: got.m };
      const g = await keyGuard(p); rec.guardSafe = g.safe;
      rec.before = { sel: await selCount(), vis: await visCount(), fs: await fsDialog() };
      await pressLetter(p, 'f');
      for (const d of [400, 900, 1600]) { await p.waitForTimeout(d); const t = await toast(); if (t) { rec.toast = t; rec.toastAfterMs = d; break; } }
      if (!rec.toast) rec.toast = null; rec.sampledToMs = 2900;
      rec.after = { sel: await selCount(), vis: await visCount(), fs: await fsDialog() };
      out.keys['F@1sel'] = rec; log('F@1sel →', JSON.stringify(rec));
      await p.keyboard.press('Escape'); await p.waitForTimeout(1200);
      out.fsAfterEsc = { fs: await fsDialog(), sel: await selCount() };
      log('Esc 后', JSON.stringify(out.fsAfterEsc));
    }
    // ② 反向对照：pad 放宽到罩住多个 → F
    {
      await clickPane();
      const m = await marquee(one, 40);
      const rec = { pre: m };
      rec.before = { sel: await selCount(), vis: await visCount(), fs: await fsDialog() };
      await pressLetter(p, 'f');
      for (const d of [400, 900, 1600]) { await p.waitForTimeout(d); const t = await toast(); if (t) { rec.toast = t; rec.toastAfterMs = d; break; } }
      if (!rec.toast) rec.toast = null; rec.sampledToMs = 2900;
      rec.after = { sel: await selCount(), vis: await visCount(), fs: await fsDialog() };
      out.keys['F@multi'] = rec; log('F@multi →', JSON.stringify(rec));
      await p.keyboard.press('Escape'); await p.waitForTimeout(1000);
    }
  }
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
  writeFileSync(new URL('./_tmp-b82l.json', import.meta.url), JSON.stringify(out, null, 1));
  await b.close();
}

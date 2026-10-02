// 批次 82 · M：补「F @ 恰好 1 选中 + 焦点在画布」这一格。
//
// l 轮的死局：pad 从 24 一路收到 2，`selCount` **恒为 2**。
// 原因不是 pad 不够小，而是**这块画布的节点本来就大面积交叠**——
// 基线三连「文本 1 [480,240] / 文本 2 [520,278.75] / 文本 3 [560,319.38]」
// 各自 320×320 canvas，矩形彼此盖住。⇒ **框选在��块画布上拿不到「恰好 1 个」**。
//
// 🔑 换减法而不是加法：**框选罩住一片 → 再 Shift+点其中一个**。
//    页面第 208-213 行早就写明 Shift+点选是**标准 toggle**
//    （点已选中的节点 = 取消选中它，实测 2 → 1）。
//    这样既用上了**框选**（焦点留在画布）又用上了 **toggle**（减到 1 个），
//    两个前置条件同时成立。
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
  const close = e.querySelector('[aria-label*="full-screen"],[aria-label*="Close"]'); const cr = close ? close.getBoundingClientRect() : null;
  return { box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
    closeAria: close ? close.getAttribute('aria-label') : null,
    closeBox: cr ? `${Math.round(cr.width)}x${Math.round(cr.height)}@${Math.round(cr.x)},${Math.round(cr.y)}` : null }; });
const agentState = () => p.evaluate(() => { const els = Array.from(document.querySelectorAll('[data-testid^="canvas-agent-"]'));
  return { withArea: els.filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; }).length,
    pmAnywhere: document.querySelectorAll('.ProseMirror[contenteditable="true"]').length }; });
const readScale = async () => { const rd = () => p.evaluate(() => { const vp = document.querySelector('.react-flow__viewport');
    const m = (vp ? (vp.style.transform || '') : '').match(/scale\(([-\d.]+)\)/); return m ? Number(m[1]) : null; });
  const a = await rd(); await p.waitForTimeout(500); const c = await rd(); return { scale: a, stable: a !== null && a === c }; };
const setZoom = async (t0) => { for (let t = 1; t <= 3; t++) { if (await zoomPct() === t0) return { ok: true, how: 'already' };
    await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(800);
    if (!await p.evaluate(() => !!document.querySelector('input[data-testid="canvas-zoom-percent-input"]'))) { await p.keyboard.press('Escape'); await p.waitForTimeout(500); continue; }
    await p.evaluate((v) => { const i = document.querySelector('input[data-testid="canvas-zoom-percent-input"]');
      Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(i, String(v));
      i.dispatchEvent(new Event('input', { bubbles: true })); i.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
      i.dispatchEvent(new Event('change', { bubbles: true })); i.blur(); }, t0);
    await p.waitForTimeout(1300); await p.keyboard.press('Escape'); await p.waitForTimeout(600);
    const a = await zoomPct(); await p.waitForTimeout(900); const c = await zoomPct();
    if (a === c && a === t0) return { ok: true, how: 'input', pct: a }; }
  return { ok: false, pct: await zoomPct() }; };
const clickPane = async () => { const e = await p.evaluate(() => { const pane = document.querySelector('.react-flow__pane'); if (!pane) return null;
    for (let y = 110; y < 660; y += 20) for (let x = 210; x < 1240; x += 28) { const h = document.elementFromPoint(x, y); if (h && pane.contains(h)) return { x, y }; }
    return null; });
  if (!e) return null; await p.mouse.click(e.x, e.y); await p.waitForTimeout(650); return e; };

try {
  out.zoom = await setZoom(60); log('缩放', JSON.stringify(out.zoom));
  const ab = await agentState();
  if (ab.withArea > 5) { await p.keyboard.press('Meta+Slash'); await p.waitForTimeout(1400); log('关抽屉', JSON.stringify(await agentState())); }
  const pre0 = await ids();
  const rail = await p.evaluate(() => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
    .find((x) => /^文本$/.test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
    const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(3400);
  const made = (await ids()).filter((x) => !pre0.includes(x));
  log('新建', made.length, made.join(' '), '缩放=', await zoomPct());
  if (made.length < 1) throw new Error('新建失败');
  mine.push(...made);
  const one = made[0];

  const sc = await readScale();
  // ① 框选罩一片（pad=40）
  await clickPane();
  const geo = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); const r = n.getBoundingClientRect();
    return { x: r.x, y: r.y, w: r.width, h: r.height }; }, one);
  const pad = 40;
  const x0 = Math.round(geo.x - pad), y0 = Math.round(geo.y - pad), x1 = Math.round(geo.x + geo.w + pad), y1 = Math.round(geo.y + geo.h + pad);
  const startOk = await p.evaluate(([x, y]) => { const pane = document.querySelector('.react-flow__pane'); const h = document.elementFromPoint(x, y); return !!(pane && h && pane.contains(h)); }, [x0, y0]);
  out.marquee = { from: `${x0},${y0}`, to: `${x1},${y1}`, startOk, scale: sc.scale };
  if (startOk) {
    await p.mouse.move(x0, y0); await p.mouse.down();
    for (let k = 1; k <= 6; k++) { await p.mouse.move(Math.round(x0 + (x1 - x0) * k / 6), Math.round(y0 + (y1 - y0) * k / 6)); await p.waitForTimeout(70); }
    await p.mouse.up(); await p.waitForTimeout(900);
  }
  out.afterMarquee = { sel: await selCount(), focusWhere: (await keyGuard(p)).where };
  log('框选后', JSON.stringify(out.afterMarquee));

  // ② Shift+点其中一个，把它 toggle 掉 ⇒ 剩 1
  const title = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); const r = n.getBoundingClientRect();
    for (let k = -70; k <= 4; k += 3) for (const f of [0.25, 0.5, 0.75]) { const x = Math.round(r.x + r.width * f), y = Math.round(r.y + Math.round(k * 0.6));
      if (x < 0 || y < 0 || y > 716) continue; const h = document.elementFromPoint(x, y);
      if (h && n.contains(h) && (h.innerText || h.getAttribute('aria-label'))) return { x, y, txt: (h.innerText || '').trim().slice(0, 12) }; }
    return null; }, one);
  out.titlePoint = title;
  if (title) {
    await p.keyboard.down('Shift'); await p.mouse.click(title.x, title.y); await p.keyboard.up('Shift');
    await p.waitForTimeout(900);
  }
  const g1 = await keyGuard(p);
  out.afterShift = { sel: await selCount(), focusWhere: g1.where, focusOnCanvas: /Canvas|react-flow/i.test(g1.where),
    stillSelected: await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); return /(^|\s)selected(\s|$)/.test(n.className); }, one) };
  log('Shift toggle 后', JSON.stringify(out.afterShift));

  // ③ 若正好 1 选中且焦点在画布 → 按 F
  out.keys = {};
  if (Number(out.afterShift.sel) === 1) {
    const rec = { pre: out.afterShift };
    if (!g1.safe) rec.void = 'keyGuard 拒绝';
    else {
      rec.before = { sel: await selCount(), vis: await visCount(), fs: await fsDialog() };
      await pressLetter(p, 'f');
      for (const d of [400, 900, 1600]) { await p.waitForTimeout(d); const t = await toast(); if (t) { rec.toast = t; rec.toastAfterMs = d; break; } }
      if (!rec.toast) rec.toast = null; rec.sampledToMs = 2900;
      rec.after = { sel: await selCount(), vis: await visCount(), fs: await fsDialog() };
    }
    out.keys['F@1'] = rec; log('F@1 →', JSON.stringify(rec));
    await p.keyboard.press('Escape'); await p.waitForTimeout(1300);
    out.fsAfterEsc = { fs: await fsDialog(), sel: await selCount(), pmInNode: await p.evaluate(() => document.querySelectorAll('.react-flow__node .ProseMirror[contenteditable="true"]').length) };
    log('Esc 后', JSON.stringify(out.fsAfterEsc));
  } else out.verdict = `Shift toggle 后仍是 ${out.afterShift.sel} 选中，放弃 F@1 这一格`;
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
  writeFileSync(new URL('./_tmp-b82m.json', import.meta.url), JSON.stringify(out, null, 1));
  await b.close();
}

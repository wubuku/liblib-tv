// 批次 78 · K：补上文本节点的同法对照 + 拍最终配图。
// b78j 的视频读数已经拿到（handle DIV 34.09×68.17 屏上 @S=0.568085 ⇒ 60.00×120.01 canvas），
// 但配图守卫把「并集 bbox 的角上没被任何后代矩形覆盖」判成 HOLE 而中止 ⇒ 文本节点没跑到。
// 这次修守卫口径：**HOLE 不再一律判负** —— bbox 角上本就可以是空的（标题在上、手柄在左，
// 两者不重叠，bbox 左上角天然没人覆盖）。真正会污染图的是**带语义的可见 UI**：
//   BUTTON / INPUT / FORM / TEXTAREA / 有非空 aria-label 的元素，且不属于本节点 ⇒ 判负。
// 除数一律取当场真实 scale（读两次相同才算静止），绝不写死 0.6。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';
const BASE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const LEDGER = new URL('./jimeng-ephemeral-ledger.json', import.meta.url);
const SHOTS = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const esc = async (n = 1) => { for (let i = 0; i < n; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(450); } };
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
const mine = [];
const scaleOf = () => p.evaluate(() => { const v = document.querySelector('.react-flow__viewport');
  const m = /matrix\(([-\d.]+)/.exec(getComputedStyle(v).transform); return m ? +(+m[1]).toFixed(6) : null; });
const labelOf = () => p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'));
const settle = async () => { for (let i = 0; i < 15; i++) { const a = await scaleOf(); await p.waitForTimeout(200); const c = await scaleOf();
  if (a === c) return { stable: true, scale: c, tries: i + 1, label: await labelOf() }; } return { stable: false, scale: await scaleOf() }; };
const setZoom = async (pct) => { await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(700);
  const sl = 'input[data-testid=canvas-zoom-percent-input]';
  if (!(await p.$(sl))) { await p.keyboard.press('Escape'); await p.waitForTimeout(400); return; }
  await p.fill(sl, String(pct)); await p.keyboard.press('Enter'); await p.waitForTimeout(1500); };
const mk = async (label) => { const pre = await ids();
  const rail = await p.evaluate((L) => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
    .find((x) => new RegExp('^' + L + '$').test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
    if (!el) return null; const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; }, label);
  if (!rail) throw new Error('找不到 rail 按钮：' + label);
  await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(3000);
  const c = (await ids()).filter((x) => !pre.includes(x));
  if (c.length !== 1) throw new Error('新建异常 ' + label + '：' + JSON.stringify(c));
  mine.push(c[0]); return c[0]; };
const delById = async (id) => { for (let a = 1; a <= 3; a++) { if (!(await ids()).includes(id)) return '✅';
    const pt = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return null;
      const r = n.getBoundingClientRect();
      for (const f of [[0.5, 0.5], [0.5, 0.2], [0.25, 0.5], [0.75, 0.5], [0.5, 0.8]]) { const x = Math.round(r.x + r.width * f[0]), y = Math.round(r.y + r.height * f[1]);
        const h = document.elementFromPoint(x, y); if (h && n.contains(h) && !h.closest('[role="menu"]')) return { x, y }; } return null; }, id);
    if (!pt) return '🔴 不在屏上';
    await p.mouse.click(pt.x, pt.y, { button: 'right' }); await p.waitForTimeout(1000);
    await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"],[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
      const it = m && Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || '')); if (it) it.click(); });
    await p.waitForTimeout(1500); }
  return (await ids()).includes(id) ? '🔴 仍在' : '✅'; };
const measure = (id, kind) => p.evaluate(([v, k]) => {
  const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return { missing: true };
  if (!/(^|\s)selected(\s|$)/.test(n.className)) return { notSelected: true, cls: n.className };
  const m = /matrix\(([-\d.]+)/.exec(getComputedStyle(document.querySelector('.react-flow__viewport')).transform);
  const S = m ? +(+m[1]).toFixed(6) : null; if (S === null) return { noScale: true };
  const r = n.getBoundingClientRect();
  const cv = (el) => { if (!el) return null; const b = el.getBoundingClientRect();
    return { screen: [+b.width.toFixed(2), +b.height.toFixed(2)], canvas: [+(b.width / S).toFixed(2), +(b.height / S).toFixed(2)],
      at: [Math.round(b.x - r.x), Math.round(b.y - r.y)] }; };
  const counterVar = getComputedStyle(n).getPropertyValue('--octo-canvas-node-chrome-counter-scale').trim();
  return { kind: k, scale: S, counterVar, counterIsReciprocal: Math.abs(+counterVar - 1 / S) < 1e-6,
    nodeRect: cv(n), surface: cv(n.querySelector('[data-testid=video-flow-node-surface]') || n.firstElementChild),
    handleDivBefore: cv(n.querySelector('[data-testid=flow-node-target-handle]')),
    handleDivAfter: cv(n.querySelector('[data-testid=flow-node-source-handle]')),
    plusBefore: cv(n.querySelector('[data-testid=flow-node-target-connection-menu-button]')),
    plusAfter: cv(n.querySelector('[data-testid=flow-node-source-connection-menu-button]')),
    title: cv(n.querySelector('[data-testid=flow-node-title]')),
    rename: cv(n.querySelector('button[aria-label^="Rename"]')),
    tagBtn: cv(n.querySelector('[data-testid=flow-node-selected-tag]')) };
}, [id, kind]);
try {
  await setZoom(60);
  const z0 = await settle(); log('开场', JSON.stringify(z0)); out.z0 = z0;
  if (!z0.stable) throw new Error('开场缩放未静止');

  // ① 视频节点：读数 + 配图
  const v = await mk('视频');
  const zv = await settle(); log('视频 缩放', JSON.stringify(zv)); out.zv = zv;
  if (!zv.stable) throw new Error('缩放未静止 ⇒ VOID');
  out.video = await measure(v, '视频'); log('视频读数', JSON.stringify(out.video));
  if (out.video.notSelected) throw new Error('未选中 ⇒ VOID');
  const shot = await p.evaluate((id) => {
    const n = document.querySelector(`.react-flow__node[data-id="${id}"]`); const r = n.getBoundingClientRect();
    const vis = Array.from(n.querySelectorAll('*')).filter((x) => { const b = x.getBoundingClientRect();
      return b.width > 1 && b.height > 1 && getComputedStyle(x).display !== 'none'; });
    const u = vis.map((x) => x.getBoundingClientRect()).reduce((a, b) => ({ x0: Math.min(a.x0, b.x), y0: Math.min(a.y0, b.y), x1: Math.max(a.x1, b.right), y1: Math.max(a.y1, b.bottom) }),
      { x0: r.x, y0: r.y, x1: r.right, y1: r.bottom });
    const pad = 10;
    const L = Math.max(0, Math.round(u.x0 - pad)), T = Math.max(0, Math.round(u.y0 - pad));
    const R = Math.min(innerWidth, Math.round(u.x1 + pad)), B = Math.min(innerHeight, Math.round(u.y1 + pad));
    const intr = Array.from(document.querySelectorAll('.react-flow__node')).filter((o) => o.getAttribute('data-id') !== id)
      .map((o) => ({ id: o.getAttribute('data-id'), r: o.getBoundingClientRect() }))
      .filter(({ r: o }) => o.x < R && o.right > L && o.y < B && o.bottom > T).map(({ id }) => id);
    const bad = [];
    for (let y = T + 2; y < B; y += 5) for (let x = L + 2; x < R; x += 5) {
      const h = document.elementFromPoint(x, y); if (!h || n.contains(h)) continue;
      const cs = getComputedStyle(h);
      const semantic = /^(BUTTON|INPUT|FORM|TEXTAREA|SELECT|A)$/.test(h.tagName) || (h.getAttribute('aria-label') || '').trim().length > 0;
      if (semantic && cs.display !== 'none' && cs.visibility !== 'hidden' && +cs.opacity > 0.01) {
        const t = `${h.tagName}#${h.getAttribute('data-testid') || '-'}[${(h.getAttribute('aria-label') || h.innerText || '').trim().split('\n')[0].slice(0, 18)}]`;
        if (!bad.some((c) => c.t === t)) bad.push({ t, at: `${x},${y}` }); }
    }
    const want = ['[data-testid=flow-node-title]', '[data-testid=video-node-empty]',
      '[data-testid=flow-node-target-connection-menu-button]', '[data-testid=flow-node-source-connection-menu-button]']
      .map((s) => ({ s, el: n.querySelector(s) })).filter((o) => o.el);
    const outside = want.filter((o) => { const w = o.el.getBoundingClientRect(); return w.x < L || w.right > R || w.y < T || w.bottom > B; }).map((o) => o.s);
    return { pad, clip: { x: L, y: T, width: R - L, height: B - T }, intruding: intr, bad, outside, wantCount: want.length,
      union: [Math.round(u.x0), Math.round(u.y0), Math.round(u.x1 - u.x0), Math.round(u.y1 - u.y0)],
      node: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
  }, v);
  out.shot = shot; log('shot', JSON.stringify(shot));
  if (shot.intruding.length) throw new Error('clip 内有他人节点');
  if (shot.bad.length) throw new Error('clip 内有语义 UI：' + shot.bad.map((c) => `${c.t}@${c.at}`).join(' / '));
  if (shot.wantCount < 1) throw new Error('wantCount=0 ⇒ 断言空转');
  if (shot.outside.length) throw new Error('没裁进来：' + shot.outside.join(','));
  await p.screenshot({ path: new URL('78-empty-video-node-card.png', SHOTS).pathname, clip: shot.clip });
  log('📷 78-empty-video-node-card.png', shot.clip.width + 'x' + shot.clip.height);

  // ② 文本节点：同法对照
  await esc(2);
  const t = await mk('文本');
  const zt = await settle(); log('文本 缩放', JSON.stringify(zt)); out.zt = zt;
  out.text = await measure(t, '文本'); log('文本读数', JSON.stringify(out.text));
  if (out.video.handleDivBefore && out.text.handleDivBefore) out.compare = {
    videoHandleCanvas: out.video.handleDivBefore.canvas, textHandleCanvas: out.text.handleDivBefore.canvas,
    same: JSON.stringify(out.video.handleDivBefore.canvas) === JSON.stringify(out.text.handleDivBefore.canvas),
    videoScale: out.video.scale, textScale: out.text.scale,
    legacyDivBy06: out.video.handleDivBefore.screen.map((x) => +(x / 0.6).toFixed(1)),
    plusSame: JSON.stringify(out.video.plusBefore?.canvas) === JSON.stringify(out.text.plusBefore?.canvas),
  };
  log('对照', JSON.stringify(out.compare));
} catch (e) { out.error = e.message; console.error('ABORT:', e.message); }
finally {
  await esc(3);
  for (const id of mine) log('清理', id, await delById(id));
  await esc(3);
  for (let t2 = 0; t2 < 3; t2++) { const z = await labelOf(); if (z && z.includes('60%')) break; await setZoom(60); }
  const zf = await settle();
  const cp = await p.evaluate(() => Object.fromEntries(Array.from(document.querySelectorAll('.react-flow__node')).map((e) => {
    const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(e.style.transform || '');
    return [e.getAttribute('data-id'), m ? [Math.round(parseFloat(m[1]) * 100) / 100, Math.round(parseFloat(m[2]) * 100) / 100] : null]; })));
  const dev = []; for (const [id, b2] of Object.entries(BASE.nodes)) { const c = cp[id]; const d = c && b2.canvas ? [Math.round((c[0] - b2.canvas[0]) * 100) / 100, Math.round((c[1] - b2.canvas[1]) * 100) / 100] : 'MISSING';
    if (d === 'MISSING' || (Array.isArray(d) && (Math.abs(d[0]) > 0.01 || Math.abs(d[1]) > 0.01))) dev.push([id, d]); }
  const st = await p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
  out.end = { status: st, zoomLabel: await labelOf(), scale: zf.scale, deviation: dev };
  log('终态', JSON.stringify(out.end));
  try { const led = JSON.parse(readFileSync(LEDGER, 'utf8')); const add = mine.filter((x) => !led.ids.includes(x));
    if (add.length) { led.ids = [...new Set([...led.ids, ...add])].sort();
      led.per_batch = { ...(led.per_batch || {}), 78: [...new Set([...(led.per_batch?.['78'] || []), ...mine])] };
      writeFileSync(LEDGER, JSON.stringify(led, null, 1)); } } catch {}
  writeFileSync(new URL('./_tmp-b78k.json', import.meta.url), JSON.stringify(out, null, 1));
  await b.close();
}

// 批次 78 · G：最终重拍。三处修正都来自前几轮的判据错误。
// ① **裁切基准**：`.react-flow__node` 矩形**不等于**节点的视觉范围 ——
//    标题行在它上方 33px（relTop=−33），两个 ⊕ 手柄左右各外伸 ~17px。
//    视频 1 实测：DOM 矩形 192×341，可见后代并集 227×375。
//    前两版按 DOM 矩形裁 ⇒ 标题被裁掉、顶部还漏进半截 ⇒ 图上像「有个说不清的东西」。
//    现在按**可见后代并集**裁。
// ② **守卫放行自己人**：上一版守卫把「clip 内、节点矩形外」的非背景元素全判为杂物，
//    结果把这个节点自己的标题行/重命名按钮判成杂物（ABORT 是对的，但判据过宽）。
//    正确口径：命中元素必须是纯背景 **或本节点的后代**。
// ③ **量之前先断言缩放已静止**：b78e 读到的 scale 0.568085 是缩放动画中途的瞬时值，
//    那一轮所有 canvas 尺寸因此偏小 5.6% —— 判据错，不是被测物变了。
//    现在任何读数前都断言 |scale−0.6| < 1e-6，不成立就等，不成立就 VOID。
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
const esc = async (n = 1) => { for (let i = 0; i < n; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(400); } };
const zoomOf = () => p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'));
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
const scaleOf = () => p.evaluate(() => { const v = document.querySelector('.react-flow__viewport');
  const m = /matrix\(([-\d.]+)/.exec(getComputedStyle(v).transform); return m ? +(+m[1]).toFixed(6) : null; });
/** 等缩放静止：连续两次读数相同才返回。判据：|scale−0.6|<1e-6。 */
const settleZoom = async (want = 0.6) => {
  for (let i = 0; i < 12; i++) {
    const s1 = await scaleOf(); await p.waitForTimeout(220); const s2 = await scaleOf();
    if (s1 === s2 && Math.abs(s2 - want) < 1e-6) return { ok: true, scale: s2, tries: i + 1 };
  }
  return { ok: false, scale: await scaleOf() };
};
const log = (...a) => console.log(a.join(' '));
const out = { startedAt: new Date().toISOString() };
let mine = null;
try {
  const z0 = await settleZoom(); log('开场缩放', JSON.stringify(z0), '|', await status());
  if (!z0.ok) throw new Error('开场缩放未静止 ⇒ 读数作废(VOID)');
  const pre = await ids();
  const rail = await p.evaluate(() => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
    .find((x) => /^视频$/.test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
    const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(2600);
  const nowIds = await ids();
  const created = nowIds.filter((x) => !pre.includes(x));
  if (created.length !== 1) throw new Error('新建异常：' + JSON.stringify(created));
  mine = created[0]; log('新建', mine);

  const plan = await p.evaluate((v) => {
    const others = Array.from(document.querySelectorAll('.react-flow__node'))
      .filter((n) => n.getAttribute('data-id') !== v).map((n) => n.getBoundingClientRect());
    const r = document.querySelector(`.react-flow__node[data-id="${v}"]`).getBoundingClientRect();
    // 视觉包围盒比 DOM 矩形大一圈（标题在上、手柄在两侧），这里按 DOM 矩形先留足余量
    for (let y = 300; y < 640; y += 20) for (let x = 320; x < 1200; x += 20) {
      const box = { x: x - r.width / 2, y: y - r.height / 2, right: x + r.width / 2, bottom: y + r.height / 2 };
      if (box.x - 50 < 8 || box.y - 50 < 8 || box.right + 50 > innerWidth - 8 || box.bottom + 50 > innerHeight - 8) continue;
      if (others.some((o) => box.x - 50 < o.right + 12 && box.right + 50 + 12 > o.x && box.y - 50 < o.bottom + 12 && box.bottom + 50 + 12 > o.y)) continue;
      return { x, y };
    } return null;
  }, mine);
  if (!plan) throw new Error('找不到落点');
  const grip = await p.evaluate((v) => {
    const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); const r = n.getBoundingClientRect();
    const cx = Math.round(r.x + r.width * 0.22), cy = Math.round(r.y + r.height * 0.5);
    const hit = document.elementFromPoint(cx, cy);
    return { cx, cy, ok: !!hit && n.contains(hit), hit: hit ? `${hit.tagName}.${(hit.getAttribute('class') || '').slice(0, 40)}` : 'null' };
  }, mine);
  if (!grip.ok) throw new Error('抓手落点不属于本节点');
  await p.mouse.move(grip.cx, grip.cy); await p.mouse.down();
  for (let i = 1; i <= 10; i++) { await p.mouse.move(Math.round(grip.cx + (plan.x - grip.cx) * i / 10), Math.round(grip.cy + (plan.y - grip.cy) * i / 10)); await p.waitForTimeout(70); }
  await p.mouse.up(); await p.waitForTimeout(1200);
  out.plan = plan;

  // —— 前置：选中 + 无组 + 缩放静止，三条全成立才允许读数
  const pre1 = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`);
    return { selected: /(^|\s)selected(\s|$)/.test(n.className), group: !!document.querySelector('.react-flow__node-group') }; }, mine);
  const z1 = await settleZoom();
  log('前置', JSON.stringify(pre1), '缩放', JSON.stringify(z1));
  if (!pre1.selected) throw new Error('未保持选中 ⇒ VOID');
  if (pre1.group) throw new Error('存在组节点 ⇒ VOID');
  if (!z1.ok) throw new Error('缩放未静止 ⇒ VOID');

  // —— 读数（这次 scale 已钉在 0.6）
  const probe = await p.evaluate((v) => {
    const n = document.querySelector(`.react-flow__node[data-id="${v}"]`);
    const S = 0.6, cv = (x) => +(x / S).toFixed(1);
    const r = n.getBoundingClientRect();
    const e = n.querySelector('[data-testid=video-node-empty]');
    const svg = e && e.querySelector('svg');
    const rel = (sel) => { const el = n.querySelector(sel); if (!el) return null; const b = el.getBoundingClientRect();
      return { screen: `${Math.round(b.width)}x${Math.round(b.height)}`, canvas: `${cv(b.width)}x${cv(b.height)}`,
        relTop: Math.round(b.y - r.y), relLeft: Math.round(b.x - r.x) }; };
    const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2);
    const hit = document.elementFromPoint(cx, cy);
    const chain = []; for (let x = hit; x && x !== document.body; x = x.parentElement) {
      chain.push(`${x.tagName}${x.getAttribute('data-testid') ? '#' + x.getAttribute('data-testid') : ''}|cursor=${getComputedStyle(x).cursor}`);
      if (chain.length > 5) break; }
    const vis = Array.from(n.querySelectorAll('*')).filter((x) => { const b = x.getBoundingClientRect();
      return b.width > 1 && b.height > 1 && getComputedStyle(x).display !== 'none'; });
    const u = vis.map((x) => x.getBoundingClientRect()).reduce((a, b) => ({
      x0: Math.min(a.x0, b.x), y0: Math.min(a.y0, b.y), x1: Math.max(a.x1, b.right), y1: Math.max(a.y1, b.bottom) }),
      { x0: r.x, y0: r.y, x1: r.right, y1: r.bottom });
    return {
      nodeRectScreen: `${Math.round(r.width)}x${Math.round(r.height)}`, nodeRectCanvas: `${cv(r.width)}x${cv(r.height)}`,
      visualUnionScreen: `${Math.round(u.x1 - u.x0)}x${Math.round(u.y1 - u.y0)}`,
      visualUnionCanvas: `${cv(u.x1 - u.x0)}x${cv(u.y1 - u.y0)}`,
      title: rel('[data-testid=flow-node-title]'), beforeBtn: rel('[data-testid=flow-node-target-connection-menu-button]'),
      afterBtn: rel('[data-testid=flow-node-source-connection-menu-button]'), empty: rel('[data-testid=video-node-empty]'),
      rename: rel('button[aria-label^="Rename"]'),
      emptyAria: e ? e.getAttribute('aria-label') : null, emptyInnerText: e ? JSON.stringify(e.innerText) : null,
      svgAttr: svg ? `${svg.getAttribute('width')}x${svg.getAttribute('height')} ${svg.getAttribute('data-icon')}` : null,
      svgAriaHidden: svg ? svg.getAttribute('aria-hidden') : null, svgCursor: svg ? getComputedStyle(svg).cursor : null,
      centerChain: chain, visibleCount: vis.length,
      statusText: (n.innerText || '').split('\n').filter(Boolean).slice(0, 3),
    };
  }, mine);
  out.probe = probe; log('读数', JSON.stringify(probe, null, 1));

  // —— 裁切守卫 v3：按可见后代并集；命中须是纯背景或本节点后代
  const clipInfo = await p.evaluate((v) => {
    const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); const r = n.getBoundingClientRect();
    const vis = Array.from(n.querySelectorAll('*')).filter((x) => { const b = x.getBoundingClientRect();
      return b.width > 1 && b.height > 1 && getComputedStyle(x).display !== 'none'; });
    const u = vis.map((x) => x.getBoundingClientRect()).reduce((a, b) => ({
      x0: Math.min(a.x0, b.x), y0: Math.min(a.y0, b.y), x1: Math.max(a.x1, b.right), y1: Math.max(a.y1, b.bottom) }),
      { x0: r.x, y0: r.y, x1: r.right, y1: r.bottom });
    const pad = 10;
    const L = Math.max(0, Math.round(u.x0 - pad)), T = Math.max(0, Math.round(u.y0 - pad));
    const R = Math.min(innerWidth, Math.round(u.x1 + pad)), B = Math.min(innerHeight, Math.round(u.y1 + pad));
    const intr = Array.from(document.querySelectorAll('.react-flow__node')).filter((o) => o.getAttribute('data-id') !== v)
      .map((o) => ({ id: o.getAttribute('data-id'), r: o.getBoundingClientRect() }))
      .filter(({ r: o }) => o.x < R && o.right > L && o.y < B && o.bottom > T).map(({ id }) => id);
    const bad = [];
    for (let y = T + 2; y < B; y += 6) for (let x = L + 2; x < R; x += 6) {
      const insideUnion = x >= u.x0 - 1 && x <= u.x1 + 1 && y >= u.y0 - 1 && y <= u.y1 + 1;
      const h = document.elementFromPoint(x, y); if (!h) continue;
      if (insideUnion) { if (!n.contains(h)) { const t = 'MISSING:' + h.tagName; if (!bad.some((c) => c.t === t)) bad.push({ t, at: `${x},${y}` }); } continue; }
      const okBg = h === document.body || h.classList.contains('react-flow') || h.classList.contains('react-flow__pane')
        || h.classList.contains('react-flow__renderer') || h.classList.contains('react-flow__viewport') || n.contains(h);
      if (!okBg) { const t = `CHROME:${h.tagName}${(h.getAttribute('aria-label') || h.innerText || '').trim().split('\n')[0].slice(0, 20)}`;
        if (!bad.some((c) => c.t === t)) bad.push({ t, at: `${x},${y}` }); }
    }
    const want = ['[data-testid=flow-node-title]', '[data-testid=video-node-empty]',
      '[data-testid=flow-node-target-connection-menu-button]', '[data-testid=flow-node-source-connection-menu-button]']
      .map((s) => ({ s, el: n.querySelector(s) })).filter((o) => o.el);
    const outside = want.filter((o) => { const w = o.el.getBoundingClientRect(); return w.x < L || w.right > R || w.y < T || w.bottom > B; }).map((o) => o.s);
    return { pad, clip: { x: L, y: T, width: R - L, height: B - T }, intruding: intr, bad, outside, wantCount: want.length };
  }, mine);
  out.clip = clipInfo; log('clip', JSON.stringify(clipInfo));
  if (clipInfo.intruding.length) throw new Error('clip 内有他人节点：' + clipInfo.intruding.join(','));
  if (clipInfo.bad.length) throw new Error('clip 守卫不过：' + clipInfo.bad.map((c) => `${c.t}@${c.at}`).join(' / '));
  if (clipInfo.wantCount < 1) throw new Error('wantCount=0 ⇒ 断言空转，不算通过');
  if (clipInfo.outside.length) throw new Error('以下元素没被裁进来：' + clipInfo.outside.join(','));
  await p.screenshot({ path: new URL('78-empty-video-node-card.png', SHOTS).pathname, clip: clipInfo.clip });
  log('📷 78-empty-video-node-card.png（按视觉包围盒裁 ' + clipInfo.clip.width + 'x' + clipInfo.clip.height + '，目标元素 ' + clipInfo.wantCount + ' 个全在内，他人节点 0，杂物 0）');
} catch (e) { out.error = e.message; console.error('ABORT:', e.message); }
finally {
  await esc(3);
  if (mine) {
    const box = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return null; const r = n.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + 14) }; }, mine);
    if (box) { await p.mouse.click(box.x, box.y, { button: 'right' }); await p.waitForTimeout(1000);
      await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"],[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
        const it = m && Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || '')); if (it) it.click(); });
      await p.waitForTimeout(1500); }
    log('清理', mine, (await ids()).includes(mine) ? '🔴 仍在' : '✅');
  }
  await esc(3);
  for (let t = 0; t < 3; t++) { const z = await zoomOf(); if (z && z.includes('60%')) break;
    await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(700);
    const sl = 'input[data-testid=canvas-zoom-percent-input]';
    if (await p.$(sl)) { await p.fill(sl, '60'); await p.keyboard.press('Enter'); await p.waitForTimeout(1100); } else { await p.keyboard.press('Escape'); await p.waitForTimeout(400); } }
  const zf = await settleZoom();
  const cp = await p.evaluate(() => Object.fromEntries(Array.from(document.querySelectorAll('.react-flow__node')).map((e) => {
    const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(e.style.transform || '');
    return [e.getAttribute('data-id'), m ? [Math.round(parseFloat(m[1]) * 100) / 100, Math.round(parseFloat(m[2]) * 100) / 100] : null]; })));
  const dev = []; for (const [id, b2] of Object.entries(BASE.nodes)) { const c = cp[id]; const d = c && b2.canvas ? [Math.round((c[0] - b2.canvas[0]) * 100) / 100, Math.round((c[1] - b2.canvas[1]) * 100) / 100] : 'MISSING';
    if (d === 'MISSING' || (Array.isArray(d) && (Math.abs(d[0]) > 0.01 || Math.abs(d[1]) > 0.01))) dev.push([id, d]); }
  out.end = { status: await status(), zoom: await zoomOf(), scaleSettled: zf, deviation: dev };
  log('终态', out.end.status, '| 缩放', out.end.zoom, JSON.stringify(zf), '| 偏离', JSON.stringify(dev));
  try { const led = JSON.parse(readFileSync(LEDGER, 'utf8')); if (mine && !led.ids.includes(mine)) { led.ids = [...new Set([...led.ids, mine])].sort(); writeFileSync(LEDGER, JSON.stringify(led, null, 1)); } } catch {}
  writeFileSync(new URL('./_tmp-b78g.json', import.meta.url), JSON.stringify(out, null, 1));
  await b.close();
}

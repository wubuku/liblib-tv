// 批次 80 · E：收尾两点。
// ① **真身 node-toolbar 的缩放无关性** —— b80b 量到 `0×0` 是因为
//    `[data-testid="node-toolbar"]` 在文档里有**两个**：一个 `.react-flow__renderer` 下的
//    `0×0` 常驻占位、一个真身 `192×40`。⇒ 单数选择器撞占位（老坑）。
//    本轮**按面积筛选**后再量 60% / 100% 两档。
// ② 补一张配图：文本节点右键菜单**实为 7 项**（页面正文只列了 6 项，漏「重做」），
//    而这一节原本**一张图都没有**。裁切守卫与批次 78 定下的口径一致。
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
const labelOf = () => p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'));
const scaleOf = () => p.evaluate(() => { const m = /matrix\(([-\d.]+)/.exec(getComputedStyle(document.querySelector('.react-flow__viewport')).transform); return m ? +(+m[1]).toFixed(6) : null; });
const settle = async () => { for (let i = 0; i < 15; i++) { const a = await scaleOf(); await p.waitForTimeout(200); const c = await scaleOf();
  if (a === c) return { scale: c, stable: true }; } return { scale: await scaleOf(), stable: false }; };
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
let mine = null;
const setZoom = async (pct) => { await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(700);
  const sl = 'input[data-testid=canvas-zoom-percent-input]';
  if (!(await p.$(sl))) { await p.keyboard.press('Escape'); await p.waitForTimeout(400); return; }
  await p.fill(sl, String(pct)); await p.keyboard.press('Enter'); await p.waitForTimeout(1400); };
try {
  const pre = await ids();
  const rail = await p.evaluate(() => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
    .find((x) => /^文本$/.test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
    const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(3000);
  const made = (await ids()).filter((x) => !pre.includes(x));
  if (made.length !== 1) throw new Error('新建异常');
  mine = made[0];
  const sel = await p.evaluate((v) => /(^|\s)selected(\s|$)/.test(document.querySelector(`.react-flow__node[data-id="${v}"]`).className), mine);
  log('新建', mine, '自动选中 =', sel);
  if (!sel) throw new Error('未选中 ⇒ 读数作废(VOID)');

  // ① 真身工具条 × 缩放（**按面积筛掉 0×0 占位**）
  out.toolbarByZoom = [];
  for (const pct of [60, 100, 60]) {
    await setZoom(pct);
    const zz = await settle();
    const r = await p.evaluate(() => {
      const all = Array.from(document.querySelectorAll('[data-testid="node-toolbar"]')).map((e) => { const b = e.getBoundingClientRect();
        return { box: `${b.width.toFixed(0)}x${b.height.toFixed(0)}@${Math.round(b.x)},${Math.round(b.y)}`, area: b.width * b.height,
          buttons: e.querySelectorAll('button,[role="button"]').length }; }).sort((a, c) => c.area - a.area);
      const real = all[0];
      return { count: all.length, real, realIsUsable: real && real.area > 1, all };
    });
    out.toolbarByZoom.push({ pct, scale: zz.scale, ...r });
    log(`node-toolbar @${pct}%`, 'scale', zz.scale, '→', JSON.stringify(r));
  }
  // ①2 菜单 × 缩放（**与工具条对照**：工具条实测随缩放变，菜单是 portal，预期不变）
  out.menuByZoom = [];
  for (const pct of [60, 100]) {
    await setZoom(pct);
    const zz = await settle();
    const q = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); const r = n.getBoundingClientRect();
      for (const f of [[0.5, 0.18], [0.3, 0.5], [0.7, 0.5], [0.5, 0.35], [0.5, 0.65]]) { const x = Math.round(r.x + r.width * f[0]), y = Math.round(r.y + r.height * f[1]);
        const h = document.elementFromPoint(x, y); if (h && n.contains(h) && !h.closest('[role="menu"]')) return { x, y }; } return null; }, mine);
    if (!q) { log('⚠️', pct + '% 右键落点找不到'); continue; }
    await p.mouse.click(q.x, q.y, { button: 'right' }); await p.waitForTimeout(1300);
    const m = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"],[role="menu"]')).filter((x) => x.getBoundingClientRect().width > 1).pop();
      if (!e) return null; const b = e.getBoundingClientRect();
      return { box: `${Math.round(b.width)}x${Math.round(b.height)}`, n: e.querySelectorAll('[role="menuitem"]').length }; });
    out.menuByZoom.push({ pct, scale: zz.scale, ...m });
    log(`右键菜单 @${pct}%`, 'scale', zz.scale, '→', JSON.stringify(m));
    await p.keyboard.press('Escape'); await p.waitForTimeout(700);   // ⚠️ 一次
  }
  await setZoom(60); const zs = await settle(); log('回到 60%', JSON.stringify(zs));

  // ② 右键菜单 + 配图
  const pt = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); const r = n.getBoundingClientRect();
    for (const f of [[0.5, 0.18], [0.3, 0.5], [0.7, 0.5], [0.5, 0.35], [0.5, 0.65]]) { const x = Math.round(r.x + r.width * f[0]), y = Math.round(r.y + r.height * f[1]);
      const h = document.elementFromPoint(x, y); if (h && n.contains(h) && !h.closest('[role="menu"]')) return { x, y }; } return null; }, mine);
  if (!pt) throw new Error('右键落点找不到');
  await p.mouse.click(pt.x, pt.y, { button: 'right' }); await p.waitForTimeout(1400);
  const menu = await p.evaluate(() => {
    const m = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"],[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
    if (!m) return { found: false };
    const r = m.getBoundingClientRect();
    return { found: true, box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
      aria: m.getAttribute('aria-label'),
      items: Array.from(m.querySelectorAll('[role="menuitem"]')).map((e) => ({ text: (e.innerText || '').split('\n')[0].trim(),
        disabled: e.getAttribute('aria-disabled') === 'true', cursor: getComputedStyle(e).cursor,
        srOnly: e.querySelector('.sr-only') ? (e.querySelector('.sr-only').textContent || '').trim().slice(0, 30) : null })) };
  });
  out.menu = menu; log('菜单', JSON.stringify(menu, null, 1));
  if (!menu.found) throw new Error('菜单没打开');
  if (menu.items.length < 7) throw new Error(`菜单只有 ${menu.items.length} 项，与预期 7 项不符 ⇒ 不拍图`);
  // 裁切：菜单 ∪ 节点可见后代并集；守卫只拦「带语义的、且不属本节点或本菜单」的可见元素
  const clip = await p.evaluate((v) => {
    const n = document.querySelector(`.react-flow__node[data-id="${v}"]`);
    const m = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"],[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
    const r = n.getBoundingClientRect(), mr = m.getBoundingClientRect();
    // 节点浮动工具条：**不在节点 DOM 内**（在 .react-flow__renderer 下），但它是本节点的浮层，
    // 必须纳入并集并放行 —— 否则守卫会把它当「外来语义 UI」判负（b80e 第一版就这样被拦下）。
    const tbs = Array.from(document.querySelectorAll('[data-testid="node-toolbar"]'))
      .map((e) => ({ e, b: e.getBoundingClientRect() })).filter((o) => o.b.width * o.b.height > 1)
      .sort((a, c) => c.b.width * c.b.height - a.b.width * a.b.height);
    const tb = tbs[0] || null;
    const vis = Array.from(n.querySelectorAll('*')).filter((e) => { const b = e.getBoundingClientRect();
      return b.width > 1 && b.height > 1 && getComputedStyle(e).display !== 'none'; });
    const u = vis.map((e) => e.getBoundingClientRect()).reduce((a, b) => ({ x0: Math.min(a.x0, b.x), y0: Math.min(a.y0, b.y), x1: Math.max(a.x1, b.right), y1: Math.max(a.y1, b.bottom) }),
      { x0: r.x, y0: r.y, x1: r.right, y1: r.bottom });
    const X0 = Math.min(u.x0, mr.x, tb ? tb.b.x : Infinity), Y0 = Math.min(u.y0, mr.y, tb ? tb.b.y : Infinity);
    const X1 = Math.max(u.x1, mr.right, tb ? tb.b.right : -Infinity), Y1 = Math.max(u.y1, mr.bottom, tb ? tb.b.bottom : -Infinity);
    const pad = 10;
    const L = Math.max(0, Math.round(X0 - pad)), T = Math.max(0, Math.round(Y0 - pad));
    const R = Math.min(innerWidth, Math.round(X1 + pad)), B = Math.min(innerHeight, Math.round(Y1 + pad));
    const intr = Array.from(document.querySelectorAll('.react-flow__node')).filter((o) => o.getAttribute('data-id') !== v)
      .map((o) => ({ id: o.getAttribute('data-id'), r: o.getBoundingClientRect() }))
      .filter(({ r: o }) => o.x < R && o.right > L && o.y < B && o.bottom > T).map(({ id }) => id);
    const bad = [];
    for (let y = T + 2; y < B; y += 5) for (let x = L + 2; x < R; x += 5) {
      const inU = x >= u.x0 - 1 && x <= u.x1 + 1 && y >= u.y0 - 1 && y <= u.y1 + 1;
      const inM = x >= mr.x - 1 && x <= mr.right + 1 && y >= mr.y - 1 && y <= mr.bottom + 1;
      const inTb = tb && x >= tb.b.x - 1 && x <= tb.b.right + 1 && y >= tb.b.y - 1 && y <= tb.b.bottom + 1;
      if (inU || inM || inTb) continue;
      const h = document.elementFromPoint(x, y); if (!h || n.contains(h) || m.contains(h) || (tb && tb.e.contains(h))) continue;
      const cs = getComputedStyle(h);
      const sem = /^(BUTTON|INPUT|FORM|TEXTAREA|SELECT|A)$/.test(h.tagName) || (h.getAttribute('aria-label') || '').trim().length > 0;
      if (sem && cs.display !== 'none' && cs.visibility !== 'hidden' && +cs.opacity > 0.01) {
        const t = `CHROME:${h.tagName}[${(h.getAttribute('aria-label') || h.innerText || '').trim().split('\n')[0].slice(0, 18)}]`;
        if (!bad.some((c) => c.t === t)) bad.push({ t, at: `${x},${y}` }); }
    }
    const wantItems = Array.from(m.querySelectorAll('[role="menuitem"]'));
    const outside = wantItems.map((e, i) => { const w = e.getBoundingClientRect(); return w.x < L || w.right > R || w.y < T || w.bottom > B ? i : -1; }).filter((i) => i >= 0);
    return { pad, clip: { x: L, y: T, width: R - L, height: B - T }, intruding: intr, bad, outside, itemCount: wantItems.length };
  }, mine);
  out.clip = clip; log('clip', JSON.stringify(clip));
  if (clip.intruding.length) throw new Error('clip 内有他人节点：' + clip.intruding.join(','));
  if (clip.bad.length) throw new Error('clip 内有语义 UI：' + clip.bad.map((c) => `${c.t}@${c.at}`).join(' / '));
  if (clip.itemCount < 7) throw new Error('菜单项没全在 clip 计数里');
  if (clip.outside.length) throw new Error('有菜单项没被裁进来：' + clip.outside.join(','));
  await p.screenshot({ path: new URL('80-text-node-context-menu.png', SHOTS).pathname, clip: clip.clip });
  log('📷 80-text-node-context-menu.png', clip.clip.width + 'x' + clip.clip.height, '| 菜单项', clip.itemCount, '个全在内');
} catch (e) { out.error = e.message; console.error('ABORT:', e.message); }
finally {
  await p.keyboard.press('Escape'); await p.waitForTimeout(800);
  if (mine) {
    for (let a = 1; a <= 3 && (await ids()).includes(mine); a++) {
      const q = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return null;
        const r = n.getBoundingClientRect();
        for (const f of [[0.5, 0.5], [0.5, 0.2], [0.25, 0.5], [0.75, 0.5], [0.5, 0.8]]) { const x = Math.round(r.x + r.width * f[0]), y = Math.round(r.y + r.height * f[1]);
          const h = document.elementFromPoint(x, y); if (h && n.contains(h) && !h.closest('[role="menu"]')) return { x, y }; } return null; }, mine);
      if (!q) break;
      await p.mouse.click(q.x, q.y, { button: 'right' }); await p.waitForTimeout(1000);
      await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"],[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
        const it = m && Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || '')); if (it) it.click(); });
      await p.waitForTimeout(1500);
    }
    log('清理', mine, (await ids()).includes(mine) ? '🔴 仍在' : '✅');
  }
  for (let t = 0; t < 3; t++) { const z = await labelOf(); if (z && z.includes('60%')) break; await setZoom(60); }
  const zf = await settle();
  const cp = await p.evaluate(() => Object.fromEntries(Array.from(document.querySelectorAll('.react-flow__node')).map((e) => {
    const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(e.style.transform || '');
    return [e.getAttribute('data-id'), m ? [Math.round(parseFloat(m[1]) * 100) / 100, Math.round(parseFloat(m[2]) * 100) / 100] : null]; })));
  const dev = []; for (const [id, b2] of Object.entries(BASE.nodes)) { const c = cp[id]; const d = c && b2.canvas ? [Math.round((c[0] - b2.canvas[0]) * 100) / 100, Math.round((c[1] - b2.canvas[1]) * 100) / 100] : 'MISSING';
    if (d === 'MISSING' || (Array.isArray(d) && (Math.abs(d[0]) > 0.01 || Math.abs(d[1]) > 0.01))) dev.push([id, d]); }
  out.end = { status: await status(), zoomLabel: await labelOf(), scale: zf.scale, deviation: dev };
  log('终态', JSON.stringify(out.end));
  try { const led = JSON.parse(readFileSync(LEDGER, 'utf8')); if (mine && !led.ids.includes(mine)) {
    led.ids = [...new Set([...led.ids, mine])].sort();
    led.per_batch = { ...(led.per_batch || {}), 80: [...new Set([...(led.per_batch?.['80'] || []), mine])] };
    writeFileSync(LEDGER, JSON.stringify(led, null, 1)); } } catch {}
  writeFileSync(new URL('./_tmp-b80e.json', import.meta.url), JSON.stringify(out, null, 1));
  await b.close();
}

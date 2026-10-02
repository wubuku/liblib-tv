// 批次 78 · J：换算基准的对照实验 + 最终配图。
// 起因（b78f/b78h/b78i 三轮）：缩放标签 = 真实 scale 四舍五入；而**每次新建节点，
// 画布都会自动缩小把新节点纳入视野**（100%→81%→70%→70%）。于是此前手册里
// 「屏上读数 ÷ 0.6」这个除数在选中态是错的：真实 scale 常常是 0.568085。
// 0.6/0.568085 = 1.0562 —— 正好是批次 72 那两个数之差：
//   旧记「320×320 类手柄 60×120，视频 56.8×113.6，**因类型而异**」
//   34.08/0.568085 = 60.0，68.16/0.568085 = 120.0 ⇒ **两者本来一样**。
// 本轮只做一件事：同一会话内用**同一套方法**量视频节点与文本节点，
// 除数一律取当场读到的真实 scale，验「手柄热区是否真的因类型而异」。
// 外加：按**视觉包围盒**（不是 DOM 矩形）拍最终配图。
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
/** 缩放静止 = 连续两次读数相同。注意：**不**预设目标值 —— 新建节点会改缩放，
 *  预设 0.6 正是前几轮误判的根源。 */
const settle = async () => { for (let i = 0; i < 15; i++) { const a = await scaleOf(); await p.waitForTimeout(200);
  const c = await scaleOf(); if (a === c) return { stable: true, scale: c, tries: i + 1, label: await labelOf() }; } return { stable: false, scale: await scaleOf() }; };
const setZoom = async (pct) => { await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(700);
  const sl = 'input[data-testid=canvas-zoom-percent-input]';
  if (!(await p.$(sl))) { await p.keyboard.press('Escape'); await p.waitForTimeout(400); return; }
  await p.fill(sl, String(pct)); await p.keyboard.press('Enter'); await p.waitForTimeout(1500); };
const mk = async (label) => {
  const pre = await ids();
  const rail = await p.evaluate((L) => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
    .find((x) => new RegExp('^' + L + '$').test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
    if (!el) return null; const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; }, label);
  if (!rail) throw new Error('找不到 rail 按钮：' + label);
  await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(3000);
  const c = (await ids()).filter((x) => !pre.includes(x));
  if (c.length !== 1) throw new Error('新建异常 ' + label + '：' + JSON.stringify(c));
  mine.push(c[0]); return c[0];
};
/** 只按 id 删，且删前用 elementFromPoint 确认落点真属于该节点（上一轮就是在中心右键结果删错/没删掉）。 */
const delById = async (id) => {
  for (let attempt = 1; attempt <= 3; attempt++) {
    if (!(await ids()).includes(id)) return '✅';
    const pt = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return null;
      const r = n.getBoundingClientRect();
      for (const f of [[0.5, 0.5], [0.5, 0.2], [0.25, 0.5], [0.75, 0.5], [0.5, 0.8]]) {
        const x = Math.round(r.x + r.width * f[0]), y = Math.round(r.y + r.height * f[1]);
        const h = document.elementFromPoint(x, y);
        if (h && n.contains(h) && !h.closest('[role="menu"]')) return { x, y };
      } return null; }, id);
    if (!pt) return '🔴 节点不在屏上';
    await p.mouse.click(pt.x, pt.y, { button: 'right' }); await p.waitForTimeout(1000);
    const hit = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`);
      const m = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"],[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
      if (!m) return { menu: false };
      const it = Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || ''));
      if (!it) return { menu: true, item: false, disabled: it === null };
      it.click(); return { menu: true, item: true, sel: n ? /(^|\s)selected(\s|$)/.test(n.className) : null }; }, id);
    await p.waitForTimeout(1500);
    log('  删除尝试', attempt, id, JSON.stringify(hit));
  }
  return (await ids()).includes(id) ? '🔴 仍在' : '✅';
};
/** 量一个「已选中」的节点。除数取当场真实 scale，绝不写死 0.6。 */
const measure = (id, kind) => p.evaluate(([v, k]) => {
  const n = document.querySelector(`.react-flow__node[data-id="${v}"]`);
  if (!n) return { missing: true };
  if (!/(^|\s)selected(\s|$)/.test(n.className)) return { notSelected: true, cls: n.className };  // 前置不成立 ⇒ VOID
  const vw = document.querySelector('.react-flow__viewport');
  const m = /matrix\(([-\d.]+)/.exec(getComputedStyle(vw).transform);
  const S = m ? +(+m[1]).toFixed(6) : null;
  if (S === null) return { noScale: true };
  const r = n.getBoundingClientRect();
  const pick = (sel) => { const el = n.querySelector(sel); if (!el) return null; const b = el.getBoundingClientRect();
    return { screen: [+b.width.toFixed(2), +b.height.toFixed(2)],
      canvas: [+(b.width / S).toFixed(2), +(b.height / S).toFixed(2)],
      at: [Math.round(b.x - r.x), Math.round(b.y - r.y)] }; };
  const cv = (el) => { const bb = el.getBoundingClientRect(); return { screen: [+bb.width.toFixed(2), +bb.height.toFixed(2)], canvas: [+(bb.width / S).toFixed(2), +(bb.height / S).toFixed(2)], at: [Math.round(bb.x - r.x), Math.round(bb.y - r.y)] }; };
  const before = n.querySelector('[data-testid=flow-node-target-connection-menu-button]');
  const after = n.querySelector('[data-testid=flow-node-source-connection-menu-button]');
  const surface = n.querySelector('[data-testid=video-flow-node-surface]') || n.firstElementChild;
  const counterVar = getComputedStyle(n).getPropertyValue('--octo-canvas-node-chrome-counter-scale').trim();
  return { kind: k, scale: S, counterVar, counterIsReciprocal: Math.abs(+counterVar - 1 / S) < 1e-6,
    nodeRectScreen: [+r.width.toFixed(2), +r.height.toFixed(2)], nodeRectCanvas: [+(r.width / S).toFixed(2), +(r.height / S).toFixed(2)],
    surface: surface ? cv(surface) : null,
    handleBefore: before ? cv(before) : null, handleAfter: after ? cv(after) : null,
    handleDivBefore: cv(n.querySelector('[data-testid=flow-node-target-handle]') || document.createElement('i')),
    title: pick('[data-testid=flow-node-title]'),
    empty: pick('[data-testid=video-node-empty]') || pick('[data-testid=audio-node-empty]') || pick('[data-testid=image-node-empty]'),
  };
}, [id, kind]);
try {
  await setZoom(60);
  const z0 = await settle(); log('开场', JSON.stringify(z0)); out.z0 = z0;
  if (!z0.stable) throw new Error('开场缩放未静止');

  // —— 视频节点：量 + 拍配图
  const v = await mk('视频');
  const zv = await settle(); log('建视频后缩放', JSON.stringify(zv)); out.zv = zv;
  if (!zv.stable) throw new Error('缩放未静止 ⇒ VOID');
  out.video = await measure(v, '视频'); log('视频读数', JSON.stringify(out.video, null, 1));
  if (out.video.notSelected) throw new Error('未选中 ⇒ VOID');

  // 配图：按可见后代并集裁；守卫允许本节点后代
  const clipInfo = await p.evaluate((id) => {
    const n = document.querySelector(`.react-flow__node[data-id="${id}"]`); const r = n.getBoundingClientRect();
    const vis = Array.from(n.querySelectorAll('*')).filter((x) => { const b = x.getBoundingClientRect();
      return b.width > 1 && b.height > 1 && getComputedStyle(x).display !== 'none'; });
    const u = vis.map((x) => x.getBoundingClientRect()).reduce((a, b) => ({ x0: Math.min(a.x0, b.x), y0: Math.min(a.y0, b.y), x1: Math.max(a.x1, b.right), y1: Math.max(a.y1, b.bottom) }),
      { x0: r.x, y0: r.y, x1: r.right, y1: r.bottom });
    const pad = 12;
    const L = Math.max(0, Math.round(u.x0 - pad)), T = Math.max(0, Math.round(u.y0 - pad));
    const R = Math.min(innerWidth, Math.round(u.x1 + pad)), B = Math.min(innerHeight, Math.round(u.y1 + pad));
    const intr = Array.from(document.querySelectorAll('.react-flow__node')).filter((o) => o.getAttribute('data-id') !== id)
      .map((o) => ({ id: o.getAttribute('data-id'), r: o.getBoundingClientRect() }))
      .filter(({ r: o }) => o.x < R && o.right > L && o.y < B && o.bottom > T).map(({ id }) => id);
    const bad = [];
    for (let y = T + 2; y < B; y += 6) for (let x = L + 2; x < R; x += 6) {
      const inU = x >= u.x0 - 1 && x <= u.x1 + 1 && y >= u.y0 - 1 && y <= u.y1 + 1;
      const h = document.elementFromPoint(x, y); if (!h) continue;
      if (inU) { if (!n.contains(h)) { const t = 'HOLE:' + h.tagName; if (!bad.some((c) => c.t === t)) bad.push({ t, at: `${x},${y}` }); } continue; }
      const ok = h === document.body || h.classList.contains('react-flow') || h.classList.contains('react-flow__pane')
        || h.classList.contains('react-flow__renderer') || h.classList.contains('react-flow__viewport') || n.contains(h);
      if (!ok) { const t = 'CHROME:' + h.tagName + (h.getAttribute('aria-label') || h.innerText || '').trim().split('\n')[0].slice(0, 18);
        if (!bad.some((c) => c.t === t)) bad.push({ t, at: `${x},${y}` }); }
    }
    const want = ['[data-testid=flow-node-title]', '[data-testid=video-node-empty]',
      '[data-testid=flow-node-target-connection-menu-button]', '[data-testid=flow-node-source-connection-menu-button]']
      .map((s) => ({ s, el: n.querySelector(s) })).filter((o) => o.el);
    const outside = want.filter((o) => { const w = o.el.getBoundingClientRect(); return w.x < L || w.right > R || w.y < T || w.bottom > B; }).map((o) => o.s);
    return { pad, clip: { x: L, y: T, width: R - L, height: B - T }, intruding: intr, bad, outside, wantCount: want.length,
      unionVsNode: { unionH: Math.round(u.y1 - u.y0), nodeH: Math.round(r.height), unionW: Math.round(u.x1 - u.x0), nodeW: Math.round(r.width) } };
  }, v);
  out.clip = clipInfo; log('clip', JSON.stringify(clipInfo));
  if (clipInfo.intruding.length) throw new Error('clip 内有他人节点');
  if (clipInfo.bad.length) throw new Error('clip 守卫不过：' + clipInfo.bad.map((c) => `${c.t}@${c.at}`).join(' / '));
  if (clipInfo.wantCount < 1) throw new Error('wantCount=0 ⇒ 断言空转');
  if (clipInfo.outside.length) throw new Error('没裁进来：' + clipInfo.outside.join(','));
  await p.screenshot({ path: new URL('78-empty-video-node-card.png', SHOTS).pathname, clip: clipInfo.clip });
  log('📷 78-empty-video-node-card.png', clipInfo.clip.width + 'x' + clipInfo.clip.height, '| 目标元素', clipInfo.wantCount, '个全在内');

  // —— 文本节点：同法对照，验「手柄热区是否因类型而异」
  await esc(2);
  const t = await mk('文本');
  const zt = await settle(); log('建文本后缩放', JSON.stringify(zt)); out.zt = zt;
  out.text = await measure(t, '文本'); log('文本读数', JSON.stringify(out.text, null, 1));
  if (out.video.handleBefore && out.text.handleBefore) {
    out.compare = {
      videoHandleCanvas: out.video.handleBefore.canvas, textHandleCanvas: out.text.handleBefore.canvas,
      same: out.video.handleBefore.canvas[0] === out.text.handleBefore.canvas[0] && out.video.handleBefore.canvas[1] === out.text.handleBefore.canvas[1],
      videoScale: out.video.scale, textScale: out.text.scale,
      legacyVideoWithDivBy06: [+(out.video.handleBefore.screen[0] / 0.6).toFixed(1), +(out.video.handleBefore.screen[1] / 0.6).toFixed(1)],
    };
    log('对照', JSON.stringify(out.compare));
  }
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
  const cred = await p.evaluate(() => (document.body.innerText.match(/积分[^0-9]{0,6}(\d+)/) || [])[1] || null);
  out.end = { status: st, zoomLabel: await labelOf(), scale: zf.scale, deviation: dev, credits: cred, leftover: mine.filter((x) => (cp[x] !== undefined)) };
  log('终态', JSON.stringify(out.end));
  try { const led = JSON.parse(readFileSync(LEDGER, 'utf8')); const add = mine.filter((x) => !led.ids.includes(x));
    if (add.length) { led.ids = [...new Set([...led.ids, ...add])].sort(); writeFileSync(LEDGER, JSON.stringify(led, null, 1)); }
    led.per_batch = { ...(led.per_batch || {}), 78: [...(led.per_batch?.['78'] || []), ...mine] }; writeFileSync(LEDGER, JSON.stringify(led, null, 1)); } catch {}
  writeFileSync(new URL('./_tmp-b78j.json', import.meta.url), JSON.stringify(out, null, 1));
  await b.close();
}

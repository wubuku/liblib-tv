// 批次 101 · c17 轮：把节点挪到**算出来**的无遮挡位置，再拍。
//
// c16 查实了鬼影的来历，而且**比预想的严重**：
//   · 鬼影 = `node_d4tjtpnatq`（时间线 2）的 `timeline-playback-clock` + `timeline-toolbar`
//   · **z-index：时间线 22 > 本节点 11** ⇒ 它是**压在本节点上面**的，不是「透上来」
//   · 本节点各层 `opacity` 全是 `1`，`backgroundColor` 全是 `rgba(0,0,0,0)`
//     ⇒ 半透明那条路走不通，**纯粹是 z 序被压**
//
// 🔑 **c15 的「可见判据」为什么漏了**：9×9 网格的采样 y 是 264 / 291 / 319……
//    鬼影在 **y≈280–290**，**正好落在两行采样之间**。
//    ⇒ **网格采样只能证明它采到的那几个点**。要判「整块区域干不干净」，
//      得把**所有他人节点的矩形**都算进来，而不是靠撒点。
//
// 本轮的做法：**不撒点，直接算** —— 遍历视口内所有空位，算出卡片放哪不会被任何他人节点矩形相交。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString(), selfId: 'node_fxhrsbbfrz' };
const SELF = out.selfId;
const SHOT = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);

// ---- 先等节点与 surface 都在（**c17 首跑撞到过瞬时读空**：脚本抛
//      「Cannot read properties of null」时 `n` 为 null，几秒后再查又好了 —— 共享画布在被人改动） ----
out.wait = await p.evaluate(async (i) => {
  const t0 = Date.now();
  while (Date.now() - t0 < 15000) {
    const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    if (n && n.querySelector('[data-testid="video-flow-node-surface"]')) return { ok: true, ms: Date.now() - t0 };
    await new Promise((r) => setTimeout(r, 250));
  }
  return { ok: false, ms: Date.now() - t0 };
}, SELF);
log('等节点就绪：', JSON.stringify(out.wait));
if (!out.wait.ok) { log('🔴 等不到 ⇒ 中止'); writeFileSync(new URL('./_tmp-b101c17.json', import.meta.url), JSON.stringify(out, null, 1)); await b.close(); process.exit(1); }

// ⚠️ **共享画布在被人持续改动**（节点数本轮 47 → 49 → 53），
//    React 会整树重渲染，`.react-flow__node[data-id=…]` 会**短暂消失**。
//    「等一次再查」不够 —— 必须**重试**。下面 `tryPlan()` 最多试 8 次。
const planFn = (i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { err: 'node-null' };
  const se = n.querySelector('[data-testid="video-flow-node-surface"]');
  const te = n.querySelector('[data-testid="flow-node-title"]');
  if (!se || !te) return { err: 'child-null', have: Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')).slice(0, 20) };
  const surf = se.getBoundingClientRect();
  const W = Math.round(surf.width), H = Math.round(surf.height);
  const TITLE = Math.round(surf.y - te.getBoundingClientRect().y);
  const M = 12;
  const bw = W + 2 * M, bh = H + TITLE + 2 * M;
  const others = Array.from(document.querySelectorAll('.react-flow__node'))
    .filter((e) => e !== n && !e.contains(n) && !n.contains(e))
    .map((e) => { const r = e.getBoundingClientRect();
      return { id: e.getAttribute('data-id'), aria: e.getAttribute('aria-label'), z: getComputedStyle(e).zIndex,
        x0: r.x, y0: r.y, x1: r.x + r.width, y1: r.y + r.height }; });
  const fits = (x, y) => {
    const bx0 = x - M, by0 = y - TITLE - M, bx1 = x + W + M, by1 = y + H + M;
    if (bx0 < 195 || by0 < 62 || bx1 > 1276 || by1 > 638) return { ok: false, why: '出可用区' };
    for (const o of others) {
      if (o.x0 < bx1 && o.x1 > bx0 && o.y0 < by1 && o.y1 > by0)
        return { ok: false, why: `撞 ${o.aria}(z=${o.z})`, id: o.id };
    }
    return { ok: true, box: [bx0, by0, bx1, by1] };
  };
  const cur = { x: Math.round(surf.x), y: Math.round(surf.y) };
  let best = null;
  for (let y = 80; y <= 620 - H; y += 4) for (let x = 210; x <= 1260 - W; x += 4) {
    const f = fits(x, y); if (!f.ok) continue;
    const d = Math.abs(x - cur.x) + Math.abs(y - cur.y);
    if (!best || d < best.d) best = { x, y, d, box: f.box };
  }
  return { W, H, TITLE, M, cur, card: `${cur.x},${cur.y} ${W}×${H}`,
    best, othersCount: others.length, othersZ: others.map((o) => `${o.aria}:z=${o.z}`).slice(0, 12) };
};
async function tryPlan() {
  for (let k = 0; k < 8; k++) {
    const r = await p.evaluate(planFn, SELF);
    if (!r.err) { r.tries = k + 1; return r; }
    if (k === 0) log('  第一次撞空：', JSON.stringify(r));
    await p.waitForTimeout(700);
  }
  return { err: 'gave-up' };
}
out.plan = await tryPlan();
if (out.plan.err) { log('🔴', out.plan.err, '⇒ 中止'); writeFileSync(new URL('./_tmp-b101c17.json', import.meta.url), JSON.stringify(out, null, 1)); await b.close(); process.exit(1); }
log('算落点用了', out.plan.tries, '次');
log('尺寸与当前位置：', JSON.stringify({ W: out.plan.W, H: out.plan.H, TITLE: out.plan.TITLE, cur: out.plan.cur, card: out.plan.card }));
log(`视口内他人节点 ${out.plan.othersCount} 个；z 序样例：`, JSON.stringify(out.plan.othersZ));
log('算出的无遮挡落点：', JSON.stringify(out.plan.best));
out.canPlace = !!out.plan.best;

// ---- 拖过去 ----
if (out.canPlace) {
  const grab = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const t = n.querySelector('[data-testid="flow-node-title"]'); const r = t.getBoundingClientRect();
    const x = Math.round(r.x + r.width * 0.08), y = Math.round(r.y + r.height / 2);
    const el = document.elementFromPoint(x, y);
    return { point: [x, y], hitTid: el ? el.getAttribute('data-testid') : null, insideSelf: !!(el && el.closest(`.react-flow__node[data-id="${i}"]`)) }; }, SELF);
  log('抓取点：', JSON.stringify(grab));
  if (grab.hitTid === 'flow-node-title' && grab.insideSelf) {
    const dx = out.plan.best.x - out.plan.cur.x;
    const dy = out.plan.best.y - out.plan.cur.y;
    log(`  拖动位移（屏上）：${dx},${dy}`);
    await p.mouse.move(grab.point[0], grab.point[1]); await p.waitForTimeout(450);
    await p.mouse.down(); await p.waitForTimeout(300);
    await p.mouse.move(grab.point[0] + Math.round(dx / 2), grab.point[1] + Math.round(dy / 2), { steps: 14 });
    await p.waitForTimeout(400);
    await p.mouse.move(grab.point[0] + dx, grab.point[1] + dy, { steps: 14 }); await p.waitForTimeout(500);
    await p.mouse.up(); await p.waitForTimeout(1400);
    out.afterMove = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
      const s = n.querySelector('[data-testid="video-flow-node-surface"]').getBoundingClientRect();
      return { transform: n.style.transform, surf: `${Math.round(s.x)},${Math.round(s.y)}`, sel: n.classList.contains('selected'),
        count: (document.body.innerText.match(/(\d+) nodes?/) || [])[1] }; }, SELF);
    log('拖后：', JSON.stringify(out.afterMove));
    out.movedOk = out.afterMove.surf === `${out.plan.best.x},${out.plan.best.y}`;
    log('  ⇒ 落在算出的位置？', out.movedOk);
  } else log('  🔴 抓取点不对 ⇒ 不拖');
}

// ---- 重新选中 + 起播到 ~2.5s ----
{
  const pt = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const s = n.querySelector('[data-testid="video-flow-node-surface"]').getBoundingClientRect();
    const x = Math.round(s.x + s.width / 2), y = Math.round(s.y + s.height * 0.2);
    const el = document.elementFromPoint(x, y);
    return { point: [x, y], insideSelf: !!(el && el.closest(`.react-flow__node[data-id="${i}"]`)), hitTag: el ? el.tagName : null }; }, SELF);
  log('重新选中落点：', JSON.stringify(pt));
  if (pt.insideSelf) { await p.mouse.move(pt.point[0], pt.point[1]); await p.waitForTimeout(350);
    await p.mouse.click(pt.point[0], pt.point[1]); }
  // 「选中即播」⇒ **不要**再点播放钮（c13 就是在这多 点了一发，结果拍成暂停态）
  await p.waitForTimeout(2500);
}
out.st = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const v = n.querySelector('video'); const c = n.querySelector('[data-testid="video-node-player-clock"]');
  return { ct: v ? v.currentTime : null, paused: v ? v.paused : null,
    clock: c ? c.innerText.replace(/\s+/g, ' ').trim() : null,
    toggle: (n.querySelector('[data-testid="video-node-playback-toggle"]') || {}).getAttribute?.('aria-label') || null,
    mute: (n.querySelector('[data-testid="video-node-mute-toggle"]') || {}).getAttribute?.('aria-label') || null,
    full: (n.querySelector('[data-testid="video-node-fullscreen-toggle"]') || {}).getAttribute?.('aria-label') || null }; }, SELF);
log('拍前状态：', JSON.stringify(out.st));

// ---- 裁切 + **不撒点**的守卫：遍历所有他人节点矩形 ----
out.crop = await p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const pick = ['flow-node-title', 'video-flow-node-surface', 'video-node-player-bar', 'image-primary-preview-viewport', 'video-hover-surface'];
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (const t of pick) { const e = n.querySelector(`[data-testid="${t}"]`); if (!e) continue;
    const r = e.getBoundingClientRect(); if (r.width === 0 || r.height === 0) continue;
    x0 = Math.min(x0, r.x); y0 = Math.min(y0, r.y); x1 = Math.max(x1, r.x + r.width); y1 = Math.max(y1, r.y + r.height); }
  const M = 12;
  const clip = { x: Math.max(0, Math.floor(x0 - M)), y: Math.max(0, Math.floor(y0 - M)), width: 0, height: 0 };
  clip.width = Math.ceil(Math.min(x1 - x0 + 2 * M, 1280 - clip.x));
  clip.height = Math.ceil(Math.min(y1 - y0 + 2 * M, 720 - clip.y));
  const hits = Array.from(document.querySelectorAll('.react-flow__node')).filter((e) => {
      if (e === n || e.contains(n) || n.contains(e)) return false;
      const r = e.getBoundingClientRect();
      return r.x < clip.x + clip.width && r.x + r.width > clip.x && r.y < clip.y + clip.height && r.y + r.height > clip.y; })
    .map((e) => ({ id: e.getAttribute('data-id'), aria: e.getAttribute('aria-label'), z: getComputedStyle(e).zIndex }));
  // 非节点 UI 也要查：顶栏/左栏/底栏/浮层
  const chrome = Array.from(document.querySelectorAll('[data-testid="canvas-topbar"],[data-testid^="canvas-zoom"],[data-testid="canvas-navigation-dock"],.react-flow__panel,[role=menu],[role=dialog],[data-testid="node-toolbar"]'))
    .map((e) => { const r = e.getBoundingClientRect();
      if (r.width === 0 || r.height === 0) return null;
      if (!(r.x < clip.x + clip.width && r.x + r.width > clip.x && r.y < clip.y + clip.height && r.y + r.height > clip.y)) return null;
      return { tid: e.getAttribute('data-testid'), cls: (e.className || '').toString().slice(0, 40),
        rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}` }; })
    .filter(Boolean);
  const wanted = ['flow-node-title', 'video-node-player-bar', 'video-node-playback-toggle', 'video-node-player-clock',
    'video-node-mute-toggle', 'video-node-fullscreen-toggle', 'slider-track'];
  return { clip, union: `${Math.round(x0)},${Math.round(y0)} ${Math.round(x1 - x0)}×${Math.round(y1 - y0)}`,
    nodeHits: hits, chrome, present: wanted.filter((t) => n.querySelector(`[data-testid="${t}"]`)),
    missing: wanted.filter((t) => !n.querySelector(`[data-testid="${t}"]`)) };
}, SELF);
log('裁切：', JSON.stringify(out.crop, null, 1));
out.guardPass = out.crop.nodeHits.length === 0 && out.crop.chrome.length === 0 && out.crop.missing.length === 0;
log('守卫：', out.guardPass ? '✅ 通过' : '🔴 不通过');

if (out.guardPass) {
  const buf = await p.screenshot({ type: 'png', clip: out.crop.clip });
  const f = new URL('102-video-card-player-bar.png', SHOT);
  writeFileSync(f, buf);
  out.shot = { file: f.pathname, bytes: buf.length, sha256: createHash('sha256').update(buf).digest('hex'), clip: out.crop.clip };
  log('📸 卡片播放态：', JSON.stringify(out.shot));
}
writeFileSync(new URL('./_tmp-b101c17.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();

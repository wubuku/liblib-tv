// 批次 101 · c18 轮：退到 **40% 档**再找空位。
//
// c17 查实：60% 档视口里有 **52 个他人节点**，把「卡片 + 标题 + 12px 余量」= `366×248`
// 放到视口内**任何位置**都会压到别人 —— 穷举 4px 步长，`best = null`。
// ⇒ 这不是「没找对位置」，是**这块画布在这个缩放下已经塞满了**。
//
// 另外冒出一样之前没注意的东西：**选中态的浮动工具条 `node-toolbar` `766×40` 在 `257,218`**，
// 它横跨在节点**上方**，底边 258，而裁切上沿 250 ⇒ **必然切进去 8px**。
// （这可能就是批次 95 那两条 `511×40` / `1298×40` 读数一直复现不了的原因：**宽度随节点类型/内容变**，
//   同一批次里 766 / 511 / 1298 三个值都出现过。）
// ⇒ 本轮裁切用**非对称余量**：上边 0（贴着标题行），其余 12。
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

const scaleNow = () => p.evaluate(() => { const e = document.querySelector('.react-flow__viewport');
  const m = e && /scale\(([\d.]+)\)/.exec(e.style.transform || ''); return m ? Number(m[1]) : null; });
const zoomLabel = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]');
  return e ? e.getAttribute('aria-label') : null; });
const setZoom = async (t) => { for (let k = 1; k <= 4; k++) {
  const zl = await zoomLabel(); if (zl && new RegExp(`, ${t}%`).test(zl)) return true;
  await p.click('[data-testid="canvas-zoom-percent"]'); await p.waitForTimeout(1000);
  if (await p.evaluate(() => !!document.querySelector('input[data-testid="canvas-zoom-percent-input"]'))) {
    await p.evaluate((v) => { const i = document.querySelector('input[data-testid="canvas-zoom-percent-input"]');
      Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(i, String(v));
      i.dispatchEvent(new Event('input', { bubbles: true }));
      i.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
      i.dispatchEvent(new Event('change', { bubbles: true })); i.blur(); }, t);
    await p.waitForTimeout(1700);
  }
  await p.keyboard.press('Escape'); await p.waitForTimeout(900); }
  return false; };
const stableScale = async () => { const a = await scaleNow(); await p.waitForTimeout(900); const b2 = await scaleNow(); return [a, b2, a === b2]; };

// ---- 通用：带重试的取数（共享画布会被整树重渲染） ----
const safeEval = async (fn, arg, tries = 8) => {
  for (let k = 0; k < tries; k++) { const r = await p.evaluate(fn, arg); if (!r || !r.__err) return r;
    if (k === 0) log('  重渲染竞态：', JSON.stringify(r)); await p.waitForTimeout(700); }
  return { __err: 'gave-up' };
};

log('换档前：', await zoomLabel());
await setZoom(40);
out.z40 = await stableScale();
log('40% 档连读：', JSON.stringify(out.z40), '｜', await zoomLabel());
if (!out.z40[2] || out.z40[0] !== 0.4) { log('🔴 缩放不稳 ⇒ 中止'); await b.close(); process.exit(1); }

// ---- 算空位 ----
out.plan = await safeEval((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'node-null' };
  const se = n.querySelector('[data-testid="video-flow-node-surface"]');
  const te = n.querySelector('[data-testid="flow-node-title"]');
  if (!se || !te) return { __err: 'child-null' };
  const surf = se.getBoundingClientRect();
  const W = Math.round(surf.width), H = Math.round(surf.height);
  const TITLE = Math.round(surf.y - te.getBoundingClientRect().y);
  const M = 12, TOPM = 0;                       // 上边 0：避开 node-toolbar
  const others = Array.from(document.querySelectorAll('.react-flow__node'))
    .filter((e) => e !== n && !e.contains(n) && !n.contains(e))
    .map((e) => { const r = e.getBoundingClientRect();
      return { aria: e.getAttribute('aria-label'), x0: r.x, y0: r.y, x1: r.x + r.width, y1: r.y + r.height }; });
  const fits = (x, y) => {
    const bx0 = x - M, by0 = y - TITLE - TOPM, bx1 = x + W + M, by1 = y + H + M;
    if (bx0 < 195 || by0 < 62 || bx1 > 1276 || by1 > 636) return null;
    for (const o of others) if (o.x0 < bx1 && o.x1 > bx0 && o.y0 < by1 && o.y1 > by0) return null;
    return [bx0, by0, bx1, by1];
  };
  const cur = { x: Math.round(surf.x), y: Math.round(surf.y) };
  let best = null;
  for (let y = 70; y <= 630 - H; y += 3) for (let x = 205; x <= 1265 - W; x += 3) {
    const box = fits(x, y); if (!box) continue;
    const d = Math.abs(x - cur.x) + Math.abs(y - cur.y);
    if (!best || d < best.d) best = { x, y, d, box };
  }
  return { W, H, TITLE, cur, card: `${cur.x},${cur.y} ${W}×${H}`, best, othersCount: others.length };
}, SELF);
if (out.plan.__err) { log('🔴 取数失败：', JSON.stringify(out.plan)); await b.close(); process.exit(1); }
log('40% 档尺寸：', JSON.stringify({ W: out.plan.W, H: out.plan.H, TITLE: out.plan.TITLE, cur: out.plan.cur }));
log(`视口内他人节点 ${out.plan.othersCount} 个｜无遮挡落点：`, JSON.stringify(out.plan.best));

// ---- 挪过去 ----
if (out.plan.best) {
  const grab = await safeEval((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const t = n.querySelector('[data-testid="flow-node-title"]'); if (!t) return { __err: 'no-title' };
    const btn = t.querySelector('button');           // 内层就是「改名」BUTTON
    const r = t.getBoundingClientRect();
    // 在标题 DIV 内**横向扫**，找一个既在 DIV 里、又不在改名 BUTTON 里的点。
    // （c18 首跑按 8% 处取点，40% 档标题只有 26px 宽，8% 仍落在改名钮上 ⇒ hitTid=null）
    for (let f = 0.03; f <= 0.97; f += 0.02) {
      const x = Math.round(r.x + r.width * f), y = Math.round(r.y + r.height / 2);
      const el = document.elementFromPoint(x, y);
      if (!el) continue;
      if (el.closest('button')) continue;
      // ⚠️ 判据不是「命中元素**就是** flow-node-title」——
      //    标题 DIV 内部还有一层**标题文字 SPAN**，命中它才是常态（c18 两次都读到 hitTid=null）。
      //    正路：命中元素在 `flow-node-title` **子树内**，且不在任何 button 内。
      if (!el.closest('[data-testid="flow-node-title"]')) continue;
      return { point: [x, y], frac: Math.round(f * 100), hitTid: el.getAttribute('data-testid'),
        hitTag: el.tagName, insideSelf: !!(el.closest(`.react-flow__node[data-id="${i}"]`)) };
    }
    return { __err: 'no-free-point-in-title' }; }, SELF);
  log('抓取点：', JSON.stringify(grab));
  if (grab.hitTid !== undefined && !grab.__err) {
    const dx = out.plan.best.x - out.plan.cur.x, dy = out.plan.best.y - out.plan.cur.y;
    log(`  位移 ${dx},${dy}`);
    await p.mouse.move(grab.point[0], grab.point[1]); await p.waitForTimeout(450);
    await p.mouse.down(); await p.waitForTimeout(300);
    await p.mouse.move(grab.point[0] + Math.round(dx / 2), grab.point[1] + Math.round(dy / 2), { steps: 12 }); await p.waitForTimeout(350);
    await p.mouse.move(grab.point[0] + dx, grab.point[1] + dy, { steps: 12 }); await p.waitForTimeout(500);
    await p.mouse.up(); await p.waitForTimeout(1400);
    out.after = await safeEval((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
      const s = n.querySelector('[data-testid="video-flow-node-surface"]').getBoundingClientRect();
      return { surf: `${Math.round(s.x)},${Math.round(s.y)}`, transform: n.style.transform }; }, SELF);
    log('拖后：', JSON.stringify(out.after));
  }
}

// ---- 重新选中 + 等它自己播到 ~2.5s（**不再多点播放钮**） ----
{
  const pt = await safeEval((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const s = n.querySelector('[data-testid="video-flow-node-surface"]').getBoundingClientRect();
    const x = Math.round(s.x + s.width / 2), y = Math.round(s.y + s.height * 0.2);
    const el = document.elementFromPoint(x, y);
    return { point: [x, y], insideSelf: !!(el && el.closest(`.react-flow__node[data-id="${i}"]`)), hitTag: el ? el.tagName : null }; }, SELF);
  log('重新选中落点：', JSON.stringify(pt));
  if (pt.insideSelf) { await p.mouse.move(pt.point[0], pt.point[1]); await p.waitForTimeout(350); await p.mouse.click(pt.point[0], pt.point[1]); }
  await p.waitForTimeout(2400);
}
out.st = await safeEval((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const v = n.querySelector('video'); const c = n.querySelector('[data-testid="video-node-player-clock"]');
  return { ct: v ? v.currentTime : null, paused: v ? v.paused : null,
    clock: c ? c.innerText.replace(/\s+/g, ' ').trim() : null,
    toggle: (n.querySelector('[data-testid="video-node-playback-toggle"]') || {}).getAttribute?.('aria-label') || null,
    mute: (n.querySelector('[data-testid="video-node-mute-toggle"]') || {}).getAttribute?.('aria-label') || null }; }, SELF);
log('拍前状态：', JSON.stringify(out.st));

// ---- 裁切（非对称余量）+ 守卫 ----
out.crop = await safeEval((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'node-null' };
  const pick = ['flow-node-title', 'video-flow-node-surface', 'video-node-player-bar', 'image-primary-preview-viewport', 'video-hover-surface'];
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (const t of pick) { const e = n.querySelector(`[data-testid="${t}"]`); if (!e) continue;
    const r = e.getBoundingClientRect(); if (r.width === 0 || r.height === 0) continue;
    x0 = Math.min(x0, r.x); y0 = Math.min(y0, r.y); x1 = Math.max(x1, r.x + r.width); y1 = Math.max(y1, r.y + r.height); }
  const L = 12, T = 0, R = 12, Bt = 12;
  const clip = { x: Math.max(0, Math.floor(x0 - L)), y: Math.max(0, Math.floor(y0 - T)), width: 0, height: 0 };
  clip.width = Math.ceil(Math.min(x1 - x0 + L + R, 1280 - clip.x));
  clip.height = Math.ceil(Math.min(y1 - y0 + T + Bt, 720 - clip.y));
  const hits = Array.from(document.querySelectorAll('.react-flow__node')).filter((e) => {
      if (e === n || e.contains(n) || n.contains(e)) return false;
      const r = e.getBoundingClientRect();
      return r.x < clip.x + clip.width && r.x + r.width > clip.x && r.y < clip.y + clip.height && r.y + r.height > clip.y; })
    .map((e) => ({ id: e.getAttribute('data-id'), aria: e.getAttribute('aria-label'), z: getComputedStyle(e).zIndex }));
  const chrome = Array.from(document.querySelectorAll('.react-flow__node-toolbar,[role=menu],[role=dialog],[data-testid^="canvas-zoom"],[data-testid="canvas-navigation-dock"]'))
    .map((e) => { const r = e.getBoundingClientRect();
      if (r.width === 0 || r.height === 0) return null;
      if (!(r.x < clip.x + clip.width && r.x + r.width > clip.x && r.y < clip.y + clip.height && r.y + r.height > clip.y)) return null;
      return { tid: e.getAttribute('data-testid'), cls: (e.className || '').toString().slice(0, 40),
        rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}` }; }).filter(Boolean);
  const wanted = ['flow-node-title', 'video-node-player-bar', 'video-node-playback-toggle', 'video-node-player-clock',
    'video-node-mute-toggle', 'video-node-fullscreen-toggle', 'slider-track'];
  return { clip, union: `${Math.round(x0)},${Math.round(y0)} ${Math.round(x1 - x0)}×${Math.round(y1 - y0)}`,
    nodeHits: hits, chrome, missing: wanted.filter((t) => !n.querySelector(`[data-testid="${t}"]`)) };
}, SELF);
log('裁切：', JSON.stringify(out.crop, null, 1));
out.guardPass = !out.crop.__err && out.crop.nodeHits.length === 0 && out.crop.chrome.length === 0 && out.crop.missing.length === 0;
log('守卫：', out.guardPass ? '✅ 通过' : '🔴 不通过');

if (out.guardPass) {
  const buf = await p.screenshot({ type: 'png', clip: out.crop.clip });
  const f = new URL('102-video-card-player-bar.png', SHOT);
  writeFileSync(f, buf);
  out.shot = { file: f.pathname, bytes: buf.length, sha256: createHash('sha256').update(buf).digest('hex'), clip: out.crop.clip };
  log('📸 卡片播放态（40% 档）：', JSON.stringify(out.shot));
}

// ---- 归位缩放 ----
log('\n=== 归位缩放 ===');
for (let k = 0; k < 3; k++) {
  await setZoom(60);
  const s = await stableScale();
  log(`  第 ${k + 1} 次：`, JSON.stringify(s), '｜', await zoomLabel());
  if (s[2] && s[0] === 0.6) { log('  ✅ 归位 60%'); break; }
}
writeFileSync(new URL('./_tmp-b101c18.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();

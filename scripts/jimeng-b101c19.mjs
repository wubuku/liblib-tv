// 批次 101 · c19 轮：换策略 —— 不再和邻居抢位置，**把视口平移到空区**再拖过去。
//
// c18 第三次尝试的账：拖动**成功**了（音频 6 已避开），但「时间线 2」`z=22` 仍然压着。
// 而且计划算出的空位 `[514,131,766,297]` 与实际裁切 `[514,138,766,304]` **对不上** ——
// 说明**算的位置和拍的时候，画布已经被人改了**（本轮节点数一路 47→49→52→53）。
// ⇒ 「先算空位、再挪、再拍」这三步之间**没有原子性**，这个策略在活画布上不可靠。
//
// 本轮改成：**先平移，平移到「我这张卡旁边就是空的」为止，挪的位移尽量小，然后立刻拍。**
// 每换一个平移量就重算一次空位；挪不动或仍不净，最多试 4 个方向就收手。
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
const safeEval = async (fn, arg, tries = 6) => {
  for (let k = 0; k < tries; k++) { const r = await p.evaluate(fn, arg); if (!r || !r.__err) return r; await p.waitForTimeout(700); }
  return { __err: 'gave-up' }; };

await setZoom(40);
const z0 = await (async () => { const a = await scaleNow(); await p.waitForTimeout(900); const b2 = await scaleNow(); return [a, b2, a === b2]; })();
log('40% 档：', JSON.stringify(z0), '｜', await zoomLabel());
if (!z0[2] || z0[0] !== 0.4) { log('🔴 缩放不稳 ⇒ 中止'); await b.close(); process.exit(1); }

const planFn = (i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'node-null' };
  const se = n.querySelector('[data-testid="video-flow-node-surface"]');
  const te = n.querySelector('[data-testid="flow-node-title"]');
  if (!se || !te) return { __err: 'child-null' };
  const surf = se.getBoundingClientRect();
  const W = Math.round(surf.width), H = Math.round(surf.height);
  const TITLE = Math.round(surf.y - te.getBoundingClientRect().y);
  const L = 12, T = 0, R = 12, Bt = 12;
  const others = Array.from(document.querySelectorAll('.react-flow__node')).filter((e) => e !== n && !e.contains(n) && !n.contains(e))
    .map((e) => { const r = e.getBoundingClientRect(); return { aria: e.getAttribute('aria-label'), x0: r.x, y0: r.y, x1: r.x + r.width, y1: r.y + r.height }; });
  const clearAt = (x, y) => {
    const bx0 = x - L, by0 = y - TITLE - T, bx1 = x + W + R, by1 = y + H + Bt;
    if (bx0 < 195 || by0 < 62 || bx1 > 1276 || by1 > 636) return null;
    for (const o of others) if (o.x0 < bx1 && o.x1 > bx0 && o.y0 < by1 && o.y1 > by0) return null;
    return true;
  };
  const cur = { x: Math.round(surf.x), y: Math.round(surf.y) };
  // 只要**位移小**的空位（≤160px 屏上），保证「挪完立刻拍」的时间窗最短
  let best = null;
  for (let dy = -160; dy <= 160; dy += 4) for (let dx = -260; dx <= 260; dx += 4) {
    if (!clearAt(cur.x + dx, cur.y + dy)) continue;
    const d = Math.abs(dx) + Math.abs(dy);
    if (!best || d < best.d) best = { dx, dy, d, to: { x: cur.x + dx, y: cur.y + dy } };
  }
  return { W, H, TITLE, cur, card: `${cur.x},${cur.y} ${W}×${H}`, best, othersCount: others.length,
    hereClear: clearAt(cur.x, cur.y) };
};

const grabFn = (i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'node-null' };
  const t = n.querySelector('[data-testid="flow-node-title"]'); if (!t) return { __err: 'no-title' };
  const r = t.getBoundingClientRect();
  for (let f = 0.03; f <= 0.97; f += 0.02) {
    const x = Math.round(r.x + r.width * f), y = Math.round(r.y + r.height / 2);
    const el = document.elementFromPoint(x, y);
    if (!el || el.closest('button') || !el.closest('[data-testid="flow-node-title"]')) continue;
    return { point: [x, y], hitTag: el.tagName };
  }
  return { __err: 'no-free-point' };
};

const cropFn = (i) => {
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
      return { tid: e.getAttribute('data-testid'), rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}` }; }).filter(Boolean);
  const wanted = ['flow-node-title', 'video-node-player-bar', 'video-node-playback-toggle', 'video-node-player-clock',
    'video-node-mute-toggle', 'video-node-fullscreen-toggle', 'slider-track'];
  return { clip, hits, chrome, missing: wanted.filter((t) => !n.querySelector(`[data-testid="${t}"]`)) };
};

// ---- 4 个平移方向，每个方向：算空位 → 挪 → 立刻拍 ----
const PANS = [[0, 0], [0, 520], [0, -520], [640, 0]];
out.attempts = [];
for (const [wx, wy] of PANS) {
  if (wx || wy) {
    await p.mouse.move(760, 400); await p.waitForTimeout(300);
    await p.mouse.wheel(wx, wy); await p.waitForTimeout(1400);
    log(`\n--- 平移 ${wx},${wy} 后 ---`);
  } else log('\n--- 不平移（原地）---');
  const plan = await safeEval(planFn, SELF);
  if (plan.__err) { log('  取数失败'); continue; }
  log(`  卡片 ${plan.card}｜视口内他人 ${plan.othersCount}｜原位干净？${plan.hereClear}｜小位移空位：`, JSON.stringify(plan.best));
  if (!plan.best) { out.attempts.push({ pan: [wx, wy], best: null }); continue; }

  const grab = await safeEval(grabFn, SELF);
  if (grab.__err) { log('  抓取点失败：', grab.__err); continue; }
  await p.mouse.move(grab.point[0], grab.point[1]); await p.waitForTimeout(400);
  await p.mouse.down(); await p.waitForTimeout(280);
  await p.mouse.move(grab.point[0] + Math.round(plan.best.dx / 2), grab.point[1] + Math.round(plan.best.dy / 2), { steps: 10 });
  await p.waitForTimeout(300);
  await p.mouse.move(grab.point[0] + plan.best.dx, grab.point[1] + plan.best.dy, { steps: 10 });
  await p.waitForTimeout(450);
  await p.mouse.up(); await p.waitForTimeout(1200);
  // 重新选中（拖动会掉选中；「选中即播」⇒ 不再多点播放钮）
  const pt = await safeEval((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const s = n.querySelector('[data-testid="video-flow-node-surface"]').getBoundingClientRect();
    const x = Math.round(s.x + s.width / 2), y = Math.round(s.y + s.height * 0.2);
    const el = document.elementFromPoint(x, y);
    return { point: [x, y], insideSelf: !!(el && el.closest(`.react-flow__node[data-id="${i}"]`)) }; }, SELF);
  if (pt.insideSelf) { await p.mouse.move(pt.point[0], pt.point[1]); await p.waitForTimeout(300); await p.mouse.click(pt.point[0], pt.point[1]); }
  await p.waitForTimeout(1800);

  const crop = await safeEval(cropFn, SELF);
  const st = await safeEval((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const v = n.querySelector('video'); const c = n.querySelector('[data-testid="video-node-player-clock"]');
    return { ct: v ? v.currentTime : null, paused: v ? v.paused : null, clock: c ? c.innerText.replace(/\s+/g, ' ').trim() : null }; }, SELF);
  const ok = !crop.__err && crop.hits.length === 0 && crop.chrome.length === 0 && crop.missing.length === 0;
  log(`  拍前：${JSON.stringify(st)}｜守卫：节点${crop.hits.length} 浮层${crop.chrome.length} 缺件${crop.missing.length} ⇒ ${ok ? '✅' : '🔴'}`);
  if (crop.hits && crop.hits.length) log('    压着的：', JSON.stringify(crop.hits));
  out.attempts.push({ pan: [wx, wy], dx: plan.best.dx, dy: plan.best.dy, st, hits: crop.hits, ok });
  if (ok) {
    out.win = { clip: crop.clip, st };
    const buf = await p.screenshot({ type: 'png', clip: crop.clip });
    const f = new URL('102-video-card-player-bar.png', SHOT);
    writeFileSync(f, buf);
    out.shot = { file: f.pathname, bytes: buf.length, sha256: createHash('sha256').update(buf).digest('hex'), clip: crop.clip };
    log('  📸 卡片播放态：', JSON.stringify(out.shot));
    break;
  }
}

log('\n=== 归位缩放 ===');
for (let k = 0; k < 3; k++) {
  await setZoom(60);
  const s = await (async () => { const a = await scaleNow(); await p.waitForTimeout(900); const b2 = await scaleNow(); return [a, b2, a === b2]; })();
  log(`  第 ${k + 1} 次：`, JSON.stringify(s), '｜', await zoomLabel());
  if (s[2] && s[0] === 0.6) { log('  ✅ 归位 60%'); break; }
}
out.shotTaken = !!out.shot;
writeFileSync(new URL('./_tmp-b101c19.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();

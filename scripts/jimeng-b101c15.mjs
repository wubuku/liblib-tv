// 批次 101 · c15 轮：把**自建节点拖到空区**再拍，顺手把「守卫该怎么写」这件事想清楚。
//
// c14 的实测：收紧裁切到「标题 + 卡片本体」之后，clip 里仍然有别人的节点，
//   `node_9y4j9jf0qv`（音频 6）`483,319 192×192` —— 与本卡片 `469,288 341×192` **大面积重叠**
//   `node_d4tjtpnatq`（时间线 2）`280,266 720×124` —— 横穿整张卡
// ⇒ 这不是「裁切没收紧」的问题，是**共享画布上邻居就压在头上**。
//
// 🔑 **守卫的两种写法，差别很大**：
//   · 「clip 的矩形与他人节点矩形相交」= **几何判据**，会把**被遮挡的**节点也判成污染（假阳性）
//   · 「clip 里逐点取 `elementsFromPoint`，首个元素不是自节点」= **可见判据**，问的是「看得见吗」
//   本轮**两条都记**，但**先把节点挪到空区**，让几何判据也能过 —— 手册截图宁可多花一轮，也不放宽守卫。
//
// ⚠️ 拖动要点在**标题行 DIV** 上，不能点它内层的 `Rename …` BUTTON（会进改名态）。
//    落点必须先验 `elementFromPoint` 命中的是 `flow-node-title` 本身。
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

// ---- 找一个「能塞下 380×260 且四邻无节点」的屏上落点 ----
out.spot = await p.evaluate(() => {
  const rects = Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getBoundingClientRect());
  const clear = (cx, cy, hw, hh) => rects.every((r) => !(r.x < cx + hw && r.x + r.width > cx - hw && r.y < cy + hh && r.y + r.height > cy - hh));
  const inUI = (x, y) => x < 200 || y < 60 || y > 630 || x > 1120;
  for (let cy = 340; cy <= 600; cy += 20) for (let cx = 380; cx <= 1000; cx += 20) {
    if (inUI(cx, cy)) continue;
    if (clear(cx, cy, 200, 135)) {
      const el = document.elementFromPoint(cx, cy);
      if (el && !el.closest('.react-flow__node') && !el.closest('button,[role=button]')) return { cx, cy };
    }
  }
  return null;
});
log('空区落点：', JSON.stringify(out.spot));

// ---- 拖动：抓标题行 DIV（不是内层 Rename BUTTON） ----
out.before = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  return { transform: n.style.transform, rect: (() => { const r = n.getBoundingClientRect();
    return `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`; })() }; }, SELF);
log('拖动前：', JSON.stringify(out.before));

if (out.spot) {
  const grab = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const t = n.querySelector('[data-testid="flow-node-title"]'); const r = t.getBoundingClientRect();
    // 取标题 DIV **左侧 1/4**，那里不在内层 Rename BUTTON 里
    const x = Math.round(r.x + r.width * 0.1), y = Math.round(r.y + r.height / 2);
    const el = document.elementFromPoint(x, y);
    return { point: [x, y], hitTid: el ? el.getAttribute('data-testid') : null, hitTag: el ? el.tagName : null,
      hitAria: el ? el.getAttribute('aria-label') : null,
      insideSelf: !!(el && el.closest(`.react-flow__node[data-id="${i}"]`)) }; }, SELF);
  log('抓取点：', JSON.stringify(grab));
  out.grab = grab;
  if (grab.hitTid === 'flow-node-title') {
    await p.mouse.move(grab.point[0], grab.point[1]); await p.waitForTimeout(450);
    await p.mouse.down(); await p.waitForTimeout(300);
    await p.mouse.move(Math.round((grab.point[0] + out.spot.cx) / 2), Math.round((grab.point[1] + out.spot.cy) / 2), { steps: 12 });
    await p.waitForTimeout(350);
    await p.mouse.move(out.spot.cx, out.spot.cy, { steps: 12 }); await p.waitForTimeout(500);
    await p.mouse.up(); await p.waitForTimeout(1300);
    out.after = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
      const v = n.querySelector('video');
      return { transform: n.style.transform, sel: n.classList.contains('selected'),
        rect: (() => { const r = n.getBoundingClientRect();
          return `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`; })(),
        ct: v ? v.currentTime : null, paused: v ? v.paused : null }; }, SELF);
    log('拖动后：', JSON.stringify(out.after));
    out.moved = out.after.transform !== out.before.transform;
    log('  ⇒ 位置变了？', out.moved);
  } else log('  🔴 抓取点没落在 flow-node-title 上 ⇒ 不拖');
}

// ---- 重新选中并起播（拖动会掉选中） ----
{
  const pt = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const v = n.querySelector('video,img'); const r = v.getBoundingClientRect();
    const x = Math.round(r.x + r.width / 2), y = Math.round(r.y + r.height * 0.25);
    const el = document.elementFromPoint(x, y);
    return { point: [x, y], insideSelf: !!(el && el.closest(`.react-flow__node[data-id="${i}"]`)), hitTag: el ? el.tagName : null }; }, SELF);
  log('重新选中落点：', JSON.stringify(pt));
  if (pt.insideSelf) { await p.mouse.move(pt.point[0], pt.point[1]); await p.waitForTimeout(350);
    await p.mouse.click(pt.point[0], pt.point[1]); }
  await p.waitForTimeout(2600);   // 「选中即播」，等 2.6s 让时间读数到 00:02
}
out.st = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const v = n.querySelector('video'); const c = n.querySelector('[data-testid="video-node-player-clock"]');
  return { sel: n.classList.contains('selected'), ct: v ? v.currentTime : null, paused: v ? v.paused : null,
    clock: c ? c.innerText.replace(/\s+/g, ' ').trim() : null,
    toggle: (n.querySelector('[data-testid="video-node-playback-toggle"]') || {}).getAttribute?.('aria-label') || null,
    mute: (n.querySelector('[data-testid="video-node-mute-toggle"]') || {}).getAttribute?.('aria-label') || null,
    full: (n.querySelector('[data-testid="video-node-fullscreen-toggle"]') || {}).getAttribute?.('aria-label') || null }; }, SELF);
log('拍前状态：', JSON.stringify(out.st));

// ---- 裁切 + **双判据**守卫 ----
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
  // 判据①几何：矩形相交
  const geom = Array.from(document.querySelectorAll('.react-flow__node')).filter((e) => {
      if (e === n || e.contains(n) || n.contains(e)) return false;
      const r = e.getBoundingClientRect();
      return r.x < clip.x + clip.width && r.x + r.width > clip.x && r.y < clip.y + clip.height && r.y + r.height > clip.y; })
    .map((e) => ({ id: e.getAttribute('data-id'), aria: e.getAttribute('aria-label') }));
  // 判据②可见：clip 内 9×9 网格取 elementsFromPoint，看**首个**元素是不是自节点/画布底
  const bad = [];
  for (let gx = 0; gx < 9; gx++) for (let gy = 0; gy < 9; gy++) {
    const x = Math.round(clip.x + (clip.width * (gx + 0.5)) / 9), y = Math.round(clip.y + (clip.height * (gy + 0.5)) / 9);
    const top = document.elementFromPoint(x, y);
    if (!top) continue;
    if (top.closest(`.react-flow__node[data-id="${i}"]`)) continue;
    const t = top.getAttribute && top.getAttribute('data-testid');
    if (t === 'canvas' || top.classList.contains('react-flow__pane') || top.tagName === 'CANVAS' || top.tagName === 'svg') continue;
    if (top.closest('.react-flow__pane')) continue;
    bad.push({ at: [x, y], tag: top.tagName, tid: t, aria: top.getAttribute && top.getAttribute('aria-label'),
      cls: (top.className || '').toString().slice(0, 40) });
  }
  const wanted = ['flow-node-title', 'video-node-player-bar', 'video-node-playback-toggle', 'video-node-player-clock',
    'video-node-mute-toggle', 'video-node-fullscreen-toggle', 'slider-track'];
  return { clip, union: `${Math.round(x0)},${Math.round(y0)} ${Math.round(x1 - x0)}×${Math.round(y1 - y0)}`,
    geomOverlaps: geom, visibleForeign: bad,
    present: wanted.filter((t) => n.querySelector(`[data-testid="${t}"]`)), missing: wanted.filter((t) => !n.querySelector(`[data-testid="${t}"]`)) };
}, SELF);
log('裁切：', JSON.stringify(out.crop, null, 1));
out.guardGeom = out.crop.geomOverlaps.length === 0;
out.guardVisible = out.crop.visibleForeign.length === 0;
out.guardTargets = out.crop.missing.length === 0;
log(`守卫：几何=${out.guardGeom ? '✅' : '🔴'}(${out.crop.geomOverlaps.length}) 可见=${out.guardVisible ? '✅' : '🔴'}(${out.crop.visibleForeign.length}) 目标齐=${out.guardTargets ? '✅' : '🔴'}`);

if (out.guardTargets) {
  const buf = await p.screenshot({ type: 'png', clip: out.crop.clip });
  const f = new URL('102-video-card-player-bar.png', SHOT);
  writeFileSync(f, buf);
  out.shot = { file: f.pathname, bytes: buf.length, sha256: createHash('sha256').update(buf).digest('hex'), clip: out.crop.clip };
  log('📸 卡片播放态：', JSON.stringify(out.shot));
}
writeFileSync(new URL('./_tmp-b101c15.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();

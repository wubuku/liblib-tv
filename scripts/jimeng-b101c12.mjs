// 批次 101 · c12 轮：抓「卡片播放态」截图（带控件行），并做批次 78 那套裁切守卫。
//
// 裁切口径沿用批次 78 的做法（**踩过的坑不能再踩**）：
//   · 不能用 `.react-flow__node` 的矩形 —— 它会**把上方 31px 的标题裁掉**
//   · 要用**可见后代的并集**，再留 10px 余量
//   · 守卫三条：clip 内他人节点 `0`、带语义的非节点 UI（`BUTTON/INPUT/FORM/TEXTAREA/A` 或非空 aria）`0`、
//     目标元素全在 clip 内
// ⚠️ 本节点在 60% 档，卡片 341×192 屏上很小；截图前要确认控件行**看得清**。
//    若太小就**当场换档位**（换档必须锁 data-id，批次 93/95 的规矩），
//    换完**必须归位**并回读验证。
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

// 连读两次 scale，相同才算静止（**绝不写死 0.6**）
const scaleStable = async () => { const a = await scaleNow(); await p.waitForTimeout(900); const b2 = await scaleNow();
  out.scalePair = [a, b2]; return { a, b: b2, same: a !== null && a === b2 }; };

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

// ---- 起播到 ~2s，让时间读数有内容 ----
async function playTo(sec) {
  const t = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const e = n.querySelector('[data-testid="video-node-playback-toggle"]'); if (!e) return null;
    const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, SELF);
  if (!t) return false;
  await p.mouse.move(t[0], t[1]); await p.waitForTimeout(300); await p.mouse.click(t[0], t[1]);
  await p.waitForTimeout(sec * 1000);
  return true;
}

out.z0 = await scaleStable();
log('缩放：', JSON.stringify(out.z0), '｜', await zoomLabel());

// 60% 档下卡片只有 341×192，控件行 22px 屏上 ⇒ 换 100% 档，**换完必须归位**
await setZoom(100);
out.z1 = await scaleStable();
log('换到 100%：', JSON.stringify(out.z1), '｜', await zoomLabel());
if (!out.z1.same) { log('🔴 scale 连读两次不同 ⇒ 不截图（会拍到动画中间帧）'); writeFileSync(new URL('./_tmp-b101c12.json', import.meta.url), JSON.stringify(out, null, 1)); await b.close(); process.exit(1); }

// 换档后节点可能跑出视口（批次 95：60%/100% 档节点跑出视口也照样量到）
out.nodeLoc = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const r = n.getBoundingClientRect();
  return { screen: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
    inViewport: r.x + r.width > 0 && r.y + r.height > 0 && r.x < 1280 && r.y < 720,
    sel: n.classList.contains('selected') }; }, SELF);
log('节点位置：', JSON.stringify(out.nodeLoc));

// 若跑出视口，用「画布平移」把它拖回来 —— 这里只做**读数与截图**，平移属安全操作
if (!out.nodeLoc.inViewport) {
  log('  节点在视口外 ⇒ 需要平移画布才能入镜');
  out.panned = false;
}

// 起播
await playTo(2.2);
out.playing = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const v = n.querySelector('video'); const c = n.querySelector('[data-testid="video-node-player-clock"]');
  return { ct: v ? v.currentTime : null, paused: v ? v.paused : null, clock: c ? c.innerText.replace(/\s+/g,' ').trim() : null,
    inViewport: (() => { const r = n.getBoundingClientRect();
      return r.x + r.width > 0 && r.y + r.height > 0 && r.x < 1280 && r.y < 720; })() }; }, SELF);
log('播放态：', JSON.stringify(out.playing));

if (!out.playing.inViewport) { log('🔴 仍不在视口 ⇒ 放弃截图（不硬拍）'); writeFileSync(new URL('./_tmp-b101c12.json', import.meta.url), JSON.stringify(out, null, 1)); await b.close(); process.exit(1); }

// ---- 裁切 + 守卫 ----
out.crop = await p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  const targets = [];
  for (const e of n.querySelectorAll('*')) {
    const r = e.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    x0 = Math.min(x0, r.x); y0 = Math.min(y0, r.y); x1 = Math.max(x1, r.x + r.width); y1 = Math.max(y1, r.y + r.height);
    if (e.getAttribute('data-testid') || e.getAttribute('aria-label')) targets.push(e.getAttribute('data-testid') || e.getAttribute('aria-label'));
  }
  const nr = n.getBoundingClientRect();
  const M = 10;
  const clip = { x: Math.max(0, Math.floor(x0 - M)), y: Math.max(0, Math.floor(y0 - M)),
    width: Math.ceil(x1 - x0 + 2 * M), height: Math.ceil(y1 - y0 + 2 * M) };
  clip.width = Math.min(clip.width, 1280 - clip.x); clip.height = Math.min(clip.height, 720 - clip.y);
  // 守卫
  const otherNodes = Array.from(document.querySelectorAll('.react-flow__node')).filter((e) => {
    if (e === n || e.contains(n) || n.contains(e)) return false;
    const r = e.getBoundingClientRect();
    return r.x < clip.x + clip.width && r.x + r.width > clip.x && r.y < clip.y + clip.height && r.y + r.height > clip.y;
  }).map((e) => e.getAttribute('data-id'));
  const semantic = Array.from(document.elementsFromPoint(
    Math.round(clip.x + clip.width / 2), Math.round(clip.y + clip.height / 2)))
    .filter((e) => !n.contains(e) && /^(BUTTON|INPUT|FORM|TEXTAREA|A)$/.test(e.tagName) || (!n.contains(e) && e.getAttribute('aria-label')))
    .map((e) => `${e.tagName}[${e.getAttribute('aria-label') || ''}]`);
  const wanted = ['video-node-player-bar', 'video-node-playback-toggle', 'video-node-player-clock',
    'video-node-mute-toggle', 'video-node-fullscreen-toggle', 'slider-track', 'flow-node-title'];
  const present = wanted.filter((t) => n.querySelector(`[data-testid="${t}"]`));
  return { clip, nodeRect: `${Math.round(nr.x)},${Math.round(nr.y)} ${Math.round(nr.width)}×${Math.round(nr.height)}`,
    union: `${Math.round(x0)},${Math.round(y0)} ${Math.round(x1 - x0)}×${Math.round(y1 - y0)}`,
    otherNodes, semantic, present, targets: targets.slice(0, 24) };
}, SELF);
log('裁切：', JSON.stringify(out.crop, null, 1));
out.guardPass = out.crop.otherNodes.length === 0 && out.crop.semantic.length === 0 && out.crop.present.length === 7;
log('守卫：', out.guardPass ? '✅ 通过' : '🔴 不通过 ⇒ 不截图');

if (out.guardPass) {
  const buf = await p.screenshot({ type: 'png', clip: { x: out.crop.clip.x, y: out.crop.clip.y, width: out.crop.clip.width, height: out.crop.clip.height } });
  const f = new URL('102-video-card-player-bar.png', SHOT);
  writeFileSync(f, buf);
  out.shot = { file: f.pathname, bytes: buf.length, sha256: createHash('sha256').update(buf).digest('hex') };
  log('📸 卡片播放态：', JSON.stringify(out.shot));
}

// ---- 归位缩放（**必须**，回读验证） ----
log('\n=== 归位缩放 ===');
out.restore = [];
for (let k = 0; k < 3; k++) {
  await setZoom(60);
  const s = await scaleStable();
  out.restore.push({ k, pair: [s.a, s.b], same: s.same, label: await zoomLabel() });
  log(`  第 ${k + 1} 次：`, JSON.stringify(out.restore[out.restore.length - 1]));
  if (s.same && s.a === 0.6) { log('  ✅ 归位到 60%'); break; }
}

writeFileSync(new URL('./_tmp-b101c12.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();

// 批次 101 · c14 轮：把裁切**收紧到卡片本体**，避开旁边别人的节点。
//
// c13 的两处修正：
//   ① `selectSelf()` 本身就会触发「选中即播」（c5 已验证）⇒ 我紧接着又点了一次播放钮，
//      那是**再点一次 = 暂停**，所以拍到的是暂停态。**这一页的脚本顺序错了**：
//      「选中」已经开播，就不该再点播放钮。
//   ② 「可见后代并集」把**外伸的连接手柄**（右侧 ⊕，canvas 60×60）也算了进去
//      ⇒ 并集被撑到 `451,262 407×228`，比卡片本体大出一圈，正好把旁边的
//      「音频 6」「时间线 2」框进来。
//      **裁切口径要分层**：要展示的是「标题行 + 卡片本体（含控件行）」，
//      手柄属于 [连接节点] 那一页，不该出现在本页截图里。
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

// ① 先看当前是不是暂停；是就**再点一次**播回去（c13 把顺序搞反了）
out.st0 = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const v = n.querySelector('video'); const c = n.querySelector('[data-testid="video-node-player-clock"]');
  return { sel: n.classList.contains('selected'), ct: v ? v.currentTime : null, paused: v ? v.paused : null,
    clock: c ? c.innerText.replace(/\s+/g, ' ').trim() : null,
    toggle: (n.querySelector('[data-testid="video-node-playback-toggle"]') || {}).getAttribute?.('aria-label') || null }; }, SELF);
log('当前：', JSON.stringify(out.st0));
if (out.st0.paused) {
  const t = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const e = n.querySelector('[data-testid="video-node-playback-toggle"]'); if (!e) return null;
    const r = e.getBoundingClientRect();
    const x = Math.round(r.x + r.width / 2), y = Math.round(r.y + r.height / 2);
    const el = document.elementFromPoint(x, y);
    return { point: [x, y], inside: !!(el && (el === e || e.contains(el))) }; }, SELF);
  if (t && t.inside) { await p.mouse.move(t.point[0], t.point[1]); await p.waitForTimeout(300); await p.mouse.click(t.point[0], t.point[1]); }
  // 播到 ~2.5s 再拍，时间读数更有内容
  await p.waitForTimeout(1400);
}
out.st1 = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const v = n.querySelector('video'); const c = n.querySelector('[data-testid="video-node-player-clock"]');
  return { ct: v ? v.currentTime : null, paused: v ? v.paused : null,
    clock: c ? c.innerText.replace(/\s+/g, ' ').trim() : null,
    toggle: (n.querySelector('[data-testid="video-node-playback-toggle"]') || {}).getAttribute?.('aria-label') || null }; }, SELF);
log('拍前：', JSON.stringify(out.st1));

// ② 收紧裁切：只要「标题行 + 卡片本体」，**不含外伸手柄**
out.crop = await p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const pick = ['flow-node-title', 'video-flow-node-surface', 'video-node-player-bar', 'image-primary-preview-viewport', 'video-hover-surface'];
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity; const used = [];
  for (const t of pick) { const e = n.querySelector(`[data-testid="${t}"]`); if (!e) continue;
    const r = e.getBoundingClientRect(); if (r.width === 0 || r.height === 0) continue;
    x0 = Math.min(x0, r.x); y0 = Math.min(y0, r.y); x1 = Math.max(x1, r.x + r.width); y1 = Math.max(y1, r.y + r.height); used.push(t); }
  const M = 12;
  const clip = { x: Math.max(0, Math.floor(x0 - M)), y: Math.max(0, Math.floor(y0 - M)),
    width: 0, height: 0 };
  clip.width = Math.ceil(Math.min(x1 - x0 + 2 * M, 1280 - clip.x));
  clip.height = Math.ceil(Math.min(y1 - y0 + 2 * M, 720 - clip.y));
  const others = Array.from(document.querySelectorAll('.react-flow__node')).filter((e) => {
      if (e === n || e.contains(n) || n.contains(e)) return false;
      const r = e.getBoundingClientRect();
      return r.x < clip.x + clip.width && r.x + r.width > clip.x && r.y < clip.y + clip.height && r.y + r.height > clip.y; })
    .map((e) => { const r = e.getBoundingClientRect();
      return { id: e.getAttribute('data-id'), aria: e.getAttribute('aria-label'),
        rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
        overlapPx: Math.round(Math.min(r.x + r.width, clip.x + clip.width) - Math.max(r.x, clip.x)) *
                    Math.round(Math.min(r.y + r.height, clip.y + clip.height) - Math.max(r.y, clip.y)) }; });
  const wanted = ['flow-node-title', 'video-node-player-bar', 'video-node-playback-toggle', 'video-node-player-clock',
    'video-node-mute-toggle', 'video-node-fullscreen-toggle', 'slider-track'];
  return { clip, used, others, union: `${Math.round(x0)},${Math.round(y0)} ${Math.round(x1 - x0)}×${Math.round(y1 - y0)}`,
    present: wanted.filter((t) => n.querySelector(`[data-testid="${t}"]`)), missing: wanted.filter((t) => !n.querySelector(`[data-testid="${t}"]`)) };
}, SELF);
log('收紧裁切：', JSON.stringify(out.crop, null, 1));
out.guardPass = out.crop.others.length === 0 && out.crop.missing.length === 0;
log('守卫：', out.guardPass ? '✅ 通过' : `🔴 不通过：clip 内还有 ${out.crop.others.length} 个他人节点`);

if (out.guardPass) {
  const buf = await p.screenshot({ type: 'png', clip: out.crop.clip });
  const f = new URL('102-video-card-player-bar.png', SHOT);
  writeFileSync(f, buf);
  out.shot = { file: f.pathname, bytes: buf.length, sha256: createHash('sha256').update(buf).digest('hex'), clip: out.crop.clip };
  log('📸 卡片播放态：', JSON.stringify(out.shot));
}
writeFileSync(new URL('./_tmp-b101c14.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();

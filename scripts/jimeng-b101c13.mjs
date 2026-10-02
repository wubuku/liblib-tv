// 批次 101 · c13 轮：在 **60% 档**重拍卡片播放态。
//
// c12 失败得很正确，守卫**两次都报了**，这正是它存在的意义：
//   ① **换缩放会顺带取消选中**（`sel: true` → `false`）⇒ 播放器整条 bar 消失，
//      `present` 只剩 `flow-node-title`，截图会拍成一张「没有控件」的卡片 —— 完全跑题。
//   ② **100% 档下两个别人的节点压在这张卡上**（`node_9y4j9jf0qv`、`node_d4tjtpnatq`，
//      其中一个是「时间线 2」）⇒ 共享画布，密集区。
// ⇒ 结论：**这一页的截图只能在 60% 档拍**，而且每次拍前都要**重新确认选中态**。
//    （缩放已由 c12 归位回 60%，连读两次 0.6/0.6 相同。）
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

out.z = await (async () => { const a = await scaleNow(); await p.waitForTimeout(900); const b2 = await scaleNow(); return [a, b2, a === b2]; })();
log('缩放连读：', JSON.stringify(out.z), '｜', await p.evaluate(() => document.querySelector('[data-testid="canvas-zoom-percent"]').getAttribute('aria-label')));
if (!out.z[2] || out.z[0] !== 0.6) { log('🔴 缩放不是稳定的 60% ⇒ 中止'); await b.close(); process.exit(1); }

// ---- 重新选中（c12 证明换档会掉选中） ----
async function selectSelf() {
  const before = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const v = n.querySelector('video,img'); const r = v.getBoundingClientRect();
    return { sel: n.classList.contains('selected'), screen: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
      inViewport: r.x + r.width > 0 && r.y + r.height > 0 && r.x < 1280 && r.y < 720 }; }, SELF);
  if (before.sel) { log('  已是选中态'); return before; }
  const pt = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const v = n.querySelector('video,img'); const r = v.getBoundingClientRect();
    const x = Math.round(r.x + r.width / 2), y = Math.round(r.y + r.height * 0.25);
    const el = document.elementFromPoint(x, y);
    return { point: [x, y], insideSelf: !!(el && el.closest(`.react-flow__node[data-id="${i}"]`)), hitTag: el ? el.tagName : null,
      inViewport: r.x + r.width > 0 && r.y + r.height > 0 && r.x < 1280 && r.y < 720 }; }, SELF);
  log('  重新选中落点：', JSON.stringify(pt));
  if (!pt.insideSelf || !pt.inViewport) return { ...before, failed: true };
  await p.mouse.move(pt.point[0], pt.point[1]); await p.waitForTimeout(400);
  await p.mouse.click(pt.point[0], pt.point[1]); await p.waitForTimeout(1400);
  const after = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const v = n.querySelector('video');
    return { sel: n.classList.contains('selected'), ct: v ? v.currentTime : null, paused: v ? v.paused : null }; }, SELF);
  log('  选中后：', JSON.stringify(after));
  return after;
}

out.sel = await selectSelf();

// ---- 起播到 ~2s ----
{
  const t = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const e = n.querySelector('[data-testid="video-node-playback-toggle"]'); if (!e) return null;
    const r = e.getBoundingClientRect();
    const x = Math.round(r.x + r.width / 2), y = Math.round(r.y + r.height / 2);
    const el = document.elementFromPoint(x, y);
    return { point: [x, y], inside: !!(el && (el === e || e.contains(el))) }; }, SELF);
  log('  播放钮落点：', JSON.stringify(t));
  if (t && t.inside) { await p.mouse.move(t.point[0], t.point[1]); await p.waitForTimeout(300);
    await p.mouse.click(t.point[0], t.point[1]); }
  await p.waitForTimeout(2000);
}
out.playing = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const v = n.querySelector('video'); const c = n.querySelector('[data-testid="video-node-player-clock"]');
  return { ct: v ? v.currentTime : null, paused: v ? v.paused : null,
    clock: c ? c.innerText.replace(/\s+/g, ' ').trim() : null,
    muteAria: (n.querySelector('[data-testid="video-node-mute-toggle"]') || {}).getAttribute?.('aria-label') || null }; }, SELF);
log('  播放态：', JSON.stringify(out.playing));

// ---- 裁切 + 守卫（批次 78 口径：可见后代并集 + 10px） ----
out.crop = await p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (const e of n.querySelectorAll('*')) { const r = e.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    x0 = Math.min(x0, r.x); y0 = Math.min(y0, r.y); x1 = Math.max(x1, r.x + r.width); y1 = Math.max(y1, r.y + r.height); }
  const M = 10;
  const clip = { x: Math.max(0, Math.floor(x0 - M)), y: Math.max(0, Math.floor(y0 - M)),
    width: Math.ceil(Math.min(x1 - x0 + 2 * M, 1280 - Math.max(0, Math.floor(x0 - M)))),
    height: Math.ceil(Math.min(y1 - y0 + 2 * M, 720 - Math.max(0, Math.floor(y0 - M)))) };
  const otherNodes = Array.from(document.querySelectorAll('.react-flow__node')).filter((e) => {
      if (e === n || e.contains(n) || n.contains(e)) return false;
      const r = e.getBoundingClientRect();
      return r.x < clip.x + clip.width && r.x + r.width > clip.x && r.y < clip.y + clip.height && r.y + r.height > clip.y; })
    .map((e) => ({ id: e.getAttribute('data-id'), aria: e.getAttribute('aria-label') }));
  const wanted = ['flow-node-title', 'video-node-player-bar', 'video-node-playback-toggle', 'video-node-player-clock',
    'video-node-mute-toggle', 'video-node-fullscreen-toggle', 'slider-track'];
  return { clip, union: `${Math.round(x0)},${Math.round(y0)} ${Math.round(x1 - x0)}×${Math.round(y1 - y0)}`,
    otherNodes, present: wanted.filter((t) => n.querySelector(`[data-testid="${t}"]`)), missing: wanted.filter((t) => !n.querySelector(`[data-testid="${t}"]`)) };
}, SELF);
log('裁切：', JSON.stringify(out.crop, null, 1));
out.guardPass = out.crop.otherNodes.length === 0 && out.crop.missing.length === 0;
log('守卫：', out.guardPass ? '✅ 通过（clip 内无他人节点 + 7 个目标 testid 齐）' : '🔴 不通过 ⇒ 不截图');

if (out.guardPass) {
  const buf = await p.screenshot({ type: 'png', clip: out.crop.clip });
  const f = new URL('102-video-card-player-bar.png', SHOT);
  writeFileSync(f, buf);
  out.shot = { file: f.pathname, bytes: buf.length, sha256: createHash('sha256').update(buf).digest('hex') };
  log('📸 卡片播放态：', JSON.stringify(out.shot));
}
writeFileSync(new URL('./_tmp-b101c13.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();

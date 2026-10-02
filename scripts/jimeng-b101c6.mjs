// 批次 101 · c6 轮：全屏播放器 + 音量滑杆（手册三项「未验证」里的最后一项）。
//
// c5 轮的结论：
//   ① **「选中即播」成立**：取消选中（sel 0）后再点卡片 → 从 0 自动开播（ct 1.61 / paused false / aria `Pause`）
//   ② 取消选中时：player bar 整个消失，`video-simple-player` **也不在**，
//      但 `<video>` 元素**仍留在 DOM 里**（ct=6, paused=true）⇒ 「播放停止」成立，
//      停止的方式是 **pause**（时间冻结）而不是卸载。
//   ③ **双击重播被证伪**：播放中双击 ct 4.19→5.81（一直前进）；暂停态双击 ct 3.60→3.60（纹丝不动）。
//      两种状态都不是「归零重播」⇒ 手册那条「未验证」项应改写成「**不存在该行为**」。
//
// 本轮：
//   A 取消选中态的**带媒体卡片**长什么样（手册只写了空卡片与选中卡片）
//   B 进全屏播放器 → 找出音量滑杆 → 拖动 → 看 video.volume 变不变
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString(), selfId: 'node_fxhrsbbfrz' };
const SELF = out.selfId;

// ---------- A：取消选中态的带媒体卡片 ----------
log('=== A 取消选中态的带媒体卡片 ===');
await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]');
  if (e && e.getAttribute('aria-label') !== '选择工具') e.click(); });
await p.waitForTimeout(400);
const blank = await p.evaluate(() => {
  const bad = (x, y) => { const el = document.elementFromPoint(x, y);
    if (!el || el.closest('.react-flow__node')) return true;
    if (x < 190 || y < 60 || y > 640 || x > 1120) return true;
    if (el.closest('button,[role=button],input,a')) return true; return false; };
  for (let y = 300; y < 620; y += 24) for (let x = 260; x < 1100; x += 24) if (!bad(x, y)) return [x, y];
  return null; });
if (blank) { await p.mouse.move(blank[0], blank[1]); await p.waitForTimeout(300); await p.mouse.click(blank[0], blank[1]); await p.waitForTimeout(1100); }
out.deselected = await p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { gone: true };
  const v = n.querySelector('video');
  return {
    sel: (document.body.innerText.match(/(\d+) selected/) || [])[1],
    cls: n.className,
    testids: Array.from(new Set(Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))),
    arias: Array.from(new Set(Array.from(n.querySelectorAll('[aria-label]')).map((e) => e.getAttribute('aria-label')))),
    hasVideo: !!v, ct: v ? v.currentTime : null, paused: v ? v.paused : null,
    hasImg: !!n.querySelector('img'),
    videoStyle: v ? (v.getAttribute('style') || '').slice(0, 120) : null,
    videoVisible: v ? (() => { const r = v.getBoundingClientRect(); return `${Math.round(r.width)}×${Math.round(r.height)}`; })() : null,
    innerText: n.innerText.replace(/\s+/g, ' ').trim(),
  };
}, SELF);
log(JSON.stringify(out.deselected, null, 1));

// ---------- B：全屏播放器 + 音量滑杆 ----------
log('\n=== B 全屏播放器 ===');
// 重新选中 → 起播 → 点全屏钮
const cardPt = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const e = n.querySelector('[data-testid="video-node-player-bar"]') ? n.querySelector('video') : n.querySelector('video,img');
  const r = e.getBoundingClientRect();
  const x = Math.round(r.x + r.width / 2), y = Math.round(r.y + r.height * 0.25);
  const el = document.elementFromPoint(x, y);
  return { point: [x, y], insideSelf: !!(el && el.closest(`.react-flow__node[data-id="${i}"]`)) }; }, SELF);
if (cardPt.insideSelf) { await p.mouse.move(cardPt.point[0], cardPt.point[1]); await p.waitForTimeout(300);
  await p.mouse.click(cardPt.point[0], cardPt.point[1]); await p.waitForTimeout(1300); }
out.beforeFs = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const v = n.querySelector('video');
  return { hasBar: !!n.querySelector('[data-testid="video-node-player-bar"]'), ct: v ? v.currentTime : null, paused: v ? v.paused : null }; }, SELF);
log('  进全屏前：', JSON.stringify(out.beforeFs));

const fsBtn = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const e = n.querySelector('[data-testid="video-node-fullscreen-toggle"]'); if (!e) return null;
  const r = e.getBoundingClientRect();
  return { point: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], aria: e.getAttribute('aria-label') }; }, SELF);
log('  全屏钮：', JSON.stringify(fsBtn));
if (fsBtn) {
  await p.mouse.move(fsBtn.point[0], fsBtn.point[1]); await p.waitForTimeout(350);
  await p.mouse.click(fsBtn.point[0], fsBtn.point[1]); await p.waitForTimeout(1600);
  out.fsState = await p.evaluate((i) => {
    const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const v = n.querySelector('video');
    // 全屏播放器很可能是挂在 body 下的独立浮层，要全文档找
    const docAll = Array.from(document.querySelectorAll('[role=slider],[class*=volume],[class*=Volume],[data-testid*=volume],[data-testid*=fullscreen],[data-testid*=player]'));
    return {
      inNode: !!n.querySelector('[data-testid="video-node-fullscreen-toggle"]'),
      nodeFullscreen: v ? v.webkitFullscreenElement === v : null,
      bodyFullscreenEl: (() => { const f = document.fullscreenElement; return f ? `${f.tagName}${f.getAttribute('data-testid') ? '#' + f.getAttribute('data-testid') : ''}${f.getAttribute('aria-label') ? '[' + f.getAttribute('aria-label') + ']' : ''}` : null; })(),
      vol: v ? v.volume : null, muted: v ? v.muted : null, ct: v ? v.currentTime : null, paused: v ? v.paused : null,
      sliders: docAll.map((e) => { const r = e.getBoundingClientRect();
        return { tag: e.tagName, role: e.getAttribute('role'), tid: e.getAttribute('data-testid'),
          cls: (e.className || '').toString().slice(0, 55),
          rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
          aria: e.getAttribute('aria-label'),
          vals: { min: e.getAttribute('aria-valuemin'), max: e.getAttribute('aria-valuemax'), now: e.getAttribute('aria-valuenow') } }; }),
    };
  }, SELF);
  log('  全屏态：', JSON.stringify({ inNode: out.fsState.inNode, bodyFullscreenEl: out.fsState.bodyFullscreenEl, vol: out.fsState.vol, ct: out.fsState.ct, paused: out.fsState.paused }));
  log('  全屏态里所有 slider / volume / player 元素：');
  for (const s of out.fsState.sliders) log('    ', JSON.stringify(s));
}

writeFileSync(new URL('./_tmp-b101c6.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();

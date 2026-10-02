// 批次 101 · c4 轮：进度条点击跳转 + 双击重播。
//
// c3 轮已结（全部为**推翻**或**证实**，没有含糊项）：
//   · 播完后控件行**不消失**，点 `video-node-playback-toggle` 会**从 0 重播**
//   · 暂停：currentTime 冻结（两次采样差 <0.02）｜**aria 翻回 `Play …`** ⇒ 推翻手册第 31-33 行
//   · 静音：aria `Unmute video` ↔ `Mute video` 翻转，`video.muted` 跟着变；默认 muted=true
//   · 播放/暂停钮只有 **10×10 屏上像素**（16×16 canvas）—— 极小的点，按钮内还套着 svg/path
//
// 本轮两项，都是手册标了「未验证 —— 因为没有带媒体的视频节点」的：
//   C 进度条点击跳转
//   D 双击重播
// ⚠️ 进度条本体是 `slider-track`（Radix slider）；`[role=slider]` 命中的是**滑块 thumb**，
//    它是 `0×0`（批次 98 的老教训：判非零高度的真身）。这里按 testid 取 `slider-track`。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString(), selfId: 'node_fxhrsbbfrz' };
const SELF = out.selfId;

const probe = () => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { gone: true };
  const v = n.querySelector('video');
  const t = n.querySelector('[data-testid="video-node-player-clock"]');
  const tr = n.querySelector('[data-testid="slider-track"]');
  const fill = tr ? tr.querySelector('[class*="player-progress-fill"]') : null;
  const thumb = tr ? tr.querySelector('[role=slider]') : null;
  const trr = tr ? tr.getBoundingClientRect() : null;
  return {
    ct: v ? v.currentTime : null, dur: v ? v.duration : null, paused: v ? v.paused : null, ended: v ? v.ended : null,
    clock: t ? t.innerText.replace(/\s+/g, ' ').trim() : null,
    pauseAria: (n.querySelector('[data-testid="video-node-playback-toggle"]') || {}).getAttribute?.('aria-label') || null,
    track: trr ? { x: Math.round(trr.x), y: Math.round(trr.y), w: Math.round(trr.width), h: Math.round(trr.height) } : null,
    thumbLeft: thumb ? (thumb.getAttribute('style') || '') : null,
    fillW: fill ? Math.round(fill.getBoundingClientRect().width * 100) / 100 : null,
    innerText: n.innerText.replace(/\s+/g, ' ').trim(),
  };
}, SELF);

async function clickAt(x, y, label) {
  const land = await p.evaluate(([px, py, i]) => {
    const el = document.elementFromPoint(px, py);
    return { hitTag: el ? el.tagName : null, hitTid: el ? el.getAttribute('data-testid') : null,
      hitCls: el ? (el.className || '').toString().slice(0, 60) : null,
      insideSelf: !!(el && el.closest(`.react-flow__node[data-id="${i}"]`)) };
  }, [x, y, SELF]);
  log(`  [${label}] @${x},${y} →`, JSON.stringify(land));
  if (!land.insideSelf) { log(`  🔴 ${label} 落点不在 SELF 节点内 ⇒ 跳过`); return false; }
  await p.mouse.move(x, y); await p.waitForTimeout(400);
  await p.mouse.click(x, y);
  return true;
}

// ================= 起手：确保在播 =================
out.s0 = await probe();
log('起手：', JSON.stringify({ ct: out.s0.ct, paused: out.s0.paused, clock: out.s0.clock, track: out.s0.track }));
if (out.s0.paused) {
  const ok = await p.evaluate((i) => {
    const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const e = n.querySelector('[data-testid="video-node-playback-toggle"]');
    if (!e) return null; const r = e.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
  }, SELF);
  if (ok) { await p.mouse.move(ok[0], ok[1]); await p.waitForTimeout(300); await p.mouse.click(ok[0], ok[1]); await p.waitForTimeout(1000); }
  out.s1 = await probe(); log('  已起播：', JSON.stringify({ ct: out.s1.ct, paused: out.s1.paused, clock: out.s1.clock }));
}

// ================= C 进度条点击跳转 =================
log('\n=== C 进度条点击跳转 ===');
out.C = [];
for (const frac of [0.25, 0.5, 0.8, 0.05]) {
  const tr = out.s0.track || (await probe()).track;
  if (!tr) { log('  🔴 找不到 slider-track'); break; }
  const x = Math.round(tr.x + tr.w * frac), y = Math.round(tr.y + tr.h / 2);
  const before = await probe();
  const ok = await clickAt(x, y, `进度条 ${Math.round(frac * 100)}%`);
  if (!ok) continue;
  await p.waitForTimeout(650);
  const after = await probe();
  const row = { frac, x, y, beforeCt: before.ct, afterCt: after.ct, beforeClock: before.clock, afterClock: after.clock,
    expectCt: tr.w > 0 ? (frac * (before.dur || 6)).toFixed(2) : null, fillW: after.fillW, thumbLeft: after.thumbLeft };
  row.landed = after.ct !== null && before.ct !== null && Math.abs(after.ct - before.ct) > 0.4;
  row.accurate = row.landed && Math.abs(after.ct - frac * (before.dur || 6)) < 1.0;
  out.C.push(row);
  log(`  ${Math.round(frac * 100)}%：ct ${before.ct} → ${after.ct}（期望≈${row.expectCt}）｜clock ${before.clock} → ${after.clock}｜落点=${row.landed} 准=${row.accurate}`);
}

// ================= D 双击重播 =================
log('\n=== D 双击重播 ===');
// 先把进度推到中段（~3s），双击才能测出「是否归零」
{
  const tr = (await probe()).track;
  const x = Math.round(tr.x + tr.w * 0.5), y = Math.round(tr.y + tr.h / 2);
  if (tr) { await p.mouse.move(x, y); await p.waitForTimeout(300); await p.mouse.click(x, y); }
  await p.waitForTimeout(1200);
}
out.D0 = await probe();
log('  双击前：', JSON.stringify({ ct: out.D0.ct, paused: out.D0.paused, clock: out.D0.clock }));

// 双击落在**视频画面区**（避开底部控件行，也避开标题栏）
const dbl = await p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const v = n.querySelector('video'); const r = v ? v.getBoundingClientRect() : null;
  if (!r) return null;
  const x = Math.round(r.x + r.width * 0.35), y = Math.round(r.y + r.height * 0.3);
  const el = document.elementFromPoint(x, y);
  return { point: [x, y], rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
    hitTag: el ? el.tagName : null, insideSelf: !!(el && el.closest(`.react-flow__node[data-id="${i}"]`)) };
}, SELF);
log('  双击落点：', JSON.stringify(dbl));
out.D_land = dbl;
if (dbl && dbl.insideSelf) {
  await p.mouse.move(dbl.point[0], dbl.point[1]); await p.waitForTimeout(400);
  await p.mouse.click(dbl.point[0], dbl.point[1], { clickCount: 2, delay: 90 });
  await p.waitForTimeout(900);
  out.D1 = await probe();
  log('  双击后：', JSON.stringify({ ct: out.D1.ct, paused: out.D1.paused, clock: out.D1.clock }));
  out.D_reset = out.D1.ct !== null && out.D1.ct < (out.D0.ct || 0) - 0.3;
  out.D_playing = out.D1.paused === false;
  log('  ⇒ 双击是否归零重播？', out.D_reset, '｜是否在播？', out.D_playing);
}

out.end = await probe();
log('\n终态：', JSON.stringify({ ct: out.end.ct, paused: out.end.paused, clock: out.end.clock }));
writeFileSync(new URL('./_tmp-b101c4.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();

// 批次 101 · c3 轮：卡片播放控件的四个动作 —— 暂停 / 静音翻转 / 进度条跳转 / 双击重播。
//
// c2 轮已把「控件行是播放时才挂载的」这件事钉死：
//   静止  : video-simple-player (BUTTON 44×44, 卡片正中, aria `Play …`)，无 <video>、无时间、无进度条
//   播放中: video-node-player-bar / -controls 出现，含
//           video-node-playback-toggle (16×16, `Pause …`)、video-node-player-clock、
//           video-node-mute-toggle (36×36, `Unmute video`)、
//           video-node-fullscreen-toggle (36×36, `Enter browser full screen`)、
//           slider-track (Radix slider, aria `Seek …`)
// ⇒ 手册第 20-27 行那套控件**是条件存在的**，手册没写这个前提。
//
// 本轮要回答的四个问题：
//   A 暂停：aria 会不会翻回 `Play`？currentTime 会不会真停？（手册第 31-33 行断言「aria 不翻转」）
//   B 静音：aria 翻不翻？video.muted 跟不跟着变？
//   C 进度条：点击能不能跳？跳到哪儿？时间读数跟不跟着走？
//   D 双击：双击是不是「从头重播」？
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString(), selfId: 'node_fxhrsbbfrz' };
const SELF = out.selfId;

// ---- 读数：一次读全，**aria 与 DOM 状态一起读**（aria 会骗人，paused/currentTime 不会）----
const probe = () => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { gone: true };
  const v = n.querySelector('video');
  const g = (sel) => n.querySelector(sel);
  const ariaOf = (sel) => { const e = g(sel); return e ? e.getAttribute('aria-label') : null; };
  const rct = (sel) => { const e = g(sel); if (!e) return null; const r = e.getBoundingClientRect();
    return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; };
  const track = g('[data-testid="slider-track"]');
  const seekAria = Array.from(n.querySelectorAll('[aria-label]'))
    .map((e) => ({ tag: e.tagName, tid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label') }))
    .filter((x) => /seek/i.test(x.aria || ''));
  return {
    hasBar: !!g('[data-testid="video-node-player-bar"]'),
    pauseAria: ariaOf('[data-testid="video-node-playback-toggle"]'),
    playAria: ariaOf('[data-testid="video-simple-player"]'),
    muteAria: ariaOf('[data-testid="video-node-mute-toggle"]'),
    fullAria: ariaOf('[data-testid="video-node-fullscreen-toggle"]'),
    clock: g('[data-testid="video-node-player-clock"]') ? g('[data-testid="video-node-player-clock"]').innerText.replace(/\s+/g, ' ').trim() : null,
    paused: v ? v.paused : null, ct: v ? v.currentTime : null, dur: v ? v.duration : null,
    muted: v ? v.muted : null, vol: v ? v.volume : null, ended: v ? v.ended : null,
    vRect: rct('video'), toggleRect: rct('[data-testid="video-node-playback-toggle"]'),
    muteRect: rct('[data-testid="video-node-mute-toggle"]'),
    trackRect: track ? (() => { const r = track.getBoundingClientRect();
      return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; })() : null,
    trackCls: track ? track.className.slice(0, 90) : null,
    seekAria, innerText: n.innerText.replace(/\s+/g, ' ').trim(),
  };
}, SELF);

// ---- 落点校验 + 真实鼠标点击：判据 =「落点属于 SELF 节点」且「落点落在目标元素内」 ----
async function clickIn(sel, label, frac = 0.5) {
  const land = await p.evaluate(([i, s, f]) => {
    const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const e = n.querySelector(s);
    if (!e) return { missing: true };
    const r = e.getBoundingClientRect();
    const x = Math.round(r.x + r.width * f), y = Math.round(r.y + r.height / 2);
    const el = document.elementFromPoint(x, y);
    return { point: [x, y], rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
      hitTag: el ? el.tagName : null, hitTid: el ? el.getAttribute('data-testid') : null,
      insideSelf: !!(el && el.closest(`.react-flow__node[data-id="${i}"]`)),
      insideTarget: !!(el && (el === e || e.contains(el))) };
  }, [SELF, sel, frac]);
  log(`  [${label}] 落点：`, JSON.stringify(land));
  if (land.missing || !land.insideSelf || !land.insideTarget) { log(`  🔴 ${label} 落点判失败 ⇒ 跳过该动作`); return false; }
  await p.mouse.move(land.point[0], land.point[1]); await p.waitForTimeout(450);
  await p.mouse.click(land.point[0], land.point[1]);
  return true;
}

// ================= 起手：确保处于「播放中」 =================
// 🔑 **播完之后控件行不消失**（c3 首次撞上）：ct=6 / paused=true / bar 仍在，
//    播放钮 aria 已翻回 `Play`，而**大播放键 `video-simple-player` 已不在 DOM 里**。
//    ⇒ 「点一下重播」要点的是那个 `16×16` 的 `video-node-playback-toggle`，不是大播放键。
//    这本身也是手册没写的一条（手册只说「取消 / 恢复：点击空白取消选中，播放停止」）。
out.s0 = await probe();
log('起手：', JSON.stringify({ bar: out.s0.hasBar, pauseAria: out.s0.pauseAria, ct: out.s0.ct, paused: out.s0.paused, ended: out.s0.ended, clock: out.s0.clock }));
if (out.s0.paused || out.s0.ct === null || out.s0.ended) {
  const sel = out.s0.hasBar ? '[data-testid="video-node-playback-toggle"]' : '[data-testid="video-simple-player"]';
  log('  用', sel, '起播');
  if (!(await clickIn(sel, '起播', 0.5))) { log('🔴 播不起来'); writeFileSync(new URL('./_tmp-b101c3.json', import.meta.url), JSON.stringify(out, null, 1)); await b.close(); process.exit(1); }
  await p.waitForTimeout(1400);
  out.s1 = await probe();
  log('  点后立刻：', JSON.stringify({ bar: out.s1.hasBar, pauseAria: out.s1.pauseAria, ct: out.s1.ct, paused: out.s1.paused, ended: out.s1.ended, clock: out.s1.clock }));
  // 若点「Play」后仍停在 6 秒不动 ⇒ 说明它不自动归零，这条要单独记
  out.replayFromEnd = !(out.s1.ct !== null && out.s1.ct < 5.5) && !out.s1.paused;
  log('  ⇒ 播完后点 Play 会从 0 重播吗？', out.s1.ct, out.replayFromEnd ? '（未归零，判否）' : '（归零，判是）');
}

// ================= A 暂停 =================
log('\n=== A 暂停 ===');
if (await clickIn('[data-testid="video-node-playback-toggle"]', 'Pause 钮')) {
  await p.waitForTimeout(700);
  out.A1 = await probe();
  await p.waitForTimeout(1100);
  out.A2 = await probe();
  log('  暂停后 t1：', JSON.stringify({ pauseAria: out.A1.pauseAria, playAria: out.A1.playAria, ct: out.A1.ct, paused: out.A1.paused, clock: out.A1.clock, bar: out.A1.hasBar }));
  log('  暂停后 t2：', JSON.stringify({ pauseAria: out.A2.pauseAria, ct: out.A2.ct, paused: out.A2.paused, clock: out.A2.clock, bar: out.A2.hasBar }));
  out.A_frozen = out.A1.ct !== null && out.A2.ct !== null && Math.abs(out.A1.ct - out.A2.ct) < 0.02;
  out.A_ariaFlips = out.A2.pauseAria !== null && /^Play /.test(out.A2.pauseAria);
  log('  ⇒ 时间冻结？', out.A_frozen, '｜aria 翻回 Play？', out.A_ariaFlips, `（读作「${out.A2.pauseAria}」）`);
}

// ================= B 静音翻转 =================
log('\n=== B 静音翻转 ===');
out.B0 = await probe();
log('  点击前：', JSON.stringify({ muteAria: out.B0.muteAria, muted: out.B0.muted, vol: out.B0.vol }));
if (await clickIn('[data-testid="video-node-mute-toggle"]', 'Mute 钮')) {
  await p.waitForTimeout(800);
  out.B1 = await probe();
  log('  点击后：', JSON.stringify({ muteAria: out.B1.muteAria, muted: out.B1.muted, vol: out.B1.vol }));
  out.B_flips = out.B0.muteAria !== out.B1.muteAria;
  out.B_follows = out.B0.muted !== out.B1.muted;
  log('  ⇒ aria 翻转？', out.B_flips, '｜ video.muted 跟着变？', out.B_follows);
  // 还原
  if (await clickIn('[data-testid="video-node-mute-toggle"]', 'Mute 钮（还原）')) await p.waitForTimeout(700);
  out.B2 = await probe();
  log('  还原后：', JSON.stringify({ muteAria: out.B2.muteAria, muted: out.B2.muted }));
}

writeFileSync(new URL('./_tmp-b101c3.json', import.meta.url), JSON.stringify(out, null, 1));
log('\n（进度条与双击留给 c4，先把 A/B 的落盘存住）');
await b.close();

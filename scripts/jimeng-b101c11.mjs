// 批次 101 · c11 轮：把 c10 的两处判据错误修掉重测。
//
// 🔴 **c10 的两处自伤**（都是判据/顺序问题，不是页面问题）：
//   ① `bar.querySelector('[data-testid="slider-track"]')` 取的是**第一条** ——
//      那是 **seek 条**（`16,659 1248×2`），不是音量条（`1124,691 52×2`）。
//      ⇒ 拖拽目标点全算错（`trackX=16, trackW=1248`）。
//      **正路**：从 `aria-valuemax="1"` 的 thumb 反查 —— `thumb.parentElement.parentElement` 才是音量条那一族。
//   ② 步骤③排在步骤②之后，而②已经退出全屏 ⇒ `video-fullscreen-mute-toggle` 为 null，脚本崩在半路。
//      **顺序错了**：所有「全屏态内」的测量必须排在「退出全屏」之前。
//
// c10 的**真结论**（不受上面两条影响）：
//   · **退出全屏的正确操作是点「全屏钮」本身**（`video-fullscreen-browser-toggle`，aria 仍是「Enter browser full screen」）✅
//   · c9 那次拖动之所以把音量拖成 0，是因为我把点拖到了 x=390，
//     **远在音量条（1124–1176）左边界之外 ⇒ 被钳到 0**。这恰恰证明拖动是**跟手的**。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString(), selfId: 'node_fxhrsbbfrz' };
const SELF = out.selfId;

// ---- 读数：音量条用「从 thumb 反查」定位，seek 条按 vmax≠1 排除 ----
const st = () => p.evaluate(() => {
  const v = document.querySelector('video');
  const bar = document.querySelector('[data-testid="video-fullscreen-player-bar"]');
  const thumbs = bar ? Array.from(bar.querySelectorAll('[role=slider]')) : [];
  const volThumb = thumbs.find((e) => e.getAttribute('aria-valuemax') === '1') || null;
  const seekThumb = thumbs.find((e) => e.getAttribute('aria-valuemax') !== '1') || null;
  const volFamily = volThumb ? volThumb.parentElement.parentElement : null;      // 52×16 那一族
  const volTrack = volFamily ? volFamily.querySelector('[data-testid="slider-track"]') : null;
  const seekTrack = bar ? Array.from(bar.querySelectorAll('[data-testid="slider-track"]')).find((e) => e !== volTrack) : null;
  const R = (e) => { if (!e) return null; const r = e.getBoundingClientRect();
    return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height),
      cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; };
  return { inFs: !!document.fullscreenElement, ct: v ? v.currentTime : null, paused: v ? v.paused : null,
    vol: v ? v.volume : null, muted: v ? v.muted : null,
    playAria: (document.querySelector('[data-testid="video-fullscreen-playback-toggle"]') || {}).getAttribute?.('aria-label') || null,
    muteAria: (document.querySelector('[data-testid="video-fullscreen-mute-toggle"]') || {}).getAttribute?.('aria-label') || null,
    volNow: volThumb ? volThumb.getAttribute('aria-valuenow') : null,
    volThumb: R(volThumb), volTrack: R(volTrack), volFamily: R(volFamily),
    seekThumb: R(seekThumb), seekTrack: R(seekTrack) };
});

async function clickTid(tid) {
  const t = await p.evaluate((s) => { const e = document.querySelector(`[data-testid="${s}"]`); if (!e) return null;
    const r = e.getBoundingClientRect();
    const x = Math.round(r.x + r.width / 2), y = Math.round(r.y + r.height / 2);
    const el = document.elementFromPoint(x, y);
    return { point: [x, y], inside: !!(el && (el === e || e.contains(el))) }; }, tid);
  if (!t || !t.inside) { log(`  [${tid}] 落点判失败：`, JSON.stringify(t)); return false; }
  await p.mouse.move(t.point[0], t.point[1]); await p.waitForTimeout(350);
  await p.mouse.click(t.point[0], t.point[1]); return true;
}

// ================= 回到卡片态 =================
log('=== 回到卡片态 ===');
let s0 = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const v = n.querySelector('video');
  return { sel: (document.body.innerText.match(/(\d+) selected/) || [])[1], hasBar: !!n.querySelector('[data-testid="video-node-player-bar"]'),
    ct: v ? v.currentTime : null, paused: v ? v.paused : null, vol: v ? v.volume : null, muted: v ? v.muted : null }; }, SELF);
log('  卡片态：', JSON.stringify(s0));
// 取消选中 → 再选中（选中即播，c5 已验证），顺便把音量恢复到有声音的状态
{
  const blank = await p.evaluate(() => { const bad = (x, y) => { const el = document.elementFromPoint(x, y);
      if (!el || el.closest('.react-flow__node')) return true;
      if (x < 190 || y < 60 || y > 640 || x > 1120) return true;
      if (el.closest('button,[role=button],input,a')) return true; return false; };
    for (let y = 300; y < 620; y += 24) for (let x = 260; x < 1100; x += 24) if (!bad(x, y)) return [x, y]; return null; });
  if (blank) { await p.mouse.move(blank[0], blank[1]); await p.waitForTimeout(300); await p.mouse.click(blank[0], blank[1]); await p.waitForTimeout(900); }
  const c = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const v = n.querySelector('video,img'); const r = v.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height * 0.25)]; }, SELF);
  await p.mouse.move(c[0], c[1]); await p.waitForTimeout(300); await p.mouse.click(c[0], c[1]); await p.waitForTimeout(1400);
}
log('  重新选中后：', JSON.stringify(await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const v = n.querySelector('video');
  return { hasBar: !!n.querySelector('[data-testid="video-node-player-bar"]'), ct: v ? v.currentTime : null, paused: v ? v.paused : null,
    muteAria: (n.querySelector('[data-testid="video-node-mute-toggle"]') || {}).getAttribute?.('aria-label') || null,
    hasFullBtn: !!n.querySelector('[data-testid="video-node-fullscreen-toggle"]') }; }, SELF)));

// ---- 进全屏 ----
if (!(await clickTid('video-node-fullscreen-toggle'))) { log('🔴 进不去全屏 ⇒ 中止'); await b.close(); process.exit(1); }
await p.waitForTimeout(1600);
s0 = await st();
log('  全屏态：', JSON.stringify({ inFs: s0.inFs, volTrack: s0.volTrack, volFamily: s0.volFamily, volThumb: s0.volThumb, volNow: s0.volNow, vol: s0.vol }));
out.fsIn = s0;

// ================= ① 音量滑杆逐步映射（这次用对轨道） =================
log('\n=== ① 音量滑杆逐步映射（用音量条自己的坐标）===');
if (s0.volThumb && s0.volTrack) {
  const tr = s0.volTrack, th = s0.volThumb;
  out.dragSteps = [];
  // 先把音量顶到 1，方便往左走
  await p.mouse.move(th.cx, th.cy); await p.waitForTimeout(300); await p.mouse.down(); await p.waitForTimeout(200);
  await p.mouse.move(tr.x + tr.w, th.cy, { steps: 8 }); await p.waitForTimeout(400);
  await p.mouse.up(); await p.waitForTimeout(600);
  const top = await st();
  log('  顶到最右：', JSON.stringify({ now: top.volNow, vol: top.vol }));
  await p.mouse.move(top.volThumb.cx, top.volThumb.cy); await p.waitForTimeout(300);
  await p.mouse.down(); await p.waitForTimeout(250);
  for (const frac of [0.8, 0.6, 0.4, 0.2]) {
    const x = Math.round(tr.x + tr.w * frac);
    await p.mouse.move(x, th.cy, { steps: 8 }); await p.waitForTimeout(350);
    const q = await st();
    const row = { frac: Math.round(frac * 100) / 100, x, valNow: q.volNow, vol: q.vol, thumbCx: q.volThumb && q.volThumb.cx };
    out.dragSteps.push(row);
    log(`  拖到 ${Math.round(frac * 100)}%（x=${x}）→ valuenow=${q.volNow}｜volume=${q.vol}｜thumb中心=${q.volThumb && q.volThumb.cx}`);
  }
  await p.mouse.up(); await p.waitForTimeout(600);
  out.afterDrag = await st();
  out.dragLinear = out.dragSteps.every((r) => r.valNow !== null && Math.abs(Number(r.valNow) - r.frac) < 0.15);
  log('  ⇒ 映射近似线性？', out.dragLinear, '｜松手后：', JSON.stringify({ now: out.afterDrag.volNow, vol: out.afterDrag.vol }));
}

// ================= ② 点静音钮会不会连带开播（全屏态内，最后一步之前） =================
log('\n=== ② 点静音钮会不会连带开播 ===');
{
  let s = await st();
  if (!s.paused) { await clickTid('video-fullscreen-playback-toggle'); await p.waitForTimeout(700); }
  s = await st();
  out.m0 = { ct: s.ct, paused: s.paused, muted: s.muted, muteAria: s.muteAria, vol: s.vol };
  log('  定格：', JSON.stringify(out.m0));
  if (s.muteAria) {
    await clickTid('video-fullscreen-mute-toggle'); await p.waitForTimeout(800);
    const s2 = await st();
    out.m1 = { ct: s2.ct, paused: s2.paused, muted: s2.muted, muteAria: s2.muteAria, playAria: s2.playAria };
    out.muteClickStartsPlaying = out.m0.paused === true && out.m1.paused === false;
    log('  点静音钮后：', JSON.stringify(out.m1));
    log('  ⇒ 点静音钮会连带开播？', out.muteClickStartsPlaying);
  } else log('  ⓘ 起点无静音钮，跳过');
}

// ================= ③ 退出全屏（回卡片） =================
log('\n=== ③ 退出全屏 ===');
{
  const before = await st();
  const ok = await clickTid('video-fullscreen-browser-toggle');
  await p.waitForTimeout(1500);
  const after = await st();
  out.exit = { clicked: ok, beforeInFs: before.inFs, afterInFs: after.inFs };
  log('  ', JSON.stringify(out.exit));
  if (!after.inFs) {
    out.backToCard = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
      const v = n.querySelector('video');
      return { sel: (document.body.innerText.match(/(\d+) selected/) || [])[1],
        hasBar: !!n.querySelector('[data-testid="video-node-player-bar"]'),
        hasFullBtn: !!n.querySelector('[data-testid="video-node-fullscreen-toggle"]'),
        ct: v ? v.currentTime : null, paused: v ? v.paused : null, vol: v ? v.volume : null, muted: v ? v.muted : null }; }, SELF);
    log('  回到卡片：', JSON.stringify(out.backToCard));
  }
}

writeFileSync(new URL('./_tmp-b101c11.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();

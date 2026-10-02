// 批次 101 · c10 轮：① 音量滑杆的**逐步映射**（c9 只读到起点和终点，中间是黑的）
//                            ② **全屏怎么退**（Esc 已被 c8 证伪三次；容器里只有 3 个钮，**没有 X 关闭钮**）
//                            ③ 受控复测「点解除静音会连带开播」（c7 单次观测，c9 因已取消静音而跳过）
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString(), selfId: 'node_fxhrsbbfrz' };

const st = () => p.evaluate(() => {
  const v = document.querySelector('video');
  const bar = document.querySelector('[data-testid="video-fullscreen-player-bar"]');
  const thumbs = bar ? Array.from(bar.querySelectorAll('[role=slider]')) : [];
  const vol = thumbs.find((e) => e.getAttribute('aria-valuemax') === '1');
  const tr = bar ? bar.querySelector('[data-testid="slider-track"]') : null;
  return { inFs: !!document.fullscreenElement, ct: v ? v.currentTime : null, paused: v ? v.paused : null,
    vol: v ? v.volume : null, muted: v ? v.muted : null,
    playAria: (document.querySelector('[data-testid="video-fullscreen-playback-toggle"]') || {}).getAttribute?.('aria-label') || null,
    muteAria: (document.querySelector('[data-testid="video-fullscreen-mute-toggle"]') || {}).getAttribute?.('aria-label') || null,
    volNow: vol ? vol.getAttribute('aria-valuenow') : null,
    volCx: vol ? (() => { const r = vol.getBoundingClientRect(); return Math.round(r.x + r.width / 2); })() : null,
    volCy: vol ? (() => { const r = vol.getBoundingClientRect(); return Math.round(r.y + r.height / 2); })() : null,
    trackX: tr ? Math.round(tr.getBoundingClientRect().x) : null,
    trackW: tr ? Math.round(tr.getBoundingClientRect().width) : null,
    trackY: tr ? Math.round(tr.getBoundingClientRect().y + tr.getBoundingClientRect().height / 2) : null };
});

if (!(await st()).inFs) { log('🔴 已不在全屏 ⇒ 中止'); writeFileSync(new URL('./_tmp-b101c10.json', import.meta.url), JSON.stringify(out, null, 1)); await b.close(); process.exit(1); }

// ================= ① 音量滑杆逐步映射 =================
log('=== ① 音量滑杆逐步映射（按住 thumb 往左走，每步读一次）===');
{
  let s = await st();
  log('  起点：', JSON.stringify({ now: s.volNow, vol: s.vol, cx: s.volCx, trackX: s.trackX, trackW: s.trackW }));
  await p.mouse.move(s.volCx, s.volCy); await p.waitForTimeout(350);
  await p.mouse.down(); await p.waitForTimeout(250);
  out.dragSteps = [];
  const left = s.trackX + s.trackW;
  for (const frac of [0.75, 0.5, 0.3, 0.1, 0]) {
    const x = Math.round(s.trackX + s.trackW * frac);
    await p.mouse.move(x, s.trackY, { steps: 6 }); await p.waitForTimeout(320);
    const q = await st();
    const row = { frac, x, valNow: q.volNow, vol: q.vol, thumbCx: q.volCx,
      expect: Math.round(frac * 100) / 100 };
    out.dragSteps.push(row);
    log(`  拖到 ${Math.round(frac * 100)}%（x=${x}）→ valuenow=${q.volNow}｜video.volume=${q.vol}｜thumb 中心=${q.volCx}`);
  }
  await p.mouse.up(); await p.waitForTimeout(500);
  out.afterDrag = await st();
  out.dragLinear = out.dragSteps.every((r) => r.valNow !== null && Math.abs(Number(r.valNow) - r.expect) < 0.12);
  log('  ⇒ 拖动映射是否近似线性（|实测-期望|<0.12）？', out.dragLinear);
}

// ================= ② 退出全屏 =================
log('\n=== ② 怎么退出全屏 ===');
{
  const t = await p.evaluate(() => { const e = document.querySelector('[data-testid="video-fullscreen-browser-toggle"]');
    if (!e) return null; const r = e.getBoundingClientRect();
    const x = Math.round(r.x + r.width / 2), y = Math.round(r.y + r.height / 2);
    const el = document.elementFromPoint(x, y);
    return { point: [x, y], inside: !!(el && (el === e || e.contains(el))), aria: e.getAttribute('aria-label') }; });
  log('  browser-toggle 落点：', JSON.stringify(t));
  if (t && t.inside) { await p.mouse.move(t.point[0], t.point[1]); await p.waitForTimeout(350);
    await p.mouse.click(t.point[0], t.point[1]); await p.waitForTimeout(1400); }
  out.afterBrowserToggle = await st();
  log('  点后：', JSON.stringify({ inFs: out.afterBrowserToggle.inFs, playAria: out.afterBrowserToggle.playAria, vol: out.afterBrowserToggle.vol, muted: out.afterBrowserToggle.muted }));
  out.browserToggleExits = !out.afterBrowserToggle.inFs;
  if (!out.afterBrowserToggle.inFs) log('  ⇒ browser-toggle 退出全屏 ✅');
}

// ================= ③ 解除静音是否连带开播（受控） =================
log('\n=== ③ 解除静音是否连带开播（受控复测）===');
{
  let s = await st();
  // 先确保处于「暂停 + 已取消静音」，再点静音钮取消静音（这一步会不会开播？）
  if (!s.paused) { const t = await p.evaluate(() => { const e = document.querySelector('[data-testid="video-fullscreen-playback-toggle"]');
      const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
    await p.mouse.move(t[0], t[1]); await p.waitForTimeout(300); await p.mouse.click(t[0], t[1]); await p.waitForTimeout(700); }
  s = await st();
  out.m0 = s;
  log('  定格：', JSON.stringify({ ct: s.ct, paused: s.paused, muted: s.muted, muteAria: s.muteAria }));
  if (!s.muted) {
    const t = await p.evaluate(() => { const e = document.querySelector('[data-testid="video-fullscreen-mute-toggle"]');
      const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
    await p.mouse.move(t[0], t[1]); await p.waitForTimeout(300); await p.mouse.click(t[0], t[1]); await p.waitForTimeout(700);
    out.m1 = await st();
    out.muteClickStartsPlaying = out.m0.paused === true && out.m1.paused === false;
    log('  点「取消静音」后：', JSON.stringify({ ct: out.m1.ct, paused: out.m1.paused, muted: out.m1.muted }));
    log('  ⇒ 点静音钮会连带开播？', out.muteClickStartsPlaying);
    // 还原成「已取消静音」便于后续
    if (out.m1.muted) { const t2 = await p.evaluate(() => { const e = document.querySelector('[data-testid="video-fullscreen-mute-toggle"]');
      const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
      await p.mouse.move(t2[0], t2[1]); await p.waitForTimeout(300); await p.mouse.click(t2[0], t2[1]); await p.waitForTimeout(700); }
  } else { out.muteClickStartsPlaying = null; log('  ⓘ 起点就是静音态，本项跳过（不硬凑）'); }
}

out.end = await st();
log('\n终态：', JSON.stringify({ inFs: out.end.inFs, ct: out.end.ct, paused: out.end.paused, vol: out.end.vol, muted: out.end.muted }));
writeFileSync(new URL('./_tmp-b101c10.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();

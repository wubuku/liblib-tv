// 批次 101 · c9 轮：拖音量滑杆 + 受控复测「解除静音会连带开播」+ 找出全屏的退出口。
//
// c8 轮把全屏条 34 个后代全导了出来，得到三条硬事实：
//   ① **thumb 不是 `slider-track` 的后代**，而是它的**兄弟**：
//        SPAN 1124,684 52×16          ← 可点区（真身高 16，不是 2）
//          ├── SPAN#slider-track 1124,691 52×2
//          └── SPAN 1168,688 8×8
//              └── SPAN[role=slider] vmin=0 **vmax=1** vnow=1
//      ⇒ 两条 slider 靠 **`aria-valuemax` 区分**：seek 的 vmax = 素材时长（6），volume 的 vmax = 1。
//   ② 时间读数是**三个 SPAN**：`0:06` ／ `4×14` 的分隔条 ／ `0:06`
//      —— 全屏格式**无前导零**（`0:06`），与卡片内 `00:06` 不同，这条手册已写对。
//   ③ **Esc 连按三次都退不出全屏**，也不改播放态（ct 6 / paused 恒定）。
//      ⇒ 手册第 42 行「按 Esc 退出」**不成立**。
//
// ⚠️ c7 里「点解除静音 ⇒ 视频从 0 重新开播」是**只发生一次**的观测，本轮受控复测（先定格再点）。
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
  const seek = thumbs.find((e) => e.getAttribute('aria-valuemax') !== '1');
  const g = (e) => { if (!e) return null; const r = e.getBoundingClientRect();
    return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2), w: Math.round(r.width), h: Math.round(r.height),
      now: e.getAttribute('aria-valuenow') }; };
  return { inFs: !!document.fullscreenElement, ct: v ? v.currentTime : null, paused: v ? v.paused : null,
    vol: v ? v.volume : null, muted: v ? v.muted : null,
    playAria: (document.querySelector('[data-testid="video-fullscreen-playback-toggle"]') || {}).getAttribute?.('aria-label') || null,
    muteAria: (document.querySelector('[data-testid="video-fullscreen-mute-toggle"]') || {}).getAttribute?.('aria-label') || null,
    clock: (() => { const c = document.querySelector('[data-testid="video-fullscreen-player-clock"]');
      return c ? c.innerText.replace(/\s+/g, ' ').trim() : null; })(),
    volThumb: g(vol), seekThumb: g(seek) };
});

async function clickTid(tid) {
  const t = await p.evaluate((s) => { const e = document.querySelector(`[data-testid="${s}"]`); if (!e) return null;
    const r = e.getBoundingClientRect();
    const x = Math.round(r.x + r.width / 2), y = Math.round(r.y + r.height / 2);
    const el = document.elementFromPoint(x, y);
    return { point: [x, y], inside: !!(el && (el === e || e.contains(el))), hitTag: el ? el.tagName : null }; }, tid);
  if (!t || !t.inside) { log(`  [${tid}] 落点判失败：`, JSON.stringify(t)); return false; }
  log(`  [${tid}] 落点：`, JSON.stringify(t));
  await p.mouse.move(t.point[0], t.point[1]); await p.waitForTimeout(350);
  await p.mouse.click(t.point[0], t.point[1]); return true;
}

// ================= ① 受控复测：定格 → 点静音钮 → 会不会开播 =================
log('=== ① 定格后点解除静音，会不会连带开播 ===');
// 先定格：点 seek 轨道到 ~50%，再点播放钮暂停
{
  const g = await p.evaluate(() => { const bar = document.querySelector('[data-testid="video-fullscreen-player-bar"]');
    const tr = bar.querySelector('[data-testid="slider-track"]'); const r = tr.getBoundingClientRect();
    return { x: Math.round(r.x + r.width * 0.5), y: Math.round(r.y + r.height / 2) }; });
  await p.mouse.move(g.x, g.y); await p.waitForTimeout(300); await p.mouse.click(g.x, g.y); await p.waitForTimeout(500);
  const s = await st();
  if (!s.paused) { await clickTid('video-fullscreen-playback-toggle'); await p.waitForTimeout(700); }
}
out.r0 = await st();
log('  定格：', JSON.stringify({ ct: out.r0.ct, paused: out.r0.paused, playAria: out.r0.playAria, clock: out.r0.clock }));
if (out.r0.muted) {
  await clickTid('video-fullscreen-mute-toggle'); await p.waitForTimeout(900);
  out.r1 = await st();
  out.unmuteStartsPlaying = out.r0.paused === true && out.r1.paused === false;
  log('  点解除静音后：', JSON.stringify({ ct: out.r1.ct, paused: out.r1.paused, playAria: out.r1.playAria, muted: out.r1.muted }));
  log('  ⇒ 解除静音会连带开播？', out.unmuteStartsPlaying);
}

// ================= ② 拖音量滑杆 =================
log('\n=== ② 拖动音量滑杆 ===');
{
  const before = await st();
  const th = before.volThumb;
  log('  拖动前：', JSON.stringify({ thumb: th, vol: before.vol, muted: before.muted }));
  if (!th) log('  🔴 仍找不到音量 thumb');
  else {
    // 音量轨道 x 范围：从 slider-track 读
    const tr = await p.evaluate(() => { const bar = document.querySelector('[data-testid="video-fullscreen-player-bar"]');
      const tr = bar.querySelector('[data-testid="slider-track"]'); const r = tr.getBoundingClientRect();
      return { x: Math.round(r.x), w: Math.round(r.width), y: Math.round(r.y + r.height / 2) }; });
    const targetX = Math.round(tr.x + tr.w * 0.3);
    const land = await p.evaluate(([x, y]) => { const el = document.elementFromPoint(x, y);
      return { hitTag: el ? el.tagName : null, hitRole: el ? el.getAttribute('role') : null,
        hitVmax: el ? el.getAttribute('aria-valuemax') : null,
        cls: (el && el.className || '').toString().slice(0, 46) }; }, [th.cx, th.cy]);
    log('  落点校验：', JSON.stringify(land));
    out.volLand = { ...land, wantVmax: '1' };
    await p.mouse.move(th.cx, th.cy); await p.waitForTimeout(400);
    await p.mouse.down(); await p.waitForTimeout(300);
    await p.mouse.move(Math.round((th.cx + targetX) / 2), tr.y, { steps: 10 }); await p.waitForTimeout(300);
    await p.mouse.move(targetX, tr.y, { steps: 10 }); await p.waitForTimeout(500);
    out.volMid = await st();
    log('  拖动中：', JSON.stringify({ now: out.volMid.volThumb && out.volMid.volThumb.now, vol: out.volMid.vol }));
    await p.mouse.up(); await p.waitForTimeout(800);
    out.volAfter = await st();
    out.drag = { before: { now: before.volThumb.now, vol: before.vol },
      mid: { now: out.volMid.volThumb && out.volMid.volThumb.now, vol: out.volMid.vol },
      after: { now: out.volAfter.volThumb && out.volAfter.volThumb.now, vol: out.volAfter.vol },
      targetX, trackX: tr.x, trackW: tr.w, wantNow: '0.3' };
    out.drag.thumbMoved = out.drag.after.now !== out.drag.before.now;
    out.drag.videoFollows = out.drag.after.vol !== out.drag.before.vol;
    log('  拖完：', JSON.stringify(out.drag.after), '｜目标 0.3');
    log('  ⇒ thumb 动了？', out.drag.thumbMoved, '｜ video.volume 跟着变？', out.drag.videoFollows);
  }
}

// ================= ③ 全屏容器里所有按钮：找退出口 =================
log('\n=== ③ 全屏容器里的按钮 ===');
out.fsButtons = await p.evaluate(() => {
  const fs = document.fullscreenElement;
  if (!fs) return { inFs: false };
  const r0 = fs.getBoundingClientRect();
  return { fsRect: `${Math.round(r0.x)},${Math.round(r0.y)} ${Math.round(r0.width)}×${Math.round(r0.height)}`,
    fsTid: fs.getAttribute('data-testid'), fsCls: (fs.className || '').toString().slice(0, 60),
    buttons: Array.from(fs.querySelectorAll('button,[role=button]')).map((e) => { const r = e.getBoundingClientRect();
      return { tid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'),
        rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}` }; }) };
});
log(JSON.stringify(out.fsButtons, null, 1));

// 截图：全屏播放器（音量拖过之后的状态）
{
  const buf = await p.screenshot({ type: 'png' });
  const { writeFileSync } = await import('node:fs');
  const f = new URL('../docs/user-manual/jimeng-canvas/screenshots/101-video-fullscreen-player.png', import.meta.url);
  writeFileSync(f, buf);
  log('\n📸 全屏截图已覆盖：', f.pathname, buf.length, 'bytes');
  out.shotFsBytes = buf.length;
}

writeFileSync(new URL('./_tmp-b101c9.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();

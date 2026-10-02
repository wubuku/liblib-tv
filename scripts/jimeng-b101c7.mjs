// 批次 101 · c7 轮：全屏播放器里的**音量滑杆拖动**（手册三项「未验证」的最后一项）+ 截图取证。
//
// c6 轮已把全屏播放器的结构挖全（全部 testid 都是新面孔，手册里一个都没有）：
//   video-fullscreen-player-bar        1280×88 铺满底部
//   video-fullscreen-playback-toggle   20×32，aria `Play/Pause …`
//   video-fullscreen-player-clock      68×18
//   slider-track（音量）               **52×2**（两像素高！）
//     └ thumb [role=slider] 8×8，aria-valuemin=0 / max=1 / now=0
//   video-fullscreen-mute-toggle       32×32，aria `Unmute video`
//   video-fullscreen-browser-toggle    32×32，aria `Enter browser full screen`
//   另有一条 seek slider，thumb 的 aria-valuemax=**6**（= 素材时长）⇒ 两条 slider 可用 valuemax 区分
//
// ⚠️ c6 轮**进全屏时视频刚好播完**（ct 6 / paused），
//    所以「音量 = 0」这件事是「静音态下的显示」还是「真实音量」必须分开读 `video.volume` 判。
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

const readFs = () => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const v = n ? n.querySelector('video') : document.querySelector('video');
  const bar = document.querySelector('[data-testid="video-fullscreen-player-bar"]');
  const volTrack = bar ? Array.from(bar.querySelectorAll('[data-testid="slider-track"]')).pop() : null;
  const volThumb = volTrack ? volTrack.querySelector('[role=slider]') : null;
  const r = volThumb ? volThumb.getBoundingClientRect() : null;
  const tr = volTrack ? volTrack.getBoundingClientRect() : null;
  return {
    inFs: !!document.fullscreenElement,
    bar: bar ? (() => { const q = bar.getBoundingClientRect();
      return `${Math.round(q.x)},${Math.round(q.y)} ${Math.round(q.width)}×${Math.round(q.height)}`; })() : null,
    vol: v ? v.volume : null, muted: v ? v.muted : null, ct: v ? v.currentTime : null, paused: v ? v.paused : null,
    muteAria: (document.querySelector('[data-testid="video-fullscreen-mute-toggle"]') || {}).getAttribute?.('aria-label') || null,
    playAria: (document.querySelector('[data-testid="video-fullscreen-playback-toggle"]') || {}).getAttribute?.('aria-label') || null,
    clock: (() => { const c = document.querySelector('[data-testid="video-fullscreen-player-clock"]');
      return c ? c.innerText.replace(/\s+/g, ' ').trim() : null; })(),
    volTrack: tr ? { x: Math.round(tr.x), y: Math.round(tr.y), w: Math.round(tr.width), h: Math.round(tr.height) } : null,
    volThumb: r ? { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2),
      w: Math.round(r.width), h: Math.round(r.height),
      now: (volThumb.getAttribute('aria-valuenow')), min: volThumb.getAttribute('aria-valuemin'), max: volThumb.getAttribute('aria-valuemax'),
      style: (volThumb.getAttribute('style') || '').slice(0, 100) } : null,
  };
});

out.fs0 = await readFs();
log('全屏起手：', JSON.stringify(out.fs0, null, 1));
if (!out.fs0.inFs) { log('🔴 已不在全屏态 ⇒ 中止（不猜）'); writeFileSync(new URL('./_tmp-b101c7.json', import.meta.url), JSON.stringify(out, null, 1)); await b.close(); process.exit(1); }

// ---------- 1) 解除静音 ----------
log('\n=== 1 全屏态解除静音 ===');
{
  const t = await p.evaluate(() => { const e = document.querySelector('[data-testid="video-fullscreen-mute-toggle"]');
    if (!e) return null; const r = e.getBoundingClientRect();
    const x = Math.round(r.x + r.width / 2), y = Math.round(r.y + r.height / 2);
    const el = document.elementFromPoint(x, y);
    return { point: [x, y], inside: !!(el && (el === e || e.contains(el))) }; });
  log('  静音钮落点：', JSON.stringify(t));
  if (t && t.inside) { await p.mouse.move(t.point[0], t.point[1]); await p.waitForTimeout(350);
    await p.mouse.click(t.point[0], t.point[1]); await p.waitForTimeout(800); }
  out.fs1 = await readFs();
  log('  解除后：', JSON.stringify({ muteAria: out.fs1.muteAria, muted: out.fs1.muted, vol: out.fs1.vol, now: out.fs1.volThumb && out.fs1.volThumb.now }));
  out.unmute = { before: { aria: out.fs0.muteAria, muted: out.fs0.muted }, after: { aria: out.fs1.muteAria, muted: out.fs1.muted } };
}

// ---------- 2) 拖音量滑杆 ----------
log('\n=== 2 拖动音量滑杆 ===');
{
  const before = await readFs();
  const th = before.volThumb;
  if (!th) { log('  🔴 找不到音量 thumb'); }
  else {
    // 落点校验：thumb 上是什么
    const land = await p.evaluate(([x, y]) => { const el = document.elementFromPoint(x, y);
      return { hitTag: el ? el.tagName : null, hitRole: el ? el.getAttribute('role') : null,
        hitCls: (el && el.className || '').toString().slice(0, 50) }; }, [th.cx, th.cy]);
    log('  thumb 落点：', JSON.stringify(land));
    // 目标：把 thumb 拖到轨道 60% 处
    const tr = before.volTrack;
    const targetX = Math.round(tr.x + tr.w * 0.6);
    log(`  拖动：(${th.cx},${th.cy}) → (${targetX},${th.cy})｜轨道 ${tr.w}×${tr.h}，当前 valuenow=${th.now}`);
    await p.mouse.move(th.cx, th.cy); await p.waitForTimeout(400);
    await p.mouse.down(); await p.waitForTimeout(250);
    await p.mouse.move(Math.round((th.cx + targetX) / 2), th.cy, { steps: 8 }); await p.waitForTimeout(250);
    await p.mouse.move(targetX, th.cy, { steps: 8 }); await p.waitForTimeout(450);
    out.midDrag = await readFs();
    log('  拖动中：', JSON.stringify({ now: out.midDrag.volThumb && out.midDrag.volThumb.now, vol: out.midDrag.vol, muted: out.midDrag.muted }));
    await p.mouse.up(); await p.waitForTimeout(800);
    const after = await readFs();
    out.drag = { before: { now: th.now, vol: before.vol, muted: before.muted },
      mid: { now: out.midDrag.volThumb && out.midDrag.volThumb.now, vol: out.midDrag.vol },
      after: { now: after.volThumb && after.volThumb.now, vol: after.vol, muted: after.muted },
      targetFrac: 0.6 };
    out.drag.moved = out.drag.after.now !== out.drag.before.now;
    out.drag.reachesVideo = out.drag.after.vol !== out.drag.before.vol;
    log('  拖完：', JSON.stringify(out.drag.after));
    log('  ⇒ thumb 动了？', out.drag.moved, '｜ video.volume 跟着变？', out.drag.reachesVideo);
  }
}

// ---------- 3) 截图：全屏播放器 ----------
{
  const buf = await p.screenshot({ type: 'png' });
  const file = new URL('101-video-fullscreen-player.png', SHOT);
  const { writeFileSync } = await import('node:fs');
  writeFileSync(file, buf);
  out.shotFs = { file: file.pathname, bytes: buf.length, sha256: createHash('sha256').update(buf).digest('hex') };
  log('\n📸 全屏截图：', JSON.stringify(out.shotFs));
}

// ---------- 4) 退出全屏 ----------
log('\n=== 3 退出全屏 ===');
await p.keyboard.press('Escape');
await p.waitForTimeout(1400);
out.afterEsc = await readFs();
log('  Esc 后：', JSON.stringify({ inFs: out.afterEsc.inFs, bar: out.afterEsc.bar, ct: out.afterEsc.ct, paused: out.afterEsc.paused, muted: out.afterEsc.muted, vol: out.afterEsc.vol }));
out.escExits = !out.afterEsc.inFs && out.afterEsc.bar === null;

writeFileSync(new URL('./_tmp-b101c7.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();

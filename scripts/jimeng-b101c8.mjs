// 批次 101 · c8 轮：修 c7 的两个失败，并查清一件**没料到的事**。
//
// c7 的两处翻车（都是判据/操作问题，不是页面问题）：
//   ① `volTrack.querySelector('[role=slider]')` 取到 `null`
//      ⇒ **音量 thumb 不是 track 的后代**（c6 的扁平清单里它是独立一条），
//        得在 `video-fullscreen-player-bar` 的**全部后代**里按 `aria-valuemax=1` 认人
//        （seek 那条的 valuemax 是 6 = 素材时长，两条 slider 靠 valuemax 区分）。
//   ② `p.keyboard.press('Escape')` **没有退出全屏**（`document.fullscreenElement` 仍在），
//      反而让视频**从 0 开始播了**（ct 6 → 2.707 / paused false）。
//      这两件事可能是**两件**，也可能是一件事（Esc 被播放器吃了）。
//      本轮分开验：先单按一次 Esc 读全屏态，再单按一次读播放态，**受控复测**。
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

const st = () => p.evaluate(() => {
  const v = document.querySelector('video');
  const bar = document.querySelector('[data-testid="video-fullscreen-player-bar"]');
  return { inFs: !!document.fullscreenElement, ct: v ? v.currentTime : null, paused: v ? v.paused : null,
    vol: v ? v.volume : null, muted: v ? v.muted : null,
    playAria: (document.querySelector('[data-testid="video-fullscreen-playback-toggle"]') || {}).getAttribute?.('aria-label') || null,
    clock: (() => { const c = document.querySelector('[data-testid="video-fullscreen-player-clock"]');
      return c ? c.innerText.replace(/\s+/g, ' ').trim() : null; })() };
});

// ---------- ① 全屏条结构全量：把 thumb 的**父子关系**一次问清 ----------
out.barTree = await p.evaluate(() => {
  const bar = document.querySelector('[data-testid="video-fullscreen-player-bar"]');
  if (!bar) return { noBar: true };
  const rows = [];
  for (const e of bar.querySelectorAll('*')) {
    const r = e.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) continue;
    const parent = e.parentElement;
    rows.push({
      tag: e.tagName, tid: e.getAttribute('data-testid'), role: e.getAttribute('role'),
      aria: e.getAttribute('aria-label'), vmin: e.getAttribute('aria-valuemin'), vmax: e.getAttribute('aria-valuemax'),
      vnow: e.getAttribute('aria-valuenow'),
      parentTid: parent ? parent.getAttribute('data-testid') : null,
      parentTag: parent ? parent.tagName : null,
      parentCls: parent ? (parent.className || '').toString().slice(0, 40) : null,
      cls: (e.className || '').toString().slice(0, 46),
      rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
    });
  }
  return { count: rows.length, rows };
});
log('=== 全屏条后代（' + (out.barTree.count || 0) + '）===');
for (const r of out.barTree.rows || []) log(`  ${r.tag} tid=${r.tid || '-'} role=${r.role || '-'} aria=${r.aria || '-'} vmin=${r.vmin || '-'} vmax=${r.vmax || '-'} vnow=${r.vnow || '-'} 父=${r.parentTid || r.parentTag}  ${r.rect}`);

// ---------- ② 受控复测 Esc ----------
log('\n=== Esc 受控复测（先按一次）===');
out.esc = [];
for (let k = 0; k < 3; k++) {
  const before = await st();
  await p.keyboard.press('Escape');
  await p.waitForTimeout(1200);
  const after = await st();
  out.esc.push({ k, before, after });
  log(`  第 ${k + 1} 次：inFs ${before.inFs}→${after.inFs}｜ct ${before.ct}→${after.ct}｜paused ${before.paused}→${after.paused}｜playAria ${before.playAria}→${after.playAria}`);
  if (!after.inFs) { log('  ⇒ Esc 退全屏了'); break; }
}

writeFileSync(new URL('./_tmp-b101c8.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();

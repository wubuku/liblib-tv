// 批次 101 · c2 轮：**点播放，看控件从哪来**。
//
// c1 轮实测（静止态、已选中）：
//   · 卡片里 **没有** 时间读数、**没有** 进度条、**没有** `<video>`、**没有** `<canvas>`
//   · 只有一个 `video-simple-player` **BUTTON**（canvas 44×44，卡片正中），aria=`Play …`
//   · 封面是 `video-passive-preview` 这个 `<img>`（640×360）
// ⇒ 手册第 20-27 行那套「底部一行控件」**在静止态并不存在**。
//   本轮要回答：**它们是不是播放时才挂载的**。
//
// 🔑 观测手段**双路并行**（批次 97 试过 MutationObserver 记 0 条，与批次 32 矛盾）：
//   ① 轮询采样（每 350ms 读一次全量结构）—— 慢但不会漏
//   ② MutationObserver（记 childList 增删）—— 快但可能收不到
//   两条都上，**哪条先给出答案就采信哪条，另一条作为对照**。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString(), selfId: 'node_fxhrsbbfrz' };
const SELF = out.selfId;

// ---- 采样函数：一次读全所有「播放相关」读数 ----
const sample = () => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { gone: true };
  const A = (sel) => Array.from(n.querySelectorAll(sel));
  const sc = (() => { const e = document.querySelector('.react-flow__viewport');
    const m = e && /scale\(([\d.]+)\)/.exec(e.style.transform || ''); return m ? Number(m[1]) : null; })();
  const nodeRect = n.getBoundingClientRect();
  const t = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
  const ox = t ? Number(t[1]) : 0, oy = t ? Number(t[2]) : 0;
  const cvOf = (e) => { const r = e.getBoundingClientRect();
    return sc ? `${Math.round(r.width / sc * 100) / 100}×${Math.round(r.height / sc * 100) / 100}@${Math.round((r.x - nodeRect.x) / sc + ox)},${Math.round((r.y - nodeRect.y) / sc + oy)}` : null; };

  const player = n.querySelector('[data-testid="video-simple-player"]');
  const videos = Array.from(n.querySelectorAll('video')).map((v) => ({
    paused: v.paused, ct: v.currentTime, dur: v.duration, muted: v.muted, vol: v.volume,
    loop: v.loop, readyState: v.readyState, w: v.videoWidth, h: v.videoHeight,
    rect: (() => { const r = v.getBoundingClientRect(); return `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`; })(),
  }));
  const times = Array.from(n.querySelectorAll('*'))
    .filter((e) => e.children.length === 0 && /\d+:\d\d/.test(e.textContent || ''))
    .map((e) => ({ txt: e.textContent.trim(), cv: cvOf(e) }));
  const btns = A('button,[role=button]').map((e) => ({ aria: e.getAttribute('aria-label'), tid: e.getAttribute('data-testid'), cv: cvOf(e) }))
    .filter((x) => x.aria);
  const bars = A('[role=slider],[role=progressbar],input[type=range]').map((e) => ({
    role: e.getAttribute('role'), tag: e.tagName, aria: e.getAttribute('aria-label'), cv: cvOf(e),
  }));
  return {
    testids: Array.from(new Set(Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))),
    playerAria: player ? player.getAttribute('aria-label') : null,
    playerTag: player ? player.tagName : null,
    playerHTML: player ? player.innerHTML.slice(0, 200) : null,
    videos, times, btns, bars,
    innerText: n.innerText.replace(/\s+/g, ' ').trim(),
  };
}, SELF);

// ---- 落点校验：点击前必须看清落点上是什么、属于谁 ----
out.landing = await p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const btn = n.querySelector('[data-testid="video-simple-player"]');
  const r = btn.getBoundingClientRect();
  const x = Math.round(r.x + r.width / 2), y = Math.round(r.y + r.height / 2);
  const el = document.elementFromPoint(x, y);
  return {
    point: [x, y], rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
    hitTestid: el ? el.getAttribute('data-testid') : null,
    hitAria: el ? el.getAttribute('aria-label') : null,
    hitTag: el ? el.tagName : null,
    insideSelfNode: !!(el && el.closest(`.react-flow__node[data-id="${i}"]`)),
    // ⚠️ 按钮里有 SVG 图标 ⇒ elementFromPoint 返回的是内层 <path>，**不是** BUTTON。
    //    所以判据问的是「落点是否在这个按钮内」（含其后代），而不是「落点是不是 BUTTON」。
    insideTargetBtn: !!(el && (el === btn || btn.contains(el))),
    selCount: (document.body.innerText.match(/(\d+) selected/) || [])[1],
  };
}, SELF);
log('落点校验：', JSON.stringify(out.landing));
if (!out.landing.insideSelfNode || !out.landing.insideTargetBtn) { log('🔴 落点不对 ⇒ 中止'); await b.close(); process.exit(1); }

// ---- 挂 MutationObserver（对照组 ②） ----
await p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  window.__b101 = { added: [], removed: [], attrs: [] };
  const o = new MutationObserver((muts) => {
    for (const mu of muts) {
      for (const e of mu.addedNodes) if (e.nodeType === 1) window.__b101.added.push(`+${e.tagName}${e.getAttribute?.('data-testid') ? '#' + e.getAttribute('data-testid') : ''}${e.getAttribute?.('aria-label') ? '[' + e.getAttribute('aria-label') + ']' : ''}`);
      for (const e of mu.removedNodes) if (e.nodeType === 1) window.__b101.removed.push(`-${e.tagName}${e.getAttribute?.('data-testid') ? '#' + e.getAttribute('data-testid') : ''}`);
      for (const e of mu.targets || []) {}
      if (mu.type === 'attributes' && mu.target) window.__b101.attrs.push(`~${mu.target.getAttribute?.('data-testid') || mu.target.tagName}:${mu.attributeName}=${mu.target.getAttribute(mu.attributeName)}`);
    }
  });
  o.observe(n, { childList: true, subtree: true, attributes: true, attributeFilter: ['aria-label', 'class', 'style'] });
  window.__b101obs = o;
}, SELF);

// ---- 采样（对照组 ①）：先取静止基线，再点播放，再连采 10 次 ----
out.baseline = await sample();
log('静止基线：playerAria=', out.baseline.playerAria, '| videos=', out.baseline.videos.length,
  '| times=', out.baseline.times.length, '| bars=', out.baseline.bars.length, '| btns=', out.baseline.btns.length);
log('  静止态按钮：', JSON.stringify(out.baseline.btns));

const [px, py] = out.landing.point;
await p.mouse.move(px, py); await p.waitForTimeout(600);
await p.mouse.click(px, py);

out.series = [];
for (let k = 0; k < 10; k++) {
  await p.waitForTimeout(350);
  const s = await sample();
  out.series.push({ t: (k + 1) * 350, playerAria: s.playerAria, vids: s.videos, times: s.times, bars: s.bars, nBtn: s.btns.length });
  log(`  t=${(k + 1) * 350}ms  aria=${s.playerAria}  video=${JSON.stringify(s.videos)}  time=${JSON.stringify(s.times.map((x) => x.txt))}  bars=${s.bars.length}`);
}

// ---- 播放态下再看一次完整结构 ----
out.during = await sample();
log('\n播放态按钮：', JSON.stringify(out.during.btns, null, 1));
log('播放态 testids：', JSON.stringify(out.during.testids));
log('播放态 innerText：', out.during.innerText);
log('播放态进度条：', JSON.stringify(out.during.bars, null, 1));

out.mo = await p.evaluate(() => {
  try { window.__b101obs.disconnect(); } catch {}
  return window.__b101;
});
log('\nMutationObserver 记录：added=', out.mo.added.length, 'removed=', out.mo.removed.length, 'attrs=', out.mo.attrs.length);
log('  added:', JSON.stringify(out.mo.added.slice(0, 40)));
log('  attrs:', JSON.stringify(out.mo.attrs.slice(0, 20)));

writeFileSync(new URL('./_tmp-b101c2.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();

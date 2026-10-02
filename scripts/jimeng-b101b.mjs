// 批次 101 · b 轮：**只读现状探针**。
// 先确认上一轮（a）建的自建视频节点 `node_fxhrsbbfrz` 是否还在画布上、
// 状态如何（selected? 资源就绪? 封面图?），再决定 b 轮实测怎么做。
// 本轮**不点击任何东西**，纯读。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString(), selfId: 'node_fxhrsbbfrz' };

out.state = await p.evaluate(() => ({
  nodes: (document.body.innerText.match(/(\d+) nodes?/) || [])[1],
  sel: (document.body.innerText.match(/(\d+) selected/) || [])[1],
  credits: (document.querySelector('[data-testid="canvas-commerce-entry"]') || {}).getAttribute?.('aria-label'),
  zoom: (document.querySelector('[data-testid="canvas-zoom-percent"]') || {}).getAttribute?.('aria-label'),
  scale: (() => { const e = document.querySelector('.react-flow__viewport');
    const m = e && /scale\(([\d.]+)\)/.exec(e.style.transform || ''); return m ? Number(m[1]) : null; })(),
  tool: (document.querySelector('[data-testid="canvas-pointer-tool-toggle"]') || {}).getAttribute?.('aria-label'),
}));
log('画布现状：', JSON.stringify(out.state));

out.self = await p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { present: false };
  const r = n.getBoundingClientRect();
  const sc = (() => { const e = document.querySelector('.react-flow__viewport');
    const m = e && /scale\(([\d.]+)\)/.exec(e.style.transform || ''); return m ? Number(m[1]) : null; })();
  return {
    present: true,
    cls: n.className,
    aria: n.getAttribute('aria-label'),
    translate: n.style.transform,
    screen: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
    inViewport: r.x + r.width > 0 && r.y + r.height > 0 && r.x < 1280 && r.y < 720,
    canvasSize: sc ? `${Math.round(r.width / sc)}×${Math.round(r.height / sc)}` : null,
    innerText: n.innerText.replace(/\s+/g, ' ').trim(),
    testids: Array.from(new Set(Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))),
    arias: Array.from(new Set(Array.from(n.querySelectorAll('[aria-label]')).map((e) => e.getAttribute('aria-label')))),
    media: Array.from(n.querySelectorAll('video,audio')).map((e) => ({ tag: e.tagName, paused: e.paused })),
    imgs: Array.from(n.querySelectorAll('img')).map((e) => ({ nw: e.naturalWidth, nh: e.naturalHeight, complete: e.complete })),
  };
}, out.selfId);
log('SELF 现状：', JSON.stringify(out.self, null, 1));

// 若节点还在，顺手看看全画布有没有别的**带媒体**的视频节点（有封面图 ⇒ 有素材），
// 这是给「有播放控件」的前置判据，避免只盯着自己那一个。
out.videoNodes = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node-video')).map((n) => {
  const img = n.querySelector('img');
  return {
    id: n.getAttribute('data-id'),
    aria: n.getAttribute('aria-label'),
    hasImg: !!img,
    nw: img ? img.naturalWidth : 0,
    nVideos: n.querySelectorAll('video').length,
    hasPlayAria: !!Array.from(n.querySelectorAll('[aria-label]')).find((e) => /^(Play|Pause) /.test(e.getAttribute('aria-label') || '')),
  };
}));
log(`画布上的视频节点共 ${out.videoNodes.length} 个：`);
for (const v of out.videoNodes) log('  ', JSON.stringify(v));

writeFileSync(new URL('./_tmp-b101b.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();

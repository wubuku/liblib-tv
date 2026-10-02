// 批次 101 · c1 轮：**播放前结构深挖**（只读，不点任何控件）。
//
// 手册第 20-33 行描述了「播放/暂停钮、时间读数、静音钮、全屏钮、底部细进度条」，
// 但这些都是 **2026-09-23 在「视频 1」节点上** 观测到的。
// 现在要在一个**自建**节点上把这些结构定位到 testid / 几何 / canvas 坐标，
// 为后面的动作轮（c2）准备**可机械复现的判据**。
//
// 🔑 已知的前置事实（a/b 轮实测）：
//   · 节点 DOM 里**没有** `<video>` 元素，只有 1 张 `<img>` 封面（640×360）
//   · 内部 testid 里有 `video-passive-preview`（封面）与 `video-simple-player`（疑似播放器）
//   · 节点仍处选中态，但播放钮 aria 是 **`Play …`**（不是 Pause）
//     ⇒ 「选中即播」在本节点上**至少此刻不成立**，要专门验。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString(), selfId: 'node_fxhrsbbfrz' };

// 位置一律用 **canvas 坐标**（节点 inline transform 推出的画布坐标），不用屏幕坐标。
out.deep = await p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { present: false };
  const nodeRect = n.getBoundingClientRect();
  // 节点 inline transform = translate(dx,dy) ⇒ dx,dy 就是 canvas 坐标
  const m = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
  const cx = m ? Number(m[1]) : null;
  const cy = m ? Number(m[2]) : null;
  const sc = (() => { const e = document.querySelector('.react-flow__viewport');
    const mm = e && /scale\(([\d.]+)\)/.exec(e.style.transform || ''); return mm ? Number(mm[1]) : null; })();

  // 屏上矩形 → canvas 矩形（尺寸契约：屏上读数 = canvas × scale，除数当场读）
  const cv = (r) => sc ? {
    w: Math.round(r.width / sc * 100) / 100,
    h: Math.round(r.height / sc * 100) / 100,
    x: Math.round((r.x - nodeRect.x) / sc + cx),
    y: Math.round((r.y - nodeRect.y) / sc + cy),
  } : null;

  const walk = (root, depth) => {
    const rows = [];
    for (const e of root.querySelectorAll('*')) {
      const r = e.getBoundingClientRect();
      if (r.width === 0 || r.height === 0) continue;
      const tid = e.getAttribute('data-testid');
      const aria = e.getAttribute('aria-label');
      const role = e.getAttribute('role');
      const txt = (e.innerText || '').replace(/\s+/g, ' ').trim();
      // 只留「有语义线索」的元素：testid / aria / role / 自身有文字 / 进度条类
      if (!tid && !aria && !role && !txt && !/^(DIV|SPAN)$/.test(e.tagName)) continue;
      if (['SECTION', 'svg', 'path', 'g'].includes(e.tagName)) continue;
      rows.push({
        tag: e.tagName, depth,
        tid: tid || undefined, aria: aria || undefined, role: role || undefined,
        txt: txt ? txt.slice(0, 60) : undefined,
        cls: (e.className && typeof e.className === 'string' ? e.className : '').slice(0, 60) || undefined,
        rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
        cv: cv(r),
      });
    }
    return rows;
  };
  return {
    present: true, scale: sc, canvasOrigin: [cx, cy],
    rows: walk(n, 0).filter((x) => x.tid || x.aria || x.role || x.txt),
  };
}, out.selfId);

log('scale =', out.deep.scale, '｜节点 canvas 原点 =', JSON.stringify(out.deep.canvasOrigin));
log('语义元素清单（' + out.deep.rows.length + ' 个）：');
for (const r of out.deep.rows) {
  log(`  [${r.tag}] tid=${r.tid || '-'} aria=${r.aria || '-'} role=${r.role || '-'} cv=${r.cv ? `${r.cv.w}×${r.cv.h}@${r.cv.x},${r.cv.y}` : '-'}${r.txt ? ` txt="${r.txt}"` : ''}`);
}

// ---- 专门找「时间读数」和「进度条」：这两样手册写了但从没给出定位方式 ----
out.findings = await p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const timeish = Array.from(n.querySelectorAll('*'))
    .filter((e) => e.children.length === 0 && /\d+:\d\d/.test(e.textContent || ''))
    .map((e) => { const r = e.getBoundingClientRect();
      return { tag: e.tagName, txt: e.textContent.trim(), rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}` }; });
  const bars = Array.from(n.querySelectorAll('[role=slider],[role=progressbar],input[type=range],progress,[class*=progress],[class*=Progress],[class*=seek],[class*=Seek],[class*=scrub]'))
    .map((e) => { const r = e.getBoundingClientRect();
      return { tag: e.tagName, role: e.getAttribute('role'), cls: (e.className||'').toString().slice(0,70),
        rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}` }; });
  const canvasEls = Array.from(n.querySelectorAll('canvas')).map((e) => { const r = e.getBoundingClientRect();
    return { cls: (e.className||'').toString().slice(0,50), rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}` }; });
  const player = n.querySelector('[data-testid="video-simple-player"]');
  const preview = n.querySelector('[data-testid="video-passive-preview"]');
  return {
    timeish, bars, canvasEls,
    player: player ? { rect: (() => { const r = player.getBoundingClientRect();
        return `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`; })(),
      childTags: Array.from(player.querySelectorAll('*')).map((e) => e.tagName).filter((t, k, a) => a.indexOf(t) === k),
      hasVideo: !!player.querySelector('video'), hasImg: !!player.querySelector('img') } : null,
    preview: preview ? { tag: preview.tagName, children: Array.from(preview.children).map((e) => e.tagName) } : null,
  };
}, out.selfId);
log('\n=== 找时间读数 / 进度条 / canvas ===');
log(JSON.stringify(out.findings, null, 1));

writeFileSync(new URL('./_tmp-b101c1.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();

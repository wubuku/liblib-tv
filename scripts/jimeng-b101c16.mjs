// 批次 101 · c16 轮：查那条「鬼影」。
//
// c15 拍到的图，标题行上方压着一条**半透明**的「▶ 00:00 / 00:00」，
// 但我们自己的卡片读数是 `00:06 / 00:06` —— **不是同一个**。
// 而 c15 的「可见判据」（clip 内 9×9 网格取 `elementsFromPoint` 的**首个**元素）报 `0` 污染。
//
// 🔑 **这说明「可见判据」也不够**：它只问「谁在最上层」，不问「下层有没有东西透上来」。
//     本节点的 `video-hover-surface` / `video-flow-node-stroke` 一类是**半透明**的，
//     下层的邻居就会**透过**它显出来 —— 命中测试完全查不到，但**像素里有**。
//     ⇒ 第三条判据必须是：**clip 区域内，下层是否还有别的节点**。
//     这不是放宽守卫，是把守卫从「两层」补到「三层」。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString(), selfId: 'node_fxhrsbbfrz' };
const SELF = out.selfId;

// 鬼影大约在 clip 内的 (582,285) / (600,285) 一带
out.ghost = await p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const clip = { x: 457, y: 250, width: 366, height: 248 };
  const pts = [[500, 262], [560, 280], [582, 285], [600, 288], [620, 285], [660, 284], [700, 283]];
  return {
    at: pts.map(([x, y]) => {
      const stack = document.elementsFromPoint(x, y).slice(0, 6).map((e) => ({
        tag: e.tagName, tid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'),
        cls: (e.className || '').toString().slice(0, 44),
        inSelf: !!(e.closest(`.react-flow__node[data-id="${i}"]`)),
        node: (e.closest('.react-flow__node') || {}).getAttribute ? (e.closest('.react-flow__node') || {}).getAttribute('data-id') : null,
        op: getComputedStyle(e).opacity,
        bg: getComputedStyle(e).backgroundColor,
      }));
      return { pt: [x, y], stack };
    }),
    // 本节点表面本身的透明度
    selfStyles: Array.from(n.querySelectorAll('[data-testid]')).map((e) => {
      const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
      return { tid: e.getAttribute('data-testid'), op: cs.opacity, bg: cs.backgroundColor,
        rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}` }; }),
    // clip 区域里，**下层**有没有别的节点
    underClip: Array.from(document.querySelectorAll('.react-flow__node')).filter((e) => {
        if (e === n || e.contains(n) || n.contains(e)) return false;
        const r = e.getBoundingClientRect();
        return r.x < clip.x + clip.width && r.x + r.width > clip.x && r.y < clip.y + clip.height && r.y + r.height > clip.y; })
      .map((e) => { const r = e.getBoundingClientRect();
        return { id: e.getAttribute('data-id'), aria: e.getAttribute('aria-label'), z: getComputedStyle(e).zIndex,
          op: getComputedStyle(e).opacity,
          rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}` }; }),
  };
}, SELF);
log('=== 各采样点的元素栈 ===');
for (const a of out.ghost.at) { log(` pt=${a.pt}`); for (const s of a.stack) log(`    ${s.tag} tid=${s.tid || '-'} aria=${s.aria || '-'} inSelf=${s.inSelf} node=${s.node} op=${s.op} bg=${s.bg}`); }
log('\n=== 本节点各层样式 ===');
for (const s of out.ghost.selfStyles) log(`  ${s.tid.padEnd(34)} op=${s.op} bg=${s.bg}  ${s.rect}`);
log('\n=== clip 下层的他人节点 ===');
log(JSON.stringify(out.ghost.underClip, null, 1));

writeFileSync(new URL('./_tmp-b101c16.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();

// 批次 121 · a 轮（只读）：连线到底是 SVG path 画��，还是画在一张 `<canvas>` 上？
//
// 🔑 靶子来自批次 120 的**全文档 testid 普查**：那次普查读到两个此前从未被手册记录的
//   chrome testid —— `canvas-connection-flow-layer-host` 与 `canvas-connection-flow-layer`，
//   而后者的标签是 **`<CANVAS>`**（不是 DIV），矩形 `1280×720`。
//   `connect-nodes.md`「连线的 DOM 结构」小节写的是**两层 SVG path**
//   （`.react-flow__edge-path` 1px 视觉线 ＋ `.react-flow__edge-interaction` 20px 命中区）。
//   ⇒ 要回答：**屏幕上那条线，到底是谁画的？**
//
// 本轮**纯只读**：当前画布 `0 edges`，先把「这张 canvas 是什么」读清楚；
// 要判断「谁画出了可见的线」需要至少 1 条边，那是 b 轮的事（会自建节点，不碰他人节点）。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'a' };
const save = () => writeFileSync(new URL('./_tmp-b121a.json', import.meta.url), JSON.stringify(out, null, 1));

const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
out.start = { zoom: await zoom(), credits: await credits(), edges: await p.evaluate(() => document.querySelectorAll('.react-flow__edge').length) };
log('起点：', JSON.stringify(out.start));

// ============================================================
// ① canvas 连线层：标签、属性、层级、像素
// ============================================================
out.layer = await p.evaluate(() => {
  const desc = (e) => { if (!e) return null; const q = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return { tag: e.tagName, tid: e.getAttribute('data-testid'), id: e.id || null,
      cls: (e.getAttribute('class') || '').toString(), rect: [q.x, q.y, q.width, q.height].map(Math.round),
      z: cs.zIndex, pos: cs.position, pe: cs.pointerEvents, op: cs.opacity, vis: cs.visibility, disp: cs.display,
      mixBlend: cs.mixBlendMode, filter: cs.filter, transform: cs.transform,
      attrWidth: e.getAttribute('width'), attrHeight: e.getAttribute('height'),
      styleW: e.style.width, styleH: e.style.height }; };
  const host = document.querySelector('[data-testid="canvas-connection-flow-layer-host"]');
  const layer = document.querySelector('[data-testid="canvas-connection-flow-layer"]');
  const chain = []; let cur = layer;
  for (let k = 0; k < 5 && cur; k++) { chain.push(desc(cur)); cur = cur.parentElement; }
  // 这张 canvas 的位图现在画了什么？
  let pixels = null;
  if (layer && layer.tagName === 'CANVAS') {
    try {
      const ctx = layer.getContext('2d');
      const w = layer.width, h = layer.height;
      const d = ctx.getImageData(0, 0, w, h).data;
      let nonEmpty = 0, maxA = 0;
      for (let i = 3; i < d.length; i += 4) { if (d[i] !== 0) { nonEmpty++; if (d[i] > maxA) maxA = d[i]; } }
      pixels = { 位图宽: w, 位图高: h, 非透明像素数: nonEmpty, 最大alpha: maxA, 屏幕像素比: (layer.getBoundingClientRect().width / w).toFixed(3) };
    } catch (e) { pixels = { __err: String(e) }; }
  }
  // host 的兄弟节点（同层还有没有别的东西）
  const siblings = host ? Array.from(host.parentElement.children).map(desc) : null;
  return { host: desc(host), layer: desc(layer), layer祖先链: chain, 位图: pixels, host的兄弟: siblings };
});
log('\n=== ① 连线层 ===');
log('  host：', JSON.stringify(out.layer.host));
log('  layer：', JSON.stringify(out.layer.layer));
log('  位图：', JSON.stringify(out.layer.位图));
log('  layer 祖先链：');
out.layer.祖先链 = out.layer.layer祖先链;
out.layer.layer祖先链.forEach((d, i) => log(`    ${'  '.repeat(i)}${d ? JSON.stringify({ tag: d.tag, tid: d.tid, cls: d.cls.slice(0, 70), z: d.z, pos: d.pos, pe: d.pe }) : null}`));
log('  host 的兄弟（同层还有什么）：');
(out.layer.host的兄弟 || []).forEach((d) => log(`    ${JSON.stringify({ tag: d.tag, tid: d.tid, cls: (d.cls || '').slice(0, 60), z: d.z, pe: d.pe, disp: d.disp })}`));
save();

// ============================================================
// ② SVG 那条路：`.react-flow__edges` 容器在不在、里面有什么
// ============================================================
out.svg = await p.evaluate(() => {
  const r = (e) => { const q = e.getBoundingClientRect(); return [q.x, q.y, q.width, q.height].map(Math.round); };
  const cs = (e) => { const c = getComputedStyle(e); return { pe: c.pointerEvents, op: c.opacity, vis: c.visibility, disp: c.display, z: c.zIndex, stroke: c.stroke, strokeWidth: c.strokeWidth, fill: c.fill, strokeLinecap: c.strokeLinecap }; };
  const conts = Array.from(document.querySelectorAll('.react-flow__edges'));
  const svgs = Array.from(document.querySelectorAll('svg.react-flow__edges'));
  return {
    容器: conts.map((e) => ({ cls: (e.getAttribute('class') || ''), rect: r(e), 子元素数: e.children.length, 样式: cs(e), 父: e.parentElement ? e.parentElement.className.toString().slice(0, 60) : null })),
    svg容器: svgs.map((e) => ({ rect: r(e), viewBox: e.getAttribute('viewBox'), 子元素数: e.children.length, 样式: cs(e) })),
    edge数: document.querySelectorAll('.react-flow__edge').length,
    edgeupdater数: document.querySelectorAll('.react-flow__edgeupdater').length,
    文档里所有svg: Array.from(document.querySelectorAll('svg')).filter((e) => e.className && e.className.baseVal !== undefined && /react-flow/.test(e.className.baseVal || '')).length,
  };
});
log('\n=== ② SVG 路线 ===');
log('  .react-flow__edges 容器：', JSON.stringify(out.svg.容器, null, 1));
log('  svg.react-flow__edges：', JSON.stringify(out.svg.svg容器));
log('  edge 数 / edgeupdater 数：', out.svg.edge数, '/', out.svg.edgeupdater数);
save();

// ============================================================
// ③ 两个层的 z 序：谁压着谁（用 elementFromPoint 验，需要有边才有意义，这里只记层序）
// ============================================================
out.zorder = await p.evaluate(() => {
  const l = document.querySelector('[data-testid="canvas-connection-flow-layer"]');
  const cont = document.querySelector('.react-flow__edges');
  const pane = document.querySelector('.react-flow__pane');
  const nodes = document.querySelector('.react-flow__nodes');
  const g = (e) => { if (!e) return null; const cs = getComputedStyle(e); return { tag: e.tagName, cls: (e.getAttribute('class') || '').toString().slice(0, 60), z: cs.zIndex, pos: cs.position, pe: cs.pointerEvents, op: cs.opacity }; };
  return { 连线canvas: g(l), edges容器: g(cont), pane: g(pane), nodes容器: g(nodes) };
});
log('\n=== ③ 层序 ===');
for (const [k, v] of Object.entries(out.zorder)) log(`   ${k.padEnd(12)} ${JSON.stringify(v)}`);

out.end = { zoom: await zoom(), credits: await credits() };
save();
log('\n终点：', JSON.stringify(out.end));
log('\nDONE a');
process.exit(0);

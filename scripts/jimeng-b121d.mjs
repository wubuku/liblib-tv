// 批次 121 · d 轮：从 **handle 的 ::before 热区**拖出一条边，然后做因果实验。
//
// 🔑 c 轮查清了机制（本批第二个真发现）：
//   `flow-node-source-connection-menu-button` 与 `flow-node-target-connection-menu-button`
//   **两个 ⊕ 按钮的 `pointer-events` 都是 `none`**（本体与 `::before`/`::after` 全是 `none`）
//   ⇒ **它们自己永远不可能成为命中目标**。唯一能接事件的是 **handle 的 `::before`**：
//   `pointer-events:auto`、盒子 `40px × 80px`、`top:60px; left:30px`。
//   两条 handle 的 `::before` 都是 `auto`（left / right 各一）。
//   ⇒ **「⊕ 按钮」是视觉件，点击事件其实落在 handle 的伪元素上** —— 这是批次 91
//     「元素在 ≠ 交互在」的升级版：**按钮在 ≠ 按钮接事件**。
//   ⇒ 推论：b3 轮那个「按钮矩形内逐点都命中 handle」的读数**不是异常，是这套机制的必然**。
//
// ⇒ 所以本轮不点 ⊕，改走**手册记载的那条路**：从 handle 热区**拖**到目标节点。
//   落点判据仍是护栏④：**起点**必须命中 handle（读 elementFromPoint），
//   **终点**必须命中目标节点内部。
//
// 本轮只碰**自建**的两个空视频节点（`node_5k3gf1n51s` / `node_bm52y0m7hn`），
// **不碰任何他人的节点**。z 轮负责删边 + 删两个节点。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'd' };
const save = () => writeFileSync(new URL('./_tmp-b121d.json', import.meta.url), JSON.stringify(out, null, 1));
const shotDir = new URL('./_tmp-b121d-shots/', import.meta.url);

const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);

out.start = { zoom: await zoom(), status: await status(), credits: await credits() };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);

const A = 'node_5k3gf1n51s', B = 'node_bm52y0m7hn';

// ---- 起点：handle 热区里 elementFromPoint 命中 handle 的点 ----
const from = await p.evaluate((id) => {
  const n = document.querySelector(`.react-flow__node[data-id="${id}"]`); if (!n) return { __err: 'gone' };
  const h = n.querySelector('[data-testid="flow-node-source-handle"]'); if (!h) return { __err: 'no-handle' };
  const r = h.getBoundingClientRect();
  for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2)
    for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
      if (x < 2 || y < 2 || y > innerHeight - 2 || x > innerWidth - 2) continue;
      const e = document.elementFromPoint(x, y);
      if (e === h) return { x, y, handle矩形: [r.x, r.y, r.width, r.height].map(Math.round) };
    }
  return { __err: 'no-hot-point', handle矩形: [r.x, r.y, r.width, r.height].map(Math.round) };
}, A);
log('\n起点（handle 热区）：', JSON.stringify(from));
out.from = from;
if (from.__err) { log('⛔ 中止'); save(); await b.close(); process.exit(3); }

// ---- d2 前置：两个自建节点几乎完全重叠（都落在视口中心），先把 A 拖开 ----
{
  const mv = await p.evaluate((id) => {
    const n = document.querySelector(`.react-flow__node[data-id="${id}"]`); if (!n) return { __err: 'gone' };
    const r = n.getBoundingClientRect();
    let grab = null;
    for (let y = Math.ceil(r.y) + 8; y < r.y + r.height - 8 && !grab; y += 4)
      for (let x = Math.ceil(r.x) + 8; x < r.x + r.width - 8; x += 4) {
        if (x < 4 || y < 4 || y > innerHeight - 4 || x > innerWidth - 4) continue;
        const e = document.elementFromPoint(x, y); if (e && (e === n || n.contains(e))) { grab = { x, y }; break; } }
    if (!grab) return { __err: 'no-grab-point' };
    // 找一块落点：不在任何节点内、且尽量远离其它节点
    let drop = null;
    for (const cand of [[240, 560], [980, 200], [240, 180], [1000, 560], [620, 600]]) {
      const e = document.elementFromPoint(cand[0], cand[1]);
      if (e && !e.closest('.react-flow__node') && e.id !== 'root') { drop = cand; break; } }
    if (!drop) return { __err: 'no-drop-point', grab };
    return { grab, drop, 落点命中: (() => { const e = document.elementFromPoint(drop[0], drop[1]); return e ? e.tagName + ' cls=' + (e.className || '').toString().slice(0, 40) : null; })() };
  }, A);
  log('\n把 A 拖开：', JSON.stringify(mv));
  out.move = mv;
  if (!mv.__err) {
    await p.mouse.move(mv.grab.x, mv.grab.y); await p.waitForTimeout(300);
    await p.mouse.down(); await p.waitForTimeout(250);
    await p.mouse.move(mv.drop[0], mv.drop[1], { steps: 16 }); await p.waitForTimeout(300);
    await p.mouse.up(); await p.waitForTimeout(1600);
    out.moveAfter = await p.evaluate((ids) => ids.map((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); const q = n.getBoundingClientRect(); return { id: i, 矩形: [q.x, q.y, q.width, q.height].map(Math.round) }; }), [A, B]);
    log('  拖开后两个节点：', JSON.stringify(out.moveAfter));
  }
  save();
}

// ---- 终点：目标节点内部 ----
const to = await p.evaluate((id) => {
  const n = document.querySelector(`.react-flow__node[data-id="${id}"]`); if (!n) return { __err: 'gone' };
  const r = n.getBoundingClientRect();
  for (let y = Math.ceil(r.y) + 10; y < r.y + r.height - 10; y += 4)
    for (let x = Math.ceil(r.x) + 10; x < r.x + r.width - 10; x += 4) {
      if (x < 2 || y < 2 || y > innerHeight - 2 || x > innerWidth - 2) continue;
      const e = document.elementFromPoint(x, y); if (e && (e === n || n.contains(e))) return { x, y, 节点矩形: [r.x, r.y, r.width, r.height].map(Math.round) };
    }
  return { __err: 'unreachable', 节点矩形: [r.x, r.y, r.width, r.height].map(Math.round) };
}, B);
log('终点（目标节点内部）：', JSON.stringify(to));
out.to = to;
if (to.__err) { log('⛔ 中止'); save(); await b.close(); process.exit(3); }

// ---- 拖 ----
await p.mouse.move(from.x, from.y); await p.waitForTimeout(350);
await p.mouse.down(); await p.waitForTimeout(250);
await p.mouse.move(Math.round((from.x + to.x) / 2), Math.round((from.y + to.y) / 2), { steps: 12 }); await p.waitForTimeout(250);
out.midDrag = await p.evaluate(() => ({ 状态行: (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0],
  临时线元素: document.querySelectorAll('.react-flow__connectionline, .react-flow__connection, [class*="connection"]').length }));
log('拖到中点：', JSON.stringify(out.midDrag));
await p.mouse.move(to.x, to.y, { steps: 12 }); await p.waitForTimeout(350);
out.overTarget = await p.evaluate(() => ({ 状态行: (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0] }));
log('悬在目标上：', JSON.stringify(out.overTarget));
await p.mouse.up();
await p.waitForTimeout(2200);
out.afterLink = { status: await status(), edge数: await p.evaluate(() => document.querySelectorAll('.react-flow__edge').length) };
log('\n松手后：', JSON.stringify(out.afterLink));
save();
if (out.afterLink.edge数 < 1) { log('⛔ 没建出边（z 轮仍要清理自建节点）'); save(); log('DONE d-no-edge'); process.exit(0); }

// ---- ① SVG 层逐条读数 ----
out.edgeDom = await p.evaluate(() => {
  const r = (e) => { const q = e.getBoundingClientRect(); return [q.x, q.y, q.width, q.height].map(Math.round); };
  const c = (e) => { const s = getComputedStyle(e); return { pe: s.pointerEvents, op: s.opacity, vis: s.visibility, disp: s.display, stroke: s.stroke, sw: s.strokeWidth, fill: s.fill, dash: s.strokeDasharray, cap: s.strokeLinecap }; };
  const cont = document.querySelector('.react-flow__edges');
  return { 容器矩形: cont ? r(cont) : null, 容器样式: cont ? c(cont) : null, 容器子元素数: cont ? cont.children.length : null,
    容器内svg: cont ? Array.from(cont.querySelectorAll('svg')).map((s) => ({ viewBox: s.getAttribute('viewBox'), 矩形: r(s), 样式: c(s) })) : null,
    edges: Array.from(document.querySelectorAll('.react-flow__edge')).map((e) => ({ cls: e.getAttribute('class'), tid: e.getAttribute('data-testid'), id: e.getAttribute('data-id'),
      aria: e.getAttribute('aria-label'), 矩形: r(e), 样式: c(e),
      子: Array.from(e.children).map((k) => ({ tag: k.tagName, cls: (k.getAttribute('class') || '').toString(), d: (k.getAttribute('d') || '').slice(0, 100), 矩形: r(k), 样式: c(k) })) })) };
});
log('\n=== ① 边线的 DOM ===');
log('  容器矩形：', JSON.stringify(out.edgeDom.容器矩形), '｜容器子元素数：', out.edgeDom.容器子元素数);
log('  容器内 svg：', JSON.stringify(out.edgeDom.容器内svg));
out.edgeDom.edges.forEach((e, i) => { log(`  edge[${i}] cls=${e.cls}`); log(`     tid=${e.tid} 矩形=${JSON.stringify(e.矩形)}`); log(`     aria=${JSON.stringify(e.aria)}`); log(`     样式=${JSON.stringify(e.样式)}`);
  e.子.forEach((k) => log(`     └ <${k.tag}> cls=${JSON.stringify(k.cls)}\n        d=${JSON.stringify(k.d)}\n        矩形=${JSON.stringify(k.矩形)} stroke=${k.样式.stroke}/${k.样式.sw} op=${k.样式.op} vis=${k.样式.vis} pe=${k.样式.pe}`)); });
save();

// ---- ② 因果实验：藏 canvas 层 vs 藏 SVG 层 ----
const nodesRects = await p.evaluate((ids) => ids.map((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const q = n.getBoundingClientRect(); return [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)]; }), [A, B]);
const x0 = Math.max(0, Math.min(...nodesRects.map((r) => r[0])) - 60);
const y0 = Math.max(0, Math.min(...nodesRects.map((r) => r[1])) - 60);
const x1 = Math.min(1280, Math.max(...nodesRects.map((r) => r[0] + r[2])) + 60);
const y1 = Math.min(720, Math.max(...nodesRects.map((r) => r[1] + r[3])) + 60);
const crop = { x: x0, y: y0, width: x1 - x0, height: y1 - y0 };
log('\n裁剪区（包住两个节点与连线）：', JSON.stringify(crop));

await p.screenshot({ path: new URL('00-baseline.png', shotDir).pathname, clip: crop });
const h1 = await p.evaluate(() => { const h = document.querySelector('[data-testid="canvas-connection-flow-layer-host"]'); h.style.display = 'none'; return getComputedStyle(h).display; });
await p.waitForTimeout(700);
await p.screenshot({ path: new URL('01-canvas-hidden.png', shotDir).pathname, clip: crop });
await p.evaluate(() => { document.querySelector('[data-testid="canvas-connection-flow-layer-host"]').style.display = ''; });
await p.waitForTimeout(700);
const h2 = await p.evaluate(() => { const h = document.querySelector('.react-flow__edges'); h.style.display = 'none'; return getComputedStyle(h).display; });
await p.waitForTimeout(700);
await p.screenshot({ path: new URL('02-svg-hidden.png', shotDir).pathname, clip: crop });
await p.evaluate(() => { document.querySelector('.react-flow__edges').style.display = ''; });
await p.waitForTimeout(700);
await p.screenshot({ path: new URL('03-restored.png', shotDir).pathname, clip: crop });
out.causal = { 裁剪: crop, 藏canvas层时display: h1, 藏SVG层时display: h2,
  恢复校验: await p.evaluate(() => ({ canvasHost: getComputedStyle(document.querySelector('[data-testid="canvas-connection-flow-layer-host"]')).display,
    svg层: getComputedStyle(document.querySelector('.react-flow__edges')).display, edge数: document.querySelectorAll('.react-flow__edge').length })),
  截图: ['00-baseline.png', '01-canvas-hidden.png', '02-svg-hidden.png', '03-restored.png'] };
log('\n=== ② 因果实验 ===');
log('  ', JSON.stringify(out.causal));
out.end = { zoom: await zoom(), credits: await credits(), status: await status() };
save();
log('\n终点：', JSON.stringify(out.end));
log('\nDONE d');
process.exit(0);

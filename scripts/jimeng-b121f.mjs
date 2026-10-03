// 批次 121 · f 轮：把新节点拖开，**重做**因果实验。
//
// 🔴 e 轮的因果实验**不成立**（不是结论，是实验设计缺陷）：
//   截图里两个节点几乎贴在一起 —— `视频 2` 的卡片右缘 x≈485、`视频 4` 的左缘 x≈483，
//   **中间那段连线几乎为零长**，本来就看不见。
//   ⇒ 藏 canvas 层前后两张截图**逐像素看不出差别**，这**不能**推出「canvas 不负责画」。
//   📌 **立规：因果实验的裁剪区里必须有一段「足够长的、可确认存在的」被测对象**；
//     被测对象「本来就看不见」时，实验无效 —— 要先修实验，再下结论。
//
// 本轮：把 `视频 4` 拖到右边拉开距离 → 重读 SVG 边（它的矩形/`<g>` 会不会变大）
//       → 重做三张截图（baseline / 藏 canvas / 藏 SVG）。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'f' };
const save = () => writeFileSync(new URL('./_tmp-b121e.json', import.meta.url), JSON.stringify(out, null, 1));
const shotDir = new URL('./_tmp-b121e-shots/', import.meta.url);

const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);
const A = 'node_5k3gf1n51s', B = 'node_fs3jetarej';
out.start = { zoom: await zoom(), status: await status() };
log('起点：', JSON.stringify(out.start));

// ---- 拖开 B ----
const mv = await p.evaluate((id) => {
  const n = document.querySelector(`.react-flow__node[data-id="${id}"]`); if (!n) return { __err: 'gone' };
  const r = n.getBoundingClientRect();
  let grab = null;
  for (let y = Math.ceil(r.y) + 10; y < r.y + r.height - 10 && !grab; y += 4)
    for (let x = Math.ceil(r.x) + 10; x < r.x + r.width - 10; x += 4) {
      if (x < 4 || y < 4 || y > innerHeight - 4 || x > innerWidth - 4) continue;
      const e = document.elementFromPoint(x, y); if (e && (e === n || n.contains(e))) { grab = { x, y }; break; } }
  if (!grab) return { __err: 'no-grab' };
  let drop = null;
  for (const c of [[1180, 640], [1200, 200], [900, 640], [1150, 120]]) { const e = document.elementFromPoint(c[0], c[1]);
    if (e && !e.closest('.react-flow__node') && e.id !== 'root') { drop = c; break; } }
  return drop ? { grab, drop, 落点命中: (() => { const e = document.elementFromPoint(drop[0], drop[1]); return e ? e.tagName + ' ' + (e.className || '').toString().slice(0, 34) : null; })() } : { __err: 'no-drop' };
}, B);
log('拖开 B：', JSON.stringify(mv));
out.move = mv;
if (mv.__err) { log('⛔ 中止'); save(); await b.close(); process.exit(3); }
await p.mouse.move(mv.grab.x, mv.grab.y); await p.waitForTimeout(300);
await p.mouse.down(); await p.waitForTimeout(250);
await p.mouse.move(mv.drop[0], mv.drop[1], { steps: 20 }); await p.waitForTimeout(350);
await p.mouse.up(); await p.waitForTimeout(1800);
out.after = { zoom: await zoom(), status: await status(),
  矩形: await p.evaluate((ids) => ids.map((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); const q = n.getBoundingClientRect();
    return { id: i, 矩形: [q.x, q.y, q.width, q.height].map(Math.round) }; }), [A, B]) };
log('拖开后：', JSON.stringify(out.after));
save();

// ---- 重读 SVG 边：矩形/子元素会不会随两节点距离变大而变大 ----
out.edgeDom = await p.evaluate(() => {
  const r = (e) => { const q = e.getBoundingClientRect(); return [q.x, q.y, q.width, q.height].map(Math.round); };
  const c = (e) => { const s = getComputedStyle(e); return { pe: s.pointerEvents, op: s.opacity, vis: s.visibility, disp: s.display, stroke: s.stroke, sw: s.strokeWidth, fill: s.fill }; };
  const cont = document.querySelector('.react-flow__edges');
  const walk = (e, d) => { if (d > 3) return null; return { tag: e.tagName, cls: (e.getAttribute('class') || '').toString().slice(0, 60),
    d: (e.getAttribute('d') || '').slice(0, 120), 矩形: r(e), 样式: c(e), 子: Array.from(e.children).map((k) => walk(k, d + 1)).filter(Boolean) }; };
  return { 容器矩形: cont ? r(cont) : null, 容器样式: cont ? c(cont) : null,
    edge树: Array.from(document.querySelectorAll('.react-flow__edge')).map((e) => walk(e, 0)),
    edgeupdater: document.querySelectorAll('.react-flow__edgeupdater').length,
    全部path数: document.querySelectorAll('.react-flow__edge path').length,
    interaction命中区: document.querySelectorAll('.react-flow__edge-interaction').length };
});
log('\n=== SVG 边（拉开距离后）===');
log('  容器矩形：', JSON.stringify(out.edgeDom.容器矩形));
log('  edgeupdater 数 / .react-flow__edge path 数 / interaction 数：', out.edgeDom.edgeupdater, '/', out.edgeDom.全部path数, '/', out.edgeDom.interaction命中区);
log(JSON.stringify(out.edgeDom.edge树, null, 1));
save();

// ---- 三张截图 ----
const rects = out.after.矩形.map((r) => r.矩形);
const x0 = Math.max(0, Math.floor(Math.min(...rects.map((r) => r[0])) - 50));
const y0 = Math.max(0, Math.floor(Math.min(...rects.map((r) => r[1])) - 50));
const x1 = Math.min(1280, Math.ceil(Math.max(...rects.map((r) => r[0] + r[2])) + 50));
const y1 = Math.min(720, Math.ceil(Math.max(...rects.map((r) => r[1] + r[3])) + 50));
const crop = { x: x0, y: y0, width: x1 - x0, height: y1 - y0 };
log('\n裁剪区：', JSON.stringify(crop), '（连线净长度约 ' + Math.round(rects[1][0] - (rects[0][0] + rects[0][2])) + 'px）');
await p.screenshot({ path: new URL('10-baseline.png', shotDir).pathname, clip: crop });
await p.screenshot({ path: new URL('14-full.png', shotDir).pathname });
const h1 = await p.evaluate(() => { const h = document.querySelector('[data-testid="canvas-connection-flow-layer-host"]'); h.style.display = 'none'; return getComputedStyle(h).display; });
await p.waitForTimeout(800);
await p.screenshot({ path: new URL('11-canvas-hidden.png', shotDir).pathname, clip: crop });
await p.evaluate(() => { document.querySelector('[data-testid="canvas-connection-flow-layer-host"]').style.display = ''; });
await p.waitForTimeout(800);
const h2 = await p.evaluate(() => { const h = document.querySelector('.react-flow__edges'); h.style.display = 'none'; return getComputedStyle(h).display; });
await p.waitForTimeout(800);
await p.screenshot({ path: new URL('12-svg-hidden.png', shotDir).pathname, clip: crop });
await p.evaluate(() => { document.querySelector('.react-flow__edges').style.display = ''; });
await p.waitForTimeout(800);
await p.screenshot({ path: new URL('13-restored.png', shotDir).pathname, clip: crop });
out.causal = { 裁剪: crop, 藏canvas层时display: h1, 藏SVG层时display: h2,
  恢复校验: await p.evaluate(() => ({ canvasHost: getComputedStyle(document.querySelector('[data-testid="canvas-connection-flow-layer-host"]')).display,
    svg层: getComputedStyle(document.querySelector('.react-flow__edges')).display, edge数: document.querySelectorAll('.react-flow__edge').length })),
  截图: ['10-baseline.png', '11-canvas-hidden.png', '12-svg-hidden.png', '13-restored.png', '14-full.png'] };
log('\n因果：', JSON.stringify(out.causal));
out.end = { zoom: await zoom(), status: await status() };
save();
log('\n终点：', JSON.stringify(out.end));
log('\nDONE f');
process.exit(0);

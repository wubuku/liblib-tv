// 批次 121 · b3 轮：接着 b2 轮。
//
// 🔴 b2 轮的中断点：after ⊕ 按钮矩形读到了 `[770,310,36,36]`，但**中心落点的
//   `elementFromPoint` 命中的不是它**（`命中在按钮内: false`）⇒ 护栏④正确地拦下了点击。
//   原因：共享画布在 50% 下节点互相覆盖，**按钮中心被别的元素盖住**。
//   ⇒ 立规补强：**中心落点被否决时，不要换判据，要在按钮内部扫描出一个
//     真正命中它自己的点**（护栏④的「同一把尺」不许换，扫描是同一把尺）。
//     批次 115/117 那次栽的是「点容器空白处」，这次是「点被遮挡的中心」——两件事，
//     同一个解法：**在目标自身范围内重新取点，并逐点自检**。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'b3', 承接: 'b2 轮 after ⊕ 中心落点被遮挡，护栏④拦下' };
const save = () => writeFileSync(new URL('./_tmp-b121b.json', import.meta.url), JSON.stringify(out, null, 1));
const shotDir = new URL('./_tmp-b121b-shots/', import.meta.url);

const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node[data-id]')).map((n) => n.getAttribute('data-id')));
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);

// 在目标元素自身范围内扫描出一个「elementFromPoint 命中它自己」的点
const interiorPoint = (sel, id) => p.evaluate(([s, i]) => {
  const host = i ? document.querySelector(`.react-flow__node[data-id="${i}"]`) : document;
  const el = host.querySelector(s); if (!el) return { __err: 'not-found' };
  const r = el.getBoundingClientRect();
  const seen = [];
  for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 3)
    for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 3) {
      if (x < 2 || y < 2 || y > innerHeight - 2 || x > innerWidth - 2) continue;
      const h = document.elementFromPoint(x, y);
      if (h && (h === el || el.contains(h))) return { x, y, 矩形: [r.x, r.y, r.width, r.height].map(Math.round), 命中: h.tagName, aria: el.getAttribute('aria-label') };
      if (seen.length < 3) seen.push({ x, y, 盖住它的: h ? h.tagName + ' tid=' + h.getAttribute('data-testid') + ' cls=' + (h.className || '').toString().slice(0, 30) : null });
    }
  return { __err: 'no-interior-point', 矩形: [r.x, r.y, r.width, r.height].map(Math.round), 采样: seen };
}, [sel, id]);

out.start = { zoom: await zoom(), credits: await credits(), status: await status(), 节点数: (await ids()).length };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);

// ---- 确保「视频 2」是唯一选中项 ----
const A = 'node_5k3gf1n51s';
let selNow = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
if (selNow.length !== 1 || selNow[0] !== A) {
  const sp = await p.evaluate((id) => { const n = document.querySelector(`.react-flow__node[data-id="${id}"]`); if (!n) return { __err: 'gone' };
    const r = n.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 8; y < r.y + r.height - 8; y += 4)
      for (let x = Math.ceil(r.x) + 8; x < r.x + r.width - 8; x += 4) { if (x < 4 || y < 4 || y > innerHeight - 4 || x > innerWidth - 4) continue;
        const el = document.elementFromPoint(x, y); if (el && (el === n || n.contains(el))) return { x, y }; }
    return { __err: 'unreachable', rect: [r.x, r.y, r.width, r.height].map(Math.round) }; }, A);
  log('补选落点：', JSON.stringify(sp));
  if (sp.__err) { log('⛔ 中止'); save(); await b.close(); process.exit(3); }
  await p.mouse.click(sp.x, sp.y); await p.waitForTimeout(1500);
  selNow = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
}
log('选中态：', JSON.stringify(selNow));
if (selNow.length !== 1 || selNow[0] !== A) { log('⛔ 选中态不对，中止'); save(); await b.close(); process.exit(3); }

// ---- after ⊕ 按钮：在它自己范围内扫一个有效点 ----
const src = await interiorPoint('[data-testid="flow-node-source-connection-menu-button"], [aria-label^="Create connected node after"]', A);
log('\nafter ⊕ 落点（内部扫描）：', JSON.stringify(src));
out.srcPoint = src;
if (src.__err) { log('⛔ 按钮内部找不到有效落点，中止'); save(); await b.close(); process.exit(3); }
await p.mouse.click(src.x, src.y);
await p.waitForTimeout(1600);

out.menu = await p.evaluate(() => { for (const m of document.querySelectorAll('[role=menu]')) {
  if (getComputedStyle(m).visibility === 'hidden') continue; const r = m.getBoundingClientRect(); if (r.width < 1) continue;
  return { 菜单矩形: [r.x, r.y, r.width, r.height].map(Math.round),
    项: Array.from(m.querySelectorAll('[role=menuitem]')).map((it) => { const q = it.getBoundingClientRect();
      return { 逐字: (it.innerText || '').replace(/\s+/g, ' ').trim(), 矩形: [q.x, q.y, q.width, q.height].map(Math.round),
        禁用: it.getAttribute('aria-disabled') === 'true' || it.hasAttribute('disabled') }; }) }; }
  return null; });
log('菜单：', JSON.stringify(out.menu));
save();
const vi = out.menu && out.menu.项.find((x) => x.逐字.trim() === '视频' && !x.禁用);
if (!vi) { log('⛔ 菜单里没有可点的「视频」'); save(); await b.close(); process.exit(3); }
// 菜单项同样扫内部点
const mi = await p.evaluate((rect) => { const cx0 = rect[0], cy0 = rect[1], w = rect[2], h = rect[3];
  for (let y = Math.ceil(cy0) + 2; y <= cy0 + h - 2; y += 3) for (let x = Math.ceil(cx0) + 2; x <= cx0 + w - 2; x += 3) {
    const el = document.elementFromPoint(x, y);
    if (el && (el.innerText || '').replace(/\s+/g, ' ').trim() === rect.__逐字) return { x, y, 命中: el.tagName }; }
  const c = document.elementFromPoint(Math.round(cx0 + w / 2), Math.round(cy0 + h / 2));
  return { __err: 'no-point', 中心命中: c ? (c.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20) : null }; }, { ...vi.矩形, __逐字: vi.逐字 });
log('菜单项落点：', JSON.stringify(mi));
if (mi.__err) { log('⛔ 菜单项找不到有效落点，中止'); save(); await b.close(); process.exit(3); }
await p.mouse.click(mi.x, mi.y);
await p.waitForTimeout(2200);

out.afterLink = { status: await status(), edge数: await p.evaluate(() => document.querySelectorAll('.react-flow__edge').length) };
log('\n连线后：', JSON.stringify(out.afterLink));
save();
if (out.afterLink.edge数 < 1) { log('⛔ 没建出边，z 轮仍要清理自建节点'); save(); log('DONE b3-no-edge'); process.exit(0); }

// ---- ① SVG 层逐条读数 ----
out.edgeDom = await p.evaluate(() => {
  const r = (e) => { const q = e.getBoundingClientRect(); return [q.x, q.y, q.width, q.height].map(Math.round); };
  const c = (e) => { const s = getComputedStyle(e); return { pe: s.pointerEvents, op: s.opacity, vis: s.visibility, disp: s.display, stroke: s.stroke, strokeWidth: s.strokeWidth, fill: s.fill, dash: s.strokeDasharray }; };
  const cont = document.querySelector('.react-flow__edges');
  return { 容器矩形: cont ? r(cont) : null, 容器样式: cont ? c(cont) : null, 容器子元素数: cont ? cont.children.length : null,
    容器内svg: cont ? Array.from(cont.querySelectorAll('svg')).map((s) => ({ viewBox: s.getAttribute('viewBox'), 矩形: r(s), 样式: c(s) })) : null,
    edges: Array.from(document.querySelectorAll('.react-flow__edge')).map((e) => ({ cls: e.getAttribute('class'), tid: e.getAttribute('data-testid'), id: e.getAttribute('data-id'),
      aria: e.getAttribute('aria-label'), 矩形: r(e), 样式: c(e),
      子: Array.from(e.children).map((k) => ({ tag: k.tagName, cls: (k.getAttribute('class') || '').toString(), d: (k.getAttribute('d') || '').slice(0, 90), 矩形: r(k), 样式: c(k) })) })) };
});
log('\n=== ① 边线的 DOM ===');
log('  容器矩形：', JSON.stringify(out.edgeDom.容器矩形), '｜容器子元素数：', out.edgeDom.容器子元素数);
log('  容器内 svg：', JSON.stringify(out.edgeDom.容器内svg));
out.edgeDom.edges.forEach((e, i) => { log(`  edge[${i}] cls=${e.cls} tid=${e.tid} 矩形=${JSON.stringify(e.矩形)}`); log(`     aria=${JSON.stringify(e.aria)} 样式=${JSON.stringify(e.样式)}`);
  e.子.forEach((k) => log(`     └ <${k.tag}> cls=${JSON.stringify(k.cls)}\n        d=${JSON.stringify(k.d)}\n        矩形=${JSON.stringify(k.矩形)} stroke=${k.样式.stroke}/${k.样式.strokeWidth} op=${k.样式.op} vis=${k.样式.vis} pe=${k.样式.pe}`)); });
save();

// ---- ② 因果实验 ----
const crop = { x: 150, y: 100, width: 1000, height: 560 };
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
out.causal = { 藏canvas层时display: h1, 藏SVG层时display: h2,
  恢复校验: await p.evaluate(() => ({ canvasHost: getComputedStyle(document.querySelector('[data-testid="canvas-connection-flow-layer-host"]')).display,
    svg层: getComputedStyle(document.querySelector('.react-flow__edges')).display })),
  截图: ['01-canvas-hidden.png', '02-svg-hidden.png', '03-restored.png'], 裁剪: crop };
log('\n=== ② 因果实验 ===');
log('  ', JSON.stringify(out.causal));
out.end = { zoom: await zoom(), credits: await credits(), status: await status() };
save();
log('\n终点：', JSON.stringify(out.end));
log('\nDONE b3');
process.exit(0);

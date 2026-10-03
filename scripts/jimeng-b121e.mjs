// 批次 121 · e 轮：从 handle 热区**单击**（按 c 轮机制，这等价于「点 ⊕」）打开菜单，
// 用菜单建边，然后做因果实验。
//
// 🔴 d 轮的两个失败读数（本批第三次被护栏④拦下/读数落空）：
//   ① **拖拽建线失败**：起点命中 handle 热区 `[758,309]`、终点命中目标节点内部 `[488,280]`，
//      拖到中点时 `document.querySelectorAll('[class*="connection"]')` = **234**
//      （说明 React Flow **确实进入了连线态**），松手后仍是 **`0 edges`**。
//   ② **两个自建空视频节点几乎完全重叠**（都落在视口中心 `[473,257]` vs `[478,270]`），
//      目标节点内部**逐点都命中上面那个节点** ⇒ `unreachable`。
//      （d2 已把 A 拖到 `[249,534,284,160]`，两个节点现已分开。）
//
// 🔑 c 轮已查明：`[aria-label^="Create connected node after"]` 那个 ⊕ 按钮
//   **`pointer-events` 是 `none`** ⇒ 点它其实点的是 handle 的 `::before`。
//   ⇒ **点击 handle 热区 ≡ 点击 ⊕**。本轮就按这个来，先验证菜单是否弹出。
//
// ⚠️ 菜单若弹出并点「视频」，按手册那是「**添加节点**」——会**再建一个节点**并连上，
//   正好凑出一条边（三个自建节点，z 轮一起清）。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'e' };
const save = () => writeFileSync(new URL('./_tmp-b121e.json', import.meta.url), JSON.stringify(out, null, 1));
const shotDir = new URL('./_tmp-b121e-shots/', import.meta.url);

const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);
const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node[data-id]')).map((n) => n.getAttribute('data-id')));

out.start = { zoom: await zoom(), status: await status(), 节点数: (await ids()).length };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);
const baseline = new Set(await ids());
out.baselineCount = baseline.size;

const A = 'node_5k3gf1n51s';
// 确保 A 选中
let selNow = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
if (selNow.length !== 1 || selNow[0] !== A) {
  const sp = await p.evaluate((id) => { const n = document.querySelector(`.react-flow__node[data-id="${id}"]`); if (!n) return { __err: 'gone' };
    const r = n.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 8; y < r.y + r.height - 8; y += 4)
      for (let x = Math.ceil(r.x) + 8; x < r.x + r.width - 8; x += 4) { if (x < 4 || y < 4 || y > innerHeight - 4 || x > innerWidth - 4) continue;
        const e = document.elementFromPoint(x, y); if (e && (e === n || n.contains(e))) return { x, y }; }
    return { __err: 'unreachable', rect: [r.x, r.y, r.width, r.height].map(Math.round) }; }, A);
  if (sp.__err) { log('⛔ 补选失败'); save(); await b.close(); process.exit(3); }
  await p.mouse.click(sp.x, sp.y); await p.waitForTimeout(1500);
  selNow = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
}
log('选中态：', JSON.stringify(selNow));
if (selNow.length !== 1 || selNow[0] !== A) { log('⛔ 中止'); save(); await b.close(); process.exit(3); }

// handle 热区里命中 handle 的点
const hot = await p.evaluate((id) => {
  const n = document.querySelector(`.react-flow__node[data-id="${id}"]`); if (!n) return { __err: 'gone' };
  const h = n.querySelector('[data-testid="flow-node-source-handle"]'); const r = h.getBoundingClientRect();
  for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2)
    for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
      if (x < 2 || y < 2 || y > innerHeight - 2 || x > innerWidth - 2) continue;
      if (document.elementFromPoint(x, y) === h) return { x, y, handle矩形: [r.x, r.y, r.width, r.height].map(Math.round) }; }
  return { __err: 'no-hot-point' };
}, A);
log('\nhandle 热区落点：', JSON.stringify(hot));
out.hot = hot;
if (hot.__err) { log('⛔ 中止'); save(); await b.close(); process.exit(3); }

// 单击（不是拖）
await p.mouse.click(hot.x, hot.y);
await p.waitForTimeout(1600);
out.afterClick = await p.evaluate(() => {
  const menus = Array.from(document.querySelectorAll('[role=menu]')).filter((m) => getComputedStyle(m).visibility !== 'hidden' && m.getBoundingClientRect().width > 1);
  return { 菜单数: menus.length, 菜单: menus.map((m) => { const r = m.getBoundingClientRect();
    return { 矩形: [r.x, r.y, r.width, r.height].map(Math.round),
      项: Array.from(m.querySelectorAll('[role=menuitem]')).map((it) => { const q = it.getBoundingClientRect();
        return { 逐字: (it.innerText || '').replace(/\s+/g, ' ').trim(), 矩形: [q.x, q.y, q.width, q.height].map(Math.round),
          禁用: it.getAttribute('aria-disabled') === 'true' || it.hasAttribute('disabled') }; }) }; }),
    状态行: (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0] };
});
log('单击后：', JSON.stringify(out.afterClick, null, 1));
save();

const menu = out.afterClick.菜单[0];
if (!menu) { log('⛔ 菜单没弹出'); save(); log('DONE e-no-menu'); process.exit(0); }
const vi = menu.项.find((x) => x.逐字.trim() === '视频' && !x.禁用);
if (!vi) { log('⛔ 菜单里没有可点的「视频」'); save(); log('DONE e-no-video'); process.exit(0); }
const mi = await p.evaluate((rect) => { for (let y = Math.ceil(rect[1]) + 2; y <= rect[1] + rect[3] - 2; y += 3)
  for (let x = Math.ceil(rect[0]) + 2; x <= rect[0] + rect[2] - 2; x += 3) { const e = document.elementFromPoint(x, y);
    if (e && e.closest('[role=menuitem]') && (e.closest('[role=menuitem]').innerText || '').replace(/\s+/g, ' ').trim() === '视频') return { x, y }; }
  return { __err: 'no-point' }; }, vi.矩形);
log('菜单项落点：', JSON.stringify(mi));
if (mi.__err) { log('⛔ 中止'); save(); await b.close(); process.exit(3); }
await p.mouse.click(mi.x, mi.y);
await p.waitForTimeout(2400);

out.afterMenu = { status: await status(), edge数: await p.evaluate(() => document.querySelectorAll('.react-flow__edge').length), 节点数: (await ids()).length };
log('\n点完「视频」：', JSON.stringify(out.afterMenu));
const nowIds = await ids();
out.新出现节点 = nowIds.filter((i) => !baseline.has(i));
log('新出现的节点：', JSON.stringify(out.新出现节点));
save();
if (out.afterMenu.edge数 < 1) { log('⛔ 还是没建出边'); save(); log('DONE e-no-edge'); process.exit(0); }

// ---- ① SVG 层读数 ----
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

// ---- ② 因果实验 ----
const rects = await p.evaluate((list) => list.map((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
  const q = n.getBoundingClientRect(); return [q.x, q.y, q.width, q.height]; }).filter(Boolean), [A, ...out.新出现节点]);
const x0 = Math.max(0, Math.floor(Math.min(...rects.map((r) => r[0])) - 70));
const y0 = Math.max(0, Math.floor(Math.min(...rects.map((r) => r[1])) - 70));
const x1 = Math.min(1280, Math.ceil(Math.max(...rects.map((r) => r[0] + r[2])) + 70));
const y1 = Math.min(720, Math.ceil(Math.max(...rects.map((r) => r[1] + r[3])) + 70));
const crop = { x: x0, y: y0, width: x1 - x0, height: y1 - y0 };
log('\n裁剪区：', JSON.stringify(crop));
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
log('\nDONE e');
process.exit(0);

// 批次 121 · b 轮：造一条边，回答「屏幕上那条线到底是谁画的」。
//
// 🔴 a 轮已经把天平倾向 canvas 一侧，但**还没有决定性证据**：
//   a 轮实测 `canvas-connection-flow-layer` 是 **`<CANVAS>`**，`width=2560 height=1440`（dpr 2）、
//   CSS `100%×100%`、`pointer-events:none`，宿主 `canvas-connection-flow-layer-host`
//   `z-index:3` —— 而 `.react-flow__renderer`（节点层）是 **z=4**、`canvas-dot-grid` 是 **z=-1**。
//   🔑 **`canvas.getContext('2d')` 直接抛 `InvalidStateError: Cannot get context from a
//      canvas that has transferred its control to offscreen.`**
//   ⇒ 这张画布的位图**由 OffscreenCanvas + worker 持有**，页面侧读不到像素。
//   同时 `.react-flow__edges` 容器实测 `[-1019,-1221,0,0]`、**子元素 0**、`pointer-events:none`。
//
// ⚠️ a 轮**不足以下结论**：「0 条边时 SVG 容器是空的」既可能是「SVG 不负责画」，
//   也可能是「没边所以空」。⇒ 本轮造 1 条边再看。
//
// 🔑 决定性实验（**因果**，不是相关）：分别把两个绘制层**临时藏起来**再截图，
//   看那条线在不在：
//   ① 藏 `canvas-connection-flow-layer-host` ⇒ 线没了？⇒ canvas 负责画
//   ② 藏 `.react-flow__edges`（SVG 层）      ⇒ 线没了？⇒ SVG 负责画
//   每次都**立刻恢复**，两次都截图取证。
//
// 护栏：自建 2 个**空视频节点**（手册 7×7 表：视频源 after 只能连「视频」），
//   建前存 id 集合、建后差集必须恰好一个且是 `.selected`；连完 z 轮删干净。
//   **不碰任何他人的节点。**
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'b', 自建: [] };
const save = () => writeFileSync(new URL('./_tmp-b121b.json', import.meta.url), JSON.stringify(out, null, 1));
const shotDir = new URL('./_tmp-b121b-shots/', import.meta.url);

const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node[data-id]')).map((n) => n.getAttribute('data-id')));
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);

out.start = { zoom: await zoom(), credits: await credits(), status: await status() };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);
const before = await ids();
out.before = { 节点数: before.length };
log('基线节点数：', before.length);

// ============================================================
// 建 2 个空视频节点
// ============================================================
for (let k = 1; k <= 2; k++) {
  const beforeN = await ids();
  // 落点现算 + 自检：命中必须落在「视频」这个按钮内部
  const pt = await p.evaluate(() => {
    const rail = document.querySelector('[data-testid="canvas-fixed-toolbar-left-rail"]');
    if (!rail) return { __err: 'no-rail' };
    const btn = Array.from(rail.querySelectorAll('button,[role=button]')).find((e) => (e.getAttribute('aria-label') || '').trim() === '视频');
    if (!btn) return { __err: 'no-video-btn' };
    const r = btn.getBoundingClientRect();
    const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2);
    const el = document.elementFromPoint(cx, cy);
    return { rect: [r.x, r.y, r.width, r.height].map(Math.round), 落点: [cx, cy],
      命中: el ? el.tagName + ' aria=' + (el.getAttribute('aria-label') || el.getAttribute('data-testid')) : null,
      命中在按钮内: el ? (el === btn || btn.contains(el)) : false };
  });
  log(`\n建第 ${k} 个：落点 ` + JSON.stringify(pt));
  if (pt.__err || !pt.命中在按钮内) { log('⛔ 落点自检不通过，中止'); save(); await b.close(); process.exit(3); }
  await p.mouse.click(pt.落点[0], pt.落点[1]);
  await p.waitForTimeout(1600);
  const afterN = await ids();
  const diff = afterN.filter((i) => !beforeN.includes(i));
  const sel = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => ({ id: n.getAttribute('data-id'), 标题: (n.innerText || '').split('\n')[0] })));
  log(`  差集 = ${JSON.stringify(diff)}｜选中 = ${JSON.stringify(sel)}`);
  if (diff.length !== 1 || sel.length !== 1 || sel[0].id !== diff[0]) { log('⛔ 护栏②不通过，中止'); save(); await b.close(); process.exit(3); }
  out.自建.push({ 第: k, id: diff[0], 标题: sel[0].标题 });
  save();
}
log('\n自建节点：', JSON.stringify(out.自建));
save();

// 把视口缩一点，保证两个节点和它们的连线都在视口内
await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); e.click(); });
await p.waitForTimeout(500);
await p.fill('[data-testid="canvas-zoom-percent-input"]', '50');
await p.keyboard.press('Enter');
await p.waitForTimeout(1800);
out.zoomForWork = await zoom();
log('\n工作缩放：', out.zoomForWork);

// ============================================================
// 连线：点第一个节点的 after ⊕ → 菜单里选「视频」
// ============================================================
const A = out.自建[0].id;
const src = await p.evaluate((id) => {
  const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
  if (!n) return { __err: 'gone' };
  const r = n.getBoundingClientRect();
  // 先把它拖到一片空地（用 handle 之外的空白处？——不，共享画布禁止乱拖，改用现算的当前位置）
  const btn = n.querySelector('[data-testid="flow-node-source-connection-menu-button"], [aria-label^="Create connected node after"]');
  if (!btn) return { __err: 'no-after-btn', aria: Array.from(n.querySelectorAll('[aria-label]')).map((e) => e.getAttribute('aria-label')) };
  const br = btn.getBoundingClientRect();
  const cx = Math.round(br.x + br.width / 2), cy = Math.round(br.y + br.height / 2);
  const el = document.elementFromPoint(cx, cy);
  return { 节点矩形: [r.x, r.y, r.width, r.height].map(Math.round), 按钮矩形: [br.x, br.y, br.width, br.height].map(Math.round),
    落点: [cx, cy], 按钮aria: btn.getAttribute('aria-label'), 命中: el ? el.tagName : null, 命中在按钮内: el ? (el === btn || btn.contains(el)) : false };
}, A);
log('\nafter ⊕ 按钮：', JSON.stringify(src));
if (src.__err || !src.命中在按钮内) { log('⛔ 中止'); save(); await b.close(); process.exit(3); }
await p.mouse.click(src.落点[0], src.落点[1]);
await p.waitForTimeout(1500);

out.menu = await p.evaluate(() => {
  for (const m of document.querySelectorAll('[role=menu]')) {
    if (getComputedStyle(m).visibility === 'hidden') continue;
    const r = m.getBoundingClientRect(); if (r.width < 1) continue;
    return { 菜单矩形: [r.x, r.y, r.width, r.height].map(Math.round),
      项: Array.from(m.querySelectorAll('[role=menuitem]')).map((it) => { const q = it.getBoundingClientRect();
        return { 逐字: (it.innerText || '').replace(/\s+/g, ' ').trim(), 矩形: [q.x, q.y, q.width, q.height].map(Math.round),
          禁用: it.getAttribute('aria-disabled') === 'true' || it.hasAttribute('disabled') }; }) };
  }
  return null;
});
log('菜单：', JSON.stringify(out.menu, null, 1));
save();

const videoItem = out.menu && out.menu.项.find((x) => x.逐字.trim() === '视频' && !x.禁用);
if (!videoItem) { log('⛔ 菜单里没有可点的「视频」，中止'); save(); await b.close(); process.exit(3); }
const hitItem = await p.evaluate((rect) => { const cx = Math.round(rect[0] + rect[2] / 2), cy = Math.round(rect[1] + rect[3] / 2);
  const el = document.elementFromPoint(cx, cy); return { 命中: el ? el.tagName + ' ' + (el.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 12) : null, 命中逐字: el ? (el.innerText || '').replace(/\s+/g, ' ').trim() : null }; }, videoItem.矩形);
log('菜单项落点自检：', JSON.stringify(hitItem));
await p.mouse.click(videoItem.矩形[0] + videoItem.矩形[2] / 2, videoItem.矩形[1] + videoItem.矩形[3] / 2);
await p.waitForTimeout(2000);

out.afterLink = { status: await status(), edge数: await p.evaluate(() => document.querySelectorAll('.react-flow__edge').length) };
log('\n连线后：', JSON.stringify(out.afterLink));
save();

// ============================================================
// ① SVG 层的逐条读数（这条边到底由什么元素构成、画不画得出来）
// ============================================================
out.edgeDom = await p.evaluate(() => {
  const r = (e) => { const q = e.getBoundingClientRect(); return [q.x, q.y, q.width, q.height].map(Math.round); };
  const c = (e) => { const s = getComputedStyle(e); return { pe: s.pointerEvents, op: s.opacity, vis: s.visibility, disp: s.display,
    stroke: s.stroke, strokeWidth: s.strokeWidth, fill: s.fill, strokeDasharray: s.strokeDasharray, strokeLinecap: s.strokeLinecap }; };
  const cont = document.querySelector('.react-flow__edges');
  const edges = Array.from(document.querySelectorAll('.react-flow__edge')).map((e) => ({
    cls: e.getAttribute('class'), tid: e.getAttribute('data-testid'), id: e.getAttribute('data-id'),
    aria: e.getAttribute('aria-label'), rect: r(e), 样式: c(e),
    子: Array.from(e.children).map((k) => ({ tag: k.tagName, cls: (k.getAttribute('class') || '').toString(), d: (k.getAttribute('d') || '').slice(0, 70), 矩形: r(k), 样式: c(k) })),
  }));
  return { 容器矩形: cont ? r(cont) : null, 容器样式: cont ? c(cont) : null, 容器子元素数: cont ? cont.children.length : null,
    容器内svg: cont ? Array.from(cont.querySelectorAll('svg')).map((s) => ({ viewBox: s.getAttribute('viewBox'), 矩形: r(s), 样式: c(s) })) : null,
    edge数: edges.length, edges };
});
log('\n=== ① 边线的 DOM ===');
log('  容器矩形：', JSON.stringify(out.edgeDom.容器矩形), '｜子元素数：', out.edgeDom.容器子元素数, '｜容器内 svg：', JSON.stringify(out.edgeDom.容器内svg));
out.edgeDom.edges.forEach((e, i) => { log(`  edge[${i}] cls=${e.cls} tid=${e.tid} rect=${JSON.stringify(e.rect)}`); log(`     aria=${JSON.stringify(e.aria)}`); log(`     样式=${JSON.stringify(e.样式)}`); e.子.forEach((k) => log(`     └ <${k.tag}> cls=${JSON.stringify(k.cls)} 矩形=${JSON.stringify(k.矩形)} stroke=${k.样式.stroke}/${k.样式.strokeWidth} op=${k.样式.opacity} vis=${k.样式.vis} pe=${k.样式.pe}`)); });
save();

// ============================================================
// ② 因果实验：分别藏两个绘制层，各截一张图（每次都恢复）
// ============================================================
async function shot(name) { await p.screenshot({ path: new URL(name, shotDir).pathname }); }
const crop = { x: 200, y: 120, width: 900, height: 520 };
await p.screenshot({ path: new URL('00-baseline.png', shotDir).pathname, clip: crop });
out.causal = {};
out.causal.baseline = '00-baseline.png';

// 实验①：藏 canvas 层
const hid1 = await p.evaluate(() => { const h = document.querySelector('[data-testid="canvas-connection-flow-layer-host"]'); if (!h) return null;
  const prev = h.style.display; h.style.display = 'none'; return { prev, now: getComputedStyle(h).display }; });
await p.waitForTimeout(500);
await p.screenshot({ path: new URL('01-canvas-hidden.png', shotDir).pathname, clip: crop });
await p.evaluate(() => { document.querySelector('[data-testid="canvas-connection-flow-layer-host"]').style.display = ''; });
await p.waitForTimeout(500);
out.causal.藏canvas层 = { 藏时: hid1, 截图: '01-canvas-hidden.png' };

// 实验②：藏 SVG 层
const hid2 = await p.evaluate(() => { const h = document.querySelector('.react-flow__edges'); if (!h) return null;
  const prev = h.style.display; h.style.display = 'none'; return { prev, now: getComputedStyle(h).display }; });
await p.waitForTimeout(500);
await p.screenshot({ path: new URL('02-svg-hidden.png', shotDir).pathname, clip: crop });
await p.evaluate(() => { document.querySelector('.react-flow__edges').style.display = ''; });
await p.waitForTimeout(500);
await p.screenshot({ path: new URL('03-restored.png', shotDir).pathname, clip: crop });
out.causal.藏SVG层 = { 藏时: hid2, 截图: '02-svg-hidden.png', 恢复后: '03-restored.png' };
log('\n=== ② 因果实验 ===');
log('  藏 canvas 层：', JSON.stringify(out.causal.藏canvas层));
log('  藏 SVG 层：', JSON.stringify(out.causal.藏SVG层));
// 恢复校验
out.causal.恢复校验 = await p.evaluate(() => ({
  canvasHost: getComputedStyle(document.querySelector('[data-testid="canvas-connection-flow-layer-host"]')).display,
  svg层: getComputedStyle(document.querySelector('.react-flow__edges')).display,
}));
log('  恢复校验：', JSON.stringify(out.causal.恢复校验));
save();

out.end = { zoom: await zoom(), credits: await credits(), status: await status() };
save();
log('\n终点：', JSON.stringify(out.end));
log('\nDONE b（自建节点留给 z 轮清理）');
process.exit(0);

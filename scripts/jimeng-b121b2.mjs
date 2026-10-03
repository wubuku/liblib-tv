// 批次 121 · b2 轮：接着 b 轮往下走。
//
// 🔴 b 轮的中断点：两个自建空视频节点已建好（`node_5k3gf1n51s` 视频 2 /
//   `node_bm52y0m7hn` 视频 3，护栏②两次都通过），但改缩放时用
//   `page.evaluate(() => el.click())` **合成点击**没能打开 Radix 缩放菜单，
//   `canvas-zoom-percent-input` 30s 超时。
//   ⇒ 教训入册：**Radix 弹层要用真实鼠标点击打开**，合成 `.click()` 不行。
//   （落点仍按护栏④现算 + `elementFromPoint` 自检。）
//
// 本轮：改缩放 → 连线 → 读 SVG 层 → 因果实验（分别藏两个绘制层）→ 截图。
// 自建节点留给 z 轮清理。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'b2', 承接: 'b 轮建节点后中断（合成 click 打不开 Radix 缩放菜单）' };
const save = () => writeFileSync(new URL('./_tmp-b121b.json', import.meta.url), JSON.stringify(out, null, 1));
const shotDir = new URL('./_tmp-b121b-shots/', import.meta.url);

const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node[data-id]')).map((n) => n.getAttribute('data-id')));
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);

out.start = { zoom: await zoom(), credits: await credits(), status: await status(), 节点数: (await ids()).length };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);

// ---- 真实鼠标点击打开缩放菜单 ----
const zpt = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); const r = e.getBoundingClientRect();
  const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2); const el = document.elementFromPoint(cx, cy);
  return { 落点: [cx, cy], 命中在按钮内: el ? (el === e || e.contains(el)) : false, 命中: el ? el.tagName : null }; });
log('缩放按钮落点自检：', JSON.stringify(zpt));
if (!zpt.命中在按钮内) { log('⛔ 中止'); save(); await b.close(); process.exit(3); }
await p.mouse.click(zpt.落点[0], zpt.落点[1]);
await p.waitForTimeout(900);
out.zoomMenuOpened = await p.evaluate(() => ({ 菜单: !!document.querySelector('[data-testid="canvas-zoom-menu"]'), 输入框: !!document.querySelector('[data-testid="canvas-zoom-percent-input"]') }));
log('缩放菜单：', JSON.stringify(out.zoomMenuOpened));
if (out.zoomMenuOpened.输入框) { await p.fill('[data-testid="canvas-zoom-percent-input"]', '50'); await p.keyboard.press('Enter'); }
else { log('⛔ 输入框没出现，中止'); save(); await b.close(); process.exit(3); }
await p.waitForTimeout(1900);
out.zoomForWork = await zoom();
log('工作缩放：', out.zoomForWork);
save();

// ---- 连线：重新选中「视频 2」，点它的 after ⊕ ----
const A = 'node_5k3gf1n51s';
let selNow = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
log('\n改缩放后选中态：', JSON.stringify(selNow));
if (selNow.length !== 1 || selNow[0] !== A) {
  const sp = await p.evaluate((id) => { const n = document.querySelector(`.react-flow__node[data-id="${id}"]`); if (!n) return { __err: 'gone' };
    const r = n.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 8; y < r.y + r.height - 8; y += 5)
      for (let x = Math.ceil(r.x) + 8; x < r.x + r.width - 8; x += 5) { if (x < 4 || y < 4 || y > innerHeight - 4 || x > innerWidth - 4) continue;
        const el = document.elementFromPoint(x, y); if (el && (el === n || n.contains(el))) return { x, y }; }
    return { __err: 'unreachable', rect: [r.x, r.y, r.width, r.height].map(Math.round) }; }, A);
  log('补选落点：', JSON.stringify(sp));
  if (sp.__err) { log('⛔ 中止'); save(); await b.close(); process.exit(3); }
  await p.mouse.click(sp.x, sp.y); await p.waitForTimeout(1500);
  selNow = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
  log('补选后：', JSON.stringify(selNow));
  if (selNow.length !== 1 || selNow[0] !== A) { log('⛔ 补选失败，中止'); save(); await b.close(); process.exit(3); }
}

const src = await p.evaluate((id) => {
  const n = document.querySelector(`.react-flow__node[data-id="${id}"]`); if (!n) return { __err: 'gone' };
  const r = n.getBoundingClientRect();
  const btn = n.querySelector('[data-testid="flow-node-source-connection-menu-button"], [aria-label^="Create connected node after"]');
  if (!btn) return { __err: 'no-after-btn', aria: Array.from(n.querySelectorAll('[aria-label]')).map((e) => e.getAttribute('aria-label')) };
  const br = btn.getBoundingClientRect(); const cx = Math.round(br.x + br.width / 2), cy = Math.round(br.y + br.height / 2);
  const el = document.elementFromPoint(cx, cy);
  return { 节点矩形: [r.x, r.y, r.width, r.height].map(Math.round), 按钮矩形: [br.x, br.y, br.width, br.height].map(Math.round), 落点: [cx, cy],
    按钮aria: btn.getAttribute('aria-label'), 命中在按钮内: el ? (el === btn || btn.contains(el)) : false };
}, A);
log('\nafter ⊕：', JSON.stringify(src));
if (src.__err || !src.命中在按钮内) { log('⛔ 中止'); save(); await b.close(); process.exit(3); }
await p.mouse.click(src.落点[0], src.落点[1]);
await p.waitForTimeout(1500);

out.menu = await p.evaluate(() => { for (const m of document.querySelectorAll('[role=menu]')) {
  if (getComputedStyle(m).visibility === 'hidden') continue; const r = m.getBoundingClientRect(); if (r.width < 1) continue;
  return { 菜单矩形: [r.x, r.y, r.width, r.height].map(Math.round), 标题: (m.innerText || '').split('\n')[0],
    项: Array.from(m.querySelectorAll('[role=menuitem]')).map((it) => { const q = it.getBoundingClientRect();
      return { 逐字: (it.innerText || '').replace(/\s+/g, ' ').trim(), 矩形: [q.x, q.y, q.width, q.height].map(Math.round),
        禁用: it.getAttribute('aria-disabled') === 'true' || it.hasAttribute('disabled') }; }) }; }
  return null; });
log('菜单：', JSON.stringify(out.menu));
save();
const vi = out.menu && out.menu.项.find((x) => x.逐字.trim() === '视频' && !x.禁用);
if (!vi) { log('⛔ 菜单里没有可点的「视频」'); save(); await b.close(); process.exit(3); }
await p.mouse.click(vi.矩形[0] + vi.矩形[2] / 2, vi.矩形[1] + vi.矩形[3] / 2);
await p.waitForTimeout(2100);
out.afterLink = { status: await status(), edge数: await p.evaluate(() => document.querySelectorAll('.react-flow__edge').length) };
log('\n连线后：', JSON.stringify(out.afterLink));
save();

// ---- ① SVG 层逐条读数 ----
out.edgeDom = await p.evaluate(() => {
  const r = (e) => { const q = e.getBoundingClientRect(); return [q.x, q.y, q.width, q.height].map(Math.round); };
  const c = (e) => { const s = getComputedStyle(e); return { pe: s.pointerEvents, op: s.opacity, vis: s.visibility, disp: s.display, stroke: s.stroke, strokeWidth: s.strokeWidth, fill: s.fill, d: s.strokeDasharray }; };
  const cont = document.querySelector('.react-flow__edges');
  return { 容器矩形: cont ? r(cont) : null, 容器样式: cont ? c(cont) : null, 容器子元素数: cont ? cont.children.length : null,
    容器内svg: cont ? Array.from(cont.querySelectorAll('svg')).map((s) => ({ viewBox: s.getAttribute('viewBox'), 矩形: r(s), 样式: c(s) })) : null,
    edges: Array.from(document.querySelectorAll('.react-flow__edge')).map((e) => ({ cls: e.getAttribute('class'), tid: e.getAttribute('data-testid'), id: e.getAttribute('data-id'),
      aria: e.getAttribute('aria-label'), 矩形: r(e), 样式: c(e),
      子: Array.from(e.children).map((k) => ({ tag: k.tagName, cls: (k.getAttribute('class') || '').toString(), d: (k.getAttribute('d') || '').slice(0, 80), 矩形: r(k), 样式: c(k) })) })) };
});
log('\n=== ① 边线的 DOM ===');
log('  容器矩形：', JSON.stringify(out.edgeDom.容器矩形), '｜容器子元素数：', out.edgeDom.容器子元素数);
log('  容器内 svg：', JSON.stringify(out.edgeDom.容器内svg));
out.edgeDom.edges.forEach((e, i) => { log(`  edge[${i}] cls=${e.cls} tid=${e.tid} 矩形=${JSON.stringify(e.矩形)}`); log(`     aria=${JSON.stringify(e.aria)} 样式=${JSON.stringify(e.样式)}`);
  e.子.forEach((k) => log(`     └ <${k.tag}> cls=${JSON.stringify(k.cls)}\n        d=${JSON.stringify(k.d)}\n        矩形=${JSON.stringify(k.矩形)} stroke=${k.样式.stroke}/${k.样式.strokeWidth} op=${k.样式.op} vis=${k.样式.vis} pe=${k.样式.pe}`)); });
save();

// ---- ② 因果实验 ----
const crop = { x: 150, y: 100, width: 1000, height: 560 };
out.causal = {};
await p.screenshot({ path: new URL('00-baseline.png', shotDir).pathname, clip: crop });
const h1 = await p.evaluate(() => { const h = document.querySelector('[data-testid="canvas-connection-flow-layer-host"]'); const prev = h.style.display; h.style.display = 'none'; return getComputedStyle(h).display; });
await p.waitForTimeout(600);
await p.screenshot({ path: new URL('01-canvas-hidden.png', shotDir).pathname, clip: crop });
await p.evaluate(() => { document.querySelector('[data-testid="canvas-connection-flow-layer-host"]').style.display = ''; });
await p.waitForTimeout(600);
const h2 = await p.evaluate(() => { const h = document.querySelector('.react-flow__edges'); const prev = h.style.display; h.style.display = 'none'; return getComputedStyle(h).display; });
await p.waitForTimeout(600);
await p.screenshot({ path: new URL('02-svg-hidden.png', shotDir).pathname, clip: crop });
await p.evaluate(() => { document.querySelector('.react-flow__edges').style.display = ''; });
await p.waitForTimeout(600);
await p.screenshot({ path: new URL('03-restored.png', shotDir).pathname, clip: crop });
out.causal = { 藏canvas层时display: h1, 藏SVG层时display: h2,
  恢复校验: await p.evaluate(() => ({ canvasHost: getComputedStyle(document.querySelector('[data-testid="canvas-connection-flow-layer-host"]')).display,
    svg层: getComputedStyle(document.querySelector('.react-flow__edges')).display })),
  截图: ['00-baseline.png', '01-canvas-hidden.png', '02-svg-hidden.png', '03-restored.png'] };
log('\n=== ② 因果实验 ===');
log('  ', JSON.stringify(out.causal));
out.end = { zoom: await zoom(), credits: await credits(), status: await status() };
save();
log('\n终点：', JSON.stringify(out.end));
log('\nDONE b2');
process.exit(0);

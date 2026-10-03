// 批次 123 · b 轮：把「顶栏空白处会把点击穿透到画布」做成**双向对照**。
//
// 🔴 **a 轮推翻了我自己的假设**（这条要如实写进手册）：
//   我以为「节点盖住了顶栏」。实测否掉了：
//   · 顶栏 `HEADER[canvas-top-bar]` **z-index = 30**，节点层 `.react-flow__renderer` **z-index = 4**
//     ⇒ **顶栏在节点之上**，几何上「压过」根本没发生。
//   · 顶栏 8 个按钮逐点自测：`canvas-project-title-trigger` 198/198、
//     `canvas-project-trigger` 54/54、`canvas-node-summary-trigger` 90/90、
//     `canvas-share-trigger` 171/171、`canvas-editor-menu` 121/121、
//     `canvas-commerce-entry` 324/324、`canvas-user-menu-trigger` 81/81
//     —— **全部 100% 可命中**；`canvas-project-logo` 158/169，挡住它的 11 个采样点
//     是**它自己的兄弟** `DIV[canvas-title-details]` 压了右边缘，**不是节点**。
//   · 真正的机制：顶栏整条是 **`pointer-events: none`**（`HEADER`、`canvas-top-bar-left` 都是 `none`），
//     **只有真正的按钮把 `pointer-events` 重开成 `auto`**（`canvas-top-bar-actions` 是 `auto`）。
//     ⇒ 中线上 52.5%（x∈[250,906]）命中的是节点/节点把手，**不是「被盖住」，是顶栏自己让开了**。
//
// 🔑 双向对照（本轮要做的，两边只差「点的是空白还是按钮」）：
//   ① 在**空白处**点（命中某个节点本体）→ 那个节点会不会被选中？
//   ② 在**按钮上**点（同一个 x 区间之外的「节点 N」）→ 按钮会不会赢（面板打开）？
//   ⇒ 两条读数合起来才敢说「空白处穿透、按钮处不穿透」。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'b' };
const save = () => writeFileSync(new URL('./_tmp-b123b.json', import.meta.url), JSON.stringify(out, null, 1));
const shotDir = new URL('./_tmp-b123b-shots/', import.meta.url);

const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);
const sel = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => ({ id: n.getAttribute('data-id'), 标题: (n.innerText || '').split('\n')[0] })));

out.start = { zoom: await zoom(), credits: await credits(), status: await status() };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);

// ============================================================
// 找「顶栏空白处、且命中某个节点本体」的点（避开 handle）
// ============================================================
const spot = await p.evaluate(() => {
  const bar = document.querySelector('[data-testid="canvas-top-bar"]');
  const r = bar.getBoundingClientRect();
  const y = Math.round(r.y + r.height / 2);
  for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
    const e = document.elementFromPoint(x, y);
    if (!e) continue;
    if (bar.contains(e)) continue;                      // 必须是顶栏让开的地方
    const node = e.closest('.react-flow__node[data-id]');
    if (!node) continue;
    if (e.hasAttribute('data-testid') && /handle/.test(e.getAttribute('data-testid'))) continue;  // 避开连接把手
    const nq = node.getBoundingClientRect();
    return { x, y, 命中: e.tagName + ' tid=' + e.getAttribute('data-testid'),
      节点id: node.getAttribute('data-id'), 节点标题: (node.innerText || '').split('\n')[0],
      节点矩形: [nq.x, nq.y, nq.width, nq.height].map(Math.round),
      该点在节点内: x > nq.left && x < nq.right && y > nq.top && y < nq.bottom,
      该点在顶栏矩形内: x > r.left && x < r.right && y > r.top && y < r.bottom,
      该点在顶栏任何可点子元素内: (() => { for (const c of bar.querySelectorAll('*')) { const q = c.getBoundingClientRect();
        if (getComputedStyle(c).pointerEvents === 'auto' && q.width > 1 && x > q.left && x < q.right && y > q.top && y < q.bottom) return c.tagName + ' tid=' + c.getAttribute('data-testid'); } return null; })() };
  }
  return null;
});
log('\n① 候选落点（顶栏空白处 + 命中节点本体）：', JSON.stringify(spot, null, 1));
out.spot = spot;
if (!spot || !spot.该点在节点内 || !spot.该点在顶栏矩形内 || spot.该点在顶栏任何可点子元素内) {
  log('⛔ 落点不满足三条件，中止'); save(); await b.close(); process.exit(3);
}
await p.screenshot({ path: new URL('00-before.png', shotDir).pathname, clip: { x: 0, y: 0, width: 1280, height: 90 } });

// ---- ① 点它 ----
await p.mouse.click(spot.x, spot.y);
await p.waitForTimeout(1500);
out.afterBlankClick = { 选中: await sel(), status: await status() };
log('\n② 点顶栏空白处之后：', JSON.stringify(out.afterBlankClick));
await p.screenshot({ path: new URL('01-after-blank-click.png', shotDir).pathname, clip: { x: 0, y: 0, width: 1280, height: 90 } });
save();

// ---- 取消选中：找一个真正的画布空白点（命中 .react-flow__pane 且不在任何节点内） ----
const blank = await p.evaluate(() => { for (let y = 200; y < 600; y += 7) for (let x = 200; x < 1100; x += 7) {
  const e = document.elementFromPoint(x, y);
  if (e && e.classList && e.classList.contains('react-flow__pane') && !e.closest('.react-flow__node')) return { x, y }; }
  return null; });
log('取消选中的落点（必须是 pane）：', JSON.stringify(blank));
out.blank = blank;
if (blank) { await p.mouse.click(blank.x, blank.y); await p.waitForTimeout(1300); }
out.afterUnselect = { 选中: await sel(), status: await status() };
log('  取消后：', JSON.stringify(out.afterUnselect));
save();

// ============================================================
// ② 对照：点「节点 N」按钮（同一顶栏的另一处）
// ============================================================
const btn = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-node-summary-trigger"]');
  const r = e.getBoundingClientRect();
  for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
    const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y, 矩形: [r.x, r.y, r.width, r.height].map(Math.round) }; }
  return { __err: 'no-point' }; });
log('\n③「节点 N」按钮落点：', JSON.stringify(btn));
out.btnPoint = btn;
if (!btn.__err) {
  await p.mouse.click(btn.x, btn.y);
  await p.waitForTimeout(1500);
  out.afterBtnClick = await p.evaluate(() => ({ 选中: Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')),
    浮层: Array.from(document.querySelectorAll('[role=dialog],[role=menu]')).filter((m) => m.getBoundingClientRect().width > 1)
      .map((m) => ({ role: m.getAttribute('role'), tid: m.getAttribute('data-testid'), 矩形: (() => { const q = m.getBoundingClientRect(); return [q.x, q.y, q.width, q.height].map(Math.round); })(),
        文字: (m.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 60) })) }));
  log('  点按钮后：', JSON.stringify(out.afterBtnClick, null, 1));
  await p.screenshot({ path: new URL('02-after-btn-click.png', shotDir).pathname, clip: { x: 0, y: 0, width: 1280, height: 420 } });
  await p.keyboard.press('Escape'); await p.waitForTimeout(1200);
  out.afterEsc = await p.evaluate(() => ({ 浮层数: Array.from(document.querySelectorAll('[role=dialog],[role=menu]')).filter((m) => m.getBoundingClientRect().width > 1).length,
    选中: Array.from(document.querySelectorAll('.react-flow__node.selected')).length }));
  log('  Esc 后：', JSON.stringify(out.afterEsc));
}
save();

// ---- 收尾：确保 0 选中 ----
if ((await sel()).length !== 0) {
  const b2 = await p.evaluate(() => { for (let y = 200; y < 620; y += 7) for (let x = 200; x < 1100; x += 7) {
    const e = document.elementFromPoint(x, y); if (e && e.classList && e.classList.contains('react-flow__pane')) return { x, y }; } return null; });
  if (b2) { await p.mouse.click(b2.x, b2.y); await p.waitForTimeout(1300); }
}
out.终态 = { zoom: await zoom(), credits: await credits(), 选中: await sel(), status: await status(),
  浮层数: await p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu]')).filter((m) => m.getBoundingClientRect().width > 1).length) };
log('\n终态：', JSON.stringify(out.终态));
save();
log('\nDONE b');
process.exit(0);

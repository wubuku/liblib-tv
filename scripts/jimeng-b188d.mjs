// 批次 188 d 轮：**多选工具条里的 ⊕ 与单节点 ⊕ 是不是同一个契约？**
//
// 起因：20-reference.md:533（批次 135）写着「同一 testid 下另有四个元素四档**屏上恒定**
// … 多选手柄 `60×120`、**连接菜单按钮 `36×36`**」，而 188 刚测出单节点 ⊕ 是
// **canvas 恒定 72×72**（26%→19、50%→36）⇒ 两处的 `36×36` **只可能成立于不同元素或不同缩放**。
//
// 🔑 线索：共用库 `readMultiToolbar` 读的那个 testid 是
//   `flow-node-multi-selection-source-connection-menu-button`，
//   与单节点的 `flow-node-source-connection-menu-button` **字面就不同**。
//
// 本轮做**同页同轮**对照：框选 ≥2 节点后，在 4 档缩放下**同时**读这两个元素 ——
// 如果一个随缩放变、另一个不变，那就是**两套契约**，手册必须分开写，不能笼统说「连接菜单按钮」。
import { openCanvas, readers, settle, setZoom, planBox, doBox, endState } from './jimeng-b135-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '188d', 假设: '多选 ⊕ 与单节点 ⊕ 是两套契约' };
await settle(p, R);
rec.起点 = { 节点数: (await R.ids()).length, 积分: await R.credits(), 缩放: await R.zoom(), 状态行: await R.status() };
// endState 的基线要的是 ids/testids 数组，不是计数
const 基线 = { ids: await R.ids(), testids: await R.testids() };

/** 同时读：多选 ⊕ / 多选手柄 / 单节点 ⊕（逐个列 testid）+ 当前 scale。 */
const 读两个加号 = () => p.evaluate(() => {
  const box = (e) => { if (!e) return null; const r = e.getBoundingClientRect();
    return { w: Math.round(r.width * 10) / 10, h: Math.round(r.height * 10) / 10 }; };
  const vp = document.querySelector('.react-flow__viewport');
  const ms = vp ? /scale\(([-\d.]+)\)/.exec(vp.style.transform || '') : null;
  const scale = ms ? parseFloat(ms[1]) : null;
  const inMulti = (e) => !!e.closest('[data-testid="selection-context-toolbar-surface"]');
  const 单节点加号 = Array.from(document.querySelectorAll('[aria-label^="Create connected node"]'))
    .map((e) => ({ testid: e.getAttribute('data-testid'), 逐字aria: e.getAttribute('aria-label'),
      在多选工具条内: inMulti(e), ...box(e) }))
    .filter((x) => !x.在多选工具条内);
  const 多选加号 = Array.from(document.querySelectorAll('[data-testid^="flow-node-multi-selection-connection-menu-button"]'))
    .map((e) => ({ testid: e.getAttribute('data-testid'), 逐字aria: e.getAttribute('aria-label'),
      ...box(e), 祖先末级: (() => { let n = e; const c = []; for (let i = 0; i < 6 && n && n !== document.body; i++, n = n.parentElement) c.push(String(n.className || '').split(' ')[0] || n.tagName); return c; })() }));
  return {
    scale, 缩放aria: (document.querySelector('[data-testid="canvas-zoom-percent"]') || {}).ariaLabel || null,
    选中数: document.querySelectorAll('.react-flow__node.selected').length,
    多选加号, 单节点加号,
    多选手柄: box(document.querySelector('[data-testid="flow-node-multi-selection-source-handle"]')),
    多选条: box(document.querySelector('[data-testid="selection-context-toolbar-surface"]')),
    多选条内层: box(document.querySelector('[data-testid="selection-context-toolbar"]')),
    计数项: box(document.querySelector('[data-testid="selection-context-toolbar-count"]')),
  };
});

// —— 选中 ≥2 个节点：框选规划在 76 个节点挤在一起的画布上找不到四角都空着的矩形，
//    ⇧+点击加选也只选中 1 个（实测，本轮 188d）⇒ 改成**从 pane 空白点拖出选区**：
//    只要求**按下点**落在 `.react-flow__pane`（doBox 也是这么验的），终点取两个节点的包围盒外扩。
rec.落点 = await p.evaluate(() => {
  const isPane = (x, y) => { const h = document.elementFromPoint(x, y); return !!(h && h.classList && h.classList.contains('react-flow__pane')); };
  let 起 = null;
  for (let y = 80; y <= innerHeight - 80 && !起; y += 6)
    for (let x = 8; x <= innerWidth - 340; x += 6) if (isPane(x, y)) { 起 = [x, y]; break; }
  if (!起) return { ok: false, 原因: '画布右侧 340px 内找不到 pane 空白点' };
  const ns = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => { const r = n.getBoundingClientRect();
    return { id: n.getAttribute('data-id'), x: r.x, y: r.y, right: r.right, bottom: r.bottom, w: r.width, h: r.height }; })
    .filter((n) => n.right > 8 && n.x < innerWidth - 340 && n.bottom > 70 && n.y < innerHeight - 70 && n.w > 10 && n.h > 10);
  if (ns.length < 2) return { ok: false, 原因: '可视节点不足 2 个', 候选: ns.length };
  // 取离 pane 起点最近的两个节点，选区终点 = 它们包围盒外扩 8px
  const d = (n) => Math.hypot((n.x + n.right) / 2 - 起[0], (n.y + n.bottom) / 2 - 起[1]);
  const s = [...ns].sort((a, b) => d(a) - d(b));
  const two = s.slice(0, 2);
  const 终 = [Math.round(Math.max(two[0].right, two[1].right) + 8), Math.round(Math.max(two[0].bottom, two[1].bottom) + 8)];
  return { ok: true, 起, 终, 目标: two.map((n) => n.id), 命中检查: isPane(起[0], 起[1]) };
});
if (!rec.落点.ok) throw new Error('找不到可用的框选起点：' + JSON.stringify(rec.落点));
if (!rec.落点.命中检查) throw new Error('起点已不在 pane 上（画布动了），拒绝拖');
await p.mouse.move(rec.落点.起[0], rec.落点.起[1]);
await p.mouse.down();
for (let i = 1; i <= 14; i++) {
  await p.mouse.move(Math.round(rec.落点.起[0] + ((rec.落点.终[0] - rec.落点.起[0]) * i) / 14), Math.round(rec.落点.起[1] + ((rec.落点.终[1] - rec.落点.起[1]) * i) / 14));
  await p.waitForTimeout(25);
}
await p.mouse.up();
await p.waitForTimeout(1600);
rec.框选后选中数 = await p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
rec.选中集 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
if (rec.框选后选中数 < 2) throw new Error('框选后不足 2 个节点选中，本轮作废（没有多选工具条可读）：' + JSON.stringify(rec.落点));
await p.mouse.move(1250, 706); await p.waitForTimeout(800);

// —— 四档缩放，每档同时读两个 ⊕
rec.各档 = [];
for (const pct of [26, 50, 22, 100, 26]) {
  const z = await setZoom(p, pct);
  await p.mouse.move(1250, 706); await p.waitForTimeout(700);
  const rd = await 读两个加号();
  rec.各档.push({ 档: pct, 缩放设置: { 回读: z.回读, 实测scale: z.实测scale, 已追平: z.scale已追平 },
    scale: rd.scale, 缩放aria: rd.缩放aria, 选中数: rd.选中数,
    多选加号: rd.多选加号, 单节点加号: rd.单节点加号,
    多选手柄: rd.多选手柄, 多选条: rd.多选条, 多选条内层: rd.多选条内层, 计数项: rd.计数项 });
}

// —— 判定
const 档 = rec.各档;
const 取 = (i, k) => (档[i] && 档[i][k] && 档[i][k][0]) ? 档[i][k][0] : null;
rec.判定 = {};
const 单 = 档.map((d) => ({ 档: d.档, scale: d.scale, w: d.单节点加号[0] ? d.单节点加号[0].w : null, canvas: d.单节点加号[0] ? d.单节点加号[0].w / d.scale : null }));
const 多 = 档.map((d) => ({ 档: d.档, scale: d.scale, w: d.多选加号[0] ? d.多选加号[0].w : null, canvas: d.多选加号[0] && d.scale ? d.多选加号[0].w / d.scale : null }));
rec.判定.单节点加号 = 单;
rec.判定.多选加号 = 多;
rec.判定.单节点canvas读数是否恒定 = (() => {
  const v = 单.map((x) => x.canvas).filter((x) => x !== null);
  return v.length >= 2 ? { 值: v, 极差: Math.round((Math.max(...v) - Math.min(...v)) * 100) / 100 } : null;
})();
rec.判定.多选加号屏上读数是否恒定 = (() => {
  const v = 多.map((x) => x.w).filter((x) => x !== null);
  return v.length >= 2 ? { 值: v, 极差: Math.round((Math.max(...v) - Math.min(...v)) * 100) / 100 } : null;
})();
rec.判定.多选手柄屏上读数 = 档.map((d) => ({ 档: d.档, scale: d.scale, ...(d.多选手柄 || {}) }));
rec.判定.两套契约 = (() => {
  const a = rec.判定.单节点canvas读数是否恒定, b = rec.判定.多选加号屏上读数是否恒定;
  if (!a || !b) return null;
  return { 单节点是canvas恒定: a.极差 <= 2, 多选是屏上恒定: b.极差 <= 0.5, 结论: (a.极差 <= 2 && b.极差 <= 0.5) ? '两套契约' : (a.极差 <= 2 ? '两者都是canvas恒定' : (b.极差 <= 0.5 ? '两者都是屏上恒定' : '都不符合这两个假设')) };
})();
rec.判定.非空守卫 = { 档数: 档.length, 多选加号曾出现: 档.some((d) => d.多选加号.length > 0), 单节点加号曾出现: 档.some((d) => d.单节点加号.length > 0) };

// —— 收尾
await p.keyboard.press('Escape'); await p.waitForTimeout(700);
rec.收尾 = await endState(p, R, 基线);
console.log(JSON.stringify(rec, null, 1));
await b.close();

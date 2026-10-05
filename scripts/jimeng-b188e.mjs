// 批次 188 e 轮：把「⊕ 有两套契约」的**机制**钉死 —— 同一个页面上、同一轮里，
// 分别在**多选态**与**单选态**读两个 ⊕ 的祖先链 / 是否在 `.react-flow__viewport` 内 / `offsetWidth`。
//
// 188d 已经量到的事实：
//   多选态（9 个节点选中）：全文档**只有一个**带 aria^="Create connected node" 的元素，
//     testid `flow-node-multi-selection-source-connection-menu-button`、aria 逐字
//     `Create connected node after selected nodes`、**22/26/50/100% 四档都是 36×36**（屏上恒定）。
//     ⇒ **多选时每节点的 ⊕ 根本不出现**（9 个节点选中，全文档只剩这 1 个）。
//   ⇒ 与批次 135 那句「多选工具条里连接菜单按钮 36×36 四档屏上恒定」**吻合**，
//      但 188d 用的 testid 前缀写错（`^=flow-node-multi-selection-connection-menu-button`，
//      实际是 `flow-node-multi-selection-source-connection-menu-button`）⇒ 那个桶恒空，
//      元素被归进了另一个桶。**读数没错，标签错了** —— 属于「读数异常先怀疑自己的读数」。
//
// 本轮要补的：**为什么**一个恒定一个不恒定。
//   手册 20-reference.md §4.131 已经为**多选手柄**记过机制：
//   「多选手柄挂在 `.react-flow__node-toolbar` 下、**不在 `.react-flow__viewport` 里**（不被 scale 乘）」。
//   ⇒ 预测（先写下来再验）：**多选 ⊕ 走同一条机制**（`closest('.react-flow__viewport')` 为 null、
//   `offsetWidth = 36`），而**每节点 ⊕ 在 viewport 内**（`offsetWidth = 72`、随 scale 缩放）。
import { openCanvas, readers, settle, setZoom, endState } from './jimeng-b135-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '188e', 预测: '多选⊕不在viewport内(不缩放,offsetWidth=36)；每节点⊕在viewport内(缩放,offsetWidth=72)' };
await settle(p, R);
rec.起点 = { 节点数: (await R.ids()).length, 积分: await R.credits(), 缩放: await R.zoom() };
const 基线 = { ids: await R.ids(), testids: await R.testids() };

/** 把「这一类 ⊕」的结构性证据一次性读全：祖先链 / 在不在 viewport / offsetWidth / 屏上尺寸 / scale。 */
const 读 = () => p.evaluate(() => {
  const vp = document.querySelector('.react-flow__viewport');
  const ms = vp ? /scale\(([-\d.]+)\)/.exec(vp.style.transform || '') : null;
  const scale = ms ? parseFloat(ms[1]) : null;
  const 链 = (e) => { const c = []; for (let n = e; n && n !== document.body; n = n.parentElement) c.push(String(n.className || '').split(' ')[0] || n.tagName); return c; };
  const 盒 = (e) => { const r = e.getBoundingClientRect(); return { w: Math.round(r.width * 10) / 10, h: Math.round(r.height * 10) / 10 }; };
  const es = Array.from(document.querySelectorAll('[aria-label^="Create connected node"]'));
  return {
    scale, 缩放aria: (document.querySelector('[data-testid="canvas-zoom-percent"]') || {}).ariaLabel || null,
    选中数: document.querySelectorAll('.react-flow__node.selected').length,
    个数: es.length,
    逐个: es.map((e) => ({ testid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'),
      屏上: 盒(e), offsetWidth: e.offsetWidth, offsetHeight: e.offsetHeight,
      在viewport内: !!e.closest('.react-flow__viewport'),
      在nodeToolbar内: !!e.closest('[data-testid="node-toolbar"]'),
      在多选条内: !!e.closest('[data-testid="selection-context-toolbar-surface"]'),
      祖先链: 链(e) })),
    多选手柄: (() => { const e = document.querySelector('[data-testid="flow-node-multi-selection-source-handle"]');
      return e ? { 屏上: 盒(e), offsetWidth: e.offsetWidth, 在viewport内: !!e.closest('.react-flow__viewport'), 祖先链: 链(e) } : null; })(),
    每节点手柄: (() => { const e = document.querySelector('.react-flow__node.selected [data-testid="flow-node-source-handle"]');
      return e ? { 屏上: 盒(e), offsetWidth: e.offsetWidth, 在viewport内: !!e.closest('.react-flow__viewport'), 祖先链: 链(e) } : null; })(),
  };
});

const 各档 = async (标签) => {
  const out = [];
  for (const pct of [26, 50, 22, 100, 26]) {
    const z = await setZoom(p, pct);
    await p.mouse.move(1250, 706); await p.waitForTimeout(650);
    out.push({ 态: 标签, 档: pct, 回读: z.回读, scale已追平: z.scale已追平, ...(await 读()) });
  }
  return out;
};

// —— ① 多选态
rec.落点 = await p.evaluate(() => {
  const isPane = (x, y) => { const h = document.elementFromPoint(x, y); return !!(h && h.classList && h.classList.contains('react-flow__pane')); };
  let 起 = null;
  for (let y = 80; y <= innerHeight - 80 && !起; y += 6) for (let x = 8; x <= innerWidth - 340; x += 6) if (isPane(x, y)) { 起 = [x, y]; break; }
  if (!起) return { ok: false };
  const ns = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => { const r = n.getBoundingClientRect();
    return { x: r.x, y: r.y, right: r.right, bottom: r.bottom, w: r.width, h: r.height }; })
    .filter((n) => n.right > 8 && n.x < innerWidth - 340 && n.bottom > 70 && n.y < innerHeight - 70 && n.w > 10 && n.h > 10);
  if (ns.length < 2) return { ok: false, 原因: '可视节点不足 2' };
  const d = (n) => Math.hypot((n.x + n.right) / 2 - 起[0], (n.y + n.bottom) / 2 - 起[1]);
  const two = [...ns].sort((a, b) => d(a) - d(b)).slice(0, 2);
  return { ok: true, 起, 终: [Math.round(Math.max(two[0].right, two[1].right) + 8), Math.round(Math.max(two[0].bottom, two[1].bottom) + 8)], 起点仍在pane: isPane(起[0], 起[1]) };
});
if (!rec.落点.ok || !rec.落点.起点仍在pane) throw new Error('多选起点不可用：' + JSON.stringify(rec.落点));
await p.mouse.move(rec.落点.起[0], rec.落点.起[1]); await p.mouse.down();
for (let i = 1; i <= 14; i++) { await p.mouse.move(Math.round(rec.落点.起[0] + ((rec.落点.终[0] - rec.落点.起[0]) * i) / 14), Math.round(rec.落点.起[1] + ((rec.落点.终[1] - rec.落点.起[1]) * i) / 14)); await p.waitForTimeout(25); }
await p.mouse.up(); await p.waitForTimeout(1600);
rec.多选选中数 = await p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
if (rec.多选选中数 < 2) throw new Error('框选后不足 2 个节点，本轮作废');
rec.各档 = await 各档('多选态');

// —— ② 切回单选：Escape 清空，再点一个节点
await p.keyboard.press('Escape'); await p.waitForTimeout(900);
rec.点单选 = await p.evaluate(() => {
  const n = Array.from(document.querySelectorAll('.react-flow__node')).find((x) => { const r = x.getBoundingClientRect();
    return r.right > 8 && r.x < innerWidth - 340 && r.bottom > 70 && r.y < innerHeight - 70 && r.width > 30; });
  if (!n) return null; const r = n.getBoundingClientRect();
  return { id: n.getAttribute('data-id'), 点: [Math.round((r.x + r.right) / 2), Math.round((r.y + r.bottom) / 2)] };
});
if (!rec.点单选) throw new Error('找不到可点的单节点');
await p.mouse.click(rec.点单选.点[0], rec.点单选.点[1]); await p.waitForTimeout(1500);
rec.单选选中数 = await p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
if (rec.单选选中数 !== 1) throw new Error('单选态不干净：选中数 ' + rec.单选选中数);
rec.各档 = rec.各档.concat(await 各档('单选态'));

// —— 判定
const 汇总 = (态) => rec.各档.filter((r) => r.态 === 态).map((r) => ({
  档: r.档, scale: r.scale, 个数: r.个数, testid: r.逐个[0] ? r.逐个[0].testid : null, aria: r.逐个[0] ? r.逐个[0].aria : null,
  屏上: r.逐个[0] ? r.逐个[0].屏上 : null, offsetWidth: r.逐个[0] ? r.逐个[0].offsetWidth : null,
  在viewport内: r.逐个[0] ? r.逐个[0].在viewport内 : null, 在nodeToolbar内: r.逐个[0] ? r.逐个[0].在nodeToolbar内 : null,
  在多选条内: r.逐个[0] ? r.逐个[0].在多选条内 : null, 祖先链: r.逐个[0] ? r.逐个[0].祖先链 : null,
  每节点手柄: r.每节点手柄 ? { 屏上: r.每节点手柄.屏上, offsetWidth: r.每节点手柄.offsetWidth, 在viewport内: r.每节点手柄.在viewport内 } : null,
  多选手柄: r.多选手柄 ? { 屏上: r.多选手柄.屏上, offsetWidth: r.多选手柄.offsetWidth, 在viewport内: r.多选手柄.在viewport内 } : null,
}));
rec.多选态 = 汇总('多选态'); rec.单选态 = 汇总('单选态');
const 屏上恒定 = (arr, k) => { const v = arr.map((x) => x[k]).filter((x) => x !== null && x !== undefined);
  return v.length >= 2 ? { 值: v, 极差: Math.round((Math.max(...v) - Math.min(...v)) * 100) / 100, 恒定: Math.max(...v) - Math.min(...v) <= 0.5 } : null; };
const off恒定 = (arr) => { const v = arr.map((x) => x.offsetWidth).filter((x) => x !== null);
  return v.length >= 2 ? { 值: v, 恒定: new Set(v).size === 1 } : null; };
rec.判定 = {
  多选态: { 屏上是否恒定: 屏上恒定(rec.多选态, null) || (() => { const v = rec.多选态.map((x) => x.屏上 && x.屏上.w).filter((x) => x); return { 值: v, 极差: Math.round((Math.max(...v) - Math.min(...v)) * 100) / 100, 恒定: Math.max(...v) - Math.min(...v) <= 0.5 }; })(), offsetWidth: off恒定(rec.多选态), 全在viewport内: rec.多选态.every((x) => x.在viewport内 === false), 全在nodeToolbar内: rec.多选态.every((x) => x.在nodeToolbar内 === true) },
  单选态: { 屏上是否恒定: (() => { const v = rec.单选态.map((x) => x.屏上 && x.屏上.w).filter((x) => x); return { 值: v, 极差: Math.round((Math.max(...v) - Math.min(...v)) * 100) / 100, 恒定: Math.max(...v) - Math.min(...v) <= 0.5 }; })(), offsetWidth: off恒定(rec.单选态), 全在viewport内: rec.单选态.every((x) => x.在viewport内 === true) },
  多选态每节点加号个数: rec.多选态.map((x) => x.个数),
  单选态每节点加号个数: rec.单选态.map((x) => x.个数),
};
rec.判定.预测是否成立 = (() => {
  const m = rec.判定.多选态, s = rec.判定.单选态;
  const ok1 = m.offsetWidth && m.offsetWidth.恒定 && m.offsetWidth.值[0] === 36 && m.屏上是否恒定.恒定 && m.全在viewport内 === false;
  const ok2 = s.offsetWidth && s.offsetWidth.恒定 && s.offsetWidth.值[0] === 72 && s.屏上是否恒定.恒定 === false && s.全在viewport内 === true;
  return { 多选侧成立: !!ok1, 单选侧成立: !!ok2, 整体: !!(ok1 && ok2) };
})();
rec.判定.非空守卫 = { 多选档数: rec.多选态.length, 单选档数: rec.单选态.length,
  多选侧读到过加号: rec.多选态.some((x) => x.个数 > 0), 单选侧读到过加号: rec.单选态.some((x) => x.个数 > 0),
  多选侧每档都只有一个加号: rec.多选态.every((x) => x.个数 === 1), 单选侧每档都只有一个加号: rec.单选态.every((x) => x.个数 === 1) };

await p.keyboard.press('Escape'); await p.waitForTimeout(700);
rec.收尾 = await endState(p, R, 基线);
console.log(JSON.stringify(rec, null, 1));
await b.close();

// 批次 188 h 轮：只为一件事 —— **多选态那个 ⊕ 到底挂在哪一层**。
//
// 188 d/e 已经量到：多选态全文档只有一个带 aria^="Create connected node" 的元素，
// testid `flow-node-multi-selection-source-connection-menu-button`、`36×36` 四档屏上恒定。
// e 轮顺手记了三个**否定**读数：不在 `.react-flow__viewport` 内、不在 `[data-testid=node-toolbar]` 内、
// 不在 `selection-context-toolbar-surface` 内。
// 手册 20-reference.md §4.131 给**多选手柄**写过机制（「挂在 .react-flow__node-toolbar 下、不被 scale 乘」），
// 但那是**手柄**；⊕ 是不是同一层，**没有证据**，不能顺手类推。
// ⇒ 本轮把 ⊕ 的**完整祖先链**（带每层 testid / class / 在不在 viewport）读出来。
import { openCanvas, readers, settle, endState } from './jimeng-b135-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '188h', 目标: '多选态 ⊕ 的完整祖先链' };
await settle(p, R);
const 基线 = { ids: await R.ids(), testids: await R.testids() };
rec.起点 = { 节点数: 基线.ids.length, 积分: await R.credits(), 缩放: await R.zoom() };

// 框选：按下点必须在 pane 上（立规：不许盲拖）
rec.落点 = await p.evaluate(() => {
  const isPane = (x, y) => { const h = document.elementFromPoint(x, y); return !!(h && h.classList && h.classList.contains('react-flow__pane')); };
  let 起 = null;
  for (let y = 80; y <= innerHeight - 80 && !起; y += 6) for (let x = 8; x <= innerWidth - 340; x += 6) if (isPane(x, y)) { 起 = [x, y]; break; }
  if (!起) return { ok: false, 原因: '找不到 pane 空白点' };
  const ns = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => { const r = n.getBoundingClientRect();
    return { x: r.x, y: r.y, right: r.right, bottom: r.bottom, w: r.width, h: r.height }; })
    .filter((n) => n.right > 8 && n.x < innerWidth - 340 && n.bottom > 70 && n.y < innerHeight - 70 && n.w > 10 && n.h > 10);
  if (ns.length < 2) return { ok: false, 原因: '可视节点不足 2' };
  const d = (n) => Math.hypot((n.x + n.right) / 2 - 起[0], (n.y + n.bottom) / 2 - 起[1]);
  const two = [...ns].sort((a, b) => d(a) - d(b)).slice(0, 2);
  return { ok: true, 起, 终: [Math.round(Math.max(two[0].right, two[1].right) + 8), Math.round(Math.max(two[0].bottom, two[1].bottom) + 8)], 起点仍在pane: isPane(起[0], 起[1]) };
});
if (!rec.落点.ok || !rec.落点.起点仍在pane) throw new Error('框选起点不可用：' + JSON.stringify(rec.落点));
await p.mouse.move(rec.落点.起[0], rec.落点.起[1]); await p.mouse.down();
for (let i = 1; i <= 14; i++) { await p.mouse.move(Math.round(rec.落点.起[0] + ((rec.落点.终[0] - rec.落点.起[0]) * i) / 14), Math.round(rec.落点.起[1] + ((rec.落点.终[1] - rec.落点.起[1]) * i) / 14)); await p.waitForTimeout(25); }
await p.mouse.up(); await p.waitForTimeout(1600);
rec.选中数 = await p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
if (rec.选中数 < 2) throw new Error('框选不足 2 个节点，本轮作废');

rec.读数 = await p.evaluate(() => {
  const vp = document.querySelector('.react-flow__viewport');
  const ms = vp ? /scale\(([-\d.]+)\)/.exec(vp.style.transform || '') : null;
  const scale = ms ? parseFloat(ms[1]) : null;
  const es = Array.from(document.querySelectorAll('[aria-label^="Create connected node"]'));
  const 深读 = (e) => { const cs = getComputedStyle(e); const r = e.getBoundingClientRect();
    return { 名: e.tagName + '.' + String(e.className || '').split(' ').slice(0, 2).join('.'), testid: e.getAttribute('data-testid'),
      屏上: { w: Math.round(r.width * 100) / 100, h: Math.round(r.height * 100) / 100 }, offsetWidth: e.offsetWidth,
      transform: cs.transform, scale属性: cs.scale, zoom: cs.zoom, position: cs.position, pointerEvents: cs.pointerEvents }; };
  const 链 = (e) => { const c = []; for (let n = e; n && n !== document.body; n = n.parentElement) c.push(深读(n)); return c; };
  const 每节点内部加号 = Array.from(document.querySelectorAll('.react-flow__node')).reduce((acc, n) => acc + n.querySelectorAll('[aria-label^="Create connected node"]').length, 0);
  return {
    scale, 缩放aria: (document.querySelector('[data-testid="canvas-zoom-percent"]') || {}).ariaLabel || null,
    选中数: document.querySelectorAll('.react-flow__node.selected').length,
    全文档加号个数: es.length, 每节点内部加号总数: 每节点内部加号,
    多选手柄: (() => { const e = document.querySelector('[data-testid="flow-node-multi-selection-source-handle"]'); return e ? { 层: 深读(e), 链: 链(e) } : null; })(),
    元素: es.map((e) => ({ 层: 深读(e), 链: 链(e) })),
  };
});
// 与多选手柄比：两者是否挂在同一条链上
const 链A = (rec.读数.元素[0] || { 链: [] }).链.map((l) => l.名);
const 链B = rec.读数.多选手柄 ? rec.读数.多选手柄.链.map((l) => l.名) : [];
rec.判定 = {
  读到的加号个数: rec.读数.全文档加号个数, testid: rec.读数.元素[0] ? rec.读数.元素[0].层.testid : null,
  aria: rec.读数.元素[0] ? (rec.读数.元素[0].层.名, null) : null,
  屏上: rec.读数.元素[0] ? rec.读数.元素[0].层.屏上 : null,
  scale属性: rec.读数.元素[0] ? rec.读数.元素[0].层.scale属性 : null,
  在viewport内: (() => { const c = (rec.读数.元素[0] || { 链: [] }).链; return c.some((l) => /viewport/.test(l.名)) ? 'viewport 在链上（需逐层判断是不是同向）' : 'viewport 不在链上'; })(),
  加号链: 链A, 多选手柄链: 链B, 两条链的前缀重合长度: (() => { let i = 0; while (i < 链A.length && i < 链B.length && 链A[i] === 链B[i]) i++; return i; })(),
  每节点内部加号总数: rec.读数.每节点内部加号总数,
  多选手柄的scale属性: rec.读数.多选手柄 ? rec.读数.多选手柄.层.scale属性 : null,
  多选手柄offsetWidth: rec.读数.多选手柄 ? rec.读数.多选手柄.层.offsetWidth : null,
};
rec.判定.非空守卫 = { 读到加号: rec.读数.全文档加号个数 > 0, 读到多选手柄: !!rec.读数.多选手柄, 选中数: rec.读数.选中数 };

await p.keyboard.press('Escape'); await p.waitForTimeout(700);
rec.收尾 = await endState(p, R, 基线);
console.log(JSON.stringify(rec, null, 1));
await b.close();

// 批次 176 b 轮：**每个节点都有一条「描述」通道**（aria-describedby → canvas-node-description-<id>）。
//
// a 轮意外发现：页面上 aria-describedby 的宿主共 **77 个** —— 1 个是画布状态行，
// 另外 **76 个恰好等于节点数**，id 形如 `canvas-node-description-<node id>`。
// 手册至今零覆盖这条通道。
//
// 本轮要回答：
//   ① 76 条描述按**文案模式**能分成几类？（空壳 / 有内容 / 编辑提示 / 选中态）
//   ② 它**会不会随状态变**？（选中 / 未选中、播放中、加载中）
//   ③ 哪些**看得见**、哪些是 sr-only？（描述带面积 = 画布上真的会显示）
//   ④ 描述文本和节点的 `aria-label`（批次 135 起就记的「N resources…」那套）**是不是同一套**
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '176b' };
await settle(p, R);
await p.mouse.move(1250, 10); await p.waitForTimeout(600);

const 全描述 = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
  const id = n.getAttribute('data-id');
  const 宿主 = document.getElementById(`canvas-node-description-${id}`);
  const r = 宿主 ? 宿主.getBoundingClientRect() : null;
  return { id, 类型: (n.className.match(/react-flow__node-(\S+)/) || [])[1] || null,
    标题: (n.querySelector('[data-testid="flow-node-title"]')?.innerText || '').trim().split('\n')[0],
    节点aria: n.getAttribute('aria-label'),
    描述: 宿主 ? (宿主.innerText || '').trim() : null,
    描述有面积: r ? (r.width > 1 && r.height > 1) : null,
    描述盒: r ? [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] : null,
    描述class: 宿主 ? (typeof 宿主.className === 'string' ? 宿主.className.slice(0, 90) : null) : null,
    描述ariaHidden: 宿主 ? 宿主.getAttribute('aria-hidden') : null,
    选中: n.classList.contains('selected') };
}));

rec.基线 = await 全描述();
rec.统计 = {
  节点数: rec.基线.length,
  有描述的: rec.基线.filter((x) => x.描述).length,
  描述有面积的: rec.基线.filter((x) => x.描述有面积).length,
  按类型: rec.基线.reduce((a, x) => { a[x.类型] = (a[x.类型] || 0) + 1; return a; }, {}),
  描述文案分组: Object.entries(rec.基线.reduce((a, x) => { const k = (x.描述 || '(无)').replace(/node_\w+/g, '<id>'); a[k] = (a[k] || 0) + 1; return a; }, {}))
    .map(([文案, n]) => ({ 文案, n })).sort((a, b2) => b2.n - a.n),
  节点aria分组: Object.entries(rec.基线.reduce((a, x) => { const k = (x.节点aria || '(无)').replace(/node_\w+/g, '<id>'); a[k] = (a[k] || 0) + 1; return a; }, {}))
    .map(([文案, n]) => ({ 文案, n })).sort((a, b2) => b2.n - a.n),
};
// 抽样：每种类型取 1 条，逐字对比「节点 aria」与「描述」两列
rec.抽样 = {};
for (const t of Object.keys(rec.统计.按类型)) {
  const s = rec.基线.find((x) => x.类型 === t);
  if (s) rec.抽样[t] = { id: s.id, 标题: s.标题, 节点aria: s.节点aria, 描述: s.描述, 描述有面积: s.描述有面积, 描述class: s.描述class, 描述ariaHidden: s.描述ariaHidden };
}

// ── ② 选中一个节点，看描述变不变
const 目标 = rec.基线.find((x) => x.类型 === 'video') || rec.基线[0];
rec.状态变化 = { 目标: { id: 目标.id, 类型: 目标.类型, 标题: 目标.标题 } };
await p.evaluate((i) => document.querySelector(`.react-flow__node[data-id="${i}"] [data-testid="flow-node-title"]`)
  ?.scrollIntoView({ block: 'center', inline: 'center' }), 目标.id);
await p.waitForTimeout(900);
const pt = await p.evaluate((i) => { const t = document.querySelector(`.react-flow__node[data-id="${i}"] [data-testid="flow-node-title"]`);
  const r = t.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, 目标.id);
await p.mouse.click(pt[0], pt[1]); await p.waitForTimeout(1200);
rec.状态变化.选中后 = await p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const h = document.getElementById(`canvas-node-description-${i}`);
  return { 节点aria: n?.getAttribute('aria-label'), 描述: h ? (h.innerText || '').trim() : null,
    描述有面积: h ? (() => { const r = h.getBoundingClientRect(); return r.width > 1 && r.height > 1; })() : null,
    选中: n?.classList.contains('selected') };
}, 目标.id);
await p.mouse.click(640, 690); await p.waitForTimeout(1000);
rec.状态变化.取消选中后 = await p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const h = document.getElementById(`canvas-node-description-${i}`);
  return { 节点aria: n?.getAttribute('aria-label'), 描述: h ? (h.innerText || '').trim() : null, 选中: n?.classList.contains('selected') };
}, 目标.id);
await p.keyboard.press('Escape'); await p.waitForTimeout(600);

rec.收尾 = { 状态行: await R.status(), 积分: await R.credits(), 缩放: await R.zoom(),
  选中: await p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length) };
console.log(JSON.stringify(rec, null, 1));
process.exit(0);

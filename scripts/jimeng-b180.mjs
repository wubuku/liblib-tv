// 批次 180：把「七种描述文案」**用 id 重新出一遍**，并做成**类型 × 文案的交叉表**。
//
// 批次 179 查出批次 176 的错误根源：**先按文案分组、再凭印象把类型补上去**。
// 而实测这两件事是**独立**的 —— 分组只告诉你「有几种文案」，不告诉你「哪种类型用哪种」。
// ⇒ 本批**逐个节点**读：id、类型 class、标题、描述，一次性建成交叉表。
//
// ⛔ 纯只读。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '180' };
await settle(p, R);
await p.mouse.move(1250, 10); await p.waitForTimeout(600);

const 全部 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
  const id = n.getAttribute('data-id');
  const h = document.getElementById(`canvas-node-description-${id}`);
  const r = h ? h.getBoundingClientRect() : null;
  const t = n.querySelector('[data-testid="flow-node-title"]');
  return {
    id,
    类型class: (n.className.match(/react-flow__node-(\S+)/) || [])[1] || null,
    标题: t ? (t.innerText || '').trim().split('\n')[0] : null,
    有描述宿主: !!h,
    描述: h ? (h.innerText || '').trim() : null,
    描述有面积: r ? (r.width > 1 && r.height > 1) : null,
    描述盒: r ? [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] : null,
    节点aria: n.getAttribute('aria-label'),
    // 🔴 关键：把「描述元素引给谁」也记下来（aria-describedby 的真实指向）
    描述by: n.getAttribute('aria-describedby'),
  };
}));
rec.节点数 = 全部.length;
rec.有宿主 = 全部.filter((x) => x.有描述宿主).length;
rec.描述by与命名规律一致 = 全部.filter((x) => x.描述by === `canvas-node-description-${x.id}`).length;
rec.描述by异常 = 全部.filter((x) => x.描述by && x.描述by !== `canvas-node-description-${x.id}`).map((x) => ({ id: x.id, 描述by: x.描述by }));

// ── 交叉表：类型 × 描述（**这是 176 缺的那一步**）
const 交叉 = {};
for (const x of 全部) {
  const k = x.类型class || '(无类型类)';
  (交叉[k] ||= { 节点数: 0, 描述分布: new Map(), 样例: [] });
  交叉[k].节点数++;
  const d = x.描述 === null ? '(没有宿主)' : (x.描述 === '' ? '(宿主存在但 innerText 为空)' : x.描述);
  交叉[k].描述分布.set(d, (交叉[k].描述分布.get(d) || 0) + 1);
  if (交叉[k].样例.length < 2) 交叉[k].样例.push({ id: x.id, 标题: x.标题, 描述: x.描述, 有面积: x.描述有面积 });
}
rec.交叉表 = Object.entries(交叉).map(([类型, v]) => ({
  类型, 节点数: v.节点数,
  描述种类: v.描述分布.size,
  描述分布: [...v.描述分布.entries()].map(([文案, n]) => ({ 文案, n })),
  样例: v.样例,
}));

// ── 「有面积」的那些（有面积 ≠ 有文字，这一对要一起记）
rec.有面积的描述 = 全部.filter((x) => x.描述有面积).map((x) => ({ id: x.id, 类型: x.类型class, 标题: x.标题, 描述: x.描述, 描述盒: x.描述盒 }));
// ── 「没有宿主」的
rec.没有宿主的 = 全部.filter((x) => !x.有描述宿主).map((x) => ({ id: x.id, 类型: x.类型class, 标题: x.标题 }));
// ── 描述文本里带「.」句号的那些，拆成句段看模板
rec.模板拆解 = [...new Set(全部.map((x) => x.描述).filter(Boolean))].map((d) => ({
  逐字: d, 句段: d.split('. '), 有NotSelected尾: /Not selected\.$/.test(d), 有Selected尾: /(?<!Not )Selected\.$/.test(d) }));

rec.收尾 = { 状态行: await R.status(), 积分: await R.credits(), 缩放: await R.zoom() };
console.log(JSON.stringify(rec, null, 1));
process.exit(0);

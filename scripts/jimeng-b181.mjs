// 批次 181：把 180 的「归因」推到**组件层** —— 读每种类型那条描述元素的
// **class 指纹 + 祖先链 + 在 DOM 里的位置**，看它们是不是**同一个组件**。
//
// 180 已归因出：「`Current preview: 暂无X`」是**音视频共用**，
// 「三个计数器」只属于 `external`（导演台），`image` 是空，`text` 是正文。
// 但**为什么**不同，要看**承载它们的元素**是不是同一个组件。
// ⇒ 判据：① 元素自己的 class 串；② 逐层祖先链（tag + data-testid + role）；
//        ③ 宿主在 `aria-describedby` 引用之外还挂在谁下面。
//
// ⛔ 纯只读。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '181' };
await settle(p, R);
await p.mouse.move(1250, 10); await p.waitForTimeout(600);

const 指纹 = await p.evaluate(() => {
  const out = [];
  for (const n of document.querySelectorAll('.react-flow__node')) {
    const id = n.getAttribute('data-id');
    const h = document.getElementById(`canvas-node-description-${id}`);
    if (!h) continue;
    const 类型 = (n.className.match(/react-flow__node-(\S+)/) || [])[1] || null;
    const 链 = [];
    for (let x = h; x && x !== document.body; x = x.parentElement) {
      链.push(x.tagName.toLowerCase() +
        (x.dataset?.testid ? `[testid=${x.dataset.testid}]` : '') +
        (x.getAttribute('role') ? `[role=${x.getAttribute('role')}]` : '') +
        (typeof x.className === 'string' && x.className.trim()
          ? '.' + x.className.trim().split(/\s+/).slice(0, 6).join('.') : ''));
      if (链.length >= 6) break;
    }
    const r = h.getBoundingClientRect();
    // 宿主在 aria-describedby 之外**还被谁描述**？以及它在节点内的相对位置
    const 节点盒 = n.getBoundingClientRect();
    out.push({
      id, 类型,
      描述: (h.innerText || '').trim(),
      宿主标签: h.tagName.toLowerCase(),
      宿主class: typeof h.className === 'string' ? h.className : null,
      宿主属性: Array.from(h.attributes).map((a) => `${a.name}="${a.value.slice(0, 40)}"`),
      祖先链: 链,
      在节点内的位置: 节点盒.width > 0
        ? { x比: Math.round(((r.x - 节点盒.x) / 节点盒.width) * 100),
            y比: Math.round(((r.y - 节点盒.y) / 节点盒.height) * 100) } : null,
      宿主盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      节点盒: [Math.round(节点盒.x), Math.round(节点盒.y), Math.round(节点盒.width), Math.round(节点盒.height)],
    });
  }
  return out;
});
rec.总数 = 指纹.length;
// 每种类型取 1 个，打出指纹
rec.按类型 = {};
for (const x of 指纹) {
  if (rec.按类型[x.类型]) continue;
  rec.按类型[x.类型] = { 节点数: 指纹.filter((y) => y.类型 === x.类型).length, 样本: x };
}
// 🔴 关键：同类型的多个节点，**指纹是否完全一致**？（不一致就说明它是动态拼的）
rec.同类型指纹一致性 = {};
for (const [类型, 们] of Object.entries(
  指纹.reduce((a, x) => { (a[x.类型] ||= []).push(x); return a; }, {}))) {
  const 键们 = [...new Set(们.map((x) => x.祖先链.join(' > ') + ' || class=' + x.宿主class))];
  rec.同类型指纹一致性[类型] = { 节点数: 们.length, 不同指纹数: 键们.length, 指纹们: 键们 };
}
rec.收尾 = { 状态行: await R.status(), 积分: await R.credits(), 缩放: await R.zoom() };
console.log(JSON.stringify(rec, null, 1));
process.exit(0);

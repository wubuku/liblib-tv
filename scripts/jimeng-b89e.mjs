// 批次 89 · E：`Add tags` 三种屏上尺寸的**机制**。
//
// d 轮已排除「按节点类型分」：`audio` 同时出现在 28×28 / 29×29 / 24×24 三组里。
// 三组的 **inline style、class、aria 逐字相同**，唯一可疑的是那一行：
//     scale: var(--octo-canvas-node-chrome-counter-scale, 1)
// 这个变量**不在元素自己的 style 里**，说明它定义在**某个祖先**上。
// 本页批次 88 已钉过它 = 1/scale —— 但那是在**某一个节点**上量的。
//
// ⇒ 可证伪预测 **P1e**：`--octo-canvas-node-chrome-counter-scale` 是**逐节点不同**的，
//   且三组分别等于 1/0.6、别的值… 屏上尺寸 = 24 × 视口 scale × 该变量。
//   若三组的变量**都等于 1/0.6**，那尺寸差就不是这个变量造成的（预测不成立），
//   得往 transform 链上找。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };

out.rows = await p.evaluate(() => {
  const rows = [];
  for (const n of document.querySelectorAll('.react-flow__node')) {
    const t = n.querySelector('[data-testid="flow-node-selected-tag"]');
    if (!t) continue;
    const r = t.getBoundingClientRect();
    // 沿祖先链找变量的**定义处**（哪个元素的 style 里真的写了它）
    let owner = null, chain = [];
    for (let e = t; e && e !== document.documentElement; e = e.parentElement) {
      const s = e.getAttribute('style') || '';
      const cs = getComputedStyle(e);
      const has = /--octo-canvas-node-chrome-counter-scale/.test(s);
      if (has && owner === null) owner = { tag: e.tagName, cls: String(e.className || '').slice(0, 60), style: s.slice(0, 220) };
      chain.push({ tag: e.tagName, tid: e.getAttribute('data-testid'), transform: (cs.transform || '').slice(0, 60),
        counterVar: cs.getPropertyValue('--octo-canvas-node-chrome-counter-scale').trim() });
      if (chain.length > 6) break;
    }
    const title = n.querySelector('[data-testid="flow-node-title"]');
    const tr = title ? title.getBoundingClientRect() : null;
    rows.push({ id: n.getAttribute('data-id'), aria: (n.getAttribute('aria-label') || '').slice(0, 20),
      tagBox: `${Math.round(r.width)}×${Math.round(r.height)}`,
      titleBox: tr ? `${Math.round(tr.width)}×${Math.round(tr.height)}` : null,
      nodeBox: (() => { const q = n.getBoundingClientRect(); return `${Math.round(q.width)}×${Math.round(q.height)}`; })(),
      ownCounter: getComputedStyle(t).getPropertyValue('--octo-canvas-node-chrome-counter-scale').trim(),
      varOwner: owner, chain });
  }
  return rows;
});

const groups = {};
for (const r of out.rows) (groups[r.tagBox] = groups[r.tagBox] || []).push(r);
out.groups = Object.keys(groups).map((k) => ({ box: k, n: groups[k].length,
  ownCounter: [...new Set(groups[k].map((x) => x.ownCounter))],
  varOwnerCls: [...new Set(groups[k].map((x) => (x.varOwner ? x.varOwner.cls : '(未定义)')))] }));

log('══ 屏上尺寸 × 该元素上解析到的 counter-scale 变量：');
for (const g of out.groups) {
  log(`  ${g.box} ×${g.n}｜ownCounter=${JSON.stringify(g.ownCounter)}`);
  for (const c of g.varOwnerCls) log(`        变量定义于 class=${c}`);
}
log('══ 逐节点（前 6 个）：');
for (const r of out.rows.slice(0, 6)) {
  log(`  ${r.aria} tag=${r.tagBox} title=${r.titleBox} node=${r.nodeBox} ownCounter=${r.ownCounter}`);
  for (const c of r.chain) log(`        ${c.tag}${c.tid ? '[' + c.tid + ']' : ''} transform=${c.transform || '(无)'} counter=${c.counterVar || '(未定义)'}`);
}
writeFileSync(new URL('./_tmp-b89e.json', import.meta.url), JSON.stringify(out, null, 1));
log('已写 _tmp-b89e.json');
await b.close();

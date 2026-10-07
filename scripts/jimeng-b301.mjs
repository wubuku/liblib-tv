/**
 * 批次 301 · 「compound 多出来的那 ≈205px（在节点下方）」到底是什么？
 *
 * 🔴 起意：批次 300 用两点判据钉死 `flow-node-title` 是屏幕固定装饰，
 *    🔴 **并算出了它只占 `compound` 多出来部分的 `≈15.6%`**（`32 / 205`）。
 *    ⇒ 📌 本批不去猜，**直接把 DOM 里那一块区域的东西全列出来**。
 *
 * 📌 区域怎么定（**写死，不事后调**）：
 *   纵向 `y ∈ [48, 640]` —— `48` 是实测的标题顶，`640` 是安全区底；
 *   横向 `x ∈ [100, 780]` —— `100 = 中心440 − safeW/2(340)`，`780 = 中心440 + 340`。
 *   📌 列出这个带子里**所有非空矩形**元素，标出「在节点内 / 节点上方 / 节点下方 / 与节点横向重叠」。
 *
 * 📌 要回答的那一问（**一句话可判**）：
 *   「节点下方那 `205px` 里，有没有一整块**属于这个节点**的元素？」
 *   有 ⇒ 外框在下方，标题不是主体；没有 ⇒ 🔴 那 `205px` 不是 DOM 里的任何东西
 *        ⇒ **它只能是「算出来但没渲染」的量**（那正是批次 298 说的定点迭代的产物）。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const STATE = `${process.env.HOME}/.jimeng-automation/state.json`;
const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b301.json';
const 目标 = { w: 1212, kind: '音频', 名: '音频 1' };

const b = await chromium.launch({ headless: true });
const ctx = await b.newContext({ storageState: STATE, viewport: { width: 目标.w, height: 720 } });
const p = await ctx.newPage();
await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
await p.waitForSelector('.react-flow__node', { timeout: 60000 });
await p.waitForTimeout(6000);

for (let i = 0; i < 13; i++) { await p.keyboard.press('Meta+Equal'); await p.waitForTimeout(380); }
await p.waitForTimeout(1200);

const ariaWant = `${目标.kind} node: ${目标.名}`;
const 节点id = await p.evaluate((aria) => {
  const e = Array.from(document.querySelectorAll('.react-flow__node[data-id]')).find((x) => x.getAttribute('aria-label') === aria);
  return e ? e.dataset.id : null;
}, ariaWant);
if (!节点id) throw new Error(`找不到 ${ariaWant}`);

const 钮 = await p.evaluate(() => {
  const x = document.querySelector('button[aria-label="搜索"]');
  const r = x.getBoundingClientRect();
  return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
});
await p.mouse.click(钮.x, 钮.y);
await p.waitForTimeout(1600);
await p.evaluate(() => { const i = document.querySelector('[data-testid="canvas-search-panel"] input'); if (i) { i.focus(); i.select(); } });
await p.keyboard.type(目标.名, { delay: 80 });
await p.waitForTimeout(2000);
const 行 = await p.evaluate((nid) => {
  const e = document.querySelector(`[data-testid="canvas-search-result-node_${nid.replace(/^node_/, '')}"]`);
  if (!e) return null;
  e.scrollIntoView({ block: 'center' });
  const r = e.getBoundingClientRect();
  return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) };
}, 节点id);
await p.mouse.click(行.x, 行.y);
await p.waitForTimeout(5000);

const 结果 = await p.evaluate((nid) => {
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  const node = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  const nr = node.getBoundingClientRect();
  const BAND = { x0: 100, x1: 780, y0: 48, y1: 640 };
  const inBand = (r) => r.width > 0 && r.height > 0 && r.right > BAND.x0 && r.left < BAND.x1 && r.bottom > BAND.y0 && r.top < BAND.y1;
  const all = Array.from(document.querySelectorAll('*'));
  const 命中 = [];
  const seen = new Set();
  for (const e of all) {
    const r = e.getBoundingClientRect();
    if (!inBand(r)) continue;
    const key = `${Math.round(r.x)},${Math.round(r.y)},${Math.round(r.width)},${Math.round(r.height)}|${e.tagName}`;
    if (seen.has(key)) continue;
    seen.add(key);
    const tid = e.getAttribute('data-testid');
    const cn = typeof e.className === 'string' ? e.className : '';
    const 在节点内 = node.contains(e);
    命中.push({
      testid: tid || null,
      tag: e.tagName,
      className: cn.slice(0, 70),
      rect: [+r.x.toFixed(1), +r.y.toFixed(1), +r.width.toFixed(1), +r.height.toFixed(1)],
      在节点内,
      与节点上下关系: r.bottom <= nr.top + 0.5 ? '节点上方' : (r.top >= nr.bottom - 0.5 ? '节点下方' : '与节点竖直重叠'),
    });
  }
  // 节点子树里最高的那个底边
  let 子树最低 = -1e9; let 子树最高 = 1e9; let 命中子树 = null;
  for (const e of node.querySelectorAll('*')) {
    const r = e.getBoundingClientRect();
    if (r.height > 0) { if (r.bottom > 子树最低) { 子树最低 = r.bottom; 命中子树 = e.getAttribute('data-testid') || e.className.toString().slice(0, 50) || e.tagName; } if (r.top < 子树最高) 子树最高 = r.top; }
  }
  return {
    scale: m ? Number(m[1]) : null,
    节点rect: [+nr.x.toFixed(2), +nr.y.toFixed(2), +nr.width.toFixed(2), +nr.height.toFixed(2)],
    节点id: nid,
    节点子树最高: 子树最高 === 1e9 ? null : +子树最高.toFixed(2),
    节点子树最低: 子树最低 === -1e9 ? null : +子树最低.toFixed(2),
    节点子树最低元素: 命中子树,
    BAND,
    命中,
  };
}, 节点id);

结果.节点下方空间 = +(640 - (结果.节点rect[1] + 结果.节点rect[3])).toFixed(2);
结果.节点上方空间 = +(结果.节点rect[1] - 48).toFixed(2);
结果.子树伸到节点下方 = 结果.节点子树最低 !== null && 结果.节点子树最低 > 结果.节点rect[1] + 结果.节点rect[3] + 0.5;

console.log('scale =', 结果.scale);
console.log('节点屏盒 =', 结果.节点rect, '→ 顶', 结果.节点rect[1], '底', +(结果.节点rect[1] + 结果.节点rect[3]).toFixed(2));
console.log('节点子树：最高 y =', 结果.节点子树最高, '｜最低 y =', 结果.节点子树最低, '（', 结果.节点子树最低元素, '）');
console.log('节点上方空间 =', 结果.节点上方空间, '｜节点下方空间 =', 结果.节点下方空间);
console.log('🔴 子树有没有伸到节点下方？', 结果.子树伸到节点下方);
console.log('\n带子内元素（y ∈ [48,640]、x ∈ [100,780]），按 y 排序：');
const 排序 = [...结果.命中].sort((a, c) => a.rect[1] - c.rect[1]);
for (const h of 排序) {
  console.log(`  y=${String(h.rect[1]).padStart(7)} h=${String(h.rect[3]).padStart(7)} x=${String(h.rect[0]).padStart(7)} w=${String(h.rect[2]).padStart(7)} ${h.与节点上下关系.padEnd(8)} ${h.在节点内 ? '节点内' : '节点外'} ${h.testid || h.className || h.tag}`);
}
fs.writeFileSync(OUT, JSON.stringify(结果, null, 1));
console.log('\n写入', OUT);

const pz = await ctx.newPage();
try {
  await pz.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await pz.waitForSelector('.react-flow__node', { timeout: 60000 });
  await pz.waitForTimeout(6000);
  console.log('末态独立复查：', JSON.stringify(await pz.evaluate(() => ({
    节点数: document.querySelectorAll('.react-flow__node').length,
    状态行: (document.body.innerText.match(/\d+ nodes, \d+ edges, \d+ selected[^\n]*/) || [])[0] || null,
    积分: (document.querySelector('[data-testid="canvas-commerce-entry"]') || {}).textContent || null,
  }))));
} finally { try { await pz.close(); } catch (e) { /* 忽略 */ } }

await ctx.close();
await b.close();
process.exit(0);
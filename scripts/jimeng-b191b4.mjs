// 批次 191 b4 轮：b3 打出**两个不同的吸引子**（0.5 与 0.626），而且是**同一个节点**（node_236ctpehgg）
//   起点 26/50  → 0.5      屏上 160×284
//   起点 80/100/200 → 0.626 屏上 200×356
// ⇒ 目标缩放**不是节点的函数，是起点的函数** ⇒ 它是一个**分支**，不是一条拟合公式。
//
// 🔑 b4 只找**翻转阈值**：在 50 与 80 之间逐档扫，找到「终点从 0.5 变成 0.626」的那个点。
//   顺带把 viewport 的**原始 transform 字符串**读出来 —— 0.626 这个数太不像人手写的常量，
//   可能是某个 fit 计算的落点（那就该按「算出来的」记，而不是按「预设档」记）。
import fs from 'node:fs';
import { openCanvas, readers, setZoom, settle } from './jimeng-b135-lib.mjs';

const OUT = '/tmp/b191b4.json';
const 记 = { 轮次: 'b191b4', 问题: '吸引子从 0.5 翻到 0.626 的阈值在哪', 档位表: [], 收尾: null };
const save = () => fs.writeFileSync(OUT, JSON.stringify(记, null, 1));

const 读缩放 = (p) => p.evaluate(() => {
  const e = document.querySelector('[data-testid="canvas-zoom-percent"]');
  const vp = document.querySelector('.react-flow__viewport');
  const t = (vp && vp.style.transform) || '';
  return { aria: e ? e.getAttribute('aria-label') : null, 原始transform: t,
    实测scale: (function () { const m = /scale\(([-\d.]+)\)/.exec(t); return m ? Math.round(parseFloat(m[1]) * 1000) / 1000 : null; })() };
});
const 输入框 = 'input[aria-label="搜索"]';
async function 开面板(p) {
  const btn = await p.evaluate(() => { const a = Array.from(document.querySelectorAll('BUTTON[data-testid="canvas-panel-launcher"]'))
    .find((x) => (x.getAttribute('aria-label') || '') === '搜索'); if (!a) return null;
    const r = a.getBoundingClientRect(); return { expanded: a.getAttribute('aria-expanded'), 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; });
  if (btn && btn.expanded !== 'true') { await p.mouse.click(btn.中心[0], btn.中心[1]); await p.waitForTimeout(1100); }
}
async function 取结果行(p, 词) {
  let 点 = await p.evaluate((sel) => { const i = document.querySelector(sel); if (!i) return null;
    const r = i.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, 输入框);
  if (!点) { await 开面板(p); 点 = await p.evaluate((sel) => { const i = document.querySelector(sel); if (!i) return null;
    const r = i.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, 输入框); }
  if (!点) return [];
  await p.mouse.click(点[0], 点[1]); await p.waitForTimeout(300);
  await p.keyboard.press('Meta+a'); await p.keyboard.type(词); await p.waitForTimeout(1500);
  return p.evaluate(() => Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-"]')).map((b) => {
    const r = b.getBoundingClientRect();
    return { id: (b.getAttribute('data-testid') || '').replace('canvas-search-result-', ''), aria: b.getAttribute('aria-label'),
      中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; }));
}

const { b, p } = await openCanvas();
const R = readers(p);
await settle(p, R);
const 基线 = { ids: await R.ids(), credits: await R.credits() };

for (const 起点 of [55, 60, 62, 65, 70, 75]) {
  await setZoom(p, 起点); await p.waitForTimeout(600);
  await p.keyboard.press('Escape'); await p.waitForTimeout(400);
  const 前 = await 读缩放(p);
  const 结果 = await 取结果行(p, '视频');
  if (!结果.length) { 记.档位表.push({ 起点, 无效: true }); save(); continue; }
  const 目标 = 结果[0];
  await p.mouse.click(目标.中心[0], 目标.中心[1]);
  const 选中 = await R.selCount();
  await p.waitForTimeout(2200);
  const 末 = await 读缩放(p);
  const 节点屏上 = await p.evaluate((nid) => { const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`); if (!n) return null;
    const r = n.getBoundingClientRect(); return { 左: Math.round(r.x), 上: Math.round(r.y), 宽: Math.round(r.width), 高: Math.round(r.height) }; }, 目标.id);
  记.档位表.push({ 起点, 目标id: 目标.id, 前: 前.实测scale, 前aria: 前.aria, 选中, 无效: 选中 !== 1,
    末态: 末, 节点屏上, 判定: { 旧: 前.实测scale, 新: 末.实测scale, 变化: 前.实测scale !== 末.实测scale } });
  console.log(`起点${起点}% (实读 ${前.实测scale}) → 末 ${末.实测scale}  aria ${末.aria}  节点屏上 ${JSON.stringify(节点屏上 && [节点屏上.宽, 节点屏上.高])}`);
  await p.keyboard.press('Escape'); await p.waitForTimeout(400);
  save();
}
const 有效 = 记.档位表.filter((x) => !x.无效);
记.小结 = { 逐档: 有效.map((x) => ({ 起: x.前, 终: x.末态.实测scale, 屏上: x.节点屏上 && [x.节点屏上.宽, x.节点屏上.高] })),
  终点集合: [...new Set(有效.map((x) => x.末态.实测scale))],
  原始transform样本: 有效.map((x) => x.末态.原始transform) };
console.log('小结 =', JSON.stringify(记.小结, null, 1));
const ids = await R.ids();
记.收尾 = { 状态行: await R.status(), credits: await R.credits(), 节点数: ids.length, 基线节点数: 基线.ids.length,
  残留: ids.filter((x) => !基线.ids.includes(x)), 丢失: 基线.ids.filter((x) => !ids.includes(x)) };
await setZoom(p, 26); await p.waitForTimeout(500);
记.收尾.zoom = await R.zoom();
save();
console.log('收尾 =', JSON.stringify(记.收尾));
await b.close();

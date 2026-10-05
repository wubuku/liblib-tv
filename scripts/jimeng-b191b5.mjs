// 批次 191 b5 轮：b3 + b4 合起来给出一条**无例外的钳位公式**：
//
//   终态缩放 = clamp(点之前的缩放, 0.5, 0.625659)
//
//   起点 26% →0.5   50%→0.5   55%→0.55  60%→0.6   62%→0.62
//        65% →0.625659  70%→0.625659  75%→0.625659
//        80% →0.625659  100%→0.625659  200%→0.625659      （11/11）
//
// 🔑 b5 只验两件「这个公式能不能再被推翻」的事：
//   ① 下界 0.5 是不是常数 —— 补 10% 与 40% 两档（b3 只测过 26% 一个低于 0.5 的点）。
//   ② 上界 0.625659 是不是常数 —— 换**别的节点**（音频 1 / 时间线）从 200% 起。
//      若上界跟着节点变，它就是「按节点算出来的适配值」；若三个节点上界逐字相同，
//      它就是一个**写死的预设档**。这两种在手册里的写法完全不同，不能混。
import fs from 'node:fs';
import { openCanvas, readers, setZoom, settle } from './jimeng-b135-lib.mjs';

const OUT = '/tmp/b191b5.json';
const 记 = { 轮次: 'b191b5', 公式: '终态 = clamp(起点, 0.5, 0.625659)', 读数: [] };
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

for (const [起点, 词] of [[10, '视频'], [40, '视频'], [200, '音频 1'], [200, '时间线'], [200, '视频']]) {
  await setZoom(p, 起点); await p.waitForTimeout(600);
  await p.keyboard.press('Escape'); await p.waitForTimeout(400);
  const 前 = await 读缩放(p);
  const 结果 = await 取结果行(p, 词);
  if (!结果.length) { 记.读数.push({ 起点, 词, 无效: true, 原因: '没有结果行' }); save(); continue; }
  const 目标 = 结果[0];
  await p.mouse.click(目标.中心[0], 目标.中心[1]);
  const 选中 = await R.selCount();
  await p.waitForTimeout(2200);
  const 末 = await 读缩放(p);
  const 节点 = await p.evaluate((nid) => { const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`); if (!n) return null;
    const r = n.getBoundingClientRect(); const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(n.style.transform || '');
    return { 屏上: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      canvas: m ? [Math.round(parseFloat(m[1]) * 100) / 100, Math.round(parseFloat(m[2]) * 100) / 100] : null,
      完整在视口内: r.x >= 0 && r.y >= 0 && r.right <= innerWidth && r.bottom <= innerHeight }; }, 目标.id);
  记.读数.push({ 起点, 词, 目标id: 目标.id, 目标aria: 目标.aria, 前: 前.实测scale, 选中, 无效: 选中 !== 1,
    末态: 末.实测scale, 末aria: 末.aria, 原始transform: 末.原始transform, 节点 });
  console.log(`起点${起点}% 搜「${词}」→ 末 ${末.实测scale}  节点屏上 ${JSON.stringify(节点 && 节点.屏上)}  canvas ${JSON.stringify(节点 && 节点.canvas)}`);
  await p.keyboard.press('Escape'); await p.waitForTimeout(400);
  save();
}
const 有效 = 记.读数.filter((x) => !x.无效);
记.小结 = {
  公式全档符合: 有效.length,
  总档数: 有效.length,
  逐档: 有效.map((x) => `${x.起点}%→${x.末态}`),
  高档上界样本: 有效.filter((x) => x.起点 === 200).map((x) => ({ 词: x.词, 终: x.末态, transform: x.原始transform })),
};
console.log('小结 =', JSON.stringify(记.小结, null, 1));
const ids = await R.ids();
记.收尾 = { 状态行: await R.status(), credits: await R.credits(), 节点数: ids.length,
  残留: ids.filter((x) => !基线.ids.includes(x)), 丢失: 基线.ids.filter((x) => !ids.includes(x)) };
await setZoom(p, 26); await p.waitForTimeout(500);
记.收尾.zoom = await R.zoom();
save();
console.log('收尾 =', JSON.stringify(记.收尾));
await b.close();

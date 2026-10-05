// 批次 191 b3 轮：b2 已经把「点搜索结果行 ⇒ 缩放变成 0.5」测实了（三类节点、屏上尺寸差 5 倍，全是 0.5，
// 且 0~302ms 之间的读数是 0.28/0.344/0.379 这类**中间值** ⇒ 动画，终点恒为 0.5）。
//
// 🔑 b3 只问一个问题：**50% 是「固定目标缩放」还是「按节点算出来的适配值」？**
//   分辨办法：从**不同起始档**（26 / 50 / 80 / 100 / 200）各点一次同一个结果行。
//     · 终点全是 0.5            ⇒ 它是**写死的目标缩放**（不管从哪来都去 50%）
//     · 终点随起点变            ⇒ 它是**算出来的**（可能带钳位）
//   顺带量「点完之后那个节点在屏幕的哪个位置」—— 若三档落点逐字相同，就是**写死的落点**。
import fs from 'node:fs';
import { openCanvas, readers, setZoom, settle } from './jimeng-b135-lib.mjs';

const OUT = '/tmp/b191b3.json';
const 记 = { 轮次: 'b191b3', 问题: '50% 是写死的目标缩放，还是按节点算出来的适配值', 档位表: [], 收尾: null };
const save = () => fs.writeFileSync(OUT, JSON.stringify(记, null, 1));

const 读缩放 = (p) => p.evaluate(() => {
  const e = document.querySelector('[data-testid="canvas-zoom-percent"]');
  const vp = document.querySelector('.react-flow__viewport');
  const t = (vp && vp.style.transform) || '';
  const ms = /scale\(([-\d.]+)\)/.exec(t);
  const mt = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(t);
  return { aria: e ? e.getAttribute('aria-label') : null,
    实测scale: ms ? Math.round(parseFloat(ms[1]) * 1000) / 1000 : null,
    平移: mt ? [Math.round(parseFloat(mt[1]) * 10) / 10, Math.round(parseFloat(mt[2]) * 10) / 10] : null };
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

for (const 起点 of [26, 50, 80, 100, 200]) {
  const 归位读 = await setZoom(p, 起点);
  await p.waitForTimeout(700);
  await p.keyboard.press('Escape'); await p.waitForTimeout(500);
  const 前 = await 读缩放(p);
  const 结果 = await 取结果行(p, '视频');
  if (!结果.length) { 记.档位表.push({ 起点, 无效: true, 原因: '没有结果行' }); save(); continue; }
  const 目标 = 结果[0];
  await p.mouse.click(目标.中心[0], 目标.中心[1]);
  const 选中 = await R.selCount();
  // 0 / 150 / 400 / 1200 / 2500 ms 连读
  const 点 = []; const t0 = Date.now();
  for (const 计划 of [0, 150, 400, 1200, 2500]) { const 等 = 计划 - (Date.now() - t0); if (等 > 0) await p.waitForTimeout(等);
    点.push({ ms: Date.now() - t0, ...(await 读缩放(p)) }); }
  const 末 = 点[点.length - 1];
  const 节点屏上 = await p.evaluate((nid) => { const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`); if (!n) return null;
    const r = n.getBoundingClientRect();
    return { 左: Math.round(r.x), 上: Math.round(r.y), 宽: Math.round(r.width), 高: Math.round(r.height),
      完整在视口内: r.x >= 0 && r.y >= 0 && r.right <= innerWidth && r.bottom <= innerHeight }; }, 目标.id);
  记.档位表.push({ 起点, 归位回读: 归位读.回读, 前, 目标: { id: 目标.id, aria: 目标.aria },
    选中, 阳性守卫: { 通过: 选中 === 1, 判据: `选中数 = ${选中}` }, 无效: 选中 !== 1,
    时间序列: 点, 末态: 末, 节点屏上,
    判定: { 缩放变了: 前.实测scale !== 末.实测scale, 旧: 前.实测scale, 新: 末.实测scale,
      平移变了: JSON.stringify(前.平移) !== JSON.stringify(末.平移) } });
  console.log(`起点${起点}% → 末 ${末.实测scale}（aria ${末.aria}）节点屏上 ${JSON.stringify(节点屏上 && [节点屏上.左, 节点屏上.上, 节点屏上.宽, 节点屏上.高])} 在视口内=${节点屏上 && 节点屏上.完整在视口内}`);
  await p.keyboard.press('Escape'); await p.waitForTimeout(500);
  save();
}

const 有效 = 记.档位表.filter((x) => !x.无效);
记.小结 = { 有效档数: 有效.length,
  终点集合: [...new Set(有效.map((x) => x.判定.新))],
  落点左集合: [...new Set(有效.map((x) => x.节点屏上 && x.节点屏上.左))],
  全部完整在视口内: 有效.every((x) => x.节点屏上 && x.节点屏上.完整在视口内) };
console.log('小结 =', JSON.stringify(记.小结));

const ids = await R.ids();
记.收尾 = { 状态行: await R.status(), 选中: await R.selCount(), credits: await R.credits(),
  节点数: ids.length, 基线节点数: 基线.ids.length,
  残留: ids.filter((x) => !基线.ids.includes(x)), 丢失: 基线.ids.filter((x) => !ids.includes(x)) };
await setZoom(p, 26); await p.waitForTimeout(600);
记.收尾.zoom = await R.zoom();
save();
console.log('收尾 =', JSON.stringify(记.收尾));
await b.close();
console.log('写出', OUT);

// 批次 192 c 轮：a 轮说「行里没有定位图标」是**我自己的选择器错了**
//   （写成 `canvas-search-locate-icon-node-`，真实 testid 是 `canvas-search-locate-icon-node_`）。
//   b 轮把行子树读出来后确认：图标**确实在行内右端**，`16×16`，中心 `[1061, 184]`，
//   行本身是 `BUTTON 312×64@773,152`（手册记的 `304×64` 偏窄 8px，本轮一并订正）。
//
// 🔑 本轮问：点那个 ⌖ 小图标，**是不是和点整行一样的取景行为**？
//   是 ⇒ 手册第 5 条那句「行内另有一个 …」可以升级成「两个入口、行为相同」。
//   不是 ⇒ 手册那句要补上「行为不同」。
import fs from 'node:fs';
import { openCanvas, readers, setZoom, settle } from './jimeng-b135-lib.mjs';

const OUT = '/tmp/b192c.json';
const 记 = { 轮次: 'b192c', 读数: [], 收尾: null };
const save = () => fs.writeFileSync(OUT, JSON.stringify(记, null, 1));
const 读缩放 = (p) => p.evaluate(() => {
  const e = document.querySelector('[data-testid="canvas-zoom-percent"]');
  const vp = document.querySelector('.react-flow__viewport');
  const t = (vp && vp.style.transform) || '';
  return { aria: e ? e.getAttribute('aria-label') : null,
    实测scale: (function () { const m = /scale\(([-\d.]+)\)/.exec(t); return m ? Math.round(parseFloat(m[1]) * 1000000) / 1000000 : null; })() };
});
const 输入框 = 'input[aria-label="搜索"]';
async function 开面板(p) {
  const btn = await p.evaluate(() => { const a = Array.from(document.querySelectorAll('BUTTON[data-testid="canvas-panel-launcher"]'))
    .find((x) => (x.getAttribute('aria-label') || '') === '搜索'); const r = a.getBoundingClientRect();
    return { expanded: a.getAttribute('aria-expanded'), 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; });
  if (btn.expanded !== 'true') { await p.mouse.click(btn.中心[0], btn.中心[1]); await p.waitForTimeout(1100); }
}
async function 取行(p, 词) {
  let 点 = await p.evaluate((sel) => { const i = document.querySelector(sel); if (!i) return null;
    const r = i.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, 输入框);
  if (!点) { await 开面板(p); 点 = await p.evaluate((sel) => { const i = document.querySelector(sel); if (!i) return null;
    const r = i.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, 输入框); }
  if (!点) return [];
  await p.mouse.click(点[0], 点[1]); await p.waitForTimeout(300);
  await p.keyboard.press('Meta+a'); await p.keyboard.type(词); await p.waitForTimeout(1500);
  return p.evaluate(() => Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-"]')).map((b) => {
    const r = b.getBoundingClientRect();
    const 图标 = b.querySelector('[data-testid^="canvas-search-locate-icon-node_"]');
    const ir = 图标 ? 图标.getBoundingClientRect() : null;
    return { id: (b.getAttribute('data-testid') || '').replace('canvas-search-result-', ''), aria: b.getAttribute('aria-label'),
      行屏上: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)],
      中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
      图标testid: 图标 ? 图标.getAttribute('data-testid') : null,
      图标屏上: ir ? [Math.round(ir.width), Math.round(ir.height)] : null,
      图标中心: ir ? [Math.round(ir.x + ir.width / 2), Math.round(ir.y + ir.height / 2)] : null };
  }));
}
const 读节点 = (p, id) => p.evaluate((nid) => { const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`); if (!n) return null;
  const r = n.getBoundingClientRect();
  return { 屏上: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    中心: [Math.round((r.x + r.width / 2) * 10) / 10, Math.round((r.y + r.height / 2) * 10) / 10],
    完整在视口内: r.x >= 0 && r.y >= 0 && r.right <= innerWidth && r.bottom <= innerHeight }; }, id);

const { b, p } = await openCanvas();
const R = readers(p);
await settle(p, R);
const 基线 = { ids: await R.ids(), credits: await R.credits() };

// 臂 1：点**行**（对照） 臂 2：点**行内的 ⌖ 图标**
for (const [臂, 用图标] of [[1, false], [2, true]]) {
  await setZoom(p, 26); await p.waitForTimeout(550);
  await p.keyboard.press('Escape'); await p.waitForTimeout(400);
  const 前 = await 读缩放(p);
  const 行 = await 取行(p, '音频 12');
  if (!行.length || (用图标 && !行[0].图标中心)) { 记.读数.push({ 臂, 无效: true, 原因: '取不到行或图标' }); save(); continue; }
  const 落点 = 用图标 ? 行[0].图标中心 : 行[0].中心;
  await p.mouse.click(落点[0], 落点[1]);
  const 选中 = await R.selCount();
  await p.waitForTimeout(2200);
  const 末 = await 读缩放(p);
  const 节点 = await 读节点(p, 行[0].id);
  记.读数.push({ 臂, 点的是: 用图标 ? '行内 ⌖ 定位图标' : '整行', 落点, 目标aria: 行[0].aria, 目标id: 行[0].id,
    行屏上: 行[0].行屏上, 图标testid: 行[0].图标testid, 图标屏上: 行[0].图标屏上,
    前: 前.实测scale, 选中, 无效: 选中 !== 1, 阳性守卫: { 通过: 选中 === 1, 判据: `选中数 = ${选中}` },
    取景: 末.实测scale, 末aria: 末.aria, 节点,
    面板还在: await p.evaluate(() => !!document.querySelector('input[aria-label="搜索"]')) });
  console.log(`臂${臂} 点${用图标 ? '⌖图标' : '整行'} → 守卫 ${选中}  取景 ${末.实测scale}  中心 ${JSON.stringify(节点 && 节点.中心)}  面板还在=${记.读数[记.读数.length - 1].面板还在}`);
  await p.keyboard.press('Escape'); await p.waitForTimeout(500);
  save();
}
const 有效 = 记.读数.filter((x) => !x.无效);
记.小结 = { 两臂取景是否相同: 有效.length === 2 ? 有效[0].取景 === 有效[1].取景 : null,
  两臂落点中心是否相同: 有效.length === 2 ? JSON.stringify(有效[0].节点.中心) === JSON.stringify(有效[1].节点.中心) : null,
  行屏上: 有效.map((x) => x.行屏上), 图标屏上: 有效.map((x) => x.图标屏上) };
console.log('小结 =', JSON.stringify(记.小结));
const ids = await R.ids();
记.收尾 = { 状态行: await R.status(), 选中: await R.selCount(), credits: await R.credits(), 节点数: ids.length,
  残留: ids.filter((x) => !基线.ids.includes(x)), 丢失: 基线.ids.filter((x) => !ids.includes(x)) };
await setZoom(p, 26); await p.waitForTimeout(500);
记.收尾.zoom = await R.zoom();
save();
console.log('收尾 =', JSON.stringify(记.收尾));
await b.close();

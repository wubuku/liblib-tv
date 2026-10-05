// 批次 192 a 轮：把批次 191 数据里露出来但没写进手册的**取景落点**钉死。
//
// 191 的 15 条落点读数里，有一条整齐得可疑：**节点中心的横坐标恒为 474.0**
//   —— 5 种类型、6 个不同缩放档（视频 1 在 50% 与 62.6% 两档）、15/15 条读数逐字相同。
//   而纵坐标中心**按类型固定**（视频 258 / 音频 260 / 时间线 360 / 文本 390 / 导演台 360）。
//
// 🔑 手册 `navigate-canvas.md` 搜索一节第 5 条（批次 127）写的是
//   「实测节点**从屏幕右下被移到视野中央**」—— **这一句与 15 条读数对不上**：
//   横向落在 474（不是视口中线 640），纵向只有时间线与导演台落在 360（视口中线）。
//   本轮要做的：① 补齐图片类型（191 只测了它的缩放预设，没测落点）
//   ② 把视频 1 的落点在**第三档缩放**上再验一次（证明落点与缩放无关）
//   ③ 结果行里那个 `canvas-search-locate-icon-node_<id>` 小图标是不是**第二个入口**
import fs from 'node:fs';
import { openCanvas, readers, setZoom, settle } from './jimeng-b135-lib.mjs';

const OUT = '/tmp/b192a.json';
const 记 = { 轮次: 'b192a', 问题: '取景落点是否恒定；定位小图标是不是第二个入口', 读数: [], 小图标: null, 收尾: null };
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
  const btn = await p.evaluate(() => { const a = Array.from(document.querySelectorAll('BUTTON[data-panel-launcher], BUTTON[data-testid="canvas-panel-launcher"]'))
    .find((x) => (x.getAttribute('aria-label') || '') === '搜索'); if (!a) return null;
    const r = a.getBoundingClientRect(); return { expanded: a.getAttribute('aria-expanded'), 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; });
  if (btn && btn.expanded !== 'true') { await p.mouse.click(btn.中心[0], btn.中心[1]); await p.waitForTimeout(1100); }
}
async function 取结果(p, 词) {
  let 点 = await p.evaluate((sel) => { const i = document.querySelector(sel); if (!i) return null;
    const r = i.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, 输入框);
  if (!点) { await 开面板(p); 点 = await p.evaluate((sel) => { const i = document.querySelector(sel); if (!i) return null;
    const r = i.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, 输入框); }
  if (!点) return [];
  await p.mouse.click(点[0], 点[1]); await p.waitForTimeout(300);
  await p.keyboard.press('Meta+a'); await p.keyboard.type(词); await p.waitForTimeout(1500);
  return p.evaluate(() => {
    const 行 = Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-"]'));
    return 行.map((b) => {
      const r = b.getBoundingClientRect();
      const 图标 = b.querySelector('[data-testid^="canvas-search-locate-icon-node-"]');
      const ir = 图标 ? 图标.getBoundingClientRect() : null;
      return { id: (b.getAttribute('data-testid') || '').replace('canvas-search-result-', ''), aria: b.getAttribute('aria-label'),
        中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
        有定位图标: !!图标, 图标testid: 图标 ? 图标.getAttribute('data-testid') : null,
        图标中心: ir && ir.width ? [Math.round(ir.x + ir.width / 2), Math.round(ir.y + ir.height / 2)] : null,
        图标屏上: ir ? [Math.round(ir.width), Math.round(ir.height)] : null };
    });
  });
}

const { b, p } = await openCanvas();
const R = readers(p);
await settle(p, R);
const 基线 = { ids: await R.ids(), credits: await R.credits() };

// ① 补齐图片类型落点 ② 视频 1 在 100% 档的落点（第三档，证明与缩放无关）
for (const [起点, 词] of [[200, 'b22-upload'], [100, '视频'], [50, '音频 5'], [200, '组']]) {
  await setZoom(p, 起点); await p.waitForTimeout(550);
  await p.keyboard.press('Escape'); await p.waitForTimeout(400);
  const 前 = await 读缩放(p);
  const 行 = await 取结果(p, 词);
  if (!行.length) { 记.读数.push({ 起点, 词, 无效: true, 原因: '没有结果行' }); save(); continue; }
  await p.mouse.click(行[0].中心[0], 行[0].中心[1]);
  const 选中 = await R.selCount();
  await p.waitForTimeout(2200);
  const 末 = await 读缩放(p);
  const 节点 = await p.evaluate((nid) => { const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`); if (!n) return null;
    const r = n.getBoundingClientRect();
    return { 屏上: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      中心: [Math.round((r.x + r.width / 2) * 10) / 10, Math.round((r.y + r.height / 2) * 10) / 10],
      完整在视口内: r.x >= 0 && r.y >= 0 && r.right <= innerWidth && r.bottom <= innerHeight }; }, 行[0].id);
  记.读数.push({ 起点, 词, 目标aria: 行[0].aria, 目标id: 行[0].id, 前: 前.实测scale, 选中, 无效: 选中 !== 1,
    取景: 末.实测scale, 节点, 行有定位图标: 行[0].有定位图标, 图标屏上: 行[0].图标屏上 });
  console.log(`起点${起点}% 搜「${词}」(${行[0].aria}) → 取景 ${末.实测scale}  屏上 ${JSON.stringify(节点 && 节点.屏上)}  中心 ${JSON.stringify(节点 && 节点.中心)}`);
  await p.keyboard.press('Escape'); await p.waitForTimeout(400);
  save();
}

// ③ 结果行里那个定位小图标：点它会发生什么？
{
  await setZoom(p, 26); await p.waitForTimeout(550);
  await p.keyboard.press('Escape'); await p.waitForTimeout(400);
  const 前 = await 读缩放(p);
  const 行 = await 取结果(p, '音频 10');
  if (!行.length || !行[0].有定位图标) { 记.小图标 = { 无效: true, 原因: !行.length ? '没有结果行' : '行里没有定位图标' }; }
  else {
    const 图标 = 行[0];
    await p.mouse.click(图标.图标中心[0], 图标.图标中心[1]);
    const 选中 = await R.selCount();
    await p.waitForTimeout(2200);
    const 末 = await 读缩放(p);
    const 节点 = await p.evaluate((nid) => { const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`); if (!n) return null;
      const r = n.getBoundingClientRect();
      return { 屏上: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        中心: [Math.round((r.x + r.width / 2) * 10) / 10, Math.round((r.y + r.height / 2) * 10) / 10] }; }, 图标.id);
    记.小图标 = { 目标aria: 图标.aria, 图标testid: 图标.图标testid, 图标屏上: 图标.图标屏上,
      前: 前.实测scale, 选中, 阳性守卫: { 通过: 选中 === 1, 判据: `选中数 = ${选中}` }, 无效: 选中 !== 1,
      取景: 末.实测scale, 末aria: 末.aria, 节点, 面板还在: await p.evaluate(() => !!document.querySelector('input[aria-label="搜索"]')) };
    console.log('定位小图标 =', JSON.stringify(记.小图标));
  }
  save();
}

const ids = await R.ids();
记.收尾 = { 状态行: await R.status(), 选中: await R.selCount(), credits: await R.credits(), 节点数: ids.length,
  残留: ids.filter((x) => !基线.ids.includes(x)), 丢失: 基线.ids.filter((x) => !ids.includes(x)) };
await setZoom(p, 26); await p.waitForTimeout(500);
记.收尾.zoom = await R.zoom();
save();
console.log('收尾 =', JSON.stringify(记.收尾));
await b.close();
console.log('写出', OUT);

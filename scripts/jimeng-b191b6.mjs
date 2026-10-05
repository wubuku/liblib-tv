// 批次 191 b6 轮：b5 把「上界是常数」**推翻了** —— 同一 200% 起点：
//   音频 1 → 1.125   时间线 → 0.623333   视频 1 → 0.625659
// ⇒ 上界**随节点而异**；其中 1.125 = 9/8 过于整齐，怀疑它是**全局上限**而那三个节点只是更小。
//
// 🔑 b6 只做一件事：从 200% 起，逐个换节点，量它的取景缩放。
//   · 若有多个节点精确落在 1.125 且没有超过它的 ⇒ 1.125 是**全局上限**。
//   · 手册里的写法随之确定：**「取景缩放被钳在 50%–112.5% 之间，具体值随节点而异」**。
import fs from 'node:fs';
import { openCanvas, readers, setZoom, settle } from './jimeng-b135-lib.mjs';

const OUT = '/tmp/b191b6.json';
const 记 = { 轮次: 'b191b6', 问题: '取景缩放的全局上限是多少', 读数: [] };
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

for (const 词 of ['图片', '文本', '导演台', '音频 2', '音频 3', '时间线']) {
  await setZoom(p, 200); await p.waitForTimeout(600);
  await p.keyboard.press('Escape'); await p.waitForTimeout(400);
  const 前 = await 读缩放(p);
  const 结果 = await 取结果行(p, 词);
  if (!结果.length) { 记.读数.push({ 词, 无效: true, 原因: '没有结果行' }); save(); continue; }
  const 目标 = 结果[0];
  await p.mouse.click(目标.中心[0], 目标.中心[1]);
  const 选中 = await R.selCount();
  await p.waitForTimeout(2200);
  const 末 = await 读缩放(p);
  // ⚠️ 上一版把 Node 侧的 `末` 直接写进 `p.evaluate` 的回调里 ⇒ 页面里根本没有这个变量
  //    （`ReferenceError: 末scale is not defined`）。`node --check` 查不出这类**跨边界作用域**错误，
  //    只能靠把需要的值**显式当参数传进去**。⇒ 立规：**传进 evaluate 的回调只能用形参**。
  const 节点 = await p.evaluate(([nid, z]) => { const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`); if (!n) return null;
    const r = n.getBoundingClientRect(); const s = z || 1;
    return { 屏上: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      canvas尺寸: [Math.round(r.width / s), Math.round(r.height / s)],
      完整在视口内: r.x >= 0 && r.y >= 0 && r.right <= innerWidth && r.bottom <= innerHeight }; }, [目标.id, 末.实测scale]);
  记.读数.push({ 词, 目标id: 目标.id, 目标aria: 目标.aria, 前: 前.实测scale, 选中, 无效: 选中 !== 1,
    末态: 末.实测scale, 末aria: 末.aria, 原始transform: 末.原始transform, 节点 });
  console.log(`搜「${词}」(${目标.aria}) 200% → ${末.实测scale}  屏上 ${JSON.stringify(节点 && 节点.屏上)}`);
  await p.keyboard.press('Escape'); await p.waitForTimeout(400);
  save();
}
const 有效 = 记.读数.filter((x) => !x.无效);
记.小结 = { 档数: 有效.length, 取景缩放集合: 有效.map((x) => ({ 词: x.词, aria: x.目标aria, 取景: x.末态, transform: x.原始transform })),
  全在视口内: 有效.every((x) => x.节点 && x.节点.完整在视口内) };
console.log('小结 =', JSON.stringify(记.小结, null, 1));
const ids = await R.ids();
记.收尾 = { 状态行: await R.status(), credits: await R.credits(), 节点数: ids.length,
  残留: ids.filter((x) => !基线.ids.includes(x)), 丢失: 基线.ids.filter((x) => !ids.includes(x)) };
await setZoom(p, 26); await p.waitForTimeout(500);
记.收尾.zoom = await R.zoom();
save();
console.log('收尾 =', JSON.stringify(记.收尾));
await b.close();

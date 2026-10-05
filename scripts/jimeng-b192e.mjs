// 批次 192 e 轮：第 180 张拍出来，**虚线框里是空的** —— ⌖ 定位图标默认看不见。
// 但第 179 张（点完结果行之后）里那个图标是**看得见的** ⇒ 它大概率是**悬停/选中才显形**。
//
// 🔑 本轮把显隐条件读出来（不靠对比两张图去猜），并带悬停重拍第 180 张。
// 判据：同一个元素在「未悬停 / 悬停 / 已选中」三态下的
//   `opacity` / `visibility` / `display` / 屏上矩形 / `color`，逐项对照。
import fs from 'node:fs';
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const SHOTS = 'docs/user-manual/jimeng-canvas/screenshots';
const 输入框 = 'input[aria-label="搜索"]';
const 读图标 = (p) => p.evaluate(() => {
  const 行 = document.querySelector('[data-testid^="canvas-search-result-"]');
  const 图标 = 行 ? 行.querySelector('[data-testid^="canvas-search-locate-icon-node_"]') : null;
  if (!图标) return null;
  const cs = getComputedStyle(图标); const r = 图标.getBoundingClientRect();
  const svg = 图标.querySelector('svg') || (图标.tagName.toLowerCase() === 'svg' ? 图标 : null);
  const ss = svg ? getComputedStyle(svg) : null;
  return { 屏上: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    opacity: cs.opacity, visibility: cs.visibility, display: cs.display, color: cs.color,
    自身rect: [Math.round(r.width), Math.round(r.height)],
    有svg: !!svg, svg的opacity: ss ? ss.opacity : null, svg的stroke: ss ? ss.stroke : null,
    行hover: 行.matches(':hover') };
});

const { b, p } = await openCanvas();
const R = readers(p);
await pinViewport(p);
await settle(p, R);
const btn = await p.evaluate(() => { const a = Array.from(document.querySelectorAll('BUTTON[data-testid="canvas-panel-launcher"]'))
  .find((x) => (x.getAttribute('aria-label') || '') === '搜索'); const r = a.getBoundingClientRect();
  return { expanded: a.getAttribute('aria-expanded'), 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; });
if (btn.expanded !== 'true') { await p.mouse.click(btn.中心[0], btn.中心[1]); await p.waitForTimeout(1100); }
const 点 = await p.evaluate((sel) => { const i = document.querySelector(sel); const r = i.getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, 输入框);
await p.mouse.click(点[0], 点[1]); await p.waitForTimeout(300);
await p.keyboard.press('Meta+a'); await p.keyboard.type('视频'); await p.waitForTimeout(1600);
// 鼠标挪到面板外空白处，确保没有 hover
await p.mouse.move(200, 400); await p.waitForTimeout(700);

const 态 = {};
态.未悬停 = await 读图标(p);
// 悬停到行的左半（避开图标本身）
const 行中 = await p.evaluate(() => { const 行 = document.querySelector('[data-testid^="canvas-search-result-"]');
  const r = 行.getBoundingClientRect(); return [Math.round(r.x + 60), Math.round(r.y + r.height / 2)]; });
await p.mouse.move(行中[0], 行中[1]); await p.waitForTimeout(800);
态.悬停行上 = await 读图标(p);
// 点它 → 选中态
await p.mouse.click(行中[0], 行中[1]); await p.waitForTimeout(1800);
态.点过之后 = await 读图标(p);
console.log('三态 =', JSON.stringify(态, null, 1));

// 带悬停重拍：把鼠标放回行上，再画两个框
await p.mouse.move(行中[0], 行中[1]); await p.waitForTimeout(900);
const 信息 = await p.evaluate(() => {
  const 行 = document.querySelector('[data-testid^="canvas-search-result-"]');
  const 图标 = 行.querySelector('[data-testid^="canvas-search-locate-icon-node_"]');
  const rr = 行.getBoundingClientRect(); const ir = 图标.getBoundingClientRect();
  const 加框 = (id, x, y, w, h, 线型) => { const d = document.createElement('div'); d.id = id;
    d.style.cssText = `position:fixed;left:${x}px;top:${y}px;width:${w}px;height:${h}px;border:3px ${线型} #ff8c00;border-radius:8px;pointer-events:none;z-index:2147483000;`;
    document.body.appendChild(d); };
  加框('__b192-row', rr.x - 4, rr.y - 4, rr.width + 8, rr.height + 8, 'solid');
  加框('__b192-icon', ir.x - 8, ir.y - 8, ir.width + 16, ir.height + 16, 'dashed');
  return { 行屏上: [Math.round(rr.x), Math.round(rr.y), Math.round(rr.width), Math.round(rr.height)],
    图标屏上: [Math.round(ir.x), Math.round(ir.y), Math.round(ir.width), Math.round(ir.height)],
    裁切: { x: Math.round(rr.x - 20), y: Math.round(rr.y - 60), width: Math.round(rr.width + 40), height: Math.round(rr.height + 120) } };
});
const 守卫 = await p.evaluate(() => {
  const 读一个 = (id) => { const e = document.getElementById(id); if (!e) return null;
    const cs = getComputedStyle(e); const r = e.getBoundingClientRect();
    return { 宽: Math.round(r.width), 高: Math.round(r.height), borderStyle: cs.borderStyle, pointerEvents: cs.pointerEvents }; };
  const 行 = 读一个('__b192-row'), 图标 = 读一个('__b192-icon');
  const 认线型 = ['solid', 'dashed', 'dotted', 'double'];
  return { 行, 图标, 全过: !!行 && !!图标 && 认线型.includes(行.borderStyle) && 认线型.includes(图标.borderStyle)
    && 行.pointerEvents === 'none' && 图标.pointerEvents === 'none' };
});
console.log('守卫 =', JSON.stringify(守卫));
if (守卫.全过) {
  await p.screenshot({ path: `${SHOTS}/180-search-result-two-entries.png`, clip: 信息.裁切 });
  console.log('已重拍 180');
}
await p.evaluate(() => { for (const id of ['__b192-row', '__b192-icon']) { const e = document.getElementById(id); if (e) e.remove(); } });
const 收 = { 状态行: await R.status(), 选中: await R.selCount(), zoom: await R.zoom(), credits: await R.credits(), 节点数: (await R.ids()).length };
console.log('收尾 =', JSON.stringify(收));
fs.writeFileSync('/tmp/b192e.json', JSON.stringify({ 态, 信息, 守卫, 收 }, null, 1));
await p.keyboard.press('Escape'); await p.waitForTimeout(600);
await b.close();

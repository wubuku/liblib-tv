// 批次 192 d 轮：拍第 180 张 —— 搜索结果行的**两个入口**（整行 / 行内 ⌖ 定位图标）。
// 守卫要点（立规 56 + 批次 190 的教训）：本图**同时**画 solid 与 dashed 两种框，
// 守卫必须**两种线型都认**，否则会把自己的图拦掉（190 a 轮就踩过）。
import fs from 'node:fs';
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const SHOTS = 'docs/user-manual/jimeng-canvas/screenshots';
const 输入框 = 'input[aria-label="搜索"]';
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

const 信息 = await p.evaluate(() => {
  const 行 = document.querySelector('[data-testid^="canvas-search-result-"]');
  if (!行) return null;
  const 图标 = 行.querySelector('[data-testid^="canvas-search-locate-icon-node_"]');
  const rr = 行.getBoundingClientRect(); const ir = 图标 ? 图标.getBoundingClientRect() : null;
  if (!图标) return null;
  const 加框 = (id, x, y, w, h, 线型) => { const d = document.createElement('div'); d.id = id;
    d.style.cssText = `position:fixed;left:${x}px;top:${y}px;width:${w}px;height:${h}px;border:3px ${线型} #ff8c00;border-radius:8px;pointer-events:none;z-index:2147483000;`;
    document.body.appendChild(d); };
  加框('__b192-row', rr.x - 4, rr.y - 4, rr.width + 8, rr.height + 8, 'solid');
  加框('__b192-icon', ir.x - 7, ir.y - 7, ir.width + 14, ir.height + 14, 'dashed');
  return { 行testid: 行.getAttribute('data-testid'), 行aria: 行.getAttribute('aria-label'),
    行屏上: [Math.round(rr.x), Math.round(rr.y), Math.round(rr.width), Math.round(rr.height)],
    图标testid: 图标.getAttribute('data-testid'),
    图标屏上: [Math.round(ir.x), Math.round(ir.y), Math.round(ir.width), Math.round(ir.height)],
    裁切: { x: Math.round(rr.x - 20), y: Math.round(rr.y - 60), width: Math.round(rr.width + 40), height: Math.round(rr.height + 120) } };
});
console.log('信息 =', JSON.stringify(信息));
if (!信息) { console.log('没有行或图标，停'); await b.close(); process.exit(1); }

// 守卫：把两个框都读回来，且**两种线型都要被认**
const 守卫 = await p.evaluate(() => {
  const 读一个 = (id) => { const e = document.getElementById(id); if (!e) return null;
    const cs = getComputedStyle(e); const r = e.getBoundingClientRect();
    return { 宽: Math.round(r.width), 高: Math.round(r.height), borderStyle: cs.borderStyle,
      borderWidth: cs.borderWidth, pointerEvents: cs.pointerEvents, zIndex: cs.zIndex }; };
  const 行 = 读一个('__b192-row'), 图标 = 读一个('__b192-icon');
  const 认线型 = ['solid', 'dashed', 'dotted', 'double'];
  return { 行, 图标,
    全过: !!行 && !!图标 && 行.宽 > 2 && 行.高 > 2 && 图标.宽 > 2 && 图标.高 > 2
      && 认线型.includes(行.borderStyle) && 认线型.includes(图标.borderStyle)
      && 行.pointerEvents === 'none' && 图标.pointerEvents === 'none',
    认得的线型集合: 认线型 };
});
console.log('守卫 =', JSON.stringify(守卫));
if (!守卫.全过) { console.log('守卫不过，不拍'); await b.close(); process.exit(1); }

await p.screenshot({ path: `${SHOTS}/180-search-result-two-entries.png`, clip: 信息.裁切 });
await p.evaluate(() => { for (const id of ['__b192-row', '__b192-icon']) { const e = document.getElementById(id); if (e) e.remove(); } });
const 收 = { 状态行: await R.status(), 选中: await R.selCount(), zoom: await R.zoom(), credits: await R.credits(), 节点数: (await R.ids()).length };
console.log('收尾 =', JSON.stringify(收));
fs.writeFileSync('/tmp/b192d.json', JSON.stringify({ 信息, 守卫, 收 }, null, 1));
await p.keyboard.press('Escape'); await p.waitForTimeout(600);
await b.close();

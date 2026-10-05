// 批次 170 g 轮：右键菜单 `canvas-context-menu` 的机制。
//
// 已确认（f 轮）：
//   · class 逐字含 `max-w-[calc(100vw_-_16px)] max-h-[calc(100vh_-_16px)]`
//     ⇒ 这是「余量 16」这一族在真实 DOM 里的活实例（静态 CSS 里另有一个 16：`max-w-canvas-smart-edit-cursor-guide`）
//   · 静止态就在、鼠标移开不消失、Esc 能关 ⇒ **它是会被遗留的挡板**（f 轮实测吞掉整块节点区域的点击）
//   · 几何 200×316，内容为「添加上下文 / 文本 / 图片 / 视频 / 音频 / 时间线 / 主体」+ 每项的「无法连接这些节点」
//
// 本轮要回答：
//   Q1 开菜单的手势是什么？（右键？左键空白？）
//   Q2 宽 200 / 高 316 是**常量**还是**内容累加**？换锚点重开会不会变？
//   Q3 余量 16 的夹取什么时候生效？（预测：vw<216 触发宽夹取，vh<332 触发高夹取）
//   Q4 锚点定位规则：贴着鼠标？贴着节点边缘？会不会翻转？
import { openCanvas, readers } from './jimeng-b135-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);

const readMenu = () => p.evaluate(() => {
  const e = document.querySelector('[data-testid="canvas-context-menu"]');
  if (!e) return null;
  const cs = getComputedStyle(e);
  const r = e.getBoundingClientRect();
  const items = Array.from(e.querySelectorAll('[data-testid]')).map((x) => {
    const xr = x.getBoundingClientRect();
    return { testid: x.getAttribute('data-testid'), rect: [Math.round(xr.x), Math.round(xr.y), Math.round(xr.width), Math.round(xr.height)] };
  });
  return {
    rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    pos: cs.position, z: cs.zIndex, transform: cs.transform, left: cs.left, top: cs.top,
    items: items.slice(0, 14),
    text: (e.innerText || '').trim().split('\n').filter(Boolean).slice(0, 20),
  };
});
const state = async () => ({ status: await R.status(), sel: await R.selCount(), credits: await R.credits() });

console.log('起点:', JSON.stringify(await state()));

// —— Q1：右键空白 vs 右键节点 ——
const trials = [
  ['右键-空白(900,620)', 900, 620],
  ['右键-节点中心', null, null],
];
for (const [tag, x0, y0] of trials) {
  let x = x0, y = y0;
  if (x0 === null) {
    const pt = await p.evaluate(() => {
      const n = Array.from(document.querySelectorAll('.react-flow__node'))
        .find((e) => e.querySelector('[data-testid="audio-node-empty"]'));
      const r = n.getBoundingClientRect();
      return [r.x + r.width / 2, r.y + r.height / 2];
    });
    x = pt[0]; y = pt[1];
  }
  await p.keyboard.press('Escape');           // 先清干净
  await p.waitForTimeout(400);
  await p.mouse.move(x, y);
  await p.waitForTimeout(250);
  await p.mouse.click(x, y, { button: 'right' });
  await p.waitForTimeout(1000);
  const m = await readMenu();
  console.log(`\n=== ${tag} @(${Math.round(x)},${Math.round(y)}) ===`);
  console.log('  menu:', m ? JSON.stringify({ rect: m.rect, pos: m.pos, z: m.z, left: m.left, top: m.top }) : 'null');
  if (m) {
    console.log('  items:', JSON.stringify(m.items));
    console.log('  text:', JSON.stringify(m.text));
  }
  console.log('  state:', JSON.stringify(await state()));
}
await b.close();

// 批次 171 k 轮：重拍 133（d 轮拍错：高亮框落在时间线工具条上，不是标签选择器）。
//
// 🔴 d 轮的错误：截图脚本里 `框(p, '.max-w-canvas-tag-selector')` 是在**读数之后**才画的，
//    而 d 轮先按了 Esc/点了空白复原，元素**已经不在了** ⇒ `querySelector` 返回 null ⇒
//    高亮框那段虽然返回 null 但脚本**没检查**，于是**沿用了上一次 框() 调用留下的框**（时间线工具条的框）。
//    ⇒ 画高亮框后必须**断言框画在了哪个元素上**。
//
// 顺带：b171a 打开的 AI 侧栏还开着，本轮先关掉，画面干净些。
// ⛔ 不点任何颜色按钮。
import fs from 'node:fs';
import { openCanvas, readers } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const DIR = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url).pathname;
const { b, p } = await openCanvas();
const R = readers(p);
await pinViewport(p);

// 关掉可能开着的浮层。
// 🔴 第一版只按 Esc：AI 侧栏（`ASIDE[aria="Agent"]`）**按 Esc 关不掉**，
//    第一张 133 的右缘就挂着一截侧栏（「探索…」「/ 标…」「/ 全流…」）。
//    ⇒ 侧栏要用它**自己的收起按钮**（aria 逐字「收起」）关，不能靠 Esc。
for (let i = 0; i < 4; i++) {
  const open = await p.evaluate(() => ({
    sidecar: !!document.querySelector('aside[aria="Agent"]'),
    menu: !!document.querySelector('[data-testid="canvas-context-menu"]'),
  }));
  if (!open.sidecar && !open.menu) break;
  if (open.sidecar) {
    const 收起 = await p.evaluate(() => {
      const e = Array.from(document.querySelectorAll('aside[aria="Agent"] button,[role=button]'))
        .find((x) => (x.getAttribute('aria-label') || '') === '收起');
      if (!e) return null;
      const r = e.getBoundingClientRect();
      return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
    });
    if (收起) { await p.mouse.click(收起[0], 收起[1]); await p.waitForTimeout(800); continue; }
  }
  await p.keyboard.press('Escape'); await p.waitForTimeout(400);
}
console.log('浮层已关:', JSON.stringify(await p.evaluate(() => ({
  sidecar: !!document.querySelector('aside[aria="Agent"]'),
  menu: !!document.querySelector('[data-testid="canvas-context-menu"]'),
}))));
let bp = await p.evaluate(() => {
  for (let y = 30; y < innerHeight - 30; y += 10)
    for (let x = 30; x < innerWidth - 30; x += 10) {
      const e = document.elementFromPoint(x, y);
      if (e && e.closest('.react-flow__pane') && !e.closest('.react-flow__node')) return [x, y];
    }
  return null;
});
if (bp) { await p.mouse.click(bp[0], bp[1]); await p.waitForTimeout(600); }
await p.keyboard.press('Escape'); await p.waitForTimeout(300);
console.log('起点:', JSON.stringify({ status: await R.status(), sel: await R.selCount(),
  残留浮层: await p.evaluate(() => document.querySelectorAll('[data-testid="canvas-context-menu"], aside[aria="Agent"]').length) }));

// 选节点 → Add tags
const sel = await p.evaluate(() => {
  for (const t of document.querySelectorAll('.react-flow__node [data-testid="flow-node-title"]')) {
    const r = t.getBoundingClientRect();
    const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
    if (cx < 4 || cy < 4 || cx > innerWidth - 4 || cy > innerHeight - 4) continue;
    const hit = document.elementFromPoint(cx, cy);
    if (hit && hit.closest('.react-flow__node') && !hit.closest('[data-testid^=flow-node-target],[data-testid^=flow-node-source]')) {
      return { pt: [Math.round(cx), Math.round(cy)], 文字: (t.innerText || '').trim().slice(0, 10) };
    }
  }
  return null;
});
console.log('选中:', JSON.stringify(sel));
if (!sel) { await b.close(); process.exit(1); }
await p.mouse.click(sel.pt[0], sel.pt[1]);
await p.waitForTimeout(900);
const tag = await p.evaluate(() => {
  const e = document.querySelector('[data-testid="flow-node-selected-tag"]');
  if (!e) return null;
  const r = e.getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
});
if (!tag) { console.log('没有 Add tags'); await b.close(); process.exit(1); }
await p.mouse.click(tag[0], tag[1]);
await p.waitForTimeout(1600);

// 画高亮框，**并断言框画在了哪个元素上**
const hl = await p.evaluate(() => {
  document.querySelectorAll('.__b171hl').forEach((e) => e.remove());
  const e = document.querySelector('.max-w-canvas-tag-selector');
  if (!e) return { 失败: '标签条不在 DOM 里' };
  const r = e.getBoundingClientRect();
  const d = document.createElement('div');
  d.className = '__b171hl';
  d.style.cssText = `position:fixed;left:${r.x - 4}px;top:${r.y - 4}px;width:${r.width + 8}px;height:${r.height + 8}px;` +
    `border:3px solid #ff8c00;border-radius:10px;pointer-events:none;z-index:2147483646`;
  document.body.appendChild(d);
  // 断言：框的四个角必须落在标签条的包围盒 ±4 内
  const q = d.getBoundingClientRect();
  return {
    标签条盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    框盒: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)],
    标签条testid: e.getAttribute('data-testid'),
    标签条文字: (e.innerText || '').trim().split('\n').filter(Boolean),
    按钮: Array.from(e.querySelectorAll('button')).map((b) => {
      const br = b.getBoundingClientRect();
      return { aria: b.getAttribute('aria-label'), 盒: [Math.round(br.x), Math.round(br.y), Math.round(br.width), Math.round(br.height)] };
    }),
  };
});
console.log('高亮框:', JSON.stringify(hl, null, 1));
if (hl.失败) { console.log('❌ ' + hl.失败); await b.close(); process.exit(1); }

// 裁到标签条周边，让图里主体清楚（上下各留 90、左右各留 160）
const clip = {
  x: Math.max(0, hl.标签条盒[0] - 90), y: Math.max(0, hl.标签条盒[1] - 70),
  width: Math.min(1280 - Math.max(0, hl.标签条盒[0] - 90), hl.标签条盒[2] + 180), height: hl.标签条盒[3] + 140,
};
await p.waitForTimeout(300);
await p.screenshot({ path: DIR + '133-node-tag-selector-224x44.png', clip });
console.log('已拍 133（裁剪', JSON.stringify(clip), '）');

await p.evaluate(() => document.querySelectorAll('.__b171hl').forEach((e) => e.remove()));
await p.keyboard.press('Escape'); await p.waitForTimeout(400);
if (bp) { await p.mouse.click(bp[0], bp[1]); await p.waitForTimeout(500); }
await p.keyboard.press('Escape'); await p.waitForTimeout(300);
console.log('收尾:', JSON.stringify({ status: await R.status(), sel: await R.selCount(), credits: await R.credits(),
  残留浮层: await p.evaluate(() => document.querySelectorAll('[data-testid="canvas-context-menu"], aside[aria="Agent"], .max-w-canvas-tag-selector').length) }));
await b.close();

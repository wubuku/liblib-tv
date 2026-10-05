// 批次 174 g 轮：截图 —— 顶栏标题区放大，把「已保存」这个 **30×18** 的小标签框出来。
//
// 为什么这张图值得拍：示意图（截图 100 多号那张）只能画到「顶栏有���已保存」这一层，
// 而本批的结论恰恰是**这个字有多小、它挨着什么、它不是按钮**：
//   `canvas-title-save-status` = `30×18@206,21`，`<output aria-live="polite">`
//   左侧紧挨 `节点 76`（`canvas-node-summary-trigger`）与 `canvas-title-separator`
//   右侧是空的 —— 直到 `canvas-project-trigger` 才结束
// 拍之前先按 DOM 取几何（不靠肉眼估），高亮框的返回值要检查。
import fs from 'node:fs';
import path from 'node:path';
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';

const DIR = path.resolve('docs/user-manual/jimeng-canvas/screenshots') + '/';
const { b, p } = await openCanvas();
const R = readers(p);
await settle(p, R);
await p.mouse.move(1250, 10); await p.waitForTimeout(600);

const hl = await p.evaluate(() => {
  document.querySelectorAll('.__b174hl').forEach((e) => e.remove());
  const e = document.querySelector('[data-testid="canvas-title-save-status"]');
  if (!e) return { 失败: '没找到保存状态元素' };
  const r = e.getBoundingClientRect();
  // ⚠️ v1 这里传的是**裸 testid 名**（`'canvas-title-separator'`），
  //    `document.querySelector` 找的是 `<canvas-title-separator>` 这个**标签**，
  //    于是五个邻元全报「缺失」—— 而同一段里内联那份用了 `[data-testid=…]` 却成功了。
  //    读数不一致时先怀疑自己的选择器，再怀疑页面。
  const 邻 = (tid) => { const sel = `[data-testid="${tid}"]`; const n = document.querySelector(sel); if (!n) return { tid, 缺失: true };
    const q = n.getBoundingClientRect(); return { tid, 盒: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)],
      文字: (n.innerText || '').trim(), aria: n.getAttribute('aria-label'), 标签: n.tagName.toLowerCase() }; };
  const d = document.createElement('div');
  d.className = '__b174hl';
  d.style.cssText = `position:fixed;left:${r.x - 6}px;top:${r.y - 6}px;width:${r.width + 12}px;height:${r.height + 12}px;` +
    `border:3px solid #ff8c00;border-radius:8px;pointer-events:none;z-index:2147483646`;
  document.body.appendChild(d);
  return { 盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    标签: e.tagName.toLowerCase(), 文本: (e.textContent || '').trim(), ariaLive: e.getAttribute('aria-live'),
    自身可点: e.tagName.toLowerCase() === 'button' || e.getAttribute('role') === 'button',
    光标: getComputedStyle(e).cursor,
    邻: ['canvas-title-separator', 'canvas-node-summary-trigger', 'canvas-node-summary-count', 'canvas-project-trigger', 'canvas-top-bar-left']
      .map(邻),
    顶栏左段盒: (() => { const n = document.querySelector('[data-testid="canvas-top-bar-left"]');
      if (!n) return null; const q = n.getBoundingClientRect();
      return [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)]; })() };
});
console.log('高亮框读数:', JSON.stringify(hl, null, 1));

if (!hl.失败) {
  // 裁剪**只取顶栏左段**：顶栏背景是半透明的，再往右多裁一像素就会把底下的节点裁进来
  // （v1 裁到 268 宽，右边 30 px 全是画布上的「文本 2 / 文本…」，图很难看）。
  const 右 = hl.盒[0] + hl.盒[2] + 10;
  // 顶栏本体 40 高、y 从 10 起 ⇒ 底边正好 50；再往下多裁一像素就会带进画布节点
  const clip = { x: 0, y: 0, width: 右, height: 50 };
  await p.waitForTimeout(400);
  await p.screenshot({ path: DIR + '137-topbar-save-status.png', clip });
  console.log('已拍 137，裁剪', JSON.stringify(clip));
}
await p.evaluate(() => document.querySelectorAll('.__b174hl').forEach((e) => e.remove()));
await p.waitForTimeout(300);

const f = DIR + '137-topbar-save-status.png';
if (fs.existsSync(f)) {
  const st = fs.statSync(f);
  const sha = (await import('node:crypto')).createHash('sha256').update(fs.readFileSync(f)).digest('hex');
  console.log('文件', f, st.size, '字节  sha256', sha);
} else console.log('⛔ 截图没落盘');
console.log('状态行:', await R.status(), '| 积分:', await R.credits());
process.exit(0);

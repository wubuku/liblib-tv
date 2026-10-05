// 批次 192 b 轮：a 轮证伪了手册的一句 —— `navigate-canvas.md` 搜索一节第 5 条写着
//   「行内另有一个 `canvas-search-locate-icon-node_<同一个 id>`」，
//   而 a 轮在**结果行内部**用 `[data-testid^="canvas-search-locate-icon-node-"]` **一个都没找到**
//   （三行结果、有定位图标 全是 false）。但第 179 张截图里结果行右端**肉眼可见**一个 ⌖ 图标。
//
// ⇒ 两种可能：① 那个 testid 记错了 / 已改名；② 它不在行**内部**（是兄弟节点或更外层）。
// 本轮把结果行的子树逐层读出来，把「图标到底是什么、在哪一层、能不能点」坐实。
import fs from 'node:fs';
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';

const 输入框 = 'input[aria-label="搜索"]';
const { b, p } = await openCanvas();
const R = readers(p);
await settle(p, R);
const btn = await p.evaluate(() => { const a = Array.from(document.querySelectorAll('BUTTON[data-testid="canvas-panel-launcher"]'))
  .find((x) => (x.getAttribute('aria-label') || '') === '搜索'); const r = a.getBoundingClientRect();
  return { expanded: a.getAttribute('aria-expanded'), 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; });
if (btn.expanded !== 'true') { await p.mouse.click(btn.中心[0], btn.中心[1]); await p.waitForTimeout(1100); }
const 点 = await p.evaluate((sel) => { const i = document.querySelector(sel); const r = i.getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, 输入框);
await p.mouse.click(点[0], 点[1]); await p.waitForTimeout(300);
await p.keyboard.press('Meta+a'); await p.keyboard.type('视频'); await p.waitForTimeout(1500);

const 行子树 = await p.evaluate(() => {
  const 行 = document.querySelector('[data-testid^="canvas-search-result-"]');
  if (!行) return { 有行: false };
  const 走 = (e, d) => { const r = e.getBoundingClientRect();
    return { 深度: d, tag: e.tagName, testid: e.getAttribute('data-testid'), role: e.getAttribute('role'),
      aria: e.getAttribute('aria-label'), 文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24),
      屏上: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      子: d < 4 ? Array.from(e.children).map((c) => 走(c, d + 1)) : [] }; };
  return { 有行: true, 行testid: 行.getAttribute('data-testid'), 树: 走(行, 0) };
});
// 全页搜 locate 相关 testid（不预设它在行内）
const 全页 = await p.evaluate(() => Array.from(new Set(Array.from(document.querySelectorAll('[data-testid]'))
  .map((e) => e.getAttribute('data-testid')).filter((t) => t && /locate|icon|target/i.test(t)))));
const svg数 = await p.evaluate(() => {
  const 行 = document.querySelector('[data-testid^="canvas-search-result-"]');
  if (!行) return null;
  return { 行内svg: 行.querySelectorAll('svg').length, 行内path: 行.querySelectorAll('path').length,
    行内button: 行.querySelectorAll('button').length, 行内span: 行.querySelectorAll('span').length,
    每个svg的屏上: Array.from(行.querySelectorAll('svg')).map((s) => { const r = s.getBoundingClientRect();
      return { 屏上: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], class: String(s.className.baseVal || s.className || '').slice(0, 60) }; }) };
});
console.log('全页 locate/icon/target 相关 testid =', JSON.stringify(全页));
console.log('行内元素统计 =', JSON.stringify(svg数, null, 1));
console.log('行子树 =', JSON.stringify(行子树, null, 1));
fs.writeFileSync('/tmp/b192b.json', JSON.stringify({ 行子树, 全页, svg数 }, null, 1));
await p.keyboard.press('Escape'); await p.waitForTimeout(500);
await b.close();

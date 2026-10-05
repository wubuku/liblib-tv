// 批次 191 c2 轮：b 轮那个取不到 input 的选择器，逐个候选当面验一遍。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
const { b, p } = await openCanvas();
const R = readers(p);
await settle(p, R);
const 开 = await p.evaluate(() => { const a = Array.from(document.querySelectorAll('BUTTON[data-testid="canvas-panel-launcher"]'))
  .find((x) => (x.getAttribute('aria-label') || '') === '搜索');
  const r = a.getBoundingClientRect(); return { expanded: a.getAttribute('aria-expanded'), 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; });
if (开.expanded !== 'true') { await p.mouse.click(开.中心[0], 开.中心[1]); await p.waitForTimeout(1200); }
const 候选 = [
  '[data-testid="canvas-feature-panel"] input[aria="搜索"]',
  '[data-testid="canvas-feature-panel"] input',
  'input[aria="搜索"]',
  'input[placeholder="搜索节点..."]',
  '[data-testid="canvas-search-panel"] input',
  '[data-testid="canvas-search-results-slot"] input',
];
const 结果 = await p.evaluate((sels) => sels.map((s) => { const e = document.querySelector(s);
  if (!e) return { 选择器: s, 命中: false };
  const r = e.getBoundingClientRect();
  return { 选择器: s, 命中: true, tag: e.tagName, value: e.value, placeholder: e.placeholder,
    中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; }), 候选);
console.log(JSON.stringify(结果, null, 1));
// 顺手确认：填词之后结果行到底叫什么
await p.fill('input[aria="搜索"]', '视频');
await p.waitForTimeout(1500);
const 行 = await p.evaluate(() => Array.from(document.querySelectorAll('[data-testid]'))
  .map((x) => x.getAttribute('data-testid')).filter((t) => t && /result/i.test(t)));
const 实际行 = await p.evaluate(() => {
  const AS = document.querySelector('[data-testid="canvas-feature-panel"]'); if (!AS) return null;
  return Array.from(AS.querySelectorAll('button,[role=option],[role=button]')).slice(0, 8).map((e) => {
    const r = e.getBoundingClientRect();
    return { tag: e.tagName, role: e.getAttribute('role'), testid: e.getAttribute('data-testid'),
      aria: e.getAttribute('aria-label'), 文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40),
      中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; });
});
console.log('结果行相关 testid =', JSON.stringify(行));
console.log('面板内可点元素 =', JSON.stringify(实际行, null, 1));
await p.keyboard.press('Escape'); await p.waitForTimeout(500);
await b.close();

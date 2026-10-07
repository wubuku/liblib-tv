/**
 * 批次 299 · 探路：节点外框（node toolbar）在 DOM 里到底叫什么、长什么样。
 * 只读：定位一次后读元素，不点任何新东西。
 */
import { chromium } from 'playwright';

const STATE = `${process.env.HOME}/.jimeng-automation/state.json`;
const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';

const b = await chromium.launch({ headless: true });
const ctx = await b.newContext({ storageState: STATE, viewport: { width: 1212, height: 720 } });
const p = await ctx.newPage();
await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
await p.waitForSelector('.react-flow__node', { timeout: 60000 });
await p.waitForTimeout(6000);

for (let i = 0; i < 13; i++) { await p.keyboard.press('Meta+Equal'); await p.waitForTimeout(380); }
await p.waitForTimeout(1200);

const 钮 = await p.evaluate(() => {
  const x = document.querySelector('button[aria-label="搜索"]');
  if (!x) return null;
  const r = x.getBoundingClientRect();
  return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
});
await p.mouse.click(钮.x, 钮.y);
await p.waitForTimeout(1600);
await p.evaluate(() => { const i = document.querySelector('[data-testid="canvas-search-panel"] input'); if (i) { i.focus(); i.select(); } });
await p.keyboard.type('音频 1', { delay: 80 });
await p.waitForTimeout(2000);
const 行 = await p.evaluate(() => {
  const 全 = Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-node_"]'));
  const e = 全[0];
  if (!e) return null;
  e.scrollIntoView({ block: 'center' });
  const b = e.getBoundingClientRect();
  return { x: Math.round(b.x + b.width / 2), y: Math.round(b.y + b.height / 2), testid: e.dataset.testid };
});
console.log('结果行 =', JSON.stringify(行));
await p.mouse.click(行.x, 行.y);
await p.waitForTimeout(4500);

const 探 = await p.evaluate(() => {
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  const node = document.querySelector('.react-flow__node.selected');
  const out = { scale: m ? Number(m[1]) : null, 节点: null, 外框候选: [] };
  if (node) {
    const r = node.getBoundingClientRect();
    out.节点 = { aria: node.getAttribute('aria-label'), testid: node.dataset.testid, 屏: [r.x, r.y, r.width, r.height], 画布: [node.offsetWidth, node.offsetHeight], className: node.className };
    // 找所有 testid / class 里带 toolbar 的后代
    const all = Array.from(node.querySelectorAll('*'));
    for (const e of all) {
      const tid = e.getAttribute && e.getAttribute('data-testid');
      const cn = typeof e.className === 'string' ? e.className : '';
      if ((tid && /toolbar|chrome|decorate/i.test(tid)) || /toolbar|chrome/i.test(cn)) {
        const q = e.getBoundingClientRect();
        out.外框候选.push({ testid: tid, className: cn.slice(0, 60), tag: e.tagName, 屏: [+q.x.toFixed(1), +q.y.toFixed(1), +q.width.toFixed(1), +q.height.toFixed(1)] });
      }
    }
    // 画布 wrapper 上的 CSS 变量
    const wrap = document.querySelector('.react-flow');
    out.counterScale = wrap ? getComputedStyle(wrap).getPropertyValue('--octo-canvas-node-chrome-counter-scale') : null;
  }
  return out;
});
console.log(JSON.stringify(探, null, 1));
await ctx.close();
await b.close();
process.exit(0);

// 批次 191 c 轮：把搜索面板的**真实 DOM 逐字读出来**（不猜选择器）。
// b 轮踩到：`[data-testid="canvas-feature-panel"] input[aria="搜索"]` 取到 null，
// 而面板本体确实存在（`320×211@769,56`）⇒ 先读结构，再写选择器。
import fs from 'node:fs';
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
await settle(p, R);

const out = {};
const 启动 = await p.evaluate(() => Array.from(document.querySelectorAll('BUTTON[data-testid="canvas-panel-launcher"]'))
  .map((x) => { const r = x.getBoundingClientRect(); return { aria: x.getAttribute('aria-label'), expanded: x.getAttribute('aria-expanded'),
    中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; }));
out.启动器 = 启动;
const 开 = 启动.find((x) => x.aria === '搜索');
if (开 && 开.expanded !== 'true') { await p.mouse.click(开.中心[0], 开.中心[1]); await p.waitForTimeout(1200); }

out.面板 = await p.evaluate(() => {
  const e = document.querySelector('[data-testid="canvas-feature-panel"]');
  if (!e) return null;
  const r = e.getBoundingClientRect();
  return { tag: e.tagName, role: e.getAttribute('role'), aria: e.getAttribute('aria-label'),
    矩形: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)],
    全部input: Array.from(e.querySelectorAll('input')).map((i) => { const q = i.getBoundingClientRect();
      return { type: i.type, aria: i.getAttribute('aria-label'), placeholder: i.placeholder, value: i.value,
        testid: i.getAttribute('data-testid'), 中心: [Math.round(q.x + q.width / 2), Math.round(q.y + q.height / 2)] }; }),
    全部testid: Array.from(new Set(Array.from(e.querySelectorAll('[data-testid]')).map((x) => x.getAttribute('data-testid')))) };
});
out.面板外input = await p.evaluate(() => Array.from(document.querySelectorAll('input')).map((i) => { const r = i.getBoundingClientRect();
  return { aria: i.getAttribute('aria-label'), placeholder: i.placeholder, type: i.type,
    在面板内: !!i.closest('[data-testid="canvas-feature-panel"]'),
    矩形: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)] }; }));
out.结果行testid = await p.evaluate(() => Array.from(new Set(Array.from(document.querySelectorAll('[data-testid]'))
  .map((x) => x.getAttribute('data-testid')).filter((t) => t && /search/i.test(t)))));
console.log(JSON.stringify(out, null, 1));
fs.writeFileSync('/tmp/b191c.json', JSON.stringify(out, null, 1));
await b.close();

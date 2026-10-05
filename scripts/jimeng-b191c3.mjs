// 批次 191 c3 轮：查 `page.fill` 为什么在这个搜索框上超时 ——
// 元素在 DOM 里、有真实矩形，但 Playwright 的可操作性检查过不去。
// 判据是复现「Playwright 看到的」与「DOM 说的」之间的差：命中测试 / 可见性 / pointer-events。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
const { b, p } = await openCanvas();
const R = readers(p);
await settle(p, R);
const btn = await p.evaluate(() => { const a = Array.from(document.querySelectorAll('BUTTON[data-testid="canvas-panel-launcher"]'))
  .find((x) => (x.getAttribute('aria-label') || '') === '搜索'); const r = a.getBoundingClientRect();
  return { expanded: a.getAttribute('aria-expanded'), 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; });
if (btn.expanded !== 'true') { await p.mouse.click(btn.中心[0], btn.中心[1]); await p.waitForTimeout(1200); }

const 诊断 = await p.evaluate(() => {
  const i = document.querySelector('input[aria-label="搜索"]');
  if (!i) return { 有: false };
  const r = i.getBoundingClientRect();
  const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
  const top = document.elementFromPoint(cx, cy);
  const cs = getComputedStyle(i);
  const chain = []; for (let n = i; n && n !== document.body; n = n.parentElement) {
    const c = getComputedStyle(n);
    chain.push({ tag: n.tagName, testid: n.getAttribute('data-testid'), ariaHidden: n.getAttribute('aria-hidden'),
      inert: n.hasAttribute('inert'), pointerEvents: c.pointerEvents, visibility: c.visibility, display: c.display, opacity: c.opacity });
  }
  return { 有: true, 矩形: [r.x, r.y, r.width, r.height].map(Math.round), 中心: [Math.round(cx), Math.round(cy)],
    值: i.value, disabled: i.disabled, readOnly: i.readOnly, tabIndex: i.tabIndex,
    input自身: { visibility: cs.visibility, display: cs.display, opacity: cs.opacity, pointerEvents: cs.pointerEvents, width: cs.width, height: cs.height },
    命中测试最上层: top ? top.tagName + '[' + (top.getAttribute('data-testid') || top.className || '') + ']' : null,
    命中的是输入框本身: top === i || i.contains(top),
    祖先链: chain };
});
console.log(JSON.stringify(诊断, null, 1));

// 试真实键盘路径：点一下 → 全选 → 输入
const 键盘路径 = { ok: null, err: null };
try {
  const 点 = 诊断.中心;
  await p.mouse.click(点[0], 点[1]);
  await p.waitForTimeout(400);
  const 点后焦点 = await p.evaluate(() => { const a = document.activeElement; return a ? a.tagName + '[' + (a.getAttribute('aria-label') || a.getAttribute('data-testid') || '') + ']' : null; });
  await p.keyboard.press('Meta+a');
  await p.keyboard.type('视频');
  await p.waitForTimeout(1500);
  键盘路径.ok = { 点后焦点, 输入框值: await p.evaluate(() => document.querySelector('input[aria-label="搜索"]').value),
    结果行: await p.evaluate(() => Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-"]')).map((b) => {
      const r = b.getBoundingClientRect(); return { id: b.getAttribute('data-testid'), aria: b.getAttribute('aria-label'),
        中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; })) };
} catch (e) { 键盘路径.err = String(e).slice(0, 200); }
console.log('键盘路径 =', JSON.stringify(键盘路径, null, 1));
await p.keyboard.press('Escape'); await p.waitForTimeout(600);
await b.close();

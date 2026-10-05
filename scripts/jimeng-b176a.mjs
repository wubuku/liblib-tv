// 批次 176 a 轮：**全画布禁用态普查**（灰的东西 + 逐字禁用原因）。
//
// 承接批次 175：菜单项的「禁用原因写在第二个 SPAN 里」这条规律，
// 手册目前只在上传流程（assets-and-upload.md）与节点右键菜单零星记过几条。
// 用户真正会问的是一句：**「为什么这个按钮是灰的？」**
//
// 本轮做**静态普查**（不开浮层）：页面上所有
//   aria-disabled="true" / :disabled / [data-disabled] / 灰字（text 透明度低）
// 的可见元素，连同它们所在的面板与**逐字原因文案**。
// ⚠️ 立规 48：**浮层里的禁用项要单独一轮**（浮层关闭时它们不在 DOM 里）。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '176a' };
await settle(p, R);
await p.mouse.move(1250, 10); await p.waitForTimeout(600);

rec.总览 = await p.evaluate(() => ({
  元素总数: document.querySelectorAll('body *').length,
  ariaDisabled: document.querySelectorAll('[aria-disabled="true"]').length,
  nativeDisabled: document.querySelectorAll('button:disabled,input:disabled,[disabled]').length,
  dataDisabled: document.querySelectorAll('[data-disabled],[data-state="disabled"]').length,
  浮层数: Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox],[data-testid$=-popover],[data-testid$=panel]'))
    .filter((m) => m.getBoundingClientRect().width > 1).length,
}));

rec.禁用元素 = await p.evaluate(() => {
  const 面 = (e) => {
    const f = e.closest('[role=dialog],[role=menu],[role=listbox],[data-testid$=-popover],[data-testid$=panel],[data-testid=canvas-top-bar],[data-testid=canvas-fixed-toolbar-left-rail],[data-testid=canvas-bottom-dock]');
    if (f) return f.getAttribute('data-testid') || f.getAttribute('aria-label') || f.tagName.toLowerCase();
    const t = e.closest('.react-flow__node');
    if (t) return 'node:' + (t.querySelector('[data-testid="flow-node-title"]')?.innerText || '').trim().split('\n')[0];
    return '(页面本体)';
  };
  const 出 = [];
  const seen = new Set();
  for (const e of document.querySelectorAll('[aria-disabled="true"],button:disabled,input:disabled,[disabled],[data-state="disabled"]')) {
    const r = e.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) continue;
    if (getComputedStyle(e).display === 'none' || getComputedStyle(e).visibility === 'hidden') continue;
    const 键 = `${e.getAttribute('data-testid')}|${e.getAttribute('aria-label')}|${面(e)}`;
    if (seen.has(键)) continue; seen.add(键);
    const cs = getComputedStyle(e);
    出.push({
      所在: 面(e),
      标签: e.tagName.toLowerCase(),
      testid: e.getAttribute('data-testid'),
      aria: e.getAttribute('aria-label'),
      文字: (e.innerText || '').trim().replace(/\n/g, ' | ').slice(0, 60),
      描述: e.getAttribute('aria-describedby'),
      盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      颜色: cs.color, 光标: cs.cursor, 不透明度: cs.opacity,
      周围文字: (() => { const p2 = e.parentElement; return p2 ? (p2.innerText || '').trim().replace(/\n/g, ' | ').slice(0, 80) : null; })(),
    });
  }
  return 出;
});

// 顺带：页面上所有 aria-describedby 指向的「原因说明」元素（不只禁用的）
rec.原因说明宿主 = await p.evaluate(() => {
  const ids = new Set();
  for (const e of document.querySelectorAll('[aria-describedby]')) (e.getAttribute('aria-describedby') || '').split(/\s+/).filter(Boolean).forEach((i) => ids.add(i));
  const 出 = [];
  for (const id of ids) {
    const n = document.getElementById(id); if (!n) continue;
    const r = n.getBoundingClientRect();
    出.push({ id, 文字: (n.innerText || '').trim().slice(0, 80), 有面积: r.width > 1 && r.height > 1,
      class: typeof n.className === 'string' ? n.className.slice(0, 80) : null, 被几个元素描述: document.querySelectorAll(`[aria-describedby~="${id}"]`).length });
  }
  return 出;
});

rec.基线 = { 状态行: await R.status(), 积分: await R.credits(), 缩放: await R.zoom() };
console.log(JSON.stringify(rec, null, 1));
process.exit(0);

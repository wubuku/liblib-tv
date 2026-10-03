// 批次 121 · c 轮：诊断「⊕ 按钮被 handle 盖住」到底是怎么回事。
//
// 🔴 b3 轮的中断点：在 after ⊕ 按钮自己的矩形 `[770,310,36,36]` 里**逐点扫描**，
//   **一个能命中它自己的点都没有** —— 每一个点的 `elementFromPoint` 都返回
//   `DIV[data-testid="flow-node-source-handle"]`。
//   ⇒ 护栏④又一次正确地拦下了点击（这是本批第二次被它拦下）。
//
// 🔑 但这里有个**真问题**，不是脚本问题：
//   批次 91 记的是「手柄元素本体 `pointer-events: none`，热区在 `::before`（`40×80` canvas）」，
//   而 `elementFromPoint` **不考虑伪元素** —— 命中 ::before 时它返回**宿主元素**。
//   所以「elementFromPoint 返回 handle」与「handle 本体是 `pointer-events:none`」**并不矛盾**。
//   ⇒ 那这个 ⊕ 按钮**到底还能不能点**？它是不是 handle 的**子元素**？
//     手册说点 ⊕ 会弹「添加节点」菜单 —— 那个点击**事件到底挂在谁身上**？
//
// 本轮只读诊断：handle 与 ⊕ 按钮的 DOM 关系、pointer-events 实测、命中链。
// （读完再决定「怎么点」，不在本轮动手。）
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'c' };
const save = () => writeFileSync(new URL('./_tmp-b121c.json', import.meta.url), JSON.stringify(out, null, 1));

const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);
out.start = { zoom: await zoom(), status: await status() };
log('起点：', JSON.stringify(out.start));

out.diag = await p.evaluate((id) => {
  const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
  if (!n) return { __err: 'gone' };
  const r = (e) => { const q = e.getBoundingClientRect(); return [q.x, q.y, q.width, q.height].map(Math.round); };
  const pe = (e, pseudo) => getComputedStyle(e, pseudo || null).pointerEvents;
  const btn = n.querySelector('[data-testid="flow-node-source-connection-menu-button"], [aria-label^="Create connected node after"]');
  const handle = n.querySelector('[data-testid="flow-node-source-handle"]');
  const desc = (e) => e ? { tag: e.tagName, tid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'),
    cls: (e.getAttribute('class') || '').toString().slice(0, 90), 矩形: r(e), pe本体: pe(e), peBefore: pe(e, '::before'), peAfter: pe(e, '::after'),
    opacity: getComputedStyle(e).opacity, z: getComputedStyle(e).zIndex, pos: getComputedStyle(e).position } : null;
  // before 伪元素的实际盒子
  let beforeBox = null;
  if (handle) {
    const cs = getComputedStyle(handle, '::before');
    beforeBox = { content: cs.content, w: cs.width, h: cs.height, top: cs.top, left: cs.left, pos: cs.position, pe: cs.pointerEvents };
  }
  // 命中链：从按钮中心往上，elementFromPoint 给谁
  let hitChain = null;
  if (btn) {
    const br = btn.getBoundingClientRect();
    const cx = Math.round(br.x + br.width / 2), cy = Math.round(br.y + br.height / 2);
    const el = document.elementFromPoint(cx, cy);
    hitChain = { 点: [cx, cy], 命中: el ? { tag: el.tagName, tid: el.getAttribute('data-testid'), cls: (el.className || '').toString().slice(0, 60) } : null,
      命中在按钮内: el ? (el === btn || btn.contains(el)) : false, 命中在handle内: el && handle ? (el === handle || handle.contains(el)) : null };
  }
  // 按钮是不是 handle 的后代？
  const relation = { 按钮存在: !!btn, handle存在: !!handle,
    按钮在handle内: btn && handle ? handle.contains(btn) : null,
    handle在按钮内: btn && handle ? btn.contains(handle) : null,
    按钮父: btn ? btn.parentElement.tagName + ' tid=' + btn.parentElement.getAttribute('data-testid') : null,
    handle父: handle ? handle.parentElement.tagName + ' tid=' + handle.parentElement.getAttribute('data-testid') : null,
    两者共同祖先: (() => { if (!btn || !handle) return null; let c = btn; while (c && !c.contains(handle)) c = c.parentElement; return c ? c.tagName + ' tid=' + c.getAttribute('data-testid') : null; })() };
  return { 节点矩形: r(n), 按钮: desc(btn), handle: desc(handle), before伪元素盒子: beforeBox, 命中链: hitChain, 关系: relation,
    节点内全部handle: Array.from(n.querySelectorAll('.react-flow__handle')).map((h) => ({ tid: h.getAttribute('data-testid'), 矩形: r(h), pe本体: pe(h), peBefore: pe(h, '::before'), cls: (h.getAttribute('class') || '').toString().slice(0, 60) })),
    节点内全部连接菜单钮: Array.from(n.querySelectorAll('[data-testid$="connection-menu-button"]')).map((x) => ({ tid: x.getAttribute('data-testid'), aria: x.getAttribute('aria-label'), 矩形: r(x), pe本体: pe(x) })) };
}, 'node_5k3gf1n51s');

log('\n=== 关系 ===');
log(JSON.stringify(out.diag.关系, null, 1));
log('\n=== 按钮 ===');
log(JSON.stringify(out.diag.按钮, null, 1));
log('\n=== handle ===');
log(JSON.stringify(out.diag.handle, null, 1));
log('\n=== ::before 盒子 ===');
log(JSON.stringify(out.diag.before伪元素盒子, null, 1));
log('\n=== 命中链 ===');
log(JSON.stringify(out.diag.命中链, null, 1));
log('\n=== 节点内全部 handle ===');
out.diag.节点内全部handle.forEach((h) => log('   ' + JSON.stringify(h)));
log('\n=== 节点内全部连接菜单钮 ===');
out.diag.节点内全部连接菜单钮.forEach((h) => log('   ' + JSON.stringify(h)));
save();
log('\nDONE c');
process.exit(0);

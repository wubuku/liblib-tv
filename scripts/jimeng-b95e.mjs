// 批次 95 · 收尾第 5 轮：**四格受控对照**（悬停 / 悬停+单击 / 悬停+右键 / 菜单关掉），
// 外加把 `node_ce47a7tnzq` 真删掉。
//
// 🔴 上一轮（b95d）自我推翻：它 click 之后读控件树，**10 个 testid 全 null**、`node-toolbar` 命中 0；
//     而 b95c 在**右键之后**读到的是全套（resize 8 向 + outline + host + 两层 toolbar + 菜单）。
//     ⇒ 「文本节点选中态有 resize 控件」这个说法**站不住**：至少在
//     「click 之后不右键」这个状态下它们不在 DOM 里。到底是 hover 触发、还是右键触发，本轮分清楚。
//
// 每一格都回读前置条件（selected 类 / 菜单开合 / 控件计数），不符就照实记，不猜。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const ID = 'node_ce47a7tnzq';
const out = { at: new Date().toISOString(), target: ID, cells: [] };

const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const nodeN = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]);
const selN = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const pointerToolState = () => p.evaluate(() => {
  const b = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]');
  if (!b) return null;
  return { aria: b.getAttribute('aria-label'), pressed: b.getAttribute('aria-pressed'), cls: (b.className || '').toString().slice(0, 60) }; });

// 一次读全：控件树 + 选中态 + 菜单开合 + 编辑态（作为一格的全部观测量）
const read = (cell) => p.evaluate((c) => {
  const n = document.querySelector('.react-flow__node[data-id="' + c.id + '"]');
  const cnt = (t) => document.querySelectorAll(`[data-testid="${t}"]`).length;
  const cntRole = (r) => document.querySelectorAll(`[role="${r}"]`).length;
  const g = (t) => { const e = document.querySelector(`[data-testid="${t}"]`); if (!e) return null;
    const r = e.getBoundingClientRect();
    return `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`; };
  return {
    cell: c.cell,
    nodePresent: !!n,
    hasSelectedClass: n ? n.classList.contains('selected') : null,
    selectedIds: Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id')),
    menuOpen: !!document.querySelector('[data-testid="canvas-context-menu"]'),
    menuItems: cntRole('menuitem'),
    editable: document.querySelectorAll('[contenteditable="true"],.ProseMirror').length,
    pointerTool: (() => { const t = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]');
      return t ? { aria: t.getAttribute('aria-label'), pressed: t.getAttribute('aria-pressed') } : null; })(),
    tids: {
      resizeControls: cnt('text-node-resize-controls'), outline: cnt('text-node-selection-outline'),
      chromeHost: cnt('node-feature-chrome-host'), nodeToolbar: cnt('node-toolbar'),
      featureHost: cnt('node-toolbar-feature-host'), selToolbar: cnt('selection-context-toolbar'),
      selSurface: cnt('selection-context-toolbar-surface'), popupHost: cnt('selection-context-toolbar-popup-host'),
      editorMenu: cnt('canvas-editor-menu'), srcConnBtn: cnt('flow-node-source-connection-menu-button'),
    },
    geo: { resizeControls: g('text-node-resize-controls'), outline: g('text-node-selection-outline'),
      selSurface: g('selection-context-toolbar-surface'), selToolbar: g('selection-context-toolbar'),
      nodeToolbar: g('node-toolbar'), editorMenu: g('canvas-editor-menu') },
  };
}, cell);

const pt = await p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return null;
  const r = n.getBoundingClientRect();
  for (let fx = 0.05; fx <= 0.95; fx += 0.05) for (let fy = 0.05; fy <= 0.95; fy += 0.05) {
    const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
    if (x < 0 || y < 0 || x > 1280 || y > 720) continue;
    if (document.elementFromPoint(x, y)?.closest('.react-flow__node') === n) return { x, y };
  }
  return null;
}, ID);
out.pt = pt;
out.pointerToolAtStart = await pointerToolState();
log('落点', JSON.stringify(pt), '｜指针工具', JSON.stringify(out.pointerToolAtStart));
if (!pt) { log('🔴 节点已不在'); writeFileSync(new URL('./_tmp-b95e.json', import.meta.url), JSON.stringify(out, null, 1)); await b.close(); process.exit(0); }

out.cells.push(await read({ cell: 'g0-baseline(点之前)', id: ID }));

// 格 1：只悬停，不点
await p.mouse.move(pt.x, pt.y);
await p.waitForTimeout(1200);
out.cells.push(await read({ cell: 'g1-hover-only', id: ID }));

// 格 2：悬停态下单击选中
await p.mouse.click(pt.x, pt.y);
await p.waitForTimeout(1200);
out.cells.push(await read({ cell: 'g2-hover+click(selected)', id: ID }));

// 格 3：悬停态下右键
await p.mouse.move(pt.x, pt.y);
await p.waitForTimeout(250);
await p.mouse.down({ button: 'right' });
await p.waitForTimeout(260);
await p.mouse.up({ button: 'right' });
await p.waitForTimeout(1500);
out.cells.push(await read({ cell: 'g3-hover+rightclick(menu)', id: ID }));

// 菜单若开 ⇒ 记下逐字条目后点删除（收尾正事）
const menu = await p.evaluate(() => {
  const m = document.querySelector('[data-testid="canvas-context-menu"]');
  if (!m) return null;
  const r = m.getBoundingClientRect();
  return { screen: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
    items: Array.from(m.querySelectorAll('[role="menuitem"]')).map((x) => {
      const bb = x.getBoundingClientRect();
      return { text: x.innerText.replace(/\s+/g, ' ').trim(), w: Math.round(bb.width), h: Math.round(bb.height),
        disabled: x.getAttribute('aria-disabled') }; }) };
});
out.menuAtG3 = menu;
log('g3 菜单：', menu ? menu.items.map((i) => i.text).join(' | ') : 'null');

if (menu) {
  out.deleteClick = await p.evaluate(() => {
    const m = document.querySelector('[data-testid="canvas-context-menu"]');
    const it = Array.from(m.querySelectorAll('[role="menuitem"]'))
      .find((x) => /^删除/.test(x.innerText.replace(/\s+/g, ' ').trim()) && x.getAttribute('aria-disabled') !== 'true');
    if (!it) return 'no-item'; it.click(); return 'clicked';
  });
  await p.waitForTimeout(1900);
  out.left = (await ids()).includes(ID);
  log('点删除：', out.deleteClick, '｜仍在？', out.left);
}

// 格 4：菜单关掉之后（无论删没删成功）控件树什么样
if (!(await ids()).includes(ID)) {
  out.note = '节点已在 g3 被删除 ⇒ g4 换用另一个节点（`时间线 1`）做「菜单关掉后」的读数';
  const alt = await p.evaluate(() => { const n = document.querySelector('.react-flow__node[data-id="node_"]') ;
    const all = Array.from(document.querySelectorAll('.react-flow__node'));
    return all.map((e) => e.getAttribute('data-id')); });
  log('现存 id 抽样：', JSON.stringify(alt.slice(0, 6)));
  out.cells.push(await p.evaluate(() => ({ cell: 'g4-选后无菜单(任意节点计数)', tids: {
    nodeToolbar: document.querySelectorAll('[data-testid="node-toolbar"]').length,
    selToolbar: document.querySelectorAll('[data-testid="selection-context-toolbar"]').length,
    resizeControls: document.querySelectorAll('[data-testid="text-node-resize-controls"]').length,
    menuOpen: !!document.querySelector('[data-testid="canvas-context-menu"]'),
    editorMenu: document.querySelectorAll('[data-testid="canvas-editor-menu"]').length } })));
}

out.end = { nodes: await nodeN(), sel: await selN(), left: (await ids()).filter((x) => ['node_ce47a7tnzq', 'node_tjf3grfajp'].includes(x)) };
log('终态：', JSON.stringify(out.end));
for (const c of out.cells) log(`${c.cell}: sel=${JSON.stringify(c.selectedIds)} menu=${c.menuOpen} resize=${c.tids?.resizeControls} nt=${c.tids?.nodeToolbar} ed=${c.editable}`);
writeFileSync(new URL('./_tmp-b95e.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();

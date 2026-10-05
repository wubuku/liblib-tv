// 批次 194 a 轮：查清批次 190 记的那条「文本节点上『复制 ⌘C』禁用、原因逐字
// `画布编辑尚未准备就绪`」——**触发条件是什么**（190 只记了现象，注「机制未隔离」）。
//
// 🔑 假设：「画布编辑尚未准备就绪」里的**「画布编辑」指的是全局的编辑会话状态**，
//   而不是一个节点的属性。若成立，则：
//     · 从未编辑过的节点上右键 —— 也应该是这条原因（否则就不是「编辑」相关）；
//     · 进过编辑态再退出来 —— 原因**可能变**（会话已就绪）。
//   证法：四个受控臂，逐项读右键菜单的 `aria-disabled` 与禁用原因的 `title` / `aria-label`。
import fs from 'node:fs';
import { openCanvas, readers, setZoom, settle } from './jimeng-b135-lib.mjs';

const OUT = '/tmp/b194a.json';
const 记 = { 轮次: 'b194a', 假设: '「画布编辑尚未准备就绪」指向全局编辑会话状态', 臂: [], 收尾: null };
const save = () => fs.writeFileSync(OUT, JSON.stringify(记, null, 1));

const 读菜单 = (p) => p.evaluate(() => Array.from(document.querySelectorAll('[role=menuitem]')).map((m) => {
  const cs = getComputedStyle(m);
  return { 文字: (m.innerText || '').replace(/\s+/g, ' ').trim(),
    ariaDisabled: m.getAttribute('aria-disabled'),
    dataDisabled: m.getAttribute('data-disabled'),
    title: m.getAttribute('title'),
    ariaLabel: m.getAttribute('aria-label'),
    testid: m.getAttribute('data-testid'),
    cursor: cs.cursor,
    颜色: cs.color,
    屏上: (({ width, height, x, y }) => [Math.round(width), Math.round(height), Math.round(x), Math.round(y)])(m.getBoundingClientRect()) };
}));
const 关菜单 = async (p) => { await p.keyboard.press('Escape'); await p.waitForTimeout(700); };
const 点标题 = async (p, nid) => {
  const pt = await p.evaluate((n) => { const t = document.querySelector(`.react-flow__node[data-id="${n}"] [data-testid="flow-node-title"]`);
    if (!t) return null; const r = t.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, nid);
  if (!pt) return false;
  await p.mouse.click(pt[0], pt[1]); await p.waitForTimeout(900);
  return true;
};
const 右键标题 = async (p, nid) => {
  const pt = await p.evaluate((n) => { const t = document.querySelector(`.react-flow__node[data-id="${n}"] [data-testid="flow-node-title"]`);
    if (!t) return null; const r = t.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, nid);
  if (!pt) return false;
  await p.mouse.click(pt[0], pt[1], { button: 'right' }); await p.waitForTimeout(1000);
  return true;
};
const 编辑器在 = (p) => p.evaluate(() => ({ 编辑面数: document.querySelectorAll('.tiptap.ProseMirror, [contenteditable="true"]').length,
  节点内contenteditable: document.querySelectorAll('.react-flow__node [contenteditable]').length,
  工具条: !!document.querySelector('[data-testid="text-editor-toolbar"]'),
  焦点: (() => { const a = document.activeElement; if (!a) return null;
    return a.tagName + (a.getAttribute('aria-label') ? `[aria=${a.getAttribute('aria-label')}]` : '') + (a.getAttribute('data-testid') ? `[${a.getAttribute('data-testid')}]` : ''); })() }));

const 文本 = 'node_5gftn3dnt1';      // 文本 3
const 视频 = 'node_236ctpehgg';      // 视频 1

const { b, p } = await openCanvas();
const R = readers(p);
await settle(p, R);
const 基线 = { ids: await R.ids(), credits: await R.credits() };

async function 臂(序, 名, 节点id, 前置) {
  await 关菜单(p);
  const 前 = await 编辑器在(p);
  if (前置) await 前置(p, 节点id);
  const 前置后 = await 编辑器在(p);
  const 选中 = await R.selCount();
  const 弹了 = await 右键标题(p, 节点id);
  const 菜单 = 弹了 ? await 读菜单(p) : [];
  记.臂.push({ 序, 名, 节点id, 前置: !!前置, 前置前编辑器: 前, 前置后编辑器: 前置后, 选中,
    菜单弹出: 菜单.length > 0, 菜单项数: 菜单.length, 菜单,
    阳性守卫: { 通过: 菜单.length > 0, 判据: `菜单项数 = ${菜单.length}` } });
  const 复制 = 菜单.find((m) => m.文字.startsWith('复制 ') || m.文字 === '复制');
  console.log(`臂${序} ${名}：菜单${菜单.length}项 复制项=${复制 ? JSON.stringify({ 文字: 复制.文字, ariaDisabled: 复制.ariaDisabled, title: 复制.title, cursor: 复制.cursor }) : '（无）'}`);
  save();
}

// 臂 1：文本节点，从未编辑过，直接右键
await 臂(1, '文本节点 · 从未编辑 · 直接右键', 文本, null);
// 臂 2：视频节点，从未编辑过，直接右键（对照：与节点类型有关吗）
await 臂(2, '视频节点 · 从未编辑 · 直接右键（对照）', 视频, null);
// 臂 3：文本节点 → 双击进正文编辑态 → Esc 退回 → 右键
await 臂(3, '文本节点 · 进过编辑态并 Esc 退出 · 再右键', 文本, async (pg, nid) => {
  const pt = await pg.evaluate((n) => { const t = document.querySelector(`.react-flow__node[data-id="${n}"] [data-testid="flow-node-title"]`);
    const r = t.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, nid);
  await pg.mouse.dblclick(pt[0], pt[1]); await pg.waitForTimeout(2600);
  await pg.keyboard.press('Escape'); await pg.waitForTimeout(1200);
});
// 臂 4：文本节点 → 双击进正文编辑态 → **不退出**，直接右键（手册说编辑态右键弹不出来）
await 臂(4, '文本节点 · 停在编辑态 · 直接右键', 文本, async (pg, nid) => {
  const pt = await pg.evaluate((n) => { const t = document.querySelector(`.react-flow__node[data-id="${n}"] [data-testid="flow-node-title"]`);
    const r = t.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, nid);
  await pg.mouse.dblclick(pt[0], pt[1]); await pg.waitForTimeout(2600);
});

const ids = await R.ids();
记.收尾 = { 状态行: await R.status(), 选中: await R.selCount(), credits: await R.credits(), 节点数: ids.length,
  残留: ids.filter((x) => !基线.ids.includes(x)), 丢失: 基线.ids.filter((x) => !ids.includes(x)) };
await setZoom(p, 26); await p.waitForTimeout(500);
记.收尾.zoom = await R.zoom();
save();
console.log('收尾 =', JSON.stringify(记.收尾));
await b.close();
console.log('写出', OUT);

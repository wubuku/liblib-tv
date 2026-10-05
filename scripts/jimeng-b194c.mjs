// 批次 194 c 轮：a/b 两轮五臂都读到「复制 ⌘ C」**可用**，「刚创建」也被排除。
// 本轮按**批次 190 的原始操作顺序**复现一次：
//   ① 先右键文本节点的**正文区**（批次 190 c 轮实测：菜单一个项都弹不出来）
//   ② 紧接着右键**标题行**（批次 190 d 轮实测：弹出完整 7 项，且读到「复制」禁用、
//      原因逐字「画布编辑尚未准备就绪」）
// 假设：① 那次失败的右键**把画布带进了某种编辑会话的中间态**，② 的菜单因此能弹，
//      但「复制」因为「画布编辑尚未就绪」而禁用 ⇒ **那三个字是时序状态，不是节点属性**。
import fs from 'node:fs';
import { openCanvas, readers, setZoom, settle } from './jimeng-b135-lib.mjs';

const OUT = '/tmp/b194c.json';
const 记 = { 轮次: 'b194c', 顺序: '先右键正文区 → 紧接着右键标题行', 读数: [], 收尾: null };
const save = () => fs.writeFileSync(OUT, JSON.stringify(记, null, 1));
const 读菜单 = (p) => p.evaluate(() => Array.from(document.querySelectorAll('[role=menuitem]')).map((m) => {
  const cs = getComputedStyle(m);
  return { 文字: (m.innerText || '').replace(/\s+/g, ' ').trim(), ariaDisabled: m.getAttribute('aria-disabled'),
    title: m.getAttribute('title'), cursor: cs.cursor, 颜色: cs.color,
    title属性全集: Array.from(m.querySelectorAll('[title]')).map((e) => e.getAttribute('title')) }; }));
const 编辑器态 = (p) => p.evaluate(() => ({ 编辑面: document.querySelectorAll('.tiptap.ProseMirror, [contenteditable="true"]').length,
  工具条: !!document.querySelector('[data-testid="text-editor-toolbar"]'),
  焦点: (() => { const a = document.activeElement; return a ? a.tagName + (a.getAttribute('aria-label') ? `[${a.getAttribute('aria-label')}]` : '') +
    (a.getAttribute('data-testid') ? `[${a.getAttribute('data-testid')}]` : '') : null; })() }));

const TID = 'node_5gftn3dnt1';  // 文本 3
const { b, p } = await openCanvas();
const R = readers(p);
await settle(p, R);
const 基线 = { ids: await R.ids(), credits: await R.credits() };
{
  const 空 = await p.evaluate(() => { const ns = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getBoundingClientRect());
    for (let y = 100; y < innerHeight - 100; y += 15) for (let x = 330; x < innerWidth - 350; x += 15) {
      const h = document.elementFromPoint(x, y);
      if (h && h.classList && h.classList.contains('react-flow__pane') && !ns.some((r) => x >= r.x && x <= r.right && y >= r.y && y <= r.bottom)) return [x, y]; }
    return null; });
  if (空) { await p.mouse.click(空[0], 空[1]); await p.waitForTimeout(900); }
}
// 先把节点取景到画面里
{
  const btn = await p.evaluate(() => { const a = Array.from(document.querySelectorAll('BUTTON[data-testid="canvas-panel-launcher"]'))
    .find((x) => (x.getAttribute('aria-label') || '') === '搜索'); const r = a.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  await p.mouse.click(btn[0], btn[1]); await p.waitForTimeout(1100);
  const 点 = await p.evaluate(() => { const i = document.querySelector('input[aria-label="搜索"]'); const r = i.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  await p.mouse.click(点[0], 点[1]); await p.waitForTimeout(300);
  await p.keyboard.press('Meta+a'); await p.keyboard.type('文本 3'); await p.waitForTimeout(1500);
  const 行 = await p.evaluate((nid) => { const r = document.querySelector(`[data-testid="canvas-search-result-${nid}"]`);
    if (!r) return null; const q = r.getBoundingClientRect(); return [Math.round(q.x + q.width / 2), Math.round(q.y + q.height / 2)]; }, TID);
  if (行) { await p.mouse.click(行[0], 行[1]); await p.waitForTimeout(2400); }
  await p.keyboard.press('Escape'); await p.waitForTimeout(700);
}
const 位置 = await p.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`); if (!n) return null;
  const r = n.getBoundingClientRect();
  const t = n.querySelector('[data-testid="flow-node-title"]').getBoundingClientRect();
  return { 节点: [r.x, r.y, r.width, r.height], 标题行: [t.x, t.y, t.width, t.height],
    正文中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
    标题中心: [Math.round(t.x + t.width / 2), Math.round(t.y + t.height / 2)],
    完整在视口内: r.x >= 0 && r.y >= 0 && r.right <= innerWidth && r.bottom <= innerHeight };
}, TID);
console.log('位置 =', JSON.stringify(位置));
if (!位置 || !位置.完整在视口内) { console.log('节点不在视口内，停'); await b.close(); process.exit(1); }
{
  const 空 = await p.evaluate(() => { const ns = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getBoundingClientRect());
    for (let y = 100; y < innerHeight - 100; y += 15) for (let x = 330; x < innerWidth - 350; x += 15) {
      const h = document.elementFromPoint(x, y);
      if (h && h.classList && h.classList.contains('react-flow__pane') && !ns.some((r) => x >= r.x && x <= r.right && y >= r.y && y <= r.bottom)) return [x, y]; }
    return null; });
  if (空) { await p.mouse.click(空[0], 空[1]); await p.waitForTimeout(900); }
}
记.前置 = { 选中: await R.selCount(), 编辑器: await 编辑器态(p) };

// ① 右键正文区（不做任何等待，看紧接下一拍的状态）
await p.mouse.click(位置.正文中心[0], 位置.正文中心[1], { button: 'right' });
await p.waitForTimeout(300);
const 第一拍 = { 菜单项数: await p.evaluate(() => document.querySelectorAll('[role=menuitem]').length), 编辑器: await 编辑器态(p) };
// ② 紧接着右键标题行
await p.mouse.click(位置.标题中心[0], 位置.标题中心[1], { button: 'right' });
await p.waitForTimeout(900);
const 菜单 = await 读菜单(p);
const 第二拍 = { 菜单项数: 菜单.length, 菜单, 编辑器: await 编辑器态(p),
  全页找那句话: await p.evaluate(() => ({
    body文本命中: document.body.innerText.includes('画布编辑尚未准备就绪'),
    任何元素title命中: Array.from(document.querySelectorAll('[title]')).map((e) => e.getAttribute('title')).filter((t) => t && /未准备就绪|尚未准备/.test(t)),
    任何元素aria命中: Array.from(document.querySelectorAll('[aria-label]')).map((e) => e.getAttribute('aria-label')).filter((t) => t && /未准备就绪|尚未准备/.test(t)) })) };
记.读数.push({ 第一拍, 第二拍 });
console.log('第一拍 =', JSON.stringify(第一拍));
console.log('第二拍 =', JSON.stringify({ 菜单项数: 第二拍.菜单项数, 复制: 第二拍.菜单.find((m) => m.文字.startsWith('复制 ')), 全页找那句话: 第二拍.全页找那句话 }, null, 1));
save();
await p.keyboard.press('Escape'); await p.waitForTimeout(700);

const ids = await R.ids();
记.收尾 = { 状态行: await R.status(), 选中: await R.selCount(), credits: await R.credits(), 节点数: ids.length,
  残留: ids.filter((x) => !基线.ids.includes(x)), 丢失: 基线.ids.filter((x) => !ids.includes(x)) };
{
  const 空 = await p.evaluate(() => { const ns = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getBoundingClientRect());
    for (let y = 100; y < innerHeight - 100; y += 15) for (let x = 330; x < innerWidth - 350; x += 15) {
      const h = document.elementFromPoint(x, y);
      if (h && h.classList && h.classList.contains('react-flow__pane') && !ns.some((r) => x >= r.x && x <= r.right && y >= r.y && y <= r.bottom)) return [x, y]; }
    return null; });
  if (空) { await p.mouse.click(空[0], 空[1]); await p.waitForTimeout(900); }
}
await setZoom(p, 26); await p.waitForTimeout(500);
记.收尾.选中 = await R.selCount();
记.收尾.zoom = await R.zoom();
save();
console.log('收尾 =', JSON.stringify(记.收尾));
await b.close();
console.log('写出', OUT);

// 批次 194 b 轮：a 轮**证伪了批次 190 的那条读数** —— 三个非编辑臂里
//   「复制 ⌘ C」全是**可用**的（`aria-disabled = null`、`cursor: pointer`、`title = 复制 (⌘ C)`），
//   而停在编辑态时右键菜单**一个项都弹不出来**（0 项，与手册既有结论一致）。
//
// ⇒ 190 读到的「禁用 + 原因逐字『画布编辑尚未准备就绪』」必然发生在别的状态上。
//   那句原因字面上指向「**画布编辑还没就绪**」，而 190 那轮正好有一个**刚 ⌘V 粘出来的文本节点**
//   （正文是哨兵串）。本轮验「**是不是刚创建的节点**」：
//     臂 5 粘出后**立刻**右键   臂 6 粘出后**等 6 秒**再右键
//   若 5 禁用、6 可用 ⇒ 变量是「节点刚创建、内容还没就绪」；
//   若两者都可用 ⇒ 190 那次的触发条件仍未查明（按纪律只记现象）。
import fs from 'node:fs';
import { openCanvas, readers, setZoom, settle } from './jimeng-b135-lib.mjs';

const OUT = '/tmp/b194b.json';
const 记 = { 轮次: 'b194b', 哨兵: 'JIMENG-B194-SENTINEL', 臂: [], 收尾: null, 清理: [] };
const save = () => fs.writeFileSync(OUT, JSON.stringify(记, null, 1));
const 读菜单 = (p) => p.evaluate(() => Array.from(document.querySelectorAll('[role=menuitem]')).map((m) => {
  const cs = getComputedStyle(m);
  return { 文字: (m.innerText || '').replace(/\s+/g, ' ').trim(), ariaDisabled: m.getAttribute('aria-disabled'),
    title: m.getAttribute('title'), cursor: cs.cursor, 颜色: cs.color }; }));
const 全部菜单信息 = (p) => p.evaluate(() => {
  const a = document.querySelector('[aria-label="画布编辑尚未准备就绪"]');
  const 标题栏 = Array.from(document.querySelectorAll('[title]')).map((e) => e.getAttribute('title')).filter((t) => t && /未准备|就绪|ready/i.test(t));
  return { 有aria标签的元素: !!a, title里带就绪字的: 标题栏,
    可见文本里有画布编辑尚未准备就绪: document.body.innerText.includes('画布编辑尚未准备就绪') };
});

const { b, p } = await openCanvas();
const R = readers(p);
await settle(p, R);
const 基线 = { ids: await R.ids(), credits: await R.credits() };
// 先把上一个脚本留下的选中态清掉
{
  const 空 = await p.evaluate(() => { const ns = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getBoundingClientRect());
    for (let y = 100; y < innerHeight - 100; y += 15) for (let x = 330; x < innerWidth - 350; x += 15) {
      const h = document.elementFromPoint(x, y);
      if (h && h.classList && h.classList.contains('react-flow__pane') && !ns.some((r) => x >= r.x && x <= r.right && y >= r.y && y <= r.bottom)) return [x, y]; }
    return null; });
  if (空) { await p.mouse.click(空[0], 空[1]); await p.waitForTimeout(900); }
}

await p.evaluate(() => navigator.clipboard.writeText('JIMENG-B194-SENTINEL'));
const 选中一个 = await p.evaluate(() => { const n = document.querySelector('.react-flow__node-video') || document.querySelector('.react-flow__node');
  const t = n.querySelector('[data-testid="flow-node-title"]'); const r = t.getBoundingClientRect();
  return { id: n.getAttribute('data-id'), 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; });
await p.mouse.click(选中一个.点[0], 选中一个.点[1]); await p.waitForTimeout(900);
const ids0 = await R.ids();
await p.keyboard.press('Meta+v'); await p.waitForTimeout(600);
const ids1 = await R.ids();
const 新id = ids1.find((x) => !ids0.includes(x));
记.粘贴 = { 选中: 选中一个.id, 节点数: [ids0.length, ids1.length], 新id, 阳性守卫: { 通过: !!新id, 判据: `节点数 ${ids0.length} → ${ids1.length}` } };
console.log('粘贴 =', JSON.stringify(记.粘贴));
save();
if (!新id) { console.log('粘贴没生效，后续无效臂'); await b.close(); process.exit(1); }

// 臂 5：立刻右键新节点的标题行
{
  const pt = await p.evaluate((nid) => { const t = document.querySelector(`.react-flow__node[data-id="${nid}"] [data-testid="flow-node-title"]`);
    if (!t) return null; const r = t.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, 新id);
  if (pt) { await p.mouse.click(pt[0], pt[1], { button: 'right' }); await p.waitForTimeout(900); }
  const 菜单 = pt ? await 读菜单(p) : [];
  记.臂.push({ 序: 5, 名: '刚 ⌘V 粘出的文本节点 · 立刻右键', 菜单项数: 菜单.length, 菜单, 附加: pt ? await 全部菜单信息(p) : null,
    阳性守卫: { 通过: 菜单.length > 0, 判据: `菜单项数 = ${菜单.length}` } });
  console.log('臂5 菜单项数 =', 菜单.length, '| 复制 =', JSON.stringify(菜单.find((m) => m.文字.startsWith('复制 ')) || null));
  save();
  await p.keyboard.press('Escape'); await p.waitForTimeout(700);
}
// 臂 6：等 6 秒后再右键同一个节点
{
  await p.waitForTimeout(6000);
  const pt = await p.evaluate((nid) => { const t = document.querySelector(`.react-flow__node[data-id="${nid}"] [data-testid="flow-node-title"]`);
    if (!t) return null; const r = t.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, 新id);
  if (pt) { await p.mouse.click(pt[0], pt[1], { button: 'right' }); await p.waitForTimeout(900); }
  const 菜单 = pt ? await 读菜单(p) : [];
  记.臂.push({ 序: 6, 名: '同一个新节点 · 等 6 秒后右键', 菜单项数: 菜单.length, 菜单, 附加: pt ? await 全部菜单信息(p) : null,
    阳性守卫: { 通过: 菜单.length > 0, 判据: `菜单项数 = ${菜单.length}` } });
  console.log('臂6 菜单项数 =', 菜单.length, '| 复制 =', JSON.stringify(菜单.find((m) => m.文字.startsWith('复制 ')) || null));
  await p.keyboard.press('Escape'); await p.waitForTimeout(700);
  save();
}

// 收尾：把新节点删净
{
  const pt = await p.evaluate((nid) => { const t = document.querySelector(`.react-flow__node[data-id="${nid}"] [data-testid="flow-node-title"]`);
    if (!t) return null; const r = t.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, 新id);
  if (pt) {
    await p.mouse.click(pt[0], pt[1]); await p.waitForTimeout(600);
    await p.mouse.click(pt[0], pt[1], { button: 'right' }); await p.waitForTimeout(900);
    const bb = await p.evaluateHandle(() => Array.from(document.querySelectorAll('[role=menuitem]')).find((x) => (x.innerText || '').trim().startsWith('删除')) || null);
    const el = bb.asElement();
    if (el) { const box = await el.boundingBox();
      if (box) { await p.mouse.click(box.x + box.width / 2, box.y + box.height / 2); await p.waitForTimeout(1400);
        记.清理.push({ id: 新id, 删了: true }); } else 记.清理.push({ id: 新id, 失败: '删除项无包围盒' }); }
    else { await p.keyboard.press('Escape'); 记.清理.push({ id: 新id, 失败: '菜单里没有删除项' }); }
  }
  await p.keyboard.press('Escape'); await p.waitForTimeout(700);
  const 空 = await p.evaluate(() => { const ns = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getBoundingClientRect());
    for (let y = 100; y < innerHeight - 100; y += 15) for (let x = 330; x < innerWidth - 350; x += 15) {
      const h = document.elementFromPoint(x, y);
      if (h && h.classList && h.classList.contains('react-flow__pane') && !ns.some((r) => x >= r.x && x <= r.right && y >= r.y && y <= r.bottom)) return [x, y]; }
    return null; });
  if (空) { await p.mouse.click(空[0], 空[1]); await p.waitForTimeout(900); }
  await setZoom(p, 26); await p.waitForTimeout(500);
  const ids = await R.ids();
  记.收尾 = { 状态行: await R.status(), 选中: await R.selCount(), zoom: await R.zoom(), credits: await R.credits(), 节点数: ids.length,
    残留: ids.filter((x) => !基线.ids.includes(x)), 丢失: 基线.ids.filter((x) => !ids.includes(x)) };
  save();
  console.log('收尾 =', JSON.stringify(记.收尾));
}
await b.close();
console.log('写出', OUT);

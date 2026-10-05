// 批次 183 收尾补刀第二轮：**先诊断，再删。**
//
// 上一轮补刀失败的原因已经收窄：不是「点不中」（`.selected` 读到的就是它），
// 也不是「等得不够」（4 秒）。剩下的可能：
//   甲 **节点不在视口里** —— 搜索定位把缩放改成 25%，而副本节点落在画布别处；
//       按 `⌫` 走的是键盘路径，理论上不该受视口影响，但**先确认它在哪**再动手；
//   乙 **搜索面板匹配不上 `b22-upload (2)`** —— 上一轮步骤 2 就是死在这里（`选中集` 是
//       `undefined`，说明搜索返回了「没命中」，不是删除失败）；
//   丙 **`⌫` 对「图片节点的副本」不生效** —— 批次 175/178 删掉的都是**文本节点**。
//
// 本轮顺序：① 纯诊断（几何 / 视口内外 / elementFromPoint / aria）→ ② 按诊断结果动手。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '183-补刀2' };
await settle(p, R);
await p.mouse.move(1250, 10); await p.waitForTimeout(600);

const 目标 = 'node_xjvjdw1de0';
const 存在 = (id) => p.evaluate((i) => !!document.querySelector(`.react-flow__node[data-id="${i}"]`), id);
const 节点数 = () => p.evaluate(() => document.querySelectorAll('.react-flow__node').length);
const id集 = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')).sort());

// ═════════ ① 纯诊断
rec.诊断 = await p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { 存在: false };
  const r = n.getBoundingClientRect();
  const t = n.querySelector('[data-testid="flow-node-title"]');
  const tr = t ? t.getBoundingClientRect() : null;
  const 视口 = { w: innerWidth, h: innerHeight };
  const 在视口内 = r.right > 0 && r.bottom > 0 && r.left < 视口.w && r.top < 视口.h;
  const 标题在视口内 = tr ? (tr.right > 0 && tr.bottom > 0 && tr.left < 视口.w && tr.top < 视口.h) : false;
  const cx = tr ? Math.round(tr.x + tr.width / 2) : null, cy = tr ? Math.round(tr.y + tr.height / 2) : null;
  const 落点 = (cx !== null && cx >= 0 && cx < 视口.w && cy >= 0 && cy < 视口.h)
    ? (() => { const e = document.elementFromPoint(cx, cy); return e ? { 标签: e.tagName, testid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'), class: (e.className || '').toString().slice(0, 90) } : null; })()
    : null;
  return { 存在: true, 节点框: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
    标题框: tr ? { x: Math.round(tr.x), y: Math.round(tr.y), w: Math.round(tr.width), h: Math.round(tr.height) } : null,
    视口, 在视口内, 标题在视口内, 标题中心: [cx, cy], 落点,
    节点aria: n.getAttribute('aria-label'), 节点class: (n.className || '').toString().slice(0, 120),
    transform: n.style.transform, 标题逐字: t ? (t.innerText || '').trim() : null,
    节点内img: !!n.querySelector('img'), 描述: (document.getElementById(`canvas-node-description-${i}`)?.innerText || '').trim() };
}, 目标);
rec.节点数 = await 节点数();
rec.缩放 = await R.zoom();

// ═════════ ② 动手：先把它**移进视口**（诊断说不在视口内才做），再用菜单删
const 全部 = await id集();
const 应保留 = 全部.filter((x) => x !== 目标);
rec.应保留数 = 应保留.length;
rec.动作 = [];

if (rec.诊断.存在 && !rec.诊断.标题在视口内) {
  // 用画布自己的「适配画布」把全部节点收进视野（⇧1），这是**只读导航**，不改变任何内容
  await p.mouse.move(640, 400); await p.waitForTimeout(300);
  await p.keyboard.press('Shift+Digit1'); await p.waitForTimeout(2500);
  rec.动作.push({ 动: '按 ⇧1 适配画布', 之后缩放: await R.zoom(),
    之后标题框: await p.evaluate((i) => { const t = document.querySelector(`.react-flow__node[data-id="${i}"] [data-testid="flow-node-title"]`);
      if (!t) return null; const r = t.getBoundingClientRect();
      return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height), 在视口内: r.right > 0 && r.bottom > 0 && r.left < innerWidth && r.top < innerHeight }; }, 目标) });
}

rec.动作.push({ 动: '尝试 1_菜单删除', 结果: await (async () => {
  const pt = await p.evaluate((i) => { const t = document.querySelector(`.react-flow__node[data-id="${i}"] [data-testid="flow-node-title"]`);
    if (!t) return null; const r = t.getBoundingClientRect();
    if (!(r.width > 2 && r.right > 0 && r.bottom > 0 && r.left < innerWidth && r.top < innerHeight)) return null;
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, 目标);
  if (!pt) return { 放弃: '标题仍不在视口内，不盲点' };
  await p.mouse.click(pt[0], pt[1], { button: 'right' }); await p.waitForTimeout(1500);
  const 项 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"] [role=menuitem]'))
    .find((x) => (x.innerText || '').trim().startsWith('删除'));
    if (!e) return null; const r = e.getBoundingClientRect();
    return { 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 禁用: e.getAttribute('aria-disabled') === 'true' }; });
  if (!项) return { 放弃: '菜单里没有删除项' };
  if (项.禁用) return { 放弃: '删除项是禁用态' };
  await p.mouse.click(项.点[0], 项.点[1]); await p.waitForTimeout(3000);
  return { 标题坐标: pt, 菜单项: 项, 删后还在吗: await 存在(目标), 节点数: await 节点数() };
})() });
await p.keyboard.press('Escape'); await p.waitForTimeout(700);

if (await 存在(目标)) {
  rec.动作.push({ 动: '尝试 2_选中后按 Delete（不是 Backspace）', 结果: await (async () => {
    const pt = await p.evaluate((i) => { const t = document.querySelector(`.react-flow__node[data-id="${i}"] [data-testid="flow-node-title"]`);
      if (!t) return null; const r = t.getBoundingClientRect();
      if (!(r.width > 2 && r.right > 0 && r.bottom > 0 && r.left < innerWidth && r.top < innerHeight)) return null;
      return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, 目标);
    if (!pt) return { 放弃: '标题不在视口内' };
    await p.mouse.click(pt[0], pt[1]); await p.waitForTimeout(1200);
    const 选中 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
    const 守卫 = await keyGuard(p);
    if (!选中.includes(目标)) return { 放弃: '单击没选中它', 选中, 标题坐标: pt };
    await p.keyboard.press('Delete'); await p.waitForTimeout(3000);
    return { 选中, 守卫安全: 守卫.safe, 删后还在吗: await 存在(目标), 节点数: await 节点数() };
  })() });
}

await p.reload({ waitUntil: 'domcontentloaded' }); await pinViewport(p);
const t0 = Date.now();
while (Date.now() - t0 < 40000) { if (await p.evaluate(() => document.querySelectorAll('.react-flow__node').length)) break; await p.waitForTimeout(400); }
await p.waitForTimeout(2500);
const 末 = await id集();
rec.收尾核验 = { 现在节点数: 末.length, 目标还在吗: 末.includes(目标),
  应保留的逐个还在: 应保留.filter((x) => 末.includes(x)).length, 应保留数: 应保留.length,
  意外丢失: 应保留.filter((x) => !末.includes(x)), 意外多出: 末.filter((x) => !应保留.includes(x)) };
rec.收尾 = { 状态行: await R.status(), 积分: await R.credits(), 缩放: await R.zoom(), 浮层: await R.overlays() };
console.log(JSON.stringify(rec, null, 1));
process.exit(0);

// 批次 188：**验「图片节点的 before ⊕ 到底由类型决定、还是由有没有内容决定」。**
//
// 起因是**我自己在批次 184 的一次过度概括**：
//   184 的六类型普查里，图片节点读到的 ⊕ 个数是 **1**（只有 source），
//   于是我写下「🔴 图片节点**没有** before ⊕」，并把它当成了**类型规则**登记进台账。
//   而 184 用的那个图片节点是 **`b22-upload` —— 带内容的**。
//   同一页第 468 行记着**批次 73 的实测**：
//     「带内容的图片节点，**左边的 ⊕ 在 DOM 里根本不存在**（全文档计数 0）」
//     而空图片节点那一列写的是 before ⊕「**有**」。
// ⇒ 两者其实指向同一个事实：**before ⊕ 的有无由「有没有内容」决定，不是由类型决定。**
// ⇒ 我 184 那句话的**范围写错了**（把「带内容的图片节点」写成了「图片节点」）。
//    这正是「恒真门家族」的另一个变种：**用一个实例的读数去断言整个类型。**
//
// 本轮做**同类型、有无内容**的受控对照：
//   格 A：空图片节点（左栏「图片」新建）⇒ 数 ⊕、列 testid
//   格 B：**带内容**的图片节点（现成的 `b22-upload`）⇒ 同法读
//   ⇒ 两格只差「有没有内容」。若 A 有 before、B 没有 ⇒ 变量是内容，184 那句话要收窄。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';
const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '188' };
await settle(p, R);
await p.mouse.move(1250, 10); await p.waitForTimeout(600);
const 节点数 = () => p.evaluate(() => document.querySelectorAll('.react-flow__node').length);
const id集 = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')).sort());
const 选中集 = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
const 标题坐标 = (id) => p.evaluate((i) => { const t = document.querySelector(`.react-flow__node[data-id="${i}"] [data-testid="flow-node-title"]`);
  if (!t) return null; const r = t.getBoundingClientRect();
  if (!(r.width > 2 && r.right > 0 && r.bottom > 0 && r.left < innerWidth && r.top < innerHeight)) return null;
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, id);
const 菜单删除 = async (id) => {
  if (!(await 标题坐标(id))) { await p.mouse.move(640, 400); await p.keyboard.press('Shift+Digit1'); await p.waitForTimeout(2400); }
  const pt = await 标题坐标(id); if (!pt) return { 成功: false, 原因: '标题不在视口内' };
  await p.mouse.click(pt[0], pt[1], { button: 'right' }); await p.waitForTimeout(1500);
  const 项 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"] [role=menuitem]'))
    .find((x) => (x.innerText || '').trim().startsWith('删除'));
    if (!e) return null; const r = e.getBoundingClientRect();
    return { 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 禁用: e.getAttribute('aria-disabled') === 'true' }; });
  if (!项 || 项.禁用) { await p.keyboard.press('Escape'); await p.waitForTimeout(600); return { 成功: false, 原因: '无删除项或禁用' }; }
  await p.mouse.click(项.点[0], 项.点[1]); await p.waitForTimeout(3000);
  return { 成功: !(await p.evaluate((i) => !!document.querySelector(`.react-flow__node[data-id="${i}"]`), id)) };
};
/** 选中态下数一个节点上的 ⊕（只数 DOM，不点）。 */
const 数加号 = (id) => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
  const 全部 = Array.from(n.querySelectorAll('[aria-label^="Create connected node"]'));
  return { 选中: n.classList.contains('selected'),
    '⊕个数': 全部.length,
    '⊕': 全部.map((e) => { const r = e.getBoundingClientRect();
      return { testid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'), 屏上: { w: Math.round(r.width), h: Math.round(r.height) } }; }),
    手柄: Array.from(n.querySelectorAll('.react-flow__handle')).map((e) => ({ testid: e.getAttribute('data-testid'),
      本体pe: getComputedStyle(e).pointerEvents, beforePE: getComputedStyle(e, '::before').pointerEvents })),
    节点屏上: (() => { const r = n.getBoundingClientRect(); return { w: Math.round(r.width), h: Math.round(r.height) }; })(),
    有img: !!n.querySelector('img') };
}, id);
const 前id = await id集();
rec.起点 = { 节点数: 前id.length, 积分: await R.credits(), 缩放: await R.zoom() };
try {
  // 格 B：**带内容**的图片节点（现成的）—— 先读，因为它本来就在画布上
  const 带内容 = await p.evaluate(() => { const n = document.querySelector('.react-flow__node-image'); if (!n) return null;
    const t = n.querySelector('[data-testid="flow-node-title"]');
    return { id: n.getAttribute('data-id'), 标题: t ? (t.innerText || '').trim().split('\n')[0] : null }; });
  rec.格B_带内容的图片 = 带内容;
  if (带内容) {
    const pt = await 标题坐标(带内容.id);
    if (pt) { await p.mouse.click(pt[0], pt[1]); await p.waitForTimeout(1300); }
    rec.格B_读数 = await 数加号(带内容.id);
    rec.格B_选中集 = await 选中集();
  }
  await p.keyboard.press('Escape'); await p.waitForTimeout(600);

  // 格 A：左栏「图片」新建一个**空**图片节点
  const 按钮 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[aria-label]')).find((x) => x.getAttribute('aria-label') === '图片');
    if (!e) return null; const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  rec.左栏图片按钮 = 按钮;
  if (!按钮) rec.说明 = '左栏没有「图片」按钮';
  else {
    await p.mouse.click(按钮[0], 按钮[1]); await p.waitForTimeout(4000);
    const 新增 = (await id集()).filter((i) => !前id.includes(i));
    rec.新建 = { 新增id: 新增, 节点数: await 节点数(), 积分: await R.credits(), 状态行: await R.status() };
    if (!新增.length) rec.说明 = '点了左栏「图片」但没有新节点';
    else {
      const nid = 新增[0];
      rec.格A_节点 = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
        return { aria: n?.getAttribute('aria-label'), class: (n?.className || '').toString(),
          标题: (n?.querySelector('[data-testid="flow-node-title"]')?.innerText || '').trim().split('\n')[0],
          节点内逐字: (n?.innerText || '').trim().replace(/\n/g, ' | ').slice(0, 100) }; }, nid);
      rec.格A_读数 = await 数加号(nid);
      rec.格A_选中集 = await 选中集();
      // 🔴 判据：三格的关键差只有「有没有内容」
      rec.判定 = {
        A空图片有before: !!(rec.格A_读数 && rec.格A_读数['⊕'].some((x) => x.testid === 'flow-node-target-connection-menu-button')),
        B带内容图片有before: !!(rec.格B_读数 && rec.格B_读数['⊕'].some((x) => x.testid === 'flow-node-target-connection-menu-button')),
        两格加号个数: { A: rec.格A_读数?.['⊕个数'] ?? null, B: rec.格B_读数?.['⊕个数'] ?? null },
        变量是内容而不是类型: !!(rec.格A_读数 && rec.格B_读数 && rec.格A_读数['⊕个数'] !== rec.格B_读数['⊕个数']),
      };
    }
  }
} catch (e) { rec.异常 = String(e).slice(0, 200); }
await p.keyboard.press('Escape'); await p.waitForTimeout(600);
const 现存 = await id集();
const 残留 = 现存.filter((i) => !前id.includes(i));
rec.收尾前 = { 现在节点数: 现存.length, 本轮多出: 残留 };
rec.清理 = [];
for (const id of 残留) rec.清理.push({ id, ...(await 菜单删除(id)) });
await p.keyboard.press('Escape'); await p.waitForTimeout(600);
await p.reload({ waitUntil: 'domcontentloaded' }); await pinViewport(p);
const t0 = Date.now();
while (Date.now() - t0 < 60000) { if (await p.evaluate(() => document.querySelectorAll('.react-flow__node').length)) break; await p.waitForTimeout(500); }
await p.waitForTimeout(3000);
const 末 = await id集();
rec.收尾核验 = { 现在节点数: 末.length, 起点节点数: 前id.length, 残留id: 末.filter((i) => !前id.includes(i)), 丢失id: 前id.filter((i) => !末.includes(i)), 原有仍在: 前id.filter((i) => 末.includes(i)).length };
rec.收尾 = { 状态行: await R.status(), 积分: await R.credits(), 缩放: await R.zoom(), 浮层: await R.overlays() };
console.log(JSON.stringify(rec, null, 1));
process.exit(0);

// 批次 187：**建一个主体节点**，把全册几处「主体那一行没测」的表一次关掉。
//
// 为什么值得建：画布上现存的类型只有 image / video / audio / text / timeline / external，
// **没有 `subject`**。而手册里至少三张表**都留着主体那一行的空白**：
//   ① 批次 184 新写的「哪些类型有几个 ⊕」里，`subject` 那一行标着「**未复测**」；
//   ② 「下载」类型表（批次 186 刚重写）里没有主体；
//   ③ `duplicate-delete-history` 的「保存到主体库」归属规则表里主体是其中一格。
// 建主体节点是**纯 CRUD、零成本**（左栏点一下），不触发生成、不扣积分。
//
// 读数清单（全部只读，**不点「保存到主体库」** —— 那是写操作且手册立规 20 要求不点）：
//   ① 节点本身：class / aria / 标题 / 画布尺寸 / 有几个 ⊕（各 testid 与 aria）
//   ② 右键菜单：项数、本体尺寸、逐项、「下载」在不在与禁用原因、
//      「保存到主体库」在不在（**只读，不点**）
//   ③ 选中态下手柄的 `::before` pointer-events
//
// 收尾：按 id 用菜单「删除」删掉，并核验原有 76 个 id 逐个仍在。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';
const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '187' };
await settle(p, R);
await p.mouse.move(1250, 10); await p.waitForTimeout(600);
const 节点数 = () => p.evaluate(() => document.querySelectorAll('.react-flow__node').length);
const id集 = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')).sort());
const 选中集 = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
const 标题坐标 = (id) => p.evaluate((i) => { const t = document.querySelector(`.react-flow__node[data-id="${i}"] [data-testid="flow-node-title"]`);
  if (!t) return null; const r = t.getBoundingClientRect();
  if (!(r.width > 2 && r.right > 0 && r.bottom > 0 && r.left < innerWidth && r.top < innerHeight)) return null;
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, id);
const 读菜单 = async (id) => {
  if (!(await 标题坐标(id))) { await p.mouse.move(640, 400); await p.keyboard.press('Shift+Digit1'); await p.waitForTimeout(2400); }
  const pt = await 标题坐标(id);
  if (!pt) return { 失败: '标题不在视口内' };
  const 落 = await p.evaluate((q) => { const e = document.elementFromPoint(q[0], q[1]); return e ? { 标签: e.tagName, 在节点内: !!e.closest('.react-flow__node') } : null; }, pt);
  if (!落?.在节点内) return { 失败: '落点不在节点上，不盲点', 落点: 落 };
  await p.mouse.click(pt[0], pt[1], { button: 'right' }); await p.waitForTimeout(1500);
  const m = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-context-menu"]'); if (!e) return null;
    const r = e.getBoundingClientRect();
    return { 几何: { w: Math.round(r.width), h: Math.round(r.height) },
      项: Array.from(e.querySelectorAll('[role=menuitem]')).map((i) => { const sp = Array.from(i.children).map((c) => (c.innerText || '').trim());
        return { 名: sp[0] || (i.innerText || '').trim().split('\n')[0], 禁用: i.getAttribute('aria-disabled') === 'true', 第二段: sp[1] || null,
          aria: i.getAttribute('aria-label'), 快捷键: i.getAttribute('aria-keyshortcuts') }; }) }; });
  await p.keyboard.press('Escape'); await p.waitForTimeout(800);
  if (!m) return { 失败: '菜单没开' };
  const 找 = (k) => m.项.find((x) => x.名 === k || x.名.startsWith(k) || (x.aria || '').includes(k));
  const 下 = 找('下载'), 保 = 找('保存到主体库');
  return { 几何: m.几何, 项数: m.项.length, 全部项: m.项.map((x) => ({ 名: x.名, 禁用: x.禁用, aria: x.aria, 快捷键: x.快捷键 })),
    下载: 下 ? { 在: true, 禁用: 下.禁用, 原因逐字: 下.禁用 ? 下.第二段 : null } : { 在: false },
    保存到主体库: 保 ? { 在: true, 禁用: 保.禁用, aria: 保.aria } : { 在: false } };
};
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
const 前id = await id集();
rec.起点 = { 节点数: 前id.length, 状态行: await R.status(), 积分: await R.credits(), 缩放: await R.zoom() };
try {
  const 按钮 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[aria-label]')).find((x) => x.getAttribute('aria-label') === '主体');
    if (!e) return null; const r = e.getBoundingClientRect(); return { 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 屏上: { w: Math.round(r.width), h: Math.round(r.height) } }; });
  rec.左栏主体按钮 = 按钮;
  if (!按钮) rec.说明 = '左栏没有「主体」按钮';
  else {
    await p.mouse.click(按钮.点[0], 按钮.点[1]);
    await p.waitForTimeout(4000);
    const 新增 = (await id集()).filter((i) => !前id.includes(i));
    rec.新建 = { 新增id: 新增, 节点数: await 节点数(), 状态行: await R.status() };
    if (!新增.length) rec.说明 = '点了左栏「主体」但没有新节点';
    else {
      const nid = 新增[0];
      rec.节点读数 = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
        const r = n.getBoundingClientRect();
        return { class: (n.className || '').toString(), aria: n.getAttribute('aria-label'),
          标题: (n.querySelector('[data-testid="flow-node-title"]')?.innerText || '').trim().split('\n')[0],
          节点内逐字: (n.innerText || '').trim().replace(/\n/g, ' | ').slice(0, 120),
          屏上: { w: Math.round(r.width), h: Math.round(r.height) },
          选中: n.classList.contains('selected'),
          画布几何: (() => { const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(n.style.transform || ''); return m ? { x: Math.round(parseFloat(m[1]) * 100) / 100, y: Math.round(parseFloat(m[2]) * 100) / 100 } : null; })(),
          加号按钮: Array.from(n.querySelectorAll('[aria-label^="Create connected node"]')).map((e) => { const b = e.getBoundingClientRect();
            return { testid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'), 屏上: { w: Math.round(b.width), h: Math.round(b.height) } }; }),
          手柄: Array.from(n.querySelectorAll('.react-flow__handle')).map((e) => ({ testid: e.getAttribute('data-testid'),
            本体pe: getComputedStyle(e).pointerEvents, beforePE: getComputedStyle(e, '::before').pointerEvents })) }; }, nid);
      rec.菜单 = await 读菜单(nid);
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

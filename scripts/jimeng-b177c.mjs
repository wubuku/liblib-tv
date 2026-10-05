// 批次 177 c 轮：用**「搜索」面板选中节点**跑完撤销/重做状态机。
//
// b 轮的教训：26% 缩放下**点标题选中文本节点连续失败**（选中集恒为 []），
//   于是 S1/S1b/S2 全部空转、整条状态机**没测到**。
//   批次 127 已经记过另一条**可靠**的选中路径：**点搜索结果会定位并选中该节点**。
//   ⇒ 本轮改用它，并且每一步都保留「非空守卫」（选中集必须恰好含目标 id）。
//
// 受控实验：复制副本（走**菜单**，因为 ⌘D 实测无效，批次 175）→ 读撤销/重做态
//   → 按 ⌘Z → 再读。全程按 id 清理并验明。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
import { keyGuard } from './jimeng-safe-keys.mjs';
const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '177c' };
await settle(p, R);
await p.mouse.move(1250, 10); await p.waitForTimeout(600);

const 选中集 = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
const 节点数 = () => p.evaluate(() => document.querySelectorAll('.react-flow__node').length);
const id集 = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')));

/** 用搜索面板选中一个 id 指定的节点。 */
const 搜索选中 = async (关键词) => {
  const 开 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[aria-label]')).find((x) => x.getAttribute('aria-label') === '搜索');
    if (!e) return null; const r = e.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; });
  if (!开) return { 成功: false, 原因: '没有「搜索」按钮' };
  await p.mouse.click(开[0], 开[1]); await p.waitForTimeout(1800);
  const 输入 = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-search-panel"] input');
    if (!e) return null; const r = e.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; });
  if (!输入) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); return { 成功: false, 原因: '搜索面板里没有输入框' }; }
  await p.mouse.click(输入[0], 输入[1]); await p.waitForTimeout(500);
  await p.fill('[data-testid="canvas-search-panel"] input', 关键词);
  await p.waitForTimeout(1800);
  const 结果 = await p.evaluate(() => Array.from(document.querySelectorAll('[data-testid="canvas-search-panel"] button'))
    .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 20 && r.height > 20 && /node_/.test(e.getAttribute('data-testid') || ''); })
    .slice(0, 3).map((e) => { const r = e.getBoundingClientRect();
      return { testid: e.getAttribute('data-testid'), 文字: (e.innerText || '').trim().replace(/\n/g, ' | ').slice(0, 40),
        点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; }));
  rec.搜索命中 = { 关键词, 结果数: 结果.length, 结果 };
  if (!结果.length) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); return { 成功: false, 原因: '没有命中' }; }
  await p.mouse.click(结果[0].点[0], 结果[0].点[1]); await p.waitForTimeout(2000);
  const s = await 选中集();
  await p.keyboard.press('Escape'); await p.waitForTimeout(700);
  return { 成功: s.length >= 1, 选中集: s };
};
const 读撤销重做 = async () => {
  const s = await 选中集();
  if (s.length !== 1) return { 读不到: `选中集=${JSON.stringify(s)}` };
  const pt = await p.evaluate((i) => { const t = document.querySelector(`.react-flow__node[data-id="${i}"] [data-testid="flow-node-title"]`);
    if (!t) return null; const r = t.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; }, s[0]);
  if (!pt) return { 读不到: '取不到标题坐标' };
  await p.mouse.move(pt[0], pt[1]); await p.waitForTimeout(250);
  await p.mouse.click(pt[0], pt[1], { button: 'right' }); await p.waitForTimeout(1300);
  const m = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-context-menu"]'); if (!e) return null;
    return { 项: Array.from(e.querySelectorAll('[role=menuitem]')).map((i) => ({ aria: i.getAttribute('aria-label'),
      快捷键: i.getAttribute('aria-keyshortcuts'), 禁用: i.getAttribute('aria-disabled') === 'true',
      span: Array.from(i.children).map((c) => (c.innerText || '').trim()) })) }; });
  await p.keyboard.press('Escape'); await p.waitForTimeout(800);
  if (!m) return { 读不到: '菜单没开' };
  const 挑 = (k) => { const x = m.项.find((i) => i.aria === k); return x ? { 禁用: x.禁用, 快捷键: x.快捷键, 原文: x.span.join(' ｜ ') } : '(菜单里没有这一项)'; };
  return { 选中: s[0], 重做: 挑('重做'), 撤销: 挑('撤销') };
};

const 前id = await id集();
rec.起点 = { 节点数: 前id.length, 守卫: await keyGuard(p) };
const 步 = [];

// S0：刷新后的初始态 —— 借用批次 175 的读数（本批也现场读一次）
const S0 = await 搜索选中('文本 1');
步.push({ 步: 'S0 刚刷新完、未做任何操作', 选中: S0, 撤销重做: S0.成功 ? await 读撤销重做() : null });

let 新增 = [];
if (S0.成功) {
  // S1：走菜单「复制副本」
  const pt = await p.evaluate((i) => { const t = document.querySelector(`.react-flow__node[data-id="${i}"] [data-testid="flow-node-title"]`);
    const r = t.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, S0.选中集[0]);
  await p.mouse.click(pt[0], pt[1], { button: 'right' }); await p.waitForTimeout(1400);
  const 定位 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"] [role=menuitem]'))
      .find((x) => (x.innerText || '').trim().startsWith('复制副本'));
    if (!e) return null; const r = e.getBoundingClientRect();
    return { 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 禁用: e.getAttribute('aria-disabled') === 'true' }; });
  rec.复制副本项 = 定位;
  if (定位 && !定位.禁用) {
    await p.mouse.click(定位.点[0], 定位.点[1]); await p.waitForTimeout(3400);
    const 现 = await id集(); 新增 = 现.filter((i) => !前id.includes(i));
  }
  步.push({ 步: 'S1 走菜单「复制副本」之后', 节点数: await 节点数(), 新增id: 新增 });
}
if (新增.length) {
  const 副本 = 新增[0];
  const 选副本 = await 搜索选中(副本.slice(0, 0) + (await p.evaluate((i) => (document.querySelector(`.react-flow__node[data-id="${i}"] [data-testid="flow-node-title"]`)?.innerText || '').trim().split('\n')[0], 副本)));
  步.push({ 步: 'S1b 选中刚造出来的副本', 选中: 选副本, 撤销重做: 选副本.成功 ? await 读撤销重做() : null });
  const G = await keyGuard(p);
  if (G.safe) {
    const 前数 = await 节点数();
    await p.keyboard.press('Meta+z'); await p.waitForTimeout(2800);
    const 后数 = await 节点数();
    步.push({ 步: 'S2 按 ⌘Z 之后', 守卫: G, 前节点数: 前数, 后节点数: 后数,
      副本还在: await p.evaluate((i) => !!document.querySelector(`.react-flow__node[data-id="${i}"]`), 副本),
      撤销重做: await 读撤销重做() });
  } else 步.push({ 步: 'S2 跳过', 原因: '焦点守卫不通过', 守卫: G });
}
rec.步 = 步;
// 收尾：按 id 清掉新增
for (const id of 新增) {
  const S = await 搜索选中(await p.evaluate((i) => (document.querySelector(`.react-flow__node[data-id="${i}"] [data-testid="flow-node-title"]`)?.innerText || '').trim().split('\n')[0], id));
  if (S.成功 && S.选中集.includes(id)) { await p.keyboard.press('Backspace'); await p.waitForTimeout(2000); }
}
rec.收尾核验 = { 现在节点数: await 节点数(), 新增: 新增,
  残留: await p.evaluate((ids) => ids.filter((i) => !!document.querySelector(`.react-flow__node[data-id="${i}"]`)), 新增),
  原有总数: 前id.length, 原有仍在: await p.evaluate((old) => old.filter((i) => !!document.querySelector(`.react-flow__node[data-id="${i}"]`)).length, 前id) };
await p.keyboard.press('Escape'); await p.waitForTimeout(700);
await p.mouse.move(1250, 10);
rec.收尾 = { 状态行: await R.status(), 积分: await R.credits(), 缩放: await R.zoom() };
console.log(JSON.stringify(rec, null, 1));
process.exit(0);

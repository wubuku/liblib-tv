// 批次 183 i 轮：**把「焦点是不是分水岭」这件事量清楚**，好决定能不能订正手册第 327 行。
//
// 手册现写：「从搜索面板点结果行选中的节点按 ⌫ 删不掉，**根因是焦点不在画布上**」。
// 而 183 的 5 次失败里 `keyGuard` 全部返回 `safe: true` —— 但 `safe` 的判据只是
// 「焦点不在可编辑输入面里」（能安全按字母键），**它不等于「焦点在画布上」**。
// ⇒ 不能拿 `safe` 去反驳「焦点」这条根因。必须读**完整的 `document.activeElement`**。
//
// 两格，逐格只改「选中方式」这一件事，其余（造节点、适配、焦点、等待）尽量同构：
//   格 A：点源节点 → `⌘V` → （不动）→ 读焦点 → 按 `⌫`
//   格 B：点源节点 → `⌘V` → **打开搜索面板、点结果行、按 Esc** → 读焦点 → 按 `⌫`
// 焦点读数包含：标签 / testid / class / aria / 是否在 `.react-flow` 内 / 是否在搜索面板内 /
// 逐层祖先链（取到画布或 body 为止），这样「在不在画布上」不再靠猜。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';
const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '183i' };
try {
  const g = await b.contexts()[0].newCDPSession(p);
  await g.send('Browser.grantPermissions', { permissions: ['clipboardReadWrite', 'clipboardSanitizedWrite'], origin: 'https://jimeng.jianying.com' });
  rec.剪贴板权限 = '已授予';
} catch (e) { rec.剪贴板权限 = '授予失败: ' + String(e).slice(0, 80); }
await settle(p, R);
await p.mouse.move(1250, 10); await p.waitForTimeout(600);
const 节点数 = () => p.evaluate(() => document.querySelectorAll('.react-flow__node').length);
const id集 = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')).sort());
const 选中集 = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
const 存在 = (id) => p.evaluate((i) => !!document.querySelector(`.react-flow__node[data-id="${i}"]`), id);
const 标题坐标 = (id) => p.evaluate((i) => { const t = document.querySelector(`.react-flow__node[data-id="${i}"] [data-testid="flow-node-title"]`);
  if (!t) return null; const r = t.getBoundingClientRect();
  if (!(r.width > 2 && r.right > 0 && r.bottom > 0 && r.left < innerWidth && r.top < innerHeight)) return null;
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, id);
const 写哨兵 = (s) => p.evaluate(async (t) => { try { await navigator.clipboard.writeText(t); return '写成功'; } catch (e) { return '写失败'; } }, s);
const 适配 = async () => { await p.mouse.move(640, 400); await p.waitForTimeout(250); await p.keyboard.press('Shift+Digit1'); await p.waitForTimeout(2400); };
const 菜单删除 = async (id) => {
  if (!(await 标题坐标(id))) await 适配();
  const pt = await 标题坐标(id); if (!pt) return { 成功: false, 原因: '标题不在视口内' };
  await p.mouse.click(pt[0], pt[1], { button: 'right' }); await p.waitForTimeout(1500);
  const 项 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"] [role=menuitem]'))
    .find((x) => (x.innerText || '').trim().startsWith('删除'));
    if (!e) return null; const r = e.getBoundingClientRect();
    return { 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 禁用: e.getAttribute('aria-disabled') === 'true' }; });
  if (!项 || 项.禁用) { await p.keyboard.press('Escape'); await p.waitForTimeout(600); return { 成功: false, 原因: '无删除项或禁用' }; }
  await p.mouse.click(项.点[0], 项.点[1]); await p.waitForTimeout(3000);
  return { 成功: !(await 存在(id)) };
};
/** 🔴 完整的焦点读数：不再用 keyGuard 的 safe 代替「焦点在哪」。 */
const 焦点全读 = () => p.evaluate(() => {
  const a = document.activeElement; if (!a) return { 有焦点: false };
  const 链 = []; let n = a;
  for (let i = 0; i < 12 && n && n !== document.body; i++) { n = n.parentElement; if (n) 链.push(n.tagName + (n.getAttribute?.('data-testid') ? `[${n.getAttribute('data-testid')}]` : '') + (n.getAttribute?.('class') ? '.' + String(n.getAttribute('class')).split(' ').slice(0, 2).join('.') : '')); }
  return { 有焦点: true, 标签: a.tagName, testid: a.getAttribute('data-testid'), aria: a.getAttribute('aria-label'),
    class: String(a.className || '').slice(0, 90), 是否可编辑: a.isContentEditable || ['INPUT', 'TEXTAREA'].includes(a.tagName),
    在ReactFlow内: !!a.closest('.react-flow'), 在搜索面板内: !!a.closest('[data-testid="canvas-search-panel"]'),
    在节点内: !!a.closest('.react-flow__node'), 祖先链: 链 };
});
const 前id = await id集();
rec.起点 = { 节点数: 前id.length, 积分: await R.credits(), 缩放: await R.zoom() };
const 源 = await p.evaluate(() => { const n = document.querySelector('.react-flow__node-image');
  if (!n) return null; const t = n.querySelector('[data-testid="flow-node-title"]');
  return { id: n.getAttribute('data-id'), 标题: t ? (t.innerText || '').trim().split('\n')[0] : null }; });
rec.源 = 源;
rec.格 = [];
const 跑 = async (名, 走搜索) => {
  const 行 = { 名 };
  try {
    await 适配();
    const pt = await 标题坐标(源.id);
    if (!pt) { 行.结论 = '源节点标题不在视口内'; rec.格.push(行); return; }
    await p.mouse.click(pt[0], pt[1]); await p.waitForTimeout(1200);
    行.点选后选中 = await 选中集();
    await 写哨兵(`B183I-${名}-${走搜索 ? '走搜索' : '不走搜索'}`);
    await p.keyboard.press('Meta+v'); await p.waitForTimeout(2600);
    const 新增 = (await id集()).filter((i) => !前id.includes(i));
    行.新增 = 新增;
    if (!新增.length) { 行.结论 = '⌘V 没造出节点'; rec.格.push(行); return; }
    const 目标 = 新增[0];
    行.目标aria = await p.evaluate((i) => document.querySelector(`.react-flow__node[data-id="${i}"]`)?.getAttribute('aria-label'), 目标);
    if (走搜索) {
      const 词 = 目标.replace(/^node_/, '');
      const 开 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[aria-label]')).find((x) => x.getAttribute('aria-label') === '搜索');
        const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
      await p.mouse.click(开[0], 开[1]); await p.waitForTimeout(1100);
      const 输入 = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-search-panel"] input');
        const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
      await p.mouse.click(输入[0], 输入[1]); await p.waitForTimeout(400);
      await p.fill('[data-testid="canvas-search-panel"] input', 词); await p.waitForTimeout(1500);
      const 命中 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-"]'))
        .find((x) => { const r = x.getBoundingClientRect(); return r.width > 20 && r.height > 20; });
        if (!e) return null; const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
      行.搜索命中坐标 = 命中;
      if (命中) { await p.mouse.click(命中[0], 命中[1]); await p.waitForTimeout(1400); }
      await p.keyboard.press('Escape'); await p.waitForTimeout(600);
    }
    行.按前选中集 = await 选中集();
    行.按前焦点 = await 焦点全读();
    行.按前焦点守卫 = await keyGuard(p);
    行.按前节点数 = await 节点数();
    await p.keyboard.press('Backspace'); await p.waitForTimeout(3500);
    行.删后还在吗 = await 存在(目标); 行.按后节点数 = await 节点数();
    行.结论 = 行.删后还在吗 ? '❌ ⌫ 没删掉' : '✅ ⌫ 删掉了';
    if (行.删后还在吗) 行.补救 = await 菜单删除(目标);
  } catch (e) { 行.异常 = String(e).slice(0, 180); }
  rec.格.push(行);
  await p.keyboard.press('Escape'); await p.waitForTimeout(700);
};
await 跑('A_粘贴后直接退格', false);
await 跑('B_搜索面板重选后退格', true);
await p.keyboard.press('Escape'); await p.waitForTimeout(600);
const 现存 = await id集();
rec.收尾前 = { 现在节点数: 现存.length, 本轮多出: 现存.filter((i) => !前id.includes(i)) };
rec.清理 = [];
for (const id of 现存.filter((i) => !前id.includes(i))) rec.清理.push({ id, ...(await 菜单删除(id)) });
await p.keyboard.press('Escape'); await p.waitForTimeout(600);
await p.reload({ waitUntil: 'domcontentloaded' }); await pinViewport(p);
const t0 = Date.now();
while (Date.now() - t0 < 40000) { if (await p.evaluate(() => document.querySelectorAll('.react-flow__node').length)) break; await p.waitForTimeout(400); }
await p.waitForTimeout(2500);
const 末 = await id集();
rec.收尾核验 = { 现在节点数: 末.length, 起点节点数: 前id.length, 残留id: 末.filter((i) => !前id.includes(i)),
  丢失id: 前id.filter((i) => !末.includes(i)), 原有仍在: 前id.filter((i) => 末.includes(i)).length };
rec.收尾 = { 状态行: await R.status(), 积分: await R.credits(), 缩放: await R.zoom(), 浮层: await R.overlays() };
console.log(JSON.stringify(rec, null, 1));
process.exit(0);

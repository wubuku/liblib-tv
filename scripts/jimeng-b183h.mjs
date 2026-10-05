// 批次 183 h 轮：**关掉与 175/178 的矛盾。**
//
// 已确立（2×2，7 次读数）：分水岭是**选中方式** ——
//   搜索面板选中 ＋ `⌫` ⇒ ❌ 5/5；直接点标题选中 ＋ `⌫` ⇒ ✅ 3/3。
//
// 🔴 但批次 175/178 的收尾明明是「搜索面板选中 → 按 `⌫`」且报「残留 0」。
//   有一处差别能解释：**那两批删的是「⌘V 粘贴后自动选中」的节点**，
//   搜索面板那次点击**点中的就是已经选中的那个节点**。
//   ⇒ 本轮只测这一种情形：**粘贴后什么都不点，直接按 `⌫`**。
//   成了 ⇒ 规则是「`⌫` 只在**未经搜索面板**的选中态下生效」，
//   175/178 与本批 7 次读数**全部自洽**；不成就得另找解释，如实记未定。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';
const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '183h' };
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
  const pt = await 标题坐标(id);
  if (!pt) return { 成功: false, 原因: '标题不在视口内' };
  await p.mouse.click(pt[0], pt[1], { button: 'right' }); await p.waitForTimeout(1500);
  const 项 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"] [role=menuitem]'))
    .find((x) => (x.innerText || '').trim().startsWith('删除'));
    if (!e) return null; const r = e.getBoundingClientRect();
    return { 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 禁用: e.getAttribute('aria-disabled') === 'true' }; });
  if (!项 || 项.禁用) { await p.keyboard.press('Escape'); await p.waitForTimeout(600); return { 成功: false, 原因: '无删除项或禁用' }; }
  await p.mouse.click(项.点[0], 项.点[1]); await p.waitForTimeout(3000);
  return { 成功: !(await 存在(id)) };
};
const 前id = await id集();
rec.起点 = { 节点数: 前id.length, 积分: await R.credits(), 缩放: await R.zoom() };
try {
  // 1) 选中一个源节点（这一步必须做：⌘V 需要在画布有选中态时才粘贴）
  const 源 = await p.evaluate(() => { const n = document.querySelector('.react-flow__node-image');
    if (!n) return null; const t = n.querySelector('[data-testid="flow-node-title"]');
    return { id: n.getAttribute('data-id'), 标题: t ? (t.innerText || '').trim().split('\n')[0] : null }; });
  rec.源 = 源;
  if (源) {
    await 适配();
    const pt = await 标题坐标(源.id);
    if (pt) { await p.mouse.click(pt[0], pt[1]); await p.waitForTimeout(1200); rec.源选中 = await 选中集(); }
    await 写哨兵('B183H-粘贴后直接退格');
    await p.keyboard.press('Meta+v'); await p.waitForTimeout(2600);
  }
  // 2) 🔴 **不按 Escape、不点任何东西** —— 保持「粘贴后自动选中」这一个变量
  rec.粘贴后立刻的选中集 = await 选中集();
  rec.粘贴后节点数 = await 节点数();
  const 新增 = (await id集()).filter((i) => !前id.includes(i));
  rec.新增 = 新增;
  if (新增.length) {
    const 目标 = 新增[0];
    rec.目标aria = await p.evaluate((i) => document.querySelector(`.react-flow__node[data-id="${i}"]`)?.getAttribute('aria-label'), 目标);
    rec.守卫 = (await keyGuard(p)).safe;
    rec.按前节点数 = await 节点数();
    await p.keyboard.press('Backspace'); await p.waitForTimeout(3500);
    rec.删后还在吗 = await 存在(目标); rec.按后节点数 = await 节点数();
    rec.结论 = rec.删后还在吗 ? '❌ ⌫ 没删掉' : '✅ ⌫ 删掉了';
    if (rec.删后还在吗) rec.补救 = await 菜单删除(目标);
  } else rec.结论 = '⌘V 没造出节点';
} catch (e) { rec.异常 = String(e).slice(0, 200); }
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

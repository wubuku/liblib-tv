// 批次 183 g 轮：**补上 2×2 里唯一缺的那一格**（文本节点 ＋ 搜索面板 ＋ `⌫`）。
//
// 183f 的四格结果：
//   图片副本 ＋ 搜索面板 ＋ `⌫` ⇒ ❌（183e、183f 各一次，**2/2 没删掉**）
//   图片副本 ＋ 直接点标题 ＋ `⌫` ⇒ ✅（183e、183f 各一次，**2/2 删掉了**）
//   文本节点 ＋ 直接点标题 ＋ `⌫` ⇒ ✅（1/1）
//   文本节点 ＋ 搜索面板 ＋ `⌫` ⇒ **作废** —— 🔴 非空守卫抓到了：搜索关键词用的是节点
//     **标题** `文本`，而画布上**有多个标题含「文本」的节点**，于是点中的
//     是 `node_5gftn3dnt1`（另一个节点），不是本轮造的 `node_2xtbmdwj15`。
//     若没有这道守卫，这一格会被记成「搜索面板选中也删不掉」，把结论带歪。
//
// ⇒ 本轮只做一件事：**用唯一内容词搜索**（节点的 aria 逐字是
//   `文本 node: B183G-唯一词-...`，搜索结果里带这个串），
//   让选中集**确实**等于目标 id，再按 `⌫`。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '183g' };
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
const 写哨兵 = (s) => p.evaluate(async (t) => { try { await navigator.clipboard.writeText(t); return '写成功'; } catch (e) { return '写失败: ' + String(e).slice(0, 80); } }, s);
const 适配 = async () => { await p.mouse.move(640, 400); await p.waitForTimeout(250); await p.keyboard.press('Shift+Digit1'); await p.waitForTimeout(2400); return R.zoom(); };
const 菜单删除 = async (id) => {
  if (!(await 标题坐标(id))) await 适配();
  const pt = await 标题坐标(id);
  if (!pt) return { 成功: false, 原因: '标题不在视口内' };
  await p.mouse.click(pt[0], pt[1], { button: 'right' }); await p.waitForTimeout(1500);
  const 项 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"] [role=menuitem]'))
    .find((x) => (x.innerText || '').trim().startsWith('删除'));
    if (!e) return null; const r = e.getBoundingClientRect();
    return { 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 禁用: e.getAttribute('aria-disabled') === 'true' }; });
  if (!项 || 项.禁用) { await p.keyboard.press('Escape'); await p.waitForTimeout(600); return { 成功: false, 原因: 项 ? '删除项禁用' : '没有删除项' }; }
  await p.mouse.click(项.点[0], 项.点[1]); await p.waitForTimeout(3000);
  return { 成功: !(await 存在(id)) };
};
/** 按**唯一词**搜索并逐条列出所有命中，让「选中的是不是它」肉眼可查。 */
const 搜索选中唯一 = async (词) => {
  if (typeof 词 !== 'string' || !词.trim()) return { 成功: false, 原因: '关键词非法' };
  const 开 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[aria-label]')).find((x) => x.getAttribute('aria-label') === '搜索');
    if (!e) return null; const r = e.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; });
  if (!开) return { 成功: false, 原因: '没有搜索按钮' };
  await p.mouse.click(开[0], 开[1]); await p.waitForTimeout(1100);
  const 输入 = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-search-panel"] input');
    if (!e) return null; const r = e.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; });
  if (!输入) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); return { 成功: false, 原因: '搜索面板没有输入框' }; }
  await p.mouse.click(输入[0], 输入[1]); await p.waitForTimeout(400);
  await p.fill('[data-testid="canvas-search-panel"] input', 词); await p.waitForTimeout(1500);
  const 命中 = await p.evaluate((w) => Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-"]'))
    .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 20 && r.height > 20; })
    .map((e) => { const r = e.getBoundingClientRect();
      return { id: (e.getAttribute('data-testid') || '').replace('canvas-search-result-', ''), 文字: (e.innerText || '').trim().replace(/\n/g, ' | ').slice(0, 70),
        点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; }), 词);
  rec.本次全部命中 = 命中;
  const 目标项 = 命中.find((h) => h.文字.includes(词));
  if (!目标项) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); return { 成功: false, 原因: '没有命中唯一词', 命中数: 命中.length }; }
  await p.mouse.click(目标项.点[0], 目标项.点[1]); await p.waitForTimeout(1400);
  const s = await 选中集(); await p.keyboard.press('Escape'); await p.waitForTimeout(500);
  return { 成功: s.length >= 1, 选中集: s, 点的那个: 目标项 };
};

const 前id = await id集();
rec.起点 = { 节点数: 前id.length, 积分: await R.credits(), 缩放: await R.zoom() };
const 唯一词 = 'B183G-唯一词-搜面板';

// 造文本节点：写唯一内容 → 选一个源节点 → ⌘V
await 写哨兵(唯一词);
const 源 = await p.evaluate(() => { const n = document.querySelector('.react-flow__node-image');
  if (!n) return null; const t = n.querySelector('[data-testid="flow-node-title"]');
  return { id: n.getAttribute('data-id'), 标题: t ? (t.innerText || '').trim().split('\n')[0] : null }; });
rec.源 = 源;
try {
  if (源) {
    const 开 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[aria-label]')).find((x) => x.getAttribute('aria-label') === '搜索');
      const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
    await p.mouse.click(开[0], 开[1]); await p.waitForTimeout(1100);
    const 输入 = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-search-panel"] input');
      const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
    await p.mouse.click(输入[0], 输入[1]); await p.waitForTimeout(400);
    await p.fill('[data-testid="canvas-search-panel"] input', 源.标题); await p.waitForTimeout(1400);
    const 命中 = await p.evaluate((w) => { const e = Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-"]'))
      .find((x) => (x.innerText || '').includes(w));
      if (!e) return null; const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, 源.标题);
    if (命中) { await p.mouse.click(命中[0], 命中[1]); await p.waitForTimeout(1300); rec.源选中 = await 选中集(); }
    await p.keyboard.press('Escape'); await p.waitForTimeout(500);
    await p.keyboard.press('Meta+v'); await p.waitForTimeout(2400);
    await p.keyboard.press('Escape'); await p.waitForTimeout(600);
  }
  const 新增 = (await id集()).filter((i) => !前id.includes(i));
  rec.粘贴新增 = 新增;
  if (新增.length) {
    const 目标 = 新增[0];
    rec.目标 = { id: 目标, aria: await p.evaluate((i) => document.querySelector(`.react-flow__node[data-id="${i}"]`)?.getAttribute('aria-label'), 目标) };
    await 适配();
    const S = await 搜索选中唯一(唯一词);
    rec.选中 = S;
    rec.守卫 = (await keyGuard(p)).safe;
    if (Array.isArray(S.选中集) && S.选中集.includes(目标)) {
      rec.按前节点数 = await 节点数();
      await p.keyboard.press('Backspace'); await p.waitForTimeout(3500);
      rec.删后还在吗 = await 存在(目标); rec.按后节点数 = await 节点数();
      rec.结论 = rec.删后还在吗 ? '❌ ⌫ 没删掉' : '✅ ⌫ 删掉了';
      if (rec.删后还在吗) rec.补救 = await 菜单删除(目标);
    } else rec.结论 = '没选中目标节点，留白';
  } else rec.结论 = '⌘V 没造出节点，留白';
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

// 批次 183 e 轮：**`⌫` 到底能不能删图片节点？**（手册到处写着「选中按 ⌫ 删除」）
//
// 起因是 183 收尾的一次真事故：菜单点「复制副本」造出图片副本后，
// **按 `⌫` 两次都没删掉**（选中集确认就是它、焦点守卫 safe、等了 4 秒），
// 而**菜单的「删除」项一次就删掉了**。
// ⇒ 冒出两个互斥的解释，而它们对用户的意义完全相反：
//   甲 **`⌫` 对图片节点不生效** ⇒ 🔴 手册「选中按 ⌫ 删除」这句话**对图片节点是错的**；
//   乙 **只是我的选中方式（搜索面板）不对** ⇒ 与用户无关，是我探针的问题。
//
// 受控设计（三格，逐格只改一个变量）：
//   格 1 **图片副本 ＋ 搜索面板选中 ＋ `⌫`**   ← 复现 183 的失败
//   格 2 **图片副本 ＋ 直接点标题选中 ＋ `⌫`**  ← 只把「选中方式」换掉，排乙
//   格 3 **文本节点 ＋ 选中 ＋ `⌫`**            ← **正向对照**：证明这个环境里 `⌫` 能删
//   （格 3 的文本节点用「写哨兵到剪贴板 → `⌘V`」造出来 —— 批次 178 已验证 `⌘V` 会把
//     剪贴板文本粘成**文本节点**，正好当对照，且不碰任何生成按钮。）
//
// ⚠️ **绝不动别人的 `b22-upload` 原件**：只删本轮自己造出来的节点，
//    收尾逐个按 id 验，并核验原有 76 个 id 逐个仍在。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '183e' };
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
const 标题文案 = (id) => p.evaluate((i) => (document.querySelector(`.react-flow__node[data-id="${i}"] [data-testid="flow-node-title"]`)?.innerText || '').trim().split('\n')[0], id);
const 标题坐标 = (id) => p.evaluate((i) => { const t = document.querySelector(`.react-flow__node[data-id="${i}"] [data-testid="flow-node-title"]`);
  if (!t) return null; const r = t.getBoundingClientRect();
  if (!(r.width > 2 && r.right > 0 && r.bottom > 0 && r.left < innerWidth && r.top < innerHeight)) return null;
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, id);
const 写哨兵 = (s) => p.evaluate(async (t) => { try { await navigator.clipboard.writeText(t); return '写成功'; } catch (e) { return '写失败: ' + String(e).slice(0, 80); } }, s);
const 搜索选中 = async (关键词) => {
  const 开 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[aria-label]')).find((x) => x.getAttribute('aria-label') === '搜索');
    if (!e) return null; const r = e.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; });
  if (!开) return { 成功: false, 原因: '没有「搜索」按钮' };
  await p.mouse.click(开[0], 开[1]); await p.waitForTimeout(1100);
  const 输入 = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-search-panel"] input');
    if (!e) return null; const r = e.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; });
  if (!输入) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); return { 成功: false, 原因: '搜索面板没有输入框' }; }
  await p.mouse.click(输入[0], 输入[1]); await p.waitForTimeout(400);
  await p.fill('[data-testid="canvas-search-panel"] input', 关键词); await p.waitForTimeout(1400);
  const 命中 = await p.evaluate((词) => Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-"]'))
    .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 20 && r.height > 20; })
    .map((e) => { const r = e.getBoundingClientRect();
      return { id: (e.getAttribute('data-testid') || '').replace('canvas-search-result-', ''), 文字: (e.innerText || '').trim().replace(/\n/g, ' | ').slice(0, 60),
        点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; }).filter((x) => !词 || x.文字.includes(词)), 关键词);
  if (!命中.length) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); return { 成功: false, 原因: `没有命中「${关键词}」` }; }
  await p.mouse.click(命中[0].点[0], 命中[0].点[1]); await p.waitForTimeout(1400);
  const s = await 选中集(); await p.keyboard.press('Escape'); await p.waitForTimeout(500);
  return { 成功: s.length >= 1, 选中集: s, 命中: 命中.slice(0, 2) };
};
/** 走菜单造一个图片副本（菜单「复制副本」）。 */
const 造图片副本 = async () => {
  const 前 = await id集();
  const 原 = await p.evaluate(() => { const n = document.querySelector('.react-flow__node-image');
    if (!n) return null; const t = n.querySelector('[data-testid="flow-node-title"]');
    return { id: n.getAttribute('data-id'), 标题: t ? (t.innerText || '').trim().split('\n')[0] : null }; });
  if (!原) return { 成功: false, 原因: '画布上没有图片节点' };
  const S = await 搜索选中(原.标题);
  if (!(S.成功 && S.选中集.includes(原.id))) return { 成功: false, 原因: '没选中原图片节点' };
  const pt = await 标题坐标(原.id);
  if (!pt) return { 成功: false, 原因: '原图片节点标题不在视口内' };
  await p.mouse.click(pt[0], pt[1], { button: 'right' }); await p.waitForTimeout(1500);
  const 项 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"] [role=menuitem]'))
    .find((x) => (x.innerText || '').trim().startsWith('复制副本'));
    if (!e) return null; const r = e.getBoundingClientRect();
    return { 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 禁用: e.getAttribute('aria-disabled') === 'true' }; });
  if (!项 || 项.禁用) { await p.keyboard.press('Escape'); await p.waitForTimeout(600); return { 成功: false, 原因: '没有可点的复制副本项' }; }
  await p.mouse.click(项.点[0], 项.点[1]); await p.waitForTimeout(2600);
  await p.keyboard.press('Escape'); await p.waitForTimeout(800);
  const 现 = await id集();
  const 新增 = 现.filter((i) => !前.includes(i));
  return 新增.length ? { 成功: true, 新id: 新增[0], 标题: await 标题文案(新增[0]) } : { 成功: false, 原因: '点了复制副本但没造出新节点' };
};
/** 走菜单删除（183d 已验证这条路对图片副本有效）。 */
const 菜单删除 = async (id) => {
  const pt = await 标题坐标(id);
  if (!pt) return { 成功: false, 原因: '标题不在视口内' };
  await p.mouse.click(pt[0], pt[1], { button: 'right' }); await p.waitForTimeout(1500);
  const 项 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"] [role=menuitem]'))
    .find((x) => (x.innerText || '').trim().startsWith('删除'));
    if (!e) return null; const r = e.getBoundingClientRect();
    return { 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 禁用: e.getAttribute('aria-disabled') === 'true' }; });
  if (!项 || 项.禁用) { await p.keyboard.press('Escape'); await p.waitForTimeout(600); return { 成功: false, 原因: 项 ? '删除项禁用' : '菜单里没有删除项' }; }
  await p.mouse.click(项.点[0], 项.点[1]); await p.waitForTimeout(3000);
  return { 成功: !(await 存在(id)), 还在吗: await 存在(id) };
};

const 前id = await id集();
rec.起点 = { 节点数: 前id.length, 积分: await R.credits(), 缩放: await R.zoom() };
rec.格 = [];

// ── 格 1：图片副本 ＋ 搜索面板选中 ＋ `⌫`
{
  const 行 = { 格: '1_图片副本_搜索面板选中_退格' };
  const C = await 造图片副本();
  行.造副本 = C;
  if (C.成功) {
    const S = await 搜索选中(C.标题);
    行.选中 = S.选中集; 行.选中成功 = S.成功;
    行.守卫 = (await keyGuard(p)).safe;
    行.按前节点数 = await 节点数();
    await p.keyboard.press('Backspace'); await p.waitForTimeout(3500);
    行.删后还在吗 = await 存在(C.新id); 行.按后节点数 = await 节点数();
    行.结论 = 行.删后还在吗 ? '❌ ⌫ 没删掉' : '✅ ⌫ 删掉了';
    if (行.删后还在吗) 行.补救 = await 菜单删除(C.新id);
  }
  rec.格.push(行);
  await p.keyboard.press('Escape'); await p.waitForTimeout(700);
}

// ── 格 2：**同样的图片副本**，但改成**直接点标题**选中（只换选中方式）
{
  const 行 = { 格: '2_图片副本_直接点标题选中_退格' };
  const C = await 造图片副本();
  行.造副本 = C;
  if (C.成功) {
    const pt = await 标题坐标(C.新id);
    行.标题坐标 = pt;
    if (pt) {
      await p.mouse.click(pt[0], pt[1]); await p.waitForTimeout(1300);
      行.选中 = await 选中集();
      行.守卫 = (await keyGuard(p)).safe;
      行.按前节点数 = await 节点数();
      await p.keyboard.press('Backspace'); await p.waitForTimeout(3500);
      行.删后还在吗 = await 存在(C.新id); 行.按后节点数 = await 节点数();
      行.结论 = 行.删后还在吗 ? '❌ ⌫ 没删掉' : '✅ ⌫ 删掉了';
      if (行.删后还在吗) 行.补救 = await 菜单删除(C.新id);
    } else { 行.结论 = '标题不在视口内，留白'; }
  }
  rec.格.push(行);
  await p.keyboard.press('Escape'); await p.waitForTimeout(700);
}

// ── 格 3：**文本节点** ＋ 选中 ＋ `⌫`（正向对照：这个环境里 ⌫ 到底能不能删）
{
  const 行 = { 格: '3_文本节点_退格_正向对照' };
  const 前 = await id集();
  行.写哨兵 = await 写哨兵('B183E-对照文本');
  const 图 = await p.evaluate(() => { const n = document.querySelector('.react-flow__node-image');
    if (!n) return null; const t = n.querySelector('[data-testid="flow-node-title"]');
    return { id: n.getAttribute('data-id'), 标题: t ? (t.innerText || '').trim().split('\n')[0] : null }; });
  if (!图) { 行.结论 = '没有图片节点，没法造文本对照'; rec.格.push(行); }
  else {
    const S0 = await 搜索选中(图.标题);
    行.选中源节点 = S0.成功;
    if (S0.成功) { await p.keyboard.press('Meta+v'); await p.waitForTimeout(2400); }
    const 现 = await id集();
    const 新增 = 现.filter((i) => !前.includes(i));
    行.粘贴新增 = 新增;
    if (新增.length) {
      const nid = 新增[0];
      行.新节点类型 = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
        return n ? { class: (n.className || '').toString(), aria: n.getAttribute('aria-label') } : null; }, nid);
      const S = await 搜索选中(await 标题文案(nid));
      行.选中 = S.选中集; 行.选中成功 = S.成功;
      行.守卫 = (await keyGuard(p)).safe;
      行.按前节点数 = await 节点数();
      await p.keyboard.press('Backspace'); await p.waitForTimeout(3500);
      行.删后还在吗 = await 存在(nid); 行.按后节点数 = await 节点数();
      行.结论 = 行.删后还在吗 ? '❌ ⌫ 没删掉' : '✅ ⌫ 删掉了';
      if (行.删后还在吗) 行.补救 = await 菜单删除(nid);
    } else 行.结论 = '⌘V 没造出节点';
  }
  rec.格.push(行);
}
await p.keyboard.press('Escape'); await p.waitForTimeout(700);

// ═════════ 收尾：清掉本轮全部新增 + 核验
const 现存 = await id集();
const 残留 = 现存.filter((i) => !前id.includes(i));
rec.收尾前 = { 现在节点数: 现存.length, 残留: 残留 };
rec.清理 = [];
for (const id of 残留) { const r = await 菜单删除(id); rec.清理.push({ id, 标题: await 标题文案(id), ...r }); }
await p.keyboard.press('Escape'); await p.waitForTimeout(600);
await p.reload({ waitUntil: 'domcontentloaded' }); await pinViewport(p);
const t0 = Date.now();
while (Date.now() - t0 < 40000) { if (await p.evaluate(() => document.querySelectorAll('.react-flow__node').length)) break; await p.waitForTimeout(400); }
await p.waitForTimeout(2500);
const 末 = await id集();
rec.收尾核验 = { 现在节点数: 末.length, 起点节点数: 前id.length,
  残留id: 末.filter((i) => !前id.includes(i)), 丢失id: 前id.filter((i) => !末.includes(i)), 原有仍在: 前id.filter((i) => 末.includes(i)).length };
rec.收尾 = { 状态行: await R.status(), 积分: await R.credits(), 缩放: await R.zoom(), 浮层: await R.overlays() };
console.log(JSON.stringify(rec, null, 1));
process.exit(0);

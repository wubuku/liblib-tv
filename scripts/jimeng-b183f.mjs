// 批次 183 f 轮：**把「选中方式 × `⌫` 能不能删」做成干净的 2×2，并清掉 183e 的残留。**
//
// 183e 的三格把解释**反转**了：
//   格 1 图片副本 ＋ **搜索面板**选中 ＋ `⌫` ⇒ ❌ 没删掉
//   格 2 图片副本 ＋ **直接点标题**选中 ＋ `⌫` ⇒ ✅ 删掉了
//   格 3 文本节点 ＋ **搜索面板**选中 ＋ `⌫` ⇒ ❌ 没删掉
// ⇒ 分水岭**不是节点类型，是选中方式**。
//
// 🔴 但这与批次 175/178 的成功记录**直接矛盾**：那两批的收尾同样是
//   「搜索面板选中 → 按 `⌫`」，且都报「残留 0」。
//   ⇒ 在写进手册之前必须拿到**每侧至少 2 次**的干净读数，否则就是拿单次读数下结论。
//
// 2×2 设计（每个格子都用**本轮自己造**的节点，绝不碰别人的 `b22-upload` 原件）：
//   节点类型：图片副本（菜单「复制副本」造）／ 文本节点（写哨兵 → `⌘V` 造）
//   选中方式：搜索面板 ／ 直接点标题
//
// ⚠️ 收尾：183e 留了一个 `node_sahp2bry0z`（菜单删除时「标题不在视口内」而失败）。
//   本轮开头先按 `⇧1` 适配画布把它收进视野再删 —— 这也顺带验证
//   「**菜单删除前必须先确认标题在视口内**」这条操作要求。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '183f' };
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
/** 只读导航：把全部节点收进视野。 */
const 适配 = async () => { await p.mouse.move(640, 400); await p.waitForTimeout(250); await p.keyboard.press('Shift+Digit1'); await p.waitForTimeout(2400); return R.zoom(); };
const 菜单删除 = async (id) => {
  if (!(await 标题坐标(id))) { await 适配(); }
  const pt = await 标题坐标(id);
  if (!pt) return { 成功: false, 原因: '适配之后标题仍不在视口内' };
  await p.mouse.click(pt[0], pt[1], { button: 'right' }); await p.waitForTimeout(1500);
  const 项 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"] [role=menuitem]'))
    .find((x) => (x.innerText || '').trim().startsWith('删除'));
    if (!e) return null; const r = e.getBoundingClientRect();
    return { 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 禁用: e.getAttribute('aria-disabled') === 'true' }; });
  if (!项 || 项.禁用) { await p.keyboard.press('Escape'); await p.waitForTimeout(600); return { 成功: false, 原因: 项 ? '删除项禁用' : '菜单里没有删除项' }; }
  await p.mouse.click(项.点[0], 项.点[1]); await p.waitForTimeout(3000);
  return { 成功: !(await 存在(id)) };
};
const 搜索选中 = async (关键词) => {
  // 🔴 183f 第一版就死在这里：`造图片副本()` 忘了返回 `标题` ⇒ 传进来的是 `undefined`
  //    ⇒ `page.fill` 抛 `value: expected string, got undefined` ⇒ **整轮崩在中途**，
  //    画布上留下一个没清掉的副本。⇒ 这是「恒真门家族」的老根子：
  //    **凡是要传给 page.fill / 字符串 API 的值，先断言非空。**
  if (typeof 关键词 !== 'string' || !关键词.trim()) return { 成功: false, 原因: `关键词非法：${JSON.stringify(关键词)}` };
  const 开 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[aria-label]')).find((x) => x.getAttribute('aria-label') === '搜索');
    if (!e) return null; const r = e.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; });
  if (!开) return { 成功: false, 原因: '没有「搜索」按钮' };
  await p.mouse.click(开[0], 开[1]); await p.waitForTimeout(1100);
  const 输入 = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-search-panel"] input');
    if (!e) return null; const r = e.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; });
  if (!输入) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); return { 成功: false, 原因: '搜索面板没有输入框' }; }
  await p.mouse.click(输入[0], 输入[1]); await p.waitForTimeout(400);
  await p.fill('[data-testid="canvas-search-panel"] input', 关键词); await p.waitForTimeout(1500);
  const 命中 = await p.evaluate((词) => Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-"]'))
    .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 20 && r.height > 20; })
    .map((e) => { const r = e.getBoundingClientRect();
      return { id: (e.getAttribute('data-testid') || '').replace('canvas-search-result-', ''), 文字: (e.innerText || '').trim().replace(/\n/g, ' | ').slice(0, 60),
        点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; }).filter((x) => !词 || x.文字.includes(词)), 关键词);
  if (!命中.length) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); return { 成功: false, 原因: `没有命中「${关键词}」`, 命中数: 0 }; }
  await p.mouse.click(命中[0].点[0], 命中[0].点[1]); await p.waitForTimeout(1400);
  const s = await 选中集(); await p.keyboard.press('Escape'); await p.waitForTimeout(500);
  return { 成功: s.length >= 1, 选中集: s, 命中: 命中.slice(0, 2) };
};
const 直接点选中 = async (id) => {
  if (!(await 标题坐标(id))) await 适配();
  const pt = await 标题坐标(id);
  if (!pt) return { 成功: false, 原因: '适配之后标题仍不在视口内' };
  await p.mouse.click(pt[0], pt[1]); await p.waitForTimeout(1300);
  const s = await 选中集();
  return { 成功: s.includes(id), 选中集: s, 点: pt };
};
const 造图片副本 = async () => {
  const 前 = await id集();
  const 原 = await p.evaluate(() => { const n = document.querySelector('.react-flow__node-image');
    if (!n) return null; const t = n.querySelector('[data-testid="flow-node-title"]');
    return { id: n.getAttribute('data-id'), 标题: t ? (t.innerText || '').trim().split('\n')[0] : null }; });
  if (!原) return { 成功: false, 原因: '没有图片节点' };
  const S = await 搜索选中(原.标题);
  if (!(S.成功 && S.选中集.includes(原.id))) return { 成功: false, 原因: '没选中原图片节点' };
  if (!(await 标题坐标(原.id))) await 适配();
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
  const 新增 = (await id集()).filter((i) => !前.includes(i));
  return 新增.length ? { 成功: true, 新id: 新增[0], 标题: await 标题文案(新增[0]) } : { 成功: false, 原因: '没造出新节点' };
};
const 造文本节点 = async (词) => {
  const 前 = await id集();
  await 写哨兵(词);
  const 原 = await p.evaluate(() => { const n = document.querySelector('.react-flow__node-image');
    if (!n) return null; const t = n.querySelector('[data-testid="flow-node-title"]');
    return { id: n.getAttribute('data-id'), 标题: t ? (t.innerText || '').trim().split('\n')[0] : null }; });
  if (!原) return { 成功: false, 原因: '没有图片节点当粘贴源' };
  const S = await 搜索选中(原.标题);
  if (!(S.成功 && S.选中集.includes(原.id))) return { 成功: false, 原因: '没选中粘贴源' };
  await p.keyboard.press('Meta+v'); await p.waitForTimeout(2400);
  await p.keyboard.press('Escape'); await p.waitForTimeout(600);
  const 新增 = (await id集()).filter((i) => !前.includes(i));
  if (!新增.length) return { 成功: false, 原因: '⌘V 没造出节点' };
  await 适配();
  return { 成功: true, 新id: 新增[0], 标题: await 标题文案(新增[0]),
    节点aria: await p.evaluate((i) => document.querySelector(`.react-flow__node[data-id="${i}"]`)?.getAttribute('aria-label'), 新增[0]) };
};

const 前id = await id集();
rec.起点 = { 节点数: 前id.length, 积分: await R.credits(), 缩放: await R.zoom() };

// ── 步骤 0：先清掉上一轮（183e）留下的节点
//   ⚠️ 只按**显式 id** 清，不用「看起来像残留」这种启发式 —— 画布上大部分节点是别人的，
//     任何按特征的猜测都可能删错。
rec.先清残留 = {};
for (const 旧 of ['node_sahp2bry0z', 'node_vsmpxya528', 'node_xjvjdw1de0', 'node_3b6e430xpk', 'node_dz61xbvzc1']) {
  if (前id.includes(旧)) { rec.先清残留.适配后缩放 = await 适配(); rec.先清残留[旧] = await 菜单删除(旧); }
}
if (!Object.keys(rec.先清残留).length) rec.先清残留.说明 = '没有上一轮留下的节点';
await p.keyboard.press('Escape'); await p.waitForTimeout(700);

// ── 2×2
rec.格 = [];
const 跑一格 = async (类型, 选中方式, 序号) => {
  const 行 = { 类型, 选中方式, 序号 };
  // 🔴 每格包 try/catch：**一格崩掉不能让整轮挂掉** —— 崩在中途就等于把残局留给下一次
  //   （183f 第一版就是这么把画布留在 77 节点的）。
  try {
    const C = 类型 === '图片副本' ? await 造图片副本() : await 造文本节点(`B183F-${类型}-${选中方式}-${序号}`);
    行.造 = C;
    if (!C.成功) { 行.结论 = '没造出节点，留白'; rec.格.push(行); return; }
    if (typeof C.标题 !== 'string' || !C.标题.trim()) { 行.结论 = `造出来的节点没有可用标题（${JSON.stringify(C.标题)}），留白`; rec.格.push(行); return; }
    await 适配();
    行.选中 = 选中方式 === '搜索面板' ? await 搜索选中(C.标题) : await 直接点选中(C.新id);
    行.选中集 = 行.选中.选中集;
    行.守卫 = (await keyGuard(p)).safe;
    // 🔴 守卫：选中集必须**确实包含目标 id**，否则这一格不成立（宁可留白）
    if (!Array.isArray(行.选中集) || !行.选中集.includes(C.新id)) {
      行.结论 = '没选中目标节点，留白'; rec.格.push(行); return;
    }
    行.按前节点数 = await 节点数();
    await p.keyboard.press('Backspace'); await p.waitForTimeout(3500);
    行.删后还在吗 = await 存在(C.新id); 行.按后节点数 = await 节点数();
    行.结论 = 行.删后还在吗 ? '❌ ⌫ 没删掉' : '✅ ⌫ 删掉了';
    if (行.删后还在吗) 行.补救 = await 菜单删除(C.新id);
  } catch (e) {
    行.异常 = String(e).slice(0, 160);
  }
  rec.格.push(行);
  await p.keyboard.press('Escape'); await p.waitForTimeout(700);
};
for (const [类型, 方式] of [['图片副本', '搜索面板'], ['图片副本', '直接点标题'], ['文本节点', '搜索面板'], ['文本节点', '直接点标题']])
  await 跑一格(类型, 方式, rec.格.length + 1);

// ═════════ 收尾
await p.keyboard.press('Escape'); await p.waitForTimeout(600);
const 现存 = await id集();
rec.收尾前 = { 现在节点数: 现存.length, 本轮多出: 现存.filter((i) => !前id.includes(i)) };
rec.清理 = [];
for (const id of 现存.filter((i) => !前id.includes(i))) rec.清理.push({ id, 标题: await 标题文案(id), ...(await 菜单删除(id)) });
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

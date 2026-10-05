// 批次 186：**把「下载」的类型白名单补全** —— 六种节点类型逐个开右键菜单读「下载」那一项。
//
// 靶子：`help-and-shortcuts.md` 的「下载不是所有节点都有」那张表只有 4 行，
// 其中「**音频 / 视频**」写的是「**本批未取到读数（选不中）**」，并自注「没测到，不是不能下载」。
// 而那句「选不中」的理由**今天已经过期** —— 批次 184c/185 用**搜索面板选中**把
// 音频（`node_ay7f1jn45r`）与视频（`node_236ctpehgg`）都稳定选中了，
// 184d 更用它读到了视频节点完整的 before/after 菜单。
// ⇒ 与本页第 398-403 行记的那条教训同形：**「未验证」是遗留状态没销账，不是当下真的做不了。**
//
// 本批把**画布上现存的 6 种类型**逐个开一次右键菜单，逐项读：
//   菜单项数、菜单本体尺寸、「下载」在不在、禁不禁用、**禁用原因逐字**。
// 只读菜单、**不点「下载」**（那会落盘文件）、不点任何其他项。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '186' };
await settle(p, R);
await p.mouse.move(1250, 10); await p.waitForTimeout(600);

const 节点数 = () => p.evaluate(() => document.querySelectorAll('.react-flow__node').length);
const id集 = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')).sort());
const 选中集 = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
const 标题坐标 = (id) => p.evaluate((i) => { const t = document.querySelector(`.react-flow__node[data-id="${i}"] [data-testid="flow-node-title"]`);
  if (!t) return null; const r = t.getBoundingClientRect();
  if (!(r.width > 2 && r.right > 0 && r.bottom > 0 && r.left < innerWidth && r.top < innerHeight)) return null;
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, id);

/** 开菜单并读全部项（**不点任何一项**）。 */
const 读菜单 = async (id) => {
  const pt = await 标题坐标(id);
  if (!pt) return { 失败: '标题不在视口内' };
  const 落 = await p.evaluate((q) => { const e = document.elementFromPoint(q[0], q[1]);
    return e ? { 标签: e.tagName, 逐字: (e.innerText || '').trim().slice(0, 20), 在节点内: !!e.closest('.react-flow__node') } : null; }, pt);
  if (!落?.在节点内) return { 失败: '落点不在节点上，不盲点', 落点: 落 };
  await p.mouse.click(pt[0], pt[1], { button: 'right' }); await p.waitForTimeout(1500);
  const m = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-context-menu"]'); if (!e) return null;
    const r = e.getBoundingClientRect();
    return { 几何: { w: Math.round(r.width), h: Math.round(r.height) },
      项: Array.from(e.querySelectorAll('[role=menuitem]')).map((i) => { const sp = Array.from(i.children).map((c) => (c.innerText || '').trim());
        return { 名: sp[0] || (i.innerText || '').trim().split('\n')[0], 禁用: i.getAttribute('aria-disabled') === 'true', 第二段: sp[1] || null }; }) }; });
  await p.keyboard.press('Escape'); await p.waitForTimeout(800);
  if (!m) return { 失败: '菜单没开' };
  const 下 = m.项.find((x) => x.名 === '下载' || x.名.startsWith('下载'));
  return { 落点: 落, 几何: m.几何, 项数: m.项.length, 全部项: m.项.map((x) => x.名),
    下载: 下 ? { 在: true, 禁用: 下.禁用, 原因逐字: 下.禁用 ? 下.第二段 : null } : { 在: false } };
};

const 搜索选中 = async (关键词) => {
  if (typeof 关键词 !== 'string' || !关键词.trim()) return { 成功: false, 原因: '关键词非法' };
  const 开 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[aria-label]')).find((x) => x.getAttribute('aria-label') === '搜索');
    if (!e) return null; const r = e.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; });
  if (!开) return { 成功: false, 原因: '没有搜索按钮' };
  await p.mouse.click(开[0], 开[1]); await p.waitForTimeout(1100);
  const 输入 = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-search-panel"] input');
    if (!e) return null; const r = e.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; });
  if (!输入) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); return { 成功: false, 原因: '搜索面板没有输入框' }; }
  await p.mouse.click(输入[0], 输入[1]); await p.waitForTimeout(400);
  await p.fill('[data-testid="canvas-search-panel"] input', 关键词); await p.waitForTimeout(1400);
  const 命中 = await p.evaluate((w) => Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-"]'))
    .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 20 && r.height > 20; })
    .map((e) => { const r = e.getBoundingClientRect();
      return { id: (e.getAttribute('data-testid') || '').replace('canvas-search-result-', ''), 文字: (e.innerText || '').trim().replace(/\n/g, ' | ').slice(0, 60),
        点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; }).filter((x) => !w || x.文字.includes(w)), 关键词);
  if (!命中.length) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); return { 成功: false, 原因: `没命中「${关键词}」`, 命中数: 0 }; }
  await p.mouse.click(命中[0].点[0], 命中[0].点[1]); await p.waitForTimeout(1400);
  const s = await 选中集(); await p.keyboard.press('Escape'); await p.waitForTimeout(500);
  return { 成功: s.length >= 1, 选中集: s, 命中文字: 命中[0].文字 };
};

const 前id = await id集();
rec.起点 = { 节点数: 前id.length, 状态行: await R.status(), 积分: await R.credits(), 缩放: await R.zoom() };
// 画布上现存的类型，各取一个样本（**按 class 找，不按 id 猜**）
const 样本 = await p.evaluate(() => {
  const 型 = ['image', 'video', 'audio', 'text', 'timeline', 'external'];
  const 出 = {};
  for (const t of 型) { const n = document.querySelector(`.react-flow__node-${t}`); if (n) { const q = n.querySelector('[data-testid="flow-node-title"]');
    出[t] = { id: n.getAttribute('data-id'), 标题: q ? (q.innerText || '').trim().split('\n')[0] : null,
      有资源: t === 'image' ? !!n.querySelector('img') : null }; } }
  return 出;
});
rec.样本 = 样本;
rec.普查 = {};
for (const [型, s] of Object.entries(样本)) {
  const 行 = { 型, id: s.id, 标题: s.标题 };
  try {
    if (typeof s.标题 !== 'string' || !s.标题.trim()) { 行.说明 = '标题为空，无法可靠选中'; rec.普查[型] = 行; continue; }
    const S = await 搜索选中(s.标题);
    行.选中 = S.选中集; 行.选中成功 = S.成功; 行.命中文字 = S.命中文字;
    // 🔴 非空守卫：选中集必须**确实等于**目标 id，否则本格作废
    if (!(S.成功 && S.选中集 && S.选中集.length === 1 && S.选中集[0] === s.id)) {
      行.说明 = `选中集不是目标节点（读到 ${JSON.stringify(S.选中集)}），本格作废`; rec.普查[型] = 行; continue;
    }
    行.菜单 = await 读菜单(s.id);
  } catch (e) { 行.异常 = String(e).slice(0, 160); }
  rec.普查[型] = 行;
  await p.keyboard.press('Escape'); await p.waitForTimeout(700);
}
rec.汇总 = Object.entries(rec.普查).map(([型, r]) => ({ 型, 项数: r.菜单?.项数 ?? null, 几何: r.菜单?.几何 ?? null,
  下载在: r.菜单?.下载?.在 ?? null, 下载禁用: r.菜单?.下载?.禁用 ?? null, 原因逐字: r.菜单?.下载?.原因逐字 ?? null,
  说明: r.说明 || r.异常 || r.菜单?.失败 || null }));
await p.keyboard.press('Escape'); await p.waitForTimeout(700);
await p.reload({ waitUntil: 'domcontentloaded' }); await pinViewport(p);
const t0 = Date.now();
while (Date.now() - t0 < 60000) { if (await p.evaluate(() => document.querySelectorAll('.react-flow__node').length)) break; await p.waitForTimeout(500); }
await p.waitForTimeout(3000);
const 末 = await id集();
rec.收尾核验 = { 现在节点数: 末.length, 起点节点数: 前id.length, 残留id: 末.filter((i) => !前id.includes(i)), 丢失id: 前id.filter((i) => !末.includes(i)) };
rec.收尾 = { 状态行: await R.status(), 积分: await R.credits(), 缩放: await R.zoom(), 浮层: await R.overlays() };
console.log(JSON.stringify(rec, null, 1));
process.exit(0);

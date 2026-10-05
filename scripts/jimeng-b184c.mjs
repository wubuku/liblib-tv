// 批次 184 c 轮：**普查每种节点类型在选中态下到底有哪几个 ⊕**，
// 并解释 184b 格 1「before ⊕ 取不到坐标」是「按钮不存在」还是「不在视口内」。
//
// 起因：184b 取 `flow-node-target-connection-menu-button`（before ⊕）拿到 `null`，
// 而同一节点上的 `flow-node-source-connection-menu-button`（after ⊕）坐标正常（`36×36`）。
// 手册第 300-302 行有一张「哪些类型有这个 ⊕」的表，但那是批次 71 的读数；本轮逐类复核。
//
// 判据（不靠「点得中」，点得中还要过命中测试）：**选中后数 `aria-label^="Create connected
// node"` 的元素个数，并把 testid 逐字列出来**。个数 0 ⇒ 根本没有这个按钮。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';
const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '184c' };
await settle(p, R);
await p.mouse.move(1250, 10); await p.waitForTimeout(600);
const 节点数 = () => p.evaluate(() => document.querySelectorAll('.react-flow__node').length);
const id集 = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')).sort());
const 选中集 = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
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
  if (!命中.length) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); return { 成功: false, 原因: `没命中「${关键词}」` }; }
  await p.mouse.click(命中[0].点[0], 命中[0].点[1]); await p.waitForTimeout(1400);
  const s = await 选中集(); await p.keyboard.press('Escape'); await p.waitForTimeout(500);
  return { 成功: s.length >= 1, 选中集: s };
};
/** 选中态下该节点上的 ⊕ 按钮普查。 */
const 普查 = (id) => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
  const 全部 = Array.from(n.querySelectorAll('[aria-label^="Create connected node"]'));
  return { 节点class: (n.className || '').toString().replace(/react-flow__node\s*/, ''),
    节点aria: n.getAttribute('aria-label'),
    '⊕个数': 全部.length,
    '⊕': 全部.map((e) => { const r = e.getBoundingClientRect();
      return { 标签: e.tagName, testid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'),
        屏上: { w: Math.round(r.width), h: Math.round(r.height) }, 在视口内: r.right > 0 && r.bottom > 0 && r.left < innerWidth && r.top < innerHeight }; }),
    手柄: Array.from(n.querySelectorAll('.react-flow__handle')).map((e) => { const r = e.getBoundingClientRect();
      return { testid: e.getAttribute('data-testid'), pe: getComputedStyle(e).pointerEvents,
        beforePE: getComputedStyle(e, '::before').pointerEvents,
        屏上: { w: Math.round(r.width), h: Math.round(r.height) } }; }) };
}, id);
const 前id = await id集();
rec.起点 = { 节点数: 前id.length, 积分: await R.credits(), 缩放: await R.zoom() };
// 每种类型取一个样本（用 class 找，不按 id 猜）
const 样本 = await p.evaluate(() => {
  const 型 = ['image', 'video', 'audio', 'text', 'timeline', 'external'];
  const 出 = {};
  for (const t of 型) { const n = document.querySelector(`.react-flow__node-${t}`); if (n) { const q = n.querySelector('[data-testid="flow-node-title"]');
    出[t] = { id: n.getAttribute('data-id'), 标题: q ? (q.innerText || '').trim().split('\n')[0] : null }; } }
  return 出;
});
rec.样本 = 样本;
rec.普查 = {};
for (const [型, s] of Object.entries(样本)) {
  const 行 = { 型, id: s.id, 标题: s.标题 };
  try {
    if (typeof s.标题 !== 'string' || !s.标题.trim()) { 行.说明 = '标题为空，无法可靠用搜索选中'; rec.普查[型] = 行; continue; }
    const S = await 搜索选中(s.标题);
    行.选中 = S.选中集; 行.选中成功 = S.成功;
    if (!(S.成功 && S.选中集.includes(s.id))) { 行.说明 = '没选中，留白'; rec.普查[型] = 行; continue; }
    行.读数 = await 普查(s.id);
  } catch (e) { 行.异常 = String(e).slice(0, 160); }
  rec.普查[型] = 行;
  await p.keyboard.press('Escape'); await p.waitForTimeout(700);
}
// 汇总表
rec.汇总 = Object.entries(rec.普查).map(([型, r]) => ({ 型, '⊕个数': r.读数?.['⊕个数'] ?? null,
  testid: (r.读数?.['⊕'] || []).map((x) => (x.testid || '').replace('flow-node-', '').replace('-connection-menu-button', '')),
  理由: r.说明 || r.异常 || null }));
await p.keyboard.press('Escape'); await p.waitForTimeout(700);
await p.reload({ waitUntil: 'domcontentloaded' }); await pinViewport(p);
const t0 = Date.now();
while (Date.now() - t0 < 40000) { if (await p.evaluate(() => document.querySelectorAll('.react-flow__node').length)) break; await p.waitForTimeout(400); }
await p.waitForTimeout(2500);
const 末 = await id集();
rec.收尾核验 = { 现在节点数: 末.length, 残留id: 末.filter((i) => !前id.includes(i)), 丢失id: 前id.filter((i) => !末.includes(i)) };
rec.收尾 = { 状态行: await R.status(), 积分: await R.credits(), 缩放: await R.zoom(), 浮层: await R.overlays() };
console.log(JSON.stringify(rec, null, 1));
process.exit(0);

// 批次 184 d 轮：**在「两个 ⊕ 都存在」的节点上做完整三格对照**。
//
// 184 的图片节点对照已成立（after ⊕ 与拖手柄的菜单**逐字相同** ⇒ 入口 2 属 after），
// 但图片节点**只有 1 个 ⊕**（184c 普查：`⊕个数=1`，只有 source），
// 所以「before ⊕」那一格在图片节点上**根本无法构造**（184b 读到 `null` 就是这个原因，
// 不是「按钮跑到视口外」）。
// ⇒ 换到**两个 ⊕ 都存在**的节点（video / audio，实测各 2 个）上重做三格，
//   才能得到 before ≠ after ≠ 拖手柄 的**完整**指纹链。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';
const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '184d' };
await settle(p, R);
await p.mouse.move(1250, 10); await p.waitForTimeout(600);
const 节点数 = () => p.evaluate(() => document.querySelectorAll('.react-flow__node').length);
const id集 = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')).sort());
const 选中集 = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
const 读菜单 = async () => {
  const m = await p.evaluate(() => {
    const e = document.querySelector('[data-testid="canvas-context-menu"]'); if (!e) return null;
    const r = e.getBoundingClientRect();
    return { 几何: { w: Math.round(r.width), h: Math.round(r.height) },
      标题: (Array.from(e.querySelectorAll('*')).map((x) => (x.innerText || '').trim()).find((t) => t === '添加上下文' || t === '添加节点') || null),
      项: Array.from(e.querySelectorAll('[role=menuitem]')).map((i) => { const sp = Array.from(i.children).map((c) => (c.innerText || '').trim());
        return { 名: sp[0] || (i.innerText || '').trim().split('\n')[0], 禁用: i.getAttribute('aria-disabled') === 'true', 第二段: sp[1] || null }; }) };
  });
  await p.keyboard.press('Escape'); await p.waitForTimeout(800);
  return m;
};
const 可点集 = (m) => (m?.项 || []).filter((x) => !x.禁用).map((x) => x.名);
const 指纹 = (m) => JSON.stringify({ 标题: m?.标题, 可点: 可点集(m) });
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
const 找空白 = () => p.evaluate(() => {
  for (const [x, y] of [[140, 150], [1180, 150], [140, 640], [640, 660], [1180, 640], [200, 250], [1100, 300]]) {
    const e = document.elementFromPoint(x, y);
    if (e && (e.classList?.contains('react-flow__pane') || e.classList?.contains('react-flow__renderer'))) return [x, y];
  } return null;
});
const 前id = await id集();
rec.起点 = { 节点数: 前id.length, 积分: await R.credits(), 缩放: await R.zoom() };
const 靶 = await p.evaluate(() => { const n = document.querySelector('.react-flow__node-video'); if (!n) return null;
  const t = n.querySelector('[data-testid="flow-node-title"]');
  return { id: n.getAttribute('data-id'), 标题: t ? (t.innerText || '').trim().split('\n')[0] : null }; });
rec.靶子 = 靶;
rec.格 = [];
if (靶) {
  await p.mouse.move(640, 400); await p.waitForTimeout(250);
  await p.keyboard.press('Shift+Digit1'); await p.waitForTimeout(2400);
  for (const [名, tid] of [['1_before⊕', 'flow-node-target-connection-menu-button'], ['2_after⊕', 'flow-node-source-connection-menu-button']]) {
    const 行 = { 名 };
    try {
      const S = await 搜索选中(靶.标题); 行.选中 = S.选中集;
      if (!(S.成功 && S.选中集.includes(靶.id))) { 行.说明 = '没选中靶节点'; rec.格.push(行); continue; }
      const pt = await p.evaluate(({ id, tid }) => { const e = document.querySelector(`.react-flow__node[data-id="${id}"] [data-testid="${tid}"]`);
        if (!e) return null; const r = e.getBoundingClientRect();
        if (!(r.width > 2 && r.right > 0 && r.bottom > 0 && r.left < innerWidth && r.top < innerHeight)) return null;
        return { 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], aria: e.getAttribute('aria-label') }; }, { id: 靶.id, tid });
      行.按钮 = pt;
      if (!pt) { 行.说明 = '取不到 ⊕ 按钮'; rec.格.push(行); continue; }
      await p.mouse.click(pt.点[0], pt.点[1]); await p.waitForTimeout(1500);
      行.菜单 = await 读菜单(); 行.指纹 = 指纹(行.菜单);
    } catch (e) { 行.异常 = String(e).slice(0, 160); }
    rec.格.push(行);
    await p.keyboard.press('Escape'); await p.waitForTimeout(800);
  }
  { // 格 3：拖 source 手柄到空白松手
    const 行 = { 名: '3_拖手柄到空白' };
    try {
      await p.mouse.click(640, 690); await p.waitForTimeout(1200);
      行.拖前选中集 = await 选中集();
      const 热区 = await p.evaluate((i) => {
        const h = document.querySelector(`.react-flow__node[data-id="${i}"] [data-testid="flow-node-source-handle"]`); if (!h) return null;
        const r = h.getBoundingClientRect(); const 命中 = [];
        for (let x = Math.floor(r.left); x <= Math.floor(r.right); x += 4) for (let y = Math.floor(r.top); y <= Math.floor(r.bottom); y += 4) {
          if (x < 0 || y < 0 || x >= innerWidth || y >= innerHeight) continue;
          const e = document.elementFromPoint(x, y); if (!e) continue;
          if (!(e === h || h.contains(e) || (e.closest && e.closest('.react-flow__handle') === h))) continue;
          if (getComputedStyle(h, '::before').pointerEvents === 'auto') 命中.push([x, y]);
        }
        if (!命中.length) return { 成功: false, 原因: '没有 ::before:auto 的采样点' };
        const xs = 命中.map((q) => q[0]), ys = 命中.map((q) => q[1]);
        const bx = [Math.min(...xs), Math.max(...xs)], by = [Math.min(...ys), Math.max(...ys)];
        return { 成功: true, 采样点数: 命中.length, 命中包围盒: { x: bx[0], y: by[0], w: bx[1] - bx[0], h: by[1] - by[0] }, 起点: [Math.round((bx[0] + bx[1]) / 2), Math.round((by[0] + by[1]) / 2)] };
      }, 靶.id);
      行.手柄热区 = 热区;
      const 空白 = await 找空白(); 行.空白落点 = 空白;
      if (热区?.成功 && 空白) {
        await p.mouse.move(热区.起点[0], 热区.起点[1]); await p.waitForTimeout(300);
        await p.mouse.down(); await p.waitForTimeout(200);
        for (let k = 1; k <= 12; k++) { await p.mouse.move(Math.round(热区.起点[0] + (空白[0] - 热区.起点[0]) * k / 12), Math.round(热区.起点[1] + (空白[1] - 热区.起点[1]) * k / 12)); await p.waitForTimeout(90); }
        await p.mouse.up(); await p.waitForTimeout(1600);
        行.菜单 = await 读菜单(); 行.指纹 = 指纹(行.菜单);
        行.拖后节点数 = await 节点数(); 行.拖后选中集 = await 选中集();
      } else 行.说明 = 热区?.成功 ? '找不到空白落点' : '取不到手柄热区';
    } catch (e) { 行.异常 = String(e).slice(0, 160); }
    rec.格.push(行);
  }
  const G = Object.fromEntries(rec.格.map((g) => [g.名, g.指纹]));
  rec.判定 = { 格1_before: G['1_before⊕'] || null, 格2_after: G['2_after⊕'] || null, 格3_拖手柄: G['3_拖手柄到空白'] || null };
  rec.判定['before≠after'] = !!(G['1_before⊕'] && G['2_after⊕'] && G['1_before⊕'] !== G['2_after⊕']);
  rec.判定.拖手柄等于after = !!(G['3_拖手柄到空白'] && G['2_after⊕'] && G['3_拖手柄到空白'] === G['2_after⊕']);
  rec.判定.拖手柄等于before = !!(G['3_拖手柄到空白'] && G['1_before⊕'] && G['3_拖手柄到空白'] === G['1_before⊕']);
}
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

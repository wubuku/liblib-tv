// 批次 184：**把「入口 2（从手柄拖到空白松手）打开的是哪个方向」实测出来。**
//
// 为什么非做不可：手册 `connect-nodes.md` **自相矛盾** ——
//   第 103 行（批次 72）已经写明「🔴 它属于 **after 方向**（「添加节点」那一套），
//     **不是** before」，并给了硬证据；
//   第 267 行却还留着「⚠️ 入口 2 打开的是哪一个方向，本批**未取证**，暂不写结论」。
// ⇒ 用户读到的是「这个没测」。批次 92 的教训：**改了结论 ≠ 引用它的地方也被改了**。
//   本批按 183 的纪律做：**先实测、再改那一行**，不靠抄第 103 行。
//
// 实验设计（**同一个节点实例**内三格对照，只换「怎么打开菜单」）：
//   格 1 点**左边** before ⊕  → 读菜单标题 + 哪些项可点
//   格 2 点**右边** after  ⊕  → 同上
//   格 3 **从 source 手柄拖到空白松手** → 同上
// ⇒ 判方向**不靠标题**（标题可能被复用），靠**「七项里谁可点」这个指纹**：
//   若格 3 的可点集与格 2 逐项一致 ⇒ 属 after；若与格 1 一致 ⇒ 属 before。
//
// 🔴 手柄的坑（手册第 117-119 行已记）：手柄元素本体 `pointer-events` **永远是 none**，
//   真正能接指针的是它的 `::before`（40×80）。所以起手点**不能**取元素中心，
//   必须**扫一遍找出 `::before` 的 pointer-events 为 auto 的那片区域**再取其中点。
//
// ⛔ 不生成、不分享、不下载、不点「保存到主体库」；不点任何 ⊕ 菜单项（只读菜单）。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '184' };
await settle(p, R);
await p.mouse.move(1250, 10); await p.waitForTimeout(600);

const 节点数 = () => p.evaluate(() => document.querySelectorAll('.react-flow__node').length);
const id集 = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')).sort());
const 选中集 = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));

/** 打开菜单并读它的「指纹」：标题 ＋ 七项逐项（可点 / 禁用 ＋ 禁用原因）。 */
const 读菜单 = async () => {
  const m = await p.evaluate(() => {
    const e = document.querySelector('[data-testid="canvas-context-menu"]');
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return { 几何: { w: Math.round(r.width), h: Math.round(r.height) },
      标题: (Array.from(e.querySelectorAll('*')).map((x) => (x.innerText || '').trim())
        .find((t) => t === '添加上下文' || t === '添加节点') || null),
      项: Array.from(e.querySelectorAll('[role=menuitem]')).map((i) => {
        const sp = Array.from(i.children).map((c) => (c.innerText || '').trim());
        return { 名: sp[0] || (i.innerText || '').trim().split('\n')[0], 禁用: i.getAttribute('aria-disabled') === 'true', 第二段: sp[1] || null };
      }) };
  });
  await p.keyboard.press('Escape'); await p.waitForTimeout(800);
  return m;
};
const 可点集 = (m) => (m?.项 || []).filter((x) => !x.禁用).map((x) => x.名);
const 指纹 = (m) => JSON.stringify({ 标题: m?.标题, 可点: 可点集(m) });

/** 找一个**确实是空白**的落点：elementFromPoint 必须落在画布 pane 上。 */
const 找空白 = () => p.evaluate(() => {
  for (const [x, y] of [[140, 150], [1180, 150], [140, 640], [640, 660], [1180, 640], [200, 250], [1100, 300]]) {
    const e = document.elementFromPoint(x, y);
    if (e && (e.classList?.contains('react-flow__pane') || e.classList?.contains('react-flow__renderer'))) return [x, y, e.className];
  }
  return null;
});

const 搜索选中 = async (关键词) => {
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
  return { 成功: s.length >= 1, 选中集: s, 命中: 命中.slice(0, 2) };
};

const 前id = await id集();
rec.起点 = { 节点数: 前id.length, 状态行: await R.status(), 积分: await R.credits(), 缩放: await R.zoom() };

// 靶子：**带资源的图片节点**（有资源 ⇒ 两边 ⊕ 的可点集才有区分度；空节点两边可能一样）
const 靶 = await p.evaluate(() => {
  const n = document.querySelector('.react-flow__node-image') ||
    Array.from(document.querySelectorAll('.react-flow__node')).find((x) => /node-image/.test(x.className));
  if (!n) return null;
  const t = n.querySelector('[data-testid="flow-node-title"]');
  return { id: n.getAttribute('data-id'), 标题: t ? (t.innerText || '').trim().split('\n')[0] : null, 有img: !!n.querySelector('img') };
});
rec.靶子 = 靶;
rec.格 = [];

if (靶) {
  // 适配画布，让靶节点与空白落点都在视口内
  await p.mouse.move(640, 400); await p.waitForTimeout(250);
  await p.keyboard.press('Shift+Digit1'); await p.waitForTimeout(2400);
  rec.适配后缩放 = await R.zoom();

  // ── 格 1 / 格 2：before ⊕ 与 after ⊕（**要选中才出现**）
  for (const [名, testid] of [['1_before⊕', 'flow-node-target-connection-menu-button'], ['2_after⊕', 'flow-node-source-connection-menu-button']]) {
    const 行 = { 名 };
    try {
      const S = await 搜索选中(靶.标题);
      行.选中 = S.选中集;
      if (!(S.成功 && S.选中集.includes(靶.id))) { 行.说明 = '没选中靶节点'; rec.格.push(行); continue; }
      const pt = await p.evaluate((i, tid) => { const e = document.querySelector(`.react-flow__node[data-id="${i}"] [data-testid="${tid}"]`);
        if (!e) return null; const r = e.getBoundingClientRect();
        if (!(r.width > 2 && r.right > 0 && r.bottom > 0 && r.left < innerWidth && r.top < innerHeight)) return null;
        return { 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 几何: { w: Math.round(r.width), h: Math.round(r.height) }, aria: e.getAttribute('aria-label') }; }, 靶.id, testid);
      行.按钮 = pt;
      if (!pt) { 行.说明 = '取不到 ⊕ 按钮坐标'; rec.格.push(行); continue; }
      await p.mouse.click(pt.点[0], pt.点[1]); await p.waitForTimeout(1500);
      行.菜单 = await 读菜单();
      行.指纹 = 指纹(行.菜单);
    } catch (e) { 行.异常 = String(e).slice(0, 160); }
    rec.格.push(行);
    await p.keyboard.press('Escape'); await p.waitForTimeout(800);
  }

  // ── 格 3：拖 source 手柄到空白松手（**不选中** —— 选中时手柄 pointer-events 是 none）
  {
    const 行 = { 名: '3_拖手柄到空白' };
    try {
      await p.mouse.click(640, 690); await p.waitForTimeout(1200);   // 点空白取消选中
      行.拖前选中集 = await 选中集();
      // 扫出 `::before` 的 pointer-events 为 auto 的区域
      const 热区 = await p.evaluate((i) => {
        const h = document.querySelector(`.react-flow__node[data-id="${i}"] [data-testid="flow-node-source-handle"]`);
        if (!h) return null;
        const r = h.getBoundingClientRect();
        if (!(r.width > 1)) return null;
        const 命中 = [];
        for (let x = Math.floor(r.left); x <= Math.floor(r.right); x += 4)
          for (let y = Math.floor(r.top); y <= Math.floor(r.bottom); y += 4) {
            if (x < 0 || y < 0 || x >= innerWidth || y >= innerHeight) continue;
            const e = document.elementFromPoint(x, y);
            if (!e) continue;
            const 是它 = e === h || h.contains(e) || (e.closest && e.closest('.react-flow__handle') === h);
            if (!是它) continue;
            const cs = getComputedStyle(h, '::before');
            if (cs.pointerEvents === 'auto') 命中.push([x, y]);
          }
        if (!命中.length) return { 成功: false, 原因: '::before 区域里没有 pointer-events:auto 的采样点', 手柄框: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) } };
        const xs = 命中.map((q) => q[0]), ys = 命中.map((q) => q[1]);
        const bx = [Math.min(...xs), Math.max(...xs)], by = [Math.min(...ys), Math.max(...ys)];
        return { 成功: true, 采样点数: 命中.length, 命中包围盒: { x: bx[0], y: by[0], w: bx[1] - bx[0], h: by[1] - by[0] },
          手柄框: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
          起点: [Math.round((bx[0] + bx[1]) / 2), Math.round((by[0] + by[1]) / 2)] };
      }, 靶.id);
      行.手柄热区 = 热区;
      const 空白 = await 找空白();
      行.空白落点 = 空白;
      if (!热区?.成功 || !空白) { 行.说明 = 热区?.成功 ? '找不到空白落点' : '取不到手柄热区'; rec.格.push(行); }
      else {
        await p.mouse.move(热区.起点[0], 热区.起点[1]); await p.waitForTimeout(300);
        await p.mouse.down(); await p.waitForTimeout(200);
        for (let k = 1; k <= 12; k++) {
          await p.mouse.move(Math.round(热区.起点[0] + (空白[0] - 热区.起点[0]) * k / 12),
            Math.round(热区.起点[1] + (空白[1] - 热区.起点[1]) * k / 12));
          await p.waitForTimeout(90);
        }
        await p.mouse.up(); await p.waitForTimeout(1600);
        行.菜单 = await 读菜单();
        行.指纹 = 指纹(行.菜单);
        行.拖后节点数 = await 节点数();
        行.拖后选中集 = await 选中集();
        rec.格.push(行);
      }
    } catch (e) { 行.异常 = String(e).slice(0, 160); rec.格.push(行); }
  }

  // ── 判方向：三格指纹对比
  const G = Object.fromEntries(rec.格.map((g) => [g.名, g.指纹]));
  rec.判定 = { 格1_before: G['1_before⊕'] || null, 格2_after: G['2_after⊕'] || null, 格3_拖手柄: G['3_拖手柄到空白'] || null };
  rec.判定.拖手柄等于after = !!(G['3_拖手柄到空白'] && G['2_after⊕'] && G['3_拖手柄到空白'] === G['2_after⊕']);
  rec.判定.拖手柄等于before = !!(G['3_拖手柄到空白'] && G['1_before⊕'] && G['3_拖手柄到空白'] === G['1_before⊕']);
  rec.判定.三者互不相同 = new Set(Object.values(G).filter(Boolean)).size === 3;
}

await p.keyboard.press('Escape'); await p.waitForTimeout(700);
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

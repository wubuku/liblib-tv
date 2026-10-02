// Batch BV — ⭐ 断线入口：从「键盘快捷键」转向「连线上那枚按钮」。
//
// ⭐⭐ 本批的起点是手册里**早就写着、却一直没被串起来**的一条：
//   官方快捷键面板里 `⌘L` 是「**连线**」，不是「断线」。
//   ⇒ BJ 那轮试的「八种 ⌘L 条件」全部失效，原因不是条件不够，
//     而是**我一直在按「连接」快捷键去找「断开」功能**。
//   ⇒ 而且那张面板里**根本没有断线快捷键** —— 入口只能是界面上的按钮。
//
// ⭐ 假设来自本仓库的复刻原型 `src/components/nodes/DeletableEdge.tsx`：
//   它用 `EdgeLabelRenderer` 在**连线中点**放一枚 `aria-label="删除连线"` 的**剪刀**按钮，
//   靠 `isActive` 显形（否则 `opacity-0 pointer-events-none`）。
//   ⚠️ **复刻原型不是产品源码**，只能当假设生成器 —— 本轮所有结论都必须在真站上读到才算数。
//
// 探测方法（避免「又猜错了位置」）：
//   连线是 SVG `<path>`，用 `getPointAtLength(总长/2)` 取**几何中点**，
//   再用 `getScreenCTM()` 换算成屏幕坐标 —— 不靠包围盒取中心，不猜。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBV';
const { browser, page } = await launch();

const esc = async () => { await page.keyboard.press('Escape'); await page.waitForTimeout(900); };
const findAria = (label) => page.evaluate((l) => [...document.querySelectorAll('button,[role="button"],[aria-label]')]
  .filter((x) => x.getAttribute('aria-label') === l)
  .map((x) => { const r = x.getBoundingClientRect();
    return { at: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      visible: r.width >= 4 && r.height >= 4 }; }), label);

/** ⭐ 列出所有连线，并用 path 几何算出**精确中点**的屏幕坐标。 */
const edges = () => page.evaluate(() => {
  const wrap = document.querySelector('.react-flow__viewport');
  const ctm = wrap ? wrap.getScreenCTM() : null;
  const toScreen = (pt) => {
    if (!ctm) return null;
    const p = new DOMPoint(pt.x, pt.y).matrixTransform(ctm);
    return [Math.round(p.x), Math.round(p.y)];
  };
  const out = [];
  for (const g of document.querySelectorAll('.react-flow__edge')) {
    const path = g.querySelector('path.react-flow__edge-path, path');
    let mid = null, len = null;
    if (path && path.getTotalLength) {
      try { len = path.getTotalLength(); mid = toScreen(path.getPointAtLength(len / 2)); } catch { /* 忽略 */ }
    }
    const gb = g.getBoundingClientRect();
    out.push({
      id: g.getAttribute('data-id') || g.id || null,
      aria: g.getAttribute('aria-label'),
      cls: (g.className?.baseVal ?? g.className ?? '').toString().slice(0, 60),
      pathLen: len ? Math.round(len) : null,
      mid,
      bboxCenter: [Math.round(gb.x + gb.width / 2), Math.round(gb.y + gb.height / 2)],
      bbox: [Math.round(gb.x), Math.round(gb.y), Math.round(gb.width), Math.round(gb.height)],
      // ⭐ 连线上**已经**挂着的可交互件（EdgeLabelRenderer 渲染的按钮通常在这里）
      innerBtns: [...g.querySelectorAll('button,[role="button"],[aria-label]')].map((b) => {
        const r = b.getBoundingClientRect();
        return { aria: b.getAttribute('aria-label'), t: (b.innerText || '').trim().slice(0, 10),
          op: getComputedStyle(b).opacity, pe: getComputedStyle(b).pointerEvents,
          at: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; }),
      svgCount: g.querySelectorAll('svg').length,
    });
  }
  return { edges: out, viewportTransform: wrap ? (wrap.style.transform || null) : null };
});

/** 全页扫一遍：有没有 aria-label 或文字带「连线/删除/断开/移除」的按钮。 */
const scanConnect = () => page.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; };
  const btns = [...document.querySelectorAll('button,[role="button"],[aria-label]')].filter(vis)
    .map((b) => { const r = b.getBoundingClientRect();
      return { aria: b.getAttribute('aria-label'), t: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 14),
        op: getComputedStyle(b).opacity, pe: getComputedStyle(b).pointerEvents,
        at: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        inEdge: !!b.closest('.react-flow__edge') }; })
    .filter((b) => /连线|连接|断开|移除|删除/.test((b.aria || '') + ' ' + (b.t || '')));
  return { btns, edgeBtnTotal: document.querySelectorAll('.react-flow__edge button').length };
});

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(2000);
  await beginBatch(B, { note: '断线入口：⌘L 是「连线」不是「断线」；去连线中点找按钮' });
  const out = {};

  // ── ① 先把快捷键面板里「创作」那一列逐字读出来当证据
  console.log(`═══ ① 快捷键面板里跟「连线」有关的条目 ═══`);
  await clickAriaQuick('快捷键');
  await page.waitForTimeout(1800);
  const kb = await page.evaluate(() => {
    const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    const leaves = [...document.querySelectorAll('div,span,td,li,p')].filter(vis)
      .map((e) => ({ t: (e.innerText || '').replace(/\s+/g, ' ').trim(), kids: e.children.length,
        w: Math.round(e.getBoundingClientRect().width), h: Math.round(e.getBoundingClientRect().height) }))
      .filter((x) => x.kids === 0 && x.t && x.t.length <= 26 && x.w > 10 && x.h >= 10 && x.h <= 40);
    const text = (document.body.innerText || '');
    return {
      提到连线的行: leaves.map((x) => x.t).filter((t) => /连线|连接|断开/.test(t))
        .filter((v, i, a) => a.indexOf(v) === i).slice(0, 20),
      有没有断开: /断开连线|删除连线/.test(text),
      有没有回收站: /回收站|垃圾桶| trash/i.test(text),
      撤销相关: leaves.map((x) => x.t).filter((t) => /撤销|重做|恢复|历史/.test(t))
        .filter((v, i, a) => a.indexOf(v) === i).slice(0, 12),
    };
  });
  out.shortcutPanel = kb;
  console.log(`  提到「连线/连接/断开」的行：${JSON.stringify(kb.提到连线的行)}`);
  console.log(`  ⭐ 面板里有没有「断开连线 / 删除连线」？ ${kb.有没有断开 ? '✅ 有' : '❌ 没有'}`);
  console.log(`  ⭐ 面板里有没有「回收站 / 垃圾桶」？ ${kb.有没有回收站 ? '✅ 有' : '❌ 没有'}`);
  console.log(`  撤销/历史相关：${JSON.stringify(kb.撤销相关)}`);
  await esc(); await esc();

  // ── ② 连线几何
  const E = await edges(); out.edges = E;
  console.log(`\n═══ ② 连线清单（${E.edges.length} 条）═══`);
  E.edges.forEach((e, i) => console.log(`  ${i + 1}. id=${e.id}｜aria=${JSON.stringify(e.aria)}\n     路径长=${e.pathLen}｜几何中点=${JSON.stringify(e.mid)}｜包围盒中心=${JSON.stringify(e.bboxCenter)}\n     线上已挂按钮=${e.innerBtns.length} ${JSON.stringify(e.innerBtns)}｜svg=${e.svgCount}`));
  if (!E.edges.length) { console.log('  ⛔ 视口里没有连线'); }

  // ── ③ ⭐ 悬停连线中点，找那枚按钮
  console.log(`\n═══ ③ 逐条悬停连线中点 ═══`);
  const hovers = [];
  for (const [i, e] of E.edges.entries()) {
    const pt = e.mid || e.bboxCenter;
    if (!pt) { hovers.push({ i, skipped: '没有可用坐标' }); continue; }
    await page.mouse.move(400, 400); await page.waitForTimeout(600);   // 先移开
    const before = await scanConnect();
    await page.mouse.move(pt[0], pt[1]); await page.waitForTimeout(1600);
    const after = await scanConnect();
    const E2 = await edges();
    const e2 = E2.edges[i];
    const newBtns = after.btns.filter((b) => !before.btns.some((x) => x.at[0] === b.at[0] && x.at[1] === b.at[1]));
    const atMid = after.btns.filter((b) => Math.abs(b.at[0] - pt[0]) < 60 && Math.abs(b.at[1] - pt[1]) < 60);
    hovers.push({ i, id: e.id, hoverAt: pt, edgeBtnsAfter: e2?.innerBtns,
      newBtns, atMid, total: after.btns.length });
    console.log(`  ${i + 1}. 悬停 @${JSON.stringify(pt)} → 悬停后连线内按钮 ${e2?.innerBtns.length ?? '?'} 个 ${JSON.stringify(e2?.innerBtns)}`);
    console.log(`     新冒出来的相关按钮：${JSON.stringify(newBtns)}`);
    console.log(`     中点附近的相关按钮：${JSON.stringify(atMid)}`);
    if (i === 0) await shot(page, 'M-279-悬停连线中点.png');
  }
  out.hovers = hovers;
  const anyBtn = hovers.some((h) => (h.newBtns?.length || 0) > 0 || (h.edgeBtnsAfter?.length || 0) > 0);
  out.found = anyBtn;
  console.log(`\n  ⭐⭐ 悬停能唤出「删除连线」类按钮吗？ ${anyBtn ? '✅ 能' : '❌ 不能（悬停这条路不通）'}`);

  // ── ④ 换一招：直接点连线本身，看它会不会被选中 / 冒出面板
  console.log(`\n═══ ④ 直接点连线本身 ═══`);
  const clicks = [];
  for (const [i, e] of E.edges.entries()) {
    const pt = e.mid || e.bboxCenter;
    await page.mouse.click(pt[0], pt[1]); await page.waitForTimeout(1800);
    const st = await page.evaluate(() => {
      const vis = (x) => { const r = x.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
      return { selectedEdges: document.querySelectorAll('.react-flow__edge.selected, .react-flow__edge[aria-selected="true"]').length,
        selectedNodes: document.querySelectorAll('.react-flow__node.selected').length,
        edgeBtns: document.querySelectorAll('.react-flow__edge button').length,
        focus: document.activeElement?.tagName + '/' + (document.activeElement?.className || '').toString().slice(0, 30) }; });
    clicks.push({ i, id: e.id, at: pt, ...st });
    console.log(`  ${i + 1}. 点 @${JSON.stringify(pt)} → ${JSON.stringify(st)}`);
  }
  out.clicks = clicks;
  const sel = clicks.some((c) => c.selectedEdges > 0);
  console.log(`  ⭐ 点连线会选中它吗？ ${sel ? '✅ 会' : '❌ 不会'}`);
  if (sel) await shot(page, 'M-280-选中连线之后.png');
  await esc();

  console.log(`\n═══ 本轮结论 ═══`);
  console.log(`  · 快捷键面板里有断线快捷键吗？ ${kb.有没有断开 ? '有' : '❌ 没有'}`);
  console.log(`  · 悬停连线中点能唤出删除按钮吗？ ${anyBtn ? '✅ 能' : '❌ 不能'}`);
  console.log(`  · 点连线能选中它吗？ ${sel ? '✅ 能' : '❌ 不能'}`);
  console.log(`  · 面板里有回收站字样吗？ ${kb.有没有回收站 ? '有' : '❌ 没有'}`);

  await logStep(B, {
    id: 'BV-disconnect-entry-on-edge',
    title: '⭐ 断线入口不在键盘上：⌘L 是「连线」，面板里根本没有断线快捷键',
    target: '本批的起点是手册里早就写着、却一直没串起来的一条：**官方快捷键面板里 `⌘L` 对应'
      + '「连线」而不是「断线」** —— BJ 那轮「八种 ⌘L 条件」失效的真正原因是'
      + '**一直在按连接快捷键找断开功能**，而不是条件不够。'
      + '而那张面板里**根本没有断线快捷键**，所以入口只能是界面上的按钮。'
      + '假设来自本仓库复刻原型 `src/components/nodes/DeletableEdge.tsx`：'
      + '用 `EdgeLabelRenderer` 在**连线中点**放一枚 `aria-label="删除连线"` 的剪刀按钮，'
      + '靠 `isActive` 显形。⛔ **复刻原型不是产品源码，只当假设生成器**，'
      + '本轮每条结论都在真站上读到才算数。'
      + '探测方法：用 `path.getPointAtLength(总长/2)` 取**几何中点**、'
      + '`getScreenCTM()` 换算屏幕坐标 —— 不靠包围盒取中心、不猜位置。'
      + '三招依次试：① 悬停中点 ② 直接点连线 ③（备用）读面板里所有相关按钮。',
    evidence: out,
    visible_text: JSON.stringify({
      快捷键面板: out.shortcutPanel,
      连线: out.edges?.edges?.map((e) => ({ id: e.id, aria: e.aria, pathLen: e.pathLen,
        几何中点: e.mid, 包围盒中心: e.bboxCenter, 线上按钮: e.innerBtns })),
      悬停: out.hovers?.map((h) => ({ i: h.i, hoverAt: h.hoverAt, 线上按钮: h.edgeBtnsAfter,
        新按钮: h.newBtns, 中点附近: h.atMid })),
      点连线: out.clicks,
      结论: { 面板有断线快捷键: out.shortcutPanel?.有没有断开,
        悬停能唤出删除按钮: out.found, 点连线能选中: out.clicks?.some?.((c) => c.selectedEdges > 0),
        面板有回收站字样: out.shortcutPanel?.有没有回收站 } }).slice(0, 3400),
    shot: 'M-279-悬停连线中点.png',
  });
  console.log('\nBV 完成');

  async function clickAriaQuick(label) {
    const p = await findAria(label);
    const v = p.filter((x) => x.visible);
    if (!v.length) { console.log(`  ⛔ 找不到 ${label}`); return false; }
    await page.mouse.click(v[0].at[0], v[0].at[1]); return true;
  }
} catch (e) {
  console.log('⛔ 中止：' + e.message + '\n' + (e.stack || '').split('\n').slice(0, 4).join('\n'));
} finally {
  await browser.close();
}

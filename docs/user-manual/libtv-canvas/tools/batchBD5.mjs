// Batch BD5 —— 网格吸附（这轮才算点到）+ 连线真的隐藏了吗 + 整理画布按下去的效果。
//
// BD4 修正判据后拿到的两件事：
//   ⭐ `隐藏节点连线` 点一下，**aria 从「隐藏节点连线」变成「显示节点连线」**，再点回来。
//     这正是 BD3「按旧 aria 找不到了」的真相 —— 它**不用 active class 表达状态，
//     改用按钮文案切换**。这是两种完全不同的状态表达方式，必须分开写进手册。
//   ⭐ 蓝点 5 个全部 `pointer-events: none`，归属查清：TV Director(12×12)、
//     模型下拉(6×6)、以及预设里的 **`调度故事板` / `故事板` / `人像质感调节`** ——
//     **正好三个，与手册已写的完全一致**。
//
// ⚠️ BD4 自己犯了索引错：工具条 0..4 依次是
//   `整理画布` / `切换小地图` / `隐藏节点连线` / `网格吸附` / `缩放选项`，
//   BD4 测了 0/1/2 就以为测完了三枚开关，**网格吸附（=3）根本没点**，
//   后面 `tap(page, 2)` 想点网格吸附，其实点的是「隐藏节点连线」。
//   这轮用 **aria 名字**找，不再用下标 —— 下标是这轮踩到的坑。
//
// 这轮三件事，每件都用**「业务副作用」当判据**，不再看样式：
//   1. 网格吸附：aria 会不会改名？点开后拖节点，落点是不是网格倍数？
//   2. 隐藏节点连线：`.react-flow__edge` 元素数量点前点后各是多少？
//   3. 整理画布（`⌥⇧F`）：点下去画布上节点位置有没有变？
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBD5';
const { browser, page } = await launch();

/** 按 aria **全等**找左下工具条上的按钮 —— 不再用下标（BD4 踩过）。 */
async function find(pg, aria) {
  return pg.evaluate((name) => {
    const e = [...document.querySelectorAll('button,[role="button"]')]
      .find((x) => x.getAttribute('aria-label') === name);
    if (!e) return { err: '没找到 ' + name };
    const r = e.getBoundingClientRect();
    return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2),
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
  }, aria);
}

/** 点一下，再把鼠标挪开，然后回读这一组里所有按钮的 aria。 */
async function tap(pg, aria) {
  const p = await find(pg, aria);
  if (p.err) return { err: p.err };
  await pg.mouse.move(p.x, p.y); await pg.waitForTimeout(250);
  await pg.mouse.click(p.x, p.y);
  await pg.waitForTimeout(1900);
  await pg.mouse.move(720, 260); await pg.waitForTimeout(800);
  return { clicked: p.rect, bar: await barAria(pg) };
}

const barAria = (pg) => pg.evaluate(() => [...document.querySelectorAll('button,[role="button"]')]
  .filter((e) => { const r = e.getBoundingClientRect();
    return r.y > 750 && r.y < 800 && r.x > 100 && r.x < 300 && r.width >= 20 && r.width <= 40; })
  .sort((a, b) => a.getBoundingClientRect().x - b.getBoundingClientRect().x)
  .map((e) => { const cs = getComputedStyle(e);
    return { aria: e.getAttribute('aria-label'),
      active: /bg-canvas-controls-active/.test(e.className || ''), bg: cs.backgroundColor }; }));

/** 画布的业务状态：连线数、节点数与位置。 */
const scene = (pg) => pg.evaluate(() => ({
  edges: document.querySelectorAll('.react-flow__edge').length,
  edgePaths: document.querySelectorAll('.react-flow__edge path').length,
  nodes: [...document.querySelectorAll('.react-flow__node')].map((n) => {
    const r = n.getBoundingClientRect();
    return { id: n.getAttribute('data-id'), x: Math.round(r.x), y: Math.round(r.y) }; }),
}));

const nodePts = (pg) => pg.evaluate(() => {
  const res = {};
  for (const n of document.querySelectorAll('.react-flow__node')) {
    const r = n.getBoundingClientRect();
    for (let fy = 0.2; fy <= 0.8; fy += 0.15) for (let fx = 0.06; fx <= 0.95; fx += 0.06) {
      const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
      const o = document.elementFromPoint(x, y);
      if (o && o.closest('.react-flow__node') === n) { res[n.getAttribute('data-id')] = { x, y }; break; }
    }
  }
  return res;
});

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await fitView(page); await page.waitForTimeout(1600);
  await page.mouse.move(720, 260); await page.waitForTimeout(900);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '网格吸附按 aria 找到真按钮 / 连线 aria 改名是否真生效 / 整理画布副作用' });

  const out = {};
  out.bar0 = await barAria(page);
  out.scene0 = await scene(page);
  console.log('初始工具条:', JSON.stringify(out.bar0));
  console.log(`初始场景：连线 ${out.scene0.edges} 条（path ${out.scene0.edgePaths}）/ 节点 ${out.scene0.nodes.length}`);

  // ═══ 1：隐藏节点连线 —— aria 改名，**连线数真的变了吗**
  console.log('\n--- 隐藏节点连线 ---');
  const e1 = await tap(page, '隐藏节点连线');
  out.edge = { afterClick1: e1, scene1: await scene(page) };
  console.log('点一下后工具条:', JSON.stringify(e1.bar));
  console.log(`  连线数 ${out.scene0.edges} → ${out.edge.scene1.edges}（path ${out.scene0.edgePaths} → ${out.edge.scene1.edgePaths}）`);
  const e2 = await tap(page, '显示节点连线');
  out.edge.afterClick2 = e2; out.edge.scene2 = await scene(page);
  console.log('再点一下:', JSON.stringify(e2.bar));
  console.log(`  连线数 → ${out.edge.scene2.edges}（path → ${out.edge.scene2.edgePaths}）`);
  out.edge.ariaSwaps = (e1.bar.find((b) => /节点连线/.test(b.aria || '')) || {}).aria === '显示节点连线';
  out.edge.effective = out.edge.scene1.edges !== out.scene0.edges;
  await shot(page, 'M-186-隐藏节点连线-开启.png');
  out.shot = 'M-186-隐藏节点连线-开启.png';

  // ═══ 2：网格吸附 —— 这回按 aria 找，且判据含「aria 改名」和「拖动落点」
  console.log('\n--- 网格吸附 ---');
  const g1 = await tap(page, '网格吸附');
  out.grid = { after1: g1.bar, scene1: await scene(page) };
  const gAria = g1.bar.find((b) => b.aria === '网格吸附' || /吸附/.test(b.aria || ''));
  console.log('点一下后 网格吸附 那枚:', JSON.stringify(gAria));
  out.grid.ariaChanged = gAria.aria !== '网格吸附';
  out.grid.activeAfter = gAria.active;
  console.log('  aria 改名？', out.grid.ariaChanged, ' active？', gAria.active);

  if (gAria.active || out.grid.ariaChanged) {
    const pts = await nodePts(page);
    const id = Object.keys(pts)[0];
    const p = pts[id];
    const g0 = (await scene(page)).nodes.find((n) => n.id === id);
    await page.mouse.move(p.x, p.y); await page.mouse.down();
    for (let i = 1; i <= 12; i += 1) { await page.mouse.move(p.x + 3.1 * i, p.y + 2.3 * i); await page.waitForTimeout(60); }
    await page.mouse.up(); await page.waitForTimeout(1900);
    const g1pos = (await scene(page)).nodes.find((n) => n.id === id);
    const mv = [g1pos.x - g0.x, g1pos.y - g0.y];
    console.log(`  吸附开：请求 (+37,+28) → 实际 ${JSON.stringify(mv)}`);
    out.grid.drag = { requested: [37, 28], actual: mv,
      by10: mv[0] % 10 === 0 && mv[1] % 10 === 0, by20: mv[0] % 20 === 0 && mv[1] % 20 === 0,
      by8: mv[0] % 8 === 0 && mv[1] % 8 === 0, by4: mv[0] % 4 === 0 && mv[1] % 4 === 0 };
    console.log('  是否网格倍数:', JSON.stringify(out.grid.drag));
    await shot(page, 'M-180-网格吸附-打开.png');
    out.shot2 = 'M-180-网格吸附-打开.png';
    // 拖回去
    const pts2 = await nodePts(page);
    const p2 = pts2[id];
    if (p2) {
      await page.mouse.move(p2.x, p2.y); await page.mouse.down();
      for (let i = 1; i <= 10; i += 1) { await page.mouse.move(p2.x - mv[0] * i / 10, p2.y - mv[1] * i / 10); await page.waitForTimeout(55); }
      await page.mouse.up(); await page.waitForTimeout(1600);
      const g2pos = (await scene(page)).nodes.find((n) => n.id === id);
      out.grid.drag.residual = [g2pos.x - g0.x, g2pos.y - g0.y];
      console.log('  拖回残差:', JSON.stringify(out.grid.drag.residual));
    }
    // 关回去
    const nameNow = (await barAria(page)).find((b) => /吸附/.test(b.aria || ''));
    out.grid.ariaWhenOn = nameNow.aria;
    if (/吸附/.test(nameNow.aria)) { await tap(page, nameNow.aria); }
    const back = (await barAria(page)).find((b) => /吸附/.test(b.aria || ''));
    out.grid.afterOff = back;
    console.log('  关回后:', JSON.stringify(back));
  } else {
    console.log('  ⚠️ 点下去 aria/active 都没变 —— 用业务判据再试一次（拖节点看落点）');
    const pts = await nodePts(page);
    const id = Object.keys(pts)[0];
    const p = pts[id];
    const g0 = (await scene(page)).nodes.find((n) => n.id === id);
    await page.mouse.move(p.x, p.y); await page.mouse.down();
    for (let i = 1; i <= 12; i += 1) { await page.mouse.move(p.x + 3.1 * i, p.y + 2.3 * i); await page.waitForTimeout(60); }
    await page.mouse.up(); await page.waitForTimeout(1900);
    const g1pos = (await scene(page)).nodes.find((n) => n.id === id);
    const mv = [g1pos.x - g0.x, g1pos.y - g0.y];
    out.grid.drag = { requested: [37, 28], actual: mv,
      by4: mv[0] % 4 === 0 && mv[1] % 4 === 0, by8: mv[0] % 8 === 0 && mv[1] % 8 === 0 };
    console.log('  拖动落点:', JSON.stringify(out.grid.drag));
    const pts2 = await nodePts(page);
    const p2 = pts2[id];
    if (p2) {
      await page.mouse.move(p2.x, p2.y); await page.mouse.down();
      for (let i = 1; i <= 10; i += 1) { await page.mouse.move(p2.x - mv[0] * i / 10, p2.y - mv[1] * i / 10); await page.waitForTimeout(55); }
      await page.mouse.up(); await page.waitForTimeout(1600);
      out.grid.drag.residual = [(await scene(page)).nodes.find((n) => n.id === id).x - g0.x,
        (await scene(page)).nodes.find((n) => n.id === id).y - g0.y];
    }
  }
  await page.mouse.move(720, 260); await page.waitForTimeout(800);
  await shot(page, 'M-179-网格吸附-关闭.png');
  out.shot3 = 'M-179-网格吸附-关闭.png';
  out.grid.finalBar = await barAria(page);

  // ═══ 3：整理画布（`⌥⇧F`）按下去有没有可见效果
  console.log('\n--- 整理画布 ---');
  const s0 = await scene(page);
  await page.keyboard.press('Meta+Alt+f'); await page.waitForTimeout(2600); await clearToasts(page);
  const s1 = await scene(page);
  const moved = s0.nodes.filter((n, i) => { const m = s1.nodes.find((x) => x.id === n.id); return m && (m.x !== n.x || m.y !== n.y); });
  console.log(`  按 ⌥⇧F：节点数 ${s0.nodes.length} → ${s1.nodes.length}，位置变了的 ${moved.length} 个`);
  out.tidy = { before: { n: s0.nodes.length, pos: s0.nodes }, after: { n: s1.nodes.length, pos: s1.nodes },
    movedCount: moved.length, moved: moved.slice(0, 4),
    changed: s0.nodes.length !== s1.nodes.length || moved.length > 0 };
  // 复原位置
  for (const m of moved) {
    const cur = s1.nodes.find((x) => x.id === m.id);
    const dx = m.x - cur.x, dy = m.y - cur.y;
    const pts = await nodePts(page);
    const p = pts[m.id];
    if (!p) continue;
    await page.mouse.move(p.x, p.y); await page.mouse.down();
    for (let i = 1; i <= 10; i += 1) { await page.mouse.move(p.x + dx * i / 10, p.y + dy * i / 10); await page.waitForTimeout(50); }
    await page.mouse.up(); await page.waitForTimeout(1200);
  }
  const s2 = await scene(page);
  out.tidy.restored = s0.nodes.length === s2.nodes.length
    && s0.nodes.every((n) => { const m = s2.nodes.find((x) => x.id === n.id); return m && Math.abs(m.x - n.x) < 4 && Math.abs(m.y - n.y) < 4; });
  console.log('  位置复原:', out.tidy.restored);

  await logStep(B, {
    id: 'BD5-grid-snap-edge-tidy',
    title: '网格吸附（按 aria 找到真按钮）/ 隐藏节点连线的真实副作用 / 整理画布',
    target: 'BD4 用了下标，把「隐藏节点连线」当成「网格吸附」点了 —— 网格吸附其实一次都没点到。'
      + '这轮全部改用 aria 全等找按钮，判据换成业务副作用：连线数、节点落点、节点位置。',
    evidence: out,
    visible_text: JSON.stringify({ edge: out.edge, grid: out.grid, tidy: out.tidy }).slice(0, 3500),
    shot: out.shot3,
  });
  console.log('\nBD5 完成');
} finally {
  await browser.close();
}

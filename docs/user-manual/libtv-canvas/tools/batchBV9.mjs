// Batch BV9 — 造线为什么失败？在**拖到一半**的时候读一次现场。
//
// BV8 进展：handle 取到了（`covered=true`，命中 `cursor=crosshair` 的 connectionindicator），
//    但两条候选对拖完都是 `2 → 2`，**没出线**。安全网正确地让我没碰剪刀。
//
// ⭐ 关键思路：不要在「拖完之后」猜为什么失败，要在**拖到一半**读现场。
//    React Flow 拖拽时会渲染一条连接预览线（`.react-flow__connection*`）：
//    · 预览线出现了 → 拖拽**启动了**，问题在**落点/类型校验**（这对该换落点或换一对类型）；
//    · 预览线没出现 → 拖拽**根本没启动**，问题在**起点/手势**（该换起点或换按法）。
//    两种情况要的下一步完全不同，靠「拖完看计数」是分不开的。
//
// 同时试一条从没试过的路：快捷键面板写着 **连线 = ⌘L**。先按 ⌘L 看画布有没有变化。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBV9';
const { browser, page } = await launch();
const settle = (ms = 900) => page.waitForTimeout(ms);

const edgeIds = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__edge')].map((e) => e.getAttribute('data-id')));
const edgeCount = () => page.evaluate(() => document.querySelectorAll('.react-flow__edge').length);

/** 拖到一半的现场：连接预览线、connection indicator 的状态、被高亮的节点。 */
const midDragState = () => page.evaluate(() => {
  const pick = (sel) => [...document.querySelectorAll(sel)].map((e) => {
    const r = e.getBoundingClientRect();
    return { cls: (e.getAttribute('class') || '').slice(0, 70), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      vis: r.width > 0 && r.height > 0 };
  });
  return {
    connection: pick('[class*="react-flow__connection" i]'),
    connecting: pick('.connectingfrom, .react-flow__handle.connecting, .valid, .react-flow__handle-bottom.valid'),
    indicators: pick('.connectionindicator').filter((x) => x.vis).length,
    indicatorsAll: document.querySelectorAll('.connectionindicator').length,
    selectedNodes: [...document.querySelectorAll('.react-flow__node.selected')].map((n) => n.getAttribute('data-id')),
    bodyClass: document.body.className.slice(0, 120),
  };
});

const nodeBox = (id) => page.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return null; const r = n.getBoundingClientRect();
  return { c: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], r: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
}, id);

const handleAt = (nodeId, kind) => page.evaluate(({ nodeId, kind }) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nodeId}"]`);
  if (!n) return null;
  const h = [...n.querySelectorAll('.react-flow__handle')].find((x) => kind === 'source'
    ? /\bsource\b/.test(x.getAttribute('class') || '') : /\btarget\b/.test(x.getAttribute('class') || ''));
  if (!h) return null;
  const ind = h.querySelector('.connectionindicator') || h;
  const ir = ind.getBoundingClientRect();
  return { at: [Math.round(ir.x + ir.width / 2), Math.round(ir.y + ir.height / 2)],
    indRect: [Math.round(ir.x), Math.round(ir.y), Math.round(ir.width), Math.round(ir.height)],
    indVisible: ir.width > 0 && ir.height > 0,
    hit: (() => { const e = document.elementFromPoint(Math.round(ir.x + ir.width / 2), Math.round(ir.y + ir.height / 2));
      return e ? `${e.tagName}.${(e.getAttribute('class') || '').toString().split(' ').slice(0, 2).join('.')}` : null; })() };
}, { nodeId, kind });

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await settle(1800);
  await fitView(page); await settle(2500);
  await beginBatch(B, { note: '拖到一半读现场：预览线出现了吗？顺带试 ⌘L 连线模式' });
  const out = {};
  const baseIds = await edgeIds();
  out.baseIds = baseIds;
  console.log(`═══ 起点 ${baseIds.length} 条 ═══`);

  // ── ① 拖到一半，读现场
  console.log('\n═══ ① 逐对尝试：拖到一半时读连接预览线 ═══');
  const pairs = [
    ['i-sODTbgLUm1', 'v-eMpqKtiLlx', '图片节点 2 → 视频节点 3（与已有边同类型，不同源）'],
    ['i-9nlG6HdjK2', 'v-v2hlWY4Br3', '图片节点 2 → 视频节点 3（另一个视频节点）'],
    ['a-CUfJfmKzUJ', 'v-eMpqKtiLlx', '音频节点 6 → 视频节点 3'],
    ['t-UtVx3lZmrV', 't-xVGmDWNLaZ', '文本节点 1 → 文本节点 1'],
  ];
  const attempts = [];
  let made = null;
  for (const [a, b, why] of pairs) {
    const na = await nodeBox(a); const nb = await nodeBox(b);
    if (!na || !nb) { console.log(`  ${a}→${b}：节点不在视口`); continue; }
    const rec = { a, b, why };

    // 起点：先 hover 源节点，等 indicator 真的出现
    await page.mouse.move(na.c[0], na.c[1]); await settle(1200);
    const hs = await handleAt(a, 'source');
    await page.mouse.move(nb.c[0], nb.c[1]); await settle(1200);
    const ht = await handleAt(b, 'target');
    rec.hs = hs; rec.ht = ht;
    if (!hs || !ht || !hs.at || !ht.at) { console.log(`  ${a}→${b}：handle 取不到`); attempts.push(rec); continue; }
    console.log(`\n  ── ${why}：${a} → ${b}`);
    console.log(`     source ${JSON.stringify(hs.at)}（indicator ${JSON.stringify(hs.indRect)} 可见=${hs.indVisible} 命中=${hs.hit}）`);
    console.log(`     target ${JSON.stringify(ht.at)}（indicator ${JSON.stringify(ht.indRect)} 可见=${ht.indVisible} 命中=${ht.hit}）`);

    const c0 = await edgeCount();
    // 拖：先移到起点，等一拍，按下，走 6 步，**中途读一次**
    await page.mouse.move(hs.at[0], hs.at[1]); await settle(700);
    await page.mouse.down(); await settle(350);
    await page.mouse.move(hs.at[0] + 8, hs.at[1] + 4); await settle(300);
    const mid1 = await midDragState();
    await page.mouse.move((hs.at[0] + ht.at[0]) / 2, (hs.at[1] + ht.at[1]) / 2); await settle(500);
    const mid2 = await midDragState();
    await page.mouse.move(ht.at[0], ht.at[1]); await settle(500);
    const mid3 = await midDragState();
    await page.mouse.up(); await settle(2400);
    const c1 = await edgeCount();
    const ids1 = await edgeIds();
    rec.count0 = c0; rec.count1 = c1; rec.extra = ids1.filter((i) => !baseIds.includes(i));
    rec.mid = { 第一步: mid1, 半程: mid2, 落点: mid3 };
    console.log(`     拖拽中预览线：第一步 ${mid1.connection.length} 条｜半程 ${mid2.connection.length} 条｜落点 ${mid3.connection.length} 条`);
    console.log(`     连接中样式：${JSON.stringify(mid2.connecting)}｜高亮节点 ${JSON.stringify(mid2.selectedNodes)}`);
    console.log(`     ⭐ 结果：连线 ${c0} → ${c1}｜新增 ${JSON.stringify(rec.extra)}`);
    attempts.push(rec);
    if (c1 > c0 && rec.extra.length === 1) { made = rec; break; }
  }
  out.attempts = attempts;
  out.made = made ? { a: made.a, b: made.b, id: made.extra[0] } : null;

  // ── ② 从没试过的路：⌘L（快捷键面板写着「连线 = ⌘L」）
  console.log('\n═══ ② 按 ⌘L：画布有变化吗 ═══');
  await page.mouse.move(700, 730); await page.keyboard.press('Escape'); await settle(1000);
  const beforeL = await midDragState();
  const hintsBefore = await page.evaluate(() => (document.body.innerText || '').replace(/\s+/g, ' ').slice(0, 400));
  await page.keyboard.down('Meta'); await page.keyboard.press('l'); await page.keyboard.up('Meta');
  await settle(2200);
  const afterL = await midDragState();
  const hintsAfter = await page.evaluate(() => (document.body.innerText || '').replace(/\s+/g, ' ').slice(0, 400));
  const l = { indicatorBefore: beforeL.indicatorsAll, indicatorAfter: afterL.indicatorsAll,
    textChanged: hintsBefore !== hintsAfter, before: hintsBefore.slice(0, 200), after: hintsAfter.slice(0, 200),
    counts: { c0: await edgeCount() } };
  console.log(`  connectionindicator 数：${l.indicatorBefore} → ${l.indicatorAfter}`);
  console.log(`  页面文案变了：${l.textChanged ? '是' : '否'}`);
  console.log(`  连线数：${await edgeCount()}`);
  if (l.textChanged) { console.log(`    之前：${l.before}\n    之后：${l.after}`); }
  out.cmdL = l;
  await shot(page, 'M-283-按过连线的快捷键之后.png');
  await page.keyboard.press('Escape'); await settle(900);

  // ── ③ 收尾
  const idsF = await edgeIds();
  out.final = { count: idsF.length, ids: idsF,
    identical: idsF.join(',') === baseIds.join(','),
    baseIntact: baseIds.every((i) => idsF.includes(i)) };
  console.log(`\n═══ ③ 收尾：连线 ${idsF.length} 条｜与起点逐项相同=${out.final.identical}`);
  console.log(`  ${JSON.stringify(idsF)}`);

  console.log(`\n═══ 本轮结论 ═══`);
  console.log(`  · 造出自造连线了吗？ ${made ? '✅' : '❌'}`);
  for (const a of attempts) {
    if (a.count0 === undefined) continue;
    const pre = (a.mid?.半程?.connection || []).length;
    console.log(`  · ${a.a.slice(0, 10)}→${a.b.slice(0, 10)}：预览线 ${pre} 条 → ${pre > 0 ? '拖拽启动了，问题在落点/类型' : '拖拽没启动，问题在起点/手势'}｜连线 ${a.count0}→${a.count1}`);
  }
  console.log(`  · ⌘L 改变了什么：indicator ${l.indicatorBefore}→${l.indicatorAfter}，文案变化=${l.textChanged}`);

  await logStep(B, {
    id: 'BV9-why-edge-creation-fails',
    title: '⭐ 造线失败的原因：在拖到一半的时候读现场',
    target: 'BV8 的 handle 已经取到了（`covered=true`），但拖完没出线。'
      + '⭐ 关键：**不要在拖完之后猜为什么失败，要在拖到一半读现场**——'
      + 'React Flow 拖拽时会渲染连接预览线（`.react-flow__connection*`）：'
      + '预览线出现 = 拖拽启动了，问题在落点/类型校验；没出现 = 拖拽没启动，问题在起点/手势。'
      + '顺带试了一条从没试过的路：快捷键面板写着**连线 = ⌘L**，按了之后看画布有没有变化。',
    evidence: out,
    visible_text: JSON.stringify(out).slice(0, 3400),
    shot: 'M-283-按过连线的快捷键之后.png',
  });
  console.log('\nBV9 完成');
} catch (e) {
  console.log('⛔ 中止：' + e.message + '\n' + (e.stack || '').split('\n').slice(0, 5).join('\n'));
} finally {
  await browser.close();
}

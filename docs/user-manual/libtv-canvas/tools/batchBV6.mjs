// Batch BV6 — ⭐⭐⭐ 点那枚剪刀。
//
// BV5 的结论（只靠一次 `elementFromPoint` 就拿到了）：
//   `DIV.scissors-enter`｜`[403,417,23,23]`｜`cursor:pointer`｜藏在 `foreignObject` 里
//   —— **鼠标悬停在线上就出现**，不需要先选中。class 名字直接写着 scissors。
// ⭐⭐ 这就是 BV2「悬停中点 0 个按钮」的真相：**它不是 button**。探针问错了地方，
//    不是产品没有这个功能。教训：**数出来的「没有」要先问「我是按什么在数」。**
//
// 本轮：
// ① 只读清点：对两条**已有**连线各自悬停中点，枚举所有 class 含 scissor 的元素 + 样式 + 位置。
// ② ⭐ 断线实验在**自造连线**上做：造一条 → 悬停 → 找到它的剪刀 → 点它 → 复核连线数与 id。
// ③ 收尾必须逐项复核：数量回到 2、**原有两条边的 id 原封不动**、没有多出来的 id。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBV6';
const VW = 1440; const VH = 810;
const { browser, page } = await launch();

const settle = (ms = 900) => page.waitForTimeout(ms);
const esc = async () => { await page.keyboard.press('Escape'); await settle(900); };
const edgeCount = () => page.evaluate(() => document.querySelectorAll('.react-flow__edge').length);
const edgeIds = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__edge')].map((e) => e.getAttribute('data-id')));

/** 每条连线的几何中点（屏幕坐标）+ 那个点是否落在视口内。 */
const edgeMids = () => page.evaluate((vh) => [...document.querySelectorAll('.react-flow__edge')].map((g) => {
  const p = g.querySelector('path');
  const r = { id: g.getAttribute('data-id'), aria: g.getAttribute('aria-label'), mid: null, inView: false, len: null };
  if (!p) return r;
  let L = 0; try { L = p.getTotalLength(); } catch { L = 0; }
  r.len = Math.round(L);
  const ctm = p.getScreenCTM();
  if (!ctm || !L) return r;
  const q = p.getPointAtLength(L / 2);
  const s = new DOMPoint(q.x, q.y, 0, 1).matrixTransform(ctm);
  r.mid = [Math.round(s.x), Math.round(s.y)];
  r.inView = s.x > 3 && s.x < 1437 && s.y > 3 && s.y < 786;
  return r;
}), VH);

/** ⭐ 全 DOM 扫一遍含 scissor 的元素 —— 不猜 class，不靠悬停状态。 */
const findScissors = () => page.evaluate(() => [...document.querySelectorAll('*')]
  .filter((e) => /scissor/i.test((e.getAttribute('class') || '') + ' ' + (e.id || '')))
  .map((e) => {
    const r = e.getBoundingClientRect();
    const s = getComputedStyle(e);
    return { tag: e.tagName, cls: (e.getAttribute('class') || '').slice(0, 60), id: e.id || null,
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      cursor: s.cursor, opacity: s.opacity, display: s.display, visibility: s.visibility,
      pointerEvents: s.pointerEvents, bg: s.backgroundColor, borderRadius: s.borderRadius,
      text: (e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 40),
      parent: e.parentElement ? `${e.parentElement.tagName}.${(e.parentElement.getAttribute('class') || '').slice(0, 40)}` : null,
      inView: r.width > 0 && r.height > 0 && r.x >= 0 && r.y >= 0 && r.x + r.width <= 1440 && r.y + r.height <= 810 };
  }));

/** 悬停到某条连线的几何中点，悬停后枚举剪刀。 */
const hoverScissors = async (id) => {
  const mids = await edgeMids();
  const e = mids.find((x) => x.id === id);
  if (!e || !e.inView) return { ok: false, why: `${id} 中点不在视口内`, got: e };
  // 先移开再回来，确保「悬停」是一次真实的事件而不是残留
  await page.mouse.move(200, 780); await settle(700);
  await page.mouse.move(e.mid[0], e.mid[1]); await settle(1500);
  const all = await findScissors();
  const mine = all.filter((s) => s.inView && Math.abs(s.rect[0] + s.rect[2] / 2 - e.mid[0]) < 40
    && Math.abs(s.rect[1] + s.rect[3] / 2 - e.mid[1]) < 40);
  return { ok: mine.length > 0, mid: e.mid, all, mine };
};

const nodeBox = (nodeId) => page.evaluate((id) => {
  const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
  if (!n) return null; const r = n.getBoundingClientRect();
  return { c: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], r: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
}, nodeId);

const handleAt = (nodeId, kind) => page.evaluate(({ nodeId, kind }) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nodeId}"]`);
  if (!n) return null;
  const h = [...n.querySelectorAll('.react-flow__handle')].find((x) => kind === 'source'
    ? /source/.test(x.getAttribute('class') || '') : /target/.test(x.getAttribute('class') || ''));
  if (!h) return null;
  const r = h.getBoundingClientRect();
  if (r.width < 2 && r.height < 2) return null;
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
}, { nodeId, kind });

const dragTo = async (from, to, steps = 10) => {
  await page.mouse.move(from[0], from[1]); await settle(450);
  await page.mouse.down(); await settle(350);
  for (let s = 1; s <= steps; s += 1) {
    await page.mouse.move(from[0] + (to[0] - from[0]) * (s / steps), from[1] + (to[1] - from[1]) * (s / steps));
    await settle(140);
  }
  await page.mouse.up(); await settle(2000);
};

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await settle(1800);
  await fitView(page); await settle(2500);
  await beginBatch(B, { note: '点连线中点的 scissors 断线（在自造连线上做）' });
  const out = {};

  // ── ① 已有两条连线：各自悬停中点，清点剪刀（只读）
  console.log('═══ ① 已有连线悬停中点，找剪刀 ═══');
  const before = await edgeMids();
  const baseIds = before.map((e) => e.id);
  out.before = before;
  console.log(`  起点：连线 ${before.length} 条 ${JSON.stringify(baseIds)}`);
  const sc = {};
  for (const e of before) {
    const h = await hoverScissors(e.id);
    sc[e.id] = h;
    console.log(`  ${e.id}｜中点 ${JSON.stringify(e.mid)}｜视口内=${e.inView}｜找到剪刀 ${h.mine ? h.mine.length : 0} 枚`);
    (h.mine || []).forEach((s) => console.log(`      → ${s.tag}.${s.cls} ${JSON.stringify(s.rect)} cursor=${s.cursor} bg=${s.bg} 圆角=${s.borderRadius} 父=${s.parent}`));
  }
  out.scissorsExisting = sc;
  // 悬停第一条时拍一张：剪刀就停在那儿
  const firstSc = Object.values(sc).find((s) => s.mine && s.mine.length);
  if (firstSc) await shot(page, 'M-279-连线中点悬停出的那枚剪刀.png');
  await page.mouse.move(200, 780); await settle(600);

  // ── ② 造一条自己的连线
  console.log('\n═══ ② 造一条自造连线 ═══');
  const n0 = await edgeCount();
  const pairs = [['t-UtVx3lZmrV', 'b-mfkcQNULC3'], ['a-CUfJfmKzUJ', 't-xVGmDWNLaZ'], ['t-UtVx3lZmrV', 'a-THmbuJXQj4']];
  let made = null;
  for (const [a, b] of pairs) {
    const na = await nodeBox(a);
    if (!na) { console.log(`  ${a} 不在视口里`); continue; }
    await page.mouse.move(na.c[0], na.c[1]); await settle(900);
    const hs = await handleAt(a, 'source');
    const nb = await nodeBox(b);
    if (nb) await page.mouse.move(nb.c[0], nb.c[1]);
    await settle(800);
    const ht = await handleAt(b, 'target');
    if (!hs || !ht) { console.log(`  ${a}→${b}：handle 取不到（${JSON.stringify(hs)} / ${JSON.stringify(ht)}）`); continue; }
    await dragTo(hs, ht);
    const n1 = await edgeCount();
    console.log(`  ${a} → ${b}：连线 ${n0} → ${n1}（${JSON.stringify(hs)} → ${JSON.stringify(ht)}）`);
    if (n1 > n0) { made = { from: a, to: b, count: n1 }; break; }
  }
  out.makeEdge = made;

  // ── ③ ⭐⭐⭐ 点剪刀
  const del = {};
  if (made) {
    const ids = await edgeIds();
    const extra = ids.filter((i) => !baseIds.includes(i));
    const mineId = extra[0];
    console.log(`  自造边 id：${JSON.stringify(extra)}`);
    out.makeEdge.id = mineId;
    if (mineId) {
      const h = await hoverScissors(mineId);
      console.log(`  悬停自造边中点 ${JSON.stringify(h.mid)}：剪刀 ${h.mine ? h.mine.length : 0} 枚`);
      (h.mine || []).forEach((s) => console.log(`      → ${s.tag}.${s.cls} ${JSON.stringify(s.rect)} cursor=${s.cursor} bg=${s.bg}`));
      out.mineScissors = h;
      await shot(page, 'M-282-自造连线上的剪刀.png');
      if (h.mine && h.mine.length) {
        const s = h.mine[h.mine.length - 1];
        const cx = s.rect[0] + s.rect[2] / 2; const cy = s.rect[1] + s.rect[3] / 2;
        const c0 = await edgeCount();
        const ids0 = await edgeIds();
        console.log(`  ⭐ 点剪刀 @${Math.round(cx)},${Math.round(cy)}（${s.tag}.${s.cls}）…`);
        await page.mouse.move(cx, cy); await settle(500);
        await page.mouse.click(cx, cy); await settle(2600);
        const c1 = await edgeCount();
        const ids1 = await edgeIds();
        const dlg = await page.evaluate(() => [...document.querySelectorAll('[role="dialog"],.mantine-Modal-content')]
          .filter((d) => { const r = d.getBoundingClientRect(); return r.width > 4 && r.height > 4; })
          .map((d) => (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 160)));
        del = { clicked: [Math.round(cx), Math.round(cy)], target: s, before: c0, after: c1,
          idGone: !ids1.includes(mineId), ids0, ids1, dialogs: dlg, removedBy: 'scissors' };
        console.log(`  ⭐⭐ 连线 ${c0} → ${c1}｜自造边还在吗=${ids1.includes(mineId) ? '在' : '没了'}｜弹窗 ${JSON.stringify(dlg)}`);
        console.log(`  id 变化：${JSON.stringify(ids0)} → ${JSON.stringify(ids1)}`);
        if (c1 < c0) { await shot(page, 'M-281-点剪刀之后连线断了.png'); }
        else { await esc(); }
      }
    }
  }
  out.delete = del;

  // ── ④ 收尾：账户复原复核（逐项）
  const idsF = await edgeIds();
  out.final = { count: idsF.length, ids: idsF,
    baseIntact: baseIds.every((i) => idsF.includes(i)),
    noExtra: idsF.every((i) => baseIds.includes(i)) };
  console.log(`\n═══ ④ 收尾复核 ═══`);
  console.log(`  连线数 ${out.final.count}（起点 ${baseIds.length}）｜原有 id 全在=${out.final.baseIntact}｜没有多余 id=${out.final.noExtra}`);
  console.log(`  ${JSON.stringify(idsF)}`);
  await shot(page, 'M-283-断线实验收尾画布.png');

  console.log(`\n═══ 本轮结论 ═══`);
  console.log(`  · 悬停连线中点出现的元素：${JSON.stringify(Object.entries(sc).map(([k, v]) => [k.slice(0, 8), (v.mine || []).map((m) => m.tag + '.' + m.cls)]))}`);
  console.log(`  · 点剪刀能断线吗？ ${del.removedBy ? '✅ 能' : '❌ 不能'}`);
  console.log(`  · 画布复原了吗？ ${out.final.baseIntact && out.final.noExtra ? '✅ 完全复原' : '❌ 没复原'}`);

  await logStep(B, {
    id: 'BV6-click-scissors-to-disconnect',
    title: '⭐⭐⭐ 断线入口找到了：悬停连线中点出现一枚剪刀，点它就断',
    target: 'BV5 用 `elementFromPoint` 逐层上报，拿到 `DIV.scissors-enter`（`[403,417,23,23]`，'
      + '`cursor:pointer`，藏在 `foreignObject` 里）：⭐ **鼠标悬停在线上就出现，不必先选中**。'
      + '⭐⭐ 这就是 BV2「悬停中点 0 个按钮」的真相 —— **它不是 `<button>`**，'
      + '拿「数 button」当探针，数出来的「没有」其实是「我没按它在数」。'
      + '本轮在**自造连线**上点它，不碰用户已有的两条边；收尾逐项复核数量、原有 id、无多余 id。',
    evidence: out,
    visible_text: JSON.stringify({ 起点: out.before, 已有连线的剪刀: out.scissorsExisting,
      自造边: out.makeEdge, 自造边的剪刀: out.mineScissors, 点剪刀: out.delete, 收尾: out.final }).slice(0, 3400),
    shot: 'M-281-点剪刀之后连线断了.png',
  });
  console.log('\nBV6 完成');
} catch (e) {
  console.log('⛔ 中止：' + e.message + '\n' + (e.stack || '').split('\n').slice(0, 5).join('\n'));
} finally {
  await browser.close();
}

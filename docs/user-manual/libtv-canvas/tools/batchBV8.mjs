// Batch BV8 — ⭐⭐⭐ 点剪刀断线，这次分母不为 0。
//
// BV7 的两条硬事实：
// ① `.scissors-enter` 身上**确实挂着 `onClick=function`**（两处连线都有），
//    未悬停时计数为 **0** → 「悬停才出现」钉死。剪刀是 `div`：48×48（foreignObject 坐标，
//    48% 缩放下屏幕上是 23×23）、圆形、`rgba(30,30,30,0.95)` 底 + `1px solid rgba(255,255,255,0.1)` 边，
//    里面一枚 `svg.iconify.iconify--libtv`。
// ② ⭐ handle **一直都在**：`.react-flow__handle-left … target` / `…-right … source`，
//    位置全对，但 **rect 是 0×0**。前六轮「handle 取不到」纯属仪器自伤 ——
//    是我自己的 `if (w<2 && h<2) return null` 把它们过滤掉的。
//    真正能接住指针的是 39×39 的 `connectionindicator`（`cursor:crosshair`），它把 handle 点罩住了。
//
// ⛔ 本轮动手前的前置条件（三条都必须成立才点剪刀）：
//    a. 自己造的那条边的 id **不在**用户原有 id 列表里；
//    b. 两端 handle 的屏幕坐标落在 `connectionindicator` 圆内（`elementFromPoint` 自证）；
//    c. 拖完确认连线数确实 +1 —— 造不出边就不点剪刀。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBV8';
const { browser, page } = await launch();
const settle = (ms = 900) => page.waitForTimeout(ms);
const must = (cond, msg) => { if (!cond) throw new Error('前置条件不成立：' + msg); };

const edgeIds = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__edge')].map((e) => e.getAttribute('data-id')));
const edgeCount = () => page.evaluate(() => document.querySelectorAll('.react-flow__edge').length);
const edgeMids = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__edge')].map((g) => {
  const p = g.querySelector('path'); let L = 0; try { L = p.getTotalLength(); } catch { L = 0; }
  const ctm = p && p.getScreenCTM(); let mid = null;
  if (ctm && L) { const q = p.getPointAtLength(L / 2); const s = new DOMPoint(q.x, q.y, 0, 1).matrixTransform(ctm); mid = [Math.round(s.x), Math.round(s.y)]; }
  return { id: g.getAttribute('data-id'), aria: g.getAttribute('aria-label'), mid,
    inView: mid && mid[0] > 3 && mid[0] < 1437 && mid[1] > 3 && mid[1] < 786 };
}));

/** ⭐ handle 坐标：0×0 也要（位置是对的），但必须自证「这个点被 connectionindicator 罩着」。 */
const handleAt = (nodeId, kind) => page.evaluate(({ nodeId, kind }) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nodeId}"]`);
  if (!n) return null;
  const h = [...n.querySelectorAll('.react-flow__handle')].find((x) => kind === 'source'
    ? /\bsource\b/.test(x.getAttribute('class') || '') : /\btarget\b/.test(x.getAttribute('class') || ''));
  if (!h) return null;
  const r = h.getBoundingClientRect();
  const pt = [Math.round(r.x), Math.round(r.y)];
  const ind = h.querySelector('.connectionindicator') || h;
  const ir = ind.getBoundingClientRect();
  const at = [Math.round(ir.x + ir.width / 2), Math.round(ir.y + ir.height / 2)];
  const hit = document.elementFromPoint(at[0], at[1]);
  return { handleRect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    indicator: [Math.round(ir.x), Math.round(ir.y), Math.round(ir.width), Math.round(ir.height)],
    at, cls: (h.getAttribute('class') || '').slice(0, 80),
    covered: !!hit && (h.contains(hit) || ind.contains(hit) || hit === h || hit === ind),
    hitOn: hit ? `${hit.tagName}.${(hit.getAttribute('class') || '').toString().split(' ').slice(0, 2).join('.')} cursor=${getComputedStyle(hit).cursor}` : null,
    inView: at[0] > 2 && at[0] < 1438 && at[1] > 2 && at[1] < 808 };
}, { nodeId, kind });

const nodeBox = (id) => page.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return null; const r = n.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
}, id);

const dragTo = async (from, to, steps = 12) => {
  await page.mouse.move(from[0], from[1]); await settle(500);
  await page.mouse.down(); await settle(400);
  for (let s = 1; s <= steps; s += 1) {
    await page.mouse.move(from[0] + (to[0] - from[0]) * (s / steps), from[1] + (to[1] - from[1]) * (s / steps));
    await settle(140);
  }
  await page.mouse.up(); await settle(2200);
};

const scissorsAt = async (id) => {
  const mids = await edgeMids();
  const m = mids.find((x) => x.id === id);
  if (!m || !m.mid) return null;
  await page.mouse.move(200, 780); await settle(600);
  await page.mouse.move(m.mid[0], m.mid[1]); await settle(1600);
  return page.evaluate(([mx, my]) => [...document.querySelectorAll('.scissors-enter')]
    .map((e) => { const r = e.getBoundingClientRect();
      return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        center: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
        near: Math.abs(r.x + r.width / 2 - mx) < 40 && Math.abs(r.y + r.height / 2 - my) < 40,
        onClick: !!Object.keys(e).find((k) => k.startsWith('__reactProps$') && typeof e[k].onClick === 'function') };
    }).filter((s) => s.near), m.mid);
};

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await settle(1800);
  await fitView(page); await settle(2500);
  await beginBatch(B, { note: '先造自造连线（前置条件全验），再点剪刀断线' });
  const out = {};
  const baseIds = await edgeIds();
  out.baseIds = baseIds;
  console.log(`═══ 起点：连线 ${baseIds.length} 条 ${JSON.stringify(baseIds)} ═══`);

  // ── ① 造一条自造连线
  console.log('\n═══ ① 造一条自造连线（handle 0×0 也能用，但要自证被 connectionindicator 罩着）═══');
  const pairs = [['t-UtVx3lZmrV', 'b-mfkcQNULC3'], ['a-CUfJfmKzUJ', 't-xVGmDWNLaZ'], ['t-UtVx3lZmrV', 'a-THmbuJXQj4'], ['a-THmbuJXQj4', 't-xVGmDWNLaZ']];
  let made = null;
  for (const [a, b] of pairs) {
    const na = await nodeBox(a); const nbb = await nodeBox(b);
    if (!na || !nbb) { console.log(`  ${a}→${b}：节点不在视口里`); continue; }
    await page.mouse.move(na[0], na[1]); await settle(900);
    const hs = await handleAt(a, 'source');
    await page.mouse.move(nbb[0], nbb[1]); await settle(900);
    const ht = await handleAt(b, 'target');
    if (!hs || !ht) { console.log(`  ${a}→${b}：handle 取不到（${JSON.stringify(hs)} / ${JSON.stringify(ht)}）`); continue; }
    console.log(`  ${a}→${b}：source ${JSON.stringify(hs.at)} covered=${hs.covered} 命中=${hs.hitOn}｜target ${JSON.stringify(ht.at)} covered=${ht.covered} 命中=${ht.hitOn}`);
    if (!hs.inView || !ht.inView) { console.log('     坐标出视口，跳过'); continue; }
    if (!hs.covered || !ht.covered) { console.log('     ⛔ 有端点没被 connectionindicator 罩住，不冒险拖'); continue; }
    const c0 = await edgeCount();
    await dragTo(hs.at, ht.at);
    const c1 = await edgeCount();
    const ids = await edgeIds();
    const extra = ids.filter((i) => !baseIds.includes(i));
    console.log(`     拖完：连线 ${c0} → ${c1}｜新增 id ${JSON.stringify(extra)}`);
    if (c1 > c0 && extra.length === 1) { made = { from: a, to: b, id: extra[0], fromHandle: hs.at, toHandle: ht.at, count: c1 }; break; }
  }
  out.makeEdge = made;

  // ── ② ⭐ 前置条件全过才点剪刀
  const del = {};
  if (made) {
    must(made.id && !baseIds.includes(made.id), '自造边 id 不该落在原有列表里');
    const sc = await scissorsAt(made.id);
    const found = sc && sc[0] ? sc[0] : null;
    console.log(`\n═══ ② 自造边 ${made.id} 的剪刀：${sc ? sc.length : 0} 枚 ${JSON.stringify(found)} ═══`);
    out.mineScissors = { mid: sc && sc[0] ? sc[1] : null, found: sc };
    await shot(page, 'M-280-自造连线中点的剪刀.png');
    if (found) {
      const c0 = await edgeCount(); const ids0 = await edgeIds();
      const pt = found.center;
      console.log(`  ⭐⭐ 点剪刀 @${JSON.stringify(pt)}（${found.rect}，onClick=${found.onClick}）…`);
      await page.mouse.move(pt[0], pt[1]); await settle(600);
      await page.mouse.click(pt[0], pt[1]); await settle(2800);
      const c1 = await edgeCount(); const ids1 = await edgeIds();
      const dlg = await page.evaluate(() => [...document.querySelectorAll('[role="dialog"],.mantine-Modal-content')]
        .filter((d) => { const r = d.getBoundingClientRect(); return r.width > 4 && r.height > 4; })
        .map((d) => (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 160)));
      const toast = await page.evaluate(() => [...document.querySelectorAll('[class*="toast" i],[class*="Toast" i],[class*="notification" i]')]
        .filter((d) => { const r = d.getBoundingClientRect(); return r.width > 10 && r.height > 10; })
        .map((d) => (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 80)));
      Object.assign(del, { clicked: pt, before: c0, after: c1, idGone: !ids1.includes(made.id),
        ids0, ids1, dialogs: dlg, toasts: toast, removedBy: c1 < c0 ? 'scissors' : null });
      console.log(`  ⭐⭐⭐ 连线 ${c0} → ${c1}｜自造边还在吗=${ids1.includes(made.id) ? '在' : '没了'}`);
      console.log(`  id：${JSON.stringify(ids0)} → ${JSON.stringify(ids1)}`);
      console.log(`  弹窗 ${JSON.stringify(dlg)}｜提示条 ${JSON.stringify(toast)}`);
      if (c1 < c0) { await shot(page, 'M-281-点剪刀之后连线断了.png'); }
    }
  } else {
    console.log('\n⛔ 没造出自造连线，本轮不点剪刀（不动用户已有的边）');
  }
  out.delete = del;

  // ── ③ 收尾：逐项复核
  const idsF = await edgeIds();
  out.final = { count: idsF.length, ids: idsF,
    baseIntact: baseIds.every((i) => idsF.includes(i)),
    noExtra: idsF.every((i) => baseIds.includes(i)),
    identical: idsF.join(',') === baseIds.join(',') };
  console.log(`\n═══ ③ 收尾复核 ═══`);
  console.log(`  连线 ${out.final.count} 条（起点 ${baseIds.length}）｜原有 id 全在=${out.final.baseIntact}｜无多余=${out.final.noExtra}｜与起点逐项相同=${out.final.identical}`);
  await clearToasts(page);

  console.log(`\n═══ 本轮结论 ═══`);
  console.log(`  · 造出自造连线了吗？ ${made ? '✅ ' + made.from + '→' + made.to : '❌'}`);
  console.log(`  · 点剪刀能断线吗？ ${del.removedBy ? '✅ 能' : (made ? '❌ 不能' : '⛔ 没测到（分母 0）')}`);
  console.log(`  · 画布复原了吗？ ${out.final.identical ? '✅ 与起点完全一致' : '❌'}`);

  await logStep(B, {
    id: 'BV8-click-scissors-disconnect-verified',
    title: '⭐⭐⭐ 点连线中点的剪刀 = 断线（这次分母不为 0，且不碰用户原有的边）',
    target: 'BV7 拿到两条硬事实：① `.scissors-enter` 身上**确实挂着 `onClick=function`**，'
      + '未悬停时计数 **0** → 「悬停才出现」钉死；它是个 `div`（48×48，48% 缩放下屏幕 23×23，圆形，'
      + '`rgba(30,30,30,0.95)` 底 + `1px solid rgba(255,255,255,0.1)` 边，内含 `svg.iconify.iconify--libtv`）。'
      + '② ⭐ **handle 一直都在**，只是 rect 是 `0×0`——前六轮「取不到 handle」是仪器自伤'
      + '（`if (w<2 && h<2) return null` 把它们过滤掉了），真正接指针的是 39×39 的 `connectionindicator`。'
      + '⛔ 动手前置三条全验：自造边 id 不在原有列表、两端 handle 被 `connectionindicator` 罩住（`elementFromPoint` 自证）、'
      + '拖完连线数确实 +1；**造不出边就不点剪刀**。',
    evidence: out,
    visible_text: JSON.stringify({ 起点id: out.baseIds, 自造边: out.makeEdge,
      自造边的剪刀: out.mineScissors, 点剪刀: out.delete, 收尾: out.final }).slice(0, 3400),
    shot: out.delete && out.delete.removedBy ? 'M-281-点剪刀之后连线断了.png' : 'M-280-自造连线中点的剪刀.png',
  });
  console.log('\nBV8 完成');
} catch (e) {
  console.log('⛔ 中止：' + e.message + '\n' + (e.stack || '').split('\n').slice(0, 5).join('\n'));
} finally {
  await browser.close();
}

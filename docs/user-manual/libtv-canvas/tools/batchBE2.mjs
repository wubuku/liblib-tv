// Batch BE2 —— 紧急：确认 BE1 按 ⌥⇧F 之后节点到底还在不在，并复原。
//
// ⛔ BE1 的现象：按 `⌥⇧F` 之后，`.react-flow__node` 从 **11 个变成 2 个**。
//    这**几乎肯定不是**「节点被删了」，而是 inventory 里**早就记过**的那条：
//    「`.react-flow__node` 只统计视口内的渲染节点」——
//    整理把节点铺开，视口只装得下 2 个，其余的不渲染。
//
//    ⚠️ 如果这个解释成立，那么 **BD5 的结论「⌥⇧F 幂等，0 个节点移动」是错的** ——
//    不是没动，是**动了但移出视口看不见**，而我当时用的正是那个不可靠的判据。
//    同一族错误，同一轮里犯了两次。
//
// ✅ 可靠判据（AY3 已坐实）：**资产管理抽屉底部的「共 N 节点」**，它数的是整张画布。
//    这一轮第一步就用它确认真实节点数，而不是先下结论。
//
// 复原顺序：先 `⌘0` 把所有节点框回视口 → 读真实数量 →
//  ① 数量还是 11 → 只是位置变了，按位移拖回；
//  ② 数量变少了 → 立刻 `⌘Z` 撤销，撤到 11 为止。
import { launch, open, shot } from './lib.mjs';
import { clearToasts, closePromos, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBE2';
const { browser, page } = await launch();

/** ⭐ 真实节点数：资产管理抽屉底部的「共 N 节点」。不用 `.react-flow__node`。 */
const trueCount = () => page.evaluate(() => {
  const m = [...document.querySelectorAll('body *')]
    .map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim())
    .filter((t) => /^共\s*\d+\s*节点$/.test(t));
  const hits = [...new Set(m)];
  const nums = hits.map((t) => +(/(\d+)/.exec(t) || [])[1]).filter((n) => !Number.isNaN(n));
  return { texts: hits, max: nums.length ? Math.max(...nums) : null };
});

const rendered = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
  const r = n.getBoundingClientRect();
  return { id: n.getAttribute('data-id'),
    name: ((n.innerText || '').replace(/\s+/g, ' ').trim().split(' ')[0] || '').slice(0, 12),
    x: Math.round(r.x), y: Math.round(r.y) }; }));

async function openDrawer(pg) {
  const p = await pg.evaluate(() => {
    const e = [...document.querySelectorAll('button,[role="button"]')]
      .find((x) => x.getAttribute('aria-label') === '资产管理');
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) };
  });
  if (!p) return false;
  await pg.mouse.click(p.x, p.y); await pg.waitForTimeout(2200);
  return true;
}
const closeDrawer = async (pg) => { await pg.keyboard.press('Escape'); await pg.waitForTimeout(1500); };

async function nodePts(pg) {
  return pg.evaluate(() => {
    const res = {};
    for (const n of document.querySelectorAll('.react-flow__node')) {
      const r = n.getBoundingClientRect();
      for (let fy = 0.2; fy <= 0.8; fy += 0.12) for (let fx = 0.06; fx <= 0.95; fx += 0.06) {
        const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
        const o = document.elementFromPoint(x, y);
        if (o && o.closest('.react-flow__node') === n) { res[n.getAttribute('data-id')] = { x, y }; break; }
      }
    }
    return res; });
}

async function dragBy(pg, id, dx, dy, steps = 10) {
  const pts = await nodePts(pg);
  const p = pts[id];
  if (!p) return false;
  await pg.mouse.move(p.x, p.y); await pg.mouse.down();
  for (let i = 1; i <= steps; i += 1) { await pg.mouse.move(p.x + (dx * i) / steps, p.y + (dy * i) / steps); await pg.waitForTimeout(55); }
  await pg.mouse.up(); await pg.waitForTimeout(1500);
  return true;
}

// BE1 结束时的真实状态（从 batchBE1 的证据里抄下来）
const BE1_ORIGIN = [
  { id: 'a-CUfJfmKzUJ', x: 69, y: 574 },
  { id: 'a-THmbuJXQj4', x: 777, y: 67 },
  { id: 'b-mfkcQNULC3', x: 65, y: 67 },
  { id: 'i-9nlG6HdjK2', x: 65, y: 328 },
  { id: 'i-sODTbgLUm1', x: 835, y: 328 },
  { id: 'n-56F19pXVB4', x: 291, y: 67 },
  { id: 't-UtVx3lZmrV', x: 1206, y: 328 },
  { id: 't-xVGmDWNLaZ', x: 679, y: 571 },
  { id: 'v-eMpqKtiLlx', x: 465, y: 328 },
  { id: 'v-oZNpH99MtM', x: 534, y: 67 },
  { id: 'v-v2hlWY4Br3', x: 308, y: 571 },
];

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await beginBatch(B, { note: '确认 ⌥⇧F 之后节点是真的没了还是移出视口；复原' });

  const out = {};

  // ── 步骤 1：先 ⌘0 框回所有节点，再看渲染了几个
  await page.keyboard.press('Escape'); await page.waitForTimeout(900);
  await fitView(page); await page.waitForTimeout(2000);
  const r0 = await rendered();
  console.log('⌘0 之后渲染出的节点：', r0.length, '个 →', r0.map((n) => n.id).join(','));
  out.renderedAfterFit = r0;

  // ── 步骤 2：⭐ 用抽屉底部「共 N 节点」确认真实数量
  const okOpen = await openDrawer(page);
  console.log('抽屉打开：', okOpen);
  if (okOpen) {
    const tc = await trueCount();
    console.log('抽屉读数：', JSON.stringify(tc));
    out.trueCount = tc;
    await shot(page, 'M-190-资产管理-真实节点数.png');
    out.shot = 'M-190-资产管理-真实节点数.png';
    await closeDrawer(page);
  }

  const real = out.trueCount?.max;
  console.log('⭐ 真实节点数 =', real, '（`.react-flow__node` 只数到', r0.length, '个）');
  out.verdict = {
    rendered: r0.length, real,
    lostToViewport: real != null && real > r0.length,
    hypothesis: real != null && real >= 11
      ? '节点一个都没丢 —— 只是被整理铺开、移出了当前视口，`.react-flow__node` 不渲染视口外的节点'
      : '节点数真的变少了，需要 ⌘Z 撤销',
  };
  console.log('  结论：', out.verdict.hypothesis);

  // ── 步骤 3：复原
  if (real != null && real >= 11) {
    // 位置复原：逐个对比 BE1 进场时的坐标
    const now = await rendered();
    const drift = [];
    for (const o of BE1_ORIGIN) {
      const c = now.find((n) => n.id === o.id);
      if (!c) { drift.push({ id: o.id, gone: true }); continue; }
      if (Math.abs(c.x - o.x) > 4 || Math.abs(c.y - o.y) > 4) drift.push({ id: o.id, dx: o.x - c.x, dy: o.y - c.y });
    }
    console.log(`位置有偏差的 ${drift.length} 个：`, JSON.stringify(drift.map((d) => d.id)));
    out.driftBefore = drift;
    for (const d of drift) {
      if (d.gone) continue;
      const ok = await dragBy(page, d.id, d.dx, d.dy);
      console.log(`  拖回 ${d.id} (${d.dx},${d.dy}) → ${ok ? 'ok' : '没找到可拖点'}`);
    }
    const after = await rendered();
    const still = after.filter((n) => {
      const o = BE1_ORIGIN.find((x) => x.id === n.id);
      return !o || Math.abs(o.x - n.x) > 4 || Math.abs(o.y - n.y) > 4;
    });
    console.log(`复原后仍有偏差：${still.length} 个`, JSON.stringify(still.map((n) => n.id)));
    out.driftAfter = still;
    out.restored = still.length === 0;
  } else {
    console.log('⚠️ 真实节点数不足，开始 ⌘Z 撤销');
    let u = 0;
    while (u < 10) {
      const r = await rendered();
      if (r.length >= 11) break;
      await page.keyboard.press('Escape'); await page.waitForTimeout(400);
      await page.keyboard.press('Meta+z'); await page.waitForTimeout(2000);
      u += 1;
    }
    const fin = await rendered();
    console.log(`⌘Z ×${u} 后渲染 ${fin.length} 个`);
    out.undos = u; out.renderedFinal = fin;
    await fitView(page); await page.waitForTimeout(2000);
  }

  // ── 步骤 4：把「⌥⇧F 到底会不会动」用**可靠判据**重做一遍
  //   判据：抽屉里的「共 N 节点」不变不算数，要看**坐标**；
  //   而坐标必须先 ⌘0 框回视口再读，否则读到的是「视口里能看到几个」。
  console.log('\n--- 用可靠判据重做「⌥⇧F 会不会动」---');
  await page.keyboard.press('Escape'); await page.waitForTimeout(800);
  await fitView(page); await page.waitForTimeout(2000);
  const b1 = await rendered();
  console.log('  ⌥⇧F 之前（⌘0 框好后）', b1.length, '个，坐标已记录');
  await page.mouse.click(720, 260); await page.waitForTimeout(900);
  await page.keyboard.press('Meta+Alt+f'); await page.waitForTimeout(3200);
  await clearToasts(page);
  const a1 = await rendered();
  console.log('  ⌥⇧F 之后（**没重新 ⌘0**）', a1.length, '个');
  await fitView(page); await page.waitForTimeout(2200);
  const a2 = await rendered();
  console.log('  ⌥⇧F 之后再 ⌘0', a2.length, '个');
  const changed = a2.filter((n) => { const o = b1.find((x) => x.id === n.id); return o && (o.x !== n.x || o.y !== n.y); });
  const rows = [...new Set(a2.map((n) => n.y))].sort((x, y) => x - y);
  const byRow = {};
  for (const n of a2) (byRow[n.y] = byRow[n.y] || []).push(n);
  const gaps = [];
  for (const k of Object.keys(byRow)) {
    const r = byRow[k].sort((p, q) => p.x - q.x);
    for (let i = 1; i < r.length; i += 1) gaps.push(r[i].x - r[i - 1].x);
  }
  console.log(`  ⌘0 之后对比：坐标变化 ${changed.length} 个；行数 ${rows.length}；同行 x 间距 ${JSON.stringify(gaps)}`);
  out.tidyReliable = {
    nBefore: b1.length, nAfterNoFit: a1.length, nAfterFit: a2.length,
    changedAfterFit: changed.length,
    rows: rows.length, gaps,
    regular: new Set(gaps).size <= 2,
    before: b1, after: a2,
  };
  await shot(page, 'M-189-整理后.png');
  out.shot2 = 'M-189-整理后.png';

  // 复原：⌥⇧F 一般会弹「是否保留此次整理结果？」，点「还原」
  const bar = await page.evaluate(() => [...document.querySelectorAll('button,[role="button"]')]
    .map((e) => { const r = e.getBoundingClientRect();
      return { text: (e.innerText || '').replace(/\s+/g, ' ').trim(), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; })
    .filter((e) => e.rect[2] > 0 && /^(还原|保留)$/.test(e.text)));
  console.log('  确认条按钮:', JSON.stringify(bar));
  out.tidyReliable.confirmBar = bar;
  const back = bar.find((e) => e.text === '还原');
  if (back) {
    await page.mouse.click(back.rect[0] + back.rect[2] / 2, back.rect[1] + back.rect[3] / 2);
    await page.waitForTimeout(2800);
    console.log('  已点「还原」');
    out.tidyReliable.undone = true;
  } else {
    out.tidyReliable.undone = false;
    // 兜底拖回
    const now2 = await rendered();
    for (const n of now2) {
      const o = b1.find((x) => x.id === n.id);
      if (o && (o.x !== n.x || o.y !== n.y)) await dragBy(page, n.id, o.x - n.x, o.y - n.y);
    }
  }
  await fitView(page); await page.waitForTimeout(2000);
  const fin2 = await rendered();
  const stillDrift = fin2.filter((n) => { const o = b1.find((x) => x.id === n.id); return !o || Math.abs(o.x - n.x) > 4 || Math.abs(o.y - n.y) > 4; });
  console.log(`  最终渲染 ${fin2.length} 个；与本轮开始相比有偏差的 ${stillDrift.length} 个`);
  out.finalRendered = fin2.length;
  out.finalDrift = stillDrift.map((n) => n.id);

  await logStep(B, {
    id: 'BE2-recover-tidy-reliable',
    title: '确认节点没丢 / 用可靠判据重做「⌥⇧F 会不会动」',
    target: 'BE1 按 ⌥⇧F 后 `.react-flow__node` 从 11 变 2。先用资产管理抽屉底部「共 N 节点」'
      + '确认真实数量 —— inventory 早就记过「`.react-flow__node` 只统计视口内的渲染节点」，'
      + '而 BD5 的「幂等、0 个节点移动」用的正是那个不可靠的判据。',
    evidence: out,
    visible_text: JSON.stringify({ verdict: out.verdict, tidyReliable: { ...out.tidyReliable, before: undefined, after: undefined } }).slice(0, 3500),
    shot: out.shot2,
  });
  console.log('\nBE2 完成');
} finally {
  await browser.close();
}

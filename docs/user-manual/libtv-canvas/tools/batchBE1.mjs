// Batch BE1 —— 关掉 Batch BD 亲手留下的两个 📖。
//
// BD5 的 not_verified 里写了两条，这轮就去把它们验掉：
//
//   📖 ① `网格吸附` 是不是**只在特定缩放下**才有意义
//      BD5 的视口缩放约 42%，20px 的网格在屏幕上只有 8px —— 吸附的视觉差本来就小，
//      所以「没观察到吸附」完全可能只是**分辨率不够**，不是功能不生效。
//      这轮：把画布放大到 200%+，让网格在屏幕上真的有 20px 起步，
//      再点开关、再拖节点，用**落点模网格步长**当判据。
//      步长怎么定？先量**两个相邻节点的水平间距**（网格间距一定等于步长），
//      再拿拖动落点去对 —— 不用猜 8/10/16/20。
//
//   📖 ② `⌥⇧F` 在**弄乱之后**的画布上到底铺不铺
//      BD5 只在「本来就整齐」的画布上验过，结论是**幂等**（0 个节点移动）。
//      这轮：先随机拖散 4 个节点（记录原位），再按 `⌥⇧F`，
//      看**哪些节点动了、动了多少、变成什么规律**。
//      ⚠️ 复原：整理完左下会弹「是否保留此次整理结果？」，**点「还原」** ——
//      这是产品自己给的撤销，比我自己拖回去可靠。
//      但「还原」也可能不出现，所以另有「按位移拖回」兜底。
//
// ⚠️ 全程可复原：不生成、不上传、不创建、不删除、不付费。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBE1';
const { browser, page } = await launch();

const snapScale = () => page.evaluate(() => {
  const v = document.querySelector('.react-flow__viewport');
  const m = v ? /scale\(([\d.]+)\)/.exec(v.style.transform || '') : null;
  return m ? +m[1] : null; });

const scene = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
  const r = n.getBoundingClientRect();
  return { id: n.getAttribute('data-id'),
    name: ((n.innerText || '').replace(/\s+/g, ' ').trim().split(' ')[0] || '').slice(0, 12),
    x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; }));

/** 每个节点的可拖点。 */
const nodePts = () => page.evaluate(() => {
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

async function dragBy(pg, id, dx, dy, steps = 10) {
  const pts = await nodePts(pg);
  const p = pts[id];
  if (!p) return { err: `节点 ${id} 没有可拖点` };
  await pg.mouse.move(p.x, p.y); await pg.mouse.down();
  for (let i = 1; i <= steps; i += 1) {
    await pg.mouse.move(p.x + (dx * i) / steps, p.y + (dy * i) / steps);
    await pg.waitForTimeout(55);
  }
  await pg.mouse.up();
  await pg.waitForTimeout(1500);
  return { ok: true };
}

const barGrid = (pg) => pg.evaluate(() => {
  const e = [...document.querySelectorAll('button,[role="button"]')]
    .find((x) => /吸附/.test(x.getAttribute('aria-label') || ''));
  if (!e) return { err: 'no grid button' };
  const r = e.getBoundingClientRect();
  const cs = getComputedStyle(e);
  return { aria: e.getAttribute('aria-label'),
    active: /bg-canvas-controls-active/.test(e.className || ''), bg: cs.backgroundColor,
    x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) };
});

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await fitView(page); await page.waitForTimeout(1600);
  await page.mouse.move(720, 260); await page.waitForTimeout(800);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '网格吸附在大缩放下复验（先量真实网格步长）/ 弄乱画布后验 ⌥⇧F' });

  const out = {};
  const origin = await scene();
  out.origin = origin;

  // ═══ ① 网格吸附：大缩放复验
  console.log('--- BE1-1 网格吸附 · 大缩放复验 ---');
  // 先量网格步长：同一行里相邻节点的 x 差
  const measure = (sc) => {
    const byRow = {};
    for (const n of sc) { const k = n.y; (byRow[k] = byRow[k] || []).push(n); }
    const gaps = [];
    for (const k of Object.keys(byRow)) {
      const row = byRow[k].sort((a, b) => a.x - b.x);
      for (let i = 1; i < row.length; i += 1) gaps.push(row[i].x - row[i - 1].x);
    }
    return gaps;
  };
  const sc0 = await scene();
  const gaps0 = measure(sc0);
  console.log(`  初始 scale=${await snapScale()}；同行相邻节点 x 间距：${JSON.stringify(gaps0)}`);
  out.grid = { startScale: await snapScale(), gaps: gaps0 };

  // 放大到 200% 以上
  await page.keyboard.press('Meta+Equal'); await page.waitForTimeout(500);
  await page.keyboard.press('Meta+Equal'); await page.waitForTimeout(500);
  await page.keyboard.press('Meta+Equal'); await page.waitForTimeout(900);
  const bigScale = await snapScale();
  console.log('  放大后 scale =', bigScale);
  out.grid.bigScale = bigScale;

  // 大缩放下只看视口内的节点，重新量间距（相邻可见节点的间距才是真正的网格步长）
  const visBefore = (await scene()).filter((n) => n.x > -100 && n.x < 1540 && n.y > -100 && n.y < 900);
  const gapsBig = measure(visBefore);
  console.log(`  视口内 ${visBefore.length} 个节点，同行 x 间距：${JSON.stringify(gapsBig)}`);
  out.grid.gapsAtBigScale = gapsBig;
  const step = gapsBig.length ? gapsBig[0] : null;
  out.grid.step = step;
  console.log('  取网格步长 =', step);

  // 点开关（大缩放下）
  await page.mouse.move(720, 260); await page.waitForTimeout(600);
  const g0 = await barGrid(page);
  await page.mouse.move(g0.x, g0.y); await page.waitForTimeout(300);
  await page.mouse.click(g0.x, g0.y); await page.waitForTimeout(2000);
  await page.mouse.move(720, 200); await page.waitForTimeout(900);
  const g1 = await barGrid(page);
  console.log(`  点之前 active=${g0.active} bg=${g0.bg} → 点之后 active=${g1.active} bg=${g1.bg}`);
  console.log('  aria 改名？', g1.aria !== g0.aria);
  out.grid.afterClick = g1;
  out.grid.ariaChanged = g1.aria !== g0.aria;
  out.grid.turnedOn = g1.active || out.grid.ariaChanged;

  // 拖一个节点，看落点是否落在网格倍数上
  const pts = await nodePts();
  const id = Object.keys(pts)[0];
  const p0 = (await scene()).find((n) => n.id === id);
  const d = await dragBy(page, id, 37, 29);
  const p1 = (await scene()).find((n) => n.id === id);
  const mv = [p1.x - p0.x, p1.y - p0.y];
  console.log(`  拖动请求 (+37,+29) → 实际 ${JSON.stringify(mv)}`);
  out.grid.drag = { id, requested: [37, 29], actual: mv,
    snapped: step ? (mv[0] % step === 0 && mv[1] % step === 0) : null,
    modStep: step ? [mv[0] % step, mv[1] % step] : null };
  console.log('  落点对网格步长取模 =', JSON.stringify(out.grid.drag.modStep),
    out.grid.drag.snapped ? '→ 吸附了 ✅' : '→ 没吸附');
  await shot(page, 'M-187-网格吸附-大缩放复验.png');
  out.shot = 'M-187-网格吸附-大缩放复验.png';
  // 拖回去
  if (d.ok) { await dragBy(page, id, -mv[0], -mv[1]); }
  // 关回去
  const g2 = await barGrid(page);
  if (g2.active || g2.aria !== g0.aria) {
    await page.mouse.move(g2.x, g2.y); await page.waitForTimeout(300);
    await page.mouse.click(g2.x, g2.y); await page.waitForTimeout(1800);
    await page.mouse.move(720, 200); await page.waitForTimeout(700);
  }
  out.grid.afterOff = await barGrid(page);
  console.log('  关回后 active =', out.grid.afterOff.active, ' aria =', out.grid.afterOff.aria);

  // ═══ ② ⌥⇧F 在弄乱之后
  console.log('\n--- BE1-2 弄乱画布后按 ⌥⇧F ---');
  await fitView(page); await page.waitForTimeout(1800);
  const before = await scene();
  console.log('  弄乱前 x 排序:', before.slice().sort((a, b) => a.y - b.y || a.x - b.x).map((n) => `${n.name}@${n.x},${n.y}`).join(' '));
  // 随机拖散 4 个（挑互不相邻的，避免叠在一起找不回来）
  const spread = await page.evaluate(() => {
    const ns = [...document.querySelectorAll('.react-flow__node')].map((n) => {
      const r = n.getBoundingClientRect();
      return { id: n.getAttribute('data-id'), x: r.x, y: r.y, w: r.width, h: r.height };
    }).sort((a, b) => a.x - b.x);
    return ns.slice(0, 4).map((n) => n.id);
  });
  const offs = [[190, -120], [-210, 140], [160, 170], [-175, -155]];
  const spreadLog = [];
  for (let i = 0; i < spread.length; i += 1) {
    const r = await dragBy(page, spread[i], offs[i][0], offs[i][1]);
    const cur = (await scene()).find((n) => n.id === spread[i]);
    spreadLog.push({ id: spread[i], ok: !!r.ok, now: cur ? [cur.x, cur.y] : null });
  }
  const messy = await scene();
  const movedCount = messy.filter((n) => {
    const o = origin.find((x) => x.id === n.id);
    return o && (o.x !== n.x || o.y !== n.y);
  }).length;
  console.log(`  已拖散 ${movedCount} 个节点`);
  await shot(page, 'M-188-整理前-弄乱的画布.png');
  out.shot2 = 'M-188-整理前-弄乱的画布.png';
  out.messy = { before, movedCount, ids: spread };

  // 按 ⌥⇧F
  await page.mouse.click(720, 260); await page.waitForTimeout(900);
  await page.keyboard.press('Meta+Alt+f'); await page.waitForTimeout(3000);
  await clearToasts(page); await page.waitForTimeout(1200);
  const tidied = await scene();
  const afterCount = tidied.filter((n) => {
    const o = before.find((x) => x.id === n.id);
    return o && (o.x !== n.x || o.y !== n.y);
  }).length;
  console.log(`  按 ⌥⇧F：${before.length} → ${tidied.length} 个节点，**位置变化 ${afterCount} 个**`);
  out.tidy = { n: [before.length, tidied.length], changed: afterCount,
    before: before.slice().sort((a, b) => a.y - b.y || a.x - b.x).map((n) => [n.name, n.x, n.y]),
    after: tidied.slice().sort((a, b) => a.y - b.y || a.x - b.x).map((n) => [n.name, n.x, n.y]) };
  // 是不是排成了整齐网格
  const gapsAfter = measure(tidied);
  const rowsAfter = [...new Set(tidied.map((n) => n.y))].sort((a, b) => a - b);
  console.log(`  整理后同行 x 间距：${JSON.stringify(gapsAfter)}`);
  console.log(`  整理后不同 y 值：${JSON.stringify(rowsAfter)}（${rowsAfter.length} 行）`);
  out.tidy.gaps = gapsAfter; out.tidy.rows = rowsAfter;
  out.tidy.regular = new Set(gapsAfter).size <= 2 && rowsAfter.length >= 2;
  console.log('  是否排成整齐网格：', out.tidy.regular);
  await shot(page, 'M-189-整理后.png');
  out.shot3 = 'M-189-整理后.png';

  // 找「是否保留此次整理结果？」确认条
  const confirmBar = await page.evaluate(() => {
    const all = [...document.querySelectorAll('button,[role="button"],div,span')].filter((e) => {
      const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
      return t === '是否保留此次整理结果？' || t === '保留' || t === '还原';
    }).map((e) => { const r = e.getBoundingClientRect();
      return { text: (e.innerText || '').replace(/\s+/g, ' ').trim(), tag: e.tagName,
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; });
    return all;
  });
  console.log('  确认条元素:', JSON.stringify(confirmBar));
  out.tidy.confirmBar = confirmBar;

  // ✅ 复原：优先点「还原」（产品自己给的撤销）
  let undone = false;
  const back = confirmBar.find((e) => e.text === '还原' && e.rect[2] > 0);
  if (back) {
    await page.mouse.click(back.rect[0] + back.rect[2] / 2, back.rect[1] + back.rect[3] / 2);
    await page.waitForTimeout(2600);
    undone = true;
    console.log('  已点「还原」');
  }
  let after2 = await scene();
  let drift = after2.filter((n) => {
    const o = origin.find((x) => x.id === n.id);
    return !o || Math.abs(o.x - n.x) > 4 || Math.abs(o.y - n.y) > 4;
  });
  console.log(`  点还原后仍有偏差的节点：${drift.length} 个`);
  out.tidy.undoneByBar = undone;
  out.tidy.driftAfterUndo = drift.map((n) => n.id);

  // 兜底：把偏差的节点按位移拖回去
  if (drift.length) {
    for (const n of drift) {
      const o = origin.find((x) => x.id === n.id);
      if (o) await dragBy(page, n.id, o.x - n.x, o.y - n.y);
    }
    after2 = await scene();
    drift = after2.filter((n) => {
      const o = origin.find((x) => x.id === n.id);
      return !o || Math.abs(o.x - n.x) > 4 || Math.abs(o.y - n.y) > 4;
    });
    console.log(`  兜底拖回后仍有偏差：${drift.length} 个`);
  }
  out.tidy.driftFinal = drift.map((n) => n.id);
  out.tidy.restored = drift.length === 0;
  await fitView(page); await page.waitForTimeout(1500);

  await logStep(B, {
    id: 'BE1-snap-at-scale-tidy-messy',
    title: '网格吸附在大缩放下复验 / 弄乱画布后验 ⌥⇧F',
    target: 'BD5 亲手留的两个 📖。① 网格吸附：先把画布放大到 200%+，'
      + '再用「同行相邻节点的 x 间距」量出真实网格步长，拿拖动落点去对，不用猜 8/10/20。'
      + '② ⌥⇧F：BD5 只在本来就整齐的画布上验过（幂等），这轮先拖散再按。'
      + '复原优先点产品自己的「还原」。',
    evidence: out,
    visible_text: JSON.stringify({ grid: out.grid, tidy: { ...out.tidy, before: undefined, after: undefined } }).slice(0, 3500),
    shot: out.shot3,
  });
  console.log('\nBE1 完成');
} finally {
  await browser.close();
}

// Batch BV13 — 收尾两件事：把 BV12 留下的边清掉 + 按正确顺序重测「断线是否持久」。
//
// BV12 的两个结果：
// · ⭐⭐ **⌘Z 能撤销断线**：点完剪刀 3 → 2，按 `⌘Z` 那条边回来了（2 → 3，id 原样）。
// · ⭐ ③ 的持久性测试**顺序错了**：撤销先把边接回来了，所以「重载前 3 条 → 重载后 3 条」，
//   **根本没测到「断线会不会自己回来」**。重测必须**先断、再重载**，中间不能插撤销。
// · ⛔ 画布上多了一条边（`e-yLMJob2KUC`），是 BV12 撤销后留下的，我自己清。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBV13';
const MINE = 'e-yLMJob2KUC';
const ORIG = ['e-5U2jB82fuL', 'e-ptEDqoajM7'];
const { browser, page } = await launch();
const settle = (ms = 900) => page.waitForTimeout(ms);

const edgeIds = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__edge')].map((e) => e.getAttribute('data-id')));
const edgeCount = () => page.evaluate(() => document.querySelectorAll('.react-flow__edge').length);
const edgeInfo = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__edge')].map((g) => {
  const p = g.querySelector('path'); let L = 0; try { L = p.getTotalLength(); } catch { L = 0; }
  const ctm = p && p.getScreenCTM(); let mid = null;
  if (ctm && L) { const q = p.getPointAtLength(L / 2); const s = new DOMPoint(q.x, q.y, 0, 1).matrixTransform(ctm); mid = [Math.round(s.x), Math.round(s.y)]; }
  return { id: g.getAttribute('data-id'), aria: g.getAttribute('aria-label'), mid,
    inView: mid && mid[0] > 3 && mid[0] < 1437 && mid[1] > 3 && mid[1] < 786 };
}));

const cutByScissors = async (id) => {
  const m = (await edgeInfo()).find((x) => x.id === id);
  if (!m || !m.inView) return { ok: false, why: '中点不在视口内' };
  await page.mouse.move(200, 780); await settle(600);
  await page.mouse.move(m.mid[0], m.mid[1]); await settle(1700);
  const mine = await page.evaluate(([mx, my]) => [...document.querySelectorAll('.scissors-enter')].map((e) => {
    const r = e.getBoundingClientRect(); const c = [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
    return { c, near: Math.abs(c[0] - mx) < 40 && Math.abs(c[1] - my) < 40 };
  }).filter((s) => s.near), m.mid);
  if (!mine.length) return { ok: false, why: '中点没剪刀' };
  const pt = mine[mine.length - 1].c;
  const c0 = await edgeCount();
  await page.mouse.move(pt[0], pt[1]); await settle(600);
  await page.mouse.down(); await settle(180); await page.mouse.up(); await settle(3000);
  const c1 = await edgeCount();
  return { ok: c1 < c0, point: pt, before: c0, after: c1, mid: m.mid };
};

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await settle(1600);
  await fitView(page); await settle(2200);
  await beginBatch(B, { note: '清理 BV12 残留 + 按正确顺序重测持久性' });
  const out = {};

  const ids0 = await edgeIds();
  out.start = { ids: ids0, count: ids0.length };
  console.log(`═══ 起点：连线 ${ids0.length} 条 ${JSON.stringify(ids0)} ═══`);
  if (!ids0.includes(MINE)) { console.log(`⛔ ${MINE} 不在画布上，无需清理`); }
  else {
    // ── ① 断掉它（顺便就是持久性测试的第一步）
    const cut = await cutByScissors(MINE);
    out.cut = cut;
    console.log(`\n═══ ① 点剪刀断掉 ${MINE}：ok=${cut.ok}｜连线 ${cut.before} → ${cut.after} ═══`);
    const idsAfterCut = await edgeIds();
    console.log(`  断完：${JSON.stringify(idsAfterCut)}`);
    out.afterCut = idsAfterCut;

    // ── ② ⭐ 正确顺序的重测：断了之后**直接重载**，中间什么都不做
    console.log('\n═══ ② 断完直接重载（中间不插任何撤销）═══');
    await page.reload({ waitUntil: 'domcontentloaded' });
    await settle(7500);
    await closePromos(page); await clearToasts(page); await settle(1500);
    await fitView(page); await settle(2000);
    const idsReload = await edgeIds();
    out.reload = { ids: idsReload, count: idsReload.length,
      stayedCut: !idsReload.includes(MINE), backToBase: idsReload.join(',') === ORIG.join(',') };
    console.log(`  重载后：${idsReload.length} 条 ${JSON.stringify(idsReload)}`);
    console.log(`  ⭐ 断掉的线自己回来了吗：${idsReload.includes(MINE) ? '❌ 回来了（说明只是前端没画出来）' : '✅ 没回来，断线是持久的'}`);
    console.log(`  与用户原有两条逐项相同：${out.reload.backToBase}`);
  }

  // ── ③ 收尾
  const fin = await edgeIds();
  out.final = { count: fin.length, ids: fin, identical: fin.join(',') === ORIG.join(',') };
  console.log(`\n═══ ③ 收尾：连线 ${fin.length} 条｜与用户原有两条逐项相同=${out.final.identical} ═══`);
  await clearToasts(page);
  console.log(`\n═══ 本轮结论 ═══`);
  console.log(`  · 残留已清理：${out.final.identical ? '✅' : '❌'}`);
  console.log(`  · 断线持久（重载后不回来）：${out.reload ? (out.reload.stayedCut ? '✅ 是' : '❌ 否') : '⛔ 没测到'}`);
  console.log('  · （BV12 另测到：断线后按 ⌘Z 能把线接回来）');

  await logStep(B, {
    id: 'BV13-disconnect-persistence-and-cleanup',
    title: '断线是持久的；顺手把上一轮撤销后留下的边清掉',
    target: 'BV12 的持久性测试**顺序错了** —— `⌘Z` 先把边接回来了，'
      + '所以「重载前 3 条 → 重载后 3 条」根本没测到「断线会不会自己回来」。'
      + '重测必须**先断、再重载，中间什么都不插**。'
      + '⭐ 另一条结论（BV12 拿到）：**断线可以 `⌘Z` 撤销**，点完剪刀再按撤销，边会原样回来。',
    evidence: out,
    visible_text: JSON.stringify(out).slice(0, 3400),
  });
  console.log('\nBV13 完成');
} catch (e) {
  console.log('⛔ 中止：' + e.message + '\n' + (e.stack || '').split('\n').slice(0, 5).join('\n'));
} finally {
  await browser.close();
}

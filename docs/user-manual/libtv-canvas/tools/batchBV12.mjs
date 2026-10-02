// Batch BV12 — 断线之后还能不能救回来？
//
// 断线**没有二次确认**（BV10 实测：点完直接少一条边，没有弹窗、没有提示条）。
// 那就必须回答一个用户立刻会问的问题：**点错了能不能撤回来？**
// 还有第二个：**重载页面之后它还是断的吗**（是不是只断在前端、刷新就回来了）。
//
// ⭐ 这两个都是只读性质的风险测试：造的是自己的边，删的也是自己的边，
//    最坏情况就是「边没了」，画布正好回到基线。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBV12';
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
const nodeBox = (id) => page.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return null; const r = n.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, id);
const handleAt = (nodeId, kind) => page.evaluate(({ nodeId, kind }) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nodeId}"]`);
  if (!n) return null;
  const h = [...n.querySelectorAll('.react-flow__handle')].find((x) => kind === 'source' ? /\bsource\b/.test(x.getAttribute('class') || '') : /\btarget\b/.test(x.getAttribute('class') || ''));
  if (!h) return null; const r = h.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y)];
}, { nodeId, kind });

const makeEdge = async (a, b) => {
  const n0 = await edgeCount(); const ids0 = await edgeIds();
  const na = await nodeBox(a); const nb = await nodeBox(b);
  if (!na || !nb) return { ok: false, why: '节点不在视口' };
  await page.mouse.move(na[0], na[1]); await settle(1100);
  const hs = await handleAt(a, 'source');
  await page.mouse.move(nb[0], nb[1]); await settle(1100);
  const ht = await handleAt(b, 'target');
  if (!hs || !ht) return { ok: false, why: 'handle 取不到' };
  await page.mouse.move(hs[0], hs[1]); await settle(700);
  await page.mouse.down(); await settle(350);
  await page.mouse.move(hs[0] + 8, hs[1] + 4); await settle(300);
  await page.mouse.move((hs[0] + ht[0]) / 2, (hs[1] + ht[1]) / 2); await settle(450);
  const preview = await page.evaluate(() => document.querySelectorAll('.react-flow__connection, .react-flow__connectionline').length);
  await page.mouse.move(ht[0], ht[1]); await settle(450);
  await page.mouse.up(); await settle(2400);
  const extra = (await edgeIds()).filter((i) => !ids0.includes(i));
  return { ok: extra.length === 1, preview, n0, extra: extra[0] };
};
const scissorsOn = async (id) => {
  const m = (await edgeInfo()).find((x) => x.id === id);
  if (!m || !m.inView) return { ok: false, mid: m && m.mid };
  await page.mouse.move(200, 780); await settle(600);
  await page.mouse.move(m.mid[0], m.mid[1]); await settle(1700);
  const list = await page.evaluate(([mx, my]) => [...document.querySelectorAll('.scissors-enter')].map((e) => {
    const r = e.getBoundingClientRect(); const c = [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
    return { center: c, near: Math.abs(c[0] - mx) < 40 && Math.abs(c[1] - my) < 40 };
  }), m.mid);
  const mine = list.filter((s) => s.near);
  return { ok: mine.length > 0, mid: m.mid, mine };
};
const undoOnce = async (label) => {
  const c0 = await edgeCount();
  await page.keyboard.down('Meta'); await page.keyboard.press('z'); await page.keyboard.up('Meta');
  await settle(2600);
  const c1 = await edgeCount();
  console.log(`  ${label}：连线 ${c0} → ${c1}`);
  return { label, before: c0, after: c1 };
};

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await settle(1600);
  await fitView(page); await settle(2200);
  await beginBatch(B, { note: '断线后能否撤销 + 重载后是否持久' });
  const out = {};
  const baseIds = (await edgeInfo()).map((e) => e.id);
  out.base = { ids: baseIds, count: baseIds.length };
  console.log(`═══ 基线：连线 ${baseIds.length} 条 ${JSON.stringify(baseIds)} ═══`);

  // ── ① 造边 → 点剪刀
  const made = await makeEdge('i-9nlG6HdjK2', 'v-v2hlWY4Br3');
  console.log(`\n═══ ① 造边：ok=${made.ok}｜预览线 ${made.preview}｜新增 ${JSON.stringify(made.extra)} ═══`);
  out.made = made;
  if (!made.ok) { console.log('⛔ 没造出边，本轮不测撤销'); }
  else {
    const sc = await scissorsOn(made.extra);
    console.log(`  自造边中点 ${JSON.stringify(sc.mid)}：剪刀 ${sc.ok ? '有' : '无'}`);
    out.scissors = sc;
    if (sc.ok) {
      const pt = sc.mine[sc.mine.length - 1].center;
      const c0 = await edgeCount();
      await page.mouse.move(pt[0], pt[1]); await settle(600);
      await page.mouse.down(); await settle(180); await page.mouse.up(); await settle(3200);
      const c1 = await edgeCount();
      console.log(`  ⭐ 点剪刀：${c0} → ${c1}`);
      out.cut = { point: pt, before: c0, after: c1 };

      // ── ② ⌘Z 能不能把线接回来
      console.log('\n═══ ② 断线之后：⌘Z 能撤销吗 ═══');
      const u1 = await undoOnce('⌘Z');
      const idsAfterUndo = await edgeIds();
      out.undo = { first: u1, idsAfterUndo, restored: idsAfterUndo.includes(made.extra) };
      console.log(`  自造边回来了吗：${idsAfterUndo.includes(made.extra) ? '✅ 回来了' : '❌ 没回来'}｜当前 ${JSON.stringify(idsAfterUndo)}`);
      if (!idsAfterUndo.includes(made.extra)) {
        const u2 = await undoOnce('再按一次 ⌘Z');
        const ids2 = await edgeIds();
        console.log(`  两次之后：${ids2.includes(made.extra) ? '✅ 回来了' : '❌ 仍没回来'}｜${JSON.stringify(ids2)}`);
        out.undo.second = u2; out.undo.idsAfterSecond = ids2; out.undo.restoredAfterSecond = ids2.includes(made.extra);
      }
      await clearToasts(page);
    }
  }

  // ── ③ 断线是不是「真的断了」：重载页面再看
  console.log('\n═══ ③ 重载页面：断掉的线会不会自己回来 ═══');
  const beforeReload = await edgeCount();
  await page.reload({ waitUntil: 'domcontentloaded' });
  await settle(7000);
  await closePromos(page); await clearToasts(page); await settle(1500);
  await fitView(page); await settle(2000);
  const afterReload = await edgeCount();
  const idsReload = await edgeIds();
  console.log(`  重载前 ${beforeReload} 条 → 重载后 ${afterReload} 条 ${JSON.stringify(idsReload)}`);
  out.persist = { before: beforeReload, after: afterReload, ids: idsReload,
    sameAsBase: idsReload.join(',') === baseIds.join(',') };
  console.log(`  与基线逐项相同：${out.persist.sameAsBase}`);

  // ── ④ 收尾
  const fin = await edgeIds();
  out.final = { count: fin.length, ids: fin, identical: fin.join(',') === baseIds.join(',') };
  console.log(`\n═══ ④ 收尾：连线 ${fin.length} 条｜与基线逐项相同=${out.final.identical}`);
  await clearToasts(page);

  console.log(`\n═══ 本轮结论 ═══`);
  console.log(`  · 断线后 ⌘Z 能撤销吗？ ${out.undo ? (out.undo.restored ? '✅ 能' : (out.undo.restoredAfterSecond ? '✅ 两次之后能' : '❌ 不能')) : '⛔ 没测到'}`);
  console.log(`  · 断线是持久的吗（重载后不回来）？ ${out.persist.after < out.persist.before ? '✅ 持久' : (out.persist.sameAsBase ? '（本来就没多出线，测不了）' : '⚠️ 看数据')}`);
  console.log(`  · 画布回到基线：${out.final.identical ? '✅' : '❌'}`);

  await logStep(B, {
    id: 'BV12-can-disconnect-be-undone',
    title: '断线没有二次确认 —— 那点错了能不能 ⌘Z 撤回来？重载后还在不在？',
    target: '断线**没有确认框、没有提示条**（BV10 实测），用户立刻会问「点错了能救吗」。'
      + '本轮在**自造边**上测两件事：① 断掉后按 `⌘Z`（快捷键面板里的「撤销」）能不能接回来；'
      + '② **重载页面**再看一次连线数 —— 分清「真断了」和「只是前端没画出来」。',
    evidence: out,
    visible_text: JSON.stringify(out).slice(0, 3400),
  });
  console.log('\nBV12 完成');
} catch (e) {
  console.log('⛔ 中止：' + e.message + '\n' + (e.stack || '').split('\n').slice(0, 5).join('\n'));
} finally {
  await browser.close();
}

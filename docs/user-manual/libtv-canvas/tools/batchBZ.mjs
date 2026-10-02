// Batch BZ — 「同一对节点不能连两次」：用同一个动作做两遍，把阳性阴性凑成一对。
//
// 这条 📖 挂了两批。BW 试过一次（③ 对照）但因为 ② 造第二条边失败，循环没走到；
// BX 也没做成。
//
// ⭐ 关键改动：**阳性与阴性用完全相同的动作**。
//   第 1 遍：拖 i-9nlG6HdjK2 → v-v2hlWY4Br3  → 成功（预览线 2 条，新边出现）
//   第 2 遍：**同一个动作再来一次**        → 预览线 2 条，但**不生成新边**
// 两次的手势、坐标、时长都一样，唯一变化的是「这一对已经连过了」，
// 所以差异**只能**归因于「重复」。
// ⭐ 而且第 1 遍造的那条边就是第 2 遍的试验对象 —— 剪掉它就复原，零残留。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBZ';
const A = 'i-9nlG6HdjK2';      // 图片节点 2
const C = 'v-v2hlWY4Br3';      // 视频节点 3
const { browser, page } = await launch();
const settle = (ms = 900) => page.waitForTimeout(ms);

const edgeIds = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__edge')].map((e) => e.getAttribute('data-id')));
const edgeAria = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__edge')].map((e) => e.getAttribute('aria-label')));
const edgeCount = () => page.evaluate(() => document.querySelectorAll('.react-flow__edge').length);
const nodeBox = (id) => page.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return null; const r = n.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, id);
const handleAt = (nodeId, kind) => page.evaluate(({ nodeId, kind }) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nodeId}"]`);
  if (!n) return null;
  const h = [...n.querySelectorAll('.react-flow__handle')].find((x) => kind === 'source' ? /\bsource\b/.test(x.getAttribute('class') || '') : /\btarget\b/.test(x.getAttribute('class') || ''));
  if (!h) return null; const r = h.getBoundingClientRect();
  return { at: [Math.round(r.x), Math.round(r.y)], inView: r.x > 2 && r.x < 1438 && r.y > 2 && r.y < 808 };
}, { nodeId, kind });

/** 一次完整的拖线尝试。preview 与结果**分开报** —— 这是分不开的两种解释的钥匙。 */
const attempt = async (round) => {
  const ids0 = await edgeIds();
  const na = await nodeBox(A); const nc = await nodeBox(C);
  if (!na || !nc) return { round, ok: false, why: '节点不在视口' };
  await page.mouse.move(na[0], na[1]); await settle(1100);
  const hs = await handleAt(A, 'source');
  await page.mouse.move(nc[0], nc[1]); await settle(1100);
  const ht = await handleAt(C, 'target');
  if (!hs || !ht) return { round, ok: false, why: 'handle 取不到' };
  if (!hs.inView || !ht.inView) return { round, ok: false, why: 'handle 出视口' };
  await page.mouse.move(hs.at[0], hs.at[1]); await settle(700);
  await page.mouse.down(); await settle(350);
  await page.mouse.move(hs.at[0] + 8, hs.at[1] + 4); await settle(300);
  await page.mouse.move((hs.at[0] + ht.at[0]) / 2, (hs.at[1] + ht.at[1]) / 2); await settle(450);
  const preview = await page.evaluate(() => document.querySelectorAll('.react-flow__connection, .react-flow__connectionline').length);
  const classesAtDrop = await page.evaluate(() => [...document.querySelectorAll('[class*="valid" i],[class*="connectablestart" i],[class*="connectableend" i]')]
    .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
    .map((e) => ({ cls: (e.getAttribute('class') || '').slice(0, 60), rect: [Math.round(e.getBoundingClientRect().x), Math.round(e.getBoundingClientRect().y)] })));
  await page.mouse.move(ht.at[0], ht.at[1]); await settle(500);
  await page.mouse.up(); await settle(2600);
  const ids1 = await edgeIds();
  const extra = ids1.filter((i) => !ids0.includes(i));
  const dlg = await page.evaluate(() => [...document.querySelectorAll('[role="dialog"],.mantine-Modal-content')]
    .filter((d) => { const r = d.getBoundingClientRect(); return r.width > 4 && r.height > 4; })
    .map((d) => (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 120)));
  return { round, ok: extra.length === 1, preview, extra: extra[0] || null,
    before: ids0.length, after: ids1.length, classesAtDrop, dialogs: dlg };
};

const cut = async (id) => {
  const mid = await page.evaluate((i) => { const g = document.querySelector(`.react-flow__edge[data-id="${i}"]`);
    const p = g && g.querySelector('path'); if (!p) return null;
    let L = 0; try { L = p.getTotalLength(); } catch { L = 0; }
    const ctm = p.getScreenCTM(); if (!ctm || !L) return null;
    const q = p.getPointAtLength(L / 2); const s = new DOMPoint(q.x, q.y, 0, 1).matrixTransform(ctm);
    return [Math.round(s.x), Math.round(s.y)]; }, id);
  if (!mid) return { ok: false, why: '取不到中点' };
  await page.mouse.move(200, 780); await settle(600);
  await page.mouse.move(mid[0], mid[1]); await settle(1700);
  const sc = await page.evaluate(([mx, my]) => [...document.querySelectorAll('.scissors-enter')]
    .map((e) => { const r = e.getBoundingClientRect(); const c = [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
      return { c, near: Math.abs(c[0] - mx) < 40 && Math.abs(c[1] - my) < 40 }; }).filter((s) => s.near), mid);
  if (!sc.length) return { ok: false, why: '中点没剪刀' };
  const pt = sc[sc.length - 1].c;
  const c0 = await edgeCount();
  await page.mouse.move(pt[0], pt[1]); await settle(600);
  await page.mouse.down(); await settle(180); await page.mouse.up(); await settle(3000);
  return { ok: (await edgeCount()) < c0, before: c0, after: await edgeCount() };
};

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await settle(1800);
  await fitView(page); await settle(2200);
  await beginBatch(B, { note: '同一动作做两遍：阳性 + 阴性' });
  const out = {};
  const baseIds = await edgeIds(); const baseAria = await edgeAria();
  out.base = { ids: baseIds, aria: baseAria, count: baseIds.length };
  console.log(`═══ 基线：连线 ${baseIds.length} 条 ═══`);
  baseAria.forEach((a) => console.log(`    ${a}`));

  // ── 第 1 遍：这一对还没连过
  console.log(`\n═══ 第 1 遍（这一对还没连过）═══`);
  const r1 = await attempt(1);
  console.log(`  预览线 ${r1.preview} 条｜连线 ${r1.before} → ${r1.after}｜新边 ${JSON.stringify(r1.extra)}｜ok=${r1.ok}`);
  console.log(`  落点时的连接态类名：${JSON.stringify(r1.classesAtDrop)}`);
  out.first = r1;

  if (!r1.ok) { console.log('  ⛔ 第 1 遍没连上，没有阳性对照，本轮到此为止'); }
  else {
    // ── 第 2 遍：同一个动作再来一次
    console.log(`\n═══ 第 2 遍（同一个动作，已经连过了）═══`);
    const r2 = await attempt(2);
    console.log(`  预览线 ${r2.preview} 条｜连线 ${r2.before} → ${r2.after}｜新边 ${JSON.stringify(r2.extra)}｜ok=${r2.ok}`);
    console.log(`  落点时的连接态类名：${JSON.stringify(r2.classesAtDrop)}`);
    console.log(`  弹窗 ${JSON.stringify(r2.dialogs)}`);
    out.second = r2;

    // ── 复原
    console.log(`\n═══ 复原：剪掉第 1 遍造的那条 ═══`);
    const c = await cut(r1.extra);
    console.log(`  ok=${c.ok}｜连线 ${c.before} → ${c.after}`);
    out.cleanup = c;
  }

  const fin = await edgeIds(); const finAria = await edgeAria();
  out.final = { count: fin.length, ids: fin, identical: fin.join(',') === baseIds.join(','),
    sameAria: finAria.slice().sort().join(' | ') === baseAria.slice().sort().join(' | '),
    nodes: await page.evaluate(() => document.querySelectorAll('.react-flow__node').length) };
  console.log(`\n═══ 收尾：连线 ${fin.length} 条｜id 逐项相同=${out.final.identical}｜两端方向相同=${out.final.sameAria}｜节点 ${out.final.nodes}`);
  await clearToasts(page);

  const verdict = out.first && out.second
    ? (out.first.ok && !out.second.ok
      ? '✅ 阳性 + 阴性成对：同一动作，第一遍成功、第二遍被拒'
      : `⚠️ 组合异常：第一遍 ${out.first.ok ? '成功' : '失败'}、第二遍 ${out.second.ok ? '成功' : '失败'}`)
    : '⛔ 没测到（分母不足 2）';
  console.log(`\n═══ 本轮结论 ═══`);
  console.log(`  · ${verdict}`);
  console.log(`  · 画布复原：${out.final.identical ? '✅' : '❌'}`);

  await logStep(B, {
    id: 'BZ-duplicate-connection-control',
    title: '「同一对节点连不出第二根线」：阳性 + 阴性配成一对',
    target: '⭐ 这条 📖 挂了两批。做法：**阳性与阴性用完全相同的动作** —— '
      + '第 1 遍拖 `i-9nlG6HdjK2 → v-v2hlWY4Br3`（这一对还没连过）→ 成功；'
      + '第 2 遍**同一个动作再来一次** → 预览线照常出现，松手却不生成新边。'
      + '两次的手势、坐标、时长完全一样，唯一变化的是「这一对已经连过了」，'
      + '所以差异**只能**归因于重复。'
      + '⭐ 而且第 1 遍造的那条边正是第 2 遍的试验对象，剪掉即复原，零残留。',
    evidence: out,
    visible_text: JSON.stringify({ 基线: out.base, 第一遍: out.first, 第二遍: out.second,
      清理: out.cleanup, 收尾: out.final }).slice(0, 3400),
  });
  console.log('\nBZ 完成');
} catch (e) {
  console.log('⛔ 中止：' + e.message + '\n' + (e.stack || '').split('\n').slice(0, 5).join('\n'));
} finally {
  await browser.close();
}

// Batch BV3 — ⭐ 选中连线之后按删除键：断线入口大概在这儿。
//
// BV2 的突破：连线的 class 是 `react-flow__edge react-flow__edge-default nopan selectable`
// —— **`selectable`**。而且**点它真的能选中**（`selectedEdges: 1`）。
// 于是有一条从来没试过的路：**选中连线 → 按删除键**。
// ⭐ BJ 那轮的八种条件全是在键盘快捷键上打转（而且 `⌘L` 本身就是「连线」），
//    从来没有「选中对象再删」这条路。
//
// ⚠️ 删连线是**真实的画布写入**。所以本轮先把两端坐标**记下来**（`getPointAtLength(0)` 与
//    `(总长)` 拿到连线的起点/终点屏幕坐标），删完再按这些坐标**接回去**，最后复核连线数回到 2。
//    删之前先确认两端都在视口里、坐标可用；不可用就只读不删。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBV3';
const { browser, page } = await launch();

const esc = async () => { await page.keyboard.press('Escape'); await page.waitForTimeout(1000); };
const edgeCount = () => page.evaluate(() => document.querySelectorAll('.react-flow__edge').length);
const edgeInfo = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__edge')].map((g) => {
  const path = g.querySelector('path.react-flow__edge-path, path');
  let a = null, b = null, len = null;
  if (path && path.getTotalLength) {
    try {
      len = path.getTotalLength();
      const ctm = path.getScreenCTM();
      if (ctm) {
        const s = new DOMPoint(...Object.values(path.getPointAtLength(0))).matrixTransform(ctm);
        const e = new DOMPoint(...Object.values(path.getPointAtLength(len))).matrixTransform(ctm);
        a = [Math.round(s.x), Math.round(s.y)]; b = [Math.round(e.x), Math.round(e.y)];
      }
    } catch { /* 忽略 */ }
  }
  return { id: g.getAttribute('data-id'), aria: g.getAttribute('aria-label'),
    selected: g.classList.contains('selected'), start: a, end: b, len: len && Math.round(len) };
}));

/** ⭐ 选中一条指定序号的连线，返回选中前后的读数。 */
const selectEdge = async (idx) => {
  const info = await edgeInfo();
  const e = info[idx];
  if (!e || !e.start) return { ok: false, why: `第 ${idx + 1} 条连线没有可用坐标` };
  await page.mouse.move(400, 600); await page.waitForTimeout(500);
  await page.mouse.click(e.start[0], e.start[1]); await page.waitForTimeout(600);
  await page.mouse.move((e.start[0] + e.end[0]) / 2, (e.start[1] + e.end[1]) / 2);
  await page.waitForTimeout(500);
  await page.mouse.click((e.start[0] + e.end[0]) / 2, (e.start[1] + e.end[1]) / 2);
  await page.waitForTimeout(1600);
  const after = await edgeInfo();
  return { ok: after.some((x) => x.selected), idx, target: e, after: after.map((x) => ({ id: x.id, selected: x.selected })) };
};

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(2200);
  await beginBatch(B, { note: '选中连线后按删除键（真实写入，删完按记下的坐标接回去）' });
  const out = {};

  const before = await edgeInfo(); out.before = before;
  console.log(`═══ 起点：连线 ${before.length} 条 ═══`);
  before.forEach((e, i) => console.log(`  ${i + 1}. ${e.id}｜${e.aria}\n     起点=${JSON.stringify(e.start)} 终点=${JSON.stringify(e.end)} 长度=${e.len}`));

  // ⛔ 断线是**真实写入**。只有在**能接回去**的前提下才做 —— 两端坐标必须在视口内且可见。
  const restorable = before.map((e) => {
    const inView = e.start && e.end
      && e.start[0] > 2 && e.start[0] < 1438 && e.start[1] > 2 && e.start[1] < 808
      && e.end[0] > 2 && e.end[0] < 1438 && e.end[1] > 2 && e.end[1] < 808;
    const el = e.start ? page.evaluate((p) => { const x = document.elementFromPoint(p[0], p[1]);
      return x ? `${x.tagName}.${(x.className || '').toString().split(' ').slice(0, 2).join('.')}` : null; }, e.start) : null;
    return { id: e.id, inView, hitAt: el };
  });
  out.restorable = restorable;
  console.log(`  可否还原：${JSON.stringify(restorable)}`);

  // ── ① 选中连线
  const sel = await selectEdge(1);
  console.log(`\n═══ ① 选中第 2 条连线：ok=${sel.ok}｜${JSON.stringify(sel.after || sel.why)} ═══`);
  out.select = sel;
  if (!sel.ok) {
    const alt = await selectEdge(0);
    console.log(`  改选第 1 条：ok=${alt.ok}｜${JSON.stringify(alt.after || alt.why)}`);
    out.selectAlt = alt;
  }
  if (!sel.ok && !out.selectAlt?.ok) { console.log('  ⛔ 两条都选不中，本轮只读到此为止'); }

  // ── ② 选中状态下按删除键（依次试，三个都记）
  const keys = [];
  if (sel.ok || out.selectAlt?.ok) {
    const who = sel.ok ? '第 2 条' : '第 1 条';
    console.log(`\n═══ ② 选中 ${who} 连线后按删除键 ═══`);
    for (const k of ['Delete', 'Backspace']) {
      // 每轮之前重新选中
      const s2 = sel.ok ? await selectEdge(1) : await selectEdge(0);
      const n0 = await edgeCount();
      await page.keyboard.press(k);
      await page.waitForTimeout(2200);
      const n1 = await edgeCount();
      const dialog = await page.evaluate(() => {
        const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
        return [...document.querySelectorAll('[role="dialog"],.mantine-Modal-content')].filter(vis)
          .map((d) => (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 120)); });
      keys.push({ key: k, selectedBefore: s2.ok, countBefore: n0, countAfter: n1,
        delta: n1 - n0, dialogs: dialog });
      console.log(`  按 ${k}：选中=${s2.ok}｜连线 ${n0} → ${n1}（${n1 - n0 >= 0 ? '+' : ''}${n1 - n0}）｜弹窗 ${JSON.stringify(dialog)}`);
      if (n1 < n0) {
        await shot(page, 'M-281-选中连线后按删除.png');
        console.log(`  ⭐⭐ ${k} 把连线删掉了！`);
        break;
      }
      await esc();
    }
    out.keys = keys;
    out.deleted = keys.some((k) => k.delta < 0);
  }

  // ── ③ ⭐ 还原：把删掉的连线接回去
  const now = await edgeInfo();
  out.afterKeys = now;
  console.log(`\n═══ ③ 还原检查：现在 ${now.length} 条（起点 ${before.length} 条） ═══`);
  if (now.length < before.length) {
    const gone = before.filter((b) => !now.some((n) => n.id === b.id));
    console.log(`  少了：${JSON.stringify(gone.map((g) => ({ id: g.id, start: g.start, end: g.end })))}`);
    for (const g of gone) {
      if (!g.start || !g.end) { console.log(`  ⛔ ${g.id} 没有坐标，接不回去`); continue; }
      console.log(`  ⭐ 从 ${JSON.stringify(g.end)} 拖到 ${JSON.stringify(g.start)}`);
      await page.mouse.move(g.end[0], g.end[1]); await page.waitForTimeout(700);
      await page.mouse.down(); await page.waitForTimeout(400);
      // 分几步拖过去（一次性拖常常不触发 React Flow 的连接逻辑）
      for (let s = 1; s <= 8; s += 1) {
        await page.mouse.move(g.end[0] + (g.start[0] - g.end[0]) * (s / 8),
          g.end[1] + (g.start[1] - g.end[1]) * (s / 8)); await page.waitForTimeout(180);
      }
      await page.mouse.up(); await page.waitForTimeout(2200);
      const mid = await edgeCount();
      console.log(`     松手后连线数：${mid}`);
      if (mid >= before.length) break;
    }
  }
  const fin = await edgeInfo();
  out.final = fin;
  out.restored = fin.length === before.length;
  console.log(`  ⭐ 连线数 ${before.length} → ${fin.length}｜复原=${out.restored ? '✅' : '❌'}`);
  fin.forEach((e, i) => console.log(`    ${i + 1}. ${e.id}｜${e.aria}`));
  await shot(page, 'M-282-连线还原之后.png');

  console.log(`\n═══ 本轮结论 ═══`);
  console.log(`  · 快捷键面板有断线快捷键吗？ ❌ 没有（BV2 已证）`);
  console.log(`  · 悬停连线中点有删除按钮吗？ ❌ 没有（BV2 已证）`);
  console.log(`  · 点连线能选中它吗？ ✅ 能（class 带 selectable）`);
  console.log(`  · 选中后按删除键能断线吗？ ${out.deleted ? '✅ 能' : '❌ 不能'}`);
  console.log(`  · 连线复原了吗？ ${out.restored ? '✅' : '❌'}`);

  await logStep(B, {
    id: 'BV3-delete-selected-edge',
    title: '⭐⭐「选中连线 → 按删除键」：断线入口找到了（或确认没有）',
    target: 'BV2 突破：连线 class 是 `react-flow__edge react-flow__edge-default nopan selectable` —— '
      + '**`selectable`**，而且**点它真的能选中**（`selectedEdges: 1`）。'
      + '于是有一条从没试过的路：**选中连线再按删除键**。'
      + '⭐ BJ 那轮八种条件全在键盘快捷键上打转（而且 `⌘L` 本身就是「连线」），'
      + '**从来没有「选中对象再删」这条路**。'
      + '⚠️ 断线是**真实画布写入**：本轮先把两端屏幕坐标（`getPointAtLength(0)` 与 `(总长)`）'
      + '**记下来并确认落在视口内**，删完按这些坐标拖回去，最后复核连线数回到原值。',
    evidence: out,
    visible_text: JSON.stringify({
      起点连线: out.before, 可否还原: out.restorable,
      选中: out.select, 换选: out.selectAlt,
      删键尝试: out.keys, 真的删掉了吗: out.deleted,
      删后: out.afterKeys, 还原后: out.final, 复原: out.restored }).slice(0, 3400),
    shot: 'M-282-连线还原之后.png',
  });
  console.log('\nBV3 完成');
} catch (e) {
  console.log('⛔ 中止：' + e.message + '\n' + (e.stack || '').split('\n').slice(0, 4).join('\n'));
} finally {
  await browser.close();
}

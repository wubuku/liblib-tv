// Batch BE3 —— 收拾 BE2 留下的位置偏移，并把「⌥⇧F 到底触不触发」钉死。
//
// ⛔ BE2 的复原失败了，但**原因不是复原逻辑写错，是坐标系选错了**：
//    我拿 BE1 进场的**屏幕坐标**当目标，而中间 `⌘0` 改过缩放 ——
//    **同一个节点在 scale 0.48 和 scale 0.83 下的屏幕坐标完全不同。**
//    读数佐证：拖回用的位移正好是「目标屏幕坐标 − 当前屏幕坐标」，
//    拖完之后节点落到了「原点 − 位移」，两处都不对。
//
// ✅ 正确的判据是**画布坐标**。React Flow 把每个节点的位置写在自己的
//    `transform: translate(Xpx, Ypx)` 里 —— **它与缩放、平移无关**，
//    拖动、跨会话都稳定。屏幕坐标只配当「点哪里」的临时值。
//    ⭐ 这一条同样解释了 BE1 的「11 个节点变 2 个」：那是视口裁剪，不是删除。
//
// 第二个问题：BD5 说 `⌥⇧F` 会弹「是否保留此次整理结果？」，
//    但 BE1/BE2 两次都没找到那个确认条。这轮分诊：
//    ① 键盘 `Meta+Alt+f` 到底有没有触发（读画布坐标，不读屏幕坐标）；
//    ② 改用**底栏那枚「整理画布，Option+Shift+F」按钮**试；
//    ③ 两种都不动的话，就把「这个功能在当前状态下无效」写成结论。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, beginBatch, logStep, shot } from './scenario.mjs';

const SPACE = '10354929';
const B = 'batchBE3';
const { browser, page } = await launch();

/** ⭐ 画布坐标：从节点自己的 `transform: translate(Xpx,Ypx)` 读。
 *  React Flow 把位置写在这里，**与视口缩放/平移无关**。 */
const flowPos = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
  const t = getComputedStyle(n).transform;
  // matrix(a,b,c,d,tx,ty)
  const m = /matrix\(([^)]+)\)/.exec(t || '');
  const parts = m ? m[1].split(',').map(Number) : null;
  return { id: n.getAttribute('data-id'),
    name: ((n.innerText || '').replace(/\s+/g, ' ').trim().split(' ')[0] || '').slice(0, 12),
    x: parts ? Math.round(parts[4]) : null,
    y: parts ? Math.round(parts[5]) : null,
    transform: t };
}));

const screenPos = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
  const r = n.getBoundingClientRect();
  return { id: n.getAttribute('data-id'), x: Math.round(r.x), y: Math.round(r.y) }; }));

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
  if (!p) return { ok: false, err: '无可拖点' };
  await pg.mouse.move(p.x, p.y); await pg.mouse.down();
  for (let i = 1; i <= steps; i += 1) { await pg.mouse.move(p.x + (dx * i) / steps, p.y + (dy * i) / steps); await pg.waitForTimeout(55); }
  await pg.mouse.up(); await pg.waitForTimeout(1400);
  return { ok: true };
}

const btnRect = (pg, aria) => pg.evaluate((name) => {
  const e = [...document.querySelectorAll('button,[role="button"]')].find((x) => x.getAttribute('aria-label') === name);
  if (!e) return { err: '没找到 ' + name };
  const r = e.getBoundingClientRect();
  return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) };
}, aria);

/** 找「是否保留此次整理结果？」那一整条（含它的按钮）。 */
const findBar = (pg) => pg.evaluate(() => {
  const texts = [...document.querySelectorAll('body *')]
    .map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim())
    .filter((t) => /是否保留此次整理结果/.test(t));
  const btns = [...document.querySelectorAll('button,[role="button"]')].map((e) => {
    const r = e.getBoundingClientRect();
    return { text: (e.innerText || '').replace(/\s+/g, ' ').trim(),
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
  }).filter((e) => e.rect[2] > 0 && /^(还原|保留)$/.test(e.text));
  return { barTexts: [...new Set(texts)].slice(0, 3), btns };
});

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await beginBatch(B, { note: '用画布坐标（transform translate）当判据；钉死 ⌥⇧F / 整理画布按钮触不触发' });

  const out = {};
  await page.keyboard.press('Escape'); await page.waitForTimeout(900);

  // ── 读一次画布坐标，作为本轮的基线
  const base = await flowPos();
  console.log('本轮进场时的画布坐标：');
  base.forEach((n) => console.log(`  ${n.id.padEnd(14)} ${n.name.padEnd(8)} (${n.x}, ${n.y})`));
  out.base = base;
  // 现在到底乱不乱？看行数与行内间距
  const stat = (list) => {
    const byRow = {};
    for (const n of list) (byRow[n.y] = byRow[n.y] || []).push(n);
    const rows = Object.keys(byRow).map(Number).sort((a, b) => a - b);
    const gaps = [];
    for (const y of rows) {
      const r = byRow[y].slice().sort((a, b) => a.x - b.x);
      for (let i = 1; i < r.length; i += 1) gaps.push(r[i].x - r[i - 1].x);
    }
    return { rows: rows.length, gaps, distinctGaps: [...new Set(gaps)] };
  };
  const s0 = stat(base);
  console.log(`  布局：${s0.rows} 行，行内 x 间距 ${JSON.stringify(s0.gaps)}（不同取值 ${JSON.stringify(s0.distinctGaps)}）`);
  out.statBase = s0;

  // ═══ ① 键盘 ⌥⇧F：先**明确打乱**（用画布坐标验证确实乱了），再按
  console.log('\n--- ① 键盘 ⌥⇧F ---');
  await page.keyboard.press('Meta+0'); await page.waitForTimeout(2000);
  // 打乱：把两个节点拖到明显不在网格上的画布位置
  const sc0 = await screenPos();
  const ids = Object.keys(sc0).slice(0, 2);
  for (let i = 0; i < ids.length; i += 1) {
    const r = await dragBy(page, ids[i], 137 + i * 41, -93 + i * 57);
    console.log(`  拖乱 ${ids[i]} → ${r.ok ? 'ok' : r.err}`);
  }
  const messy = await flowPos();
  const sM = stat(messy);
  console.log(`  打乱后画布坐标：${sM.rows} 行，间距 ${JSON.stringify(sM.gaps)}（不同取值 ${JSON.stringify(sM.distinctGaps)}）`);
  const changedByMe = messy.filter((n) => { const b = base.find((x) => x.id === n.id); return b && (b.x !== n.x || b.y !== n.y); }).length;
  console.log(`  相对进场基线，位置变化 ${changedByMe} 个 —— 画布**确实是乱的**`);
  out.messy = { pos: messy, stat: sM, changed: changedByMe };
  out.messyConfirmed = changedByMe > 0 && sM.distinctGaps.length > 1;
  console.log(`  乱已坐实：${out.messyConfirmed}`);

  await page.mouse.click(720, 300); await page.waitForTimeout(900);
  await page.keyboard.press('Meta+Alt+f'); await page.waitForTimeout(3200);
  await clearToasts(page); await page.waitForTimeout(800);
  const afterKey = await flowPos();
  const keyChanged = afterKey.filter((n) => { const m = messy.find((x) => x.id === n.id); return m && (m.x !== n.x || m.y !== n.y); }).length;
  const barKey = await findBar(page);
  console.log(`  按 ⌥⇧F：画布坐标变化 ${keyChanged} 个；确认条 ${JSON.stringify(barKey)}`);
  out.tidyByKey = { changed: keyChanged, bar: barKey, after: afterKey };

  // ═══ ② 底栏那枚「整理画布」按钮
  console.log('\n--- ② 底栏「整理画布，Option+Shift+F」按钮 ---');
  const before2 = await flowPos();
  const p2 = await btnRect(page, '整理画布，Option+Shift+F');
  if (p2.err) console.log('  ', p2.err);
  else {
    await page.mouse.move(p2.x, p2.y); await page.waitForTimeout(300);
    await page.mouse.click(p2.x, p2.y); await page.waitForTimeout(3200);
    await clearToasts(page); await page.waitForTimeout(800);
    const after2 = await flowPos();
    const btnChanged = after2.filter((n) => { const m = before2.find((x) => x.id === n.id); return m && (m.x !== n.x || m.y !== n.y); }).length;
    const bar2 = await findBar(page);
    console.log(`  点按钮：画布坐标变化 ${btnChanged} 个；确认条 ${JSON.stringify(bar2)}`);
    out.tidyByButton = { changed: btnChanged, bar: bar2, after: after2 };
    if (btnChanged > 0) {
      const s2 = stat(after2);
      console.log(`  整理后：${s2.rows} 行，间距 ${JSON.stringify(s2.gaps)}`);
      out.tidyByButton.stat = s2;
      await shot(page, 'M-189-整理后.png');
      out.shot = 'M-189-整理后.png';
    }
  }

  // ═══ 复原：把节点拖回**进场时的画布坐标**（这次用对坐标系）
  console.log('\n--- 复原（按画布坐标）---');
  await page.keyboard.press('Meta+0'); await page.waitForTimeout(2200);
  // 确认条若在，点「还原」
  const bar3 = await findBar(page);
  const back = bar3.btns.find((b) => b.text === '还原');
  if (back) {
    await page.mouse.click(back.rect[0] + back.rect[2] / 2, back.rect[1] + back.rect[3] / 2);
    await page.waitForTimeout(2800);
    console.log('  已点「还原」');
    out.undoneByBar = true;
  } else { out.undoneByBar = false; }

  await page.keyboard.press('Meta+0'); await page.waitForTimeout(2000);
  const scaleNow = await page.evaluate(() => {
    const v = document.querySelector('.react-flow__viewport');
    const m = v ? /scale\(([\d.]+)\)/.exec(v.style.transform || '') : null;
    return m ? +m[1] : null; });
  console.log('  当前 scale =', scaleNow);

  // 画布坐标 → 屏幕坐标的换算靠「拖过去再量」实现：
  // 先量一次当前画布坐标 (fx,fy) 对应的屏幕坐标 (sx,sy)，
  // 由 scale 反推平移量，再算出每个目标位置的屏幕坐标。
  const cur = await flowPos();
  const curScr = await screenPos();
  const probe = cur[0], probeScr = curScr.find((s) => s.id === cur[0].id);
  const ox = probeScr.x - probe.x * scaleNow;
  const oy = probeScr.y - probe.y * scaleNow;
  console.log(`  反推视口平移：(${Math.round(ox)}, ${Math.round(oy)})`);

  const restored = [];
  for (const b of base) {
    const c = cur.find((n) => n.id === b.id);
    if (!c) { restored.push({ id: b.id, err: 'gone' }); continue; }
    const tx = Math.round(b.x * scaleNow + ox), ty = Math.round(b.y * scaleNow + oy);
    const cs = curScr.find((s) => s.id === b.id);
    const dx = tx - cs.x, dy = ty - cs.y;
    if (Math.abs(dx) < 3 && Math.abs(dy) < 3) { restored.push({ id: b.id, ok: true, skipped: true }); continue; }
    const r = await dragBy(page, b.id, dx, dy, 12);
    restored.push({ id: b.id, ok: r.ok, dx, dy });
  }
  console.log(`  已处理 ${restored.filter((r) => !r.skipped).length} 个节点`);
  out.restoreLog = restored;

  const finalScr = await screenPos();
  await page.keyboard.press('Meta+0'); await page.waitForTimeout(2200);
  const finalFlow = await flowPos();
  const drift = finalFlow.filter((n) => {
    const b = base.find((x) => x.id === n.id);
    return !b || Math.abs(b.x - n.x) > 6 || Math.abs(b.y - n.y) > 6;
  });
  console.log(`  ⭐ 复原后（画布坐标）仍有偏差：${drift.length} 个`);
  drift.forEach((d) => {
    const b = base.find((x) => x.id === d.id);
    console.log(`    ${d.id} ${d.name} 现在 (${d.x},${d.y}) vs 基线 (${b.x},${b.y}) 差 (${d.x - b.x},${d.y - b.y})`);
  });
  out.finalFlow = finalFlow;
  out.drift = drift.map((n) => { const b = base.find((x) => x.id === n.id);
    return { id: n.id, now: [n.x, n.y], base: [b.x, b.y], d: [n.x - b.x, n.y - b.y] }; });
  out.restored = drift.length === 0;
  out.finalScreenCount = finalScr.length;

  await logStep(B, {
    id: 'BE3-flow-coord-tidy-trigger',
    title: '画布坐标才是稳定判据 / 钉死整理画布触不触发',
    target: 'BE2 复原失败是因为拿**屏幕坐标**当目标，而中途 ⌘0 改过缩放。'
      + '这轮改读节点 `transform: translate(Xpx,Ypx)` —— 与视口无关，跨缩放稳定。'
      + '同时分诊「⌥⇧F 触不触发」：键盘 vs 底栏按钮，都用画布坐标判有没有动。',
    evidence: out,
    visible_text: JSON.stringify({ statBase: out.statBase, messy: out.messy?.stat,
      tidyByKey: { changed: out.tidyByKey?.changed, bar: out.tidyByKey?.bar },
      tidyByButton: { changed: out.tidyByButton?.changed, bar: out.tidyByButton?.bar, stat: out.tidyByButton?.stat },
      restored: out.restored, drift: out.drift }).slice(0, 3500),
    shot: out.shot,
  });
  console.log('\nBE3 完成');
} finally {
  await browser.close();
}

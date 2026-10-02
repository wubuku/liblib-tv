// Batch BL1 — 「展示设置」的「展开/收起全部分组」，这回**先造出组**再测。
//
// 为什么一直没测出效果：这两项要看出差别，前提是画布上**真的有组**，
// 而前几轮建组都没成功（见 create-nodes 的成组说明）。
// 在**没有组**的画布上点它们，列表纹丝不动 —— 那是**前提不成立**，
// 不是功能无效。两者必须分开。
//
// ⭐ 本轮的三条纪律（都是前几批吃过的亏）：
//  ① **先造出组并断言它真的存在**，再点那两个菜单项；
//  ② 读「组」要认**结构**（组容器的 class / DOM 层级），不认「Group 1」这种默认名；
//  ③ 每步带 `executed` 自证 —— 没执行就报未执行，不许报成「无反应」（BK2 的规矩）。
//
// ⚠️ 安全边界：
//   · 成组/解组是纯画布操作，**可逆**（⌘⇧G 解开），收尾必须恢复原状；
//   · **绝不执行 ⌘A + ⌫**（会删光节点）；
//   · 不碰任何生成按钮。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep, fingerprint, diffPanels } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBL1';
const { browser, page } = await launch();

/** ⭐ 组的真实存在判据：认容器结构，不认名字。 */
const groups = () => page.evaluate(() => {
  const cands = ['.react-flow__group', '[class*="react-flow__group"]', '.react-flow__node-group',
    '[data-nodeid][class*="group"]'];
  const found = new Set();
  for (const sel of cands) for (const e of document.querySelectorAll(sel)) {
    const r = e.getBoundingClientRect();
    found.add({ sel, cls: (typeof e.className === 'string' ? e.className : '').slice(0, 80),
      dataId: e.getAttribute('data-id'), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40) });
  }
  // 也顺带看看有没有「组」字样的可见元素，作为弱信号
  const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
  const named = [...document.querySelectorAll('body *')].filter((e) => !skip.has(e.tagName))
    .map((e) => { const r = e.getBoundingClientRect();
      return { t: (e.innerText || '').replace(/\s+/g, ' ').trim(), r }; })
    .filter((x) => x.r.width > 4 && x.r.height > 4 && /^(Group|分组|组)\s*\d*$/i.test(x.t))
    .map((x) => ({ t: x.t, rect: [Math.round(x.r.x), Math.round(x.r.y), Math.round(x.r.width), Math.round(x.r.height)] }));
  return { byClass: [...found], named: named.slice(0, 6) };
});

const nodes = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')]
  .map((n) => ({ id: n.getAttribute('data-id'),
    name: (n.innerText || '').replace(/\s+/g, ' ').trim().split(' ')[0] })));

/** 资产管理抽屉里「画布」标签的列表行结构。 */
const drawerRows = () => page.evaluate(() => {
  const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
  const rows = [...document.querySelectorAll('body *')].filter((e) => !skip.has(e.tagName))
    .map((e) => { const r = e.getBoundingClientRect();
      return { e, t: (e.innerText || '').replace(/\s+/g, ' ').trim(), r,
        kids: e.children.length }; })
    .filter((x) => x.r.width > 180 && x.r.width < 340 && x.r.height > 16 && x.r.height < 90
      && x.r.x < 360 && x.t.length > 1 && x.t.length < 60 && !/资产|搜索|全部|所有评级|展示设置|筛选/.test(x.t));
  // 去重：同一行只留最内层
  const inner = rows.filter((x) => ![...x.e.children].some((c) => {
    const cr = c.getBoundingClientRect();
    return cr.width > 0 && Math.abs(cr.y - x.r.y) < 8 && cr.width <= x.r.width;
  }));
  const seen = new Set(); const out = [];
  for (const x of inner) { const k = `${Math.round(x.r.y / 6)}`; if (!seen.has(k)) { seen.add(k);
    out.push({ t: x.t, y: Math.round(x.r.y), kids: x.kids,
      rect: [Math.round(x.r.x), Math.round(x.r.y), Math.round(x.r.width), Math.round(x.r.height)] }); } }
  return out.sort((a, b) => a.y - b.y);
});

const openDrawer = async () => {
  const d = await page.evaluate(() => {
    const e = [...document.querySelectorAll('button,[role="button"]')]
      .find((x) => x.getAttribute('aria-label') === '资产管理');
    if (!e) return null; const r = e.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
  });
  if (!d) return false;
  await page.mouse.click(d[0], d[1]); await page.waitForTimeout(2600);
  return true;
};

const openDisplay = async () => {
  const b = await page.evaluate(() => {
    const e = [...document.querySelectorAll('button,[role="button"]')]
      .find((x) => x.getAttribute('aria-label') === '展示设置');
    if (!e) return null; const r = e.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
  });
  if (!b) return null;
  await page.mouse.click(b[0], b[1]); await page.waitForTimeout(1800);
  const items = await page.evaluate(() => {
    const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
    const seen = new Set(); const out = [];
    for (const e of document.querySelectorAll('body *')) {
      if (skip.has(e.tagName)) continue;
      const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
      if (!/^(列表展示|宫格展示|展开全部分组|收起全部分组)$/.test(t)) continue;
      const r = e.getBoundingClientRect();
      if (r.width < 10) continue;
      const k = `${t}@${Math.round(r.y)}`; if (seen.has(k)) continue; seen.add(k);
      out.push({ t, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] });
    }
    return out;
  });
  return items;
};

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(2000);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '先 ⌘G 建组并断言组存在，再点展开/收起全部分组' });

  const out = {};

  // ═══ A. 建组前基线
  console.log('══════ A. 建组前 ══════');
  const g0 = await groups();
  const n0 = await nodes();
  console.log(`  节点 ${n0.length} 个；组容器 ${g0.byClass.length} 个；「Group/组」命名元素 ${g0.named.length} 个`);
  g0.named.forEach((x) => console.log(`     "${x.t}" ${JSON.stringify(x.rect)}`));
  if (await openDrawer()) {
    const r0 = await drawerRows();
    console.log(`  抽屉列表行 ${r0.length} 行：${JSON.stringify(r0.map((r) => r.t))}`);
    out.rowsBefore = r0;
  }
  await page.keyboard.press('Escape'); await page.waitForTimeout(1400);
  out.before = { nodes: n0.length, groups: g0, rows: out.rowsBefore?.length };

  // ═══ B. 框选两个节点 → ⌘G
  console.log('\n══════ B. 框选两个节点按 ⌘G ══════');
  // 选相邻的两个：先找两个 rect 相邻的节点
  const pair = await page.evaluate(() => {
    const ns = [...document.querySelectorAll('.react-flow__node')].map((n) => {
      const r = n.getBoundingClientRect();
      return { id: n.getAttribute('data-id'), r, y: r.y, x: r.x, h: r.height, w: r.width };
    }).filter((n) => n.r.width > 40 && n.r.height > 40);
    if (ns.length < 2) return { err: 'less than 2' };
    ns.sort((a, b) => a.y - b.y || a.x - b.x);
    let best = null, bestD = 1e9;
    for (let i = 0; i < ns.length; i++) for (let j = i + 1; j < ns.length; j++) {
      const a = ns[i], b = ns[j];
      const dx = Math.abs(a.x - b.x), dy = Math.abs(a.y - b.y);
      const d = Math.max(dx, dy);
      if (dx < 60 && dy < 60 && d < bestD) { bestD = d; best = [a, b]; }
    }
    if (!best) { const a = ns[0], b = ns[1];
      return { a: { id: a.id, r: [a.r.x, a.r.y, a.r.width, a.r.height] },
        b: { id: b.id, r: [b.r.x, b.r.y, b.r.width, b.r.height] }, note: '取前两个' }; }
    return { a: { id: best[0].id, r: [best[0].r.x, best[0].r.y, best[0].r.width, best[0].r.height] },
      b: { id: best[1].id, r: [best[1].r.x, best[1].r.y, best[1].r.width, best[1].r.height] } };
  });
  console.log('  选中的两个：', JSON.stringify(pair));
  if (pair.err) { console.log('  ⛔ ' + pair.err); }
  else {
    // 用 Shift+点选（比框选稳），两枚
    const ptA = await page.evaluate((id) => {
      const n = [...document.querySelectorAll('.react-flow__node')].find((x) => x.getAttribute('data-id') === id);
      const r = n.getBoundingClientRect();
      for (let fy = 0.2; fy <= 0.8; fy += 0.12) for (let fx = 0.1; fx <= 0.9; fx += 0.08) {
        const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fx);
        const o = document.elementFromPoint(x, y);
        if (o && o.closest('.react-flow__node') === n) return [x, y];
      } return null;
    }, pair.a.id);
    const ptB = await page.evaluate((id) => {
      const n = [...document.querySelectorAll('.react-flow__node')].find((x) => x.getAttribute('data-id') === id);
      const r = n.getBoundingClientRect();
      for (let fy = 0.2; fy <= 0.8; fy += 0.12) for (let fx = 0.1; fx <= 0.9; fx += 0.08) {
        const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fx);
        const o = document.elementFromPoint(x, y);
        if (o && o.closest('.react-flow__node') === n) return [x, y];
      } return null;
    }, pair.b.id);
    await page.mouse.click(ptA[0], ptA[1]); await page.waitForTimeout(2000);
    await page.keyboard.down('Shift'); await page.mouse.click(ptB[0], ptB[1]); await page.keyboard.up('Shift');
    await page.waitForTimeout(2200);
    const selN = await page.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
    console.log(`  选中数 = ${selN} ${selN === 2 ? '✅' : '⚠️'}`);

    await page.keyboard.down('Meta'); await page.keyboard.press('g'); await page.keyboard.up('Meta');
    await page.waitForTimeout(2800);
    const g1 = await groups();
    console.log(`  ⌘G 后：组容器 ${g1.byClass.length} 个；「Group/组」命名元素 ${g1.named.length} 个`);
    g1.byClass.forEach((x) => console.log(`     ${x.sel} cls="${x.cls}" rect=${JSON.stringify(x.rect)} text="${x.text}"`));
    g1.named.forEach((x) => console.log(`     命名："${x.t}" ${JSON.stringify(x.rect)}`));
    await shot(page, 'M-211-建组后.png');
    out.shotGroup = 'M-211-建组后.png';
    out.afterGroup = { selected: selN, groups: g1, pair };
    console.log(`  ⭐ 组建成了吗？ ${g1.byClass.length > 0 || g1.named.length > 0 ? '✅ 是' : '❌ 仍然没有组'}`);
  }

  // ═══ C. 有组之后：展开 / 收起全部分组
  console.log('\n══════ C. 展开 / 收起全部分组 ══════');
  await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  const hasGroup = (await groups()).byClass.length > 0;
  if (!await openDrawer()) console.log('  ⛔ 抽屉开不了');
  else {
    const items = await openDisplay();
    console.log('  菜单项：', JSON.stringify(items));
    out.menuItems = items;
    if (!items) { console.log('  ⛔ 「展示设置」菜单没打开'); }
    else {
      for (const want of ['展开全部分组', '收起全部分组']) {
        const it = items.find((i) => i.t === want);
        if (!it) { console.log(`  ⚠️ 菜单里没有「${want}」`); continue; }
        const cx = Math.round(it.rect[0] + it.rect[2] / 2), cy = Math.round(it.rect[1] + it.rect[3] / 2);
        const own = await page.evaluate(([x, y]) => {
          const o = document.elementFromPoint(x, y);
          return { tag: o ? o.tagName : null, t: o ? (o.innerText || '').replace(/\s+/g, ' ').trim() : null };
        }, [cx, cy]);
        const executed = own.t === want;
        const before = await drawerRows();
        await page.mouse.click(cx, cy);
        await page.waitForTimeout(2600);
        await page.mouse.move(700, 300); await page.waitForTimeout(1500);
        const after = await drawerRows();
        console.log(`  ── 点「${want}」：落点 "${own.t}" ${executed ? '✅' : '⚠️ 未执行'}`);
        console.log(`     列表行 ${before.length} → ${after.length}`);
        console.log(`     前：${JSON.stringify(before.map((r) => r.t))}`);
        console.log(`     后：${JSON.stringify(after.map((r) => r.t))}`);
        out[want] = { executed, before: before.map((r) => r.t), after: after.map((r) => r.t),
          beforeN: before.length, afterN: after.length };
        await shot(page, want === '展开全部分组' ? 'M-212-展开全部分组.png' : 'M-213-收起全部分组.png');
        out.shot = out.shot || [];
        out.shot.push(want === '展开全部分组' ? 'M-212-展开全部分组.png' : 'M-213-收起全部分组.png');
        // 每点完一次都要重新打开菜单
        if (want === '展开全部分组') { const again = await openDisplay(); if (!again) console.log('     ⚠️ 菜单没重新打开'); }
      }
    }
  }

  // ═══ D. 收尾：解组复原
  console.log('\n══════ D. 收尾：解组复原 ══════');
  await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  if (hasGroup) {
    // 组选中后按 ⌘⇧G 解组
    const gp = await page.evaluate(() => {
      const g = document.querySelector('.react-flow__group') ||
        [...document.querySelectorAll('[class*="react-flow__group"]')][0];
      if (!g) return { err: 'no group el' };
      const r = g.getBoundingClientRect();
      return { x: Math.round(r.x + 8), y: Math.round(r.y + 8) };
    });
    console.log('  组位置：', JSON.stringify(gp));
    await page.mouse.click(120, 780); await page.waitForTimeout(1000);
    if (gp.x) {
      await page.mouse.click(gp.x, gp.y); await page.waitForTimeout(2200);
      const selG = await page.evaluate(() => document.querySelectorAll('.react-flow__node.selected, .react-flow__group.selected').length);
      console.log(`  点组之后选中数 = ${selG}`);
      await page.keyboard.down('Meta'); await page.keyboard.down('Shift');
      await page.keyboard.press('g');
      await page.keyboard.up('Shift'); await page.keyboard.up('Meta');
      await page.waitForTimeout(2600);
    }
  }
  const gEnd = await groups();
  const nEnd = await nodes();
  console.log(`  收尾：节点 ${nEnd.length} 个；组容器 ${gEnd.byClass.length} 个`);
  console.log(`  ⭐ 复原？ ${gEnd.byClass.length === 0 ? '✅ 组已解开' : '⚠️ 组还在'}`);
  await shot(page, 'M-214-解组复原.png');
  out.restore = { groups: gEnd.byClass.length, nodes: nEnd.length, shot: 'M-214-解组复原.png' };
  out.hasGroup = hasGroup;

  await logStep(B, {
    id: 'BL1-expand-collapse-groups',
    title: '有组之后，展开/收起全部分组到底有没有效果',
    target: '这两项一直「没测出效果」，原因是**前提不成立** —— 前几轮建组失败，'
      + '在没有组的画布上点它们当然纹丝不动。⭐ 本轮先 ⌘G 建组并**断言组真的存在**（认结构不认名字），'
      + '再点这两项。⚠️ 建组可逆，收尾 ⌘⇧G 解开；绝不执行 ⌘A+⌫。',
    evidence: out,
    visible_text: JSON.stringify({ 建组前: out.before, 建组后: out.afterGroup?.groups,
      菜单项: out.menuItems?.map?.((i) => i.t),
      展开: { 执行: out['展开全部分组']?.executed, 前: out['展开全部分组']?.beforeN, 后: out['展开全部分组']?.afterN },
      收起: { 执行: out['收起全部分组']?.executed, 前: out['收起全部分组']?.beforeN, 后: out['收起全部分组']?.afterN },
      复原: out.restore }).slice(0, 3000),
    shot: out.shotGroup,
  });
  console.log('\nBL1 完成');
} finally {
  await browser.close();
}

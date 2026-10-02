// Batch BM1 — 组行左侧的箭头：能不能**只展开这一个组**。
//
// BL2 拍到了组行左侧箭头的两种形态（展开 `⌄` / 收起 `›`），
// 但**没点过它**，所以手册里只能写「📖 没验」。
// 画布上**同时存在两个组**才有意义 —— 只建一个组的话，
// 「只展开一个」和「展开全部」看起来一模一样，**判据不成立**（§40.3 的教训）。
//
// ⭐ 本轮的设计：
//   · 建**两个**互不相干的组（各 2 个成员，且四个成员各不相同）；
//   · 断言两个组都真的出现（`.react-flow__node-group` 数量 == 2）；
//   · 然后才有资格测「点某一行的箭头」到底影响的是**一个**还是**全部**。
//   · 先用「收起全部分组」把两个组都收成收起态（造出「有差别」的初始状态），
//     再点其中一个组的箭头 —— 若只有它展开，就是**单组开关**；
//     若两个都展开，那它其实是「展开全部」的另一个入口。
//
// ⚠️ 收尾：⌘⇧G 解开两个组，核对回到「无组 / 11 节点」，刷新再确认一次。
//    绝不执行 ⌘A + ⌫。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBM1';
const { browser, page } = await launch();

const groups = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node-group')].map((g) => {
  const r = g.getBoundingClientRect();
  return { id: g.getAttribute('data-id'), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    name: (g.innerText || '').replace(/\s+/g, ' ').trim().match(/Group\s*\d+/)?.[0] || (g.innerText || '').trim().slice(0, 20) };
}));

const nodeCount = () => page.evaluate(() => document.querySelectorAll('.react-flow__node').length);

/** 抽屉列表：返回「有哪些组名行、每个组名行下面跟着哪些成员名」。 */
const drawerState = () => page.evaluate(() => {
  const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
  // 找抽屉容器：x < 360 且宽 > 250
  const panel = [...document.querySelectorAll('div')].filter((e) => {
    const r = e.getBoundingClientRect();
    return r.x < 40 && r.width > 250 && r.width < 360 && r.height > 400;
  }).sort((a, b) => b.getBoundingClientRect().height - a.getBoundingClientRect().height)[0];
  if (!panel) return { err: 'no drawer' };
  // 逐行读：取宽度占满且高度 20~60 的最内层元素
  const rows = [...panel.querySelectorAll('*')].filter((e) => !skip.has(e.tagName))
    .map((e) => { const r = e.getBoundingClientRect();
      return { e, t: (e.innerText || '').replace(/\s+/g, ' ').trim(), r,
        leaves: [...e.children].filter((c) => { const cr = c.getBoundingClientRect(); return cr.width > 0; }).length }; })
    .filter((x) => x.r.width > 120 && x.r.height >= 18 && x.r.height <= 60 && x.t.length > 1 && x.t.length < 40)
    .filter((x) => !/资产|搜索|全部|所有评级|展示设置|筛选|共\s*\d+/.test(x.t))
    .filter((x) => x.leaves === 0 || ![...x.e.children].some((c) => {
      const cr = c.getBoundingClientRect();
      return cr.height > 0 && Math.abs(cr.y - x.r.y) < 6 && cr.width <= x.r.width;
    }));
  const seen = new Set(); const out = [];
  for (const x of rows) { const k = `${Math.round(x.r.y / 4)}`; if (seen.has(k)) continue; seen.add(k);
    out.push({ t: x.t, y: Math.round(x.r.y), x: Math.round(x.r.x), w: Math.round(x.r.width) }); }
  out.sort((a, b) => a.y - b.y);
  // ⭐ 找每个组名行左侧那个箭头（一个独立的小元素）
  const arrows = [...panel.querySelectorAll('*')].filter((e) => !skip.has(e.tagName))
    .map((e) => { const r = e.getBoundingClientRect();
      return { t: (e.innerText || '').trim(), r,
        cls: (typeof e.className === 'string' ? e.className : '').slice(0, 50) }; })
    .filter((x) => x.r.width >= 8 && x.r.width <= 26 && x.r.height >= 8 && x.r.height <= 26
      && x.r.x < 70 && /^[›⌄>v√▾▸]$/.test(x.t))
    .map((x) => ({ t: x.t, cls: x.cls, rect: [Math.round(x.r.x), Math.round(x.r.y), Math.round(x.r.width), Math.round(x.r.height)],
      cx: Math.round(x.r.x + x.r.width / 2), cy: Math.round(x.r.y + x.r.height / 2) }));
  return { rows: out.map((r) => r.t), rowsY: out.map((r) => r.y), arrows };
});

const openDrawer = async () => {
  const d = await page.evaluate(() => {
    const e = [...document.querySelectorAll('button,[role="button"]')].find((x) => x.getAttribute('aria-label') === '资产管理');
    if (!e) return null; const r = e.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  if (!d) return false;
  await page.mouse.click(d[0], d[1]); await page.waitForTimeout(2600); return true;
};

const openDisplay = async () => {
  const b = await page.evaluate(() => {
    const e = [...document.querySelectorAll('button,[role="button"]')].find((x) => x.getAttribute('aria-label') === '展示设置');
    if (!e) return null; const r = e.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  if (!b) return null;
  await page.mouse.click(b[0], b[1]); await page.waitForTimeout(1800);
  return page.evaluate(() => {
    const seen = new Set(); const out = [];
    for (const e of document.querySelectorAll('div,button,span')) {
      const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
      if (!/^(展开全部分组|收起全部分组)$/.test(t)) continue;
      const r = e.getBoundingClientRect();
      if (r.width < 120) continue;
      const k = `${t}@${Math.round(r.y)}`; if (seen.has(k)) continue; seen.add(k);
      out.push({ t, cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) });
    } return out; });
};

async function clickDisplay(want) {
  const items = await openDisplay();
  const it = items && items.find((i) => i.t === want);
  if (!it) return { executed: false, note: '菜单里没有这一项' };
  const own = await page.evaluate(([x, y]) => {
    const o = document.elementFromPoint(x, y);
    return { tag: o ? o.tagName : null, t: o ? (o.innerText || '').replace(/\s+/g, ' ').trim() : null }; }, [it.cx, it.cy]);
  if (own.t !== want) return { executed: false, note: `落点是「${own.t}」` };
  await page.mouse.click(it.cx, it.cy); await page.waitForTimeout(2600);
  await page.mouse.move(700, 300); await page.waitForTimeout(1400);
  return { executed: true, own };
}

async function selectTwo(ids) {
  const pts = [];
  for (const id of ids) {
    const p = await page.evaluate((nid) => {
      const n = [...document.querySelectorAll('.react-flow__node')].find((x) => x.getAttribute('data-id') === nid);
      if (!n) return null;
      const r = n.getBoundingClientRect();
      if (r.width < 10) return null;
      for (let fy = 0.2; fy <= 0.8; fy += 0.12) for (let fx = 0.1; fx <= 0.9; fx += 0.08) {
        const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fx);
        const o = document.elementFromPoint(x, y);
        if (o && o.closest('.react-flow__node') === n) return [x, y];
      } return null; }, id);
    if (p) pts.push(p);
  }
  if (pts.length < 2) return { ok: false, why: `只取到 ${pts.length} 个点` };
  await page.mouse.click(pts[0][0], pts[0][1]); await page.waitForTimeout(1800);
  await page.keyboard.down('Shift'); await page.mouse.click(pts[1][0], pts[1][1]); await page.keyboard.up('Shift');
  await page.waitForTimeout(2000);
  const n = await page.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
  if (n !== 2) return { ok: false, why: `选中数 ${n} ≠ 2` };
  await page.keyboard.down('Meta'); await page.keyboard.press('g'); await page.keyboard.up('Meta');
  await page.waitForTimeout(2600);
  return { ok: true };
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(2000);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '建两个组，测组行箭头是单组开关还是展开全部' });

  const out = {};
  console.log('══════ A. 基线 ══════');
  const g0 = await groups();
  console.log(`  组 ${g0.length} 个；节点 ${await nodeCount()} 个`);
  out.base = { groups: g0.length, nodes: await nodeCount() };
  if (g0.length !== 0) { console.log('  ⚠️ 进场就带组，先解开'); }

  // ═══ B. 建两个组
  console.log('\n══════ B. 建两个组 ══════');
  const all = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node')]
    .map((n) => { const r = n.getBoundingClientRect();
      return { id: n.getAttribute('data-id'), x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width) }; })
    .filter((n) => n.w > 40));
  all.sort((a, b) => a.y - b.y || a.x - b.x);
  console.log(`  视口内节点 ${all.length} 个：${JSON.stringify(all.map((n) => n.id))}`);
  // 取两对：第 0,1 个一组；第 2,3 个一组
  const pairA = [all[0]?.id, all[1]?.id], pairB = [all[2]?.id, all[3]?.id];
  console.log(`  组 A = ${JSON.stringify(pairA)}；组 B = ${JSON.stringify(pairB)}`);
  const rA = await selectTwo(pairA);
  console.log(`  建组 A：${rA.ok ? '✅' : '✗ ' + rA.why}`);
  const rB = await selectTwo(pairB);
  console.log(`  建组 B：${rB.ok ? '✅' : '✗ ' + rB.why}`);
  const g1 = await groups();
  console.log(`  ⭐ 组 ${g1.length} 个：${JSON.stringify(g1.map((g) => g.name))}`);
  console.log(`  ${g1.length === 2 ? '✅ 两个组都在，判据成立' : '⚠️ 组数不足，「单组 vs 全部」分不开'}`);
  out.afterGroup = { a: rA, b: rB, groups: g1 };

  if (g1.length < 2) {
    console.log('\n  ⛔ 组数不足，本轮结论不成立，跳过箭头测试');
  } else {
    // ═══ C. 先把两个组都收成收起态（造出有差别的初始状态）
    console.log('\n══════ C. 造初始态：两个组都收起 ══════');
    await openDrawer();
    const s0 = await drawerState();
    console.log(`  起始（默认展开）：${JSON.stringify(s0.rows)}`);
    console.log(`  箭头：${JSON.stringify(s0.arrows)}`);
    const rc = await clickDisplay('收起全部分组');
    const s1 = await drawerState();
    console.log(`  收起后（执行=${rc.executed} ${rc.note || ''}）：${JSON.stringify(s1.rows)}`);
    console.log(`  箭头：${JSON.stringify(s1.arrows)}`);
    await shot(page, 'M-216-两组都收起.png');
    out.collapsed = { executed: rc.executed, rows: s1.rows, arrows: s1.arrows };
    out.startRows = s0.rows;

    // ═══ D. 点**其中一个**组的箭头
    console.log('\n══════ D. 点其中一个组的箭头 ══════');
    const ar = s1.arrows[0];
    if (!ar) { console.log('  ⛔ 没找到箭头元素'); out.arrow = { err: 'no arrow' }; }
    else {
      const own = await page.evaluate(([x, y]) => {
        const o = document.elementFromPoint(x, y);
        return { tag: o ? o.tagName : null, t: o ? (o.innerText || '').trim() : null,
          cls: o ? (typeof o.className === 'string' ? o.className : '').slice(0, 50) : null }; }, [ar.cx, ar.cy]);
      console.log(`  箭头落点归属：${JSON.stringify(own)}`);
      console.log(`  点 (${ar.cx},${ar.cy})`);
      await page.mouse.click(ar.cx, ar.cy);
      await page.waitForTimeout(2600);
      await page.mouse.move(700, 300); await page.waitForTimeout(1400);
      const s2 = await drawerState();
      console.log(`  点完列表：${JSON.stringify(s2.rows)}`);
      console.log(`  箭头：${JSON.stringify(s2.arrows)}`);
      await shot(page, 'M-217-点第一个组的箭头后.png');

      // ⭐ 判定：数一数「有成员跟在后面的组」有几个
      const membersOf = (rows) => {
        const outMap = [];
        for (let i = 0; i < rows.length; i++) {
          if (/^Group\s*\d+$/.test(rows[i])) {
            const members = [];
            for (let j = i + 1; j < rows.length && !/^Group\s*\d+$/.test(rows[j]); j++) members.push(rows[j]);
            outMap.push({ group: rows[i], members });
          }
        }
        return outMap;
      };
      const before = membersOf(s1.rows), after = membersOf(s2.rows);
      console.log(`\n  ⭐ 展开态分组：`);
      before.forEach((b) => console.log(`     ${b.group} → 成员 ${JSON.stringify(b.members)}`));
      console.log(`  ⭐ 点完一个箭头之后：`);
      after.forEach((b) => console.log(`     ${b.group} → 成员 ${JSON.stringify(b.members)}`));
      const changed = JSON.stringify(before) !== JSON.stringify(after);
      const onlyOne = after.filter((g) => g.members.length > 0).length === 1
        && after.filter((g) => g.members.length === 0).length >= 1;
      const allOpen = after.filter((g) => g.members.length > 0).length === after.length && after.length > 1;
      console.log(`  ⭐ 列表变了吗？ ${changed ? '是' : '否'}`);
      console.log(`  ⭐ 只有一个组被展开？ ${onlyOne ? '✅ **是 —— 它是单组开关**' : '否'}`);
      console.log(`  ⭐ 两个组都被展开？ ${allOpen ? '✅ 是 —— 它其实是「展开全部」' : '否'}`);
      out.arrow = { executed: true, own, before, after, changed, onlyOne, allOpen,
        shot: 'M-217-点第一个组的箭头后.png' };
    }
  }

  // ═══ E. 复原：解两个组
  console.log('\n══════ E. 复原 ══════');
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  let gNow = await groups();
  console.log(`  当前组 ${gNow.length} 个`);
  for (const g of gNow) {
    const p = await page.evaluate((gid) => {
      const el = document.querySelector(`.react-flow__node-group[data-id="${gid}"]`);
      if (!el) return null;
      const r = el.getBoundingClientRect();
      return [Math.round(r.x + r.width / 2), Math.round(r.y + 6)]; }, g.id);
    if (!p) { console.log(`  找不到组 ${g.id}`); continue; }
    await page.mouse.click(p[0], p[1]); await page.waitForTimeout(2200);
    const sel = await page.evaluate(() => document.querySelectorAll('.react-flow__node-group.selected').length);
    if (sel) {
      await page.keyboard.down('Meta'); await page.keyboard.down('Shift');
      await page.keyboard.press('g');
      await page.keyboard.up('Shift'); await page.keyboard.up('Meta');
      await page.waitForTimeout(2400);
      console.log(`  解开 ${g.name}（选中读数 ${sel}）→ 剩 ${(await groups()).length} 个`);
    } else console.log(`  点 ${g.name} 没选中（可能点到成员卡了）`);
  }
  gNow = await groups();
  const nEnd = await nodeCount();
  console.log(`  收尾：组 ${gNow.length} 个；节点 ${nEnd} 个`);
  out.restore = { groups: gNow.length, nodes: nEnd };

  await page.reload({ waitUntil: 'domcontentloaded' }); await page.waitForTimeout(6500);
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1800);
  await fitView(page); await page.waitForTimeout(1800);
  const gRe = await groups(); const nRe = await nodeCount();
  console.log(`  刷新后：组 ${gRe.length} 个；节点 ${nRe} 个`);
  out.afterReload = { groups: gRe.length, nodes: nRe };

  await logStep(B, {
    id: 'BM1-group-row-arrow',
    title: '组行左侧箭头：单组开关，还是「展开全部」的另一个入口',
    target: 'BL2 拍到箭头两态（展开 ⌄ / 收起 ›）但没点过，只能标 📖。'
      + '⭐ 要判「只展开一个组」，画布上**必须同时有两个组** —— 只有一个组时，'
      + '「单组」和「全部」长得一模一样，判据不成立。故本轮先建两个组并断言数量为 2。',
    evidence: out,
    visible_text: JSON.stringify({ 基线: out.base, 建组后: out.afterGroup?.groups?.length,
      收起态: out.collapsed?.rows, 箭头: out.arrow, 复原: out.restore, 刷新后: out.afterReload }).slice(0, 3000),
    shot: out.arrow?.shot,
  });
  console.log('\nBM1 完成');
} finally {
  await browser.close();
}

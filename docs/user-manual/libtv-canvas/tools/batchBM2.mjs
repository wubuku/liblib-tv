// Batch BM2 — 用**图形**认那个箭头，再点它。
//
// BM1 已坐实的：两个组都建起来了（`Group 2` + `Group 1`），
// `收起全部分组` 在多组下同样有效（两个组的成员都消失）。
// 但箭头**没点成** —— 我的选择器是 `/^[›⌄>v√▾▸]$/` 去匹配 `innerText`，
// 而那个箭头**根本不是文字，是 SVG 图标**，所以必然 0 命中。
//
// ⭐ 这是 §30「参数条上好几枚按钮既无文字也无 aria」的老坑换个地方又踩：
//     **按文字找图标按钮，永远找不到。** 认图标要看**图形结构**（svg/path/rect 的数量与形状），
//     不是看 innerText。
//
// 本轮：先建两个组 → 收起 → 在组名行左侧**按图形**找出那个图标元素 → 点它 →
//       判定是「只展开一个组」还是「两个都展开」。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBM2';
const { browser, page } = await launch();

const groups = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node-group')].map((g) => {
  const r = g.getBoundingClientRect();
  return { id: g.getAttribute('data-id'), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    name: (g.innerText || '').replace(/\s+/g, ' ').trim().match(/Group\s*\d+/)?.[0] || '' };
}));

/** ⭐ 组名行左侧那一小片：按**图形**找候选（不管有没有文字）。 */
const groupRowParts = () => page.evaluate(() => {
  const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
  // 1) 先定位组名文字元素
  const nameEls = [...document.querySelectorAll('body *')].filter((e) => !skip.has(e.tagName))
    .map((e) => { const r = e.getBoundingClientRect();
      return { e, t: (e.innerText || '').replace(/\s+/g, ' ').trim(), r,
        svg: e.querySelector('svg'), paths: e.querySelectorAll('path').length,
        polys: e.querySelectorAll('polygon,polyline').length, lines: e.querySelectorAll('line,polyline').length,
        kids: e.children.length }; })
    .filter((x) => /^Group\s*\d+$/.test(x.t) && x.r.width > 20 && x.r.height > 10 && x.r.x < 360);
  const out = [];
  for (const n of nameEls) {
    // 2) 从组名行往左 40px 内，捞所有**可见**的小元素，逐个报图形信息
    const zone = [];
    for (const e of document.querySelectorAll('body *')) {
      if (skip.has(e.tagName)) continue;
      const r = e.getBoundingClientRect();
      if (r.width < 4 || r.height < 4 || r.width > 44 || r.height > 44) continue;
      if (r.x + r.width < n.r.x - 46 || r.x > n.r.x - 2) continue;      // 组名左侧 46px 内
      if (Math.abs((r.y + r.height / 2) - (n.r.y + n.r.height / 2)) > 14) continue;
      zone.push({ tag: e.tagName, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        text: (e.innerText || '').trim(), cls: (typeof e.className === 'string' ? e.className : '').slice(0, 40),
        svg: !!e.querySelector('svg'), paths: e.querySelectorAll('path').length,
        polys: e.querySelectorAll('polygon,polyline').length,
        cursor: getComputedStyle(e).cursor,
        cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) });
    }
    zone.sort((a, b) => a.rect[0] - b.rect[0]);
    out.push({ name: n.t, nameRect: [Math.round(n.r.x), Math.round(n.r.y), Math.round(n.r.width), Math.round(n.r.height)], zone });
  }
  return out;
});

const listRows = () => page.evaluate(() => {
  const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
  const panel = [...document.querySelectorAll('div')].filter((e) => {
    const r = e.getBoundingClientRect();
    return r.x < 40 && r.width > 250 && r.width < 360 && r.height > 400; })
    .sort((a, b) => b.getBoundingClientRect().height - a.getBoundingClientRect().height)[0];
  if (!panel) return { err: 'no drawer' };
  const rows = [...panel.querySelectorAll('*')].filter((e) => !skip.has(e.tagName))
    .map((e) => { const r = e.getBoundingClientRect();
      return { t: (e.innerText || '').replace(/\s+/g, ' ').trim(), r }; })
    .filter((x) => x.r.width > 120 && x.r.height >= 18 && x.r.height <= 60 && x.t.length > 1 && x.t.length < 40)
    .filter((x) => !/资产|搜索|全部|所有评级|展示设置|筛选|共\s*\d+/.test(x.t));
  const seen = new Set(); const o = [];
  for (const x of rows) { const k = `${Math.round(x.r.y / 4)}`; if (seen.has(k)) continue; seen.add(k); o.push(x.t); }
  return o;
});

const openDrawer = async () => {
  const d = await page.evaluate(() => {
    const e = [...document.querySelectorAll('button,[role="button"]')].find((x) => x.getAttribute('aria-label') === '资产管理');
    if (!e) return null; const r = e.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  if (!d) return false;
  await page.mouse.click(d[0], d[1]); await page.waitForTimeout(2600); return true;
};

const clickDisplay = async (want) => {
  const b = await page.evaluate(() => {
    const e = [...document.querySelectorAll('button,[role="button"]')].find((x) => x.getAttribute('aria-label') === '展示设置');
    if (!e) return null; const r = e.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  if (!b) return { executed: false, note: 'no 展示设置' };
  await page.mouse.click(b[0], b[1]); await page.waitForTimeout(1800);
  const it = await page.evaluate((w) => {
    const seen = new Set();
    for (const e of document.querySelectorAll('div,button,span')) {
      const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
      if (t !== w) continue;
      const r = e.getBoundingClientRect();
      if (r.width < 120) continue;
      const k = `${t}@${Math.round(r.y)}`; if (seen.has(k)) continue; seen.add(k);
      return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
    } return null; }, want);
  if (!it) return { executed: false, note: '菜单里没有' };
  await page.mouse.click(it[0], it[1]); await page.waitForTimeout(2600);
  await page.mouse.move(700, 300); await page.waitForTimeout(1400);
  return { executed: true };
};

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
  if (await page.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length) !== 2) {
    return { ok: false, why: '选中数 ≠ 2' }; }
  await page.keyboard.down('Meta'); await page.keyboard.press('g'); await page.keyboard.up('Meta');
  await page.waitForTimeout(2600);
  return { ok: true };
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(2000);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '按图形（SVG）认组行左侧那个图标，再点它' });

  const out = {};
  const all = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node')]
    .map((n) => { const r = n.getBoundingClientRect();
      return { id: n.getAttribute('data-id'), y: Math.round(r.y), x: Math.round(r.x), w: Math.round(r.width) }; })
    .filter((n) => n.w > 40).sort((a, b) => a.y - b.y || a.x - b.x));
  const rA = await selectTwo([all[0]?.id, all[1]?.id]);
  const rB = await selectTwo([all[2]?.id, all[3]?.id]);
  const g1 = await groups();
  console.log(`建组：${rA.ok ? 'A✅' : 'A✗'} ${rB.ok ? 'B✅' : 'B✗'} → 组 ${g1.length} 个 ${JSON.stringify(g1.map((g) => g.name))}`);
  out.groups = g1;
  if (g1.length < 2) { console.log('⛔ 组数不足，判据不成立'); }

  await openDrawer();
  console.log('\n══════ 收起两个组，造初始态 ══════');
  console.log('  收起前：', JSON.stringify(await listRows()));
  const rc = await clickDisplay('收起全部分组');
  const rowsCollapsed = await listRows();
  console.log(`  收起（${rc.executed}）后：`, JSON.stringify(rowsCollapsed));
  out.collapsed = rowsCollapsed;

  // ⭐ 按图形找箭头
  console.log('\n══════ 按图形找组行左侧的图标 ══════');
  const parts = await groupRowParts();
  console.log(`  找到 ${parts.length} 个组名行`);
  for (const p of parts) {
    console.log(`  ── ${p.name}（组名 rect=${JSON.stringify(p.nameRect)}）左侧 ${p.zone.length} 个候选：`);
    p.zone.forEach((z) => console.log(`     <${z.tag}> ${JSON.stringify(z.rect)} 文字="${z.text}" svg=${z.svg} path=${z.paths} poly=${z.polys} cursor=${z.cursor} cls="${z.cls}"`));
  }
  out.parts = parts;
  await shot(page, 'M-216-两组都收起.png');
  out.shot0 = 'M-216-两组都收起.png';

  // 挑最像「可点的展开箭头」的那个：cursor 是 pointer、有 svg、尺寸 8~24
  const cands = parts.flatMap((p) => p.zone.filter((z) => z.svg && z.rect[2] <= 28 && z.rect[3] <= 28 && z.cursor !== 'default'));
  console.log(`\n  ⭐ 候选（svg + 尺寸≤28 + cursor 非 default）：${cands.length} 个`);
  cands.slice(0, 6).forEach((c) => console.log(`     ${JSON.stringify(c.rect)} path=${c.paths} cursor=${c.cursor}`));

  if (cands.length === 0) { console.log('  ⛔ 仍然没找到可点的箭头候选'); out.click = { err: 'no candidate' }; }
  else {
    const t = cands[cands.length - 1];   // 取最靠左的那个（贴着组名左侧）
    console.log(`\n  ── 点最靠左的候选 ${JSON.stringify(t.rect)}`);
    const own = await page.evaluate(([x, y]) => {
      const o = document.elementFromPoint(x, y);
      return { tag: o ? o.tagName : null, inRow: !!(o && o.closest('div')),
        cls: o ? (typeof o.className === 'string' ? o.className : '').slice(0, 50) : null,
        svg: o ? !!o.querySelector('svg') : null }; }, [t.cx, t.cy]);
    console.log(`  落点归属：${JSON.stringify(own)}`);
    await page.mouse.click(t.cx, t.cy);
    await page.waitForTimeout(2600);
    await page.mouse.move(700, 300); await page.waitForTimeout(1400);
    const rowsAfter = await listRows();
    console.log(`  ⭐ 点完列表：${JSON.stringify(rowsAfter)}`);
    await shot(page, 'M-217-点组行图标后.png');
    out.shot1 = 'M-217-点组行图标后.png';

    const membersOf = (rows) => rows.reduce((acc, r, i) => {
      if (!/^Group\s*\d+$/.test(r)) return acc;
      const ms = []; for (let j = i + 1; j < rows.length && !/^Group\s*\d+$/.test(rows[j]); j++) ms.push(rows[j]);
      acc.push({ group: r, members: ms }); return acc; }, []);
    const before = membersOf(rowsCollapsed), after = membersOf(rowsAfter);
    console.log('  展开态分组（点前）：'); before.forEach((b) => console.log(`     ${b.group} → ${JSON.stringify(b.members)}`));
    console.log('  展开态分组（点后）：'); after.forEach((b) => console.log(`     ${b.group} → ${JSON.stringify(b.members)}`));
    const changed = JSON.stringify(before) !== JSON.stringify(after);
    const openN = after.filter((g) => g.members.length > 0).length;
    console.log(`  ⭐ 列表变了吗？ ${changed ? '**是**' : '否'}`);
    console.log(`  ⭐ 有 ${openN} / ${after.length} 个组处于展开`);
    out.click = { target: t, own, before, after, changed, openN, total: after.length };
  }

  // ═══ 复原
  console.log('\n══════ 复原 ══════');
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  for (const g of await groups()) {
    const p = await page.evaluate((gid) => {
      const el = document.querySelector(`.react-flow__node-group[data-id="${gid}"]`);
      if (!el) return null; const r = el.getBoundingClientRect();
      return [Math.round(r.x + r.width / 2), Math.round(r.y + 6)]; }, g.id);
    if (!p) continue;
    await page.mouse.click(p[0], p[1]); await page.waitForTimeout(2200);
    if (await page.evaluate(() => document.querySelectorAll('.react-flow__node-group.selected').length)) {
      await page.keyboard.down('Meta'); await page.keyboard.down('Shift'); await page.keyboard.press('g');
      await page.keyboard.up('Shift'); await page.keyboard.up('Meta');
      await page.waitForTimeout(2400);
      console.log(`  解开 ${g.name} → 剩 ${(await groups()).length} 个`);
    }
  }
  await page.reload({ waitUntil: 'domcontentloaded' }); await page.waitForTimeout(6500);
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1800);
  await fitView(page); await page.waitForTimeout(1800);
  const gRe = await groups();
  const nRe = await page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
  console.log(`  刷新后：组 ${gRe.length} 个；节点 ${nRe} 个`);
  out.restore = { groups: gRe.length, nodes: nRe };

  await logStep(B, {
    id: 'BM2-group-row-icon-click',
    title: '组行左侧那个图标：单组开关还是展开全部',
    target: 'BM1 按 innerText 找箭头 → 0 命中，因为它是 **SVG 图标不是文字**（§30 老坑）。'
      + '本轮改按**图形**认：组名左侧 46px 内所有可见小元素，逐个报 svg/path/polygon/cursor，再点最靠左的那个。'
      + '前提仍是**两个组**，否则「单组」和「全部」分不开。',
    evidence: out,
    visible_text: JSON.stringify({ 组: out.groups?.map?.((g) => g.name), 收起态: out.collapsed,
      候选: out.parts?.flatMap?.((p) => p.zone?.length), 点击: out.click, 复原: out.restore }).slice(0, 3000),
    shot: out.shot1,
  });
  console.log('\nBM2 完成');
} finally {
  await browser.close();
}

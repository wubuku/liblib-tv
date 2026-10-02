// Batch BM3 — 组行左侧那个图标，**到底是不是「只展开这一个组」的开关**。
//
// BM2 的读数不可信，已经作废：
//   ① 它建的两个组**套在一起**（Group 2 的包围盒 [65,19,1329,256] 把 Group 1 的
//      [562,19,604,222] 整个包住），于是「成员属于谁」没法靠位置分；
//   ② 它靠抽屉里的**出现顺序**归属成员，可每个名字在 DOM 里出现 3 次（外层/中层/内层
//      三个元素 innerText 一样），BM2 的去重按 `y/4` 取整没真去掉，点完之后
//      「视频节点 3」从 3 次变 6 次 —— 那是去重漏了，不是节点变了。
//   ⛔ 所以 BM2 那句「点完列表变了」说明不了任何事。
//
// 本轮两条硬规矩：
//   A. 建**互不包含**的两个组（建完拿包围盒断言，谁也不包谁），成员各 2 个、名字互不相同。
//   B. 归属**不靠出现顺序**，靠两条互相独立的读数交叉：
//      · 几何：节点中心落在哪个组包围盒里（取最小的那个）。
//      · 抽屉：行按 y 间隔 ≥8px 去重，并记下**缩进 x**；组名行 x 小于成员行 x。
//      两条不一致就不下结论。
//
// ⭐ 阳性对照（这是 BM2 缺的）：点之前先读那枚图标 `<path>` 的 `d` 属性，
//    点之后再读一次。箭头如果真的会转向，`d` 一定会变 —— 这样「没变」才有资格说出口。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBM3';
const { browser, page } = await launch();

const groups = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node-group')].map((g) => {
  const r = g.getBoundingClientRect();
  return { id: g.getAttribute('data-id'),
    rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    name: (g.innerText || '').replace(/\s+/g, ' ').trim().match(/Group\s*\d+/)?.[0] || '' };
}));

const contains = (big, small) => big[0] <= small[0] && big[1] <= small[1]
  && big[0] + big[2] >= small[0] + small[2] && big[1] + big[3] >= small[1] + small[3];

/** 几何归属：每个可见节点中心落在哪个组里（取面积最小的包含者）。 */
const geoAssign = () => page.evaluate(() => {
  const gs = [...document.querySelectorAll('.react-flow__node-group')].map((g) => {
    const r = g.getBoundingClientRect();
    return { id: g.getAttribute('data-id'), name: (g.innerText || '').replace(/\s+/g, ' ').trim().match(/Group\s*\d+/)?.[0] || '',
      x0: r.x, y0: r.y, x1: r.x + r.width, y1: r.y + r.height, area: r.width * r.height };
  });
  const nodes = [...document.querySelectorAll('.react-flow__node')].map((n) => {
    const r = n.getBoundingClientRect();
    if (r.width < 10) return null;
    const name = (n.getAttribute('aria-label') || n.innerText || '').replace(/\s+/g, ' ').trim();
    const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
    const inside = gs.filter((g) => cx >= g.x0 && cx <= g.x1 && cy >= g.y0 && cy <= g.y1).sort((a, b) => a.area - b.area);
    return { name, owner: inside.length ? inside[0].name : null, matched: inside.length };
  }).filter(Boolean);
  const byGroup = {};
  for (const n of nodes) (byGroup[n.owner || '（组外）'] ||= []).push(n.name);
  return { total: nodes.length, byGroup, ambiguous: nodes.filter((n) => n.matched > 1).length };
});

/** 抽屉行：按 y 间隔 ≥8px 去重，并记缩进 x。 */
const readRows = () => page.evaluate(() => {
  const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
  const panel = [...document.querySelectorAll('div')].filter((e) => {
    const r = e.getBoundingClientRect();
    return r.x < 40 && r.width > 250 && r.width < 360 && r.height > 400; })
    .sort((a, b) => b.getBoundingClientRect().height - a.getBoundingClientRect().height)[0];
  if (!panel) return { err: 'no drawer' };
  const cands = [...panel.querySelectorAll('*')].filter((e) => !skip.has(e.tagName)).map((e) => {
    const r = e.getBoundingClientRect();
    return { t: (e.innerText || '').replace(/\s+/g, ' ').trim(), x: r.x, y: r.y, w: r.width, h: r.height, kids: e.children.length };
  }).filter((x) => x.w > 120 && x.h >= 16 && x.h <= 60 && x.t.length > 1 && x.t.length < 40)
    .filter((x) => !/资产|搜索|全部|所有评级|展示设置|筛选|共\s*\d+|节点$/.test(x.t))
    .sort((a, b) => a.y - b.y || a.w - b.w);
  const rows = [];
  for (const c of cands) {                                   // ⭐ 同名同排只留一个
    if (rows.length && Math.abs(c.y - rows[rows.length - 1].y) < 8) continue;
    rows.push(c);
  }
  return rows.map((r) => ({ t: r.t, x: Math.round(r.x), y: Math.round(r.y) }));
});

/** 抽屉行 → 归属：组名行 = /Group N/；它的成员 = 后面**缩进更深**的那些行。 */
const ownerOf = (rows) => {
  const out = [];
  for (let i = 0; i < rows.length; i++) {
    if (!/^Group\s*\d+$/.test(rows[i].t)) continue;
    const base = rows[i];
    const ms = [];
    for (let j = i + 1; j < rows.length; j++) {
      if (/^Group\s*\d+$/.test(rows[j].t)) break;
      if (rows[j].x > base.x + 6) ms.push(rows[j].t);
    }
    out.push({ group: base.t, x: base.x, members: ms });
  }
  return out;
};

const openDrawer = async () => {
  const d = await page.evaluate(() => {
    const e = [...document.querySelectorAll('button,[role="button"]')].find((x) => x.getAttribute('aria-label') === '资产管理');
    if (!e) return null; const r = e.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  if (!d) return { executed: false };
  await page.mouse.click(d[0], d[1]); await page.waitForTimeout(2600); return { executed: true };
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
  await page.mouse.move(760, 620); await page.waitForTimeout(1400);
  return { executed: true };
};

/** 组名行左侧那枚图标的位置 + 它 `<path>` 的 `d`（阳性对照用）。 */
const rowIcon = (groupName) => page.evaluate((gname) => {
  const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
  const all = [...document.querySelectorAll('body *')].filter((e) => !skip.has(e.tagName));
  const names = all.map((e) => { const r = e.getBoundingClientRect();
    return { e, t: (e.innerText || '').replace(/\s+/g, ' ').trim(), r }; })
    .filter((x) => /^Group\s*\d+$/.test(x.t) && x.r.width > 20 && x.r.height > 10 && x.r.x < 360)
    .sort((a, b) => a.r.width - b.r.width);
  const n = names.find((x) => x.t === gname);
  if (!n) return { found: false };
  let best = null;
  for (const e of all) {
    const r = e.getBoundingClientRect();
    if (r.width < 8 || r.width > 30 || r.height < 8 || r.height > 30) continue;
    if (r.x + r.width < n.r.x - 50 || r.x > n.r.x - 4) continue;
    if (Math.abs((r.y + r.height / 2) - (n.r.y + n.r.height / 2)) > 14) continue;
    if (!e.querySelector('svg')) continue;
    if (getComputedStyle(e).cursor === 'default') continue;
    if (!best || r.x < best.rect[0]) {
      const p = e.querySelector('path');
      best = { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2),
        cls: (typeof e.className === 'string' ? e.className : '').slice(0, 60),
        d: p ? p.getAttribute('d') : null, transform: e.querySelector('svg')?.getAttribute('transform') };
    }
  }
  return best ? { found: true, ...best } : { found: false, why: '组名左侧 50px 内没有 svg+cursor 候选' };
}, groupName);

const clickAt = async (p) => { await page.mouse.click(p.cx, p.cy); await page.waitForTimeout(2400);
  await page.mouse.move(760, 620); await page.waitForTimeout(1400); };

async function selectNodes(ids) {
  const pts = [];
  for (const id of ids) {
    const p = await page.evaluate((nid) => {
      const n = [...document.querySelectorAll('.react-flow__node')].find((x) => x.getAttribute('data-id') === nid);
      if (!n) return null; const r = n.getBoundingClientRect();
      if (r.width < 10) return null;
      for (let fy = 0.2; fy <= 0.81; fy += 0.12) for (let fx = 0.1; fx <= 0.9; fx += 0.08) {
        const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
        const o = document.elementFromPoint(x, y);
        if (o && o.closest('.react-flow__node') === n) return [x, y];
      } return null; }, id);
    if (p) pts.push(p);
  }
  if (pts.length < 2) return { ok: false, why: `只取到 ${pts.length} 个点` };
  await page.mouse.click(pts[0][0], pts[0][1]); await page.waitForTimeout(1600);
  await page.keyboard.down('Shift'); await page.mouse.click(pts[1][0], pts[1][1]); await page.keyboard.up('Shift');
  await page.waitForTimeout(1800);
  const sel = await page.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
  if (sel !== 2) return { ok: false, why: `选中数 ${sel} ≠ 2` };
  await page.keyboard.down('Meta'); await page.keyboard.press('g'); await page.keyboard.up('Meta');
  await page.waitForTimeout(2400);
  return { ok: true, sel };
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(2000);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '几何归属 + 抽屉缩进去重双读数，重测组行左侧图标' });
  const out = {};

  // ── 建两个互不包含的组
  const all = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
    const r = n.getBoundingClientRect();
    return { id: n.getAttribute('data-id'), name: (n.getAttribute('aria-label') || '').trim(),
      cx: r.x + r.width / 2, cy: r.y + r.height / 2, w: r.width }; })
    .filter((n) => n.w > 40).sort((a, b) => a.cx - b.cx));
  console.log(`画布上 ${all.length} 个节点，按 x 排序：`);
  all.forEach((n) => console.log(`   ${n.id}  ${n.name}  中心(${Math.round(n.cx)},${Math.round(n.cy)})`));

  // 左右各挑两个 → 组的包围盒大概率不重叠
  const left2 = all.slice(0, 2).map((n) => n.id);
  const right2 = all.slice(-2).map((n) => n.id);
  const rA = await selectNodes(left2);
  console.log(`\n建组 A（左）= ${JSON.stringify(left2)} → ${rA.ok ? '✅' : '✗ ' + rA.why}`);
  const rB = await selectNodes(right2);
  console.log(`建组 B（右）= ${JSON.stringify(right2)} → ${rB.ok ? '✅' : '✗ ' + rB.why}`);
  const g = await groups();
  out.pairs = { left2, right2, rA, rB };
  out.groups = g;
  console.log(`组：${JSON.stringify(g.map((x) => ({ n: x.name, r: x.rect })))}`);
  if (g.length < 2) { console.log('⛔ 组数不足 2，判据不成立，中止'); throw new Error('groups<2'); }
  const nested = contains(g[0].rect, g[1].rect) || contains(g[1].rect, g[0].rect);
  console.log(`⭐ 两个组互不包含？ ${nested ? '❌ 包含，本轮判据不成立' : '✅ 不包含'}`);
  out.nested = nested;
  if (nested) { console.log('⛔ 包围盒互相包含，几何归属不可信，中止'); throw new Error('nested'); }

  // ── 读数流水线
  await openDrawer();
  const read = async (label) => {
    const rows = await readRows();
    const geo = await geoAssign();
    const own = ownerOf(rows);
    console.log(`\n── ${label} ──`);
    console.log(`   抽屉行（${rows.length} 行）：`);
    rows.forEach((r) => console.log(`      x=${String(r.x).padStart(3)} y=${String(r.y).padStart(4)}  ${r.t}`));
    console.log(`   抽屉归属：${own.map((o) => `${o.group}(x=${o.x})→${JSON.stringify(o.members)}`).join('  ')}`);
    console.log(`   几何归属（共 ${geo.total} 个可见节点，重叠 ${geo.ambiguous} 个）：${JSON.stringify(geo.byGroup)}`);
    return { rows, own, geo };
  };

  const sA = await read('状态 A：建组后（默认）');
  await shot(page, 'M-218-两个组-默认展开.png');
  out.shotA = 'M-218-两个组-默认展开.png';

  console.log('\n══════ 收起全部分组，造两个都收起的初始态 ══════');
  const rc = await clickDisplay('收起全部分组');
  const sB = await read(`状态 B：点「收起全部分组」（executed=${rc.executed}）`);
  await shot(page, 'M-219-两个组-都收起.png');
  out.shotB = 'M-219-两个组-都收起.png';

  const openB = sB.own.filter((o) => o.members.length > 0);
  console.log(`  ⭐ 阳性对照：此刻处于展开的组 = ${openB.length} 个（期望 0，>0 说明「收起」就没收干净，后续判据失效）`);
  out.posCtrlB = openB.length;

  // ── 主实验：点 A 组行左侧图标
  const nameA = sB.own[0]?.group || g[0].name;
  const nameB = sB.own[1]?.group || g[1].name;
  console.log(`\n══════ 主实验：点「${nameA}」行左侧那枚图标 ══════`);
  const ic0 = await rowIcon(nameA);
  console.log(`  找到图标？ ${ic0.found ? '✅ ' + JSON.stringify(ic0.rect) + ' d=' + String(ic0.d).slice(0, 60) : '❌ ' + ic0.why}`);
  out.icon0 = ic0;
  if (!ic0.found) { console.log('⛔ 没有可点的图标候选'); out.main = { err: 'no icon' }; }
  else {
    await clickAt(ic0);
    const sC = await read(`状态 C：点完「${nameA}」图标`);
    const ic1 = await rowIcon(nameA);
    const openC = sC.own.filter((o) => o.members.length > 0).map((o) => o.group);
    console.log(`  ⭐ 图标 path d 变了吗？ ${ic1.d !== ic0.d ? '**是**' : '否'}（点前 ${String(ic0.d).slice(0, 40)} → 点后 ${String(ic1.d).slice(0, 40)}）`);
    console.log(`  ⭐ 展开的组 = ${JSON.stringify(openC)}`);
    await shot(page, 'M-220-点图标后.png');
    out.shotC = 'M-220-点图标后.png';
    out.main = { nameA, icon: { before: ic0, after: ic1, dChanged: ic1.d !== ic0.d },
      openAfter: openC, rowsBefore: sB.rows, rowsAfter: sC.rows, geoAfter: sC.geo };

    console.log(`\n══════ 再点一次：是不是开关（能收回去）？ ══════`);
    const ic1b = await rowIcon(nameA);
    if (ic1b.found) {
      await clickAt(ic1b);
      const sD = await read('状态 D：再点一次');
      const openD = sD.own.filter((o) => o.members.length > 0).map((o) => o.group);
      console.log(`  ⭐ 展开的组 = ${JSON.stringify(openD)}（回到 0 就是开关）`);
      out.toggle = { openAfterFirst: openC, openAfterSecond: openD, rows: sD.rows };
    } else { out.toggle = { err: 'icon vanished after first click' }; }
  }

  // ── 反向：两个都收起后点 B 组，验是不是「只展开 B」
  console.log('\n══════ 反向对照：两个都收起，然后点「' + nameB + '」 ══════');
  const rc2 = await clickDisplay('收起全部分组');
  const sE = await read(`状态 E：再次「收起全部分组」（executed=${rc2.executed}）`);
  const icB = await rowIcon(nameB);
  console.log(`  「${nameB}」图标：${icB.found ? '✅ ' + JSON.stringify(icB.rect) : '❌ ' + icB.why}`);
  if (icB.found) {
    await clickAt(icB);
    const sF = await read(`状态 F：点完「${nameB}」图标`);
    const openF = sF.own.filter((o) => o.members.length > 0).map((o) => o.group);
    console.log(`  ⭐ 展开的组 = ${JSON.stringify(openF)}（只含 ${nameB} 且不含 ${nameA} → 单组开关）`);
    await shot(page, 'M-221-点第二个组的图标.png');
    out.shotF = 'M-221-点第二个组的图标.png';
    out.reverse = { nameB, icon: icB, openAfter: openF, rowsBefore: sE.rows, rowsAfter: sF.rows };
  }

  // ═══ 复原
  console.log('\n══════ 复原：解开所有组 ══════');
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  for (const gg of await groups()) {
    const p = await page.evaluate((gid) => {
      const el = document.querySelector(`.react-flow__node-group[data-id="${gid}"]`);
      if (!el) return null; const r = el.getBoundingClientRect();
      return [Math.round(r.x + r.width / 2), Math.round(r.y + 6)]; }, gg.id);
    if (!p) continue;
    await page.mouse.click(p[0], p[1]); await page.waitForTimeout(2000);
    if (await page.evaluate(() => document.querySelectorAll('.react-flow__node-group.selected').length)) {
      await page.keyboard.down('Meta'); await page.keyboard.down('Shift'); await page.keyboard.press('g');
      await page.keyboard.up('Shift'); await page.keyboard.up('Meta');
      await page.waitForTimeout(2400);
      console.log(`  解开 ${gg.name} → 剩 ${(await groups()).length} 个`);
    } else console.log(`  ⚠ ${gg.name} 选不中`);
  }
  await page.reload({ waitUntil: 'domcontentloaded' }); await page.waitForTimeout(6500);
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1800);
  await fitView(page); await page.waitForTimeout(1800);
  const gRe = await groups();
  const nRe = await page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
  console.log(`  刷新后：组 ${gRe.length} 个；节点 ${nRe} 个`);
  out.restore = { groups: gRe.length, nodes: nRe };

  await logStep(B, {
    id: 'BM3-row-icon-is-per-group-toggle',
    title: '组行左侧那枚图标：到底是不是「只展开这一个组」的开关',
    target: 'BM2 的读数作废：两个组互相包含、成员归属靠出现顺序、DOM 里同名元素出现 3 次导致去重漏。'
      + '本轮建**互不包含**的两个组，归属改用「节点中心落在哪个包围盒里」+「抽屉行按 y 间隔去重并读缩进」双读数交叉；'
      + '并加阳性对照：点图标前后读它 `<path>` 的 `d`。',
    evidence: out,
    visible_text: JSON.stringify({ 建组: out.pairs, 组: out.groups?.map?.((x) => ({ n: x.name, r: x.rect })),
      嵌套: out.nested, 收起后仍展开的组数: out.posCtrlB, 主实验: out.main, 反向: out.reverse, 复原: out.restore }).slice(0, 3000),
    shot: out.shotC,
  });
  console.log('\nBM3 完成');
} catch (e) {
  console.log('⛔ 中止：' + e.message);
  try {
    await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
    for (const gg of await groups()) {
      const p = await page.evaluate((gid) => {
        const el = document.querySelector(`.react-flow__node-group[data-id="${gid}"]`);
        if (!el) return null; const r = el.getBoundingClientRect();
        return [Math.round(r.x + r.width / 2), Math.round(r.y + 6)]; }, gg.id);
      if (!p) continue;
      await page.mouse.click(p[0], p[1]); await page.waitForTimeout(2000);
      if (await page.evaluate(() => document.querySelectorAll('.react-flow__node-group.selected').length)) {
        await page.keyboard.down('Meta'); await page.keyboard.down('Shift'); await page.keyboard.press('g');
        await page.keyboard.up('Shift'); await page.keyboard.up('Meta');
        await page.waitForTimeout(2400);
        console.log(`  紧急复原：解开 ${gg.name} → 剩 ${(await groups()).length} 个`);
      }
    }
  } catch (e2) { console.log('复原失败：' + e2.message); }
} finally {
  await browser.close();
}

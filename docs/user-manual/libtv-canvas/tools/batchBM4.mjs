// Batch BM4 — ① 清掉 BM3 复原失败残留的那个组；② 补验「箭头转向」到底怎么转的。
//
// BM3 坐实的：组行左侧那枚 24×24 的 chevron 是**单组展开/收起**开关（点一次只展开它自己，再点一次收回去）。
// 但 BM3 有两处没交代清楚，这轮补：
//   ① BM3 复原时「解开 Group 2 → 剩 1 个」之后，`Group 1 选不中`，画布上**残留了 1 个组**。
//      选不中的原因八成是点的是组框的 (中心x, 顶+6)，那个位置被组里的子节点盖住了。
//      本轮改成：**先关抽屉**、**点在组名行正上方的组框空白处**、并在每次点之前把
//      命中元素读出来断言它不是子节点；解不开就用「点组 → ⌘⇧G」之外的路子。
//   ② BM3 读到 chevron 的 `<path d>` 点前点后**完全一样**（都是朝下的折线
//      `M6.2.12a.4.4…`），可界面上明明一个朝下一个朝右。
//      → 说明转向不是换 path，是 **CSS transform 旋转**。本轮读 `getComputedStyle(svg).transform`
//      把这个说清楚，并给两张**只裁组名行**的特写，肉眼可直接比对箭头朝向。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const B = 'batchBM4';
const SHOTS = resolve(import.meta.dirname, '../screenshots');
const { browser, page } = await launch();

const groups = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node-group')].map((g) => {
  const r = g.getBoundingClientRect();
  return { id: g.getAttribute('data-id'),
    rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    name: (g.innerText || '').replace(/\s+/g, ' ').trim().match(/Group\s*\d+/)?.[0] || '' };
}));

const closeDrawer = async () => {
  const has = await page.evaluate(() => [...document.querySelectorAll('button,[role="button"]')]
    .some((x) => x.getAttribute('aria-label') === '资产管理'
      && x.getAttribute('aria-pressed') === 'true' || x.className.includes('active')));
  await page.keyboard.press('Escape'); await page.waitForTimeout(900);
  return has;
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

const openDrawer = async () => {
  const d = await page.evaluate(() => {
    const e = [...document.querySelectorAll('button,[role="button"]')].find((x) => x.getAttribute('aria-label') === '资产管理');
    if (!e) return null; const r = e.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  if (!d) return { executed: false };
  await page.mouse.click(d[0], d[1]); await page.waitForTimeout(2600); return { executed: true };
};

/** 抽屉行：每行报「外层 x」和「内层（真缩进）x」，只按内层 x 判归属。 */
const readRows2 = () => page.evaluate(() => {
  const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
  const panel = [...document.querySelectorAll('div')].filter((e) => {
    const r = e.getBoundingClientRect();
    return r.x < 40 && r.width > 250 && r.width < 360 && r.height > 400; })
    .sort((a, b) => b.getBoundingClientRect().height - a.getBoundingClientRect().height)[0];
  if (!panel) return { err: 'no drawer' };
  const cands = [...panel.querySelectorAll('*')].filter((e) => !skip.has(e.tagName)).map((e) => {
    const r = e.getBoundingClientRect();
    return { t: (e.innerText || '').replace(/\s+/g, ' ').trim(), x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
  }).filter((x) => x.w > 120 && x.h >= 16 && x.h <= 60 && x.t.length > 1 && x.t.length < 40)
    .filter((x) => !/资产|搜索|全部|所有评级|展示设置|筛选|共\s*\d+|节点$/.test(x.t));
  // 一行 = 一个 46px 高的带子；把子按 y 聚成组，取组内 x 最大的当「真缩进」
  const buckets = [];
  for (const c of cands.sort((a, b) => a.y - b.y || a.x - b.x)) {
    const last = buckets[buckets.length - 1];
    if (last && Math.abs(c.y - last.y) <= 14) { last.xs.push(c.x); last.ys.push(c.y); }
    else buckets.push({ t: c.t, y: c.y, xs: [c.x], ys: [c.y] });
  }
  return buckets.map((b) => ({ t: b.t, x: Math.max(...b.xs), outer: Math.min(...b.xs), y: Math.round(Math.min(...b.ys)) }));
});

const ownerOf2 = (rows) => {
  const out = [];
  for (let i = 0; i < rows.length; i++) {
    if (!/^Group\s*\d+$/.test(rows[i].t)) continue;
    const base = rows[i]; const ms = [];
    for (let j = i + 1; j < rows.length; j++) {
      if (/^Group\s*\d+$/.test(rows[j].t)) break;
      if (rows[j].x > base.x + 6) ms.push(rows[j].t);
    }
    out.push({ group: base.t, x: base.x, members: ms });
  }
  return out;
};

/** chevron 的 path d + 计算后的 transform + 外层 span 的 transform。 */
const chevron = (gname) => page.evaluate((gname2) => {
  const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
  const all = [...document.querySelectorAll('body *')].filter((e) => !skip.has(e.tagName));
  const names = all.map((e) => { const r = e.getBoundingClientRect();
    return { e, t: (e.innerText || '').replace(/\s+/g, ' ').trim(), r, w: r.width }; })
    .filter((x) => /^Group\s*\d+$/.test(x.t) && x.w > 20 && x.r.x < 360).sort((a, b) => a.w - b.w);
  const n = names.find((x) => x.t === gname2);
  if (!n) return { found: false, why: '找不到组名行' };
  let best = null;
  for (const e of all) {
    const r = e.getBoundingClientRect();
    if (r.width < 8 || r.width > 30 || r.height < 8 || r.height > 30) continue;
    if (r.x + r.width < n.r.x - 50 || r.x > n.r.x - 4) continue;
    if (Math.abs((r.y + r.height / 2) - (n.r.y + n.r.height / 2)) > 14) continue;
    const svg = e.querySelector('svg'); if (!svg) continue;
    if (getComputedStyle(e).cursor === 'default') continue;
    if (best && r.x >= best.rect[0]) continue;
    const p = e.querySelector('path');
    const cs = getComputedStyle(svg), ce = getComputedStyle(e);
    best = { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2),
      d: p ? p.getAttribute('d') : null,
      svgTransform: cs.transform, spanTransform: ce.transform,
      rowCls: n.e.className ? String(n.e.className).slice(0, 120) : '' };
  }
  return best ? { found: true, ...best } : { found: false, why: '组名左侧没有 chevron 候选' };
}, gname);

/** 只裁组名两行的特写，肉眼直接比箭头。 */
const cropRows = async (file) => {
  const box = await page.evaluate(() => {
    const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
    const ys = [...document.querySelectorAll('body *')].filter((e) => !skip.has(e.tagName))
      .map((e) => { const r = e.getBoundingClientRect();
        return { t: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20), r, w: r.width }; })
      .filter((x) => /^Group\s*\d+$/.test(x.t) && x.w > 20 && x.r.x < 360)
      .map((x) => x.r);
    if (!ys.length) return null;
    const y0 = Math.min(...ys.map((r) => r.y)) - 8, y1 = Math.max(...ys.map((r) => r.y + r.height)) + 8;
    return { x: 0, y: Math.max(0, y0), width: 330, height: Math.min(810, y1) - Math.max(0, y0) };
  });
  if (!box) { console.log('  ⚠ 裁不到组名行'); return false; }
  await page.screenshot({ path: `${SHOTS}/${file}`, clip: box });
  console.log(`  裁剪特写 ${file}  clip=${JSON.stringify(box)}`);
  return true;
};

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

/** ⭐ 解组：先关抽屉，在组框内**避开子节点**的几个候选点上试，命中组本身才算。 */
async function ungroupAll(tag) {
  await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  for (let round = 1; round <= 4; round++) {
    const gs = await groups();
    if (!gs.length) { console.log(`  ✅ ${tag}：已无组（第 ${round} 轮）`); return { left: 0, rounds: round - 1 }; }
    const g = gs[gs.length - 1];
    let picked = null;
    const cands = await page.evaluate((gid) => {
      const el = document.querySelector(`.react-flow__node-group[data-id="${gid}"]`);
      if (!el) return []; const r = el.getBoundingClientRect();
      const out = [];
      for (const fy of [0.5, 0.25, 0.75, 0.12, 0.88]) for (const fx of [0.06, 0.5, 0.94, 0.3, 0.7]) {
        const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
        if (x < 2 || y < 2 || x > 1438 || y > 808) continue;
        const o = document.elementFromPoint(x, y);
        if (!o) continue;
        const host = o.closest('.react-flow__node-group');
        if (!host || host.getAttribute('data-id') !== gid) continue;   // ⭐ 必须命中组本身
        out.push([x, y]);
      } return out; }, g.id);
    for (const c of cands) { await page.mouse.click(c[0], c[1]); await page.waitForTimeout(1400);
      if (await page.evaluate(() => document.querySelectorAll('.react-flow__node-group.selected').length)) { picked = c; break; } }
    if (!picked) { console.log(`  ⛔ ${tag}：${g.name} 找不到能选中的空白点（试了 ${cands.length} 个）`); return { left: gs.length, fail: g.name }; }
    await page.keyboard.down('Meta'); await page.keyboard.down('Shift'); await page.keyboard.press('g');
    await page.keyboard.up('Shift'); await page.keyboard.up('Meta');
    await page.waitForTimeout(2400);
    console.log(`  ${tag}：解开 ${g.name} @${JSON.stringify(picked)} → 剩 ${(await groups()).length} 个`);
  }
  return { left: (await groups()).length };
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(2000);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '清 BM3 残留 + 补验 chevron 转向是 CSS rotate' });
  const out = {};

  // ── ① 清理 BM3 残留
  const g0 = await groups();
  console.log(`═══ ① 清理：开局组 ${g0.length} 个 ${JSON.stringify(g0.map((x) => x.name))} ═══`);
  if (g0.length) { out.cleanup = await ungroupAll('清理'); }
  else { out.cleanup = { left: 0, note: '开局就没有组' }; }
  await page.reload({ waitUntil: 'domcontentloaded' }); await page.waitForTimeout(6500);
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(1800);
  const baseN = await page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
  console.log(`  清理后刷新：组 ${(await groups()).length} 个；节点 ${baseN} 个`);
  out.afterCleanup = { groups: (await groups()).length, nodes: baseN };
  if ((await groups()).length) { console.log('⛔ 清理没成功，后续实验会污染画布，中止'); throw new Error('cleanup failed'); }

  // ── ② 建两个组
  const all = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
    const r = n.getBoundingClientRect();
    return { id: n.getAttribute('data-id'), name: (n.getAttribute('aria-label') || '').trim(), cx: r.x + r.width / 2, w: r.width }; })
    .filter((n) => n.w > 40).sort((a, b) => a.cx - b.cx));
  const left2 = all.slice(0, 2).map((n) => n.id), right2 = all.slice(-2).map((n) => n.id);
  const rA = await selectNodes(left2), rB = await selectNodes(right2);
  const g = await groups();
  console.log(`\n═══ ② 建组：左 ${rA.ok ? '✅' : '✗' + rA.why} / 右 ${rB.ok ? '✅' : '✗' + rB.why} → ${g.length} 个 ${JSON.stringify(g.map((x) => ({ n: x.name, r: x.rect })))} ═══`);
  out.pairs = { left2, right2, rA, rB }; out.groups = g;
  if (g.length < 2) { console.log('⛔ 组数不足 2'); throw new Error('groups<2'); }

  await openDrawer();
  const read = async (label) => {
    const rows = await readRows2(); const own = ownerOf2(rows);
    const openN = own.filter((o) => o.members.length > 0);
    console.log(`  ── ${label}：${rows.length} 行；展开的组 = ${JSON.stringify(openN.map((o) => o.group))}（${openN.length} 个）`);
    own.forEach((o) => console.log(`       ${o.group}(x=${o.x}) → ${JSON.stringify(o.members)}`));
    return { rows, own, openN: openN.map((o) => o.group) };
  };

  console.log('\n═══ ③ 两个都收起，看 chevron 什么样 ═══');
  await clickDisplay('收起全部分组');
  const sB = await read('收起全部分组');
  const chB = await chevron(sB.own[0]?.group || g[0].name);
  console.log(`  chevron(${sB.own[0]?.group})：d=${String(chB.d).slice(0, 44)}…`);
  console.log(`     svg transform = ${chB.svgTransform}`);
  console.log(`     span transform = ${chB.spanTransform}`);
  console.log(`  📸 特写（都收起）…`); await cropRows('M-222-组行箭头-收起.png');
  out.shotCollapsed = 'M-222-组行箭头-收起.png';

  console.log('\n═══ ④ 点它展开，再看 chevron ═══');
  const nameA = sB.own[0]?.group || g[0].name;
  if (chB.found) {
    await page.mouse.click(chB.cx, chB.cy); await page.waitForTimeout(2400);
    await page.mouse.move(760, 620); await page.waitForTimeout(1400);
    const sC = await read(`点完「${nameA}」的 chevron`);
    const chC = await chevron(nameA);
    console.log(`  chevron 同一枚：d 变了吗？ ${chC.d !== chB.d ? '是' : '否'}`);
    console.log(`     svg transform = ${chC.svgTransform}`);
    console.log(`     span transform = ${chC.spanTransform}`);
    console.log(`  📸 特写（展开一个）…`); await cropRows('M-223-组行箭头-展开.png');
    out.shotExpanded = 'M-223-组行箭头-展开.png';
    out.chevron = { collapsed: chB, expanded: chC, dChanged: chC.d !== chB.d,
      svgTransformChanged: chB.svgTransform !== chC.svgTransform,
      spanTransformChanged: chB.spanTransform !== chC.spanTransform };
    out.cta = { nameA, openBefore: sB.openN, openAfter: sC.openN, rowsAfter: sC.rows };
  }

  await logStep(B, {
    id: 'BM4-chevron-rotation',
    title: '组行左侧箭头不是换图标，是 CSS 旋转；顺带把 BM3 残留的组清掉',
    target: 'BM3 读到 chevron 的 path d 点前点后完全一样，可界面上明明一个朝下一个朝右 →'
      + '本轮读 getComputedStyle 的 transform，并给两张只裁组名行的特写，肉眼直接比朝向。'
      + '另外 BM3 复原时「Group 1 选不中」留下 1 个组，本轮用「关抽屉 + 只点命中组本身的空白点」清掉。',
    evidence: out,
    visible_text: JSON.stringify({ 清理: out.cleanup, 清理后: out.afterCleanup, 建组: out.pairs,
      组: out.groups?.map?.((x) => ({ n: x.name, r: x.rect })), chevron: out.chevron, 前后: out.cta }).slice(0, 3000),
    shot: out.shotExpanded,
  });
  console.log('\n── 收尾清理 ──');
  out.finalCleanup = await ungroupAll('收尾');
  await page.reload({ waitUntil: 'domcontentloaded' }); await page.waitForTimeout(6500);
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(1800);
  console.log(`  最终：组 ${(await groups()).length} 个；节点 ${await page.evaluate(() => document.querySelectorAll('.react-flow__node').length)} 个`);
  console.log('\nBM4 完成');
} catch (e) {
  console.log('⛔ 中止：' + e.message);
  try { console.log(JSON.stringify(await ungroupAll('紧急'))); } catch (e2) { console.log('复原失败：' + e2.message); }
} finally {
  await browser.close();
}

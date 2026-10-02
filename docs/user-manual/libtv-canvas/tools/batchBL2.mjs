// Batch BL2 — 补上 BL1 缺的那一格，并把画布复原。
//
// BL1 的收获：
//   · ⌘G **建组成功了**（前几轮一直失败）—— `.react-flow__node-group`，
//     `data-id="g-TXW2mTYowb"`，组操作条 `整组执行/添加到工具箱/转分镜组/解组` + 名 `Group 1`
//   · ⭐ 建组后抽屉列表**多出「Group 1」一行**，且底部计数 **`共 11 节点` → `共 12 节点`**
//     （**组本身被算成一个节点**）
//   · ⭐⭐ **「收起全部分组」实测有效**：点完 `导演台 5`（组内成员）从列表里消失，13 → 12 行
//
// BL1 的两个问题：
//   ⚠️ ① 复原失败：收尾那段选择器写成 `.react-flow__group`，而真实 class 是
//      **`.react-flow__node-group`** → 报 `no group el` → 组没解开，留在了画布上。
//   ⚠️ ② **顺序把判据废掉了**：BL1 先点「展开全部分组」——但那时列表**本来就是展开态**
//      （`Group 1` 和成员 `导演台 5` 都在），所以 13 → 13 是**幂等**，
//      不是「无效」。这正是 §32.4「幂等与无效分不开」的又一次现场重演。
//
// 本轮：
//   · 先点**收起**（让状态真的改变）→ 再点**展开**（看成员是否回来）—— 这才是可逆对照；
//   · 用**正确的选择器**解开组，并用**读数**确认复原（组容器 0 个、节点回到 11 个、
//     抽屉计数回到「共 11 节点」）。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBL2';
const { browser, page } = await launch();

/** ⭐ 组判据用**真实 class** `.react-flow__node-group`（BL1 收尾就是错在这）。 */
const groups = () => page.evaluate(() => {
  const gs = [...document.querySelectorAll('.react-flow__node-group')];
  return gs.map((g) => {
    const r = g.getBoundingClientRect();
    return { id: g.getAttribute('data-id'), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      text: (g.innerText || '').replace(/\s+/g, ' ').trim(),
      memberIds: [...g.querySelectorAll('[data-id]')].map((e) => e.getAttribute('data-id')).slice(0, 6) };
  });
});

const nodeCount = () => page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
const totalLabel = () => page.evaluate(() => {
  const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
  return [...document.querySelectorAll('body *')].filter((e) => !skip.has(e.tagName))
    .map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim())
    .find((t) => /^共\s*\d+\s*节点$/.test(t)) || null;
});

const drawerRows = () => page.evaluate(() => {
  const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
  const rows = [...document.querySelectorAll('body *')].filter((e) => !skip.has(e.tagName))
    .map((e) => { const r = e.getBoundingClientRect();
      return { e, t: (e.innerText || '').replace(/\s+/g, ' ').trim(), r, kids: e.children.length }; })
    .filter((x) => x.r.width > 180 && x.r.width < 340 && x.r.height > 16 && x.r.height < 90
      && x.r.x < 360 && x.t.length > 1 && x.t.length < 60
      && !/资产|搜索|全部|所有评级|展示设置|筛选|画布 \d/.test(x.t));
  const inner = rows.filter((x) => ![...x.e.children].some(() => false));
  const seen = new Set(); const out = [];
  for (const x of inner) { const k = `${Math.round(x.r.y / 6)}`; if (!seen.has(k)) { seen.add(k); out.push(x.t); } }
  return out;
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
    const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
    const seen = new Set(); const out = [];
    for (const e of document.querySelectorAll('body *')) {
      if (skip.has(e.tagName)) continue;
      const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
      if (!/^(展开全部分组|收起全部分组)$/.test(t)) continue;
      const r = e.getBoundingClientRect();
      if (r.width < 120) continue;                       // 只要外层那一行
      const k = `${t}@${Math.round(r.y)}`; if (seen.has(k)) continue; seen.add(k);
      out.push({ t, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] });
    }
    return out; });
};

async function clickItem(items, want) {
  const it = items.find((i) => i.t === want);
  if (!it) return { executed: false, note: '菜单里没有这一项' };
  const cx = Math.round(it.rect[0] + it.rect[2] / 2), cy = Math.round(it.rect[1] + it.rect[3] / 2);
  const own = await page.evaluate(([x, y]) => {
    const o = document.elementFromPoint(x, y);
    return { tag: o ? o.tagName : null, t: o ? (o.innerText || '').replace(/\s+/g, ' ').trim() : null }; }, [cx, cy]);
  if (own.t !== want) return { executed: false, note: `落点是「${own.t}」`, own };
  await page.mouse.click(cx, cy); await page.waitForTimeout(2600);
  await page.mouse.move(700, 300); await page.waitForTimeout(1500);
  return { executed: true, own };
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(2000);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '收起 → 展开 的可逆对照 + 用正确选择器解组复原' });

  const out = {};
  const g0 = await groups();
  console.log('══════ A. 进场的组状态 ══════');
  console.log(`  组 ${g0.length} 个：${JSON.stringify(g0.map((g) => ({ id: g.id, text: g.text.slice(0, 60), members: g.memberIds })))}`);
  console.log(`  页面上 .react-flow__node 数 = ${await nodeCount()}；底部计数 = ${JSON.stringify(await totalLabel())}`);
  out.entry = { groups: g0, nodes: await nodeCount(), label: await totalLabel() };

  // ═══ B. 可逆对照：收起 → 展开
  console.log('\n══════ B. 收起 → 展开（这才是可逆对照）══════');
  await openDrawer();
  const rows0 = await drawerRows();
  console.log(`  起始列表 ${rows0.length} 行：${JSON.stringify(rows0)}`);
  await shot(page, 'M-212-组-默认展开态.png');

  let items = await openDisplay();
  const r1 = await clickItem(items, '收起全部分组');
  const rows1 = await drawerRows();
  console.log(`  ── 收起：执行=${r1.executed} ${r1.note || ''}`);
  console.log(`     列表 ${rows0.length} → ${rows1.length} 行：${JSON.stringify(rows1)}`);
  await shot(page, 'M-213-组-收起全部分组.png');
  out.collapse = { executed: r1.executed, before: rows0, after: rows1 };

  items = await openDisplay();
  const r2 = await clickItem(items, '展开全部分组');
  const rows2 = await drawerRows();
  console.log(`  ── 展开：执行=${r2.executed} ${r2.note || ''}`);
  console.log(`     列表 ${rows1.length} → ${rows2.length} 行：${JSON.stringify(rows2)}`);
  await shot(page, 'M-214-组-展开全部分组.png');
  out.expand = { executed: r2.executed, before: rows1, after: rows2 };

  const back = JSON.stringify(rows1) === JSON.stringify(rows0);
  const back2 = JSON.stringify(rows2) === JSON.stringify(rows0);
  console.log(`\n  ⭐ 收起改变了列表？ ${JSON.stringify(rows0) !== JSON.stringify(rows1) ? '**是**' : '否'}`);
  console.log(`  ⭐ 展开把列表还原回起始态？ ${back2 ? '✅ 是' : '⚠️ 否'}`);
  console.log(`  ⭐ 收起后再展开 == 起始态？ ${back2 ? '✅ 可逆' : '⚠️ 不可逆或读数不稳'}`);
  out.reversible = back2;

  // 再点一次「收起」，留一个干净的收起态给截图
  items = await openDisplay();
  await clickItem(items, '收起全部分组');

  // ═══ C. 解组复原
  console.log('\n══════ C. 解组复原 ══════');
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  const gNow = await groups();
  console.log(`  当前组 ${gNow.length} 个：${JSON.stringify(gNow.map((g) => g.id))}`);
  if (gNow.length) {
    const gp = await page.evaluate(() => {
      const g = document.querySelector('.react-flow__node-group');   // ⭐ 正确的 class
      if (!g) return { err: 'still no group' };
      const r = g.getBoundingClientRect();
      // 找一个只属于组框（不在成员卡上）的点：组框的**上边缘**
      return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + 6), rect: [r.x, r.y, r.width, r.height] }; });
    console.log('  组框：', JSON.stringify(gp));
    await page.mouse.click(120, 780); await page.waitForTimeout(1200);
    if (gp.x) {
      await page.mouse.click(gp.x, gp.y); await page.waitForTimeout(2400);
      const sel = await page.evaluate(() => ({
        n: document.querySelectorAll('.react-flow__node.selected').length,
        isGroup: document.querySelectorAll('.react-flow__node-group.selected').length,
        who: [...document.querySelectorAll('.react-flow__node.selected')].map((e) => e.getAttribute('data-id')) }));
      console.log(`  点组框后选中：${JSON.stringify(sel)}`);
      out.picked = sel;
      if (sel.isGroup > 0 || sel.n > 0) {
        await page.keyboard.down('Meta'); await page.keyboard.down('Shift');
        await page.keyboard.press('g');
        await page.keyboard.up('Shift'); await page.keyboard.up('Meta');
        await page.waitForTimeout(2800);
        const gAfter = await groups();
        console.log(`  ⌘⇧G 后组 ${gAfter.length} 个`);
        out.afterUngroup = gAfter.length;
      }
    }
  }

  // 兜底：组操作条上就有一枚「解组」按钮
  const stillThere = (await groups()).length;
  if (stillThere) {
    console.log('  ⌘⇧G 没解开，改用组操作条上的「解组」按钮');
    const ub = await page.evaluate(() => {
      const g = document.querySelector('.react-flow__node-group');
      if (!g) return null;
      const e = [...g.querySelectorAll('button,[role="button"]')]
        .find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === '解组');
      if (!e) return { err: 'no 解组 button' };
      const r = e.getBoundingClientRect();
      return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
    console.log('  解组按钮：', JSON.stringify(ub));
    if (Array.isArray(ub)) {
      await page.mouse.click(ub[0], ub[1]); await page.waitForTimeout(3000);
      console.log(`  点完组 ${(await groups()).length} 个`);
      out.viaButton = (await groups()).length;
    } else { console.log('  ' + JSON.stringify(ub)); }
  }

  // ═══ D. 复原核对
  console.log('\n══════ D. 复原核对 ══════');
  await page.keyboard.press('Escape'); await page.waitForTimeout(1400);
  const gEnd = await groups();
  const nEnd = await nodeCount();
  const lEnd = await totalLabel();
  console.log(`  组 ${gEnd.length} 个；节点 ${nEnd} 个；底部计数 ${JSON.stringify(lEnd)}`);
  const ok = gEnd.length === 0 && nEnd === 11 && /^共\s*11\s*节点$/.test(lEnd || '');
  console.log(`  ⭐ 完全复原？ ${ok ? '✅ 是（无组 / 11 节点 / 共 11 节点）' : '⚠️ 未完全复原'}`);
  out.restored = { groups: gEnd.length, nodes: nEnd, label: lEnd, ok };

  // 刷新再确认一次落盘
  await page.reload({ waitUntil: 'domcontentloaded' }); await page.waitForTimeout(6500);
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1800);
  await fitView(page); await page.waitForTimeout(2000);
  const gRe = await groups(); const nRe = await nodeCount();
  console.log(`  刷新后：组 ${gRe.length} 个；节点 ${nRe} 个`);
  out.afterReload = { groups: gRe.length, nodes: nRe };
  await shot(page, 'M-215-解组后刷新确认.png');
  out.shotRestore = 'M-215-解组后刷新确认.png';

  await logStep(B, {
    id: 'BL2-collapse-expand-reversible',
    title: '收起/展开全部分组的可逆对照 + 解组复原',
    target: 'BL1 先点了「展开」而那时本就是展开态 → 13→13 是**幂等**不是无效，判据被自己废掉了。'
      + '本轮先「收起」再「展开」，构成可逆对照。'
      + '同时用**正确的 class `.react-flow__node-group`** 解组（BL1 写成 `.react-flow__group` 导致复原失败）。',
    evidence: out,
    visible_text: JSON.stringify({ 进场: out.entry, 收起: out.collapse, 展开: out.expand,
      可逆: out.reversible, 复原: out.restored, 刷新后: out.afterReload }).slice(0, 3000),
    shot: out.shotRestore,
  });
  console.log('\nBL2 完成');
} finally {
  await browser.close();
}

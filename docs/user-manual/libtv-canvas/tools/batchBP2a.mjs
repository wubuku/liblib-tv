// Batch BP2a — ⛔ **先查账号有没有被 BP1 写脏**，其余往后排。
//
// BP1 全程只点不提交，但它点过 `创建默认资产分类`（`executed=true`），
// 而点完再点 `管理` 时，抽屉文案从「**暂无资产**」变成了「**待分类资产**」，
// 还多出一枚 `更多操作` —— ⚠️ **有可能 BP1 真的建了东西**。
//
// ⭐ 纪律（BN5/BN6 立过，这回立刻用上）：
//   **收尾/清理动作要有自证，读到「我以为的初始态」也要独立复核。**
//   BP1 结尾只报了「节点 11」，**没复核账户状态** —— 那正是漏掉的那一步。
//
// 本轮：把「资产」页**逐行**读出来（名字 + 行内按钮），并逐行打开 `更多操作` 读菜单，
// 看清楚**有没有删除入口**。⛔ 不建、不删、不改名。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const B = 'batchBP2a';
const SHOTS = resolve(import.meta.dirname, '../screenshots');
const { browser, page } = await launch();

const clickAria = async (label, wait = 2400) => {
  const p = await page.evaluate((l) => {
    const e = [...document.querySelectorAll('button,[role="button"],[aria-label],a')].find((x) => x.getAttribute('aria-label') === l);
    if (!e) return null; const r = e.getBoundingClientRect();
    if (r.width < 4 || r.height < 4) return null;
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, label);
  if (!p) return { executed: false, note: `找不到可见的 aria-label=${label}` };
  await page.mouse.click(p[0], p[1]); await page.waitForTimeout(wait);
  return { executed: true, at: p };
};
const clickText = async (txt, wait = 2600, minW = 0) => {
  const p = await page.evaluate(([t, mw]) => {
    const seen = new Set();
    for (const e of document.querySelectorAll('div,button,span,li,a')) {
      if ((e.innerText || '').replace(/\s+/g, ' ').trim() !== t) continue;
      const r = e.getBoundingClientRect();
      if (r.width < 4 || r.height < 4 || r.width < mw) continue;
      const k = `${Math.round(r.x)}@${Math.round(r.y)}`; if (seen.has(k)) continue; seen.add(k);
      return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
    } return null; }, [txt, minW]);
  if (!p) return { executed: false, note: `找不到文字「${txt}」` };
  await page.mouse.click(p[0], p[1]); await page.waitForTimeout(wait);
  return { executed: true, at: p };
};

/** 抽屉里的「资产」页：逐行读出名字 + 行内图标按钮。 */
const rows = () => page.evaluate(() => {
  const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
  const panel = [...document.querySelectorAll('div')].filter((e) => {
    const r = e.getBoundingClientRect();
    return r.x < 40 && r.width > 250 && r.width < 360 && r.height > 400; })
    .sort((a, b) => b.getBoundingClientRect().height - a.getBoundingClientRect().height)[0];
  if (!panel) return { err: 'no drawer' };
  const pr = panel.getBoundingClientRect();
  // 一行 = 高度 40~56、宽 ≥ 200、带一个行内 aria 按钮的元素
  const cands = [...panel.querySelectorAll('*')].filter((e) => !skip.has(e.tagName)).map((e) => {
    const r = e.getBoundingClientRect();
    return { e, t: (e.innerText || '').replace(/\s+/g, ' ').trim(), r,
      aria: e.getAttribute('aria-label'), tag: e.tagName }; })
    .filter((x) => x.r.x < pr.x + 10 && x.r.x + x.r.width > pr.x + 180
      && x.r.y > pr.y + 170 && x.r.y + x.r.height < pr.y + pr.height - 30
      && x.r.height >= 30 && x.r.height <= 60);
  // 按 y 聚行
  const buckets = [];
  for (const c of cands.sort((a, b) => a.r.y - b.r.y || a.r.width - b.r.width)) {
    const last = buckets[buckets.length - 1];
    if (last && Math.abs(c.r.y - last.y) < 12) last.items.push(c);
    else buckets.push({ y: c.r.y, items: [c] });
  }
  return { foot: (panel.innerText || '').replace(/\s+/g, ' ').trim(),
    rows: buckets.map((b) => {
      const texts = b.items.map((i) => i.t).filter(Boolean);
      const btns = b.items.filter((i) => i.aria).map((i) => {
        const r = i.r; // ⚠️ i.r 已经是 getBoundingClientRect() 的返回值，不能再取一次
        return { aria: i.aria, tag: i.tag,
          at: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
          rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; });
      return { y: Math.round(b.y), texts: texts.filter((t, i, a) => a.indexOf(t) === i), buttons: btns };
    }) };
});

/** 点「管理」把空态变成列表态（BP1 发现它会切）。 */
const openManage = async () => { const r = await clickAria('资产管理', 2600); return r; };

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(1600);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1000);
  await beginBatch(B, { note: '⛔ 先查 BP1 有没有写脏账户；并逐行找删除入口' });
  const out = {};

  await clickAria('资产管理', 2800);
  await clickText('资产', 2600, 20);
  const r0 = await rows();
  out.before = r0;
  console.log(`═══ ① 刚进「资产」页 ═══\n  抽屉全文：${JSON.stringify(r0.foot)}`);
  console.log(`  行 ${r0.rows?.length} 个：`);
  (r0.rows || []).forEach((r, i) => console.log(`     ${i + 1}. y=${r.y} 文字=${JSON.stringify(r.texts)} 按钮=${JSON.stringify(r.buttons.map((b) => b.aria))}`));

  // ⭐ 点「管理」：BP1 说它把「暂无资产」变成「待分类资产」
  const mg = await openManage();
  const r1 = await rows();
  out.afterManage = r1;
  console.log(`\n═══ ② 点「管理」之后（executed=${mg.executed}）═══\n  抽屉全文：${JSON.stringify(r1.foot)}`);
  console.log(`  行 ${r1.rows?.length} 个：`);
  (r1.rows || []).forEach((r, i) => console.log(`     ${i + 1}. y=${r.y} 文字=${JSON.stringify(r.texts)} 按钮=${JSON.stringify(r.buttons.map((b) => b.aria))}`));
  await shot(page, 'M-250-资产页-管理之后.png');
  out.shot = 'M-250-资产页-管理之后.png';

  // ── 逐行打开「更多操作」读菜单 —— ⭐ 找删除入口
  console.log(`\n═══ ③ 逐行打开「更多操作」 ═══`);
  const menus = [];
  for (const [i, row] of (r1.rows || []).entries()) {
    const mb = row.buttons.find((b) => /更多|操作|\.\.\.|⋯/.test(b.aria || '')) || row.buttons[0];
    if (!mb) { console.log(`  第 ${i + 1} 行没有行内按钮`); continue; }
    await page.mouse.move(mb.at[0], mb.at[1]); await page.waitForTimeout(900);
    await page.mouse.click(mb.at[0], mb.at[1]); await page.waitForTimeout(2000);
    await page.mouse.move(760, 620); await page.waitForTimeout(1000);
    const menu = await page.evaluate(() => {
      const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
      return [...document.querySelectorAll('div,li,span')].map((e) => {
        const r = e.getBoundingClientRect();
        return { t: (e.innerText || '').replace(/\s+/g, ' ').trim(), k: e.children.length, w: Math.round(r.width), h: Math.round(r.height) }; })
        .filter((x) => x.t && x.t.length < 12 && x.k === 0 && x.w > 60 && x.w < 320 && x.h >= 18 && x.h < 48)
        .map((x) => x.t).filter((t, k, a) => a.indexOf(t) === k).slice(0, 14); });
    console.log(`  第 ${i + 1} 行（点的是「${mb.aria}」）→ 菜单：${JSON.stringify(menu)}`);
    menus.push({ row: i + 1, texts: row.texts, clicked: mb.aria, menu });
    if (i === 0) { await shot(page, 'M-251-资产行-更多操作.png'); out.shotMenu = 'M-251-资产行-更多操作.png'; }
    await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  }
  out.menus = menus;
  const allItems = [...new Set(menus.flatMap((m) => m.menu))];
  console.log(`\n  ⭐ 所有菜单项合起来：${JSON.stringify(allItems)}`);
  console.log(`  ⭐ 有没有「删除」类入口？ ${allItems.some((t) => /删除|移除|清空|丢弃/.test(t)) ? '✅ 有' : '❌ 没有'}`);
  out.menuItems = allItems;
  out.hasDelete = allItems.some((t) => /删除|移除|清空|丢弃/.test(t));

  // ── ④ 「创建」下拉（BP1 那轮 executed=false，这轮补）
  console.log(`\n═══ ④ 「+ 创建」下拉 ═══`);
  const cr = await clickAria('创建', 2200);
  const menu = await page.evaluate(() => {
    const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
    return [...document.querySelectorAll('div,li,span')].map((e) => { const r = e.getBoundingClientRect();
      return { t: (e.innerText || '').replace(/\s+/g, ' ').trim(), w: Math.round(r.width), h: Math.round(r.height) }; })
      .filter((x) => /^(新建文件夹|上传资产)$/.test(x.t) && x.w > 50 && x.h > 14)
      .map((x) => x.t).filter((t, k, a) => a.indexOf(t) === k); });
  console.log(`  executed=${cr.executed}${cr.note ? '（' + cr.note + '）' : ''}；下拉项：${JSON.stringify(menu)}`);
  out.createMenu = { executed: cr.executed, note: cr.note, items: menu };
  await page.keyboard.press('Escape'); await page.waitForTimeout(1200);

  const finalN = await page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
  out.finalNodes = finalN;
  console.log(`\n═══ 收尾：节点 ${finalN}（本轮零写操作）═══`);

  await logStep(B, {
    id: 'BP2a-asset-account-state',
    title: '⛔ 先查 BP1 有没有写脏账户，再逐行找删除入口',
    target: 'BP1 全程只点不提交，但它点过 `创建默认资产分类`（`executed=true`），'
      + '而点完再点 `管理` 时抽屉文案从「暂无资产」变成「待分类资产」还多出一枚 `更多操作` —— '
      + '⚠️ 有可能 BP1 真的建了东西。⭐ BP1 结尾只报了「节点 11」，**没复核账户状态**，'
      + '那正是漏掉的一步。本轮逐行读出资产页内容，并打开每行的 `更多操作` 找删除入口。'
      + '⛔ 不建、不删、不改名。',
    evidence: out,
    visible_text: JSON.stringify({ 进入资产页: out.before, 点管理后: out.afterManage,
      菜单项: out.menuItems, 有删除入口: out.hasDelete, 创建下拉: out.createMenu,
      收尾节点数: out.finalNodes }).slice(0, 3000),
    shot: out.shot,
  });
  console.log('\nBP2a 完成');
} catch (e) {
  console.log('⛔ 中止：' + e.message);
} finally {
  await browser.close();
}

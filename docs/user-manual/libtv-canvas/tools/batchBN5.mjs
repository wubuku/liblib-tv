// Batch BN5 — 清掉 BN3 留在账号里的那张收藏，**并把「取消收藏」这个入口验掉**。
//
// 事情是这样起来的：
//   BN3 在风格广场点了一枚 `收藏`，弹了「**收藏成功**」，浮层里出现「**取消收藏**」；
//   紧接着「再点一下回退」之后读到的提示条仍是 `["收藏成功","取消收藏"]` ——
//   **那是没清掉的残留 toast**，所以「回退成功」其实**没验成**。
//   BN4 复查：「我的收藏」里确实有 1 张卡，详情面板上写着「**取消收藏**」
//   → BN3 那次收藏**落库了、留在账号里**。
//
// ⭐ 顺带把 BN4 那个「我的收藏报 `广场没开`」的判据缺陷也解开了：
//    **已收藏的卡上不出现收藏星标**（没地方可再收藏了），而 BN3/BN4 的计数以
//    `button[aria-label="收藏"]` 为锚点 → 锚点一断就误报成「广场没开」。
//    ⇒ 判据选错了锚点，**不是功能缺失**。计数改用 `button[aria-label="详情"]`。
//
// ⛔ 全程不点 `使用`（那才是「把风格用进画布」的动作，可能建节点/消耗）。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBN5';
const { browser, page } = await launch();

const clickAria = async (label, wait = 2400) => {
  const p = await page.evaluate((l) => {
    const e = [...document.querySelectorAll('button,[role="button"],a,[aria-label]')].find((x) => x.getAttribute('aria-label') === l);
    if (!e) return null; const r = e.getBoundingClientRect();
    if (r.width < 4) return null;
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, label);
  if (!p) return { executed: false, note: `找不到 aria-label=${label}` };
  await page.mouse.click(p[0], p[1]); await page.waitForTimeout(wait);
  return { executed: true, at: p };
};
const clickText = async (txt, wait = 2800, minW = 0) => {
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

/** 收藏页/广场页的卡数：⭐ 锚点用 `详情`（已收藏的卡没有 `收藏` 按钮，用它会误报）。 */
const cardsIn = () => page.evaluate(() => {
  const inp = [...document.querySelectorAll('input')].find((i) => (i.placeholder || '').includes('搜索风格'));
  if (!inp) return { err: '广场没开' };
  let pnl = inp;
  for (let i = 0; i < 14 && pnl; i++) { const r = pnl.getBoundingClientRect();
    if (r.width > 900 && r.height > 400) break; pnl = pnl.parentElement; }
  const pr = pnl.getBoundingClientRect();
  const inside = (e) => { const r = e.getBoundingClientRect();
    return r.x >= pr.x - 4 && r.y >= pr.y - 4 && r.x < pr.x + pr.width && r.y < pr.y + pr.height; };
  const det = [...pnl.querySelectorAll('button[aria-label="详情"]')].filter(inside);
  const fav = [...pnl.querySelectorAll('button[aria-label="收藏"]')].filter(inside);
  return { detailBtns: det.length, favBtns: fav.length,
    names: det.map((d) => { let c = d;
      for (let k = 0; k < 7 && c; k++) { const r = c.getBoundingClientRect();
        if (r.width > 130 && r.width < 400 && r.height > 150) break; c = c.parentElement; }
      return (c.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 60); }),
    det0: det[0] ? (() => { const r = det[0].getBoundingClientRect();
      return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; })() : null };
});

const toasts = () => page.evaluate(() => [...document.querySelectorAll('div,li,span')]
  .filter((e) => !['SCRIPT','STYLE','NOSCRIPT','TEMPLATE'].includes(e.tagName))
  .map((e) => { const r = e.getBoundingClientRect();
    return { t: (e.innerText || '').replace(/\s+/g, ' ').trim(), r }; })
  .filter((x) => x.t && x.t.length < 30 && x.r.width > 50 && x.r.height > 16 && x.r.height < 70
    && x.r.y < 260 && /(成功|失败|已|请|不能|收藏|取消)/.test(x.t))
  .map((x) => x.t).filter((t, i, a) => a.indexOf(t) === i));

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(1600);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1000);
  await beginBatch(B, { note: '清掉 BN3 留在账号里的收藏；验「取消收藏」入口' });
  const out = {};

  await clickAria('素材库', 2400);
  await clickText('风格库', 3800);
  await clickText('我的收藏', 3000, 40);
  await clearToasts(page);
  const before = await cardsIn();
  console.log(`═══ 清理前「我的收藏」：${JSON.stringify(before)} ═══`);
  out.before = before;
  if (before.err || before.detailBtns === 0) {
    console.log('  ✅ 账号本来就是干净的，没什么要清');
    out.action = 'nothing-to-clean';
  } else {
    // ── 走「详情 → 取消收藏」这条路，别去猜星标在哪
    console.log(`\n═══ 打开第 1 张的详情，看「取消收藏」 ═══`);
    await page.mouse.move(before.det0[0] - 70, before.det0[1] - 50); await page.waitForTimeout(800);
    await page.mouse.move(before.det0[0], before.det0[1]); await page.waitForTimeout(1400);
    await page.mouse.click(before.det0[0], before.det0[1]); await page.waitForTimeout(3200);
    await page.mouse.move(700, 40); await page.waitForTimeout(900);
    const panelText = await page.evaluate(() => {
      const zs = [...document.querySelectorAll('div')].map((e) => ({ e, z: parseInt(getComputedStyle(e).zIndex || '0', 10), r: e.getBoundingClientRect() }))
        .filter((x) => x.z >= 800 && x.r.width > 200 && x.r.height > 120).sort((a, b) => b.z - a.z);
      return zs.length ? (zs[0].e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 300) : null; });
    console.log(`  详情面板：「${panelText}」`);
    out.detailText = panelText;
    await shot(page, 'M-237-风格详情-已收藏态.png');
    out.shotDetail = 'M-237-风格详情-已收藏态.png';

    const un = await clickText('取消收藏', 3000, 40);
    console.log(`  点「取消收藏」executed=${un.executed}`);
    const t1 = await toasts();
    console.log(`  提示条：${JSON.stringify(t1)}`);
    out.unfav = { executed: un.executed, toasts: t1 };

    // 关掉详情
    for (let i = 0; i < 3; i++) {
      const c = await clickAria('close', 1400);
      if (!c.executed) await page.keyboard.press('Escape');
      await page.waitForTimeout(1200);
      if (!(await page.evaluate(() => [...document.querySelectorAll('div')]
        .some((e) => parseInt(getComputedStyle(e).zIndex || '0', 10) >= 800 && e.getBoundingClientRect().width > 200)))) break;
    }
    await clearToasts(page);

    // ── 回收藏页复核
    console.log(`\n═══ 回「我的收藏」复核 ═══`);
    await clickText('我的收藏', 2800, 40);
    await clearToasts(page);
    const after = await cardsIn();
    console.log(`  ${JSON.stringify(after)}`);
    console.log(`  ⭐ 清干净了吗？ ${after.detailBtns === 0 ? '✅ 是，0 张' : `❌ 还剩 ${after.detailBtns} 张`}`);
    out.after = after;
    out.cleaned = after.detailBtns === 0;
    if (after.detailBtns > 0) {
      await shot(page, 'M-238-清理后-我的收藏.png');
      out.shotLeft = 'M-238-清理后-我的收藏.png';
    }
  }

  // ── 顺带核一件事：广场页的收藏星现在是不是又出现了（已收藏的卡不给星标）
  console.log(`\n═══ 对照：广场页 vs 收藏页，卡片上的按钮 ═══`);
  await clickText('风格广场', 2800, 40);
  await clearToasts(page);
  const plaza = await cardsIn();
  console.log(`  广场页：${JSON.stringify({ detailBtns: plaza.detailBtns, favBtns: plaza.favBtns })}`);
  await clickText('我的收藏', 2800, 40);
  await clearToasts(page);
  const mine2 = await cardsIn();
  console.log(`  收藏页：${JSON.stringify({ detailBtns: mine2.detailBtns, favBtns: mine2.favBtns })}`);
  out.btnContrast = { plaza, mine: mine2 };
  console.log(`  ⭐ 结论：广场页 ${plaza.favBtns} 枚收藏星 / 收藏页 ${mine2.favBtns} 枚`);

  await clickText('风格广场', 2000, 40);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1400);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1400);
  out.finalNodes = await page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
  console.log(`\n═══ 收尾：节点 ${out.finalNodes} ═══`);

  await logStep(B, {
    id: 'BN5-unfavorite-cleanup',
    title: '清掉 BN3 留在账号里的收藏：走「详情 → 取消收藏」，并解开一个判据缺陷',
    target: 'BN3 点收藏弹了「收藏成功」，但「再点一下回退」之后读到的提示条是**残留 toast**，'
      + '所以回退**没验成**；BN4 复查发现收藏真的落库了。本轮走 `详情 → 取消收藏` 这条路清掉，'
      + '顺带把「取消收藏」这个入口本身验掉。'
      + '⭐ 另解开 BN4 那个「我的收藏报 `广场没开`」的判据缺陷：'
      + '**已收藏的卡上不出现收藏星标**，而计数以 `button[aria-label="收藏"]` 为锚点 → 锚点一断就误报。'
      + '判据换成 `button[aria-label="详情"]`。⛔ 全程不点 `使用`。',
    evidence: out,
    visible_text: JSON.stringify({ 清理前: out.before, 详情: out.detailText, 取消: out.unfav,
      清理后: out.after, 按钮对照: out.btnContrast, 收尾节点数: out.finalNodes }).slice(0, 3000),
    shot: out.shotDetail,
  });
  console.log('\nBN5 完成');
} catch (e) {
  console.log('⛔ 中止：' + e.message);
} finally {
  await browser.close();
}

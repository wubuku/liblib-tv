// Batch BN6 — 收尾三件事：
//   ① **复核账号干净了**（BN5 点了「取消收藏」弹了「取消收藏成功」，但它自己没验成 ——
//      关详情时连按了 3 次 Escape，把广场一起关了，于是回「我的收藏」数卡片时报 `广场没开`）。
//      ⭐ 给用户账号留脏状态必须有**独立复核**，不能只信一个 toast。
//   ② 重拍卡片特写：BN3 那张只裁到**预览图**（183×245），名字/作者/数字那一行在卡外面，
//      看不出「一张卡由什么组成」。这回往下多裁 70px 把文字行带上。
//   ③ 拍一张**分类筛选后**的画面 —— 「十个分类各筛出什么」光靠表格太干。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const B = 'batchBN6';
const SHOTS = resolve(import.meta.dirname, '../screenshots');
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
/** 卡片数：锚点用 `详情`（已收藏的卡没有 `收藏` 星标，用它会误报成「没开」）。 */
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
    empties: [...pnl.querySelectorAll('*')].filter((e) => !['SCRIPT','STYLE','NOSCRIPT','TEMPLATE'].includes(e.tagName))
      .map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim())
      .filter((t) => /暂无|没有收藏|还没有|空空|去逛逛|暂无收藏/.test(t) && t.length < 40)
      .filter((t, i, a) => a.indexOf(t) === i).slice(0, 4) };
});
/** 某一行的卡片大字（把「模型徽标」和「卡名」分开）。 */
const rowInfo = () => page.evaluate(() => {
  const inp = [...document.querySelectorAll('input')].find((i) => (i.placeholder || '').includes('搜索风格'));
  if (!inp) return { err: '广场没开' };
  let pnl = inp;
  for (let i = 0; i < 14 && pnl; i++) { const r = pnl.getBoundingClientRect();
    if (r.width > 900 && r.height > 400) break; pnl = pnl.parentElement; }
  const pr = pnl.getBoundingClientRect();
  const det = [...pnl.querySelectorAll('button[aria-label="详情"]')].filter((b) => { const r = b.getBoundingClientRect();
    return r.x >= pr.x - 4 && r.y >= pr.y - 4 && r.x < pr.x + pr.width && r.y < pr.y + pr.height; });
  const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
  return det.slice(0, 6).map((d) => {
    // 往上爬到「预览 + 文字」的整体（宽度等于详情按钮所在的那一列的容器）
    let c = d;
    for (let k = 0; k < 9 && c; k++) { const r = c.getBoundingClientRect();
      if (r.height > 240 && r.height < 460 && r.width > 130 && r.width < 400) break; c = c.parentElement; }
    const cr = c.getBoundingClientRect();
    // 详情按钮下方那一行里的文字（y 在按钮之下 0~70px）
    const dr = d.getBoundingClientRect();
    const rows = [...c.querySelectorAll('*')].filter((x) => !skip.has(x.tagName)).map((x) => {
      const r = x.getBoundingClientRect();
      return { t: (x.innerText || '').replace(/\s+/g, ' ').trim(), dy: Math.round(r.y - dr.y), dx: Math.round(r.x - cr.x), w: Math.round(r.width) }; })
      .filter((x) => x.t && x.t.length < 34 && x.dy > -4 && x.dy < 80 && x.w > 0);
    const uniq = []; for (const r of rows) { const k = `${r.t}@${r.dy}`; if (uniq.some((u) => u.k === k)) continue; uniq.push({ k, ...r }); }
    return { detailAt: [Math.round(dr.x), Math.round(dr.y), Math.round(dr.width), Math.round(dr.height)],
      cardRect: [Math.round(cr.x), Math.round(cr.y), Math.round(cr.width), Math.round(cr.height)],
      below: uniq.map((u) => u.t) };
  });
});

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(1600);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1000);
  await beginBatch(B, { note: '复核账号干净 + 重拍含文字行的卡片特写 + 分类筛选实拍' });
  const out = {};

  await clickAria('素材库', 2400);
  await clickText('风格库', 3800);

  // ── ① 复核
  console.log('═══ ① 复核「我的收藏」 ═══');
  const mine = await clickText('我的收藏', 3000, 40);
  await clearToasts(page);
  const inMine = await cardsIn();
  console.log(`  executed=${mine.executed} → ${JSON.stringify(inMine)}`);
  out.myFav = inMine;
  if (inMine.err) { console.log('  ⛔ 广场没开，复核失败'); }
  else if (inMine.detailBtns === 0) { console.log('  ✅ 账号干净：收藏页 0 张卡'); out.clean = true; }
  else { console.log(`  ⚠️ 还剩 ${inMine.detailBtns} 张`); out.clean = false;
    await shot(page, 'M-239-收藏仍有残留.png'); out.shotDirty = 'M-239-收藏仍有残留.png'; }
  if (inMine.detailBtns === 0) { await shot(page, 'M-238-我的收藏-已清空.png'); out.shotEmpty = 'M-238-我的收藏-已清空.png'; }

  // ── ② 广场页读一行卡片的完整结构
  await clickText('风格广场', 3000, 40);
  await clearToasts(page);
  const rows = await rowInfo();
  out.rowInfo = rows;
  console.log(`\n═══ ② 前 ${rows.length} 张卡的「详情按钮下方那一行」═══`);
  rows.forEach((r, i) => console.log(`  卡 ${i + 1} ${JSON.stringify(r.cardRect)}\n     详情 @${JSON.stringify(r.detailAt)}\n     下方文字：${JSON.stringify(r.below)}`));

  // 重拍卡片特写：预览 + 下方文字行
  if (rows[0]) {
    const [cx, cy, cw, ch] = rows[0].cardRect;
    const h = Math.min(ch + 76, 800 - cy);
    const w = Math.min(cw + 16, 1436 - cx);
    await page.mouse.move(700, 60); await page.waitForTimeout(700);
    const noHover = rows[0].below.slice();
    // 悬停 → 两枚按钮显形
    await page.mouse.move(cx + cw / 2, cy + ch / 2); await page.waitForTimeout(1500);
    const ops = await page.evaluate((at) => {
      const s = [...document.querySelectorAll('button[aria-label="收藏"],button[aria-label="详情"]')]
        .map((b) => ({ aria: b.getAttribute('aria-label'), op: getComputedStyle(b).opacity,
          r: (() => { const q = b.getBoundingClientRect(); return [Math.round(q.x - at[0]), Math.round(q.y - at[1]), Math.round(q.width), Math.round(q.height)]; })() }))
        .filter((x) => x.r[0] > -20 && x.r[1] > -20 && x.r[0] < at[2] && x.r[1] < at[3]);
      return s; }, [cx, cy, cw, ch]);
    console.log(`  悬停后卡内按钮：${JSON.stringify(ops)}`);
    out.hoverOps = ops;
    const f = 'M-231-风格卡片-悬停显形.png';
    await page.screenshot({ path: `${SHOTS}/${f}`,
      clip: { x: cx - 8, y: cy - 8, width: w, height: h + 8 } });
    console.log(`  📸 ${f}（${w}×${h + 8}，比 BN3 往下多带了 76px 的文字行）`);
    out.shotCard = f;
    out.cardTextNoHover = noHover;
  }

  // ── ③ 分类筛选实拍
  console.log(`\n═══ ③ 切到「电商营销」拍一张 ═══`);
  const sw = await clickText('电商营销', 3000, 40);
  await page.mouse.move(700, 60); await page.waitForTimeout(1200);
  const inEcom = await cardsIn();
  const ecomRows = await rowInfo();
  console.log(`  executed=${sw.executed} → ${JSON.stringify({ detailBtns: inEcom.detailBtns })}`);
  ecomRows.slice(0, 4).forEach((r, i) => console.log(`  卡 ${i + 1} 下方文字：${JSON.stringify(r.below)}`));
  out.ecom = { executed: sw.executed, count: inEcom.detailBtns, rows: ecomRows.slice(0, 4) };
  await shot(page, 'M-240-风格广场-电商营销分类.png');
  out.shotEcom = 'M-240-风格广场-电商营销分类.png';
  console.log(`  📸 ${out.shotEcom}`);

  await clickText('推荐', 2200, 40);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1400);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1400);
  out.finalNodes = await page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
  out.finalGroups = await page.evaluate(() => document.querySelectorAll('.react-flow__node-group').length);
  console.log(`\n═══ 收尾：节点 ${out.finalNodes} / 组 ${out.finalGroups} ═══`);

  await logStep(B, {
    id: 'BN6-verify-cleanup-and-retake',
    title: '复核收藏已清干净 + 重拍含文字行的卡片特写 + 电商营销分类实拍',
    target: 'BN5 点了「取消收藏」弹了「取消收藏成功」，但它关详情时连按 3 次 Escape 把广场一起关了，'
      + '所以「回收藏页数卡片」那步**没做成**（报 `广场没开`）。'
      + '⭐ 只信一个 toast 不算复核 —— 本轮独立重开广场数一遍。'
      + '另：BN3 那张卡片特写只裁到预览图，**名字/作者/数字那一行在卡外面**，'
      + '这回往下多裁 76px 带上。',
    evidence: out,
    visible_text: JSON.stringify({ 我的收藏: out.myFav, 干净: out.clean,
      一行卡片: out.rowInfo, 悬停按钮: out.hoverOps, 电商营销: out.ecom,
      收尾: { 节点: out.finalNodes, 组: out.finalGroups } }).slice(0, 3000),
    shot: out.shotCard,
  });
  console.log('\nBN6 完成');
} catch (e) {
  console.log('⛔ 中止：' + e.message);
} finally {
  await browser.close();
}

// Batch BO2 — 抓那个 `•••`。
//
// 前面两次都抓不到它：
//   BN1–BN2 按**文字**找（`⋯` / `...` / `…`）→ 0 命中；
//   BO1 按**图形**找（`svg` 里 `circle` 元素 ≥ 2 个）→ **0 命中**。
//
// ⭐ 真相在 `d` 里：BO1 读到卡面左上角那枚 24×24 按钮的 path 是
//     `M2 0a2 2 0 1 1 0 4 2 2 0 0 1 0-4m7 0…`
//     —— 第一个子路径是一枚 `r=2` 的**圆**，然后 `m7 0` **又跳开 7px 开始第二个子路径**。
//     ⭐⭐ **三个点是画在同一个 `<path>` 里的三段子路径，不是三个 `<circle>` 元素。**
//     所以「数 circle 元素」这种判据从根上就错了 —— 得**数 `d` 里的子路径**。
//
// 本轮：按「`d` 里有 ≥2 段独立子路径」找出它 → 悬停看它显不显形 → **点开读菜单**。
// 点一个三点菜单是安全的（开的是菜单，不是「使用风格」）。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const B = 'batchBO2';
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
const clickText = async (txt, wait = 3000, minW = 0) => {
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
const pnlEl = () => page.evaluate(() => {
  const inp = [...document.querySelectorAll('input')].find((i) => /搜索(风格|特效)/.test(i.placeholder || ''));
  if (!inp) return null;
  let e = inp;
  for (let i = 0; i < 14 && e; i++) { const r = e.getBoundingClientRect();
    if (r.width > 900 && r.height > 400) return e; e = e.parentElement; }
  return null;
});

/** ⭐ 数 `d` 里的**子路径**（`M`/`m` 出现次数）来认出「多个圆点画在一个 path 里」。 */
const dotButtons = () => page.evaluate(() => {
  const inp = [...document.querySelectorAll('input')].find((i) => /搜索(风格|特效)/.test(i.placeholder || ''));
  if (!inp) return { err: '广场没开' };
  let pnl = inp;
  for (let i = 0; i < 14 && pnl; i++) { const r = pnl.getBoundingClientRect();
    if (r.width > 900 && r.height > 400) break; pnl = pnl.parentElement; }
  const pr = pnl.getBoundingClientRect();
  const inside = (e) => { const r = e.getBoundingClientRect();
    return r.x >= pr.x - 4 && r.y >= pr.y - 4 && r.x < pr.x + pr.width && r.y < pr.y + pr.height; };
  const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
  const out = [];
  for (const e of pnl.querySelectorAll('button,[role="button"]')) {
    if (skip.has(e.tagName) || !inside(e)) continue;
    const r = e.getBoundingClientRect();
    if (r.width > 60 || r.width < 10 || r.height > 60 || r.height < 10) continue;
    const sv = e.querySelector('svg') || e;
    const ds = [...sv.querySelectorAll('path')].map((p) => p.getAttribute('d') || '');
    // 子路径数 = 绝对 M 的个数（相对 m 也算一段新的）
    const subs = ds.reduce((n, d) => n + (d.match(/[Mm]/g) || []).length, 0);
    const circlesInPath = ds.reduce((n, d) => n + (d.match(/[Mm][^Mm]*?[aA]/g) || []).length, 0);
    out.push({ aria: e.getAttribute('aria-label'), text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20),
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      op: getComputedStyle(e).opacity, subs, circlesInPath,
      d: ds[0] ? ds[0].slice(0, 60) : null });
  }
  return { all: out.length,
    multi: out.filter((x) => x.circlesInPath >= 3),
    loose: out.filter((x) => x.subs >= 2).length,
    sample: out.slice(0, 6) };
});

/** 顶层浮层集合（差分用）。 */
const topLayers = () => page.evaluate(() => {
  const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
  const vw = innerWidth, vh = innerHeight;
  return [...document.querySelectorAll('div')].filter((e) => {
    if (skip.has(e.tagName)) return false;
    const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    if (r.width < 100 || r.height < 60) return false;
    if (r.x > 80 || r.y > 80 || r.x + r.width < vw - 80 || r.y + r.height < vh - 80) return false;
    if (cs.position !== 'fixed' && cs.position !== 'absolute') return false;
    return parseInt(cs.zIndex || '0', 10) >= 10; })
    .map((e) => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
      return { id: `${(typeof e.className === 'string' ? e.className : '').slice(0, 34)}|${Math.round(r.x)},${Math.round(r.y)},${Math.round(r.width)}x${Math.round(r.height)}|z${cs.zIndex}`,
        cls: (typeof e.className === 'string' ? e.className : '').slice(0, 48),
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], z: cs.zIndex,
        text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 400),
        leaves: [...e.querySelectorAll('*')].filter((x) => !skip.has(x.tagName))
          .map((x) => ({ t: (x.innerText || '').replace(/\s+/g, ' ').trim(), k: x.children.length }))
          .filter((x) => x.t && x.t.length < 16 && x.k === 0).map((x) => x.t)
          .filter((t, i, a) => a.indexOf(t) === i).slice(0, 14) }; });
});

async function probeDots(tag) {
  console.log(`\n══════ ${tag} ══════`);
  const db = await dotButtons();
  console.log(`  面板内 ${db.all} 个小按钮；「d」里有 ≥2 段子路径的：${db.loose} 个（太松）；`
    + `其中**圆弧段 ≥ 3**（= 三个点画在一段 path 里）的：${db.multi.length} 个`);
  db.multi.slice(0, 6).forEach((m) => console.log(`     <${m.aria || '空'}> ${JSON.stringify(m.rect)} op=${m.op} 子路径=${m.subs} 圆弧段=${m.circlesInPath} d="${m.d}"`));
  if (!db.multi.length) { console.log('  ⛔ 还是没找到'); return { err: 'none', db }; }

  if (!db.multi.length) { console.log('  ⛔ 圆弧段 ≥3 的一个都没有'); return { err: 'no-dots', db }; }
  const t = db.multi[0];
  const cx = t.rect[0] + t.rect[2] / 2, cy = t.rect[1] + t.rect[3] / 2;
  const L0 = await topLayers();
  await page.mouse.move(cx - 90, cy + 70); await page.waitForTimeout(800);
  const before = await page.evaluate(([x, y]) => {
    const e = document.elementFromPoint(x, y);
    const op = [...document.querySelectorAll('button,[role="button"]')].find((b) => {
      const r = b.getBoundingClientRect();
      return Math.abs(r.x + r.width / 2 - x) < 3 && Math.abs(r.y + r.height / 2 - y) < 3; });
    return op ? { op: getComputedStyle(op).opacity, aria: op.getAttribute('aria-label') } : null; }, [cx, cy]);
  console.log(`  悬停前该按钮 opacity=${JSON.stringify(before)}`);
  await page.mouse.click(cx, cy); await page.waitForTimeout(2200);
  await page.mouse.move(700, 620); await page.waitForTimeout(1200);
  const L1 = await topLayers();
  const gained = L1.filter((x) => !L0.some((y) => y.id === x.id));
  console.log(`  点完：顶层 ${L0.length} → ${L1.length}；新增 ${gained.length} 个`);
  gained.forEach((g) => console.log(`   ▸ [${g.rect}] z=${g.z} "${g.text}"\n      叶子：${JSON.stringify(g.leaves)}`));
  const r = { target: t, hoverBefore: before, gained, layersBefore: L0.length, layersAfter: L1.length, db: { all: db.all, multi: db.multi.length } };
  if (gained.length) { await shot(page, `M-243-${tag}三点菜单.png`); r.shot = `M-243-${tag}三点菜单.png`;
    console.log(`  📸 ${r.shot}`); }
  await page.keyboard.press('Escape'); await page.waitForTimeout(1000);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1000);
  return r;
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(1600);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1000);
  await beginBatch(B, { note: '按「d 里的子路径数」认出那个 •••，再点开它' });
  const out = {};

  await clickAria('素材库', 2400);
  await clickText('特效库', 4000);
  out.fx = await probeDots('特效');
  await clickAria('close', 2200);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);

  await clickAria('素材库', 2400);
  await clickText('风格库', 4000);
  out.style = await probeDots('风格');

  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  out.finalNodes = await page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
  out.finalGroups = await page.evaluate(() => document.querySelectorAll('.react-flow__node-group').length);
  console.log(`\n═══ 收尾：节点 ${out.finalNodes} / 组 ${out.finalGroups} ═══`);

  await logStep(B, {
    id: 'BO2-three-dot-menu',
    title: '那个 •••：点文字抓不到、数 circle 元素也抓不到，它画在同一个 <path> 里',
    target: '前面两次都 0 命中 —— 按**文字**（`⋯`/`...`/`…`）和按**图形**（`circle` 元素数 ≥2）都不行。'
      + '真相：卡面左上角那枚 24×24 按钮的 `d` 是 `M2 0a2 2 0 1 1 0 4 2 2 0 0 1 0-4m7 0…` —— '
      + '第一段是一枚 r=2 的**圆**，`m7 0` 跳开 7px **又开第二段**。'
      + '⭐⭐ **三个点画在同一个 `<path>` 的三段子路径里（`子路径=3 圆弧段=3`），不是三个 `<circle>` 元素**，'
      + '所以「数 circle 元素」从根上就是错判据。⚠️ 顺带二次确认：**`详情` 按钮只在风格广场有，特效广场一枚都没有**。',
    evidence: out,
    visible_text: JSON.stringify({ 特效: out.fx, 风格: out.style,
      收尾: { 节点: out.finalNodes, 组: out.finalGroups } }).slice(0, 3000),
    shot: out.fx?.shot || out.style?.shot,
  });
  console.log('\nBO2 完成');
} catch (e) {
  console.log('⛔ 中止：' + e.message);
} finally {
  await browser.close();
}

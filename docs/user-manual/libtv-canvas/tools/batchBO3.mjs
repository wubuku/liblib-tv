// Batch BO3 — 第三次试那个 `•••`。这次**不上 DOM 判据，用像素**。
//
// BO2 找到了它（`子路径=3 圆弧段=3`），也点了，但报「新增 0 个顶层浮层」。
// ⛔ 那个「新增 0」是**我自己的判据滤掉的**：`topLayers()` 要求 `r.x <= 80`，
//    而菜单紧贴着卡片左上角打开，x≈130 —— 被我自己那道边界挡在门外。
//    ⭐ 这是本批第三次同款错误：**「没变化」和「我没看着」要分开**。
//
// 本轮判据：点前点后各裁**同一块像素**比 sha256。变了就是变了，
// 变了就把两张裁剪都存下来，肉眼裁决。DOM 读数只作旁证。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';
import { resolve } from 'node:path';
import { createHash } from 'node:crypto';

const SPACE = '10354929';
const B = 'batchBO3';
const SHOTS = resolve(import.meta.dirname, '../screenshots');
const { browser, page } = await launch();
const sha = (b) => createHash('sha256').update(b).digest('hex').slice(0, 16);

const clickAria = async (label, wait = 2400) => {
  const p = await page.evaluate((l) => {
    const e = [...document.querySelectorAll('button,[role="button"],a,[aria-label]')].find((x) => x.getAttribute('aria-label') === l);
    if (!e) return null; const r = e.getBoundingClientRect();
    if (r.width < 4) return null;
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, label);
  if (!p) return { executed: false };
  await page.mouse.click(p[0], p[1]); await page.waitForTimeout(wait);
  return { executed: true, at: p };
};
const clickText = async (txt, wait = 3200) => {
  const p = await page.evaluate((t) => {
    const seen = new Set();
    for (const e of document.querySelectorAll('div,button,span,li,a')) {
      if ((e.innerText || '').replace(/\s+/g, ' ').trim() !== t) continue;
      const r = e.getBoundingClientRect();
      if (r.width < 4 || r.height < 4) continue;
      const k = `${Math.round(r.x)}@${Math.round(r.y)}`; if (seen.has(k)) continue; seen.add(k);
      return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
    } return null; }, txt);
  if (!p) return { executed: false };
  await page.mouse.click(p[0], p[1]); await page.waitForTimeout(wait);
  return { executed: true, at: p };
};

/** 圆弧段 ≥3 的按钮（= •••），**不加 x 边界**，全面板扫。 */
const dots = () => page.evaluate(() => {
  const inp = [...document.querySelectorAll('input')].find((i) => /搜索(风格|特效)/.test(i.placeholder || ''));
  if (!inp) return { err: '广场没开' };
  let pnl = inp;
  for (let i = 0; i < 14 && pnl; i++) { const r = pnl.getBoundingClientRect();
    if (r.width > 900 && r.height > 400) break; pnl = pnl.parentElement; }
  const pr = pnl.getBoundingClientRect();
  const out = [];
  for (const e of pnl.querySelectorAll('button,[role="button"]')) {
    const r = e.getBoundingClientRect();
    if (r.width < 10 || r.width > 60 || r.height < 10 || r.height > 60) continue;
    if (r.x < pr.x - 4 || r.y < pr.y - 4 || r.x > pr.x + pr.width || r.y > pr.y + pr.height) continue;
    const sv = e.querySelector('svg') || e;
    const ds = [...sv.querySelectorAll('path')].map((p) => p.getAttribute('d') || '');
    const arcs = ds.reduce((n, d) => n + (d.match(/[Mm][^Mm]*?[aA]/g) || []).length, 0);
    if (arcs >= 3) out.push({ rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], arcs, op: getComputedStyle(e).opacity });
  }
  return { n: out.length, list: out };
});

/** 面板内**所有**新出现的可见元素（不设 x 边界，只比数量和文本）。 */
const panelTexts = () => page.evaluate(() => {
  const inp = [...document.querySelectorAll('input')].find((i) => /搜索(风格|特效)/.test(i.placeholder || ''));
  if (!inp) return { err: '广场没开' };
  let pnl = inp;
  for (let i = 0; i < 14 && pnl; i++) { const r = pnl.getBoundingClientRect();
    if (r.width > 900 && r.height > 400) break; pnl = pnl.parentElement; }
  const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
  return [...pnl.querySelectorAll('*')].filter((e) => !skip.has(e.tagName))
    .map((e) => { const r = e.getBoundingClientRect();
      return { t: (e.innerText || '').replace(/\s+/g, ' ').trim(), kids: e.children.length,
        w: Math.round(r.width), h: Math.round(r.height), x: Math.round(r.x), y: Math.round(r.y) }; })
    .filter((x) => x.t && x.t.length < 20 && x.kids === 0 && x.w > 4 && x.h > 4)
    .map((x) => `${x.t}@${x.x},${x.y}`);
});

async function probe(tag) {
  console.log(`\n══════ ${tag} ══════`);
  const d = await dots();
  console.log(`  面板内「圆弧段≥3」的按钮：${d.n} 个 ${JSON.stringify(d.list.slice(0, 3))}`);
  if (!d.n) return { err: 'no dots', d };
  const [bx, by] = d.list[0].rect;
  const cx = bx + 12, cy = by + 12;
  const zone = { x: Math.max(0, bx - 10), y: Math.max(0, by - 10), width: 420, height: 340 };
  console.log(`  目标 ${JSON.stringify(d.list[0].rect)}；裁剪区 ${JSON.stringify(zone)}`);

  await page.mouse.move(700, 620); await page.waitForTimeout(900);
  const t0 = await panelTexts();
  const c0 = await page.screenshot({ clip: zone });
  await page.mouse.move(cx, cy); await page.waitForTimeout(1400);
  await page.mouse.click(cx, cy); await page.waitForTimeout(2400);
  await page.mouse.move(zone.x + zone.width - 30, zone.y + zone.height - 30); await page.waitForTimeout(1200);
  const t1 = await panelTexts();
  const c1 = await page.screenshot({ clip: zone });
  const gained = t1.filter((x) => !t0.includes(x));
  console.log(`  面板内文字块：点前 ${t0.length} → 点后 ${t1.length}；新增 ${JSON.stringify(gained)}`);
  console.log(`  ⭐ 同一块像素：${sha(c0)}(${c0.length}B) → ${sha(c1)}(${c1.length}B)  ${sha(c0) === sha(c1) ? '**完全一样**' : '**变了**'}`);

  const before = `M-244-${tag}三点-前.png`, after = `M-245-${tag}三点-后.png`;
  await page.screenshot({ path: `${SHOTS}/${before}`, clip: zone });
  const changed = sha(c0) !== sha(c1);
  if (changed) { await page.screenshot({ path: `${SHOTS}/${after}`, clip: zone });
    console.log(`  📸 ${before} / ${after}（已存盘，可肉眼比对）`); }
  else { console.log('  （没变，只留「前」一张作对照）'); }
  await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  return { target: d.list[0], zone, textsBefore: t0.length, textsAfter: t1.length, gained, changed,
    shotBefore: before, shotAfter: changed ? after : null, bytesBefore: c0.length, bytesAfter: c1.length };
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(1600);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1000);
  await beginBatch(B, { note: '那个 ••• —— 第三次，这次只用像素判' });
  const out = {};

  await clickAria('素材库', 2400);
  await clickText('特效库', 4200);
  out.fx = await probe('特效');

  await clickAria('close', 2000);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1400);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1400);
  await clickAria('素材库', 2400);
  await clickText('风格库', 4200);
  out.style = await probe('风格');

  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  out.finalNodes = await page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
  console.log(`\n═══ 收尾：节点 ${out.finalNodes} ═══`);

  await logStep(B, {
    id: 'BO3-dots-pixel-only',
    title: '那个 ••• 第三次试：不看 DOM 判据，只比像素',
    target: 'BO2 已经定位到它（`子路径=3 圆弧段=3`，特效 12 张卡都有，风格只有 2 张，'
      + '其余卡左上角是 📊 模型徽标），也点了，但报「新增 0 个顶层浮层」—— '
      + '⛔ 那个「0」是**判据自己滤掉的**：`topLayers()` 要求 `r.x <= 80`，'
      + '而菜单紧贴卡片左上角打开（x≈130），被我自己的边界挡在门外。'
      + '本轮放弃 DOM 判据，只做**点前点后同一块像素的 sha256 比对**。',
    evidence: out,
    visible_text: JSON.stringify({ 特效: out.fx, 风格: out.style, 收尾节点数: out.finalNodes }).slice(0, 2600),
    shot: out.fx?.shotAfter || out.fx?.shotBefore,
  });
  console.log('\nBO3 完成');
} catch (e) {
  console.log('⛔ 中止：' + e.message);
} finally {
  await browser.close();
}

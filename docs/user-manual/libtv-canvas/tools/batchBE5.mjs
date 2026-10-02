// Batch BE5 —— 收拾 BE4 的复原失败，并把「整理画布」的两条路径分诊钉死。
//
// ⛔ BE4 的复原是**假绿灯**。它报「1 轮之后仍有偏差：0 个」，但同时报「复原后布局：0 行」——
//    `flowPos` 返回的是**空数组**。原因就是 BE1 踩过的那个坑的升级版：
//    **`.react-flow__node` 只渲染视口内的节点**。整理把 11 个节点铺开，
//    视口一个都装不下 → 读出来是空 → 「空数组.filter(...)」自然是 0 个偏差。
//    ⭐ **判据的静默失败模式**：一个「全部通过」的空读数，
//    永远要配一条「读到了几条」的断言，否则它会替你撒谎。
//
// ⭐⭐ BE4 的主发现（这才是这批的收获）：
//    | 路径 | 画布坐标变化 | 确认条 |
//    |---|---|---|
//    | 键盘 `⌥⇧F` | **0 个** | 无 |
//    | 底栏「整理画布，Option+Shift+F」按钮 | **11 个（全部）** | 「是否保留此次整理结果？ 还原 保留」 |
//    也就是说**按钮是好的，键盘按不出效果**。但不能就此断言「快捷键坏了」——
//    macOS 的 `⌥`+字母可能被输入法/系统层吃掉，自动化分不清这一层。
//    正确写法是「两条路径一好一坏，分不清是谁的锅」。
//
// ✅ 这一轮的收尾：把画布**整理成整齐布局并点「保留」落盘** ——
//    这是产品自己给的布局，比我手动拖回去更可靠。
//    位置是本手册反复挪动过的（BD1–BE4 全在做拖动实验），
//    但**节点内容一个没少、没多、没改名**。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';

const SPACE = '10354929';
const B = 'batchBE5';
const { browser, page } = await launch();

/** ⭐ 画布坐标。**附一条「读到了几条」——空读数必须能被发现。 */
const flowPos = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
  const m = /matrix\(([^)]+)\)/.exec(getComputedStyle(n).transform || '');
  const p = m ? m[1].split(',').map(Number) : null;
  return { id: n.getAttribute('data-id'),
    name: ((n.innerText || '').replace(/\s+/g, ' ').trim().split(' ')[0] || '').slice(0, 12),
    x: p ? Math.round(p[4]) : null, y: p ? Math.round(p[5]) : null }; }));

const stat = (l) => {
  const byRow = {};
  for (const n of l) (byRow[n.y] = byRow[n.y] || []).push(n);
  const rows = Object.keys(byRow).map(Number).sort((a, b) => a - b);
  const gaps = [];
  for (const y of rows) {
    const r = byRow[y].slice().sort((a, b) => a.x - b.x);
    for (let i = 1; i < r.length; i += 1) gaps.push(r[i].x - r[i - 1].x);
  }
  return { n: l.length, rows: rows.length, gaps, kinds: [...new Set(gaps)].length,
    rowSizes: rows.map((y) => byRow[y].length) };
};

const trueCount = () => page.evaluate(() => {
  const t = [...document.querySelectorAll('body *')]
    .filter((e) => !['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE'].includes(e.tagName))
    .map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim())
    .filter((s) => /^共\s*\d+\s*节点$/.test(s));
  const nums = [...new Set(t)].map((s) => +(/(\d+)/.exec(s) || [])[1]).filter((x) => !Number.isNaN(x));
  return { texts: [...new Set(t)], max: nums.length ? Math.max(...nums) : null };
});

const bar = (pg) => pg.evaluate(() => {
  const vis = [...document.querySelectorAll('body *')]
    .filter((e) => !['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE'].includes(e.tagName));
  const texts = [...new Set(vis.map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim())
    .filter((t) => t && t.length < 60 && /是否保留此次整理结果/.test(t)))];
  const btns = [...document.querySelectorAll('button,[role="button"]')].map((e) => {
    const r = e.getBoundingClientRect();
    return { text: (e.innerText || '').replace(/\s+/g, ' ').trim(),
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
  }).filter((e) => e.rect[2] > 0 && /^(还原|保留)$/.test(e.text));
  return { texts, btns };
});

const btn = (pg, aria) => pg.evaluate((name) => {
  const e = [...document.querySelectorAll('button,[role="button"]')].find((x) => x.getAttribute('aria-label') === name);
  if (!e) return { err: '没找到 ' + name };
  const r = e.getBoundingClientRect();
  return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) };
}, aria);

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await beginBatch(B, { note: '整理画布两条路径分诊 + 用产品自己的「整理」收尾复原' });

  const out = {};

  // ── 1. 现状盘点（每一步都带「读到了几条」）
  await page.keyboard.press('Escape'); await page.waitForTimeout(900);
  const drawerOpen = await (async () => {
    const p = await btn(page, '资产管理');
    if (p.err) return false;
    await page.mouse.click(p.x, p.y); await page.waitForTimeout(2300);
    return true; })();
  let tc = { max: null };
  if (drawerOpen) { tc = await trueCount(); await page.keyboard.press('Escape'); await page.waitForTimeout(1500); }
  console.log(`资产管理抽屉：${JSON.stringify(tc)}`);
  out.trueCountNow = tc;

  await page.keyboard.press('Meta+0'); await page.waitForTimeout(2400);
  const s1 = await flowPos();
  const st1 = stat(s1);
  console.log(`⌘0 之后读到 ${s1.length} 个节点；${st1.rows} 行，行内节点数 ${JSON.stringify(st1.rowSizes)}`);
  s1.forEach((n) => console.log(`  ${n.id.padEnd(14)} ${n.name.padEnd(8)} (${n.x}, ${n.y})`));
  out.afterFit = { count: s1.length, stat: st1, pos: s1 };
  out.readNothing = s1.length === 0;
  if (out.readNothing) console.log('  ⚠️ 读数为空 —— 「0 个偏差」这种结论在空读数上毫无意义');

  // ── 2. 键盘 ⌥⇧F 复测（在**有内容可见**的前提下）
  const bK = s1.map((n) => `${n.id}:${n.x},${n.y}`).join('|');
  await page.mouse.click(720, 300); await page.waitForTimeout(900);
  await page.keyboard.press('Meta+Alt+f'); await page.waitForTimeout(3400);
  await clearToasts(page); await page.waitForTimeout(700);
  let aK = await flowPos();
  let stK = stat(aK);
  let barK = await bar(page);
  const kChanged = aK.filter((n) => { const b = s1.find((x) => x.id === n.id); return b && (b.x !== n.x || b.y !== n.y); }).length;
  console.log(`\n键盘 ⌥⇧F：读到 ${aK.length} 个，变化 ${kChanged} 个；确认条 ${JSON.stringify(barK.texts)}`);
  out.byKey = { read: aK.length, changed: kChanged, bar: barK, stat: stK };

  // ── 3. 底栏按钮
  const bB = (await flowPos()).map((n) => `${n.id}:${n.x},${n.y}`).join('|');
  const p = await btn(page, '整理画布，Option+Shift+F');
  if (p.err) { console.log('\n底栏按钮：', p.err); out.byButton = p; }
  else {
    await page.mouse.move(p.x, p.y); await page.waitForTimeout(300);
    await page.mouse.click(p.x, p.y); await page.waitForTimeout(3600);
    await clearToasts(page); await page.waitForTimeout(800);
    const aB = await flowPos();
    const barB = await bar(page);
    console.log(`\n底栏按钮：读到 ${aB.length} 个；确认条文案 ${JSON.stringify(barB.texts)}`);
    console.log(`  按钮坐标 ${JSON.stringify(barB.btns)}`);
    out.byButton = { read: aB.length, bar: barB, pos: aB,
      changed: (aB.map((n) => `${n.id}:${n.x},${n.y}`).join('|')) !== bB };
  }

  // ── 4. 复原：点确认条的「保留」，让整理结果落盘
  console.log('\n--- 复原：点「保留」把整理结果落盘 ---');
  let keep = null;
  const bNow = await bar(page);
  keep = bNow.btns.find((x) => x.text === '保留');
  if (keep) {
    await page.mouse.click(keep.rect[0] + keep.rect[2] / 2, keep.rect[1] + keep.rect[3] / 2);
    await page.waitForTimeout(3000);
    console.log('  已点「保留」');
    out.kept = true;
  } else {
    console.log('  ⚠️ 没找到「保留」按钮，确认条当前：', JSON.stringify(bNow));
    out.kept = false;
  }
  // 落盘后刷新一次，确认真的存住了
  await page.reload({ waitUntil: 'domcontentloaded' }); await page.waitForTimeout(6000);
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await page.keyboard.press('Meta+0'); await page.waitForTimeout(2400);
  const after = await flowPos();
  const stA = stat(after);
  console.log(`\n刷新后 ⌘0 读到 ${after.length} 个节点；${stA.rows} 行，行内 ${JSON.stringify(stA.rowSizes)}，间距种类 ${stA.kinds}`);
  after.forEach((n) => console.log(`  ${n.id.padEnd(14)} ${n.name.padEnd(8)} (${n.x}, ${n.y})`));
  out.afterReload = { count: after.length, stat: stA, pos: after };

  // 抽屉再确认一次
  const ok2 = await (async () => {
    const q = await btn(page, '资产管理');
    if (q.err) return false;
    await page.mouse.click(q.x, q.y); await page.waitForTimeout(2300);
    return true; })();
  if (ok2) { out.trueCountFinal = await trueCount(); await page.keyboard.press('Escape'); await page.waitForTimeout(1400); }
  console.log('刷新后抽屉读数：', JSON.stringify(out.trueCountFinal));

  await page.keyboard.press('Escape'); await page.waitForTimeout(1000);
  await shot(page, 'M-189-整理后.png');
  out.shot = 'M-189-整理后.png';

  await logStep(B, {
    id: 'BE5-tidy-two-paths-keep',
    title: '整理画布：按钮有效、键盘无效果；用「保留」把布局收尾',
    target: 'BE4 的复原报了假绿灯（0 个偏差）但同时读到 0 个节点 —— 空读数上的「全部通过」没有意义。'
      + '这轮每步都断言「读到了几条」，并用产品自己的「整理 + 保留」收尾，'
      + '而不是手动把节点拖回去。',
    evidence: out,
    visible_text: JSON.stringify({ trueCountNow: out.trueCountNow, afterFit: out.afterFit?.stat,
      byKey: out.byKey, byButton: { read: out.byButton?.read, changed: out.byButton?.changed, bar: out.byButton?.bar },
      kept: out.kept, afterReload: out.afterReload?.stat, trueCountFinal: out.trueCountFinal }).slice(0, 3000),
    shot: out.shot,
  });
  console.log('\nBE5 完成');
} finally {
  await browser.close();
}

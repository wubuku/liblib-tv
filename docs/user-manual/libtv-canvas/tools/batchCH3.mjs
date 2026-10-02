// Batch CH-3：那个「工作流 / 故事板」切换器，到底在哪儿、什么条件下才出现。
//
// 起因是 CH-2 的探查结果为**空**：在画布 2 上，页面上**根本找不到**「工作流」或「故事板」
// 这两个词的任何可见叶子元素 —— 而 `storyboard-mode.md` 开头就写着
// 「**顶栏中间**有一个切换开关：`工作流` | `故事板`」。
//
// 翻 `A4a-mode-workflow.png` 发现两点对不上：
//   ① 那个「工作流」标签**不在顶栏**，它在**画布左上角**（约 x=360,y=85）；
//   ② 那张图是**画布 1（空画布）**，而且标签上**只写了「工作流」一个选项**。
//
// ⇒ 两个可能：切换器只在**空画布**上出现；或者它是个**要点了才展开的下拉**。
// 本步把两种可能都验掉 —— 而且只在**空画布（画布 1）**上操作，零污染风险。
//
// ⚠️ 收尾必须**切回画布 2**，并复核它仍是 11 个节点、名字都是原样。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;

const { browser, page } = await launch();
const out = {};

await open(page, URL_);
await closePromos(page);
await page.evaluate(async () => {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  for (let i = 0; i < 6; i += 1) {
    const hit = [...document.querySelectorAll('button, [role="button"]')].find((b) => (b.innerText || '').trim() === '知道了');
    if (hit) { hit.click(); await sleep(500); }
    if (!(document.body.innerText || '').includes('已升级为 TV Director')) return;
  }
});
await page.waitForTimeout(1000);

// ── ① 画布 2 上：把页面上所有「像切换器 / 像标签」的可见元素扫一遍 ──
out.画布2顶栏 = await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(el).visibility !== 'hidden'; };
  const out = [];
  for (const el of document.querySelectorAll('button,[role="button"],[role="tab"],a')) {
    if (!vis(el)) continue;
    const r = el.getBoundingClientRect();
    const t = (el.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20);
    if (!t) continue;
    out.push({ 文字: t, 位置: [Math.round(r.x), Math.round(r.y)], 尺寸: `${Math.round(r.width)}x${Math.round(r.height)}`, cls: (el.className || '').toString().slice(0, 40) });
  }
  return out.slice(0, 40);
});
out.画布2含工作流吗 = await page.evaluate(() => (document.body.innerText || '').includes('工作流'));
out.画布2含故事板吗 = await page.evaluate(() => (document.body.innerText || '').includes('故事板'));
console.log('画布2 顶栏可见可点元素 =');
for (const e of out.画布2顶栏) console.log(`   [${e.位置}] "${e.文字}" ${e.尺寸}`);
console.log('画布2 文本含「工作流」=', out.画布2含工作流吗, ' 含「故事板」=', out.画布2含故事板吗);
await shot(page, 'M-319-画布2-顶栏全景.png', { clip: { x: 0, y: 0, width: 1440, height: 220 } });

// ── ② 切到画布 1（空画布）──
const dd = await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  for (const el of document.querySelectorAll('button,[role="button"]')) {
    if (!vis(el)) continue;
    if (/^画布\s*\d/.test((el.innerText || '').trim())) { const r = el.getBoundingClientRect(); return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2), 文字: (el.innerText || '').trim() }; }
  }
  return null;
});
out.画布下拉 = dd;
if (!dd) { console.log('!! 找不到画布下拉'); await browser.close(); process.exit(1); }
await page.mouse.click(dd.cx, dd.cy);
await page.waitForTimeout(1400);
out.下拉项 = await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  return [...document.querySelectorAll('button,[role="menuitem"],[role="option"],a,li,div')]
    .filter(vis).map((el) => ({ 文字: (el.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24), tag: el.tagName.toLowerCase() }))
    .filter((x) => x.文字 && x.文字.length <= 24 && /画布|工作流|故事板|新建/.test(x.文字))
    .slice(0, 20);
});
console.log('\n画布下拉项 =', JSON.stringify(out.下拉项, null, 2));

// 点「画布 1」
const one = await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  for (const el of document.querySelectorAll('button,[role="menuitem"],[role="option"],a,li,div')) {
    if (!vis(el)) continue;
    const t = (el.innerText || '').replace(/\s+/g, ' ').trim();
    if (/^画布\s*1$/.test(t) || /^画布 1/.test(t)) { const r = el.getBoundingClientRect(); return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2), 文字: t }; }
  }
  return null;
});
out.画布1入口 = one;
if (one) {
  await page.mouse.click(one.cx, one.cy);
  await page.waitForTimeout(4200);
  await closePromos(page);
  await page.waitForTimeout(1200);
  out.画布1 = await page.evaluate(() => {
    const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    const labels = [...document.querySelectorAll('*')].filter(vis).map((el) => ({
      文字: (el.innerText || '').replace(/\s+/g, ' ').trim(),
      叶子: el.children.length === 0,
      位置: (() => { const r = el.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y)]; })(),
      cursor: getComputedStyle(el).cursor,
      cls: (el.className || '').toString().slice(0, 44),
    })).filter((x) => /^(工作流|故事板)$/.test(x.文字));
    return {
      节点数: document.querySelectorAll('.react-flow__node').length,
      含工作流: (document.body.innerText || '').includes('工作流'),
      含故事板: (document.body.innerText || '').includes('故事板'),
      标签: labels,
      顶栏文字: (document.querySelector('header')?.innerText || '').replace(/\s+/g, ' ').slice(0, 80),
    };
  });
  console.log('\n画布1 =', JSON.stringify(out.画布1, null, 2));
  await shot(page, 'M-320-空画布上的模式切换器.png', { clip: { x: 0, y: 0, width: 1440, height: 400 } });
}

out.收尾url = page.url();
await writeFile(resolve(HERE, '.evidence/ch3-mode-switch.json'), JSON.stringify(out, null, 2));
console.log('\n收尾 url =', out.收尾url);
await browser.close();

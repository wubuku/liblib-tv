// Batch DT-5：补一张「5 行模型」的下拉图（M-346 那张只有 2 行）。
//
// ⭐ DT-4 的关键读数（已过阳性对照）：
//   卡面「全部适配模型」下拉会**逐行列出这张风格适配的模型**：
//     J_漫剧素材三视图…   baseType=?  → 2 行（General image V2 / General image Pro）
//     一键生成人物多视图   baseType=[27,40,70,55,68] 5 个 → ⭐ 5 行
//   ⇒ **baseType 个数 = 下拉行数，一对一**（DS 批那张 6→5 是唯一例外）
//   ⇒ 顺带把 `styleModelList` 的模型名凑到了 6 个
//
// 本轮只做一件事：**hover 第 2 个 ✧ 并截图**（5 行那张，信息量比 2 行大）。
// ⛔ 全程只 mouse.move，**不点击任何东西**。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;
const 目标 = '一键生成人物多视图';
const out = { 目标, 找到: null, 下拉: null };
const SAVE = () => writeFileSync(new URL('./batchDT5.json', import.meta.url), JSON.stringify(out, null, 2));

const { browser, page } = await launch();
await open(page, URL_);
await closePromos(page);
await page.waitForTimeout(1500);
await page.evaluate(() => document.body.focus());
await page.keyboard.press('Meta+0');
await page.waitForTimeout(2800);
for (let i = 0; i < 3; i += 1) {
  const d = page.locator('.mantine-Drawer-inner button[aria-label="关闭"]').first();
  if (await d.count()) await d.click({ timeout: 5000 }).catch(() => {});
  await page.waitForTimeout(600);
}
const pk = await page.evaluate(() => {
  const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === '下次再说');
  if (!b) return null; const r = b.getBoundingClientRect();
  return r.width > 0 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null;
});
if (pk) { await page.mouse.click(pk[0], pk[1]); await page.waitForTimeout(1200); }
await page.evaluate(() => { const b = document.querySelector('[data-sidebar-btn="open-asset"]'); if (b) b.click(); });
await page.waitForTimeout(2000);
await page.evaluate(() => [...document.querySelectorAll('button')].find((b) => (b.innerText || '').replace(/\s+/g, ' ').trim().startsWith('风格库'))?.click());
await page.waitForTimeout(5000);

// 找全部 ✧ 候选，依次 hover，直到下拉里出现目标卡的模型行
const Xs = await page.evaluate(() => {
  const 全部 = [...document.querySelectorAll('button')].filter((b) => {
    const r = b.getBoundingClientRect();
    return r.width >= 22 && r.width <= 26 && r.height >= 22 && r.height <= 26 && (b.innerText || '').trim() === '' && !b.getAttribute('aria-label') && !b.getAttribute('title') && !b.querySelector('img');
  });
  return 全部.map((b) => { const r = b.getBoundingClientRect(); return { 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; });
});
LOG(`✧ 候选 ${Xs.length} 个`);
let 命中 = null;
for (const [i, x] of Xs.entries()) {
  await page.mouse.move(x.中心[0], x.中心[1]);
  await page.waitForTimeout(1500);
  const d = await page.evaluate(() => {
    const 浮 = [...document.querySelectorAll('div')].filter((e) => {
      const t = (e.innerText || '').replace(/\s+/g, ' ');
      const s = getComputedStyle(e);
      return /全部适配模型/.test(t) && t.length < 200 && s.visibility !== 'hidden' && +s.opacity > 0.5;
    });
    if (!浮.length) return null;
    const 详 = 浮.sort((a, b) => (b.innerText || '').length - (a.innerText || '').length)[0];
    return { 全文: (详.innerText || '').replace(/\n+/g, ' | ') };
  });
  if (d) { LOG(`  第 ${i + 1} 个 ✧: ${d.全文}`); if (d.全文.includes('Lib Image') && d.全文.includes('Seedream 4.5')) { 命中 = { i, ...d }; break; } }
}
out.找到 = 命中;
if (!命中) { LOG('⛔ 没找到 5 行那张'); SAVE(); await browser.close(); process.exit(0); }

out.下拉 = 命中.全文;
LOG(`\n✅ 命中: ${命中.全文}`);
await shot(page, 'DT-b-五模型下拉.png');
LOG('📸 DT-b');
out.最终节点数 = await page.evaluate(() => document.querySelectorAll('[data-id]').length);
SAVE();
await browser.close();
LOG('\n=== 已写 tools/batchDT5.json ===');

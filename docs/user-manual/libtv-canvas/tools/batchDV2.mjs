// Batch DV-2：把广场顶部那一排页签的**真实 DOM** 读出来。
//
// ⛔ DV-1 连着两次切页签失败：
//   ① 找「特效库」—— 那是**侧栏抽屉里的入口**，广场打开后就收起来了
//   ② 找「特效广场」—— **按钮不存在**（i18n 文案 ≠ 实际 DOM 文字）
//   两次都用 `?.click()`，**找不到就静默失败**，
//   于是把**风格卡当成特效卡**分析了一整轮。
//   ⭐ 最危险的一种错：**数据是真的，只是贴错了标签。**
//
// 本轮只做一件事：**不猜，直接读**。枚举顶栏附近所有可点元素的
// 标签名 + 文字 + 高亮状态，一次看全。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;
const out = { 页签候选: [], 分类标签: [], 顶部全部按钮: null };
const SAVE = () => writeFileSync(new URL('./batchDV2.json', import.meta.url), JSON.stringify(out, null, 2));

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
await page.waitForTimeout(5500);

// ⭐ 读「广场顶部一排」：y 坐标在 150~270 之间、横向排开的所有可点元素
const 读顶栏 = () => page.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const 行 = [];
  for (const e of document.querySelectorAll('button,[role="tab"],a,div')) {
    const r = e.getBoundingClientRect();
    if (!vis(e)) continue;
    if (r.y < 130 || r.y > 290) continue;
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    if (!t || t.length > 20) continue;
    // 只取叶子/近叶子
    if (e.children.length > 2) continue;
    const c = getComputedStyle(e);
    行.push({
      文字: t, tag: e.tagName.toLowerCase(), role: e.getAttribute('role') || '',
      aria: e.getAttribute('aria-label') || '', cls: (e.className || '').toString().slice(0, 60),
      背景: c.backgroundColor, 位置: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    });
  }
  return 行;
});

const 顶 = await 读顶栏();
out.顶部全部按钮 = 顶;
LOG(`顶栏（y 130~290）可点元素 ${顶.length} 个：`);
for (const b of 顶) LOG(`   [${b.tag}${b.role ? '/' + b.role : ''}] 「${b.文字}」 bg=${b.背景} @${b.位置.join(',')}${b.aria ? ` aria=${b.aria}` : ''}`);

out.页签候选 = 顶.filter((b) => /广场|收藏|最近/.test(b.文字));
LOG(`\n⭐ 页签候选 ${out.页签候选.length} 个: ${JSON.stringify(out.页签候选.map((b) => b.文字))}`);

const 分类 = 顶.filter((b) => /^(推荐|摄影写真|电商营销|动漫游戏|风格插画|平面设计|建筑及室内设计|创意玩法|文创周边|小说推文|全部|特效)$/.test(b.文字));
out.分类标签 = 分类;
LOG(`分类/排序标签 ${分类.length} 个: ${JSON.stringify(分类.map((b) => b.文字))}`);
SAVE();
await browser.close();
LOG('\n=== 已写 tools/batchDV2.json ===');

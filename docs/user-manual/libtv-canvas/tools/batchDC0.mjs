// Batch DC-0：查清卡面左上角那三种东西的**分布规律**。
//
// DB-4 已经摆出 30 张卡的第一屏分布：
//   行1  卡0-5    [徽, ✧, 徽, 徽, 徽, 徽]
//   行2  卡6-11   [徽, ✧, 徽, 徽, 空, 徽]
//   行3  卡12-17  [徽, 徽, 徽, 徽, 徽, 徽]
//   行4  卡18-23  [徽, ✧, 徽, 徽, ✧, 徽]
//   行5  卡24-29  [徽, ✧, 徽, 徽, 徽, 徽]
// ⭐ 明显嫌疑：**每行第 2 列（x=324）都是 ✧** —— 4 行命中 4 枚。
//   ⛔ 但**卡 22（行 4 第 5 列，x=942）打破它**，而卡 10（行 2 第 5 列）又是空的。
//   ⇒ 「第 2 列」和「第 5 列」可能**不是同一种规律**，也可能是两个不同机制。
//
// 本步要回答三问：
//   ① ✧ 到底挂在**哪张卡**上？（把卡名一并读出来，别只报序号）
//   ② 那个 x=942 位置的卡 22 是**同一枚 ✧** 还是另一种？（比 SVG path）
//   ③ 卡 10 的**空槽位**到底是什么？它是「没有模型」还是「有但没渲染出来」？
//      ⇒ 判据：看那张卡有没有**别的**模型信息（比如详情浮层里的「首选推荐模型」）。
//
// ⚠️ 方法纪律：
//   · **DOM 总数**（不过滤可见性）—— DB 已经栽过这一回；
//   · **按 x 分桶**报数，别只按序号；
//   · 滚动后再采一轮，看分布**是否随加载变化**（卡 24-29 那一屏很可能还没铺满）。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;
const out = {};

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
await page.waitForTimeout(4000);

const scan = async (标签) => page.evaluate((tag) => {
  const D = [...document.querySelectorAll('button[aria-label="详情"]')];
  const rows = [];
  for (let i = 0; i < D.length; i += 1) {
    let card = null;
    for (let p = D[i].parentElement, j = 0; p && j < 8; p = p.parentElement, j += 1) {
      const r = p.getBoundingClientRect();
      if (r.width > 150 && r.height > 150) { card = p; break; }
    }
    if (!card) continue;
    const cr = card.getBoundingClientRect();
    // 卡名：卡片里最长的那行文字（排除按钮）
    const texts = [...card.querySelectorAll('*')].filter((e) => e.children.length === 0 && (e.innerText || '').trim())
      .map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim());
    const 名 = texts.sort((a, b2) => b2.length - a.length)[0] || '';
    // 左上角那一格
    const 左上 = [...card.querySelectorAll('*')].filter((e) => {
      const r = e.getBoundingClientRect();
      return r.width > 0 && r.height > 0 && r.width < 70 && r.height < 70
        && r.x >= cr.x - 2 && r.x <= cr.x + 60 && r.y >= cr.y - 2 && r.y <= cr.y + 60;
    });
    let 类型 = '空槽位'; let 徽标文字 = ''; let path = ''; let 宽 = 0;
    for (const e of 左上) {
      const r = e.getBoundingClientRect();
      if (e.tagName === 'BUTTON') {
        宽 = Math.max(宽, r.width);
        if ((e.innerText || '').trim()) { 类型 = '徽标'; 徽标文字 = (e.innerText || '').replace(/\s+/g, ' ').trim(); }
        else { 类型 = 'X入口'; const pth = e.querySelector('path'); path = pth ? (pth.getAttribute('d') || '').slice(0, 30) : ''; }
      }
    }
    rows.push({ 序: i, x: Math.round(cr.x), y: Math.round(cr.y), 名: 名.slice(0, 22), 类型, 徽标文字, path, 宽 });
  }
  return { 标签: tag, 卡数: rows.length, rows };
}, 标签);

out.首屏 = await scan('首屏');
LOG(`首屏卡数=${out.首屏.卡数}`);
const byX = {};
for (const r of out.首屏.rows) { (byX[r.x] ||= []).push(r.类型); }
LOG('\n⭐ 按 x 分桶:');
for (const x of Object.keys(byX).sort((a, b2) => a - b2)) LOG(`  x=${x}: ${byX[x].join(' ')}`);
LOG('\n✧ 入口的卡:');
for (const r of out.首屏.rows.filter((x) => x.类型 === 'X入口')) LOG(`  序${r.序} @(${r.x},${r.y}) 「${r.名}」 path=${r.path}`);
LOG('\n空槽位的卡:');
for (const r of out.首屏.rows.filter((x) => x.类型 === '空槽位')) LOG(`  序${r.序} @(${r.x},${r.y}) 「${r.名}」`);
LOG('\n徽标种类统计:');
const mm = {};
for (const r of out.首屏.rows.filter((x) => x.类型 === '徽标')) mm[r.徽标文字] = (mm[r.徽标文字] || 0) + 1;
LOG(`  ${JSON.stringify(mm)}`);

// ⭐ 滚到底再采一轮：分布会不会变（=「按位置」还是「按内容」）
LOG('\n══════════ 滚到底再采一轮 ══════════');
await page.evaluate(() => {
  const v = [...document.querySelectorAll('.mantine-ScrollArea-viewport')].find((e) => e.scrollHeight > 600);
  if (v) v.scrollTop = v.scrollHeight;
});
await page.waitForTimeout(3000);
out.底部 = await scan('底部');
LOG(`底部卡数=${out.底部.卡数}`);
const byX2 = {};
for (const r of out.底部.rows) { (byX2[r.x] ||= []).push(r.类型); }
LOG('⭐ 按 x 分桶:');
for (const x of Object.keys(byX2).sort((a, b2) => a - b2)) LOG(`  x=${x}: ${byX2[x].join(' ')}`);
LOG('\n✧ 入口的卡:');
for (const r of out.底部.rows.filter((x) => x.类型 === 'X入口')) LOG(`  序${r.序} @(${r.x},${r.y}) 「${r.名}」 path=${r.path}`);
LOG('\n空槽位的卡:');
for (const r of out.底部.rows.filter((x) => x.类型 === '空槽位')) LOG(`  序${r.序} @(${r.x},${r.y}) 「${r.名}」`);

await writeFile(new URL('./batchDC0.json', import.meta.url), JSON.stringify(out, null, 2));
LOG('\n=== 已写 tools/batchDC0.json ===');
await browser.close();

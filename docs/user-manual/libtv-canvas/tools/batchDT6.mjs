// Batch DT-6：重拍 5 行模型的下拉 —— 这次要**五行都在画面里**。
//
// ⛔ DT-b 为什么不能用：那张卡在广场**第二行**，下拉从按钮向下展开，
//    第五行「Seedream 5.0」被**广场面板底边**裁掉了。
//    文字读数是 5 行、图上只有 4 行 ⇒ **名不副实的图比没有图更糟**，重拍。
//
// ⭐ 解法：把目标卡滚到**第一行**。面板可视区约 700px 高，
//    第一行的卡（CSS y ≈ 300）下拉往下展开 5 行（≈ 200px）到 y ≈ 500 ⇒ 完全在面板内。
//
// ⛔ 全程只 mouse.move + 设置 scrollTop，**不点击任何东西**。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;
const 目标 = '一键生成人物多视图';
const out = { 目标, 尝试: [] };
const SAVE = () => writeFileSync(new URL('./batchDT6.json', import.meta.url), JSON.stringify(out, null, 2));

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

// ---- 把目标卡滚到第一行（CSS y 中心 ≈ 330）----
const 滚到位 = await page.evaluate((名) => {
  const e = [...document.querySelectorAll('p,h3,span,div')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === 名 && x.children.length === 0);
  if (!e) return { 找到: false };
  let c = e; for (let i = 0; i < 8 && c; i += 1) { const r = c.getBoundingClientRect(); if (r.width >= 150 && r.width <= 340 && r.height >= 180 && r.height <= 460) break; c = c.parentElement; }
  const v = [...document.querySelectorAll('.mantine-ScrollArea-viewport')].find((x) => x.scrollHeight > 600);
  if (!v) return { 找到: true, 滚动容器: false };
  const cr = c.getBoundingClientRect();
  const 视 = v.getBoundingClientRect();
  const 当前y = cr.y - 视.y;
  const 目标y = 60;                      // 卡片顶边离面板顶 60px ⇒ 在第一行
  v.scrollTop += (当前y - 目标y);
  return { 找到: true, 原来y: Math.round(当前y), 调整: 当前y - 目标y };
}, 目标);
LOG(`滚动定位: ${JSON.stringify(滚到位)}`);
await page.waitForTimeout(1800);

// ---- 找该卡上的 ✧ 并 hover ----
const X = await page.evaluate((名) => {
  const e = [...document.querySelectorAll('p,h3,span,div')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === 名 && x.children.length === 0);
  if (!e) return null;
  let c = e; for (let i = 0; i < 8 && c; i += 1) { const r = c.getBoundingClientRect(); if (r.width >= 150 && r.width <= 340 && r.height >= 180 && r.height <= 460) break; c = c.parentElement; }
  const cr = c.getBoundingClientRect();
  const 卡中心 = [Math.round(cr.x + cr.width / 2), Math.round(cr.y + cr.height / 2)];
  const bs = [...c.querySelectorAll('button')].filter((b) => { const r = b.getBoundingClientRect(); return r.width >= 20 && r.width <= 28 && r.height >= 20 && r.height <= 28 && (b.innerText || '').trim() === ''; });
  if (!bs.length) return { 卡中心, 无X: true, 卡box: [Math.round(cr.x), Math.round(cr.y), Math.round(cr.width), Math.round(cr.height)] };
  const r = bs[bs.length - 1].getBoundingClientRect();
  return { 卡中心, X: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 卡box: [Math.round(cr.x), Math.round(cr.y), Math.round(cr.width), Math.round(cr.height)] };
}, 目标);
LOG(`✧ 定位: ${JSON.stringify(X)}`);
if (!X) { LOG('⛔ 目标卡不在 DOM'); SAVE(); await browser.close(); process.exit(0); }
if (!X.X) { LOG(`⛔ 目标卡上没有 ✧：${JSON.stringify(X)}`); SAVE(); await browser.close(); process.exit(0); }

// ⭐ 先 hover 整张卡让 ✧ 显形，再精确 hover ✧
await page.mouse.move(X.卡中心[0], X.卡中心[1]);
await page.waitForTimeout(900);
await page.mouse.move(X.X[0], X.X[1]);
await page.waitForTimeout(1800);

const 下拉 = await page.evaluate(() => {
  const 浮 = [...document.querySelectorAll('div')].filter((e) => {
    const t = (e.innerText || '').replace(/\s+/g, ' ');
    const s = getComputedStyle(e);
    return /全部适配模型/.test(t) && t.length < 200 && s.visibility !== 'hidden' && +s.opacity > 0.5;
  });
  if (!浮.length) return null;
  const 详 = 浮.sort((a, b) => (b.innerText || '').length - (a.innerText || '').length)[0];
  const r = 详.getBoundingClientRect();
  const 叶 = [...详.querySelectorAll('*')].filter((e) => { const t = (e.innerText || '').replace(/\s+/g, ' ').trim(); return t && t.length <= 40 && e.children.length === 0; })
    .map((e) => { const b = e.getBoundingClientRect(); return { 文字: (e.innerText || '').replace(/\s+/g, ' ').trim(), y: Math.round(b.y), 底: Math.round(b.bottom) }; });
  // 面板可视区
  const v = [...document.querySelectorAll('.mantine-ScrollArea-viewport')].find((x) => x.scrollHeight > 600);
  const 视 = v ? v.getBoundingClientRect() : null;
  return { 全文: (详.innerText || '').replace(/\n+/g, ' | '), 盒子: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 行: 叶, 面板: 视 ? [Math.round(视.y), Math.round(视.bottom)] : null };
});
out.下拉 = 下拉;
if (!下拉) { LOG('⛔ 没出下拉'); SAVE(); await browser.close(); process.exit(0); }
LOG(`\n下拉全文: ${下拉.全文}`);
LOG(`下拉盒子 y=${下拉.盒子[1]} 高=${下拉.盒子[3]} | 面板可视 ${JSON.stringify(下拉.面板)}`);
for (const r of 下拉.行) LOG(`   ${r.文字}  y=${r.y}~${r.底}`);
const 溢出 = 下拉.面板 ? 下拉.行.filter((r) => r.底 > 下拉.面板[1]) : [];
LOG(`\n⭐ 被面板底边裁掉的行: ${溢出.length} ${溢出.length ? JSON.stringify(溢出.map((r) => r.文字)) : '⇒ ✅ 五行都在画面里'}`);
await shot(page, 'DT-c-五模型下拉完整.png');
LOG('📸 DT-c');
out.最终节点数 = await page.evaluate(() => document.querySelectorAll('[data-id]').length);
SAVE();
await browser.close();
LOG('\n=== 已写 tools/batchDT6.json ===');

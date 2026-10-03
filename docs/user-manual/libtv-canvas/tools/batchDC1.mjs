// Batch DC-1：给那三种东西配上**卡名**，找真正的规律。
//
// DC-0 已经证伪了「每行第 2 列」这个假设：
//   首屏 30 张：x=324 那列 5 张里 4 枚 X；x=933 那列也有 1 枚。
//   底部 54 张：x=324 那列 9 张里 **7 枚 X 但第 1 张是徽标**；x=1136 那列**也冒出 1 枚 X**（序 35）。
//   ⇒ **位置不是规律。**（又一次「坐标规律」假说被数据推翻）
//
// ⭐ DC-0 还挖到一条硬线索：那个「空槽位」的卡，**徽标文字读出来是 `Qwen Image`** ——
//   说明它**是有模型的**，只是那一格没渲染出 button。
//   ⚠️ 但这也可能是**我的取名逻辑串了**（最长文字未必是徽标）。
//   ⇒ 本步用**几何**判定：徽标 button 必须**精确落在** card.x+9, card.y+9。
//     绝不信「最长文字」。
//
// 本步两问：
//   ① 每张卡左上角那一格的**几何 + 徽标文字**，并给**卡名**（取预览图下方的名称行）；
//   ② ⭐ **`✧` 入口和「多模型」有没有关系** —— 假设：一张卡能用多个模型时
//      才出现这个「全部适配模型」入口；只有单模型时直接显示徽标。
//      验证法：点开 `✧` 卡，**读那个浮层里列了几个模型**（1 个 vs 2 个），
//      再和「只有 1 个模型」的那些卡对照。
//      ⚠️ 浮层是 hover 才出，**必须 hover 后再读**（DB-6 已坐实 257ms 出现）。
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

// ---------- ① 几何判定 + 卡名 ----------
out.首屏 = await page.evaluate(() => {
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
    // ⭐ 几何判定：徽标/入口必须精确落在 card 左上 +9
    const gx = cr.x + 9; const gy = cr.y + 9;
    let 类型 = '空'; let 徽标文字 = ''; let 实测位 = null;
    for (const e of card.querySelectorAll('button')) {
      const r = e.getBoundingClientRect();
      if (Math.abs(r.x - gx) <= 3 && Math.abs(r.y - gy) <= 3) {
        实测位 = [Math.round(r.x), Math.round(r.y)];
        if ((e.innerText || '').trim()) { 类型 = '徽标'; 徽标文字 = (e.innerText || '').replace(/\s+/g, ' ').trim(); }
        else 类型 = 'X入口';
        break;
      }
    }
    // 卡名：预览图**下方**那一行（y 在卡片下半部）
    const 名候选 = [...card.querySelectorAll('*')].filter((e) => {
      if (e.children.length) return false;
      const r = e.getBoundingClientRect();
      const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
      return t && r.y > cr.y + cr.height * 0.7 && t.length <= 30;
    }).map((e) => { const r = e.getBoundingClientRect(); return { 文字: (e.innerText || '').replace(/\s+/g, ' ').trim(), y: Math.round(r.y) }; })
      .sort((a, b2) => a.y - b2.y);
    rows.push({ 序: i, x: Math.round(cr.x), y: Math.round(cr.y), 名: 名候选[0]?.文字 || '(读不到)', 名候选数: 名候选.length, 类型, 徽标文字, 实测位 });
  }
  return { 卡数: rows.length, rows };
});
LOG(`首屏卡数=${out.首屏.卡数}`);
LOG('\n序号 | 类型 | 徽标 | 卡名');
for (const r of out.首屏.rows) LOG(`  ${String(r.序).padStart(2)} | ${r.类型.padEnd(4)} | ${(r.徽标文字 || '-').padEnd(13)} | ${r.名}`);

const byX = {};
for (const r of out.首屏.rows) { (byX[r.x] ||= []).push(r.类型); }
LOG('\n按 x 分桶:');
for (const x of Object.keys(byX).sort((a, b2) => a - b2)) LOG(`  x=${x}: ${byX[x].join(' ')}`);

// ---------- ② hover 若干张，看浮层列几个模型 ----------
LOG('\n══════════ ② hover 看浮层列几个模型 ══════════');
const picks = await page.evaluate(() => {
  const D = [...document.querySelectorAll('button[aria-label="详情"]')];
  const X = []; const M = [];
  for (let i = 0; i < D.length && (X.length < 4 || M.length < 2); i += 1) {
    let card = null;
    for (let p = D[i].parentElement, j = 0; p && j < 8; p = p.parentElement, j += 1) {
      const r = p.getBoundingClientRect();
      if (r.width > 150 && r.height > 150) { card = p; break; }
    }
    if (!card) continue;
    const cr = card.getBoundingClientRect();
    if (cr.y < 0 || cr.y > 700) continue;
    const gx = cr.x + 9; const gy = cr.y + 9;
    for (const e of card.querySelectorAll('button')) {
      const r = e.getBoundingClientRect();
      if (Math.abs(r.x - gx) <= 3 && Math.abs(r.y - gy) <= 3) {
        if (!(e.innerText || '').trim() && X.length < 4) X.push([Math.round(r.x + 12), Math.round(r.y + 12), `序${i}`]);
        else if ((e.innerText || '').trim() && M.length < 2) M.push([Math.round(r.x + 12), Math.round(r.y + 12), `序${i}:${(e.innerText || '').trim()}`]);
        break;
      }
    }
  }
  return { X, M };
});
LOG(`X入口样本: ${JSON.stringify(picks.X)}`);
LOG(`徽标样本: ${JSON.stringify(picks.M)}`);

const readPanel = async (pt) => {
  await page.mouse.move(5, 400); await page.waitForTimeout(500);
  await page.mouse.move(pt[0], pt[1]); await page.waitForTimeout(1200);
  return page.evaluate(() => {
    const vis = (e) => { if (!e) return false; const r = e.getBoundingClientRect(); const c = getComputedStyle(e); return r.width > 0 && r.height > 0 && c.visibility !== 'hidden' && +c.opacity > 0; };
    const hit = [...document.querySelectorAll('body *')].filter((e) => e.tagName !== 'SCRIPT' && vis(e) && /全部适配模型/.test(e.textContent || '') && e.children.length === 0)[0];
    if (!hit) return { 有面板: false };
    let panel = hit.parentElement;
    for (let i = 0; i < 5; i += 1) { const b = panel.getBoundingClientRect(); if (b.width > 150 && b.height > 60) break; panel = panel.parentElement; }
    const 条目 = [...panel.querySelectorAll('*')].filter((e) => e.children.length === 0 && (e.innerText || '').trim() && (e.innerText || '').trim() !== '全部适配模型')
      .map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim());
    return { 有面板: true, 模型数: 条目.length, 模型: [...new Set(条目)] };
  });
};

out.面板读数 = [];
for (const pt of [...picks.X, ...picks.M]) {
  const r = await readPanel(pt);
  out.面板读数.push({ 点: pt[2], ...r });
  LOG(`  ${pt[2].padEnd(18)} → ${r.有面板 ? `面板列出 ${r.模型数} 个模型: ${JSON.stringify(r.模型)}` : '⛔ 没出面板'}`);
}

await writeFile(new URL('./batchDC1.json', import.meta.url), JSON.stringify(out, null, 2));
LOG('\n=== 已写 tools/batchDC1.json ===');
await browser.close();

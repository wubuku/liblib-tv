// Batch DI-2：重跑「全部适配模型」大采样 —— 用 DI-1 验证过的判据。
//
// DI-1 查清了「视口内 0」的成因链：
//   · 详情按钮**全部 `vis=false`**（靠 hover 显形）—— 所以**绝不能用按钮的可见性判卡**；
//   · 卡容器是**第 3 层** `[…,191,302]`，它在祖先链上是 `vis=true`；
//   · 滚到中段时卡容器 y = **-935**（在视口外），滚回顶部才是 **197**。
// ⇒ 采样流程必须是：**切分类 → 等 → 滚回顶部 → 等 → 才取卡**。
//   DI-0 之所以读到 0，是在同一次 evaluate 里连着 collect 两次、又没重新等渲染。
//
// 本步只做一件事：跨多个分类，每张 `✧` 入口卡都悬停读一次，取模型数最大值。
// ⭐ 每张读两次：第一次没出面板就重试（DB 那轮 6 次里有 1 次偶发漏读）。
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

// ⭐ 卡容器 = 详情按钮往上第 3 层（DI-1 实测 191×302），**不判按钮可见性**
const cards = () => page.evaluate(() => {
  const modals = [...document.querySelectorAll('.mantine-Modal-inner')].filter((e) => { const r = e.getBoundingClientRect(); const c = getComputedStyle(e); return r.width > 0 && r.height > 0 && +c.opacity > 0; });
  if (!modals.length) return [];
  const root = modals.sort((a, b) => { const ra = a.getBoundingClientRect(); const rb = b.getBoundingClientRect(); return rb.width * rb.height - ra.width * ra.height; })[0];
  const out = [];
  const seen = new Set();
  for (const D of root.querySelectorAll('button[aria-label="详情"]')) {
    // ⭐⭐ DI-1 实测：真卡是**第 3 层**（191×302），但**左上角按钮在第 2 层**（183×245）里。
    //    上一版用第 3 层去算落点（card.x+9）⇒ 永远对不上 ⇒ 「左上格 0 个」。
    //    ⇒ **两层都要拿**：第 2 层用来定位按钮，第 3 层用来当「整张卡」。
    let L2 = null; let L3 = null;
    for (let p = D.parentElement, j = 0; p && j < 6; p = p.parentElement, j += 1) {
      const r = p.getBoundingClientRect();
      if (!L2 && r.width > 150 && r.width < 260 && r.height > 200 && r.height < 260) L2 = p;
      if (!L3 && r.width > 150 && r.width < 260 && r.height > 260) { L3 = p; break; }
    }
    if (!L2 || !L3) continue;
    const cr2 = L2.getBoundingClientRect(); const cr3 = L3.getBoundingClientRect();
    if (cr3.y < 0 || cr3.y > 620) continue;
    const k = `${Math.round(cr3.x)},${Math.round(cr3.y)}`;
    if (seen.has(k)) continue; seen.add(k);
    let 格 = null;
    for (const b of L2.querySelectorAll('button')) {
      const r = b.getBoundingClientRect();
      if (Math.abs(r.x - (cr2.x + 9)) <= 3 && Math.abs(r.y - (cr2.y + 9)) <= 3) { 格 = { 徽标: (b.innerText || '').trim() || null, 中心: [Math.round(r.x + 12), Math.round(r.y + 12)] }; break; }
    }
    out.push({ 格, y: Math.round(cr3.y), 卡名: (L3.innerText || '').split('\n')[0].slice(0, 16) });
  }
  return out;
});

const 读 = async (pt) => {
  await page.mouse.move(5, 400); await page.waitForTimeout(300);
  await page.mouse.move(pt[0], pt[1]); await page.waitForTimeout(950);
  return page.evaluate(() => {
    const vis = (e) => { if (!e) return false; const q = e.getBoundingClientRect(); const c = getComputedStyle(e); return q.width > 0 && q.height > 0 && c.visibility !== 'hidden' && +c.opacity > 0; };
    const hit = [...document.querySelectorAll('body *')].filter((e) => e.tagName !== 'SCRIPT' && e.tagName !== 'STYLE' && vis(e) && /全部适配模型/.test(e.textContent || '') && e.children.length === 0)[0];
    if (!hit) return { 有面板: false };
    let panel = hit.parentElement;
    for (let k = 0; k < 5; k += 1) { const b = panel.getBoundingClientRect(); if (b.width > 150 && b.height > 60) break; panel = panel.parentElement; }
    const 条 = [...panel.querySelectorAll('*')].filter((e) => e.children.length === 0 && (e.innerText || '').trim() && (e.innerText || '').trim() !== '全部适配模型')
      .map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim());
    return { 有面板: true, 模型数: [...new Set(条)].length, 模型: [...new Set(条)] };
  });
};

out.采样 = [];
for (const 名 of ['推荐', '摄影写真', '电商营销', '动漫游戏', '建筑及室内设计']) {
  const ok = await page.evaluate((n) => {
    const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === n);
    if (!b) return false; b.click(); return true;
  }, 名);
  if (!ok) { LOG(`⛔ 找不到「${名}」`); continue; }
  await page.waitForTimeout(2600);
  // ⭐ 切分类后**先滚回顶部再等**
  await page.evaluate(() => { const v = [...document.querySelectorAll('.mantine-ScrollArea-viewport')].find((e) => e.scrollHeight > 600); if (v) v.scrollTop = 0; });
  await page.waitForTimeout(2500);
  const c = await cards();
  const 入口 = c.filter((k) => k.格 && !k.格.徽标);
  const 徽标 = c.filter((k) => k.格 && k.格.徽标);
  LOG(`\n【${名}】视口内卡 ${c.length} 张：入口 ${入口.length} / 徽标 ${徽标.length}`);
  for (const k of 入口) {
    let r = await 读(k.格.中心);
    let 重试 = false;
    if (!r.有面板) { await page.waitForTimeout(500); r = await 读(k.格.中心); 重试 = true; }
    out.采样.push({ 分类: 名, 卡名: k.卡名, 重试, ...r });
    LOG(`   入口「${k.卡名}」${重试 ? '(重试后)' : ''} → ${r.有面板 ? `${r.模型数} 个: ${JSON.stringify(r.模型)}` : '⛔ 两次都无面板'}`);
  }
  await writeFile(new URL('./batchDI2.json', import.meta.url), JSON.stringify(out, null, 2));
}

const 全 = out.采样.filter((x) => x.有面板);
const 数 = 全.map((x) => x.模型数).sort((a, b) => a - b);
LOG(`\n══════════ 汇总 ══════════`);
LOG(`采样 ${out.采样.length} 张入口卡，出面板 ${全.length} 张（重试后仍无 ${out.采样.length - 全.length} 张）`);
LOG(`模型数分布: ${JSON.stringify(数)}`);
LOG(`⭐ 上限（本轮观测）: ${数.length ? Math.max(...数) : '无'}`);
LOG(`出现过的模型: ${JSON.stringify([...new Set(全.flatMap((x) => x.模型))])}`);
await shot(page, 'DI-b-采样中的一屏.png');
LOG('📸 DI-b');
await writeFile(new URL('./batchDI2.json', import.meta.url), JSON.stringify(out, null, 2));
LOG('\n=== 已写 tools/batchDI2.json ===');
await browser.close();

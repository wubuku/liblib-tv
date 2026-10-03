// Batch DG-2：别再猜「数字长什么样」—— 直接把一张卡的**下半部分完整 dump 出来**。
//
// DG-1 读数「带漏斗图标的数字 0 个」**不能用**：
//   判据是「图标 svg 的 x 在数字左侧 40px 内，且**中心 y 差 < 14px**」——
//   ⛔ 这个 y 对齐条件是我拍脑袋定的，很可能卡片里那枚图标的基线根本没和数字对齐。
// ⇒ **负读数 + 拍脑袋的判据 = 没测到。**
//
// 本步：⭐ **不设任何过滤**，把**一张卡**里所有可见的叶子元素
//   （按 y 排序）连同 rect 全部打印出来 —— 让「数字旁边到底有什么」自己显形。
//   读完再决定判据怎么写。**先看，再判。**
//
// 同时把 DG-1 的另两条确认一下：
//   · 「键名与具体数值同段 = 0 条」—— 但那次**数字列表是空的**（判据没抓到卡），
//     拿空列表去搜，当然什么都搜不到 ⇒ **这条也作废**。
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

// ---------- A 完整 dump 一张卡（不过滤）----------
out.整卡 = await page.evaluate(() => {
  const vis = (e) => { if (!e) return false; const r = e.getBoundingClientRect(); const c = getComputedStyle(e); return r.width > 0 && r.height > 0 && c.visibility !== 'hidden' && +c.opacity > 0; };
  const modals = [...document.querySelectorAll('.mantine-Modal-inner')].filter(vis);
  if (!modals.length) return { 找到: false };
  const root = modals.sort((a, b) => { const ra = a.getBoundingClientRect(); const rb = b.getBoundingClientRect(); return rb.width * rb.height - ra.width * ra.height; })[0];
  // 找第 2 张卡（有徽标+有详情按钮的）
  const Ds = [...root.querySelectorAll('button[aria-label="详情"]')];
  let card = null;
  for (const D of Ds) {
    for (let p = D.parentElement, j = 0; p && j < 8; p = p.parentElement, j += 1) { const r = p.getBoundingClientRect(); if (vis(p) && r.width > 150 && r.height > 150 && r.y > 0 && r.y < 700) { card = p; break; } }
    if (card) break;
  }
  if (!card) return { 找到: false };
  const cr = card.getBoundingClientRect();
  const leaves = [];
  for (const e of card.querySelectorAll('*')) {
    if (!vis(e)) continue;
    // ⭐ 只取"叶子"（没有子元素）以及 svg/path
    if (e.children.length && e.tagName.toLowerCase() !== 'svg') continue;
    const r = e.getBoundingClientRect();
    const ds = {}; for (const a of e.attributes) if (a.name.startsWith('data-')) ds[a.name] = a.value;
    leaves.push({
      tag: e.tagName.toLowerCase(),
      文字: (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 26) || null,
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      中心y: Math.round(r.y + r.height / 2),
      aria: e.getAttribute('aria-label'), title: e.getAttribute('title'),
      path: (e.getAttribute('d') || '').slice(0, 50) || null,
      data: ds,
      class: (e.className || '').toString().slice(0, 46),
    });
  }
  leaves.sort((a, b) => a.rect[1] - b.rect[1] || a.rect[0] - b.rect[0]);
  return { 找到: true, 卡片rect: [Math.round(cr.x), Math.round(cr.y), Math.round(cr.width), Math.round(cr.height)], 叶子数: leaves.length, leaves };
});
if (!out.整卡.找到) { LOG('⛔ 找不到视口内的卡片'); } else {
  LOG(`卡片 ${JSON.stringify(out.整卡.卡片rect)}，可见叶子 ${out.整卡.叶子数} 个，按 y 排序：`);
  for (const l of out.整卡.leaves) {
    LOG(`  y=${String(l.rect[1]).padStart(4)} 中心y=${String(l.中心y).padStart(4)} <${l.tag}> ${JSON.stringify(l.rect)} 「${l.文字 || ''}」 aria=${l.aria} title=${l.title}${l.path ? ` path=${l.path}…` : ''} ${l.class}`);
  }
  await shot(page, 'DG-b-整卡元素全景.png', { clip: { x: out.整卡.卡片rect[0] - 10, y: out.整卡.卡片rect[1] - 10, width: out.整卡.卡片rect[2] + 20, height: out.整卡.卡片rect[3] + 20 } });
  LOG('📸 DG-b');
}

await writeFile(new URL('./batchDG2.json', import.meta.url), JSON.stringify(out, null, 2));
LOG('\n=== 已写 tools/batchDG2.json ===');
await browser.close();

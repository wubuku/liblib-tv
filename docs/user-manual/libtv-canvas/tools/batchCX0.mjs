// Batch CX-0：「详情」按钮数量之谜 —— 假设是**虚拟滚动**。
//
// 线索（三次读数互相打架）：
//   · 某批次读到 **6 枚** `aria="详情"`
//   · CW-0 在不滚动的情况下读到 **1 枚**，而收藏星读到 30 枚
//   · CW-0 读到的 30 张卡坐标是 y = 210 / 524 / 838 / 1152 / 1465 ×6 列
//     ⇒ 只有 y ≤ 810 的**前 3 行**在 810px 视口内，**后 27 张全在视口外**
//
// ⭐ 假设：**列表是虚拟滚动的** —— 视口外的卡片只渲染了「壳」，
// 悬停才显形的那两枚（☆ 收藏 / ⤢ 详情）压根没进 DOM。
// 而收藏星 30 枚全在，说明**收藏星是常驻渲染**（`opacity:1`），
// **详情是 `opacity:0` 悬停才显形** ⇒ 两者的渲染条件不同。
//
// 本步：滚 → 读 → 再滚 → 再读，看「详情」按钮数是否随滚动出现。
// ⛔ 全程只读 + 滚动，不点任何卡片（点卡片 = 往画布加节点）。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;

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

await page.evaluate(() => { const b = document.querySelector('[data-sidebar-btn="open-asset"]'); b.click(); });
await page.waitForTimeout(1800);
await page.evaluate(() => [...document.querySelectorAll('button')].find((b) => (b.innerText || '').replace(/\s+/g, ' ').trim().startsWith('风格库'))?.click());
await page.waitForTimeout(2800);

// ⭐ 广场的滚动容器是谁？
const scroller = await page.evaluate(() => {
  const cands = [];
  for (const e of document.querySelectorAll('*')) {
    const s = getComputedStyle(e);
    if (!/(auto|scroll)/.test(s.overflowY) && !/(auto|scroll)/.test(s.overflow)) continue;
    const r = e.getBoundingClientRect();
    if (r.width < 300 || r.height < 200) continue;
    cands.push({ sel: e.tagName.toLowerCase() + '.' + (e.className || '').toString().slice(0, 50), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], scrollH: e.scrollHeight, clientH: e.clientHeight, overflowY: s.overflowY });
  }
  return cands;
});
LOG(`=== 可滚动容器（宽≥300 高≥200 且 overflow 含 auto/scroll）${scroller.length} 个 ===`);
for (const c of scroller) LOG(`  ${JSON.stringify(c)}`);

const counts = (page) => page.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && +s.opacity > 0; };
  const all = [...document.querySelectorAll('button')];
  const det = all.filter((b) => b.getAttribute('aria-label') === '详情');
  const fav = all.filter((b) => /^(收藏|取消收藏)$/.test(b.getAttribute('aria-label') || ''));
  const inVP = (b) => { const r = b.getBoundingClientRect(); return r.y >= 0 && r.y < 810 && r.x >= 0 && r.x < 1440; };
  // 徽标（有文字的那些 24×24）
  const badge = all.filter((b) => { const r = b.getBoundingClientRect(); return vis(b) && r.width === 24 && r.height === 24 && (b.innerText || '').trim().length > 2; });
  return {
    详情总数: det.length,
    详情在视口内: det.filter(inVP).length,
    详情位置: det.map((b) => { const r = b.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y)]; }),
    收藏星总数: fav.length,
    收藏星在视口内: fav.filter(inVP).length,
    徽标总数: badge.length,
    徽标在视口内: badge.filter(inVP).length,
    徽标文字: [...new Set(badge.map((b) => (b.innerText || '').trim()))].slice(0, 8),
    滚动位置: [...document.querySelectorAll('*')].filter((e) => { const s = getComputedStyle(e); return /(auto|scroll)/.test(s.overflowY) && e.scrollHeight > e.clientHeight + 20 && e.getBoundingClientRect().height > 200; }).map((e) => ({ top: Math.round(e.scrollTop), h: e.scrollHeight, c: e.clientHeight })).slice(0, 3),
  };
});

const out = { scroller, steps: [] };
const step = async (label) => {
  const c = await counts(page);
  out.steps.push({ label, ...c });
  LOG(`\n▸ ${label}`);
  LOG(`   详情 ${c.详情总数} 枚（视口内 ${c.详情在视口内}）位置=${JSON.stringify(c.详情位置)}`);
  LOG(`   收藏星 ${c.收藏星总数} 枚（视口内 ${c.收藏星在视口内}）`);
  LOG(`   徽标 ${c.徽标总数} 枚（视口内 ${c.徽标在视口内}）文字=${JSON.stringify(c.徽标文字)}`);
  LOG(`   滚动容器 scrollTop=${JSON.stringify(c.滚动位置)}`);
  return c;
};

await step('① 刚进广场，未滚动');

// ---- 滚到中段 -------------------------------------------------------------------
const scrolled = await page.evaluate(() => {
  for (const e of document.querySelectorAll('*')) {
    const s = getComputedStyle(e);
    if (!/(auto|scroll)/.test(s.overflowY)) continue;
    if (e.scrollHeight <= e.clientHeight + 20) continue;
    const r = e.getBoundingClientRect();
    if (r.height < 200 || r.width < 300) continue;
    e.scrollTop = Math.floor(e.scrollHeight / 2);
    return { top: e.scrollTop, h: e.scrollHeight, c: e.clientHeight };
  }
  return null;
});
LOG(`\n滚到中段: ${JSON.stringify(scrolled)}`);
await page.waitForTimeout(1600);
await step('② 滚到中段');

await page.evaluate(() => {
  for (const e of document.querySelectorAll('*')) {
    const s = getComputedStyle(e);
    if (!/(auto|scroll)/.test(s.overflowY)) continue;
    if (e.scrollHeight <= e.clientHeight + 20) continue;
    const r = e.getBoundingClientRect();
    if (r.height < 200 || r.width < 300) continue;
    e.scrollTop = e.scrollHeight;
    return;
  }
});
await page.waitForTimeout(1800);
await step('③ 滚到底');

// ---- 悬停一张卡，看详情按钮是否出现 ---------------------------------------------
const hoverCard = await page.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && +s.opacity > 0; };
  const imgs = [...document.querySelectorAll('img')].filter((i) => { const r = i.getBoundingClientRect(); return vis(i) && r.y > 150 && r.y < 700 && r.width > 100; });
  if (!imgs.length) return null;
  const r = imgs[Math.floor(imgs.length / 2)].getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
});
LOG(`\n悬停中心卡: ${JSON.stringify(hoverCard)}`);
if (hoverCard) {
  await page.mouse.move(hoverCard[0], hoverCard[1]);
  await page.waitForTimeout(1100);
  await step('④ 悬停一张卡之后');
}

await writeFile(new URL('./batchCX0.json', import.meta.url), JSON.stringify(out, null, 2));
LOG('\n已写 tools/batchCX0.json');
await browser.close();

// Batch DG-3：容器取错了 —— 数字在卡片容器**之外**。
//
// DG-2 的 dump 很清楚：圈到的那块（183×245）里**只有 6 个叶子，全是图标，零个文字**。
// 而 DG-b 截图上能看到卡名 `Seedream 5.0 pro` 的**上半截在裁剪框之外**。
// ⇒ ⛔ **不是判据问题，是「卡片容器」圈小了** —— 数字和卡名在那块下面，
//    属于**另一个**兄弟容器（多半是同一条 grid item 里的第二个 div）。
//
// 本步：
//   ① ⭐ 从**详情按钮**往上枚举**每一层**祖先，打印每层的 rect ——
//      找出**哪一层才真正包住卡名和数字**（判据：那一层的 rect 高度 > 245）；
//   ② 找到对的容器后，在**它里面**按几何找「纯数字」；
//   ③ 再挖一次数据层（这次带着**真的数字列表**）。
//
// ⭐ 顺带记一条通用教训：DG-2 那个「零个文字元素」如果我直接写成
//   「卡面上没有卡名和数字」，就是**又一次拿错容器的阴性**。
//   图和 DOM 打架时，**先怀疑自己圈错了范围**。
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

// ---------- A 逐层祖先：找出真正包住卡名和数字的那一层 ----------
out.祖先 = await page.evaluate(() => {
  const vis = (e) => { if (!e) return false; const r = e.getBoundingClientRect(); const c = getComputedStyle(e); return r.width > 0 && r.height > 0 && c.visibility !== 'hidden' && +c.opacity > 0; };
  const modals = [...document.querySelectorAll('.mantine-Modal-inner')].filter(vis);
  if (!modals.length) return { 找到: false };
  const root = modals.sort((a, b) => { const ra = a.getBoundingClientRect(); const rb = b.getBoundingClientRect(); return rb.width * rb.height - ra.width * ra.height; })[0];
  // ⭐ 不预设 y 范围（上一轮就栽在这：预设 200~400，结果一枚都没命中）
  const D = [...root.querySelectorAll('button[aria-label="详情"]')].filter(vis)
    .sort((a, b) => { const ra = a.getBoundingClientRect(); const rb = b.getBoundingClientRect(); return ra.y - rb.y || ra.x - rb.x; })[0];
  if (!D) return { 找到: false };
  const 层 = [];
  for (let p = D, i = 0; p && i < 10; p = p.parentElement, i += 1) {
    const r = p.getBoundingClientRect();
    if (r.width > 1400) break;
    // ⭐ 这一层里有没有「纯数字」和「较长的文字」
    const 数字 = [...p.querySelectorAll('*')].filter((e) => e.children.length === 0 && vis(e) && /^\d+(\.\d+)?w?$/.test((e.innerText || '').trim())).map((e) => (e.innerText || '').trim());
    const 长文 = [...p.querySelectorAll('*')].filter((e) => e.children.length === 0 && vis(e) && (e.innerText || '').trim().length >= 4).map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30));
    层.push({
      i, tag: p.tagName.toLowerCase(),
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      子元素数: p.children.length,
      纯数字: 数字, 长文字: [...new Set(长文)].slice(0, 6),
      class: (p.className || '').toString().slice(0, 70),
    });
  }
  return { 找到: true, 详情按钮rect: (() => { const r = D.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })(), 层 };
});
if (!out.祖先.找到) { LOG('⛔ 找不到详情按钮'); } else {
  LOG(`详情按钮 @${JSON.stringify(out.祖先.详情按钮rect)}`);
  LOG('\n逐层祖先（找哪一层才包住卡名和数字）:');
  for (const l of out.祖先.层) {
    LOG(`  [${l.i}] <${l.tag}> ${JSON.stringify(l.rect)} 子${l.子元素数}个  纯数字=${JSON.stringify(l.纯数字)}`);
    LOG(`       长文字=${JSON.stringify(l.长文字)}`);
    LOG(`       ${l.class}`);
  }
  const 带数字 = out.祖先.层.filter((l) => l.纯数字.length);
  LOG(`\n⭐ 含「纯数字」的层: ${JSON.stringify(带数字.map((l) => [l.i, l.rect, l.纯数字]))}`);
  const 最佳 = 带数字.length ? 带数字.reduce((a, b) => (b.rect[3] > a.rect[3] ? b : a)) : null;
  if (最佳) {
    LOG(`⭐ 最佳容器 = 第 [${最佳.i}] 层 ${JSON.stringify(最佳.rect)}，数字 ${JSON.stringify(最佳.纯数字)}`);
    out.最佳 = 最佳;
    await shot(page, 'DG-c-正确的卡片容器.png', { clip: { x: 最佳.rect[0] - 8, y: 最佳.rect[1] - 8, width: 最佳.rect[2] + 16, height: 最佳.rect[3] + 16 } });
    LOG('📸 DG-c');
  } else LOG('  ⛔ 这一条链上没有任何层含纯数字 ⇒ 需要换个起点再查');
}

await writeFile(new URL('./batchDG3.json', import.meta.url), JSON.stringify(out, null, 2));
LOG('\n=== 已写 tools/batchDG3.json ===');
await browser.close();

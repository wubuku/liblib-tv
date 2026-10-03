// Batch DB-2：找「新功能：支持真人」标记 —— 换掉错的判据。
//
// DB-1 的读数：连续两次采样都是「详情=1 / scrollH=2265」，加载过程**没有变化**
//   ⇒ 不是「没加载完」，是**判据本身错了**。
// ⭐ 根因：`asset-library.md:46` 早就写着详情按钮和收藏星「**鼠标移上去才显形**」
//   （实测 `0 → 1`）。而我在 DB-0/DB-1 里用**可见性过滤**（opacity>0 且有面积）
//   去数它们 ⇒ **只有正被 hover 的那一张能数到**，其余全被判成「不可见」。
// ⇒ 「标记命中 0」是我的尺子坏了，不是产品没有。⭐ 这是本会话第四回栽在
//   「拿可见性当存在性」上（前三回：被遮住的文字 / 裁掉的选项 / 未选中的端口）。
//
// 本步两件事：
//   ① **用 DOM 总数重测广场规模**（不滤可见性），并报每枚的 rect/opacity
//      —— 顺便把「显形」这件事本身钉成读数。
//   ② ⭐⭐ 既然两枚按钮 hover 才显形，那枚引导标记**很可能也是 hover 才出现的**。
//      ⇒ 先把鼠标停在某张卡上，再去 DOM 里找它，并打出完整祖先链。
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
await page.waitForTimeout(3000);

// =============== ① 用 DOM 总数量广场规模 ===============
LOG('══════════ ① DOM 总数 vs 可见数（钉「显形」这件事）══════════');
out.规模 = await page.evaluate(() => {
  const vis = (e) => { if (!e) return false; const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && +s.opacity > 0; };
  const D = [...document.querySelectorAll('button[aria-label="详情"]')];
  const F = [...document.querySelectorAll('button[aria-label="收藏"],button[aria-label="取消收藏"]')];
  return {
    详情DOM总数: D.length, 详情可见数: D.filter(vis).length,
    收藏DOM总数: F.length, 收藏可见数: F.filter(vis).length,
    scrollH: [...document.querySelectorAll('.mantine-ScrollArea-viewport')].map((e) => e.scrollHeight),
    详情前6: D.slice(0, 6).map((e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], opacity: s.opacity, vis: vis(e) }; }),
    op分布: D.reduce((m, e) => { const o = getComputedStyle(e).opacity; m[o] = (m[o] || 0) + 1; return m; }, {}),
    父op分布: D.reduce((m, e) => { const o = getComputedStyle(e.parentElement || e).opacity; m[o] = (m[o] || 0) + 1; return m; }, {}),
  };
});
LOG(`详情 DOM总数=${out.规模.详情DOM总数} 可见=${out.规模.详情可见数}`);
LOG(`收藏 DOM总数=${out.规模.收藏DOM总数} 可见=${out.规模.收藏可见数}`);
LOG(`scrollH=${JSON.stringify(out.规模.scrollH)}`);
LOG(`⭐ 详情按钮自身 opacity 分布: ${JSON.stringify(out.规模.op分布)}`);
LOG(`⭐ 详情按钮父容器 opacity 分布: ${JSON.stringify(out.规模.父op分布)}`);
LOG(`前6枚: ${JSON.stringify(out.规模.详情前6, null, 1)}`);

// =============== ② hover 某张卡后找标记 ===============
LOG('\n══════════ ② hover 一张卡，再找标记 ══════════');
// 选第 2 张卡（不是第 1 张 —— 账本里标记出现在"第二张卡"上）
const target = await page.evaluate(() => {
  const vis = (e) => { if (!e) return false; const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && +s.opacity > 0; };
  const cands = [...document.querySelectorAll('button[aria-label="详情"]')].filter(vis);
  if (!cands.length) return null;
  const b = cands[Math.min(1, cands.length - 1)];
  const r = b.getBoundingClientRect();
  return { 目标: '第2枚可见详情按钮', 位置: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 可见枚数: cands.length };
});
LOG(`hover 目标: ${JSON.stringify(target)}`);

out.hover前 = await page.evaluate(() => [...document.querySelectorAll('body *')].filter((e) => (e.textContent || '').includes('新功能') || (e.textContent || '').includes('真人')).map((e) => ({ tag: e.tagName.toLowerCase(), 文字: (e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 30), 子: e.children.length })).slice(0, 8));
LOG(`hover 前含「新功能/真人」的元素: ${JSON.stringify(out.hover前)}`);

if (target) {
  // ⭐ hover 卡片本体（不是那枚详情按钮）—— 标记是「卡面上的引导」，多半跟卡有关
  const cardPt = await page.evaluate((c) => {
    const e = document.elementFromPoint(c[0], c[1]);
    if (!e) return null;
    for (let p = e, i = 0; p && i < 10; p = p.parentElement, i += 1) {
      const r = p.getBoundingClientRect();
      if (r.width > 150 && r.height > 150) return [Math.round(r.x + r.width / 2), Math.round(r.y + Math.min(r.height / 2, 60))];
    }
    return [c[0], c[1]];
  }, target.中心);
  LOG(`hover 卡片坐标: ${JSON.stringify(cardPt)}`);
  await page.mouse.move(cardPt[0], cardPt[1]);
  await page.waitForTimeout(1200);
  await page.mouse.move(cardPt[0] + 1, cardPt[1] + 1);
  await page.waitForTimeout(800);

  out.hover后 = await page.evaluate(() => {
    const vis = (e) => { if (!e) return false; const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && +s.opacity > 0; };
    const pool = [...document.querySelectorAll('body *')].filter((e) => (e.textContent || '').includes('新功能') || (e.textContent || '').includes('真人'));
    const hits = [];
    for (const e of pool) {
      if ([...e.children].some((c) => (c.textContent || '').includes('真人'))) continue;
      const t = (e.textContent || '').replace(/\s+/g, ' ').trim();
      const r = e.getBoundingClientRect();
      const 链 = [];
      for (let p = e, i = 0; p && i < 10; p = p.parentElement, i += 1) {
        const b = p.getBoundingClientRect(); const c = getComputedStyle(p);
        const ds = {}; for (const a of p.attributes) if (a.name.startsWith('data-')) ds[a.name] = a.value;
        链.push({ tag: p.tagName.toLowerCase(), 文字: (p.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 40), rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)], 可见: vis(p), aria: p.getAttribute('aria-label'), pos: c.position, z: c.zIndex, overflow: c.overflow, data: ds, class: (p.className || '').toString().slice(0, 70) });
      }
      let btn = null; for (let p = e; p; p = p.parentElement) { if (p.tagName === 'BUTTON') { btn = p; break; } }
      hits.push({ 文字: t, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 可见: vis(e), 祖先链: 链, 最近button祖先: btn ? (() => { const b = btn.getBoundingClientRect(); return { 文字: (btn.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 40), aria: btn.getAttribute('aria-label'), rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)] }; })() : null, 兄弟: e.parentElement ? [...e.parentElement.children].filter((c) => c !== e).map((c) => (c.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 24)).filter(Boolean) : [] });
    }
    return { 池大小: pool.length, hits };
  });
  LOG(`hover 后池大小=${out.hover后.池大小} 命中=${out.hover后.hits.length}`);
  for (const h of out.hover后.hits) {
    LOG(`\n--- 「${h.文字}」 @${JSON.stringify(h.rect)} 可见=${h.可见}`);
    LOG(`  最近 button 祖先: ${h.最近button祖先 ? `「${h.最近button祖先.文字}」 aria=${h.最近button祖先.aria} @${JSON.stringify(h.最近button祖先.rect)}` : '⛔ 没有 button 祖先 ⇒ 独立标签，不是角标'}`);
    LOG(`  兄弟: ${JSON.stringify(h.兄弟)}`);
    for (const c of h.祖先链) LOG(`    <${c.tag}> ${JSON.stringify(c.rect)} vis=${c.可见} pos=${c.pos} z=${c.z} aria=${c.aria} data=${JSON.stringify(c.data)} 「${c.文字}」`);
  }
  await shot(page, 'DB-b-hover第二张卡.png');
  LOG('\n📸 DB-b');
}

await writeFile(new URL('./batchDB2.json', import.meta.url), JSON.stringify(out, null, 2));
LOG('\n已写 tools/batchDB2.json');
await browser.close();

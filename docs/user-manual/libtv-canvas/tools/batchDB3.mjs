// Batch DB-3：追「新功能：支持真人」—— 本轮给出两条硬证据。
//
// DB-2 的两条读数：
//  ① 详情按钮 **DOM 总数 30 / 可见 1**，自身 opacity 分布 **{"0": 29, "1": 1}**
//     ⇒ ⭐⭐ 前两轮（DB-0/DB-1）用可见性过滤去数，**把 29 枚 opacity:0 的当成了不存在**。
//        「显形」是真的，但它们**一直在 DOM 里**。
//  ② hover 之后全页搜「新功能 / 真人」，命中池只有 1 个 —— 而那 1 个是 `<script>`
//    （Next.js 的 RSC 数据流），**不是界面元素**。
//     ⇒ ⛔ **铺满态（1440×810，6 列）下，这枚标记根本不在 DOM 里。**
//
// ⭐⭐ 关键线索：**M-345 那张图本身就是「最小化之后」拍的**（那张图里卡片是 4 列，
//   `810×657` 小窗）。CZ 记标记时人在小窗态，我这两次都在铺满态。
//   ⇒ 最可能：**这枚标记只在小窗（窄）态下渲染。**
//
// 本步：⭐ 点 `minimize` 进小窗 → 在**小窗容器内**搜标记（不再全页搜，
//   避免又被 RSC script 淹掉）→ 打祖先链 → 确认挂在谁身上 → hover 看气泡。
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
await page.waitForTimeout(3500);

// 铺满态基线（不搜 script，只看真实元素）
out.铺满态 = await page.evaluate(() => {
  const real = [...document.querySelectorAll('body *')].filter((e) => e.tagName !== 'SCRIPT' && e.tagName !== 'STYLE' && (e.textContent || '').includes('真人'));
  return { 真实元素含真人: real.length, 样本: real.slice(0, 5).map((e) => { const r = e.getBoundingClientRect(); return { tag: e.tagName.toLowerCase(), 文字: (e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 30), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; }) };
});
LOG(`铺满态: 真实元素含「真人」= ${out.铺满态.真实元素含真人}`);

// =============== 点 minimize 进小窗 ===============
LOG('\n══════════ 点 minimize，找小窗容器 ══════════');
out.小窗 = await page.evaluate(() => {
  const vis = (e) => { if (!e) return false; const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && +s.opacity > 0; };
  const b = [...document.querySelectorAll('button[aria-label="minimize"]')].find(vis);
  if (!b) return null;
  const r = b.getBoundingClientRect();
  b.click();
  return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
});
LOG(`点 minimize: ${JSON.stringify(out.小窗)}`);
await page.waitForTimeout(2500);

out.小窗态 = await page.evaluate(() => {
  const vis = (e) => { if (!e) return false; const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && +s.opacity > 0; };
  const maxBtn = [...document.querySelectorAll('button[aria-label="maximize"]')].find(vis);
  if (!maxBtn) return { 找到maximize: false };
  const mr = maxBtn.getBoundingClientRect();
  // 找小窗容器：从 maximize 往上，取第一个宽 < 1300 的固定容器
  let win = null;
  for (let p = maxBtn.parentElement, i = 0; p && i < 10; p = p.parentElement, i += 1) {
    const b = p.getBoundingClientRect(); const s = getComputedStyle(p);
    if (s.position === 'fixed' && b.width > 400 && b.width < 1300) { win = p; break; }
  }
  const wr = win ? win.getBoundingClientRect() : null;
  return {
    找到maximize: true,
    maximize: [Math.round(mr.x), Math.round(mr.y), Math.round(mr.width), Math.round(mr.height)],
    小窗: win ? { rect: [Math.round(wr.x), Math.round(wr.y), Math.round(wr.width), Math.round(wr.height)], class: (win.className || '').toString().slice(0, 80) } : null,
    win内含真人: win ? [...win.querySelectorAll('*')].filter((e) => e.tagName !== 'SCRIPT' && (e.textContent || '').includes('真人')).length : null,
  };
});
LOG(`小窗: ${JSON.stringify(out.小窗态.小窗)} maximize=${JSON.stringify(out.小窗态.maximize)}`);
LOG(`⭐ 小窗内含「真人」元素数: ${out.小窗态.win内含真人}`);

if (out.小窗态.找到maximize && out.小窗态.小窗) {
  const W = out.小窗态.小窗.rect;
  out.标记 = await page.evaluate((W) => {
    const vis = (e) => { if (!e) return false; const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && +s.opacity > 0; };
    // ⭐ 严格限定在**小窗矩形内**，且排除 script/style
    const pool = [...document.querySelectorAll('body *')].filter((e) => {
      if (e.tagName === 'SCRIPT' || e.tagName === 'STYLE') return false;
      const r = e.getBoundingClientRect();
      const inWin = r.x >= W[0] - 5 && r.x <= W[0] + W[2] + 5 && r.y >= W[1] - 5 && r.y <= W[1] + W[3] + 5;
      return inWin && (e.textContent || '').includes('真人');
    });
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
  }, W);
  LOG(`\n⭐ 小窗内池大小=${out.标记.池大小} 命中=${out.标记.hits.length}`);
  for (const h of out.标记.hits) {
    LOG(`\n--- 「${h.文字}」 @${JSON.stringify(h.rect)} 可见=${h.可见}`);
    LOG(`  最近 button 祖先: ${h.最近button祖先 ? `「${h.最近button祖先.文字}」 aria=${h.最近button祖先.aria} @${JSON.stringify(h.最近button祖先.rect)}` : '⛔ 没有 button 祖先 ⇒ 独立标签，不是角标'}`);
    LOG(`  兄弟: ${JSON.stringify(h.兄弟)}`);
    for (const c of h.祖先链) LOG(`    <${c.tag}> ${JSON.stringify(c.rect)} vis=${c.可见} pos=${c.pos} z=${c.z} aria=${c.aria} data=${JSON.stringify(c.data)} 「${c.文字}」`);
  }
  await shot(page, 'DB-c-小窗态找标记.png');
  LOG('\n📸 DB-c');
}

await writeFile(new URL('./batchDB3.json', import.meta.url), JSON.stringify(out, null, 2));
LOG('\n=== 已写 tools/batchDB3.json ===');
await browser.close();

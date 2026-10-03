// Batch DB-4：那枚「新功能：支持真人」到底存不存在 —— 先把我**看见但没读**的东西读出来。
//
// DB-3 是真阴性：铺满态 0、小窗态 0，且两轮阳性对照都成立
// （铺满 30 枚详情按钮 / 小窗 `[315,77,810,657]` 定位准确）。
// 但 ⭐⭐ **看图时我在小窗态亲眼看见了别的东西**：
//   第 2/3/4 张卡左上角各有一枚**灰色圆角角标**，里面是 `✧` 图标和一枚闪烁箭头；
//   第 1 张卡同一位置是一枚 `hl` 图标（金色那张）；第 5 张是 `✕` 形状。
// 账本从来没提过这些角标。⇒ **先别急着下「不存在」的结论**，
//   得先把这批角标逐一读出来：它挂在哪、aria 是什么、hover 出不出字。
//
// ⚠️ 本轮同时复核一个可能性：那行字可能**不在 DOM 文本里**（比如画在 canvas 上、
//   或来自远程配置只经 CSS/图片呈现）。但截图上它是清晰的**中文文字**，
//   而这几枚角标**没有任何文字** ⇒ 它们是不同东西。
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

// ---- 定位每张卡的「预览图左上角」，把那一块的元素全枚举出来 ----
LOG('══════════ 每张卡左上角的元素（找角标）══════════');
out.角标 = await page.evaluate(() => {
  const D = [...document.querySelectorAll('button[aria-label="详情"]')];
  const cards = D.map((b) => {
    // ⭐ 往上找卡片容器：含 img 或有较大面积的祖先
    let card = null;
    for (let p = b.parentElement, i = 0; p && i < 8; p = p.parentElement, i += 1) {
      const r = p.getBoundingClientRect();
      if (r.width > 150 && r.height > 150) { card = p; break; }
    }
    if (!card) return null;
    const cr = card.getBoundingClientRect();
    // 左上角 60×60 区域内的小元素
    const 左上 = [...card.querySelectorAll('*')].filter((e) => {
      const r = e.getBoundingClientRect();
      return r.width > 0 && r.height > 0 && r.width < 70 && r.height < 70
        && r.x >= cr.x - 2 && r.x <= cr.x + 60 && r.y >= cr.y - 2 && r.y <= cr.y + 60;
    }).map((e) => {
      const r = e.getBoundingClientRect(); const s = getComputedStyle(e);
      const ds = {}; for (const a of e.attributes) if (a.name.startsWith('data-')) ds[a.name] = a.value;
      return {
        tag: e.tagName.toLowerCase(),
        文字: (e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 24),
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        opacity: s.opacity, bg: s.backgroundColor, radius: s.borderRadius,
        aria: e.getAttribute('aria-label'), title: e.getAttribute('title'), data: ds,
        class: (e.className || '').toString().slice(0, 60),
        svg数: e.querySelectorAll('svg').length,
        svgPath: [...e.querySelectorAll('path')].map((p) => (p.getAttribute('d') || '').slice(0, 40)),
        img: [...e.querySelectorAll('img')].map((im) => im.getAttribute('src')?.slice(-40)),
      };
    });
    return { 卡片rect: [Math.round(cr.x), Math.round(cr.y), Math.round(cr.width), Math.round(cr.height)], 左上元素: 左上 };
  }).filter(Boolean);
  return { 卡数: cards.length, cards };
});
LOG(`卡数=${out.角标.卡数}`);
for (const [i, c] of (out.角标.cards ?? []).entries()) {
  LOG(`\n--- 卡${i} @${JSON.stringify(c.卡片rect)} 左上角 ${c.左上元素.length} 个元素`);
  for (const e of c.左上元素) {
    LOG(`    <${e.tag}> ${JSON.stringify(e.rect)} 「${e.文字}」 aria=${e.aria} title=${e.title} op=${e.opacity} bg=${e.bg} svg=${e.svg数} ${e.svgPath.length ? `path=${JSON.stringify(e.svgPath[0])}` : ''} ${e.img.length ? `img=${e.img[0]}` : ''} data=${JSON.stringify(e.data)}`);
  }
}

await writeFile(new URL('./batchDB4.json', import.meta.url), JSON.stringify(out, null, 2));
LOG('\n=== 已写 tools/batchDB4.json ===');
await browser.close();

// Batch CU-5：重拍 M-344。
//
// ⛔ CU-3 拍的 M-344 图里是**「整理画布 ⌥⇧F」**的气泡，但文件名写的是
//    「画布小地图」⇒ **名不副实**。纪律：名不副实的图比没有图更糟。
//    改成真的悬停第 3 枚（`aria-label="切换小地图"` / 气泡「画布小地图」）——
//    ⭐ 顺带就把「aria 与气泡措辞不同」这件事用图说清楚了。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';

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
const p = await page.evaluate(() => {
  const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === '下次再说');
  if (!b) return null; const r = b.getBoundingClientRect();
  return r.width > 0 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null;
});
if (p) { await page.mouse.click(p[0], p[1]); await page.waitForTimeout(1200); }

const t = await page.evaluate(() => {
  const host = document.querySelector('[data-toolbar-collapsed]');
  const bs = [...host.querySelectorAll('button,[role="button"]')].filter((b) => { const r = b.getBoundingClientRect(); return r.width > 0; }).sort((a, z) => a.getBoundingClientRect().x - z.getBoundingClientRect().x);
  const b = bs[2];                       // 第 3 枚 = aria「切换小地图」
  const r = b.getBoundingClientRect();
  return { 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], rect: [Math.round(r.x), Math.round(r.y)], aria: b.getAttribute('aria-label') };
});
LOG(`目标: ${JSON.stringify(t)}`);
await page.mouse.move(400, 300); await page.waitForTimeout(400);
await page.mouse.move(t.中心[0], t.中心[1]); await page.waitForTimeout(1200);
const tip = await page.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && +s.opacity > 0; };
  return [...document.querySelectorAll('[role="tooltip"]')].filter(vis).map((e) => ({ 文字: (e.innerText || '').trim(), rect: (() => { const r = e.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })() }));
});
LOG(`气泡: ${JSON.stringify(tip)}`);
if (tip[0]?.文字 === '画布小地图') {
  await shot(page, 'M-344-画布小地图按钮-悬停出名字.png', { clip: { x: 8, y: 706, width: 300, height: 98 } });
  LOG('📸 M-344 已覆盖 clip [8,706,300,98]');
} else {
  LOG('⛔ 气泡不是「画布小地图」，不覆盖旧图（避免名不副实）');
}
await browser.close();

// Batch CT-6：重拍两张图（CT-4 的构图太散，「截图做减法」）。
//
// M-341 原图 560×380（@2x 1120×760），左边 2/3 是空描述区，构图废。
//   ⇒ 收紧到「气泡 + 它下面那排按钮」。
// M-342 原图 798×76，把底栏拍全了但没有上下文。
//   ⇒ 收紧到 800×60，只留底栏一行。
//
// ⭐ 顺带补一张**新证据图**：大编辑器底栏那 4 枚纯图标按钮里，
//   `[776,959]` 之间有 **183px 的空隙** —— 底栏不是均匀排的。
//   这个空隙在内联卡片的参数条上也存在吗？值得记，但不必单独配图。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const IMG = 'i-9nlG6HdjK2';
const LOG = console.log;

const boot = async (page) => {
  await open(page, URL_);
  await closePromos(page);
  await page.waitForTimeout(1500);
  await page.evaluate(() => document.body.focus());
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2600);
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
};

const { browser, page } = await launch();
await boot(page);
await page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  n.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: n.getBoundingClientRect().x + 40, clientY: n.getBoundingClientRect().y + 20 }));
}, IMG);
await page.waitForTimeout(800);
const fp = await page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  const f = [...n.querySelectorAll('button')].find((b) => {
    const c = (b.className || '').toString();
    return c.includes('size-7') && c.includes('absolute') && c.includes('right-2') && c.includes('top-2');
  });
  const r = f.getBoundingClientRect();
  for (let dx = 4; dx < r.width; dx += 3) for (let dy = 4; dy < r.height; dy += 3) {
    const el = document.elementFromPoint(r.x + dx, r.y + dy);
    if (el && (el === f || f.contains(el) || el.contains(f))) return [Math.round(r.x + dx), Math.round(r.y + dy)];
  }
  return null;
}, IMG);
await page.mouse.click(fp[0], fp[1]);
await page.waitForTimeout(2000);

const bar = await page.evaluate(() => {
  const d = [...document.body.children].find((e) => getComputedStyle(e).zIndex === '601');
  const bs = [...d.querySelectorAll('[data-generator-control-bar] button')].map((b) => {
    const r = b.getBoundingClientRect();
    return { x: Math.round(r.x), r: Math.round(r.x + r.width), text: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 14) };
  });
  const gaps = [];
  for (let i = 1; i < bs.length; i += 1) gaps.push({ 上一枚: bs[i - 1].text || `图标@${bs[i - 1].x}`, 下一枚: bs[i].text || `图标@${bs[i].x}`, 空隙: bs[i].x - bs[i - 1].r });
  return { 按钮: bs, 空隙: gaps, 编辑器: (() => { const r = d.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })() };
});
LOG(`底栏按钮: ${JSON.stringify(bar.按钮, null, 1)}`);
LOG(`相邻空隙: ${JSON.stringify(bar.空隙)}`);

// ---- M-342 底栏一行（带一点上下文） -----------------------------------------
const b = bar.按钮;
const x0 = b[0].x, x1 = b[b.length - 1].r;
await shot(page, 'M-342-大编辑器-底栏七枚按钮.png', { clip: { x: x0 - 10, y: 652, width: (x1 - x0) + 20, height: 56 } });
LOG(`📸 M-342 clip x=${x0 - 10} y=652 w=${(x1 - x0) + 20} h=56`);

// ---- M-341 悬停「翻译提示词」的气泡 ------------------------------------------
await page.mouse.move(10, 10); await page.waitForTimeout(350);
await page.mouse.move(975, 680);
await page.waitForTimeout(1200);
const tip = await page.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && +s.opacity > 0; };
  return [...document.querySelectorAll('[role="tooltip"]')].filter(vis).map((e) => {
    const r = e.getBoundingClientRect();
    return { 文字: (e.innerText || '').replace(/\s+/g, ' ').trim(), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
  });
});
LOG(`悬停气泡: ${JSON.stringify(tip)}`);
if (tip.length) {
  const t = tip[0].rect;
  // 气泡下沿 657，底栏 664-696 ⇒ 取 y 618→700，把气泡和底栏都框住
  await shot(page, 'M-341-大编辑器-翻译提示词悬停.png', { clip: { x: 930, y: 616, width: 220, height: 88 } });
  LOG(`📸 M-341 clip x=930 y=616 w=220 h=88（气泡 ${JSON.stringify(t)}）`);
}
await browser.close();

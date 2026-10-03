// Batch CU-3：拍两张图证明「hover 读气泡」这条路。
//
// CU-0/1/2 的结论是「气泡覆盖率极高」（默认画布 15/15），
// 但正文里那些旧图都是「点开之后的静态结果」，**没有一张是悬停态**。
// ⭐ 这两张图要证明的就是：把鼠标放上去，控件自己会报出自己的名字。
//
// 图 1：悬停底栏第 7 枚（`data-sidebar-btn="contact"`）
//        ⭐ 属性名写着 `contact`（联系），气泡报的是 **`教程`** ——
//        这就是「属性名会骗人」的实例，图能说清。
// 图 2：悬停资产管理工具行第 2 枚
//        ⭐ `aria-label` 写 **`切换小地图`**，气泡报的是 **`画布小地图`** ——
//        同一枚按钮两处措辞不同，图能说清。
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

// ---- 图 1：悬停底栏第 7 枚 -----------------------------------------------------
const t1 = await page.evaluate(() => {
  const b = document.querySelector('[data-sidebar-btn="contact"]');
  const r = b.getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2), Math.round(r.x), Math.round(r.y)];
});
LOG(`底栏第 7 枚 @${JSON.stringify(t1.slice(2))} 中心 ${JSON.stringify(t1.slice(0, 2))}`);
await page.mouse.move(400, 300); await page.waitForTimeout(400);
await page.mouse.move(t1[0], t1[1]); await page.waitForTimeout(1200);
const tip1 = await page.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && +s.opacity > 0; };
  return [...document.querySelectorAll('[role="tooltip"]')].filter(vis).map((e) => { const r = e.getBoundingClientRect(); return { 文字: (e.innerText || '').trim(), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; });
});
LOG(`气泡: ${JSON.stringify(tip1)}`);
await shot(page, 'M-343-底栏教程按钮-悬停出名字.png', { clip: { x: 566, y: 706, width: 320, height: 100 } });
LOG('📸 M-343 clip [566,706,320,100]');

// ---- 图 2：悬停资产管理工具行第 2 枚 -------------------------------------------
await page.mouse.move(400, 300); await page.waitForTimeout(500);
const t2 = await page.evaluate(() => {
  // 资产管理工具行 4 枚：整理画布 / 切换小地图 / 隐藏节点连线 / 网格吸附
  const host = document.querySelector('[data-toolbar-collapsed]');
  if (!host) return null;
  const bs = [...host.querySelectorAll('button,[role="button"]')].filter((b) => { const r = b.getBoundingClientRect(); return r.width > 0; });
  if (bs.length < 2) return null;
  const r = bs[1].getBoundingClientRect();
  return { 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], aria: bs[1].getAttribute('aria-label'), 总数: bs.length };
});
LOG(`资产管理第 2 枚: ${JSON.stringify(t2)}`);
if (t2) {
  await page.mouse.move(t2.中心[0], t2.中心[1]); await page.waitForTimeout(1200);
  const tip2 = await page.evaluate(() => {
    const vis = (e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && +s.opacity > 0; };
    return [...document.querySelectorAll('[role="tooltip"]')].filter(vis).map((e) => ({ 文字: (e.innerText || '').trim(), rect: (() => { const r = e.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })() }));
  });
  LOG(`气泡: ${JSON.stringify(tip2)}`);
  await shot(page, 'M-344-画布小地图按钮-悬停出名字.png', { clip: { x: 8, y: 700, width: 300, height: 104 } });
  LOG('📸 M-344 clip [8,700,300,104]');
}

await browser.close();

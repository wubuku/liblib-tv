// Batch CB-0：三条未执行的 📖，先做「探针自检」——
// ⭐ 核心原则（CA 教训）：每个探针必须先证明它能命中正例，再让它去读未验证的东西。
// 这一步只回答一个问题：三个探针各自能不能命中已知存在的目标？
import { launch, open, closePromos, ORIGIN } from './lib.mjs';

const URL = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;

const { browser, page } = await launch();
await open(page, URL);
await closePromos(page);

const probe = {};

// ---------- 探针 1：资产管理抽屉开关（按 x<100 挑，不靠 .first()） ----------
probe.drawerToggles = await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  return [...document.querySelectorAll('[aria-label="资产管理"]')]
    .filter(vis)
    .map((el, i) => {
      const r = el.getBoundingClientRect();
      return { i, tag: el.tagName, x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
    });
});

// 底栏那枚（x≈61）才是开关
const bottom = page.locator('[aria-label="资产管理"]').filter({ hasNot: page.locator('.mantine-Drawer-content') });
const opened = await page.evaluate(() => true);
probe.openDrawer = await page.evaluate(async () => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const cands = [...document.querySelectorAll('[aria-label="资产管理"]')].filter(vis)
    .map((el) => ({ el, r: el.getBoundingClientRect() }))
    .filter((c) => c.r.x < 100)
    .sort((a, b) => a.r.x - b.r.x);
  if (!cands.length) return { ok: false, why: 'x<100 的开关 0 个' };
  cands[0].el.click();
  return { ok: true, at: { x: Math.round(cands[0].r.x), y: Math.round(cands[0].r.y) } };
});
await page.waitForTimeout(1400);

// 抽屉正文 + 「资产」页签
probe.afterOpen = await page.evaluate(() => {
  const d = document.querySelector('.mantine-Drawer-content');
  return {
    hasDrawer: !!d,
    text: d ? (d.innerText || '').replace(/\s+/g, ' ').slice(0, 400) : null,
    tabs: d ? [...d.querySelectorAll('[role="tab"]')].map((t) => (t.innerText || '').trim()) : [],
  };
});

// ---------- 探针 2：点开资产行菜单，找「移动到 ›」 ----------
probe.moreBtns = await page.evaluate(() => {
  const d = document.querySelector('.mantine-Drawer-content');
  if (!d) return { ok: false, why: '抽屉没开' };
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const btns = [...d.querySelectorAll('[aria-label="更多操作"]')].filter(vis);
  if (!btns.length) return { ok: false, why: '资产行 0 个', rows: d.querySelectorAll('[role="row"]').length };
  btns[0].click();
  return { ok: true, count: btns.length };
});
await page.waitForTimeout(700);
probe.menuAfterMore = await page.evaluate(() => {
  const items = [...document.querySelectorAll('.mantine-Menu-item, [role="menuitem"]')]
    .filter((el) => { const r = el.getBoundingClientRect(); return r.width > 0; })
    .map((el) => (el.innerText || '').trim()).filter(Boolean);
  return { count: items.length, items };
});

// 点「移动到 ›」
probe.moveHover = await page.evaluate(() => {
  const it = [...document.querySelectorAll('.mantine-Menu-item, [role="menuitem"]')]
    .find((el) => (el.innerText || '').includes('移动到'));
  if (!it) return { ok: false };
  it.dispatchEvent(new MouseEvent('mouseover', { bubbles: true }));
  it.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
  it.click();
  const r = it.getBoundingClientRect();
  return { ok: true, at: { x: Math.round(r.x), y: Math.round(r.y) } };
});
await page.waitForTimeout(900);
probe.moveSubmenu = await page.evaluate(() => {
  const items = [...document.querySelectorAll('.mantine-Menu-item, [role="menuitem"]')]
    .filter((el) => { const r = el.getBoundingClientRect(); return r.width > 0; })
    .map((el) => {
      const r = el.getBoundingClientRect();
      return { t: (el.innerText || '').trim(), x: Math.round(r.x), y: Math.round(r.y) };
    }).filter((o) => o.t);
  return { count: items.length, items: items.slice(0, 40) };
});

console.log(JSON.stringify(probe, null, 2));
await browser.close();

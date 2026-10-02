// Batch CB-3：切到「资产」页签，dump 资产行，再点开「更多操作」找 `移动到 ›`。
// ⚠️ 安全边界：全程只读 —— 只开菜单、只悬停子菜单，**不点任何会搬动/删除的动作**。
//   搬动资产会改变用户的文件夹结构，删除更不可逆，都不在「探索」授权范围内。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;

const { browser, page } = await launch();
await open(page, URL_);
await closePromos(page);

const out = {};

// 开抽屉（x<100 的底栏开关）
await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  [...document.querySelectorAll('[aria-label="资产管理"]')].filter(vis)
    .map((el) => ({ el, r: el.getBoundingClientRect() }))
    .filter((c) => c.r.x < 100).sort((a, b) => a.r.x - b.r.x)[0]?.el.click();
});
await page.waitForTimeout(1500);

// 点「资产」页签（按坐标，不靠文本冒泡 —— CB-1 证明按文本会点到同时含两个页签的容器）
out.tabSwitch = await page.evaluate(() => {
  const d = document.querySelector('.mantine-Drawer-content');
  const btn = [...d.querySelectorAll('button')].find((b) => (b.innerText || '').trim() === '资产');
  if (!btn) return { ok: false };
  const r = btn.getBoundingClientRect();
  btn.click();
  return { ok: true, box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
});
await page.waitForTimeout(1600);

out.assetPage = await page.evaluate(() => {
  const d = document.querySelector('.mantine-Drawer-content');
  return {
    text: (d.innerText || '').replace(/\s+/g, ' ').slice(0, 500),
    moreCount: d.querySelectorAll('[aria-label="更多操作"]').length,
    manage: [...d.querySelectorAll('[aria-label="资产管理"]')].map((el) => {
      const r = el.getBoundingClientRect();
      return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
    }),
  };
});

// 点第一行的「更多操作」
out.openMenu = await page.evaluate(() => {
  const d = document.querySelector('.mantine-Drawer-content');
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const b = [...d.querySelectorAll('[aria-label="更多操作"]')].filter(vis)[0];
  if (!b) return { ok: false, why: '0 个更多操作' };
  const r = b.getBoundingClientRect();
  b.click();
  return { ok: true, box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
});
await page.waitForTimeout(800);

const readMenu = () => page.evaluate(() => [...document.querySelectorAll('.mantine-Menu-item, [role="menuitem"]')]
  .filter((el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
  .map((el) => {
    const r = el.getBoundingClientRect();
    const chev = el.querySelector('svg, .mantine-IconChevronRight') ? '有图标' : '';
    return { t: (el.innerText || '').trim(), box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], chev };
  }).filter((o) => o.t));

out.menu8 = await readMenu();
await shot(page, 'M-291-资产页-更多操作八项菜单.png', { clip: { x: 0, y: 80, width: 640, height: 460 } });

// 悬停「移动到 ›」→ 子菜单（Mantine 子菜单靠 hover 展开）
out.hoverMove = await page.evaluate(() => {
  const it = [...document.querySelectorAll('.mantine-Menu-item, [role="menuitem"]')]
    .find((el) => (el.innerText || '').includes('移动到'));
  if (!it) return { ok: false, why: '菜单里没有「移动到」' };
  const r = it.getBoundingClientRect();
  for (const type of ['mouseover', 'mouseenter', 'mousemove', 'pointerover']) {
    it.dispatchEvent(new MouseEvent(type, { bubbles: true, clientX: r.x + r.width / 2, clientY: r.y + r.height / 2 }));
  }
  return { ok: true, box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
});
await page.waitForTimeout(1100);
out.submenu = await readMenu();
await shot(page, 'M-292-资产页-移动到子菜单.png', { clip: { x: 0, y: 80, width: 760, height: 520 } });

await writeFile(resolve(HERE, '.evidence/cb3-move.json'), JSON.stringify(out, null, 2));
console.log('done');
await browser.close();

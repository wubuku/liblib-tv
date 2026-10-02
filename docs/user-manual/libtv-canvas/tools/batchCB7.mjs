// Batch CB-7：CB-6 被一个**延迟出现**的促销弹窗（Agent 已升级为 TV Director）打断 ——
// 菜单被它关掉了，于是「新建子文件夹」和「Popover-dropdown」全读成 0。
// ⭐ 与 §52（差分基线采太早造成时序污染）同源：**页面还在加载时读，读到的是中间态**。
// 修法：每一步之间都重新清一次弹窗，并且**先证弹窗不在了再动手**。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const MY_FOLDER = 'CB6临时文件夹';

const { browser, page } = await launch();
await open(page, URL_);
await closePromos(page);
const out = { promos: [] };

const clearAll = async (tag) => {
  const r = await closePromos(page);
  if (r.length) out.promos.push({ tag, r });
  await page.waitForTimeout(400);
};

// 开抽屉 → 资产页
await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const cands = [...document.querySelectorAll('[aria-label="资产管理"]')].filter(vis)
    .map((el) => ({ el, r: el.getBoundingClientRect() })).filter((c) => c.r.x < 100)
    .sort((a, b) => a.r.x - b.r.x);
  if (cands.length && !document.querySelector('.mantine-Drawer-content')) cands[0].el.click();
});
await page.waitForTimeout(1500);
await clearAll('after-drawer');
await page.evaluate(() => {
  const d = document.querySelector('.mantine-Drawer-content');
  [...d.querySelectorAll('button')].find((b) => (b.innerText || '').trim() === '资产')?.click();
});
await page.waitForTimeout(1500);
await clearAll('after-tab');

const openRowMenu = async () => {
  await page.evaluate(() => {
    const d = document.querySelector('.mantine-Drawer-content');
    const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    [...d.querySelectorAll('[aria-label="更多操作"]')].filter(vis)[0]?.click();
  });
  await page.waitForTimeout(900);
};
const menuItems = () => page.evaluate(() => [...document.querySelectorAll('.mantine-Menu-item, [role="menuitem"]')]
  .filter((el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
  .map((el) => (el.innerText || '').trim()).filter(Boolean));
const hoverItem = async (name) => {
  const box = await page.evaluate((n) => {
    const it = [...document.querySelectorAll('.mantine-Menu-item, [role="menuitem"]')]
      .find((el) => (el.innerText || '').trim() === n);
    if (!it) return null;
    const r = it.getBoundingClientRect();
    return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
  }, name);
  if (!box) return null;
  await page.mouse.move(200, 300, { steps: 6 });
  await page.mouse.move(box[0] + box[2] / 2, box[1] + box[3] / 2, { steps: 12 });
  await page.waitForTimeout(1200);
  return box;
};
const readSubmenu = () => page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const dd = [...document.querySelectorAll('.mantine-Popover-dropdown')].filter(vis);
  if (!dd.length) return { ok: false, why: '没有 Popover-dropdown' };
  const last = dd[dd.length - 1];
  return {
    ok: true,
    box: (() => { const r = last.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })(),
    rows: [...last.querySelectorAll('button')].map((b) => (b.innerText || '').trim()).filter(Boolean),
  };
});

// —— 基线：子菜单里有几项 ——
await openRowMenu();
out.menu8 = await menuItems();
out.baseMoveBox = await hoverItem('移动到');
out.base = await readSubmenu();
await shot(page, 'M-292-资产页-移动到子菜单.png', { clip: { x: 100, y: 190, width: 480, height: 420 } });

// —— 建一个本轮自己的子文件夹 ——
await hoverItem('新建子文件夹');
out.clickedNew = await page.evaluate((n) => {
  const it = [...document.querySelectorAll('.mantine-Menu-item, [role="menuitem"]')]
    .find((el) => (el.innerText || '').trim() === n);
  if (!it) return { ok: false };
  it.click();
  return { ok: true };
}, '新建子文件夹');
await page.waitForTimeout(1200);
await clearAll('after-newfolder');
out.dialog = await page.evaluate(() => {
  const d = [...document.querySelectorAll('[role="dialog"], .mantine-Modal-content')]
    .filter((el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; });
  if (!d.length) return { ok: false, why: '没弹对话框' };
  const last = d[d.length - 1];
  return {
    ok: true,
    text: (last.innerText || '').replace(/\s+/g, ' ').slice(0, 220),
    inputs: [...last.querySelectorAll('input')].map((i) => ({ ph: i.placeholder, aria: i.getAttribute('aria-label'), val: i.value })),
    btns: [...last.querySelectorAll('button')].map((b) => (b.innerText || b.getAttribute('aria-label') || '').trim()).filter(Boolean),
  };
});
out.folderName = MY_FOLDER;

await writeFile(resolve(HERE, '.evidence/cb7-a.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify({ menu8: out.menu8, base: out.base, dialog: out.dialog }, null, 2));
await browser.close();

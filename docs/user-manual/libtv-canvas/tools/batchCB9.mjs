// Batch CB-9：一次跑完「移动到 ›」的完整对照。
//   基线（只有 1 项）→ 建本轮自己的子文件夹 → 再读（应变成 2 项）→ 删掉**自己建的那个**。
// ⚠️ 收尾只按**本轮自己记下的文件夹名**删，且删前先核「它的父级是 个人资产库、它不是待分类资产」。
//    绝不按位置/顺序认目标（CA 误删事故的教训）。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const MY_FOLDER = 'CB9临时文件夹';

const { browser, page } = await launch();
await open(page, URL_);
await closePromos(page);
const out = {};

// 清促销模态（只认真正的模态；TV Director 侧栏是常驻的 role=dialog，不算）
out.clearPromo = await page.evaluate(async () => {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  for (let i = 0; i < 6; i += 1) {
    const hit = [...document.querySelectorAll('button, [role="button"]')]
      .find((b) => (b.innerText || '').trim() === '知道了');
    if (hit) { hit.click(); await sleep(500); }
    if (!(document.body.innerText || '').includes('已升级为 TV Director')) return { gone: true, tries: i + 1 };
  }
  return { gone: false };
});
await page.waitForTimeout(800);

const clickAssetTab = () => page.evaluate(() => {
  const d = document.querySelector('.mantine-Drawer-content');
  if (!d) return false;
  const b = [...d.querySelectorAll('button')].find((x) => (x.innerText || '').trim() === '资产');
  if (!b) return false;
  b.click();
  return true;
});
const openRowMenu = () => page.evaluate(() => {
  const d = document.querySelector('.mantine-Drawer-content');
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const b = [...d.querySelectorAll('[aria-label="更多操作"]')].filter(vis)[0];
  if (!b) return false;
  b.click();
  return true;
});
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
  const r = last.getBoundingClientRect();
  return {
    ok: true, box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    rows: [...last.querySelectorAll('button')].map((b) => (b.innerText || '').trim()).filter(Boolean),
  };
});

// 开抽屉 → 资产页
out.openDrawer = await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const c = [...document.querySelectorAll('[aria-label="资产管理"]')].filter(vis)
    .map((el) => ({ el, r: el.getBoundingClientRect() })).filter((o) => o.r.x < 100)
    .sort((a, b) => a.r.x - b.r.x);
  if (c.length && !document.querySelector('.mantine-Drawer-content')) { c[0].el.click(); return true; }
  return false;
});
await page.waitForTimeout(1500);
out.tab = await clickAssetTab();
await page.waitForTimeout(1600);
out.rowsBefore = await page.evaluate(() => {
  const d = document.querySelector('.mantine-Drawer-content');
  return (d.innerText || '').replace(/\s+/g, ' ').slice(0, 200);
});

// —— 基线 ——
out.openMenu = await openRowMenu();
await page.waitForTimeout(1000);
out.menu8 = await page.evaluate(() => [...document.querySelectorAll('.mantine-Menu-item, [role="menuitem"]')]
  .filter((el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
  .map((el) => (el.innerText || '').trim()).filter(Boolean));
out.base = (await hoverItem('移动到'), await readSubmenu());
await shot(page, 'M-292-资产页-移动到子菜单.png', { clip: { x: 100, y: 190, width: 480, height: 420 } });

// —— 建自己的子文件夹 ——
await hoverItem('新建子文件夹');
out.clickedNew = await page.evaluate(() => {
  const it = [...document.querySelectorAll('.mantine-Menu-item, [role="menuitem"]')]
    .find((el) => (el.innerText || '').trim() === '新建子文件夹');
  if (!it) return { ok: false, why: '菜单没了' };
  it.click();
  return { ok: true };
});
await page.waitForTimeout(1400);
out.dialog = await page.evaluate(() => {
  const d = [...document.querySelectorAll('.mantine-Modal-content, [role="dialog"]')]
    .filter((el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
    .filter((el) => /文件夹|名称|创建/.test(el.innerText || ''));
  if (!d.length) return { ok: false, why: '没弹文件夹对话框' };
  const last = d[d.length - 1];
  return {
    ok: true, text: (last.innerText || '').replace(/\s+/g, ' ').slice(0, 200),
    inputs: [...last.querySelectorAll('input')].map((i) => ({ ph: i.placeholder, aria: i.getAttribute('aria-label') })),
    btns: [...last.querySelectorAll('button')].map((b) => (b.innerText || b.getAttribute('aria-label') || '').trim()).filter(Boolean),
  };
});
out.folderName = MY_FOLDER;

await writeFile(resolve(HERE, '.evidence/cb9-a.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify({ clearPromo: out.clearPromo, menu8: out.menu8, base: out.base, clickedNew: out.clickedNew, dialog: out.dialog }, null, 2));
await browser.close();

// Batch CB-8：促销弹窗不是 Mantine Modal —— `closePromos` 扫 `.mantine-Modal-overlay` 一个都没扫到，
// 报数为 0 就返回空数组，**看起来像「没有弹窗」，其实弹窗正挡在面前**。
// ⭐ 第四次踩同一条：读数为 0 先问判据有没有挡住。这次是被自己的封装函数骗了 ——
//   `closePromos` 返回 `[]` 我就当没事，而不是去看「那个弹窗还在不在」。
// 修法：显式找「知道了」点掉，**并且回读它确实不见了**，才继续往下走。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const MY_FOLDER = 'CB8临时文件夹';

const { browser, page } = await launch();
await open(page, URL_);
await closePromos(page);
const out = {};

// —— 步骤 0：显式清促销弹窗，并自证 ——
out.step0 = await page.evaluate(async () => {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  for (let i = 0; i < 6; i += 1) {
    const hit = [...document.querySelectorAll('button, [role="button"]')]
      .find((b) => (b.innerText || '').trim() === '知道了');
    if (hit) { hit.click(); await sleep(500); }
    const still = (document.body.innerText || '').includes('已升级为 TV Director');
    if (!still) return { gone: true, tries: i + 1 };
  }
  return { gone: false };
});
await page.waitForTimeout(900);

const dialogsNow = await page.evaluate(() => [...document.querySelectorAll('[role="dialog"],.mantine-Modal-content')]
  .filter((el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
  .map((el) => (el.innerText || '').replace(/\s+/g, ' ').slice(0, 80)));
out.dialogsAfterClear = dialogsNow;
if (dialogsNow.length) { console.log(JSON.stringify(out, null, 2)); await browser.close(); process.exit(1); }

// —— A：子菜单基线 ——
await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const c = [...document.querySelectorAll('[aria-label="资产管理"]')].filter(vis)
    .map((el) => ({ el, r: el.getBoundingClientRect() })).filter((o) => o.r.x < 100)
    .sort((a, b) => a.r.x - b.r.x);
  if (c.length && !document.querySelector('.mantine-Drawer-content')) c[0].el.click();
});
await page.waitForTimeout(1500);
await page.evaluate(() => {
  const d = document.querySelector('.mantine-Drawer-content');
  [...d.querySelectorAll('button')].find((b) => (b.innerText || '').trim() === '资产')?.click();
});
await page.waitForTimeout(1600);

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
  return {
    ok: true,
    rows: [...last.querySelectorAll('button')].map((b) => (b.innerText || '').trim()).filter(Boolean),
    text: (last.innerText || '').replace(/\s+/g, ' ').trim(),
  };
});

out.openRowMenu = await openRowMenu();
await page.waitForTimeout(1000);
out.menu8 = await page.evaluate(() => [...document.querySelectorAll('.mantine-Menu-item, [role="menuitem"]')]
  .filter((el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
  .map((el) => (el.innerText || '').trim()).filter(Boolean));
out.base = (await hoverItem('移动到'), await readSubmenu());
await shot(page, 'M-292-资产页-移动到子菜单.png', { clip: { x: 100, y: 190, width: 480, height: 420 } });

// —— 建本轮自己的子文件夹 ——
await hoverItem('新建子文件夹');
out.clickedNew = await page.evaluate(() => {
  const it = [...document.querySelectorAll('.mantine-Menu-item, [role="menuitem"]')]
    .find((el) => (el.innerText || '').trim() === '新建子文件夹');
  if (!it) return { ok: false, why: '菜单没了' };
  it.click();
  return { ok: true };
});
await page.waitForTimeout(1300);
out.dialog = await page.evaluate(() => {
  const d = [...document.querySelectorAll('[role="dialog"], .mantine-Modal-content')]
    .filter((el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; });
  if (!d.length) return { ok: false, why: '没弹对话框' };
  const last = d[d.length - 1];
  return {
    ok: true,
    text: (last.innerText || '').replace(/\s+/g, ' ').slice(0, 200),
    inputs: [...last.querySelectorAll('input')].map((i) => ({ ph: i.placeholder, aria: i.getAttribute('aria-label') })),
    btns: [...last.querySelectorAll('button')].map((b) => (b.innerText || b.getAttribute('aria-label') || '').trim()).filter(Boolean),
  };
});
out.folderName = MY_FOLDER;

await writeFile(resolve(HERE, '.evidence/cb8-a.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify({ step0: out.step0, menu8: out.menu8, base: out.base, dialog: out.dialog }, null, 2));
await browser.close();

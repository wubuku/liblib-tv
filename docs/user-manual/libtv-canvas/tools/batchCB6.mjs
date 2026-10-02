// Batch CB-6：两件事，都做到「有对照」为止。
//
// 【A】「移动到 ›」子菜单：已读到它**只有一项**「个人资产库」。
//     但「只有一项」有两种可能：① 写死一项；② 它是**活的文件夹列表**，只是资产树只有一层。
//     分不开，就不叫结案。
//     做法：建一个**本轮自己造**的子文件夹 → 再看子菜单有几项 → 删掉**自己建的那个**。
//     ⭐⭐ 收尾只按**本轮自己记下的名字 + 类型**删，绝不按位置/顺序（CA 教训）。
//
// 【B】特效广场：CA③ 上轮「没找到卡片」。这次先 dump 卡片的真实结构与坐标，不猜。
//     ⚠️ 只**悬停 + 读**，不点卡片 —— 点卡片可能触发加入画布/下载等副作用。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const MY_FOLDER = `CB6临时文件夹`;

const { browser, page } = await launch();
await open(page, URL_);
await closePromos(page);
const out = {};

// ---------- A：移动到 › 子菜单的活/死对照 ----------
const openAssetMenu = async () => {
  await page.evaluate(() => {
    const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    const btn = [...document.querySelectorAll('[aria-label="资产管理"]')].filter(vis)
      .map((el) => ({ el, r: el.getBoundingClientRect() }))
      .filter((c) => c.r.x < 100).sort((a, b) => a.r.x - b.r.x)[0]?.el;
    if (btn && !document.querySelector('.mantine-Drawer-content')) btn.click();
  });
  await page.waitForTimeout(1400);
  await page.evaluate(() => {
    const d = document.querySelector('.mantine-Drawer-content');
    if (!d) return;
    [...d.querySelectorAll('button')].find((b) => (b.innerText || '').trim() === '资产')?.click();
  });
  await page.waitForTimeout(1500);
};
const hoverMove = async () => {
  await page.evaluate(() => {
    const d = document.querySelector('.mantine-Drawer-content');
    const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    [...d.querySelectorAll('[aria-label="更多操作"]')].filter(vis)[0]?.click();
  });
  await page.waitForTimeout(900);
  const box = await page.evaluate(() => {
    const it = [...document.querySelectorAll('.mantine-Menu-item, [role="menuitem"]')]
      .find((el) => (el.innerText || '').trim() === '移动到');
    if (!it) return null;
    const r = it.getBoundingClientRect();
    return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
  });
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
  return {
    ok: true,
    text: (dd[dd.length - 1].innerText || '').replace(/\s+/g, ' ').trim(),
    rows: [...dd[dd.length - 1].querySelectorAll('button')].map((b) => (b.innerText || '').trim()).filter(Boolean),
  };
});

await openAssetMenu();
out.A_moveBox = await hoverMove();
out.A_before = await readSubmenu();
await shot(page, 'M-292-资产页-移动到子菜单.png', { clip: { x: 100, y: 200, width: 460, height: 400 } });

// 建子文件夹（先点「新建子文件夹」）
out.A_newFolder = await page.evaluate(() => {
  const it = [...document.querySelectorAll('.mantine-Menu-item, [role="menuitem"]')]
    .find((el) => (el.innerText || '').trim() === '新建子文件夹');
  if (!it) return { ok: false, why: '菜单里没有「新建子文件夹」' };
  it.click();
  return { ok: true };
});
await page.waitForTimeout(1000);
out.A_dialog = await page.evaluate(() => {
  const d = [...document.querySelectorAll('[role="dialog"], .mantine-Modal-content')]
    .filter((el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; });
  if (!d.length) return { ok: false };
  const inputs = [...d[d.length - 1].querySelectorAll('input')].map((i) => ({ ph: i.placeholder, aria: i.getAttribute('aria-label') }));
  return { ok: true, text: (d[d.length - 1].innerText || '').replace(/\s+/g, ' ').slice(0, 200), inputs };
});

await writeFile(resolve(HERE, '.evidence/cb6-a.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify({ before: out.A_before, newFolder: out.A_newFolder, dialog: out.A_dialog }, null, 2));
await browser.close();

// Batch CB-11：「新建子文件夹」点下去**没有对话框**，但也不能就此记成「没反应」——
// ⭐ 先看它是不是像「重命名」那样**行内出输入框**。这正是 §54「『没报错』当『点开了』」的镜像：
//   这次是「没有对话框」，可能是弹窗、可能是行内、也可能真的没反应 —— 三者长得一样。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const MY_FOLDER = 'CB11临时文件夹';

const { browser, page } = await launch();
await open(page, URL_);
await closePromos(page);
const out = {};

await page.evaluate(async () => {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  for (let i = 0; i < 6; i += 1) {
    const hit = [...document.querySelectorAll('button, [role="button"]')].find((b) => (b.innerText || '').trim() === '知道了');
    if (hit) { hit.click(); await sleep(500); }
    if (!(document.body.innerText || '').includes('已升级为 TV Director')) return;
  }
});
await page.waitForTimeout(900);

const inDrawer = (fnBody) => page.evaluate(`(() => {
  const d = [...document.querySelectorAll('.mantine-Drawer-content')]
    .filter((x) => { const r = x.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
    .find((x) => [...x.querySelectorAll('button')].some((b) => ['画布','资产'].includes((b.innerText||'').trim())));
  if (!d) return { __err: 'asset drawer not found' };
  ${fnBody}
})()`);

await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const has = [...document.querySelectorAll('.mantine-Drawer-content')].filter(vis)
    .some((d) => [...d.querySelectorAll('button')].some((b) => ['画布', '资产'].includes((b.innerText || '').trim())));
  if (has) return;
  const c = [...document.querySelectorAll('[aria-label="资产管理"]')].filter(vis)
    .map((el) => ({ el, r: el.getBoundingClientRect() })).filter((o) => o.r.x < 100)
    .sort((a, b) => a.r.x - b.r.x);
  c[0]?.el.click();
});
await page.waitForTimeout(1600);
await inDrawer(`[...d.querySelectorAll('button')].find((b) => (b.innerText||'').trim() === '资产')?.click(); return 1;`);
await page.waitForTimeout(1600);

out.before = await inDrawer(`
  return { text: (d.innerText||'').replace(/\\s+/g,' ').slice(0,200),
    inputs: [...d.querySelectorAll('input')].map((i) => ({ ph: i.placeholder, aria: i.getAttribute('aria-label'), val: i.value })) };`);

const clicked = await inDrawer(`
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  [...d.querySelectorAll('[aria-label="更多操作"]')].filter(vis)[0]?.click();
  return 1;`);
await page.waitForTimeout(900);
await page.evaluate(() => {
  const it = [...document.querySelectorAll('.mantine-Menu-item, [role="menuitem"]')]
    .find((el) => (el.innerText || '').trim() === '新建子文件夹');
  if (it) it.click();
});
await page.waitForTimeout(1400);

out.after = await inDrawer(`
  return { text: (d.innerText||'').replace(/\\s+/g,' ').slice(0,200),
    inputs: [...d.querySelectorAll('input')].map((i) => ({ ph: i.placeholder, aria: i.getAttribute('aria-label'), val: i.value, focused: document.activeElement === i })),
    modals: [...document.querySelectorAll('.mantine-Modal-content,[role="dialog"]')]
      .filter((m) => { const r = m.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
      .map((m) => (m.innerText||'').replace(/\\s+/g,' ').slice(0,80)) };`);
await shot(page, 'M-293-资产页-新建子文件夹之后.png', { clip: { x: 0, y: 80, width: 700, height: 400 } });

out.folderName = MY_FOLDER;
await writeFile(resolve(HERE, '.evidence/cb11.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify(out, null, 2));
await browser.close();

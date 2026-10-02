// Batch CB-10：⭐⭐ 根因找到了 —— 页面里有**两个** `.mantine-Drawer-content`：
//   资产管理抽屉 和 TV Director 侧栏 **共用同一个 class**。`querySelector` 取到的是先出现的那个。
//   CB-3/CB-4 能跑通是因为那几轮 TV Director 侧栏还没展开；CB-8 起它展开了，全部读成空。
//   `rowsBefore` 读出来是「让 TV Director 辅助你的无限创意」—— 那一刻才看清是我取错了抽屉。
// ⭐ 教训升级版：**「同一个 class 可以有多个实例」** —— 凡是靠 class 定位浮层，
//    都得再加一条「这个实例里有我要的那段文字」当守卫，否则取到的可能是**另一个**浮层。
//    这跟「数 `<button>` 找不到剪刀」是同族错误：判据没错，但**选错了对象**。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const MY_FOLDER = 'CB10临时文件夹';

const { browser, page } = await launch();
await open(page, URL_);
await closePromos(page);
const out = {};

// 清促销模态
await page.evaluate(async () => {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  for (let i = 0; i < 6; i += 1) {
    const hit = [...document.querySelectorAll('button, [role="button"]')]
      .find((b) => (b.innerText || '').trim() === '知道了');
    if (hit) { hit.click(); await sleep(500); }
    if (!(document.body.innerText || '').includes('已升级为 TV Director')) return;
  }
});
await page.waitForTimeout(900);

// ⭐ 守卫生效的 drawer 选择器：所有 Drawer-content 里，**含「画布」或「资产」页签**的那个
// （用模板字符串注入，别用 new Function —— 后者会跟内层重名的 const 打架）
const inDrawer = (fnBody) => page.evaluate(`(() => {
  const d = [...document.querySelectorAll('.mantine-Drawer-content')]
    .filter((x) => { const r = x.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
    .find((x) => [...x.querySelectorAll('button')].some((b) => ['画布','资产'].includes((b.innerText||'').trim())));
  if (!d) return { __err: 'asset drawer not found' };
  ${fnBody}
})()`);
const drawers = () => page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  return [...document.querySelectorAll('.mantine-Drawer-content')].filter(vis).map((d, i) => {
    const r = d.getBoundingClientRect();
    return { i, box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      head: (d.innerText || '').replace(/\s+/g, ' ').slice(0, 60),
      hasTabs: [...d.querySelectorAll('button')].some((b) => ['画布', '资产'].includes((b.innerText || '').trim())) };
  });
});

// 开抽屉（若未开）
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
out.drawersAfterOpen = await drawers();
out.rowsBefore = await inDrawer('return (d.innerText||"").replace(/\\s+/g," ").slice(0,200);');

const tabClick = await inDrawer(`
  [...d.querySelectorAll('button')].find((b) => (b.innerText||'').trim() === '资产')?.click();
  return true;`);
out.tabClick = tabClick;
await page.waitForTimeout(1600);
out.rowsOnAsset = await inDrawer('return (d.innerText||"").replace(/\\s+/g," ").slice(0,200);');

const openRowMenu = () => inDrawer(`
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const b = [...d.querySelectorAll('[aria-label="更多操作"]')].filter(vis)[0];
  if (!b) return { ok:false, why:'0 个更多操作' };
  b.click(); return { ok:true };`);
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
  return { ok: true, rows: [...last.querySelectorAll('button')].map((b) => (b.innerText || '').trim()).filter(Boolean) };
});

out.openRowMenu = await openRowMenu();
await page.waitForTimeout(1000);
out.menu8 = await page.evaluate(() => [...document.querySelectorAll('.mantine-Menu-item, [role="menuitem"]')]
  .filter((el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
  .map((el) => (el.innerText || '').trim()).filter(Boolean));
out.base = (await hoverItem('移动到'), await readSubmenu());
await shot(page, 'M-292-资产页-移动到子菜单.png', { clip: { x: 100, y: 190, width: 480, height: 420 } });

// 建本轮自己的子文件夹
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
  return { ok: true, text: (last.innerText || '').replace(/\s+/g, ' ').slice(0, 200),
    inputs: [...last.querySelectorAll('input')].map((i) => ({ ph: i.placeholder, aria: i.getAttribute('aria-label') })),
    btns: [...last.querySelectorAll('button')].map((b) => (b.innerText || b.getAttribute('aria-label') || '').trim()).filter(Boolean) };
});
out.folderName = MY_FOLDER;

await writeFile(resolve(HERE, '.evidence/cb10-a.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify({ drawersBefore: out.drawersBefore, rowsOnAsset: out.rowsOnAsset, menu8: out.menu8, base: out.base, clickedNew: out.clickedNew, dialog: out.dialog }, null, 2));
await browser.close();

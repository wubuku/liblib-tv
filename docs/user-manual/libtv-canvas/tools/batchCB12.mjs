// Batch CB-12：「移动到 ›」的活/死对照，全流程。
//   ① 建一个**本轮自己的**子文件夹（行内输入 aria-label="素材名称"）
//   ② 回到「更多操作 → 移动到 ›」，看子菜单从 1 项变成几项
//   ③ 删掉**本轮自己建的那个**（按名字认，不按位置/顺序 —— CA 事故教训）
//   ④ 删完再读一次，确认回到 1 项
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const MY_FOLDER = 'CB12临时文件夹';

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
const clickTab = (n) => inDrawer(`[...d.querySelectorAll('button')].find((b)=>(b.innerText||'').trim()===${JSON.stringify(n)})?.click(); return 1;`);
const drawerText = () => inDrawer(`return (d.innerText||'').replace(/\\s+/g,' ').slice(0,240);`);

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
const openRowMenuByName = (rowName) => inDrawer(`
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const rows = [...d.querySelectorAll('*')].filter((el) => {
    const r = el.getBoundingClientRect();
    return vis(el) && (el.innerText||'').trim() === ${JSON.stringify(rowName)} && el.querySelector('[aria-label="更多操作"]');
  });
  const btn = rows[0] ? rows[0].querySelector('[aria-label="更多操作"]') : [...d.querySelectorAll('[aria-label="更多操作"]')].filter(vis)[0];
  if (!btn) return { ok:false, why:'找不到行' };
  btn.click(); return { ok:true, rows: rows.length };`);

// —— 准备：开抽屉 → 资产页 ——
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
await clickTab('资产');
await page.waitForTimeout(1600);
out.t0 = await drawerText();

// —— ① 建子文件夹 ——
await openRowMenuByName('待分类资产');
await page.waitForTimeout(900);
await hoverItem('新建子文件夹');
await page.evaluate(() => {
  const it = [...document.querySelectorAll('.mantine-Menu-item, [role="menuitem"]')]
    .find((el) => (el.innerText || '').trim() === '新建子文件夹');
  if (it) it.click();
});
await page.waitForTimeout(1300);
out.renameInput = await inDrawer(`
  const i = [...d.querySelectorAll('input[aria-label="素材名称"]')][0];
  return i ? { found: true, val: i.value, focused: document.activeElement === i } : { found: false };`);
if (out.renameInput.found) {
  await inDrawer(`
    const i = [...d.querySelectorAll('input[aria-label="素材名称"]')][0];
    i.focus(); i.select();
    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
    setter.call(i, ${JSON.stringify(MY_FOLDER)});
    i.dispatchEvent(new Event('input', { bubbles: true }));
    return 1;`);
  await page.waitForTimeout(400);
  await page.keyboard.press('Enter');
  await page.waitForTimeout(1800);
}
out.t1_afterCreate = await drawerText();
await shot(page, 'M-293-资产页-新建子文件夹之后.png', { clip: { x: 0, y: 80, width: 700, height: 400 } });

// —— ② 再看「移动到 ›」有几项 ——
await page.keyboard.press('Escape');
await page.waitForTimeout(500);
out.openMenu2 = await openRowMenuByName('待分类资产');
await page.waitForTimeout(900);
out.moveBox2 = await hoverItem('移动到');
out.submenu2 = await readSubmenu();
await shot(page, 'M-292-资产页-移动到子菜单.png', { clip: { x: 100, y: 190, width: 500, height: 430 } });

// —— ③ 删掉本轮自己建的那个（按名字认） ——
out.mineFound = await inDrawer(`
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const all = [...d.querySelectorAll('*')].filter((el) => vis(el) && (el.innerText||'').trim() === ${JSON.stringify(MY_FOLDER)});
  const mine = all.find((el) => el.querySelector('[aria-label="更多操作"]'));
  if (!mine) return { found: false, sameText: all.length };
  mine.querySelector('[aria-label="更多操作"]').click();
  return { found: true };`);
await page.waitForTimeout(900);
await page.evaluate(() => {
  const it = [...document.querySelectorAll('.mantine-Menu-item, [role="menuitem"]')]
    .find((el) => (el.innerText || '').trim() === '删除');
  if (it) it.click();
});
await page.waitForTimeout(1200);
out.confirmDialog = await page.evaluate(() => {
  const d = [...document.querySelectorAll('.mantine-Modal-content, [role="dialog"]')]
    .filter((el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
    .find((el) => /确定删除|删除后不可恢复/.test(el.innerText || ''));
  if (!d) return { ok: false };
  return { ok: true, text: (d.innerText || '').replace(/\s+/g, ' ').slice(0, 160),
    btns: [...d.querySelectorAll('button')].map((b) => (b.innerText || '').trim()).filter(Boolean) };
});
out.t2_beforeDelete = await drawerText();

await writeFile(resolve(HERE, '.evidence/cb12.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify({ t0: out.t0, renameInput: out.renameInput, t1: out.t1_afterCreate, submenu2: out.submenu2, mineFound: out.mineFound, confirmDialog: out.confirmDialog, t2: out.t2_beforeDelete }, null, 2));
await browser.close();

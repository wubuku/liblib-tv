// Batch CB-19：重拍三张构图正确的图。
//   ① 「更多操作」八项 + 悬停「移动到」后浮出的子菜单（**只有「个人资产库」一项**）
//   ② 「新建子文件夹」是**行内输入**，不是弹窗
//   ③ 展开后的文件夹树（子文件夹是待分类资产的**子级**，但**不出现在移动到子菜单里**）
// ⛔ 本轮不建任何东西：③ 靠「展开已有结构」取证，不新建。
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

await page.evaluate(async () => {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  for (let i = 0; i < 6; i += 1) {
    const hit = [...document.querySelectorAll('button, [role="button"]')].find((b) => (b.innerText || '').trim() === '知道了');
    if (hit) { hit.click(); await sleep(500); }
    if (!(document.body.innerText || '').includes('已升级为 TV Director')) return;
  }
});
await page.waitForTimeout(800);

const inDrawer = (fnBody) => page.evaluate(`(() => {
  const d = [...document.querySelectorAll('.mantine-Drawer-content')]
    .filter((x) => { const r = x.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
    .find((x) => [...x.querySelectorAll('button')].some((b) => ['画布','资产'].includes((b.innerText||'').trim())));
  if (!d) return { __err: 'asset drawer not found' };
  ${fnBody}
})()`);

await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const c = [...document.querySelectorAll('[aria-label="资产管理"]')].filter(vis)
    .map((el) => ({ el, r: el.getBoundingClientRect() })).filter((o) => o.r.x < 100).sort((a, b) => a.r.x - b.r.x);
  c[0]?.el.click();
});
await page.waitForTimeout(1600);
await inDrawer(`[...d.querySelectorAll('button')].find((b)=>(b.innerText||'').trim()==='资产')?.click(); return 1;`);
await page.waitForTimeout(1600);

const hoverItem = async (name) => {
  const box = await page.evaluate((n) => {
    const it = [...document.querySelectorAll('.mantine-Menu-item, [role="menuitem"]')]
      .find((el) => (el.innerText || '').trim() === n);
    if (!it) return null;
    const r = it.getBoundingClientRect();
    return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
  }, name);
  if (!box) return null;
  await page.mouse.move(60, 260, { steps: 6 });
  await page.mouse.move(box[0] + box[2] / 2, box[1] + box[3] / 2, { steps: 12 });
  await page.waitForTimeout(1200);
  return box;
};

// —— ① 八项菜单 + 移动到子菜单 ——
await inDrawer(`
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  [...d.querySelectorAll('[aria-label="更多操作"]')].filter(vis)[0]?.click();
  return 1;`);
await page.waitForTimeout(1000);
out.menu8 = await page.evaluate(() => [...document.querySelectorAll('.mantine-Menu-item, [role="menuitem"]')]
  .filter((el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
  .map((el) => (el.innerText || '').trim()).filter(Boolean));
out.moveBox = await hoverItem('移动到');
out.submenu = await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const dd = [...document.querySelectorAll('.mantine-Popover-dropdown')].filter(vis);
  if (!dd.length) return { ok: false };
  const last = dd[dd.length - 1];
  return { ok: true, rows: [...last.querySelectorAll('button')].map((b) => (b.innerText || '').trim()).filter(Boolean) };
});
out.shot1 = await shot(page, 'M-292-资产页-移动到子菜单只有个人资产库.png', { clip: { x: 0, y: 120, width: 620, height: 430 } });

// —— ② 新建子文件夹 = 行内输入 ——
await page.keyboard.press('Escape');
await page.waitForTimeout(600);
await inDrawer(`
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  [...d.querySelectorAll('[aria-label="更多操作"]')].filter(vis)[0]?.click();
  return 1;`);
await page.waitForTimeout(900);
await hoverItem('新建子文件夹');
await page.evaluate(() => {
  const it = [...document.querySelectorAll('.mantine-Menu-item, [role="menuitem"]')]
    .find((el) => (el.innerText || '').trim() === '新建子文件夹');
  if (it) it.click();
});
await page.waitForTimeout(1400);
out.inline = await inDrawer(`
  const i = [...d.querySelectorAll('input[aria-label="素材名称"]')][0];
  return i ? { val: i.value, focused: document.activeElement === i,
    box: (() => { const r = i.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })() } : { found: false };`);
out.shot2 = await shot(page, 'M-293-资产页-新建子文件夹是行内输入.png', { clip: { x: 0, y: 120, width: 620, height: 400 } });
// ⛔ 不提交：按 Esc 撤销这次行内输入
await page.keyboard.press('Escape');
await page.waitForTimeout(700);
out.afterEscape = await inDrawer(`return (d.innerText||'').replace(/\\s+/g,' ').slice(0,200);`);

// —— ③ 展开文件夹树 ——
out.expandArrow = await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const more = [...document.querySelectorAll('[aria-label="更多操作"]')].filter(vis)[0];
  if (!more) return { ok: false };
  const mr = more.getBoundingClientRect();
  const cands = [...document.querySelectorAll('svg, button, [role="button"]')].filter(vis)
    .map((k) => ({ k, r: k.getBoundingClientRect() }))
    .filter((c) => Math.abs((c.r.y + c.r.height / 2) - (mr.y + mr.height / 2)) < 12 && c.r.x < mr.x - 20)
    .sort((a, b) => a.r.x - b.r.x);
  if (!cands.length) return { ok: false, why: '找不到箭头' };
  return { ok: true, at: [Math.round(cands[0].r.x), Math.round(cands[0].r.y + cands[0].r.height / 2)] };
});
if (out.expandArrow?.ok) {
  await page.mouse.move(out.expandArrow.at[0], out.expandArrow.at[1], { steps: 8 });
  await page.waitForTimeout(500);
  await page.mouse.click(out.expandArrow.at[0], out.expandArrow.at[1]);
  await page.waitForTimeout(1500);
}
out.tree = await inDrawer(`return (d.innerText||'').replace(/\\s+/g,' ').slice(0,200);`);
out.shot3 = await shot(page, 'M-294-资产页-文件夹树默认折叠.png', { clip: { x: 0, y: 120, width: 420, height: 220 } });

// 清理：把刚才可能展开的树收回原状（点同一箭头）
if (out.expandArrow?.ok) {
  await page.mouse.click(out.expandArrow.at[0], out.expandArrow.at[1]);
  await page.waitForTimeout(900);
}
out.final = await inDrawer(`return (d.innerText||'').replace(/\\s+/g,' ').slice(0,200);`);

await writeFile(resolve(HERE, '.evidence/cb19-shots.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify({ menu8: out.menu8, submenu: out.submenu, inline: out.inline, afterEscape: out.afterEscape, tree: out.tree, final: out.final, shots: [out.shot1, out.shot2, out.shot3] }, null, 2));
await browser.close();

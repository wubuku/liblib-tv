// Batch CB-15：CB14 两条独立路径都查不到新建的文件夹。但**先别急着判它「没落盘」**
// —— 万一 Enter 不是正确的提交方式呢？
// 这一步把「提交方式」当成变量来做：改用**失焦（blur）**提交 + 等 3 秒，再整页刷新。
//   两次都用完全相同的动作，只让「提交方式」这一个变量变。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const MY_FOLDER = 'CB15临时文件夹';

const { browser, page } = await launch();
const out = {};

const dismissPromo = async () => {
  await page.evaluate(async () => {
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    for (let i = 0; i < 6; i += 1) {
      const hit = [...document.querySelectorAll('button, [role="button"]')].find((b) => (b.innerText || '').trim() === '知道了');
      if (hit) { hit.click(); await sleep(500); }
      if (!(document.body.innerText || '').includes('已升级为 TV Director')) return;
    }
  });
  await page.waitForTimeout(700);
};

const inDrawer = (fnBody) => page.evaluate(`(() => {
  const d = [...document.querySelectorAll('.mantine-Drawer-content')]
    .filter((x) => { const r = x.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
    .find((x) => [...x.querySelectorAll('button')].some((b) => ['画布','资产'].includes((b.innerText||'').trim())));
  if (!d) return { __err: 'asset drawer not found' };
  ${fnBody}
})()`);

const openAssetPage = async () => {
  await page.evaluate(() => {
    const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    const has = [...document.querySelectorAll('.mantine-Drawer-content')].filter(vis)
      .some((d) => [...d.querySelectorAll('button')].some((b) => ['画布', '资产'].includes((b.innerText || '').trim())));
    if (has) return;
    const c = [...document.querySelectorAll('[aria-label="资产管理"]')].filter(vis)
      .map((el) => ({ el, r: el.getBoundingClientRect() })).filter((o) => o.r.x < 100).sort((a, b) => a.r.x - b.r.x);
    c[0]?.el.click();
  });
  await page.waitForTimeout(1600);
  await inDrawer(`[...d.querySelectorAll('button')].find((b)=>(b.innerText||'').trim()==='资产')?.click(); return 1;`);
  await page.waitForTimeout(1600);
};

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
  await page.waitForTimeout(1100);
  return box;
};

await open(page, URL_);
await closePromos(page);
await dismissPromo();
await openAssetPage();

out.before = await inDrawer(`return (d.innerText||'').replace(/\\s+/g,' ').slice(0,240);`);

// 建（行内输入 + **失焦**提交）
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
await page.waitForTimeout(1300);
out.inputAppeared = await inDrawer(`
  const i = [...d.querySelectorAll('input[aria-label="素材名称"]')][0];
  return i ? { val: i.value, focused: document.activeElement === i } : { found:false };`);

if (out.inputAppeared?.val) {
  await inDrawer(`
    const i = [...d.querySelectorAll('input[aria-label="素材名称"]')][0];
    i.focus(); i.select();
    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
    setter.call(i, ${JSON.stringify(MY_FOLDER)});
    i.dispatchEvent(new Event('input', { bubbles: true }));
    i.blur();
    return 1;`);
  await page.waitForTimeout(3000);   // ⭐ 给它 3 秒落盘
}
out.afterBlur = await inDrawer(`return (d.innerText||'').replace(/\\s+/g,' ').slice(0,240);`);
out.inListBeforeReload = (out.afterBlur || '').includes(MY_FOLDER);
await shot(page, 'M-293-资产页-新建子文件夹之后.png', { clip: { x: 0, y: 80, width: 700, height: 400 } });

// ⭐ 整页刷新
await open(page, URL_);
await closePromos(page);
await dismissPromo();
await openAssetPage();
out.afterReload = await inDrawer(`return (d.innerText||'').replace(/\\s+/g,' ').slice(0,300);`);
out.inListAfterReload = (out.afterReload || '').includes(MY_FOLDER);

// 第二条独立路径：管理弹窗
await inDrawer(`
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  [...d.querySelectorAll('[aria-label="资产管理"]')].filter(vis)[0]?.click();
  return 1;`);
await page.waitForTimeout(2000);
out.manage = await page.evaluate((name) => {
  const m = [...document.querySelectorAll('.mantine-Modal-content, [role="dialog"]')]
    .filter((el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
    .find((el) => /资产库/.test(el.innerText || '') && el.innerText.length < 3000);
  if (!m) return { ok: false };
  return { ok: true, text: (m.innerText || '').replace(/\s+/g, ' ').slice(0, 500), has: (m.innerText || '').includes(name) };
}, MY_FOLDER);

await writeFile(resolve(HERE, '.evidence/cb15-persist.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify({ before: out.before, inputAppeared: out.inputAppeared, afterBlur: out.afterBlur, inListBeforeReload: out.inListBeforeReload, afterReload: out.afterReload, inListAfterReload: out.inListAfterReload, manage: out.manage }, null, 2));
await browser.close();

// Batch CB-4：用**真指针**悬停 `移动到`，让 Mantine 真正展开子菜单。
// ⭐ CB-3 的教训：合成 `MouseEvent` 点得开主菜单，却开不了子菜单 ——
//   主菜单是 click 触发，子菜单是 pointerover 触发，合成事件的 `isTrusted=false` 被忽略。
//   **「点开了」不等于「hover 也生效」**，两种触发方式必须分开验。
// ⚠️ 仍然只读：子菜单展开了就截图，一个子菜单项都不点（搬动资产会改用户的文件夹结构）。
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
const readMenu = () => page.evaluate(() => [...document.querySelectorAll('.mantine-Menu-item, [role="menuitem"]')]
  .filter((el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
  .map((el) => {
    const r = el.getBoundingClientRect();
    return { t: (el.innerText || '').trim(), box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
  }).filter((o) => o.t));

// 开抽屉 → 资产页签 → 更多操作
await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  [...document.querySelectorAll('[aria-label="资产管理"]')].filter(vis)
    .map((el) => ({ el, r: el.getBoundingClientRect() }))
    .filter((c) => c.r.x < 100).sort((a, b) => a.r.x - b.r.x)[0]?.el.click();
});
await page.waitForTimeout(1500);
await page.evaluate(() => {
  const d = document.querySelector('.mantine-Drawer-content');
  [...d.querySelectorAll('button')].find((b) => (b.innerText || '').trim() === '资产')?.click();
});
await page.waitForTimeout(1500);
await page.evaluate(() => {
  const d = document.querySelector('.mantine-Drawer-content');
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  [...d.querySelectorAll('[aria-label="更多操作"]')].filter(vis)[0]?.click();
});
await page.waitForTimeout(900);

// ⭐ 真指针：一步步移到「移动到」上，模拟真实鼠标轨迹
const moveBox = [130, 379, 166, 36];
const cx = moveBox[0] + moveBox[2] / 2;
const cy = moveBox[1] + moveBox[3] / 2;
await page.mouse.move(200, 300, { steps: 6 });
await page.mouse.move(cx, cy, { steps: 12 });
await page.waitForTimeout(1200);
out.submenuAfterRealHover = await readMenu();
await shot(page, 'M-292-资产页-移动到子菜单.png', { clip: { x: 0, y: 80, width: 820, height: 560 } });

// 再悬停另一个带子项的（更改图标 ›），验证子菜单确实是通用的
const changeBox = out.submenuAfterRealHover.find((o) => o.t === '更改图标')?.box;
if (changeBox) {
  await page.mouse.move(changeBox[0] + changeBox[2] / 2, changeBox[1] + changeBox[3] / 2, { steps: 10 });
  await page.waitForTimeout(1100);
  out.afterHoverChangeIcon = await readMenu();
}

await writeFile(resolve(HERE, '.evidence/cb4-submenu.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify({ moveCount: out.submenuAfterRealHover.length, items: out.submenuAfterRealHover.map((o) => o.t) }, null, 2));
await browser.close();

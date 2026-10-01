// 探针 14 —— 把「画布 2」上的九类节点排成一张能当正文插图的总览图。
//
// 为什么不能直接用 ⌘0：节点都是在同一个落点生成的，彼此重叠，⌘0 适配出来的
// 视口算下来是 190%（只框住了最上面那张），拍出来就是一张糊掉的特写。
// 这一版先 ⌥⇧F「整理画布」把节点铺开，再逐级 ⌘- 缩小到能一眼看全。
import { launch, open } from './lib.mjs';
import { CANVAS_URL } from './test-project.mjs';
import { clearToasts, closePromos, shot } from './scenario.mjs';
import { nodeCount, listNodes } from './canvas-ops.mjs';

const CLEAN_ID = '34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=10354929&projectId=${CLEAN_ID}`, { settle: 4000 });
  await closePromos(page);
  await clearToasts(page);
  await page.waitForTimeout(1200);
  console.log('节点数:', await nodeCount(page));

  // 整理画布：⌥⇧F（底部工具条上那个 aria-label 就写着一模一样的键）
  const tidy = page.getByRole('button', { name: '整理画布，Option+Shift+F', exact: true }).first();
  if (await tidy.count()) {
    await page.keyboard.press('Escape');
    await page.mouse.click(180, 150);
    await page.waitForTimeout(300);
    await page.keyboard.press('Alt+Shift+KeyF');
    await page.waitForTimeout(2500);
    console.log('已按 ⌥⇧F 整理');
  }
  await shot(page, 'D-98-整理画布后.png');

  // 逐级缩小，直到所有节点都在视口内
  for (let i = 0; i < 4; i += 1) {
    await page.keyboard.press('Meta+-');
    await page.waitForTimeout(600);
  }
  const zoomLabel = await page.evaluate(() => document.querySelector('button[aria-label="缩放选项"]')?.innerText?.trim());
  console.log('当前缩放:', zoomLabel);

  const fit = await page.evaluate(() =>
    [...document.querySelectorAll('.react-flow__node')].map((n) => {
      const r = n.getBoundingClientRect();
      return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
    }),
  );
  const outside = fit.filter((r) => r.x + r.w < 0 || r.y + r.h < 0 || r.x > 1440 || r.y > 810);
  console.log('节点数:', fit.length, '出界:', outside.length);

  await shot(page, 'D-99-九类节点总览.png');
  console.log('shot D-99-九类节点总览.png');
} finally {
  await browser.close();
}

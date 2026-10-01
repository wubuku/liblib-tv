// 探针 15 —— 收尾整理画布的取证：
//  1) 「是否保留此次整理结果？」这个确认条本身就是手册该写的东西，单独拍一张；
//  2) 点「保留」之后再拍一张 50% 的九类节点总览（20% 太糊，190% 只框住一张）；
//  3) 顺手拍一张视频节点选中态的完整编辑器（参考/标记/特效/角色库/运镜 + 底部参数条）。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, shotHighlighted } from './scenario.mjs';
import { nodeCount } from './canvas-ops.mjs';

const CLEAN_ID = '34226ef170f248248c74f85290228f6b';
const URL = `https://www.liblib.tv/canvas?spaceId=10354929&projectId=${CLEAN_ID}`;
const { browser, page } = await launch();

const setZoom = async (label) => {
  await page.getByRole('button', { name: '缩放选项', exact: true }).first().click();
  await page.waitForTimeout(700);
  const item = page.getByText(`缩放至${label}`, { exact: false }).first();
  if (await item.count()) { await item.click(); await page.waitForTimeout(1200); }
  else { await page.keyboard.press('Escape'); }
};

try {
  await open(page, URL, { settle: 4000 });
  await closePromos(page);
  await clearToasts(page);
  await page.waitForTimeout(1200);
  console.log('节点数:', await nodeCount(page));

  // 1) 整理画布 → 确认条
  await page.mouse.click(180, 150);
  await page.keyboard.press('Alt+Shift+KeyF');
  await page.waitForTimeout(2500);
  const keep = page.getByRole('button', { name: '保留', exact: true }).first();
  if (await keep.count()) {
    await shotHighlighted(page, keep, 'E-01-整理画布确认条.png', { step: 1 });
    console.log('确认条文案:', await page.evaluate(() => {
      const el = [...document.querySelectorAll('div')].find((d) => /是否保留此次整理结果/.test(d.innerText || '') && d.getBoundingClientRect().width < 400);
      return el ? (el.innerText || '').replace(/\s+/g, ' ') : null;
    }));
    await keep.click();
    await page.waitForTimeout(1500);
  } else {
    console.log('未出现整理确认条');
  }

  // 2) 50% 总览
  await setZoom('50%');
  await page.waitForTimeout(1200);
  await shot(page, 'E-02-九类节点总览-50.png');

  // 3) 视频节点选中态编辑器特写
  const v = page.locator('.react-flow__node').filter({ hasText: '视频节点' }).first();
  if (await v.count()) {
    await v.click({ force: true });
    await page.waitForTimeout(1800);
    await setZoom('50%');
    await page.waitForTimeout(800);
    await shot(page, 'E-03-视频节点编辑器.png');
    console.log('视频节点编辑器:', await page.evaluate(() => {
      const n = [...document.querySelectorAll('.react-flow__node')].find((x) => (x.innerText || '').includes('视频节点'));
      return n ? (n.innerText || '').replace(/\s+/g, ' ').slice(0, 600) : null;
    }));
  }
  console.log('done');
} finally {
  await browser.close();
}

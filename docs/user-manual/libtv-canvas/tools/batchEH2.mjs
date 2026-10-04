// Batch EH-2：为 M-356 拍「网格吸附」按钮两态的**并排对比**图。
//
// ⭐ 拍法要点（EF 批教训 §109.4）：
//   ① 读者要能**一眼看出差别** ⇒ 两态并排；
//   ② 状态切换必须有**读数自证**（svg 数 1 ↔ 2），不能只靠肉眼看图；
//   ③ 不用 injectHighlight —— 那会盖住图标，看不清「多了一个斜杠」这个关键差别。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const OUT = new URL('./batchEH2.json', import.meta.url).pathname;
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {} };

const { browser, page } = await launch();
try {
  await open(page, CANVAS_URL, { settle: 6500 });
  await closePromos(page);
  await page.waitForTimeout(1200);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(1500);

  const 读 = () => page.evaluate(() => {
    const b = document.querySelector('button[aria-label="网格吸附"]');
    return {
      svg数: b.querySelectorAll('svg').length,
      cls: [...b.querySelectorAll('svg')].map(s => s.getAttribute('class')),
      box: (() => { const r = b.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]; })(),
    };
  });

  const 关态 = await 读();
  console.log('关态:', JSON.stringify(关态));

  // ⭐ 放大视口到按钮附近（用 ⌘0 后再 zoom），把工具条那一排拍全
  const clip = { x: 0, y: Math.max(0, 关态.box[1] - 26), width: 300, height: 70 };

  // 状态 1（关）→ 截图
  await page.screenshot({ path: 'tools/.evidence/eh2-1-关.png', clip });
  console.log('已拍关态');

  // ⭐ 在**同一个 clip 位置**切到开态再拍 —— 两张图可直接并排
  await page.evaluate(() => document.querySelector('button[aria-label="网格吸附"]').click());
  await page.waitForTimeout(1300);
  const 开态 = await 读();
  console.log('开态:', JSON.stringify(开态));
  await page.screenshot({ path: 'tools/.evidence/eh2-2-开.png', clip });
  console.log('已拍开态');

  // ⭐ 还原状态
  await page.evaluate(() => document.querySelector('button[aria-label="网格吸附"]').click());
  await page.waitForTimeout(1200);
  const 复原 = await 读();
  console.log('还原后:', JSON.stringify(复原));

  结果.读数 = { 关态, 开态, 复原, clip };
  落盘(结果);
  console.log('\n两张对比图在 tools/.evidence/eh2-1-关.png 与 eh2-2-开.png');
} catch (e) {
  结果.错误 = String(e && e.stack || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEH2.json ===');
}

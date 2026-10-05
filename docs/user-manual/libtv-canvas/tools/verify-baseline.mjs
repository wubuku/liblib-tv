// 刷新后核对新基线是否真的落盘（只读，不动任何东西）
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标, 核对坐标, 读全部坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = HERE + '.evidence/';
const 日志 = [];
const 记 = (s) => { 日志.push(s); writeFileSync(HERE + 'verify-baseline.json', JSON.stringify({ 日志 }, null, 2)); console.log('· ' + s); };

const 浏览器 = await launch();
const page = 浏览器.page;
try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(12000);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(4000);
  const vp = await page.evaluate(() => {
    const v = document.querySelector('.react-flow__viewport');
    return v ? getComputedStyle(v).transform : null;
  });
  const 全 = await 读全部坐标(page);
  记(`刷新后 viewport = ${vp}｜渲染 ${Object.keys(全).length} 个节点`);
  for (const [id, xy] of Object.entries(坐标)) {
    记(`   ${id} 基线${JSON.stringify(xy)} 现${JSON.stringify(全[id] || '未渲染')}`);
  }
  const 差 = await 核对坐标(page);
  记('核对坐标 = ' + (差.length ? JSON.stringify(差) : '[]（全部一致）✅'));
  await page.screenshot({ path: EVID + 'fb14-01-新基线整屏.png' });
  // 再刷一次，确认稳定
  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(12000);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(4000);
  const 差2 = await 核对坐标(page);
  记('第二次刷新后核对坐标 = ' + (差2.length ? JSON.stringify(差2) : '[]（全部一致）✅'));
} catch (e) {
  记('❌ ' + e.message);
} finally {
  await 浏览器.browser.close();
}

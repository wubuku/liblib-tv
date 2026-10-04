// Batch EK-3：只验一件事 —— 悬停「切换小地图」到底出不出气泡。
//   EK-1/EK-2 两次都读到「没有」，但手册 M-344 的实拍图明明有那个气泡。
//   ⭐ EK-2 的方法缺陷：**只在读到气泡时才截图** ⇒ 没读到就没证据可复核。
//   本轮：悬停后**无条件截图**，并全量搜「小地图」三个字（不限叶子节点）。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEK3.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const { browser, page } = await launch();
try {
  await open(page, CANVAS_URL, { settle: 7000 });
  await closePromos(page);
  await page.waitForTimeout(1500);
  await page.evaluate(() => { const b = [...document.querySelectorAll('button')].find(x => (x.innerText || '').trim() === '知道了'); if (b) b.click(); });
  await page.waitForTimeout(800);
  await page.evaluate(() => {
    const 条 = [...document.querySelectorAll('div')].filter(d => /开启浏览器通知/.test(d.innerText || ''));
    if (条.length) { 条.sort((a, b) => b.getBoundingClientRect().width - a.getBoundingClientRect().width); const btn = [...条[条.length - 1].querySelectorAll('button')].find(b => (b.innerText || '').trim() === ''); if (btn) btn.click(); }
  });
  await page.waitForTimeout(700);
  await page.evaluate(() => { for (const b of document.querySelectorAll('button')) if (b.getAttribute('aria-label') === '关闭' && b.getBoundingClientRect().width < 40) { b.click(); return; } });
  await page.waitForTimeout(1000);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(3000);
  记(`开局坐标偏差：${JSON.stringify(await 核对坐标(page))}`);

  const 小地图 = await page.evaluate(() => {
    const b = [...document.querySelectorAll('button')].find(x => (x.getAttribute('aria-label') || '') === '切换小地图');
    if (!b) return null;
    const r = b.getBoundingClientRect();
    return { box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)] };
  });
  记(`切换小地图按钮：${JSON.stringify(小地图)}`);

  // ⭐ 悬停前：全量搜「小地图」
  const 搜 = () => page.evaluate(() => [...document.querySelectorAll('body *')]
    .filter(e => /小地图/.test(e.innerText || ''))
    .map(e => { const r = e.getBoundingClientRect(); return { tag: e.tagName, cls: (e.className || '').toString().slice(0, 50), 文本: (e.innerText || '').trim().slice(0, 20), box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] }; })
    .filter(x => x.box[2] > 0 || x.box[3] > 0));
  记(`悬停前含「小地图」的元素：${JSON.stringify(await 搜())}`);
  await page.screenshot({ path: EVID + 'ek3-0-悬停前.png', clip: { x: 0, y: 700, width: 340, height: 110 } });

  await page.mouse.move(小地图.中心[0] - 2, 小地图.中心[1] - 2);
  await page.waitForTimeout(250);
  await page.mouse.move(小地图.中心[0], 小地图.中心[1]);
  await page.waitForTimeout(3000);
  const 后 = await 搜();
  记(`\n⭐ 悬停 3000ms 后含「小地图」的元素：${JSON.stringify(后)}`);
  结果.读数.悬停后 = 后;
  await page.screenshot({ path: EVID + 'ek3-1-悬停后全视口.png' });
  await page.screenshot({ path: EVID + 'ek3-2-悬停后左下.png', clip: { x: 0, y: 660, width: 400, height: 150 } });
  记('✅ 已拍悬停前 / 悬停后（无条件下都拍）');

  // 阳性对照：同一套手法去悬停「整理画布」（已知会出气泡），证明手法本身有效
  await page.mouse.move(720, 250); await page.waitForTimeout(1200);
  const 整 = await page.evaluate(() => {
    const b = [...document.querySelectorAll('button')].find(x => (x.getAttribute('aria-label') || '').startsWith('整理画布'));
    const r = b.getBoundingClientRect();
    return [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)];
  });
  await page.mouse.move(整[0], 整[1]);
  await page.waitForTimeout(2600);
  const 对照 = await page.evaluate(() => [...document.querySelectorAll('body *')]
    .filter(e => e.children.length === 0 && /整理画布|⌥⇧F/.test(e.innerText || ''))
    .map(e => { const r = e.getBoundingClientRect(); return { 文本: e.innerText.trim(), box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] }; })
    .filter(x => x.box[2] > 0));
  记(`\n阳性对照（悬停「整理画布」）：${JSON.stringify(对照)}`);
  结果.读数.阳性对照 = 对照;
  await page.screenshot({ path: EVID + 'ek3-3-阳性对照-整理画布.png', clip: { x: 0, y: 660, width: 400, height: 150 } });
  落盘(结果);
} catch (e) {
  结果.错误 = String((e && e.stack) || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  try { 记(`⭐ 收尾坐标偏差：${JSON.stringify(await 核对坐标(page))}`); } catch {}
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEK3.json ===');
}

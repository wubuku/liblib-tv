// Batch EK-2：重测底栏 16 枚按钮的悬停气泡。
//   起因：EK-1 只有「整理画布」读到气泡，但手册 20-reference 明明记着
//   「切换小地图」的气泡是「画布小地图」、缩放那枚是「缩放选项」—— 矛盾。
//   ⭐ 先怀疑自己的判据：这轮把悬停加长到 2.6s、扫描窗口放宽到全视口、每枚都拍图。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEK2.json';
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

  const 底栏 = (await page.evaluate(() => [...document.querySelectorAll('button')].map(b => {
    const r = b.getBoundingClientRect();
    if (r.width === 0 || r.height === 0 || r.top < 700) return null;
    if (b.closest('.react-flow__node')) return null;          // ⭐ 排除节点内部的按钮
    return { 文字: (b.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 12), aria: b.getAttribute('aria-label') || '', box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)] };
  }).filter(Boolean).sort((a, b) => a.box[0] - b.box[0])));
  记(`底栏 ${底栏.length} 枚：${JSON.stringify(底栏.map(b => [b.文字 || b.aria || '(无名)', ...b.box]))}`);
  结果.读数.底栏 = 底栏;

  // ⭐ 全视口扫：任何新出现的「叶子文本节点」都算气泡
  const 全视口 = () => page.evaluate(() => [...document.querySelectorAll('body *')]
    .filter(e => e.children.length === 0)
    .map(e => { const r = e.getBoundingClientRect(); const t = (e.innerText || e.textContent || '').trim(); return { 文本: t.slice(0, 26), cls: (e.className || '').toString().slice(0, 44), box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] }; })
    .filter(x => x.文本 && x.文本.length < 20 && x.box[2] > 0 && x.box[2] < 400 && x.box[3] < 100 && x.box[1] > 400));

  结果.读数.结果 = [];
  for (const b of 底栏) {
    await page.mouse.move(720, 250);
    await page.waitForTimeout(1100);
    const 前 = await 全视口();
    await page.mouse.move(b.中心[0] - 3, b.中心[1] - 3);
    await page.waitForTimeout(300);
    await page.mouse.move(b.中心[0], b.中心[1]);          // 再走 3px，确保真的触发 mouseenter
    await page.waitForTimeout(2600);
    const 后 = await 全视口();
    const 新 = 后.filter(y => !前.some(x => x.文本 === y.文本));
    const 名 = b.文字 || b.aria || '(无名)';
    记(`　悬停 ${2600}ms「${名}」：${JSON.stringify(新.map(n => [n.文本, n.box]))}`);
    结果.读数.结果.push({ 名, aria: b.aria, 文字: b.文字, box: b.box, 气泡: 新 });
    if (新.length) {
      const bb = 新[0].box;
      await page.screenshot({ path: EVID + `ek2-气泡-${名.replace(/[^\w一-龥]/g, '')}.png`, clip: { x: Math.max(0, Math.min(bb[0], b.中心[0]) - 250), y: Math.max(0, bb[1] - 70), width: 520, height: 175 } });
    }
    await page.mouse.move(720, 250);
    await page.waitForTimeout(500);
  }
  落盘(结果);
} catch (e) {
  结果.错误 = String((e && e.stack) || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  try { 记(`⭐ 收尾坐标偏差：${JSON.stringify(await 核对坐标(page))}`); } catch {}
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEK2.json ===');
}

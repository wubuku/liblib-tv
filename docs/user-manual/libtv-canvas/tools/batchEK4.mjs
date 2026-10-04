// Batch EK-4：用**修正后的判据**重扫底栏 14 枚按钮的悬停气泡。
//
// ⭐ EK-3 查清了我在 EK-1/EK-2 里的判据缺陷：
//   我用「叶子文本节点」（children.length === 0）找气泡，
//   而 Mantine Tooltip 的容器 `.mantine-Tooltip-tooltip` **带子元素**（箭头/内层），
//   于是整枚气泡被我滤掉。
//   「整理画布」之所以能读到，是因为它那个气泡是两个**独立**的叶子元素（标题 + ⌥⇧F）。
//   ⇒ 读气泡不能要求叶子，要找「class 含 Tooltip」或「文本长度合适的任意元素」。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEK4.json';
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

  const 底栏 = await page.evaluate(() => [...document.querySelectorAll('button')].map(b => {
    const r = b.getBoundingClientRect();
    if (r.width === 0 || r.height === 0 || r.top < 700) return null;
    if (b.closest('.react-flow__node')) return null;
    return { 文字: (b.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 12), aria: b.getAttribute('aria-label') || '', data: [...b.attributes].filter(a => a.name.startsWith('data-')).map(a => a.name + '=' + a.value).join(' '), box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)] };
  }).filter(Boolean).sort((a, b) => a.box[0] - b.box[0]));
  记(`底栏 ${底栏.length} 枚`);
  结果.读数.底栏 = 底栏;

  // ⭐ 修正后的判据：class 含 Tooltip 的任意元素 + 任何「短文本 + 合理尺寸」的元素
  const 气泡 = () => page.evaluate(() => {
    const 出 = [];
    const 已 = new Set();
    for (const e of document.querySelectorAll('body *')) {
      const cls = (e.className || '').toString();
      const 是Tip = /Tooltip|tooltip/.test(cls);
      const t = (e.innerText || '').trim();
      const r = e.getBoundingClientRect();
      if (!是Tip && !t) continue;
      if (r.width === 0 || r.height === 0) continue;
      if (r.height > 110 || r.width > 460) continue;
      if (r.top < 600) continue;
      if (!t || t.length > 40) continue;
      const k = cls + '|' + t;
      if (已.has(k)) continue;
      已.add(k);
      出.push({ 文本: t.replace(/\s+/g, ' '), cls: cls.slice(0, 50), 是Tooltip类: 是Tip, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] });
    }
    return 出;
  });

  结果.读数.结果 = [];
  for (const b of 底栏) {
    await page.mouse.move(720, 250);
    await page.waitForTimeout(1100);
    const 前 = await 气泡();
    await page.mouse.move(b.中心[0] - 2, b.中心[1] - 2);
    await page.waitForTimeout(250);
    await page.mouse.move(b.中心[0], b.中心[1]);
    await page.waitForTimeout(2400);
    const 后 = await 气泡();
    const 新 = 后.filter(y => !前.some(x => x.文本 === y.文本 && x.box[0] === y.box[0]));
    const 名 = b.文字 || b.aria || '(无名)';
    记(`　悬停「${名}」：${JSON.stringify(新.map(n => [n.文本, n.box, n.是Tooltip类 ? 'Tip' : '普通']))}`);
    结果.读数.结果.push({ 名, aria: b.aria, 文字: b.文字, data: b.data, box: b.box, 气泡: 新 });
    await page.screenshot({ path: EVID + `ek4-悬停-${底栏.indexOf(b) + 1}-${名.replace(/[^\w一-龥]/g, '')}.png`, clip: { x: 0, y: 660, width: 480, height: 150 } });
    await page.mouse.move(720, 250);
    await page.waitForTimeout(450);
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
  console.log('\n=== 已写 tools/batchEK4.json ===');
}

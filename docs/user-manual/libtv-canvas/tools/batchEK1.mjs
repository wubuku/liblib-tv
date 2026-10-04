// Batch EK：左下角工具条 + 底栏中央工具条**全量结案**。
// 手册里这些按钮散落在各章（资产管理 / 角色造型室 / 素材库 / 隐藏节点连线 / 网格吸附 / 缩放…），
// 但从来没有一张「一枚不漏」的总表。本轮逐枚量：无障碍名、悬停气泡、图标 class、几何。
// ⭐ 判据纪律：悬停读气泡要用差分（先移开 → 快照 → 悬停 → 再快照）。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEK1.json';
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

  // ---- 找出两条工具条的容器
  const 容器 = await page.evaluate(() => {
    const 找 = (关键词) => {
      const all = [...document.querySelectorAll('div')].filter(e => {
        const t = (e.innerText || '');
        return t.includes(关键词) && e.getBoundingClientRect().width > 60 && e.getBoundingClientRect().height > 0;
      });
      if (!all.length) return null;
      all.sort((a, b) => a.getBoundingClientRect().width - b.getBoundingClientRect().width);
      return { box: (() => { const r = all[0].getBoundingClientRect(); return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]; })(), cls: all[0].className.toString().slice(0, 110) };
    };
    return { 左下: 找('资产管理'), 中央: 找('+') };
  });
  记(`容器：左下=${JSON.stringify(容器.左下)}；中央=${JSON.stringify(容器.中央)}`);
  结果.读数.容器 = 容器;

  // ---- 把视口底部所有可见按钮端出来，按 x 排序（覆盖两条工具条）
  const 读底栏 = () => page.evaluate(() => [...document.querySelectorAll('button')].map(b => {
    const r = b.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) return null;
    if (r.top < 700) return null;
    const cs = getComputedStyle(b);
    return {
      文字: (b.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 12),
      aria: b.getAttribute('aria-label') || '',
      title: b.getAttribute('title') || '',
      box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
      中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)],
      svg: [...b.querySelectorAll('svg')].map(s => (s.getAttribute('class') || '').slice(0, 34)),
      opacity: cs.opacity, cursor: cs.cursor, disabled: b.disabled === true,
      背景: cs.backgroundColor,
    };
  }).filter(Boolean).sort((a, b) => a.box[0] - b.box[0]));
  const 底栏 = await 读底栏();
  记(`\n底部可见按钮 ${底栏.length} 枚：`);
  for (const b of 底栏) 记(`　[${b.box}] 「${b.文字 || b.aria || '(无名)'}」 svg=${JSON.stringify(b.svg)} opacity=${b.opacity} cursor=${b.cursor}`);
  结果.读数.底栏 = 底栏;

  // ---- 逐枚悬停找气泡（差分法）
  const 快照 = (X, Y) => page.evaluate(([x0, y0]) => [...document.querySelectorAll('body *')]
    .filter(e => e.children.length === 0)
    .map(e => { const r = e.getBoundingClientRect(); const t = (e.innerText || e.textContent || '').trim(); return { 文本: t.slice(0, 26), cls: (e.className || '').toString().slice(0, 44), box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] }; })
    .filter(x => x.文本 && x.文本.length < 18 && x.box[2] > 0 && x.box[2] < 340 && x.box[3] < 90
      && x.box[1] > y0 - 180 && x.box[1] < y0 + 60 && x.box[0] > x0 - 260 && x.box[0] < x0 + 260), [X, Y]);

  结果.读数.气泡 = [];
  for (const b of 底栏) {
    await page.mouse.move(720, 300);
    await page.waitForTimeout(800);
    const 前 = await 快照(b.中心[0], b.中心[1]);
    await page.mouse.move(b.中心[0], b.中心[1]);
    await page.waitForTimeout(1500);
    const 后 = await 快照(b.中心[0], b.中心[1]);
    const 新 = 后.filter(y => !前.some(x => x.文本 === y.文本));
    const 记项 = { box: b.box, 名字: b.文字 || b.aria || '(无名)', 气泡: 新.map(n => [n.文本, n.box]) };
    记(`　悬停「${记项.名字}」：${JSON.stringify(记项.气泡)}`);
    结果.读数.气泡.push(记项);
    if (新.length) {
      const bb = 新[0].box;
      await page.screenshot({ path: EVID + `ek1-气泡-${记项.名字.replace(/[^\w一-龥]/g, '')}.png`, clip: { x: Math.max(0, bb[0] - 230), y: Math.max(0, bb[1] - 60), width: 500, height: 160 } });
    }
    await page.mouse.move(720, 300);
    await page.waitForTimeout(400);
  }

  await page.screenshot({ path: EVID + 'ek1-底栏全图.png' });
  await page.screenshot({ path: EVID + 'ek1-左下工具条裁图.png', clip: { x: 0, y: 740, width: 320, height: 70 } });
  await page.screenshot({ path: EVID + 'ek1-中央工具条裁图.png', clip: { x: 560, y: 740, width: 680, height: 70 } });
  记('✅ 已拍两张裁图');
  落盘(结果);
} catch (e) {
  结果.错误 = String((e && e.stack) || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  try { 记(`⭐ 收尾坐标偏差：${JSON.stringify(await 核对坐标(page))}`); } catch {}
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEK1.json ===');
}

// Batch EI-7：① 修 EI-6 的悬停差分 bug（cx 没传进 page.evaluate）② 读全两枚无名按钮的 innerHTML
// ③ 单独确认「打组」右上角那枚状态圆点的确切颜色
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEI7.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const { browser, page } = await launch();
try {
  await open(page, CANVAS_URL, { settle: 6500 });
  await closePromos(page);
  await page.waitForTimeout(1500);
  for (const t of ['知道了', '知道了']) {
    const r = await page.evaluate((tt) => { const b = [...document.querySelectorAll('button')].find(x => (x.innerText || '').trim() === tt); if (!b) return false; b.click(); return true; }, t);
    if (r) { await page.waitForTimeout(800); 记(`点了「${t}」`); }
  }
  await page.evaluate(() => {
    const 条 = [...document.querySelectorAll('div')].filter(d => /开启浏览器通知/.test(d.innerText || ''));
    if (!条.length) return;
    条.sort((a, b) => b.getBoundingClientRect().width - a.getBoundingClientRect().width);
    const btn = [...条[条.length - 1].querySelectorAll('button')].find(b => (b.innerText || '').trim() === '');
    if (btn) btn.click();
  });
  await page.waitForTimeout(700);
  await page.evaluate(() => {
    for (const b of document.querySelectorAll('button')) if (b.getAttribute('aria-label') === '关闭' && b.getBoundingClientRect().width < 40) { b.click(); return; }
  });
  await page.waitForTimeout(1000);
  const 残留 = await page.evaluate(() => /开启浏览器通知|让\s*TV\s*Director\s*辅助/.test(document.body.innerText || ''));
  记(`遮挡残留：${残留}`);

  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(1800);

  const 位置 = await page.evaluate(() => {
    const out = {};
    for (const id of ['i-9nlG6HdjK2', 'i-sODTbgLUm1']) {
      const r = document.querySelector(`.react-flow__node[data-id="${id}"]`).getBoundingClientRect();
      out[id] = [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)];
    }
    return out;
  });
  const a = 位置['i-9nlG6HdjK2'], b = 位置['i-sODTbgLUm1'];
  await page.mouse.move(Math.min(a[0], b[0]) - 20, Math.min(a[1], b[1]) - 10);
  await page.mouse.down();
  await page.mouse.move(Math.max(a[0] + a[2], b[0] + b[2]) + 20, Math.max(a[1] + a[3], b[1] + b[3]) + 20, { steps: 16 });
  await page.waitForTimeout(300);
  await page.mouse.up();
  await page.mouse.move(700, 700);
  await page.waitForTimeout(1800);

  // ① 工具条全部按钮的**完整** innerHTML + 文本节点
  const 详情 = await page.evaluate(() => {
    const 在条上 = (el) => { const r = el.getBoundingClientRect(); return r.top > 70 && r.top < 130 && r.left > 250 && r.left < 1000; };
    return [...document.querySelectorAll('button')].filter(b => !b.closest('.react-flow__node') && 在条上(b)).map(b => {
      const r = b.getBoundingClientRect();
      const 圆点 = [...b.querySelectorAll('span')].map(s => { const c = getComputedStyle(s); const sr = s.getBoundingClientRect(); return { cls: s.className.toString().slice(0, 70), 背景: c.backgroundColor, 尺寸: [Math.round(sr.width), Math.round(sr.height)], 位置: [Math.round(sr.left), Math.round(sr.top)] }; }).filter(x => x.尺寸[0] > 0);
      return {
        box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
        innerText: (b.innerText || '').trim(),
        文本节点: [...b.childNodes].filter(n => n.nodeType === 3 && n.textContent.trim()).map(n => n.textContent.trim()),
        全html: b.innerHTML.replace(/\s+/g, ' '),
        圆点,
      };
    });
  });
  结果.读数.工具条详情 = 详情;
  for (const d of 详情) {
    记(`[${d.box}] innerText=${JSON.stringify(d.innerText)} 裸文本节点=${JSON.stringify(d.文本节点)} 圆点=${JSON.stringify(d.圆点)}`);
    if (!d.innerText) 记(`   全html: ${d.全html.slice(0, 400)}`);
  }

  // ② ⭐ 悬停差分：这次把 cx/cy 作为参数传进去（EI-6 忘了传 ⇒ ReferenceError）
  const 无名 = 详情.filter(d => !d.innerText);
  for (const t of 无名) {
    const cx = Math.round(t.box[0] + t.box[2] / 2), cy = Math.round(t.box[1] + t.box[3] / 2);
    const 快照 = (X, Y) => page.evaluate(([x0, y0]) => [...document.querySelectorAll('body *')]
      .filter(e => e.children.length === 0)
      .map(e => {
        const r = e.getBoundingClientRect();
        const txt = (e.innerText || e.textContent || '').trim();
        return { 文本: txt.slice(0, 20), cls: (e.className || '').toString().slice(0, 50), box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] };
      })
      .filter(x => x.文本 && x.文本.length < 14 && x.box[2] > 0 && x.box[2] < 300 && x.box[3] < 90
        && Math.abs(x.box[0] - x0) < 220 && Math.abs(x.box[1] - y0) < 130), [X, Y]);

    await page.mouse.move(700, 720);
    await page.waitForTimeout(1300);
    const 前 = await 快照(cx, cy);
    await page.mouse.move(cx, cy);
    await page.waitForTimeout(1700);
    const 后 = await 快照(cx, cy);
    const 新增 = 后.filter(y => !前.some(x => x.文本 === y.文本));
    记(`悬停 [${t.box}]：附近前 ${前.length} 条 → 新出现 ${JSON.stringify(新增)}`);
    结果.读数['悬停_' + t.box[0]] = { 中心: [cx, cy], 新增, 前 };
    if (新增.length) {
      const b = 新增[0].box;
      await page.screenshot({ path: EVID + `ei7-悬停${t.box[0]}.png`, clip: { x: Math.max(0, b[0] - 200), y: Math.max(0, b[1] - 60), width: 460, height: 160 } });
      记(`   ⭐ 气泡读数：box=${JSON.stringify(b)} 文本=${JSON.stringify(新增[0].文本)}`);
    }
    await page.mouse.move(700, 720);
    await page.waitForTimeout(600);
  }
  落盘(结果);
} catch (e) {
  结果.错误 = String((e && e.stack) || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEI7.json ===');
}

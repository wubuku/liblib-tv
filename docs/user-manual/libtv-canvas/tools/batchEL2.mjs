// Batch EL-2：诊断「为什么点图片节点却选中了视频节点」——
//   EL-1 点击 i-9nlG6HdjK2 的中心，选中的却是 v-eMpqKtiLlx。
//   ⭐ 三铁律 ②：任何点击/拖拽前必须先用 elementFromPoint().closest('.react-flow__node')
//      确认落点归属。EL-1 没做这一步，结论作废。
// 本脚本只读：不点任何东西，只量。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEL2.json';
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
  await page.waitForTimeout(3500);
  记(`坐标偏差：${JSON.stringify(await 核对坐标(page))}`);

  // 所有节点：视口矩形 / z-index / DOM 次序
  const 节点表 = await page.evaluate(() => {
    const 出 = [];
    for (const n of document.querySelectorAll('.react-flow__node')) {
      const r = n.getBoundingClientRect();
      if (r.width === 0) continue;
      const cs = getComputedStyle(n);
      出.push({
        id: n.getAttribute('data-id'),
        cls: (n.className || '').toString().slice(0, 90),
        box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
        z: cs.zIndex,
        视口内: r.right > 0 && r.bottom > 0 && r.left < innerWidth && r.top < innerHeight,
        dom序: [...document.querySelectorAll('.react-flow__node')].indexOf(n),
      });
    }
    return 出;
  });
  记(`\n视口内节点 ${节点表.filter(n => n.视口内).length} / 共 ${节点表.length}`);
  for (const n of 节点表) 记(`　${n.id} box=${JSON.stringify(n.box)} z=${n.z} dom序=${n.dom序} ${n.视口内 ? '视口内' : ''}`);
  结果.读数.节点表 = 节点表;

  // ⭐ 网格采样：在图片节点 i-9nlG6HdjK2 的矩形上打 7×7 点，看每个点的 elementFromPoint 归属
  const 采样 = await page.evaluate(() => {
    const 目标 = document.querySelector('.react-flow__node[data-id="i-9nlG6HdjK2"]');
    if (!目标) return null;
    const r = 目标.getBoundingClientRect();
    const 格 = [];
    for (let i = 0; i <= 6; i++) {
      const 行 = [];
      for (let j = 0; j <= 6; j++) {
        const x = Math.round(r.left + r.width * i / 6);
        const y = Math.round(r.top + r.height * j / 6);
        const e = document.elementFromPoint(x, y);
        const 归 = e ? e.closest('.react-flow__node') : null;
        行.push(归 ? (归.getAttribute('data-id') === 'i-9nlG6HdjK2' ? '自己' : 归.getAttribute('data-id')) : '(非节点)');
      }
      格.push(行);
    }
    return { 目标框: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], 格 };
  });
  记(`\n⭐ 图片节点 i-9nlG6HdjK2 视口框 ${JSON.stringify(采样?.目标框)}，7×7 落点归属（行=上→下，列=左→右）：`);
  for (const 行 of 采样.格) 记('　' + 行.map(x => String(x).slice(0, 14).padEnd(14)).join(''));
  结果.读数.落点采样 = 采样;
  await page.screenshot({ path: EVID + 'el2-遮挡诊断.png' });

  // 另一张图片 i-sODTbgLUm1 同样采样
  const 采样2 = await page.evaluate(() => {
    const 目标 = document.querySelector('.react-flow__node[data-id="i-sODTbgLUm1"]');
    if (!目标) return null;
    const r = 目标.getBoundingClientRect();
    if (r.width === 0) return { 不在视口: true };
    const 格 = [];
    for (let i = 0; i <= 6; i++) {
      const 行 = [];
      for (let j = 0; j <= 6; j++) {
        const x = Math.round(r.left + r.width * i / 6);
        const y = Math.round(r.top + r.height * j / 6);
        const e = document.elementFromPoint(x, y);
        const 归 = e ? e.closest('.react-flow__node') : null;
        行.push(归 ? (归.getAttribute('data-id') === 'i-sODTbgLUm1' ? '自己' : 归.getAttribute('data-id')) : '(非节点)');
      }
      格.push(行);
    }
    return { 目标框: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], 格 };
  });
  记(`\n⭐ 图片节点 i-sODTbgLUm1 视口框 ${JSON.stringify(采样2?.目标框)}，7×7 落点归属：`);
  if (采样2?.格) for (const 行 of 采样2.格) 记('　' + 行.map(x => String(x).slice(0, 14).padEnd(14)).join(''));
  结果.读数.落点采样2 = 采样2;
  await page.screenshot({ path: EVID + 'el2-遮挡诊断-图2.png' });

  记('\n✅ 只读诊断，未点击任何节点');
} catch (e) {
  结果.错误 = String((e && e.stack) || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  try { 记(`⭐ 收尾坐标偏差：${JSON.stringify(await 核对坐标(page))}`); } catch {}
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEL2.json ===');
}

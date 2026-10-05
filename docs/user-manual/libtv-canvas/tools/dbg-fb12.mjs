// ⭐⭐ 纯只读：画布现在到底什么状态？（restore-v3 最后一次 11 个节点全部「未渲染」）
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const R = { 步骤: [], 读数: {} };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'dbg-fb12.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };

const 浏览器 = await launch();
const page = 浏览器.page;
const 快照 = () => page.evaluate(() => {
  const v = document.querySelector('.react-flow__viewport');
  const o = { viewport: v ? getComputedStyle(v).transform : null, 节点数: 0, 节点: {} };
  for (const n of document.querySelectorAll('.react-flow__node')) {
    o.节点数++;
    const t = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
    o.节点[n.getAttribute('data-id')] = t ? [Number(t[1]), Number(t[2])] : n.style.transform;
  }
  return o;
});
try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(12000);
  await closePromos(page);
  await page.waitForTimeout(2000);
  const a = await 快照();
  记('进场：viewport = ' + a.viewport + '｜渲染节点数 = ' + a.节点数);
  for (const [id, xy] of Object.entries(坐标)) {
    记(`   ${id} 基线${JSON.stringify(xy)} 渲染${JSON.stringify(a.节点[id] || '未渲染')}`);
  }
  R.读数.进场 = a;
  await page.screenshot({ path: HERE + '.evidence/fb12-01-进场.png' });

  for (const k of ['Meta+0', 'Meta+1', 'Meta+2']) {
    await page.keyboard.press(k);
    await page.waitForTimeout(6000);
    const b = await 快照();
    记(`按 ${k} 后：viewport = ${b.viewport}｜渲染节点数 = ${b.节点数}`);
    if (b.节点数) {
      for (const [id, xy] of Object.entries(坐标)) {
        const n = b.节点[id];
        记(`   ${id} 基线${JSON.stringify(xy)} 渲染${JSON.stringify(n || '未渲染')}${n ? ' 偏差 ' + Math.hypot(n[0] - xy[0], n[1] - xy[1]).toFixed(2) : ''}`);
      }
      R.读数['按' + k] = b;
    }
    await page.screenshot({ path: HERE + `.evidence/fb12-按${k}.png` });
  }
} catch (e) {
  R.错误 = String((e && e.stack) || e);
  记('❌ ' + e.message);
} finally {
  await 浏览器.browser.close();
}

// ⭐⭐⭐ 三件事一次问完：
//   ① 「导演台偏了 2.19」到底是真的，还是 `style.transform` 读数被 hover 污染了？
//      ⇒ 刷新后重读 11 个节点（刷新后没有 hover，最干净）
//   ② hover 污染实验（阳性对照就在同一轮）：鼠标停在一个节点上 vs 移开，各读一次全量 transform
//   ③ 如果损伤是真的，立刻用整数像素复原
//
// ⭐⭐ FB-4 的关键读数：**阳性对照 `t-UtVx3lZmrV` +5px 位移也是 0.0000**，
//   方向键两次也 0 ⇒ 那一刻**整个画布的拖拽都没生效**。
//   于是「-1px 连拖 30 轮不动」就不能当成「导演台特殊」，
//   也不能当成「吸附钉住」—— 判据本身失效了。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const R = { 步骤: [], 读数: {} };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'dbg-fb5.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };

/** 读一个节点的全部定位信息 */
const 读 = (id) => page0.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return null;
  const t = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
  const r = n.getBoundingClientRect();
  return {
    画布: t ? [Number(t[1]), Number(t[2])] : null,
    styleTransform原文: n.style.transform,
    框: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
    中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)],
    class: n.getAttribute('class'),
  };
}, id);

const 全读 = () => page0.evaluate(() => {
  const out = {};
  for (const n of document.querySelectorAll('.react-flow__node')) {
    const t = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
    out[n.getAttribute('data-id')] = t ? [Number(t[1]), Number(t[2])] : null;
  }
  return out;
});

const 浏览器 = await launch();
const page0 = 浏览器.page;
const page = page0;
let 需要复原 = [];

try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(9000);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(3000);
  const z = await page.evaluate(() => {
    const v = document.querySelector('.react-flow__viewport');
    const m = /matrix\(([^)]+)\)/.exec(getComputedStyle(v).transform || '');
    return m ? Number(m[1].split(',')[0]) : 1;
  });
  记('zoom = ' + z);

  // ① 刷新前
  const 前 = await 全读();
  记('① 刷新前 11 节点坐标：');
  for (const [id, xy] of Object.entries(坐标)) {
    const n = 前[id];
    记(`   ${id} 基线${JSON.stringify(xy)} 现${JSON.stringify(n || '未渲染')}${n && Math.hypot(n[0] - xy[0], n[1] - xy[1]) > 0.5 ? '　⛔ 有偏差' : ''}`);
  }
  R.读数.刷新前 = 前;

  // ② hover 污染实验：取两个节点做
  记('—— ② hover 会不会改 style.transform ——');
  for (const id of ['n-56F19pXVB4', 't-UtVx3lZmrV']) {
    const a = await 读(id);
    await page.mouse.move(a.中心[0], a.中心[1]);
    await page.waitForTimeout(700);
    const b = await 读(id);
    await page.mouse.move(720, 170);
    await page.waitForTimeout(900);
    const c = await 读(id);
    记(`   ${id}`);
    记(`     移开前 ${JSON.stringify(a.画布)} 原文 "${a.styleTransform原文}"`);
    记(`     鼠标停上 ${JSON.stringify(b.画布)} 原文 "${b.styleTransform原文}"`);
    记(`     再移开 ${JSON.stringify(c.画布)} 原文 "${c.styleTransform原文}"`);
    记(`     ⭐ 三次一致？ ${JSON.stringify(a.画布) === JSON.stringify(b.画布) && JSON.stringify(b.画布) === JSON.stringify(c.画布)}｜原文一致？ ${a.styleTransform原文 === b.styleTransform原文 && b.styleTransform原文 === c.styleTransform原文}`);
    R.读数['hover_' + id] = { 移开前: a, 停上: b, 再移开: c };
  }

  // ③ 刷新
  记('—— ③ 刷新页面重读 ——');
  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(10000);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(4000);
  const 后 = await 全读();
  记('刷新后 11 节点坐标：');
  const 差 = [];
  for (const [id, xy] of Object.entries(坐标)) {
    const n = 后[id];
    const d = n ? Math.hypot(n[0] - xy[0], n[1] - xy[1]) : 99999;
    记(`   ${id} 基线${JSON.stringify(xy)} 现${JSON.stringify(n || '未渲染')}${d > 0.5 ? '　⛔ 偏差 ' + d.toFixed(3) : ''}`);
    if (d > 0.5) 差.push([id, xy, n, d]);
  }
  R.读数.刷新后 = 后;
  记(差.length ? `⛔ 刷新后仍有 ${差.length} 个节点对不上基线` : '✅ 刷新后全部与基线一致 ⇒ 之前的偏差**没有落盘**');
  需要复原 = 差.map(([id, xy]) => [id, xy]);
} catch (e) {
  R.错误 = String((e && e.stack) || e);
  记('❌ ' + e.message);
} finally {
  if (需要复原.length) {
    记('—— finally：复原 ——');
    for (const [id, 目标] of 需要复原) {
      try {
        for (let 轮 = 1; 轮 <= 30; 轮++) {
          const s = await 读(id);
          if (!s || !s.画布) break;
          const dx = 目标[0] - s.画布[0], dy = 目标[1] - s.画布[1];
          if (Math.hypot(dx, dy) < 0.5) { 记(`  ✅ ${id} 复原到位（轮 ${轮}）`); break; }
          const zz = await page.evaluate(() => {
            const v = document.querySelector('.react-flow__viewport');
            const m = /matrix\(([^)]+)\)/.exec(getComputedStyle(v).transform || '');
            return m ? Number(m[1].split(',')[0]) : 1;
          });
          const px_ = Math.max(-8, Math.min(8, Math.round(dx * zz)));
          const py = Math.max(-8, Math.min(8, Math.round(dy * zz)));
          if (px_ === 0 && py === 0) { 记(`  ⛔ ${id} 整数像素为 0（剩余 ${Math.hypot(dx, dy).toFixed(4)}）`); break; }
          await page.mouse.move(s.中心[0], s.中心[1]); await page.waitForTimeout(300);
          const v = await page.evaluate((p) => {
            const e = document.elementFromPoint(p[0], p[1]);
            const n = e ? e.closest('.react-flow__node') : null;
            return n ? n.getAttribute('data-id') : null;
          }, s.中心);
          if (v !== id) { 记(`  ⛔ ${id} 落点是 ${v}，放弃该轮`); break; }
          await page.mouse.down(); await page.waitForTimeout(140);
          await page.mouse.move(s.中心[0] + px_, s.中心[1] + py, { steps: 6 });
          await page.waitForTimeout(300);
          await page.mouse.up(); await page.waitForTimeout(600);
          await page.mouse.move(720, 170); await page.waitForTimeout(260);
        }
        记(`  ${id} 终态 ${JSON.stringify((await 读(id)).画布)}｜基线 ${JSON.stringify(目标)}`);
      } catch (e2) { 记('  ⛔ 复原抛错：' + e2.message); }
    }
    await page.keyboard.press('Meta+0');
    await page.waitForTimeout(15000);
    const 终 = await 全读();
    const 残 = Object.entries(坐标).filter(([id, xy]) => {
      const n = 终[id]; return !n || Math.hypot(n[0] - xy[0], n[1] - xy[1]) > 0.5;
    }).map(([id, xy]) => `${id} 基线${JSON.stringify(xy)} 现${JSON.stringify(终[id] || '未渲染')}`);
    记('⭐⭐ 静置 15s 后复核：' + (残.length ? JSON.stringify(残) : '[]（全部一致）'));
  }
  await 浏览器.browser.close();
}

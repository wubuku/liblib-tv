// Batch EV-3：⭐⭐⭐ 用**像素分析**独立测出网格间距 —— 一条完全不依赖属性名的路。
//
// 为什么还要再测一遍：EV-2 从 `<pattern>` 读出 `width = 16.0517`，
//   而 `16.0517 / 0.458621 = 35.0` 正好是整数 —— 看着很像「网格步长 35（画布单位）」。
//   ⛔ 但这**有两种读法**，光看属性分不出：
//     ① pattern 的 user space 就是屏幕像素 ⇒ 屏上间距 16.05px ⇒ 画布步长 **35**
//     ② pattern 已经被 React Flow 按 zoom 预乘过 ⇒ 屏上间距 16.05px ⇒ 画布步长 **16.05**
//   ⛔ 同一组数字，两种相反的结论。**必须找一条不依赖属性名的路来裁。**
//
// 本轮做法：⭐ **把画布平移到一片空白区，拍下来做周期测量。**
//   空白区里只有点网格，量相邻两点的屏幕距离（px），
//   再除以 zoom 换算成画布单位。**这条路一个字都不用属性名。**
//
// 平移安全性：
//   · 只用**中键**拖（裸左键拖只会选中/移动节点）。
//   · 平移是纯位移，**反向拖同样的距离就能精确复原**，结束时比对 transform 矩阵。
//   · ⛔ 全程不碰任何节点；收尾再 `⌘0` 并核对 11 个节点坐标。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEV3.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const 读变换 = (page) => page.evaluate(() => {
  const vp = document.querySelector('.react-flow__viewport');
  if (!vp) return null;
  const m = /matrix\(([^)]+)\)/.exec(getComputedStyle(vp).transform);
  if (!m) return null;
  const n = m[1].split(',').map(Number);
  return { zoom: n[0], panX: n[4], panY: n[5], 全: getComputedStyle(vp).transform };
});

const browser = await launch();
const page = browser.page;
try {
  await open(page, CANVAS_URL);
  await closePromos(page);
  await page.waitForTimeout(4000);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2500);

  const 起始变换 = await 读变换(page);
  记('起始变换：' + JSON.stringify(起始变换));
  记('开局坐标偏差：' + JSON.stringify(await 核对坐标(page)));
  结果.读数.起始变换 = 起始变换;

  // ════════ ① 找一个当前视口里「没有节点」的点，作为中键拖拽的落点 ════════
  // ⭐ 三铁律：动手之前先 elementFromPoint 验落点归属。
  const 落点 = await page.evaluate(() => {
    const 候选 = [];
    for (let y = 60; y < 740; y += 20) {
      for (let x = 20; x < 1420; x += 20) {
        const e = document.elementFromPoint(x, y);
        if (!e) continue;
        const node = e.closest('.react-flow__node');
        if (node) continue;
        if (!e.classList.contains('react-flow__pane')) continue;
        候选.push([x, y]);
      }
    }
    return { 总数: 候选.length, 头几个: 候选.slice(0, 5) };
  });
  记('pane 空白点：' + JSON.stringify(落点));
  if (!落点.总数) throw new Error('视口里找不到空白 pane 点');
  const [px, py] = 落点.头几个[Math.floor(落点.头几个.length / 2)];

  // ════════ ② 中键平移到空白区 ════════
  // ⛔ 按画布坐标驱动：Δscreen = Δcanvas × zoom。
  //    ⚠️ 第一轮只平移 (+520,+380)，结果节点还在视口里（见 JSON 的「视口内节点」）。
  //    这里先**算清楚要平多少**：节点在画布里 x∈[-1787,636]、y∈[300,1524]，
  //    视口 1440×810 屏幕像素 = 3140×1766 画布单位。
  //    要让最左上的节点也移出屏幕，需要 panX > 1440 + 1787×0.4586 ≈ 2259，
  //    panY > 810 − 300×0.4586 ≈ 672。起始 pan 是 (884.6, −93.5) ⇒ 至少要再拖 (+855, +386)。
  //    取 (+1000, +560) 留足余量；**复原时反向拖同样距离**。
  const DX = 1000, DY = 560;
  await page.mouse.move(px, py);
  await page.mouse.down({ button: 'middle' });
  for (let i = 1; i <= 12; i++) {
    await page.mouse.move(px + Math.round((DX * i) / 12), py + Math.round((DY * i) / 12));
    await page.waitForTimeout(30);
  }
  await page.mouse.up({ button: 'middle' });
  await page.waitForTimeout(1200);

  const 平移后 = await 读变换(page);
  记('平移后变换：' + JSON.stringify(平移后));
  结果.读数.平移后变换 = 平移后;

  // ════════ ③ 确认现在视口里一个节点都没有（阴性前提）════════════
  const 视口内节点 = await page.evaluate(() => {
    const out = [];
    for (const n of document.querySelectorAll('.react-flow__node')) {
      const r = n.getBoundingClientRect();
      if (r.right < 0 || r.left > innerWidth || r.bottom < 0 || r.top > innerHeight) continue;
      out.push({ id: n.getAttribute('data-id'), box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] });
    }
    return out;
  });
  记('平移后视口内节点：' + JSON.stringify(视口内节点));
  结果.读数.视口内节点 = 视口内节点;

  // ════════ ④ 拍空白区，做像素周期测量 ════════
  await page.screenshot({ path: EVID + 'ev3-空白区网格.png', clip: { x: 200, y: 120, width: 700, height: 460 } });
  记('已拍 ev3-空白区网格.png（700×460 CSS px = 1400×920 像素）');

  // 同时把 pattern 属性再读一次，确认平移不改步长、只改偏移
  const 平移后pattern = await page.evaluate(() => {
    const p = document.querySelector('.react-flow__background pattern');
    if (!p) return null;
    const o = {};
    for (const a of p.attributes) o[a.name] = a.value;
    return o;
  });
  记('平移后 pattern：' + JSON.stringify(平移后pattern));
  结果.读数.平移后pattern = 平移后pattern;

  // ════════ ⑤ 复原：反向中键拖同样的距离 ════════
  await page.mouse.move(px + DX, py + DY);
  await page.mouse.down({ button: 'middle' });
  for (let i = 1; i <= 12; i++) {
    await page.mouse.move(px + DX - Math.round((DX * i) / 12), py + DY - Math.round((DY * i) / 12));
    await page.waitForTimeout(30);
  }
  await page.mouse.up({ button: 'middle' });
  await page.waitForTimeout(1500);
  const 复原变换 = await 读变换(page);
  记('复原后变换：' + JSON.stringify(复原变换));
  const 差 = 复原变换 && 起始变换
    ? { dx: +(复原变换.panX - 起始变换.panX).toFixed(2), dy: +(复原变换.panY - 起始变换.panY).toFixed(2), dz: +(复原变换.zoom - 起始变换.zoom).toFixed(6) }
    : null;
  记('复原偏差（应为 0）：' + JSON.stringify(差));
  结果.读数.复原偏差 = 差;

  // ════════ ⑥ 收尾：静置后核对节点 ════════
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(15000);
  const 偏差 = await 核对坐标(page);
  记('⭐⭐ 静置 15s 后坐标复核：' + JSON.stringify(偏差));
  结果.收尾 = { 偏差, 已渲染: Object.keys(await 读全部坐标(page)).length };
} catch (e) {
  记('❌ ' + e.message);
  结果.错误 = String((e && e.stack) || e);
} finally {
  落盘(结果);
  await browser.browser.close();
  console.log('\n=== 已写 tools/batchEV3.json ===');
}

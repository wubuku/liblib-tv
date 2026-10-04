// Batch EV-8：给「网格吸附」结案补取证图（只拍，不动节点）。
//
// 要拍的：
//   ① 底栏「网格吸附」**关态**特写（普通网格图标，svg 1 枚）
//   ② 底栏「网格吸附」**开态**特写（叠了斜杠，svg 2 枚）
//   ③ 空白区点网格原样 —— 证明「网格确实画在屏上」，不是没有网格
//   ④ 同一块点网格放大 —— 让人肉眼能数出 16px 的间隔
//
// ⛔ 全程不动任何节点。③ 需要中键平移到空白区，**拍完原路平移回来**，
//    并在收尾核对 transform 矩阵。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEV8.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const 读变换 = () => page.evaluate(() => {
  const m = /matrix\(([^)]+)\)/.exec(getComputedStyle(document.querySelector('.react-flow__viewport')).transform);
  const n = m[1].split(',').map(Number);
  return { zoom: n[0], panX: n[4], panY: n[5] };
});

const 底栏 = () => page.evaluate(() => {
  const out = [];
  for (const e of document.querySelectorAll('button')) {
    const r = e.getBoundingClientRect();
    if (r.top < 740 || r.bottom > 810 || r.left > 340) continue;
    if (e.querySelector('button')) continue;
    const svgs = [...e.querySelectorAll('svg')].map((s) => {
      const p = s.querySelector('path');
      return { 尺寸: [Math.round(s.getBoundingClientRect().width), Math.round(s.getBoundingClientRect().height)], cls: String(s.getAttribute('class') || '').slice(0, 60), d: p ? String(p.getAttribute('d')).slice(0, 60) : null };
    });
    out.push({ aria: e.getAttribute('aria-label'), box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)], svg数: svgs.length, svgs });
  }
  out.sort((a, b) => a.box[0] - b.box[0]);
  return out;
});

const 定位 = async () => {
  const 栏 = await 底栏();
  const 枚 = 栏[4];
  return { 栏, 枚, 认: !!枚 && 枚.aria === '网格吸附', 开: !!枚 && 枚.aria === '网格吸附' && 枚.svg数 === 2 };
};

const 切 = async (想要) => {
  const 前 = await 定位();
  if (!前.认) throw new Error('定位不到网格吸附');
  if (前.开 === 想要) return 前;
  const [x, y] = 前.枚.中心;
  const 验 = await page.evaluate(([px, py]) => document.elementFromPoint(px, py)?.closest('button')?.getAttribute('aria-label'), [x, y]);
  await page.mouse.move(x, y); await page.mouse.down(); await page.mouse.up();
  await page.waitForTimeout(1000);
  await page.mouse.move(700, 300); await page.waitForTimeout(400);
  const 后 = await 定位();
  return { ...后, 点击自证: 验 };
};

const browser = await launch();
const page = browser.page;
try {
  await open(page, CANVAS_URL);
  await closePromos(page);
  await page.waitForTimeout(4000);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2500);
  记('开局坐标偏差：' + JSON.stringify(await 核对坐标(page)));

  // ① 关态
  await 切(false);
  const 关 = await 定位();
  记('关态：' + JSON.stringify({ 认: 关.认, 开: 关.开, svg: 关.枚.svg数, 路径: 关.枚.svgs.map((s) => s.d) }));
  await page.screenshot({ path: EVID + 'ev8-底栏关态.png', clip: { x: 0, y: 756, width: 290, height: 46 } });
  记('已拍 ev8-底栏关态.png');

  // ② 开态
  const 开 = await 切(true);
  记('开态：' + JSON.stringify({ 开: 开.开, svg: 开.枚.svg数, 路径: 开.枚.svgs.map((s) => s.d) }));
  await page.screenshot({ path: EVID + 'ev8-底栏开态.png', clip: { x: 0, y: 756, width: 290, height: 46 } });
  记('已拍 ev8-底栏开态.png');
  结果.读数.关态 = 关.枚;
  结果.读数.开态 = 开.枚;

  // ③④ 平移到空白区拍点网格
  const 变0 = await 读变换();
  const 落 = await page.evaluate(() => {
    const c = [];
    for (let y = 60; y < 740; y += 20) for (let x = 20; x < 1420; x += 20) {
      const e = document.elementFromPoint(x, y);
      if (e && e.classList.contains('react-flow__pane')) c.push([x, y]);
    }
    return c;
  });
  const [px, py] = 落[Math.floor(落.length / 2)];
  const DX = 1000, DY = 560;
  await page.mouse.move(px, py);
  await page.mouse.down({ button: 'middle' });
  for (let i = 1; i <= 12; i++) { await page.mouse.move(px + Math.round((DX * i) / 12), py + Math.round((DY * i) / 12)); await page.waitForTimeout(30); }
  await page.mouse.up({ button: 'middle' });
  await page.waitForTimeout(1500);
  记('平移后：' + JSON.stringify(await 读变换()));
  await page.screenshot({ path: EVID + 'ev8-点网格原样.png', clip: { x: 260, y: 150, width: 480, height: 300 } });
  记('已拍 ev8-点网格原样.png（480×300 CSS px）');
  // ⭐ 拍的时候把指针挪开，别把悬停高亮拍进来
  await page.mouse.move(10, 400);
  await page.waitForTimeout(300);
  await page.screenshot({ path: EVID + 'ev8-点网格原样.png', clip: { x: 260, y: 150, width: 480, height: 300 } });

  // 原路平移回来
  await page.mouse.move(px + DX, py + DY);
  await page.mouse.down({ button: 'middle' });
  for (let i = 1; i <= 12; i++) { await page.mouse.move(px + DX - Math.round((DX * i) / 12), py + DY - Math.round((DY * i) / 12)); await page.waitForTimeout(30); }
  await page.mouse.up({ button: 'middle' });
  await page.waitForTimeout(1500);
  const 变1 = await 读变换();
  const 差 = { dx: +(变1.panX - 变0.panX).toFixed(1), dy: +(变1.panY - 变0.panY).toFixed(1) };
  记('平移复原偏差：' + JSON.stringify(差));
  结果.读数.平移复原偏差 = 差;

  // 复原吸附状态
  const 回 = await 切(false);
  记('吸附复原：开=' + 回.开);

  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(15000);
  const 偏差 = await 核对坐标(page);
  记('⭐⭐ 静置 15s 后坐标复核：' + JSON.stringify(偏差));
  结果.收尾 = { 偏差, 吸附最后: (await 定位()).开, 已渲染: Object.keys(await 读全部坐标(page)).length };
} catch (e) {
  记('❌ ' + e.message);
  结果.错误 = String((e && e.stack) || e);
} finally {
  落盘(结果);
  await browser.browser.close();
  console.log('\n=== 已写 tools/batchEV8.json ===');
}

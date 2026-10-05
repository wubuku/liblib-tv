// ⭐⭐⭐⭐⭐ 复原 v7：**段长随剩余量自适应**（v6 栽在段长写死 1200 上）
//
// v6 的收敛曲线（每一轮都是「整组 11 个、位移完全一致」，只差方向和段长）：
//   −12440.2 → −9954.1 → −7467.9 → −4981.8 → −2495.7 → **−9.6** → **+2476.5**（过冲）
// ⇒ 每段 1200 屏 px = 2486 画布单位，而收尾需要的是亚单位精度。
//    ⇒ 段长必须 `min(上限, 剩余量)`，越接近越要小步。
//
// ⭐ 同时把 v6 的另一个收获固化下来：落点用**朝向那一侧最外侧的节点框中心**
//    （往右拖用最左列、往左拖用最右列），这样移动方向上不会立刻压到别的节点。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const 日志 = [];
const 记 = (s) => { 日志.push(s); writeFileSync(HERE + 'restore-v7.json', JSON.stringify({ 日志 }, null, 2)); console.log('· ' + s); };
const IDS = Object.keys(坐标);
const 上限px = 1200;

const 浏览器 = await launch();
const page = 浏览器.page;
const 逐个读 = () => page.evaluate((ids) => {
  const o = {};
  for (const id of ids) {
    const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    if (!n) { o[id] = null; continue; }
    const t = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
    const r = n.getBoundingClientRect();
    o[id] = { 画布: t ? [Number(t[1]), Number(t[2])] : null, 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)], 框: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] };
  }
  return o;
}, IDS);
const 读zoom = () => page.evaluate(() => {
  const v = document.querySelector('.react-flow__viewport');
  const m = /matrix\(([^)]+)\)/.exec(getComputedStyle(v).transform || '');
  return m ? Number(m[1].split(',')[0]) : 1;
});
const 框选全部 = async () => {
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(3200);
  await page.mouse.move(12, 64); await page.waitForTimeout(300);
  await page.mouse.down(); await page.waitForTimeout(140);
  for (let i = 1; i <= 10; i++) { await page.mouse.move(Math.round(12 + (1418 * i) / 10), Math.round(64 + (671 * i) / 10)); await page.waitForTimeout(130); }
  await page.mouse.up(); await page.waitForTimeout(800);
  return page.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
};

try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(12000);
  await closePromos(page);
  const 关 = await page.evaluate(() => {
    const el = [...document.querySelectorAll('div.fixed')].find((d) => /Agent 已升级为 TV Director/.test(d.innerText || ''));
    const btn = el && [...el.querySelectorAll('button')].find((b) => /知道了/.test(b.innerText || ''));
    if (!btn) return null;
    const r = btn.getBoundingClientRect();
    return [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)];
  });
  if (关) { await page.mouse.move(关[0], 关[1]); await page.waitForTimeout(300); await page.mouse.down(); await page.mouse.up(); await page.waitForTimeout(1000); }
  await page.mouse.move(720, 300); await page.waitForTimeout(500);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(3500);
  const Z = await 读zoom();
  记(`zoom = ${Z}｜1 屏px = ${(1 / Z).toFixed(4)} 画布单位｜段长上限 ${上限px} 屏 px`);

  for (let 轮 = 1; 轮 <= 16; 轮++) {
    const 全 = await 逐个读();
    const 偏 = IDS.map((id) => ({ id, d: 全[id] && 全[id].画布 ? 全[id].画布[0] - 坐标[id][0] : null, y: 全[id] && 全[id].画布 ? 全[id].画布[1] - 坐标[id][1] : null }));
    const 有 = 偏.filter((o) => o.d !== null && Math.abs(o.d) > 0.5);
    const y偏 = 偏.filter((o) => o.y !== null && Math.abs(o.y) > 0.5);
    if (!有.length) { 记(`轮${轮}：x 偏差全部 < 0.5${y偏.length ? `，但 y 还有 ${y偏.length} 个偏离 ${JSON.stringify(y偏.map((o) => o.y.toFixed(2)))}` : ' ✅ 全部回到基线'}`); break; }
    const ds = 有.map((o) => o.d);
    const 宽 = Math.max(...ds) - Math.min(...ds);
    记(`轮${轮}：读到 ${偏.filter((o) => o.d !== null).length}/${IDS.length}｜x 偏差 ${ds[0].toFixed(2)}（宽度 ${宽.toFixed(3)}）｜y 偏离 ${y偏.length}`);
    if (宽 >= 1) { 记('⛔ 各节点 x 偏差不一致，停止'); break; }
    const 方向 = ds[0] > 0 ? -1 : 1;
    // ⭐ 段长 = min(上限, 剩余量)，且不小于 3
    const 剩屏px = Math.abs(ds[0]) / Z;
    const 量 = 方向 * Math.max(3, Math.min(上限px, Math.round(剩屏px)));

    const n = await 框选全部();
    if (!n) { 记('⛔ 框选失败'); break; }
    const 全2 = await 逐个读();
    const 列 = IDS.map((id) => ({ id, x: 全2[id].画布[0], c: 全2[id].中心 })).filter((o) => o.c);
    列.sort((a, b) => a.x - b.x);
    let 靶 = 方向 > 0 ? 列[0] : 列[列.length - 1];
    let 起 = 靶.c;
    // 落点必须在 [6,1434] 内
    if (起[0] + 量 < 6 || 起[0] + 量 > 1434) {
      const alt = 列.filter((o) => o.c[0] + 量 >= 6 && o.c[0] + 量 <= 1434);
      if (!alt.length) { 记(`   ⛔ 没有落点能让终点落在视口内（需 ${量}px）`); break; }
      靶 = 方向 > 0 ? alt[0] : alt[alt.length - 1];
      起 = 靶.c;
    }
    const 落 = [起[0] + 量, 起[1]];
    const 撞 = IDS.filter((id) => { const b = 全2[id].框; return b && 落[0] > b[0] && 落[0] < b[0] + b[2] && 落[1] > b[1] && 落[1] < b[1] + b[3]; });
    if (撞.length) { 记(`   ⛔ 落点压在 ${JSON.stringify(撞)} 上，放弃`); break; }
    记(`   ${方向 > 0 ? '右' : '左'}拖 ${量}px：${靶.id} 中心 ${JSON.stringify(起)} → ${JSON.stringify(落)}`);
    await page.mouse.move(起[0], 起[1]); await page.waitForTimeout(320);
    await page.mouse.down(); await page.waitForTimeout(160);
    for (let i = 1; i <= 10; i++) { await page.mouse.move(Math.round(起[0] + (量 * i) / 10), 起[1]); await page.waitForTimeout(150); }
    await page.mouse.up(); await page.waitForTimeout(800);
    await page.mouse.move(720, 300); await page.waitForTimeout(300);
    const 后 = await 逐个读();
    记(`   → 偏差 ${(后[IDS[0]].画布[0] - 坐标[IDS[0]][0]).toFixed(2)}`);
  }
} catch (e) {
  记('❌ ' + e.message);
} finally {
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(15000);
  const 全 = await page.evaluate((ids) => {
    const o = {};
    for (const id of ids) {
      const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
      if (!n) { o[id] = '未渲染'; continue; }
      const t = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
      o[id] = t ? [Number(t[1]), Number(t[2])] : n.style.transform;
    }
    return o;
  }, IDS);
  const 残 = Object.entries(坐标).filter(([id, xy]) => {
    const n = 全[id]; return !Array.isArray(n) || Math.hypot(n[0] - xy[0], n[1] - xy[1]) > 0.5;
  }).map(([id, xy]) => `${id} 基线${JSON.stringify(xy)} 现${JSON.stringify(全[id])}`);
  记('⭐⭐ 静置 15s 后坐标复核：' + (残.length ? JSON.stringify(残) : '[]（全部一致）'));
  await 浏览器.browser.close();
}

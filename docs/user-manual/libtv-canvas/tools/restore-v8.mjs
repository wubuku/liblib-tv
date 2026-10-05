// ⭐⭐⭐⭐⭐ 复原 v8：段长由「起点到视口边界的**实际**安全距离」决定
//
// v7 停住的原因：`⌘0`（fit view）之后 **zoom 变了**（包围盒 2364×1044 fit 进 1440 宽 ⇒ ~0.609，
//   不是常驻时的 0.4827），节点群**不再占满视口**，最右列中心也不到 1206，
//   于是「往左拖 1200px」的终点必然出界。
//   ⭐⭐⭐ 教训：**`⌘0` 之后 zoom 不是常驻值**，凡是用 `zoom` 换算像素的脚本，
//   每轮都必须**重新读一次**，不能沿用进场时的常量。
//
// 本版：每轮重新读 zoom；段长 = min(剩余量, 起点到该方向视口边界的距离 − 30px)。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const 日志 = [];
const 记 = (s) => { 日志.push(s); writeFileSync(HERE + 'restore-v8.json', JSON.stringify({ 日志 }, null, 2)); console.log('· ' + s); };
const IDS = Object.keys(坐标);
const L = 30, R = 1410;   // 视口内安全边界

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

  for (let 轮 = 1; 轮 <= 18; 轮++) {
    await page.keyboard.press('Meta+0');
    await page.waitForTimeout(3200);
    const Z = await 读zoom();
    const 全 = await 逐个读();
    const 偏 = IDS.map((id) => ({ id, d: 全[id] && 全[id].画布 ? 全[id].画布[0] - 坐标[id][0] : null, y: 全[id] && 全[id].画布 ? 全[id].画布[1] - 坐标[id][1] : null }));
    const 有 = 偏.filter((o) => o.d !== null && Math.abs(o.d) > 0.5);
    const y偏 = 偏.filter((o) => o.y !== null && Math.abs(o.y) > 0.5);
    if (!有.length) { 记(`轮${轮}：x 偏差全部 < 0.5${y偏.length ? `，y 还有 ${y偏.length} 个偏离` : '　✅ 全部回到基线'}`); break; }
    const ds = 有.map((o) => o.d);
    const 宽 = Math.max(...ds) - Math.min(...ds);
    记(`轮${轮}：zoom ${Z}｜读到 ${偏.filter((o) => o.d !== null).length}/${IDS.length}｜x 偏差 ${ds[0].toFixed(2)}（宽度 ${宽.toFixed(3)}）｜y 偏离 ${y偏.length}`);
    if (宽 >= 1) { 记('⛔ 各节点 x 偏差不一致，停止'); break; }
    const 方向 = ds[0] > 0 ? -1 : 1;

    const n = await 框选全部();
    if (!n) { 记('⛔ 框选失败'); break; }
    const 全2 = await 逐个读();
    const 列 = IDS.map((id) => ({ id, x: 全2[id].画布[0], c: 全2[id].中心 })).filter((o) => o.c);
    列.sort((a, b) => a.x - b.x);
    // ⭐ 往右拖 ⇒ 用最左列；往左拖 ⇒ 用最右列
    const 候选 = 方向 > 0 ? [...列].reverse() : 列;   // 优先挑离边界远的
    let 选 = null, 量 = 0;
    for (const o of 候选) {
      const 安全 = 方向 > 0 ? (R - o.c[0]) : (o.c[0] - L);
      if (安全 < 25) continue;
      const 需 = Math.abs(ds[0]) / (await 读zoom());
      const m = Math.max(3, Math.min(安全 - 10, Math.round(需)));
      if (!选 || m > 量) { 选 = o; 量 = m; }
    }
    if (!选) { 记('⛔ 找不到安全落点'); break; }
    const 起 = 选.c, 落 = [起[0] + 方向 * 量, 起[1]];
    const 撞 = IDS.filter((id) => { const b = 全2[id].框; return b && 落[0] > b[0] && 落[0] < b[0] + b[2] && 落[1] > b[1] && 落[1] < b[1] + b[3]; });
    if (撞.length) { 记(`   ⛔ 落点压在 ${JSON.stringify(撞)} 上`); break; }
    记(`   ${方向 > 0 ? '右' : '左'}拖 ${量}px：${选.id} 中心 ${JSON.stringify(起)} → ${JSON.stringify(落)}（安全距离 ${方向 > 0 ? R - 起[0] : 起[0] - L}）`);
    await page.mouse.move(起[0], 起[1]); await page.waitForTimeout(320);
    await page.mouse.down(); await page.waitForTimeout(160);
    for (let i = 1; i <= 10; i++) { await page.mouse.move(Math.round(起[0] + (方向 * 量 * i) / 10), 起[1]); await page.waitForTimeout(150); }
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

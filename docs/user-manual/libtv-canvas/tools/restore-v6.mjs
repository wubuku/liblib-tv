// ⭐⭐⭐⭐⭐ 复原 v6：**只认 FD-4 验证过的那一种落点**（节点框中心），大段位移，逐段读回
//
// v5 踩的两个坑，这一版都堵上：
//   ① ⛔ 「分段」算错了：`Math.ceil(|需px|/400) * sign` 得到的是**总像素**（12），
//      不是每段像素。每段只挪 12 屏 px，却被拖了 939 屏 px。
//      ⇒ 这一版**每段固定 1200 屏 px**，方向由「基线 − 当前」现算，不预判总需求。
//   ② ⛔ 落点 (30,250) **不在选区矩形内**（虚线框是 `[35,278,760,466]`），
//      那里是 pane ⇒ 拖的是**画布平移**。请求 −12 屏 px、节点却走了 1942.8 画布单位。
//      ⇒ 这一版**只用节点框中心当落点** —— FD-4 用它成功拿到 11 个节点位移完全一致。
//
// ⭐ 前置事实（FD-4 实测）：框选全部后拖动 = **11 个节点整组移动**，位移完全相同。
//    所以只要「各位移一致」这一条守住，整组拖动就是安全的。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const 日志 = [];
const 记 = (s) => { 日志.push(s); writeFileSync(HERE + 'restore-v6.json', JSON.stringify({ 日志 }, null, 2)); console.log('· ' + s); };
const IDS = Object.keys(坐标);
const 段px = 1200;

const 浏览器 = await launch();
const page = 浏览器.page;
/** ⭐ 逐个用 data-id 读 —— querySelectorAll 在框选状态下会漏读（FD-4 的教训） */
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
  记(`zoom = ${Z}｜1 屏px = ${(1 / Z).toFixed(4)} 画布单位｜每段 ${段px} 屏 px = ${(段px / Z).toFixed(1)} 画布单位`);

  for (let 轮 = 1; 轮 <= 14; 轮++) {
    const 全 = await 逐个读();
    const 偏 = IDS.map((id) => ({ id, d: 全[id] && 全[id].画布 ? 全[id].画布[0] - 坐标[id][0] : null, y: 全[id] && 全[id].画布 ? 全[id].画布[1] - 坐标[id][1] : null }));
    const 有 = 偏.filter((o) => o.d !== null && Math.abs(o.d) > 0.5);
    const y偏 = 偏.filter((o) => o.y !== null && Math.abs(o.y) > 0.5);
    记(`轮${轮}：读到 ${偏.filter((o) => o.d !== null).length}/${IDS.length}｜x 偏离 ${有.length} 个｜y 偏离 ${y偏.length} 个`);
    if (!有.length) { 记(y偏.length ? `⚠️ x 已归零，y 还有 ${y偏.length} 个偏离` : '✅ 全部回到基线'); break; }
    const ds = 有.map((o) => o.d);
    const 宽 = Math.max(...ds) - Math.min(...ds);
    记(`   x 偏差 ${Math.min(...ds).toFixed(2)} ~ ${Math.max(...ds).toFixed(2)}（宽度 ${宽.toFixed(3)}）`);
    if (宽 >= 1) { 记('⛔ 各节点偏差不一致，停止'); break; }
    const 方向 = ds[0] > 0 ? -1 : 1;      // 需要往回拖的方向
    const 量 = 方向 * 段px;

    const n = await 框选全部();
    if (!n) { 记('⛔ 框选失败'); break; }
    // ⭐ 落点用**最左/最右列的节点框中心**（随方向选），保证移动方向上不会立刻撞上别的节点
    const 全2 = await 逐个读();
    const 列 = IDS.map((id) => ({ id, x: 全2[id].画布[0], c: 全2[id].中心 })).filter((o) => o.c);
    列.sort((a, b) => a.x - b.x);
    const 靶 = 方向 > 0 ? 列[0] : 列[列.length - 1];
    记(`   框选 ${n} 个｜方向 ${方向 > 0 ? '右' : '左'}｜落点用 ${靶.id} 中心 ${JSON.stringify(靶.c)}`);
    const 起 = 靶.c;
    const 落 = [起[0] + 量, 起[1]];
    if (落[0] < 6 || 落[0] > 1434) { 记(`   ⛔ 落点 ${JSON.stringify(落)} 出视界，缩小段`); break; }
    const 撞 = IDS.filter((id) => { const b = 全2[id].框; return b && 落[0] > b[0] && 落[0] < b[0] + b[2] && 落[1] > b[1] && 落[1] < b[1] + b[3]; });
    if (撞.length) { 记(`   ⛔ 落点压在 ${JSON.stringify(撞)} 上，放弃本段`); break; }
    记(`   拖 ${量} 屏 px：${JSON.stringify(起)} → ${JSON.stringify(落)}`);
    await page.mouse.move(起[0], 起[1]); await page.waitForTimeout(320);
    await page.mouse.down(); await page.waitForTimeout(160);
    for (let i = 1; i <= 10; i++) { await page.mouse.move(Math.round(起[0] + (量 * i) / 10), 起[1]); await page.waitForTimeout(150); }
    await page.mouse.up(); await page.waitForTimeout(800);
    await page.mouse.move(720, 300); await page.waitForTimeout(300);
    const 后 = await 逐个读();
    记(`   → ${JSON.stringify(后[IDS[0]].画布)}｜基线 ${JSON.stringify(坐标[IDS[0]])}｜偏差 ${(后[IDS[0]].画布[0] - 坐标[IDS[0]][0]).toFixed(2)}`);
  }
  const 终 = await 逐个读();
  for (const id of IDS) 记(`  ${id} = ${JSON.stringify(终[id] && 终[id].画布)}｜基线 ${JSON.stringify(坐标[id])}`);
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

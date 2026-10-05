// ⭐⭐⭐ Batch FB-8：**逐帧小步长**复原导演台
//
// FB-7 的逐帧轨迹把两件事同时定案了：
//   ① 落点是**12 画布单位**的整数倍跳变（−1224 → −1212 → −1200，每次 +12，中间帧不动）
//   ② **只有逐帧小步长拖拽才生效**。FB-6 用单次 `mouse.move(x±N, y, {steps:8})`
//      从 ±1px 到 ±30px 全是 0 —— 因为 8 步之间**间隔 0ms**，React 批量更新把位移吞了。
//      FB-7 每帧之间等 170ms，位移立刻正确。
//
// 复原算术：现 x = −1200，要到 −1224（12 的倍数）需要 −24 画布单位 = −11 屏 px。
//   取 −13 屏 px = −28.35 画布单位，自由位置 −1228.35，
//   最近 12 倍数是 −1224（差 4.35）而不是 −1236（差 7.65）⇒ **正好落回 −1224**。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const ID = 'n-56F19pXVB4';
const 目标x = -1224;          // 12 的倍数格点
const HERE = new URL('.', import.meta.url).pathname;
const R = { 步骤: [], 读数: {} };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFB8.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };

const 浏览器 = await launch();
const page = 浏览器.page;
const 读 = (id) => page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return null;
  const t = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
  const r = n.getBoundingClientRect();
  return { 画布: t ? [Number(t[1]), Number(t[2])] : null, 框: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)] };
}, id);

/** ⭐⭐ 逐帧拖拽：每帧 2 屏 px，帧间 170ms（关键：不能一次大步长） */
const 逐帧拖 = async (id, dx, dy, 落点偏置) => {
  const s = await 读(id);
  if (!s || !s.中心) return { 错: '读不到节点' };
  const x0 = s.中心[0] + (落点偏置 ? 落点偏置[0] : 0);
  const y0 = s.中心[1] + (落点偏置 ? 落点偏置[1] : 0);
  await page.mouse.move(x0, y0); await page.waitForTimeout(300);
  const v = await page.evaluate((p) => {
    const e = document.elementFromPoint(p[0], p[1]);
    const n = e ? e.closest('.react-flow__node') : null;
    return n ? n.getAttribute('data-id') : null;
  }, [x0, y0]);
  if (v !== id) return { 错: `落点 ${v}` };
  const 轨迹 = [{ 帧: '按下', 画布: s.画布 }];
  await page.mouse.down(); await page.waitForTimeout(160);
  const 帧数 = Math.max(2, Math.round(Math.abs(dx) / 2));
  for (let i = 1; i <= 帧数; i++) {
    await page.mouse.move(Math.round(x0 + (dx * i) / 帧数), Math.round(y0 + (dy * i) / 帧数));
    await page.waitForTimeout(170);
    const q = await 读(id);
    轨迹.push({ 帧: i, 画布: q.画布 });
  }
  await page.mouse.up(); await page.waitForTimeout(600);
  await page.mouse.move(720, 170); await page.waitForTimeout(240);
  return { 轨迹, 后: (await 读(id)).画布 };
};

try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(9000);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(3000);
  const 起 = (await 读(ID)).画布;
  记(`导演台 基线 ${JSON.stringify(坐标[ID])}｜现 ${JSON.stringify(起)}｜框 ${JSON.stringify((await 读(ID)).框)}`);
  R.读数.起 = 起;

  // 目标：x → −1224（12 格点），y 尽量靠近 370.975
  for (let 轮 = 1; 轮 <= 6; 轮++) {
    const s = await 读(ID);
    const dx = 目标x - s.画布[0];
    if (Math.abs(dx) < 0.5) { 记(`✅ 第 ${轮} 轮：x 已到 ${JSON.stringify(s.画布[0])}`); break; }
    const 屏px = Math.round(dx * 0.458621);
    // 屏 px 取「略大于 |dx|/zoom 的 1.5 倍」以越过 12 格吸附的判定边界
    const 用 = 屏px === 0 ? (dx > 0 ? 13 : -13) : (Math.abs(屏px) < 13 ? (dx > 0 ? 13 : -13) : 屏px);
    记(`第 ${轮} 轮：x 现 ${s.画布[0]}，需 ${dx.toFixed(2)} 画布单位 → 逐帧拖 ${用} 屏 px`);
    const r = await 逐帧拖(ID, 用, 0, null);
    for (const t of (r.轨迹 || [])) 记(`   ${t.帧}｜${JSON.stringify(t.画布)}`);
    if (!r.成功 && !r.后) { 记('   ⛔ ' + JSON.stringify(r)); }
  }
  const 终 = await 读(ID);
  记(`终态 ${JSON.stringify(终.画布)}｜x 偏差 ${(终.画布[0] - 坐标[ID][0]).toFixed(4)}｜y 偏差 ${(终.画布[1] - 坐标[ID][1]).toFixed(4)}`);

  // 试 y：垂直逐帧拖，看 y 是否可控（会顺带看 x 会不会被带偏）
  const s2 = await 读(ID);
  if (Math.abs(s2.画布[1] - 坐标[ID][1]) > 0.5) {
    记('—— 试垂直拖 ——');
    const 前 = s2.画布;
    const r = await 逐帧拖(ID, 0, 2, null);
    for (const t of (r.轨迹 || [])) 记(`   ${t.帧}｜${JSON.stringify(t.画布)}`);
    const 后 = (await 读(ID)).画布;
    记(`   垂直 +2px：${JSON.stringify(前)} → ${JSON.stringify(后)}`);
  }
} catch (e) {
  R.错误 = String((e && e.stack) || e);
  记('❌ ' + e.message);
} finally {
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(15000);
  const 全 = await page.evaluate(() => {
    const o = {};
    for (const n of document.querySelectorAll('.react-flow__node')) {
      const t = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
      o[n.getAttribute('data-id')] = t ? [Number(t[1]), Number(t[2])] : null;
    }
    return o;
  });
  const 残 = Object.entries(坐标).filter(([id, xy]) => {
    const n = 全[id]; return !n || Math.hypot(n[0] - xy[0], n[1] - xy[1]) > 0.5;
  }).map(([id, xy]) => `${id} 基线${JSON.stringify(xy)} 现${JSON.stringify(全[id] || '未渲染')}`);
  记('⭐⭐ 静置 15s 后复核：' + (残.length ? JSON.stringify(残) : '[]（全部一致）'));
  R.收尾 = 残;
  await 浏览器.browser.close();
  console.log('\n=== 已写 tools/batchFB8.json ===');
}

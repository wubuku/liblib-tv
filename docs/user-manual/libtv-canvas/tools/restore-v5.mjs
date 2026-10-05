// ⭐⭐⭐⭐⭐ 复原 v5：**整组拖动**复原
//
// FD-4 证实：框选之后拖动 = 整组移动，位移 2278.9 画布单位、**11 个节点完全一致**。
// 但它的 finally 复原失败了，11 个节点现在都偏 +2278.9。
//   根因：`读全部坐标()` 用 `document.querySelectorAll('.react-flow__node')`，
//   那一刻只读到 **4 个**节点 ⇒ 4 个有偏差值、7 个被当成 99999
//   ⇒ 位移宽度算成 `97720` ⇒ 脚本判断「各节点位移不一致」而放弃。
//   ⭐ **`读全部坐标` 在框选状态下会漏读，必须逐个用 `data-id` 选择器读。**
//
// ⭐⭐⭐ 复原本身反而更简单：**框选全部 → 在选区里拖 → 整组回到原位**。
//    落点判据也简化了：框选之后有 `z-30` 的选区层铺在选区矩形上，
//    `elementFromPoint` 命中的是选区而不是节点 —— **根本不需要「无 nodrag 落点」那一套**。
//    只需保证：**落点在选区矩形内、且不在任何节点框上**（避开投放）。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const 日志 = [];
const 记 = (s) => { 日志.push(s); writeFileSync(HERE + 'restore-v5.json', JSON.stringify({ 日志 }, null, 2)); console.log('· ' + s); };

const 浏览器 = await launch();
const page = 浏览器.page;
let Z = 0.482682;
/** ⭐ 逐个用 data-id 读，不靠 querySelectorAll —— 框选状态下它会漏 */
const 逐个读 = () => page.evaluate((ids) => {
  const o = {};
  for (const id of ids) {
    const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    if (!n) { o[id] = null; continue; }
    const t = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
    const r = n.getBoundingClientRect();
    o[id] = { 画布: t ? [Number(t[1]), Number(t[2])] : null, 框: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] };
  }
  return o;
}, Object.keys(坐标));
const 读zoom = () => page.evaluate(() => {
  const v = document.querySelector('.react-flow__viewport');
  const m = /matrix\(([^)]+)\)/.exec(getComputedStyle(v).transform || '');
  return m ? Number(m[1].split(',')[0]) : 1;
});
/** 框选全部：起点取 (12,64)、终点 (1430,735) —— FD-2/FD-3/FD-4 三次都验证过 */
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
  Z = await 读zoom();

  const IDS = Object.keys(坐标);
  for (let 轮 = 1; 轮 <= 12; 轮++) {
    const 全 = await 逐个读();
    const 偏 = IDS.map((id) => ({ id, d: 全[id] && 全[id].画布 ? Number((全[id].画布[0] - 坐标[id][0]).toFixed(3)) : null }));
    const 有效 = 偏.filter((o) => o.d !== null);
    const 有偏 = 有效.filter((o) => Math.abs(o.d) > 0.5);
    记(`轮${轮}：读到 ${有效.length}/${IDS.length} 个节点，偏离基线 ${有偏.length} 个`);
    if (!有偏.length) { 记('✅ 已全部回到基线'); break; }
    const ds = 有偏.map((o) => o.d);
    const 宽 = Math.max(...ds) - Math.min(...ds);
    const y偏 = IDS.filter((id) => 全[id] && 全[id].画布 && Math.abs(全[id].画布[1] - 坐标[id][1]) > 0.5);
    记(`   x 位移 ${Math.min(...ds).toFixed(2)} ~ ${Math.max(...ds).toFixed(2)}（宽度 ${宽.toFixed(3)}）｜y 偏离 ${y偏.length} 个`);
    if (宽 >= 1) { 记('⛔ x 位移不一致，整组拖复原不了，停止'); break; }

    const 需px = Math.round(-ds[0] / Z);
    记(`   需要整组拖 ${需px} 屏 px`);
    const n = await 框选全部();
    记(`   框选 .selected = ${n}`);
    if (!n) { 记('⛔ 框选失败'); break; }

    // 找一个「在选区矩形内、且不在任何节点框上」的落点
    const 全2 = await 逐个读();
    const 空白 = (x, y) => !IDS.some((id) => { const b = 全2[id] && 全2[id].框; return b && x > b[0] && x < b[0] + b[2] && y > b[1] && y < b[1] + b[3]; });
    const 段 = Math.max(1, Math.ceil(Math.abs(需px) / 400)) * Math.sign(需px || 1);
    let p = null;
    for (const [x, y] of [[30, 250], [40, 700], [30, 700], [40, 250], [700, 20], [20, 400]]) if (空白(x, y)) { p = [x, y]; break; }
    if (!p) { 记('⛔ 找不到空白落点'); break; }
    const 终点 = [p[0] + 段, p[1]];
    if (终点[0] < 4 || 终点[0] > 1436) { 记(`⛔ 段位移 ${段} 超出视口，换基准点`); 需px = 0; }
    if (!需px) break;
    if (!空白(终点[0], 终点[1])) { 记('⛔ 终点落在节点上，放弃'); break; }
    记(`   落点 ${JSON.stringify(p)} → ${JSON.stringify(终点)}`);
    await page.mouse.move(p[0], p[1]); await page.waitForTimeout(320);
    await page.mouse.down(); await page.waitForTimeout(160);
    for (let i = 1; i <= 10; i++) { await page.mouse.move(Math.round(p[0] + (段 * i) / 10), p[1]); await page.waitForTimeout(150); }
    await page.mouse.up(); await page.waitForTimeout(800);
    await page.mouse.move(720, 300); await page.waitForTimeout(300);
    记(`   拖完 → ${JSON.stringify((await 逐个读())[IDS[0]].画布)}`);
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
  }, Object.keys(坐标));
  const 残 = Object.entries(坐标).filter(([id, xy]) => {
    const n = 全[id]; return !Array.isArray(n) || Math.hypot(n[0] - xy[0], n[1] - xy[1]) > 0.5;
  }).map(([id, xy]) => `${id} 基线${JSON.stringify(xy)} 现${JSON.stringify(全[id])}`);
  记('⭐⭐ 静置 15s 后坐标复核：' + (残.length ? JSON.stringify(残) : '[]（全部一致）'));
  await 浏览器.browser.close();
}

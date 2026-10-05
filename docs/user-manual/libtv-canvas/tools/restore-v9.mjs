// ⭐⭐⭐⭐⭐ 复原 v9：**单节点**分段闭环复原
//
// FD-5 的 finally 崩在一个老坑上：
//   `page.evaluate(fn, s.中心, o.id)` 传了**两个**参数
//   ⇒ Playwright 直接抛 `Too many arguments. … wrap them in an object.`
//   ⇒ 复原根本没执行，`v-v2hlWY4Br3` 留在偏了 +1516 画布单位的位置。
//   ⭐ 这正是本项目早就记过的判据缺陷（缺陷 381 那一类）：
//   **`page.evaluate` 的额外参数只能传一个**，要传多个就包成对象。
//
// 单节点复原的两个约束：
//   ① 拖动必须**从这个节点自己发起**（从别处发起的是画布平移）；
//      而它现在是最左列，屏幕中心 x 只有 ~190，一次拖不完 1516 画布单位。
//   ⇒ 段长 = `min(剩余量 ÷ zoom, 起点 x − 25)`，每轮 `⌘0` 重新定位。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const ID = process.argv[2] || 'v-v2hlWY4Br3';
const HERE = new URL('.', import.meta.url).pathname;
const 日志 = [];
const 记 = (s) => { 日志.push(s); writeFileSync(HERE + 'restore-v9.json', JSON.stringify({ ID, 日志 }, null, 2)); console.log('· ' + s); };

const 浏览器 = await launch();
const page = 浏览器.page;
const 读 = (id) => page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return null;
  const t = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
  const r = n.getBoundingClientRect();
  return { 画布: t ? [Number(t[1]), Number(t[2])] : null, 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)] };
}, id);
const 读zoom = () => page.evaluate(() => {
  const v = document.querySelector('.react-flow__viewport');
  const m = /matrix\(([^)]+)\)/.exec(getComputedStyle(v).transform || '');
  return m ? Number(m[1].split(',')[0]) : 1;
});
const 拖 = async (起, dx, dy) => {
  const ok = await page.evaluate(([p, nid]) => {
    const e = document.elementFromPoint(p[0], p[1]);
    const n = e ? e.closest('.react-flow__node') : null;
    return !!(n && !e.closest('.nodrag') && n.getAttribute('data-id') === nid);
  }, [起, ID]);
  if (!ok) return false;
  await page.mouse.move(起[0], 起[1]); await page.waitForTimeout(300);
  await page.mouse.down(); await page.waitForTimeout(150);
  const f = 10;
  for (let i = 1; i <= f; i++) { await page.mouse.move(Math.round(起[0] + (dx * i) / f), Math.round(起[1] + (dy * i) / f)); await page.waitForTimeout(150); }
  await page.mouse.up(); await page.waitForTimeout(700);
  await page.mouse.move(720, 200); await page.waitForTimeout(300);
  return true;
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
  await page.mouse.move(720, 200); await page.waitForTimeout(400);

  for (let 轮 = 1; 轮 <= 16; 轮++) {
    await page.keyboard.press('Meta+0');
    await page.waitForTimeout(3200);
    const Z = await 读zoom();
    const s = await 读(ID);
    if (!s || !s.画布) { 记('⛔ 读不到节点'); break; }
    const dx = 坐标[ID][0] - s.画布[0], dy = 坐标[ID][1] - s.画布[1];
    if (Math.hypot(dx, dy) < 0.5) { 记(`✅ 第 ${轮} 轮：已回到 ${JSON.stringify(s.画布)}`); break; }
    const 安全 = s.中心[0] - 25;          // 往左拖的安全距离
    const 需屏px = Math.round(Math.abs(dx) / Z);
    const px = -Math.max(3, Math.min(需屏px, 安全));
    记(`轮${轮}：zoom ${Z}｜现 ${JSON.stringify(s.画布)}｜需 ${dx.toFixed(1)},${dy.toFixed(1)}｜中心 ${JSON.stringify(s.中心)} 安全 ${安全}｜拖 ${px}px`);
    if (!(await 拖(s.中心, px, 0))) { 记('   ⛔ 中心落点不合格'); break; }
  }
  const 终 = await 读(ID);
  记(`终态 ${JSON.stringify(终.画布)}｜基线 ${JSON.stringify(坐标[ID])}`);
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

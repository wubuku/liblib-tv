// 通用定向复原：node tools/restore-any.mjs <id> [x y]
// 不给坐标就用 canvas-baseline.mjs 里的基线。
// ⭐⭐ 上一轮 FB-3 的教训：`const z = await zoom()` 写在 try 块里，
//    finally 里访问不到 ⇒ 抛 `z is not defined` ⇒ **复原根本没执行**，节点留下 2.19 画布单位的损伤。
//    ⇒ 所有量都必须在 try **之前**算好。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标, 读全部坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const ID = process.argv[2];
const 目标 = process.argv[4] ? [Number(process.argv[3]), Number(process.argv[4])] : 坐标[ID];
if (!ID || !目标) { console.error('用法：node restore-any.mjs <id> [x y]'); process.exit(1); }
const HERE = new URL('.', import.meta.url).pathname;
const 记 = (s) => { writeFileSync(HERE + 'restore-any.json', JSON.stringify({ 日志: (JSON.parse(process.env._L || '{}').日志 || []).concat(s) }, null, 2)); console.log('· ' + s); };

const 浏览器 = await launch();
const page = 浏览器.page;
let z = 1;

const 读 = () => page.evaluate((id) => {
  const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
  if (!n) return null;
  const t = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
  const r = n.getBoundingClientRect();
  return { 画布: t ? [Number(t[1]), Number(t[2])] : null, 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)] };
}, ID);

/** 拖整数像素；落点失败时把那个点上的东西**逐字记下来**，不只报 null */
const 拖 = async (dx, dy) => {
  const s = await 读();
  if (!s || !s.中心) return { 错: '读不到节点' };
  await page.mouse.move(s.中心[0], s.中心[1]);
  await page.waitForTimeout(320);
  const v = await page.evaluate((p) => {
    const e = document.elementFromPoint(p[0], p[1]);
    if (!e) return { null: true };
    const n = e.closest('.react-flow__node');
    return {
      标签: e.tagName, class: (e.getAttribute('class') || '').slice(0, 120),
      aria: e.getAttribute('aria-label'), 节点id: n ? n.getAttribute('data-id') : null,
      路径: (() => { let a = e, s = []; for (let i = 0; i < 5 && a; i++, a = a.parentElement) s.push(a.tagName + (a.getAttribute('class') ? '.' + a.getAttribute('class').split(' ').slice(0, 2).join('.') : '')); return s.join(' < '); })(),
    };
  }, s.中心);
  if (v.节点id !== ID) return { 错: '落点不属于本节点', 落点详情: v };
  await page.mouse.down(); await page.waitForTimeout(150);
  await page.mouse.move(s.中心[0] + dx, s.中心[1] + dy, { steps: 5 });
  await page.waitForTimeout(260);
  await page.mouse.up(); await page.waitForTimeout(560);
  await page.mouse.move(720, 180); await page.waitForTimeout(260);
  return { 成功: true };
};

try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(9000);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(3000);
  z = await page.evaluate(() => {
    const v = document.querySelector('.react-flow__viewport');
    const m = /matrix\(([^)]+)\)/.exec(getComputedStyle(v).transform || '');
    return m ? Number(m[1].split(',')[0]) : 1;
  });
  记(`${ID}｜目标 ${JSON.stringify(目标)}｜zoom ${z}｜起步 ${JSON.stringify((await 读()).画布)}`);
  for (let 轮 = 1; 轮 <= 30; 轮++) {
    const s = await 读();
    if (!s || !s.画布) { 记('⛔ 节点没渲染'); break; }
    const dx = 目标[0] - s.画布[0], dy = 目标[1] - s.画布[1];
    if (Math.hypot(dx, dy) < 0.5) { 记(`✅ 复原到位（轮 ${轮}）→ ${JSON.stringify(s.画布)}`); break; }
    const px_ = Math.max(-8, Math.min(8, Math.round(dx * z)));
    const py = Math.max(-8, Math.min(8, Math.round(dy * z)));
    记(`第 ${轮} 轮：现 ${JSON.stringify(s.画布)} 误差 ${Math.hypot(dx, dy).toFixed(4)} → 拖 ${px_},${py} px`);
    if (px_ === 0 && py === 0) { 记(`⛔ 整数像素已为 0（剩余 ${Math.hypot(dx, dy).toFixed(4)}）`); break; }
    const r = await 拖(px_, py);
    if (!r.成功) { 记('⛔ 拖拽失败：' + JSON.stringify(r)); break; }
  }
  const 终 = await 读();
  记(`终态 ${JSON.stringify(终.画布)}｜基线 ${JSON.stringify(目标)}`);
} catch (e) {
  记('❌ ' + e.message);
} finally {
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(15000);
  const 全 = await 读全部坐标(page);
  const 差 = Object.entries(坐标).filter(([id, xy]) => {
    const n = 全[id]; if (!n) return true;
    return Math.hypot(n[0] - xy[0], n[1] - xy[1]) > 0.5;
  }).map(([id, xy]) => `${id} 基线${JSON.stringify(xy)} 现${JSON.stringify(全[id] || '未渲染')}`);
  记('⭐⭐ 静置 15s 后复核：' + (差.length ? JSON.stringify(差) : '[]（全部一致）'));
  await 浏览器.browser.close();
}

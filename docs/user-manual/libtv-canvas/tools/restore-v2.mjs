// ⭐⭐⭐ 通用复原 v2：为「每步都重算落点」+「吸附会滞后一格」写的
//
// FB-10/FB-11 挖出两条拖拽硬规律，复原必须按它们设计：
//   ① **落点会滞后一格**：逐帧 +25 屏px，自由位置 186.51，就近的 12 倍数是 192（差 5.49），
//      但**实测落点是 180**（差 6.51，更远）。⇒ 不是「就近吸附」，是「停在上一格」。
//   ② **节点一动，落点就失效**：FB-11 的往返之所以净位移 48，
//      是因为反向拖还用了旧落点 (958, 57)，而节点已经右移 22 屏 px，那个点落到框外了。
//      ⇒ **每一轮都必须重新算落点**。
//
// 用法：node restore-v2.mjs <id> [x y]   不给坐标就用 canvas-baseline.mjs 的基线
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const ID = process.argv[2];
const 目标 = process.argv[4] ? [Number(process.argv[3]), Number(process.argv[4])] : 坐标[ID];
if (!ID || !目标) { console.error('用法：node restore-v2.mjs <id> [x y]'); process.exit(1); }
const HERE = new URL('.', import.meta.url).pathname;
const 日志 = [];
const 记 = (s) => { 日志.push(s); writeFileSync(HERE + 'restore-v2.json', JSON.stringify({ ID, 目标, 日志 }, null, 2)); console.log('· ' + s); };
const ZOOM = 0.458621;

const 浏览器 = await launch();
const page = 浏览器.page;
const 读 = (id) => page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return null;
  const t = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
  const r = n.getBoundingClientRect();
  return { 画布: t ? [Number(t[1]), Number(t[2])] : null, 框: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] };
}, id);
/** 框内找一个「属本节点 且 无 nodrag 祖先」的落点，优先靠左上（避开其它节点） */
const 找落点 = async (id) => {
  const s = await 读(id);
  if (!s || !s.框) return null;
  const [L, T, W, H] = s.框;
  for (const [fc, fr] of [[0.5, 0.5], [0.17, 0.17], [0.5, 0.17], [0.17, 0.5], [0.83, 0.17], [0.83, 0.5], [0.5, 0.83], [0.17, 0.83], [0.83, 0.83]]) {
    const x = L + Math.round(W * fc), y = T + Math.round(H * fr);
    if (x < 4 || x > 1436 || y < 4 || y > 806) continue;
    const ok = await page.evaluate((p) => {
      const e = document.elementFromPoint(p[0], p[1]);
      const n = e ? e.closest('.react-flow__node') : null;
      return !!(n && !e.closest('.nodrag') && n.getAttribute('data-id') === p[2]);
    }, [x, y, id]);
    if (ok) return { x, y };
  }
  return null;
};
const 逐帧拖 = async (id, x, y, dx, dy) => {
  await page.mouse.move(x, y); await page.waitForTimeout(300);
  await page.mouse.down(); await page.waitForTimeout(160);
  const 帧数 = Math.max(2, Math.round(Math.max(Math.abs(dx), Math.abs(dy)) / 2));
  for (let i = 1; i <= 帧数; i++) {
    await page.mouse.move(Math.round(x + (dx * i) / 帧数), Math.round(y + (dy * i) / 帧数));
    await page.waitForTimeout(170);
  }
  await page.mouse.up(); await page.waitForTimeout(600);
  await page.mouse.move(720, 170); await page.waitForTimeout(240);
};

try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(9000);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(3000);
  记(`${ID}｜目标 ${JSON.stringify(目标)}｜起步 ${JSON.stringify((await 读(ID)).画布)}`);
  for (let 轮 = 1; 轮 <= 18; 轮++) {
    const s = await 读(ID);
    if (!s || !s.画布) { 记('⛔ 节点没渲染'); break; }
    const dx = 目标[0] - s.画布[0], dy = 目标[1] - s.画布[1];
    if (Math.hypot(dx, dy) < 0.5) { 记(`✅ 复原到位（轮 ${轮}）→ ${JSON.stringify(s.画布)}`); break; }
    // ① 不足一格时多补一格，抵消「滞后一格」
    let 用x = Math.round(dx / ZOOM), 用y = Math.round(dy / ZOOM);
    if (Math.abs(用x) > 0 && Math.abs(用x) < 5) 用x = 用x > 0 ? 6 : -6;
    if (用x === 0 && 用y === 0) 用y = dy > 0 ? 6 : -6;
    const p = await 找落点(ID);
    if (!p) { 记('⛔ 找不到可用落点'); break; }
    记(`第 ${轮} 轮：现 ${JSON.stringify(s.画布)} 误差 ${Math.hypot(dx, dy).toFixed(4)}｜落点 ${JSON.stringify(p)}｜拖 ${用x},${用y}px`);
    await 逐帧拖(ID, p.x, p.y, 用x, 用y);
    记(`   → ${JSON.stringify((await 读(ID)).画布)}`);
  }
  记(`终态 ${JSON.stringify((await 读(ID)).画布)}｜基线 ${JSON.stringify(目标)}`);
} catch (e) {
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
  await 浏览器.browser.close();
}

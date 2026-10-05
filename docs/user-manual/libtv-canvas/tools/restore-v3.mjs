// ⭐⭐⭐ 复原 v3：把「吸附到 12 的倍数」当已知规律来做闭环控制
//
// 本轮把拖拽的三条硬规律都钉死了，复原必须按它们设计：
//   ① **落点量化到 12 画布单位**。导演台 −1200→−1212→−1224；智能剪辑 132→143→156→168→180。
//   ② **必须逐帧小步长**。单次 `mouse.move(x±N, y, {steps:8})`（8 步间隔 0ms）位移恒为 0，
//      ±1px 到 ±30px 全是 0 —— 事件被 React 批量更新吞掉。每帧 2px、帧间 170ms 才有效。
//   ③ **落点要朝「远离画布原点」的方向取整**：
//      132 + 13px → 自由 160.35 → 落 156（`floor(13.36)=13`×12）
//      132 + 25px → 自由 186.51 → 落 180（`floor(15.54)=15`×12）
//      −1200 − 13px → 自由 −1228.35 → 落 **−1224**（往负方向取整 = `−102`×12）
//      ⇒ 单次拖拽不能指望一步到位，**必须读回、算差、再拖**，这就是闭环。
//   ④ **每轮必须重找落点**：节点一动，原落点就落到框外了（FB-11 往返净位移 48 的原因）。
//
// 目标：智能剪辑 132 = 11×12（可达）；导演台 x 已到 −1224，y 尽力回到 370.975。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const 日志 = [];
const 记 = (s) => { 日志.push(s); writeFileSync(HERE + 'restore-v3.json', JSON.stringify({ 日志 }, null, 2)); console.log('· ' + s); };
const ZOOM = 0.458621;
const 任务 = [
  { id: 'v-oZNpH99MtM', 目标: [132, 300] },
  { id: 'n-56F19pXVB4', 目标: [-1224, 370.975] },
];

const 浏览器 = await launch();
const page = 浏览器.page;
const 读 = (id) => page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return null;
  const t = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
  const r = n.getBoundingClientRect();
  return { 画布: t ? [Number(t[1]), Number(t[2])] : null, 框: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] };
}, id);
const 找落点 = async (id) => {
  const s = await 读(id);
  if (!s || !s.框) return null;
  const [L, T, W, H] = s.框;
  const 点集 = [[0.5, 0.5], [0.2, 0.2], [0.5, 0.2], [0.2, 0.5], [0.8, 0.2], [0.8, 0.5], [0.5, 0.8], [0.2, 0.8], [0.8, 0.8]];
  for (const [fc, fr] of 点集) {
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
const 逐帧拖 = async (x, y, dx, dy) => {
  await page.mouse.move(x, y); await page.waitForTimeout(300);
  await page.mouse.down(); await page.waitForTimeout(160);
  const 帧数 = Math.max(2, Math.round(Math.max(Math.abs(dx), Math.abs(dy)) / 2));
  for (let i = 1; i <= 帧数; i++) {
    await page.mouse.move(Math.round(x + (dx * i) / 帧数), Math.round(y + (dy * i) / 帧数));
    await page.waitForTimeout(170);
  }
  await page.mouse.up(); await page.waitForTimeout(620);
  await page.mouse.move(720, 170); await page.waitForTimeout(240);
};

try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(9000);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(3000);

  for (const { id, 目标 } of 任务) {
    let s = await 读(id);
    if (!s) { await page.keyboard.press('Meta+0'); await page.waitForTimeout(2500); s = await 读(id); }
    if (!s) { 记(`⛔ ${id} 读不到（可能被拖出视口）`); continue; }
    记(`—— ${id} 目标 ${JSON.stringify(目标)}｜起步 ${JSON.stringify(s.画布)}｜原基线 ${JSON.stringify(坐标[id])} ——`);
    for (let 轮 = 1; 轮 <= 22; 轮++) {
      s = await 读(id);
      if (!s || !s.画布) { 记(`  ⛔ 第 ${轮} 轮读不到节点`); break; }
      const dx = 目标[0] - s.画布[0], dy = 目标[1] - s.画布[1];
      if (Math.hypot(dx, dy) < 0.5) { 记(`  ✅ 复原到位（轮 ${轮}）→ ${JSON.stringify(s.画布)}`); break; }
      // 阻尼：误差大时略微多走一点，抵消「朝远离原点取整」的偏置
      let px = Math.round((dx - Math.sign(dx) * Math.min(4, Math.abs(dx) / 6)) / ZOOM);
      let py = Math.round((dy - Math.sign(dy) * Math.min(4, Math.abs(dy) / 6)) / ZOOM);
      if (dx !== 0 && Math.abs(px) < 4) px = dx > 0 ? 5 : -5;
      if (dy !== 0 && Math.abs(py) < 4) py = dy > 0 ? 5 : -5;
      if (px === 0 && py === 0) py = 5;
      const p = await 找落点(id);
      if (!p) { 记(`  ⛔ 第 ${轮} 轮找不到落点`); break; }
      await 逐帧拖(p.x, p.y, px, py);
      const 后 = (await 读(id)).画布;
      记(`  轮${轮}：${JSON.stringify(s.画布)} → 拖 ${px},${py}px → ${JSON.stringify(后)}（差 ${(后[0] - 目标[0]).toFixed(2)}, ${(后[1] - 目标[1]).toFixed(2)}）`);
    }
    记(`  ${id} 终态 ${JSON.stringify((await 读(id)).画布)}｜目标 ${JSON.stringify(目标)}`);
  }
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

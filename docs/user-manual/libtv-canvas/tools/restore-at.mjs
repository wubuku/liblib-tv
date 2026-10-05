// ⭐⭐⭐ 定向复原 a-THmbuJXQj4：从 [-1360.36, 597.82] 回到 [-1356, 600]
//
// **为什么上一轮复原卡住**（FB-1 的复原循环连转 8 轮误差都不动）：
//   剩余误差 4.875 画布单位 ÷ zoom 0.458621 = **2.24 CSS px**。
//   `page.mouse.move` 的步进被取整到整数像素 ⇒ 每步 < 1px ⇒ **净位移为零**。
//   ⇒ ⭐⭐ **拖拽复原有一个精度下限：1 CSS px ÷ zoom = 2.18 画布单位。**
//
// 好消息：这两个数正好落在整数像素的格子上 ——
//   dx = -1356 − (−1360.36) = **+4.36 = 2 × 2.18**
//   dy =  600 −  597.82  = **+2.18 = 1 × 2.18**
//   ⇒ 用**整数像素**的拖拽（+2 px、−1 px）就能精确落回。
//
// 本脚本不按「算误差→算像素」的通式走，而是**整数像素逐次逼近 + 每次读回**，
// 到达误差 < 0.5 即停。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const ID = 'a-THmbuJXQj4';
const 目标 = 坐标[ID];
const HERE = new URL('.', import.meta.url).pathname;
const 日志 = [];
const 记 = (s) => { 日志.push(s); writeFileSync(HERE + 'restore-at.json', JSON.stringify({ 日志 }, null, 2)); console.log('· ' + s); };

const 浏览器 = await launch();
const page = 浏览器.page;

const 读 = () => page.evaluate((id) => {
  const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
  const v = document.querySelector('.react-flow__viewport');
  const m = /matrix\(([^)]+)\)/.exec(getComputedStyle(v).transform || '');
  const p = m ? m[1].split(',').map(Number) : [1, 0, 0, 1, 0, 0];
  const t = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
  const r = n.getBoundingClientRect();
  return {
    画布: t ? [Number(t[1]), Number(t[2])] : null,
    中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)],
    zoom: p[0],
    选中: n.classList.contains('selected'),
  };
}, ID);

try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(9000);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(3000);
  记('目标 ' + JSON.stringify(目标));
  记('起步 ' + JSON.stringify(await 读()));

  for (let 轮 = 1; 轮 <= 24; 轮++) {
    const s = await 读();
    if (!s.画布) { 记('⛔ 节点没渲染'); break; }
    const dx = 目标[0] - s.画布[0];
    const dy = 目标[1] - s.画布[1];
    const 误 = Math.hypot(dx, dy);
    记(`第 ${轮} 轮：现 [${s.画布[0]}, ${s.画布[1]}] 误差 ${误.toFixed(4)}（dx=${dx.toFixed(3)} dy=${dy.toFixed(3)}）`);
    if (误 < 0.5) { 记('✅ 到位'); break; }
    // ⭐ 只用**整数**屏幕像素；1 px = 1/zoom 画布单位
    const px = Math.max(-8, Math.min(8, Math.round(dx * s.zoom)));
    const py = Math.max(-8, Math.min(8, Math.round(dy * s.zoom)));
    if (px === 0 && py === 0) { 记(`⛔ 整数像素已为 0（dx*zoom=${(dx * s.zoom).toFixed(3)} dy*zoom=${(dy * s.zoom).toFixed(3)}），拖不动了`); break; }
    const v = await page.evaluate((p) => {
      const e = document.elementFromPoint(p[0], p[1]);
      const n = e ? e.closest('.react-flow__node') : null;
      return n && n.getAttribute('data-id');
    }, s.中心);
    if (v !== ID) { 记('⛔ 落点被 ' + v + ' 挡住'); break; }
    await page.mouse.move(s.中心[0], s.中心[1]); await page.waitForTimeout(360);
    await page.mouse.down(); await page.waitForTimeout(140);
    await page.mouse.move(s.中心[0] + px, s.中心[1] + py); await page.waitForTimeout(260);
    await page.mouse.up(); await page.waitForTimeout(650);
    await page.mouse.move(720, 250); await page.waitForTimeout(320);
  }

  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(15000);
  const 偏差 = await 核对坐标(page);
  记('⭐⭐ 静置 15s 后 `核对坐标`：' + JSON.stringify(偏差));
  const 现 = await 读全部坐标(page);
  记('复原后 ' + ID + ' = ' + JSON.stringify(现[ID]) + '（基线 ' + JSON.stringify(坐标[ID]) + '）');
} catch (e) {
  记('❌ ' + e.message);
} finally {
  await 浏览器.browser.close();
  console.log('\n=== 已写 tools/restore-at.json ===');
}

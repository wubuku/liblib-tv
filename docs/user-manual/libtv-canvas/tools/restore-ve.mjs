// ⭐⭐⭐ 定向复原：把 v-eMpqKtiLlx 从 [-1787,1320] 拖回 [-1787,900]
//
// 怎么弄的：EZ-1e 在「读下拉」那一步抛了 `选中框.map is not a function`，
// 而**复原写在那一步之后** —— 于是异常直接跳过复原，节点留在挪开的位置。
// ⭐⭐⭐ 教训：**任何改变画布的实验，复原都必须放在 `finally` 里**，
//    放在主流程里就等于「前面任何一步抛错 = 画布留伤」。
//    （这一批前面 EZ-1d 的复原是成功的，差别只在它没抛错。）
//
// 本脚本只做一件事：循环拖到误差 < 0.5 画布单位，然后静置 15s 复核。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const ID = 'v-eMpqKtiLlx';
const 目标 = 坐标[ID];
const HERE = new URL('.', import.meta.url).pathname;
const 落盘 = (o) => writeFileSync(HERE + 'restore-ve.json', JSON.stringify(o, null, 2));
const 日志 = [];
const 记 = (s) => { 日志.push(s); 落盘({ 日志 }); console.log('· ' + s); };

const 浏览器 = await launch();
const page = 浏览器.page;

const 快照 = () => page.evaluate((id) => {
  const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
  const v = document.querySelector('.react-flow__viewport');
  const m = /matrix\(([^)]+)\)/.exec(getComputedStyle(v).transform || '');
  const p = m ? m[1].split(',').map(Number) : [1, 0, 0, 1, 0, 0];
  if (!n) return null;
  const r = n.getBoundingClientRect();
  const t = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
  return {
    画布: t ? [Number(t[1]), Number(t[2])] : null,
    中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)],
    zoom: p[0],
  };
}, ID);

try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(9000);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(3000);
  记('目标画布坐标：' + JSON.stringify(目标));

  for (let 轮 = 1; 轮 <= 8; 轮++) {
    const s = await 快照();
    if (!s || !s.画布) { 记('⛔ 节点没渲染'); break; }
    const dx = 目标[0] - s.画布[0];
    const dy = 目标[1] - s.画布[1];
    const 误 = Math.hypot(dx, dy);
    记(`第 ${轮} 轮：现 [${s.画布[0]}, ${s.画布[1]}] → 目标 [${目标[0]}, ${目标[1]}]，误差 ${误.toFixed(3)}`);
    if (误 < 0.5) { 记('✅ 已到位'); break; }
    const sx = s.中心[0] + dx * s.zoom;
    const sy = s.中心[1] + dy * s.zoom;
    记(`  拖拽落点 ${sx.toFixed(0)},${sy.toFixed(0)}（zoom=${s.zoom}）`);
    if (sx < 2 || sy < 2 || sx > 1438 || sy > 808) { 记('⛔ 出视口，中止'); break; }
    // 铁律之二：点之前验落点
    const v = await page.evaluate((p) => {
      const e = document.elementFromPoint(p[0], p[1]);
      const n = e ? e.closest('.react-flow__node') : null;
      return { id: n && n.getAttribute('data-id'), tag: e && e.tagName };
    }, s.中心);
    if (v.id !== ID) { 记('⛔ 落点被 ' + v.id + ' 挡住，中止'); break; }
    await page.mouse.move(s.中心[0], s.中心[1]); await page.waitForTimeout(400);
    await page.mouse.down(); await page.waitForTimeout(140);
    for (let i = 1; i <= 14; i++) {
      await page.mouse.move(s.中心[0] + (sx - s.中心[0]) * i / 14, s.中心[1] + (sy - s.中心[1]) * i / 14);
      await page.waitForTimeout(40);
    }
    await page.mouse.up(); await page.waitForTimeout(800);
    await page.mouse.move(720, 780); await page.waitForTimeout(400);
  }

  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(15000);
  const 偏差 = await 核对坐标(page);
  记('⭐⭐ 静置 15s 后 `核对坐标`：' + JSON.stringify(偏差));
  const 现 = await 读全部坐标(page);
  记('复原后 ' + ID + ' 画布坐标 = ' + JSON.stringify(现[ID]) + '（基线 ' + JSON.stringify(坐标[ID]) + '）');
  落盘({ 日志, 偏差, 现值: 现[ID], 基线: 坐标[ID] });
} catch (e) {
  记('❌ ' + e.message);
} finally {
  落盘({ 日志 });
  await 浏览器.browser.close();
  console.log('\n=== 已写 tools/restore-ve.json ===');
}

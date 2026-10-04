// Batch EW-7：⭐⭐⭐ 最后一锤 —— 平移画布，看「新功能：支持真人」跟谁一起动。
//
// EW-6 已经排掉一大半：**6 个节点里只有 `v-v2hlWY4Br3`（视频节点 3）会出这个气泡**，
//   另外 5 个（另一个视频 / 智能剪辑 / 图片 / 逐帧拉片 / 导演台）**都没有**。
//   位置恒为 `[541,191,114,27]`。
//
//   相对那个节点卡（`[565,44,285,161]`）算：气泡左上角在卡的 **左边 24px、下边 147px**（卡高 161）。
//   ⛔ 但「只有一个节点会出」也可能是「它压根是固定位置的元素，跟节点无关」。
//
// 本轮只做一件事：**平移画布，让节点卡在屏幕上挪位置**。
//   ① 节点卡挪 Δ，气泡也挪 Δ  ⇒ 挂在节点上；
//   ② 只有节点卡挪            ⇒ 挂在别处（面板 / 顶栏 / 固定位置）；
//   ③ 两者都不挪              ⇒ 压根没挂上，位置是巧合。
//
// 平移用中键、量完原路拖回；⭐ 复原起点必须**先与视口求交**（EV-3/8 栽过这个坑）。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEW7.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const 浏览器 = await launch();
const page = 浏览器.page;

/** 一次量齐：气泡、节点卡、变换、以及面板上几个已知文字的框 */
const 量 = (page) => page.evaluate(() => {
  const 框 = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]; };
  const 出 = {};
  for (const e of document.querySelectorAll('[class*="mantine-Tooltip-tooltip"]')) {
    if ((e.innerText || '').trim() === '新功能：支持真人' && parseFloat(getComputedStyle(e).opacity) >= 0.5) { 出.气泡 = 框(e); break; }
  }
  const sel = document.querySelector('.react-flow__node.selected, .react-flow__node[aria-selected="true"]');
  if (sel) { 出.节点卡 = 框(sel); 出.节点id = sel.getAttribute('data-id'); }
  // 面板：用「全能创作」「文生视频」这类面板上才有的字当锚
  for (const t of ['全能创作', '文生视频', '开启']) {
    for (const e of document.querySelectorAll('*')) {
      if (e.children.length) continue;
      if ((e.textContent || '').trim() !== t) continue;
      const r = e.getBoundingClientRect();
      if (r.width < 2) continue;
      出['锚_' + t] = 框(e);
      break;
    }
  }
  const m = /matrix\(([^)]+)\)/.exec(getComputedStyle(document.querySelector('.react-flow__viewport')).transform);
  if (m) { const n = m[1].split(',').map(Number); 出.变换 = { zoom: n[0], pan: [n[4], n[5]] }; }
  return 出;
});

/** ⭐ 中键平移，起点终点先与视口求交 */
const 平移 = async (dx, dy) => {
  const 起 = await page.evaluate(() => {
    const c = [];
    for (let y = 120; y < 640; y += 20) for (let x = 120; x < 1320; x += 20) {
      const e = document.elementFromPoint(x, y);
      if (e && e.classList.contains('react-flow__pane')) c.push([x, y]);
    }
    return c.length ? c[Math.floor(c.length / 2)] : [720, 400];
  });
  const [sx, sy] = 起;
  const ex = Math.max(6, Math.min(1434, sx + dx));
  const ey = Math.max(6, Math.min(804, sy + dy));
  记(`平移：起(${sx},${sy}) → 终(${ex},${ey})，位移 ${ex - sx},${ey - sy}`);
  await page.mouse.move(sx, sy);
  await page.mouse.down({ button: 'middle' });
  for (let i = 1; i <= 10; i++) { await page.mouse.move(sx + Math.round(((ex - sx) * i) / 10), sy + Math.round(((ey - sy) * i) / 10)); await page.waitForTimeout(30); }
  await page.mouse.up({ button: 'middle' });
  await page.waitForTimeout(1500);
  // ⭐ 原路拖回 —— 起点就是上一次的终点，仍然在视口内
  await page.mouse.move(ex, ey);
  await page.mouse.down({ button: 'middle' });
  for (let i = 1; i <= 10; i++) { await page.mouse.move(ex - Math.round(((ex - sx) * i) / 10), ey - Math.round(((ey - sy) * i) / 10)); await page.waitForTimeout(30); }
  await page.mouse.up({ button: 'middle' });
  await page.waitForTimeout(1500);
};

try {
  await open(page, CANVAS_URL);
  await closePromos(page);
  await page.waitForTimeout(4000);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2500);
  记('开局坐标偏差：' + JSON.stringify(await 核对坐标(page)));

  // 选中视频节点 3
  const p = await page.evaluate(() => {
    const el = document.querySelector('.react-flow__node[data-id="v-v2hlWY4Br3"]');
    const r = el.getBoundingClientRect();
    return [Math.round(r.left + r.width / 2), Math.round(r.top + 14)];
  });
  const 验 = await page.evaluate(([x, y]) => {
    const n = document.elementFromPoint(x, y)?.closest('.react-flow__node');
    return n ? n.getAttribute('data-id') : null;
  }, p);
  记('落点自证=' + 验);
  if (验 !== 'v-v2hlWY4Br3') throw new Error('落点不对');
  await page.mouse.click(p[0], p[1]);
  await page.waitForTimeout(2500);

  const A = await 量(page);
  记('平移前：' + JSON.stringify(A));
  结果.读数.平移前 = A;

  // ⭐ 只平移，**不**拖回去（量完再回），这样中间态可读
  const 起 = await page.evaluate(() => {
    const c = [];
    for (let y = 120; y < 640; y += 20) for (let x = 120; x < 1320; x += 20) {
      const e = document.elementFromPoint(x, y);
      if (e && e.classList.contains('react-flow__pane')) c.push([x, y]);
    }
    return c.length ? c[Math.floor(c.length / 2)] : [720, 400];
  });
  const [sx, sy] = 起;
  const ex = Math.max(6, Math.min(1434, sx + 260));
  const ey = Math.max(6, Math.min(804, sy + 150));
  await page.mouse.move(sx, sy);
  await page.mouse.down({ button: 'middle' });
  for (let i = 1; i <= 10; i++) { await page.mouse.move(sx + Math.round(((ex - sx) * i) / 10), sy + Math.round(((ey - sy) * i) / 10)); await page.waitForTimeout(30); }
  await page.mouse.up({ button: 'middle' });
  await page.waitForTimeout(1800);

  const B = await 量(page);
  记('平移后：' + JSON.stringify(B));
  结果.读数.平移后 = B;

  const 差 = (k) => (A[k] && B[k]) ? [B[k][0] - A[k][0], B[k][1] - A[k][1]] : null;
  记('⭐ 各元素位移：');
  for (const k of ['气泡', '节点卡', '锚_全能创作', '锚_文生视频', '锚_开启']) 记(`   ${k}: ${JSON.stringify(差(k))}`);
  记(`   画布 pan: ${JSON.stringify(A.变换?.pan)} → ${JSON.stringify(B.变换?.pan)}`);
  结果.读数.位移 = {
    气泡: 差('气泡'), 节点卡: 差('节点卡'), 全能创作: 差('锚_全能创作'),
    文生视频: 差('锚_文生视频'), 开启: 差('锚_开启'),
    pan前: A.变换?.pan, pan后: B.变换?.pan,
  };
  await page.screenshot({ path: EVID + 'ew7-平移后.png' });
  记('已拍 ew7-平移后.png');

  // 复原：反向平移
  await 平移(-260, -150);
  const C = await 量(page);
  记('复原后：' + JSON.stringify(C));
  记('复原偏差（气泡）：' + JSON.stringify([C.气泡[0] - A.气泡[0], C.气泡[1] - A.气泡[1]]));
  结果.读数.复原后 = C;

  await page.mouse.click(40, 700);
  await page.waitForTimeout(1200);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(15000);
  const 偏差 = await 核对坐标(page);
  记('⭐⭐ 静置 15s 后坐标复核：' + JSON.stringify(偏差));
  结果.收尾 = { 偏差, 已渲染: Object.keys(await 读全部坐标(page)).length };
} catch (e) {
  记('❌ ' + e.message);
  结果.错误 = String((e && e.stack) || e);
} finally {
  落盘(结果);
  await 浏览器.browser.close();
  console.log('\n=== 已写 tools/batchEW7.json ===');
}

// ⭐⭐⭐⭐⭐ Batch FC-1：收掉 FB 留下的最大那个 📖
//
//   「网格吸附」**开着**和**关着**，拖动落点有没有差别？
//
// FB 已经确证：关着的时候落点就被吸附到 12 画布单位的格点。
// 但 FB-11 想测「开」态那一轮**中途失败**（节点被拖到右边后落点跑出框，`落点不合格 null`），
// 所以「开」态至今**一个字都没测到**。
//
// ⭐⭐⭐ 画布刚被「整理画布」铺成整齐网格，节点**不再互相遮挡**，
//    落点好找、拖拽干净 —— 这是做这个 A/B 最好的时机。
//
// 关键设计：
//   ① 每个节点先扫 6×6 找「属主对 且 无 nodrag 祖先」的落点，且**每轮重找**
//   ② 用「往返法」测：+13px 再 −13px，净位移必须为 0（零损伤）
//   ③ 三档开关态：关 → 开 → 关，比对**落点序列**而不只是最终位置
//   ④ 开关按「完整 outerHTML 归一化 diff」自证真的翻了
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标, 读全部坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = HERE + '.evidence/';
const R = { 步骤: [], 读数: {} };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFC1.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };

const 浏览器 = await launch();
const page = 浏览器.page;
const 读 = (id) => page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return null;
  const t = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
  const r = n.getBoundingClientRect();
  return { 画布: t ? [Number(t[1]), Number(t[2])] : null, 框: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] };
}, id);
const 开关DOM = () => page.evaluate(() => {
  let b = null;
  for (const x of document.querySelectorAll('button')) {
    const r = x.getBoundingClientRect();
    if (r.top < 740 || r.bottom > 810 || r.left > 340) continue;
    if ((x.getAttribute('aria-label') || '').includes('网格吸附')) { b = x; break; }
  }
  if (!b) return null;
  const r = b.getBoundingClientRect();
  return { svg数: b.querySelectorAll('svg').length, 外链: b.outerHTML.replace(/\s+/g, ' ').trim(), 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)] };
});
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
const 逐帧拖 = async (id, dx) => {
  const p = await 找落点(id);
  if (!p) return { 错: '找不到落点' };
  const 起 = (await 读(id)).画布;
  const 轨迹 = [];
  await page.mouse.move(p.x, p.y); await page.waitForTimeout(300);
  await page.mouse.down(); await page.waitForTimeout(160);
  const 帧数 = Math.max(2, Math.round(Math.abs(dx) / 2));
  for (let i = 1; i <= 帧数; i++) {
    await page.mouse.move(Math.round(p.x + (dx * i) / 帧数), p.y);
    await page.waitForTimeout(170);
    轨迹.push((await 读(id)).画布[0]);
  }
  await page.mouse.up(); await page.waitForTimeout(620);
  await page.mouse.move(720, 170); await page.waitForTimeout(240);
  return { 轨迹, 起, 后: (await 读(id)).画布[0] };
};
const 点开关 = async () => {
  const g = await 开关DOM();
  await page.mouse.move(g.中心[0], g.中心[1]); await page.waitForTimeout(350);
  await page.mouse.down(); await page.mouse.up(); await page.waitForTimeout(900);
  await page.mouse.move(720, 170); await page.waitForTimeout(500);
  return 开关DOM();
};

try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(12000);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(4000);
  const z = await page.evaluate(() => {
    const v = document.querySelector('.react-flow__viewport');
    const m = /matrix\(([^)]+)\)/.exec(getComputedStyle(v).transform || '');
    return m ? Number(m[1].split(',')[0]) : 1;
  });
  记(`zoom = ${z}｜1 屏px = ${(1 / z).toFixed(4)} 画布单位`);

  // ① 先看节点之间还重不重叠（FB 事故后布局变整齐了）
  记('—— ① 11 个节点的屏幕框，看有没有互相遮挡 ——');
  const 框集 = [];
  for (const id of Object.keys(坐标)) {
    const s = await 读(id);
    框集.push([id, s.框]);
    记(`   ${id} ${JSON.stringify(s.画布)} → 框 ${JSON.stringify(s.框)}`);
  }
  const 重叠 = [];
  for (let i = 0; i < 框集.length; i++) for (let j = i + 1; j < 框集.length; j++) {
    const [a, A] = 框集[i], [b, B] = 框集[j];
    const ox = Math.min(A[0] + A[2], B[0] + B[2]) - Math.max(A[0], B[0]);
    const oy = Math.min(A[1] + A[3], B[1] + B[3]) - Math.max(A[1], B[1]);
    if (ox > 0 && oy > 0) 重叠.push(`${a} × ${b} 重叠 ${ox}×${oy}`);
  }
  记(`   ⭐ 两两重叠 ${重叠.length} 对` + (重叠.length ? '：' + JSON.stringify(重叠) : ' ⇒ **没有遮挡**，落点好找'));
  R.读数.重叠 = 重叠;
  await page.screenshot({ path: EVID + 'fc1-01-新布局整屏.png' });

  // ② 挑一个四周干净的节点
  const ID = 't-UtVx3lZmrV';
  记(`—— ② 目标节点 ${ID} ——`);
  const g0 = await 开关DOM();
  记(`   开关外链（关）：svg 数 ${g0.svg数}`);
  记(`   ${g0.外链.slice(0, 260)}…`);
  R.读数.开关关 = g0;

  const 结果 = {};
  for (const 态 of ['关', '开', '关2']) {
    if (态 === '开') {
      const g1 = await 点开关();
      记(`   ⭐ 点开关后：svg 数 ${g1.svg数}｜外链变了？ ${g1.外链 !== g0.外链}`);
      R.读数.开关开 = g1;
    }
    if (态 === '关2') {
      await 点开关();
      const g2 = await 开关DOM();
      记(`   ⭐ 点回开关：svg 数 ${g2.svg数}｜外链与初始一致？ ${g2.外链 === g0.外链}`);
      R.读数.开关回 = g2;
    }
    const 当前 = await 开关DOM();
    const a = await 逐帧拖(ID, 13);
    const b = await 逐帧拖(ID, -13);
    const 止 = (await 读(ID)).画布;
    if (a.错) { 记(`   【${态}】⛔ ${a.错}`); continue; }
    记(`   【${态}】开关 svg 数 ${当前.svg数}`);
    记(`      +13px 轨迹 x：${JSON.stringify(a.轨迹)}`);
    记(`      落点 ${a.后}（起 ${a.起[0]}，位移 ${(a.后 - a.起[0]).toFixed(2)}）｜是 12 的倍数？ ${a.后 % 12 === 0}`);
    记(`      往返净位移 ${(止[0] - a.起[0]).toFixed(4)}`);
    结果[态] = { 正轨迹: a.轨迹, 正落点: a.后, 反落点: b.后, 净: Number((止[0] - a.起[0]).toFixed(4)) };
  }
  R.读数.对照 = 结果;
  const 关 = 结果['关'], 开 = 结果['开'];
  if (关 && 开) {
    记(`⭐⭐⭐ 关态落点 ${关.正落点}｜开态落点 ${开.正落点}｜**相同？ ${关.正落点 === 开.正落点}**`);
    记(`     关态轨迹 ${JSON.stringify(关.正轨迹)}`);
    记(`     开态轨迹 ${JSON.stringify(开.正轨迹)}`);
    记(`⭐⭐⭐⭐ 逐帧轨迹完全相同？ ${JSON.stringify(关.正轨迹) === JSON.stringify(开.正轨迹)}`);
  }
  await page.screenshot({ path: EVID + 'fc1-02-测完整屏.png' });
} catch (e) {
  R.错误 = String((e && e.stack) || e);
  记('❌ ' + e.message);
} finally {
  const g = await 开关DOM();
  if (g && g.svg数 >= 2) {
    await page.mouse.move(g.中心[0], g.中心[1]); await page.waitForTimeout(350);
    await page.mouse.down(); await page.mouse.up(); await page.waitForTimeout(900);
    await page.mouse.move(720, 170); await page.waitForTimeout(500);
    记(`finally：开关复原 → svg 数 ${(await 开关DOM()).svg数}`);
  }
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(15000);
  const 全 = await 读全部坐标(page);
  const 残 = Object.entries(坐标).filter(([id, xy]) => {
    const n = 全[id]; return !n || Math.hypot(n[0] - xy[0], n[1] - xy[1]) > 0.5;
  }).map(([id, xy]) => `${id} 基线${JSON.stringify(xy)} 现${JSON.stringify(全[id] || '未渲染')}`);
  记('⭐⭐ 静置 15s 后坐标复核：' + (残.length ? JSON.stringify(残) : '[]（全部一致）'));
  R.收尾 = 残;
  await 浏览器.browser.close();
  console.log('\n=== 已写 tools/batchFC1.json ===');
}

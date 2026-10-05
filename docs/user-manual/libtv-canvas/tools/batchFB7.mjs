// ⭐⭐⭐ Batch FB-7：**逐帧**看清拖拽的位移函数
//
// FB-6 读到的现象完全不合常理，必须一条条解释掉：
//   · ±1px 正 0 反 0；**±2px 正 −1.16**（正向拖却让 x 变小！）；±3~±30px 全部 0
//   · finally 里拖 (−1, 0) 屏px，却得到 x −1.16 / **y +1.025**，终态变成整数 [-1224, 372]
//   ⇒ 拖拽的位移**不是** 屏幕位移 ÷ zoom，且方向可能反
//
// ⭐⭐⭐ 两个必须先排掉的可能：
//   ① 上轮 ② 阶段按过的 `+` / `=` 键**本身有副作用**（不排除它改了节点坐标）
//   ② 导演台 class 是 `react-flow__node-director-console-3d` —— 3D 视窗节点，行为可能特殊
//      ⇒ 必须在**普通节点**上做同一实验做阳性对照
//
// 全程**只做往返**（+N 逐帧读，再 −N 逐帧读），净位移必须为 0。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const R = { 步骤: [], 读数: {} };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFB7.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };

const 浏览器 = await launch();
const page = 浏览器.page;
const ID = 'n-56F19pXVB4';
const 目标 = 坐标[ID];

const 读 = (id) => page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return null;
  const t = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
  const r = n.getBoundingClientRect();
  return {
    画布: t ? [Number(t[1]), Number(t[2])] : null,
    transform原文: n.style.transform,
    中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)],
  };
}, id);
const 读zoom = () => page.evaluate(() => {
  const v = document.querySelector('.react-flow__viewport');
  const m = /matrix\(([^)]+)\)/.exec(getComputedStyle(v).transform || '');
  return m ? Number(m[1].split(',')[0]) : 1;
});
const 全读 = () => page.evaluate(() => {
  const o = {};
  for (const n of document.querySelectorAll('.react-flow__node')) {
    const t = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
    o[n.getAttribute('data-id')] = t ? [Number(t[1]), Number(t[2])] : null;
  }
  return o;
});

/** 逐帧拖拽：steps 段，每段之间读一次坐标 */
const 逐帧拖 = async (id, dx, dy, 段数) => {
  const s = await 读(id);
  if (!s || !s.中心) return { 错: '读不到节点' };
  await page.mouse.move(s.中心[0], s.中心[1]);
  await page.waitForTimeout(320);
  const v = await page.evaluate((p) => {
    const e = document.elementFromPoint(p[0], p[1]);
    const n = e ? e.closest('.react-flow__node') : null;
    return n ? n.getAttribute('data-id') : null;
  }, s.中心);
  if (v !== id) return { 错: `落点 ${v}` };
  const 轨迹 = [];
  轨迹.push({ 帧: '按下', 画布: s.画布, 鼠标: [s.中心[0], s.中心[1]] });
  await page.mouse.down(); await page.waitForTimeout(150);
  for (let i = 1; i <= 段数; i++) {
    const mx = Math.round(s.中心[0] + (dx * i) / 段数);
    const my = Math.round(s.中心[1] + (dy * i) / 段数);
    await page.mouse.move(mx, my);
    await page.waitForTimeout(170);
    const q = await 读(id);
    轨迹.push({ 帧: i, 鼠标: [mx, my], 画布: q ? q.画布 : null });
  }
  await page.mouse.up(); await page.waitForTimeout(600);
  await page.mouse.move(720, 170); await page.waitForTimeout(240);
  const 后 = await 读(id);
  轨迹.push({ 帧: '松手后', 画布: 后.画布 });
  return { 轨迹, 后: 后.画布 };
};

try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(9000);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(3000);
  const z0 = await 读zoom();
  const 起 = (await 读(ID)).画布;
  记(`zoom=${z0}｜1 屏px = ${(1 / z0).toFixed(4)} 画布单位`);
  记(`导演台 基线 ${JSON.stringify(目标)}｜现 ${JSON.stringify(起)}｜偏差 x ${(起[0] - 目标[0]).toFixed(4)} y ${(起[1] - 目标[1]).toFixed(4)}`);
  R.读数.起 = 起;

  // ① `+` / `=` 键有没有副作用
  记('—— ① `=` / `+` 键的副作用 ——');
  for (const k of ['Equal', 'Equal', 'Equal', 'Equal', 'Equal', 'Equal']) {
    await page.keyboard.press(k);
    await page.waitForTimeout(320);
  }
  const 后键 = (await 读(ID)).画布;
  记(`   按 6 次 \`=\` 后：导演台 ${JSON.stringify(后键)}｜zoom ${await 读zoom()}`);
  记(`   ⭐ 坐标变了吗？ ${JSON.stringify(起) !== JSON.stringify(后键)}｜zoom 变了吗？ ${z0 !== await 读zoom()}`);
  R.读数.等键后 = 后键;

  // ② 滚轮缩放
  记('—— ② 滚轮缩放 ——');
  await page.mouse.move(720, 300); await page.waitForTimeout(300);
  for (let i = 0; i < 3; i++) { await page.mouse.wheel(0, -240); await page.waitForTimeout(450); }
  const z1 = await 读zoom();
  记(`   滚轮 ×3 后 zoom = ${z1}｜导演台 ${JSON.stringify((await 读(ID)).画布)}`);
  await page.keyboard.press('Meta+0'); await page.waitForTimeout(2500);
  记(`   ⌘0 复位后 zoom = ${await 读zoom()}｜导演台 ${JSON.stringify((await 读(ID)).画布)}`);
  R.读数.滚轮后 = z1;

  // ③ 导演台逐帧往返
  记(`—— ③ 导演台逐帧往返（+12px / −12px，各 6 段）——`);
  const z = await 读zoom();
  const a = await 逐帧拖(ID, 12, 0, 6);
  for (const t of (a.轨迹 || [])) 记(`   ${t.帧}｜鼠标 ${JSON.stringify(t.鼠标 || null)}｜画布 ${JSON.stringify(t.画布)}`);
  const b = await 逐帧拖(ID, -12, 0, 6);
  for (const t of (b.轨迹 || [])) 记(`   ${t.帧}｜鼠标 ${JSON.stringify(t.鼠标 || null)}｜画布 ${JSON.stringify(t.画布)}`);
  记(`   净位移：${JSON.stringify((b.后 || []).map((v, i) => Number((v - a.轨迹[0].画布[i]).toFixed(3))))}`);
  R.读数.导演台轨迹 = { 正: a.轨迹, 反: b.轨迹 };

  // ④ 普通节点逐帧往返（阳性对照）
  const 控 = 'v-oZNpH99MtM';
  const c0 = await 读(控);
  记(`—— ④ 阳性对照 ${控} ${JSON.stringify(c0.画布)} 中心 ${JSON.stringify(c0.中心)} ——`);
  const c1 = await 逐帧拖(控, 12, 0, 6);
  for (const t of (c1.轨迹 || [])) 记(`   ${t.帧}｜鼠标 ${JSON.stringify(t.鼠标 || null)}｜画布 ${JSON.stringify(t.画布)}`);
  const c2 = await 逐帧拖(控, -12, 0, 6);
  for (const t of (c2.轨迹 || [])) 记(`   ${t.帧}｜鼠标 ${JSON.stringify(t.鼠标 || null)}｜画布 ${JSON.stringify(t.画布)}`);
  记(`   净位移：${JSON.stringify((c2.后 || []).map((v, i) => Number((v - c1.轨迹[0].画布[i]).toFixed(3))))}`);
  R.读数.对照轨迹 = { 正: c1.轨迹, 反: c2.轨迹 };
} catch (e) {
  R.错误 = String((e && e.stack) || e);
  记('❌ ' + e.message);
} finally {
  记('—— finally：按基线往返复原 ——');
  for (let 轮 = 1; 轮 <= 8; 轮++) {
    const s = await 读(ID);
    if (!s || !s.画布) break;
    const dx = 目标[0] - s.画布[0], dy = 目标[1] - s.画布[1];
    if (Math.hypot(dx, dy) < 0.5) { 记(`✅ 导演台复原到位（轮 ${轮}）→ ${JSON.stringify(s.画布)}`); break; }
    const z = await 读zoom();
    const px_ = Math.round(dx * z), py = Math.round(dy * z);
    记(`   轮${轮}：现 ${JSON.stringify(s.画布)} 误差 ${Math.hypot(dx, dy).toFixed(4)} → ${px_},${py}px`);
    if (!px_ && !py) { 记('   ⛔ 整数像素为 0，停'); break; }
    const r1 = await 逐帧拖(ID, px_, py, 4);
    const r2 = await 逐帧拖(ID, -px_, -py, 4);
    记(`     一来一回后 ${JSON.stringify((await 读(ID)).画布)}`);
  }
  记(`  导演台终态 ${JSON.stringify((await 读(ID)).画布)}｜基线 ${JSON.stringify(目标)}`);
  for (const id of ['v-oZNpH99MtM']) {
    记(`  ${id} 终态 ${JSON.stringify((await 读(id)).画布)}｜基线 ${JSON.stringify(坐标[id])}`);
  }
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(15000);
  const 全 = await 全读();
  const 残 = Object.entries(坐标).filter(([id, xy]) => {
    const n = 全[id]; return !n || Math.hypot(n[0] - xy[0], n[1] - xy[1]) > 0.5;
  }).map(([id, xy]) => `${id} 基线${JSON.stringify(xy)} 现${JSON.stringify(全[id] || '未渲染')}`);
  记('⭐⭐ 静置 15s 后复核：' + (残.length ? JSON.stringify(残) : '[]（全部一致）'));
  R.收尾 = 残;
  await 浏览器.browser.close();
  console.log('\n=== 已写 tools/batchFB7.json ===');
}

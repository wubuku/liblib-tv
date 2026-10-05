// ⭐⭐⭐ Batch FB-6：解决两件事
//   ① **把导演台的 2.19 画布单位损伤复原回去**（已落盘，刷新也回不去）
//   ② 顺手把「为什么小位移拖不动」测清楚 —— 这是 FB-3/FB-4 的判据缺陷
//
// 已知事实（都是本轮亲手读出来的）：
//   · hover **不污染** `style.transform`（同一节点移开/停上/再移开，原文逐字相同）
//   · 刷新后导演台仍是 [-1222.84, 370.975] ⇒ 损伤**已落盘**
//   · 新会话里对导演台 `-1px × 30 轮`、对普通文本节点 `+5px`、方向键 ×2，位移全是 **0.0000**
//   · 但 FB-1 时期的复原**用 ±1~2px 成功过** ⇒ 不是应用行为变了，是判据/写法问题
//
// ⭐⭐⭐ 方法：**往返法**测阈值 —— 先 +N px 再 −N px，净位移必然为 0，
//   于是既能知道「从哪一档开始真的动了」，又不会留下任何新损伤。
// ⭐⭐⭐ 复原的关键：放大 zoom，让 1 屏 px 对应的画布单位变小，
//   于是 **2.19 画布单位可以用一个「大于阈值的整数屏 px」精确表达**。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const ID = 'n-56F19pXVB4';
const 目标 = 坐标[ID];
const HERE = new URL('.', import.meta.url).pathname;
const EVID = HERE + '.evidence/';
const R = { 步骤: [], 读数: {} };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFB6.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };

const 浏览器 = await launch();
const page = 浏览器.page;

const 读zoom = () => page.evaluate(() => {
  const v = document.querySelector('.react-flow__viewport');
  const m = /matrix\(([^)]+)\)/.exec(getComputedStyle(v).transform || '');
  return m ? Number(m[1].split(',')[0]) : 1;
});
const 读 = (id) => page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return null;
  const t = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
  const r = n.getBoundingClientRect();
  return { 画布: t ? [Number(t[1]), Number(t[2])] : null, 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)] };
}, id);
/** 吸附开关：返回当前是开(有第二枚 svg)还是关 */
const 吸附态 = () => page.evaluate(() => {
  let b = null;
  for (const x of document.querySelectorAll('button')) {
    const r = x.getBoundingClientRect();
    if (r.top < 740 || r.bottom > 810 || r.left > 340) continue;
    if ((x.getAttribute('aria-label') || '').includes('网格吸附')) { b = x; break; }
  }
  if (!b) return null;
  const svg数 = b.querySelectorAll('svg').length;
  const r = b.getBoundingClientRect();
  return { svg数, 开: svg数 >= 2, 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)] };
});
const 拖 = async (id, dx, dy) => {
  const s = await 读(id);
  if (!s || !s.中心) return { 错: '读不到节点' };
  await page.mouse.move(s.中心[0], s.中心[1]);
  await page.waitForTimeout(300);
  const v = await page.evaluate((p) => {
    const e = document.elementFromPoint(p[0], p[1]);
    const n = e ? e.closest('.react-flow__node') : null;
    return n ? n.getAttribute('data-id') : null;
  }, s.中心);
  if (v !== id) return { 错: `落点 ${v}` };
  await page.mouse.down(); await page.waitForTimeout(140);
  await page.mouse.move(s.中心[0] + dx, s.中心[1] + dy, { steps: 8 });
  await page.waitForTimeout(300);
  await page.mouse.up(); await page.waitForTimeout(620);
  await page.mouse.move(720, 170); await page.waitForTimeout(240);
  return { 成功: true };
};

let 动过 = [];
try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(9000);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(3000);
  let z = await 读zoom();
  记(`zoom = ${z}`);
  const 起 = (await 读(ID)).画布;
  记(`导演台 基线 ${JSON.stringify(目标)}｜现 ${JSON.stringify(起)}｜偏差 ${(起[0] - 目标[0]).toFixed(4)}`);
  动过 = [[ID, 起.slice()]];

  const g = await 吸附态();
  记(`⭐ 进场吸附态：svg 数 ${g.svg数} ⇒ **${g.开 ? '开' : '关'}**`);
  R.读数.进场吸附 = g;

  // —— ① 往返法测阈值（在当前 zoom 下）——
  记('—— ① 往返法测拖拽阈值（当前 zoom）——');
  const 阈值表 = [];
  for (const n of [1, 2, 3, 4, 6, 8, 12, 20, 30]) {
    const a0 = (await 读(ID)).画布;
    await 拖(ID, n, 0);
    const a1 = (await 读(ID)).画布;
    await 拖(ID, -n, 0);
    const a2 = (await 读(ID)).画布;
    const 正 = Number((a1[0] - a0[0]).toFixed(4));
    const 反 = Number((a2[0] - a1[0]).toFixed(4));
    const 净 = Number((a2[0] - a0[0]).toFixed(4));
    阈值表.push({ n, 正, 反, 净 });
    记(`   ±${String(n).padStart(2)}px：正 ${正}｜反 ${反}｜净 ${净}`);
  }
  R.读数.阈值 = 阈值表;
  const 起动 = 阈值表.find((t) => Math.abs(t.正) > 0.01);
  记(`   ⭐ 从 ${起动 ? 起动.n + 'px' : '（30px 都没动）'} 起开始生效`);

  // —— ② 放大 zoom ——
  记('—— ② 探缩放手段 ——');
  const 试 = [];
  for (const k of ['+', 'Equal', 'Add']) {
    for (let i = 0; i < 3; i++) { await page.keyboard.press(k); await page.waitForTimeout(400); }
    试.push({ 键: k, zoom: await 读zoom() });
  }
  await page.mouse.move(720, 300); await page.waitForTimeout(300);
  for (const d of [-240, -240, -240, -240]) { await page.mouse.wheel(0, d); await page.waitForTimeout(500); }
  试.push({ 键: '滚轮×4', zoom: await 读zoom() });
  记('   ' + JSON.stringify(试));
  await page.screenshot({ path: EVID + 'fb6-01-放大后.png' });

  const z2 = await 读zoom();
  R.读数.缩放尝试 = 试; R.读数.放大后zoom = z2;
  记(`⭐ 放大后 zoom = ${z2}｜1 屏 px = ${(1 / z2).toFixed(5)} 画布单位`);

  // —— ③ 在放大后的 zoom 下再测一次阈值，然后精确复原 ——
  记('—— ③ 放大后重测阈值 + 精确复原 ——');
  const 单位 = 1 / z2;
  const 需要屏px = Math.round((目标[0] - 起[0]) / 单位);
  记(`⭐ 要补 ${(目标[0] - 起[0]).toFixed(4)} 画布单位 ⇒ 需要 ${(目标[0] - 起[0]) / 单位} 屏 px ⇒ 取整 **${需要屏px} 屏 px**（等于 ${(需要屏px * 单位).toFixed(4)} 画布单位）`);
  if (Math.abs(需要屏px * 单位 - (目标[0] - 起[0])) > 0.5) 记('⛔ 取整误差超过 0.5 画布单位，不能这样复原');

  if (需要屏px !== 0) {
    const 前 = (await 读(ID)).画布;
    const r = await 拖(ID, 需要屏px, 0);
    const 后 = (await 读(ID)).画布;
    记(`   拖 ${需要屏px}px：${r.成功 ? '成功' : JSON.stringify(r)}｜${JSON.stringify(前)} → ${JSON.stringify(后)}`);
    记(`   ⭐ 偏差 ${(后[0] - 目标[0]).toFixed(4)}（|偏差| < 0.5 即复原成功）`);
  }
  await page.screenshot({ path: EVID + 'fb6-02-复原尝试后.png' });
} catch (e) {
  R.错误 = String((e && e.stack) || e);
  记('❌ ' + e.message);
} finally {
  // 复原：先按基线拖回去，容差 0.5
  for (const [id, 原位] of 动过) {
    for (let 轮 = 1; 轮 <= 20; 轮++) {
      const s = await 读(id);
      if (!s || !s.画布) break;
      const dx = 目标[0] - s.画布[0], dy = 目标[1] - s.画布[1];
      if (Math.hypot(dx, dy) < 0.5) { 记(`✅ ${id} 复原到位（轮 ${轮}）→ ${JSON.stringify(s.画布)}`); break; }
      const zz = await 读zoom();
      const px_ = Math.max(-30, Math.min(30, Math.round(dx * zz)));
      const py = Math.max(-30, Math.min(30, Math.round(dy * zz)));
      if (px_ === 0 && py === 0) { 记(`⛔ ${id} 整数像素为 0（剩余 ${Math.hypot(dx, dy).toFixed(4)}）`); break; }
      const r = await 拖(id, px_, py);
      if (!r.成功) { 记(`⛔ ${id} 复原拖失败：${JSON.stringify(r)}`); break; }
    }
    记(`  ${id} 终态 ${JSON.stringify((await 读(id)).画布)}｜基线 ${JSON.stringify(目标)}`);
  }
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
  记('⭐⭐ 静置 15s 后坐标复核：' + (残.length ? JSON.stringify(残) : '[]（全部一致）'));
  R.收尾 = 残;
  await 浏览器.browser.close();
  console.log('\n=== 已写 tools/batchFB6.json ===');
}

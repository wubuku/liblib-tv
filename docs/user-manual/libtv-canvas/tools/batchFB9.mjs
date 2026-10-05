// ⭐⭐⭐ Batch FB-9：确证「12 画布单位吸附」并查清 y 抖动
//
// FB-7/FB-8 在导演台上看到落点按 12 画布单位跳变，FB-8 把 x 精确复原到 −1224。
// 但导演台 class 是 `react-flow__node-director-console-3d`，**是个 3D 视窗节点**，
// 它的 y 读数在 367 / 370.975 / 372 之间来回跳 ⇒ 可能是读数不可靠，而不是真的动了。
//
// 本轮三件事：
//   ① 导演台静止时连读 20 次，看 y 自己会不会抖；并把它 `getComputedStyle().transform`
//      与 `style.transform` 并排，看 3D 到底叠了什么
//   ② ⭐⭐⭐ **在普通节点上验证 12 格吸附**（往返，净位移必须为 0）
//      预测：t-UtVx3lZmrV 现在 x=600，逐帧 +13px（=+28.35 画布单位）⇒ 自由位置 628.35，
//      最近 12 倍数是 624（差 4.35）而不是 636（差 7.65）⇒ **应落在 624**；
//      再逐帧 −13px ⇒ 595.65 ⇒ 最近是 600 ⇒ **应回到 600**。落点对上了才算数。
//   ③ 顺带量一下「吸附」在关/开两态下有没有区别（这才是「网格吸附」这枚开关的作用）
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const R = { 步骤: [], 读数: {} };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFB9.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };

const 浏览器 = await launch();
const page = 浏览器.page;
const 读 = (id) => page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return null;
  const t = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
  const r = n.getBoundingClientRect();
  return { 画布: t ? [Number(t[1]), Number(t[2])] : null, 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)] };
}, id);
const 吸附态 = () => page.evaluate(() => {
  let b = null;
  for (const x of document.querySelectorAll('button')) {
    const r = x.getBoundingClientRect();
    if (r.top < 740 || r.bottom > 810 || r.left > 340) continue;
    if ((x.getAttribute('aria-label') || '').includes('网格吸附')) { b = x; break; }
  }
  if (!b) return null;
  const r = b.getBoundingClientRect();
  return { svg数: b.querySelectorAll('svg').length, 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)] };
});
const 逐帧拖 = async (id, dx, dy) => {
  const s = await 读(id);
  if (!s || !s.中心) return { 错: '读不到节点' };
  await page.mouse.move(s.中心[0], s.中心[1]); await page.waitForTimeout(300);
  const v = await page.evaluate((p) => {
    const e = document.elementFromPoint(p[0], p[1]);
    const n = e ? e.closest('.react-flow__node') : null;
    return n ? n.getAttribute('data-id') : null;
  }, s.中心);
  if (v !== id) return { 错: `落点 ${v}` };
  const 轨迹 = [{ 帧: '按下', 画布: s.画布 }];
  await page.mouse.down(); await page.waitForTimeout(160);
  const 帧数 = Math.max(2, Math.round(Math.abs(dx) / 2));
  for (let i = 1; i <= 帧数; i++) {
    await page.mouse.move(Math.round(s.中心[0] + (dx * i) / 帧数), Math.round(s.中心[1] + (dy * i) / 帧数));
    await page.waitForTimeout(170);
    轨迹.push({ 帧: i, 画布: (await 读(id)).画布 });
  }
  await page.mouse.up(); await page.waitForTimeout(600);
  await page.mouse.move(720, 170); await page.waitForTimeout(240);
  return { 轨迹, 后: (await 读(id)).画布 };
};

try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(9000);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(3000);

  // ① 导演台静止连读
  记('—— ① 导演台静止时连读 20 次 ——');
  const 序列 = [];
  for (let i = 0; i < 20; i++) { 序列.push((await 读('n-56F19pXVB4')).画布); await page.waitForTimeout(300); }
  const uniq = [...new Set(序列.map((s) => JSON.stringify(s)))];
  记('   取值集合 = ' + JSON.stringify(uniq) + `｜共 ${uniq.length} 种`);
  R.读数.静止序列 = 序列;
  const 详细 = await page.evaluate(() => {
    const n = document.querySelector('.react-flow__node[data-id="n-56F19pXVB4"]');
    const c = getComputedStyle(n);
    return { styleTransform: n.style.transform, 计算transform: c.transform, transformStyle: c.transformStyle, perspective: c.perspective, 宽: c.width, 高: c.height };
  });
  记('   style.transform = ' + JSON.stringify(详细.styleTransform));
  记('   计算 transform  = ' + JSON.stringify(详细.计算transform));
  记('   transform-style = ' + 详细.transformStyle + '｜perspective = ' + 详细.perspective);
  记('   尺寸 = ' + 详细.宽 + ' × ' + 详细.高);
  R.读数.导演台样式 = 详细;

  // ② 普通节点验证 12 格吸附
  const 控 = 't-UtVx3lZmrV';
  const g0 = await 吸附态();
  记(`—— ② 普通节点 ${控}（${JSON.stringify(坐标[控])}）｜吸附开关 svg 数 ${g0.svg数} ⇒ ${g0.svg数 >= 2 ? '开' : '关'} ——`);
  for (const 态 of ['关', '开']) {
    if (态 === '开') {
      await page.mouse.move(g0.中心[0], g0.中心[1]); await page.waitForTimeout(300);
      await page.mouse.down(); await page.mouse.up(); await page.waitForTimeout(900);
      await page.mouse.move(720, 170); await page.waitForTimeout(500);
      const g1 = await 吸附态();
      记(`   点开关后 svg 数 = ${g1.svg数} ⇒ ${g1.svg数 >= 2 ? '开' : '关'}`);
    }
    const 起 = (await 读(控)).画布;
    const a = await 逐帧拖(控, 13, 0);
    const 中 = (await 读(控)).画布;
    const b = await 逐帧拖(控, -13, 0);
    const 止 = (await 读(控)).画布;
    记(`   【吸附${态}】${JSON.stringify(起)} --+13px--> ${JSON.stringify(中)} --−13px--> ${JSON.stringify(止)}`);
    记(`      预测落点 ${JSON.stringify([624, 起[1]])}（600+28.35=628.35，最近 12 倍数是 624）｜实测 ${JSON.stringify(中)}｜**命中？ ${Math.abs(中[0] - 624) < 0.5}**`);
    记(`      往返净位移 = ${(止[0] - 起[0]).toFixed(4)}, ${(止[1] - 起[1]).toFixed(4)}`);
    记(`      轨迹：${JSON.stringify(a.轨迹.map((t) => t.画布))}`);
    R.读数['控_' + 态] = { 起, 中, 止, 轨迹: a.轨迹.map((t) => t.画布) };
  }
  // 开关复原
  const g2 = await 吸附态();
  if (g2.svg数 >= 2) {
    await page.mouse.move(g2.中心[0], g2.中心[1]); await page.waitForTimeout(300);
    await page.mouse.down(); await page.mouse.up(); await page.waitForTimeout(900);
    await page.mouse.move(720, 170); await page.waitForTimeout(500);
    记(`   开关复原：svg 数 = ${(await 吸附态()).svg数}`);
  }
} catch (e) {
  R.错误 = String((e && e.stack) || e);
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
  R.收尾 = 残;
  await 浏览器.browser.close();
  console.log('\n=== 已写 tools/batchFB9.json ===');
}

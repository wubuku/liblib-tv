// ⭐⭐⭐ Batch FB-11：同一节点、开/关两态，各做一次**可预测**的拖拽
//
// FB-10 已经在普通节点 `v-oZNpH99MtM` 上看到落点量化：132 → **156**，156 = 13×12。
// ⛔ 我那个预测公式写错了（`13 * 0.458621 * 2.1804` = 13，不是 28.35），
//    所以打印出来的「预测 144」是脚本 bug，**不是判据反例**。正确预测就是 156。
//
// 本轮把公式修正，并用更大的位移做**可手算的预测**，同时对比开关两态：
//   +25 屏 px = +54.51 画布单位
//   起点 x=132 ⇒ 自由位置 186.51 ⇒ 最近 12 倍数 = **192**（差 5.49）而不是 180（差 6.51）
//   ⇒ 若吸附是「就近取整」，落点必须是 **192**
//   若不吸附，落点应落在 186.51 附近（不可能正好是 192）
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const ID = 'v-oZNpH99MtM';
const 屏px = 25;
const HERE = new URL('.', import.meta.url).pathname;
const R = { 步骤: [], 读数: {} };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFB11.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };
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
const 逐帧拖 = async (id, x, y, dx) => {
  await page.mouse.move(x, y); await page.waitForTimeout(300);
  const v = await page.evaluate((p) => {
    const e = document.elementFromPoint(p[0], p[1]);
    const n = e ? e.closest('.react-flow__node') : null;
    return n && !e.closest('.nodrag') ? n.getAttribute('data-id') : null;
  }, [x, y]);
  if (v !== id) return { 错: `落点不合格 ${v}` };
  const 起 = (await 读(id)).画布;
  const 轨迹 = [{ 帧: '按下', 画布: 起 }];
  await page.mouse.down(); await page.waitForTimeout(160);
  const 帧数 = Math.max(2, Math.round(Math.abs(dx) / 2));
  for (let i = 1; i <= 帧数; i++) {
    await page.mouse.move(Math.round(x + (dx * i) / 帧数), y);
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
  const s = await 读(ID);
  const [L, T, W] = s.框;
  const 落点 = [L + Math.round(W * 0.5 / 6), T + Math.round(H_at(T, s) * 0.5 / 6)];
  function H_at(_t, ss) { return ss.框[3]; }
  记(`${ID} 基线 ${JSON.stringify(坐标[ID])}｜框 ${JSON.stringify(s.框)}｜落点 ${JSON.stringify(落点)}`);

  for (const 态 of ['关', '开']) {
    const g = await 吸附态();
    记(`—— 吸附开关 svg 数 = ${g.svg数} ⇒ **${g.svg数 >= 2 ? '开' : '关'}** ——`);
    const 起 = (await 读(ID)).画布;
    const 自由 = 起[0] + 屏px / ZOOM;
    const 预测 = Math.round(自由 / 12) * 12;
    记(`   起点 ${JSON.stringify(起)}｜+${屏px} 屏px = +${(屏px / ZOOM).toFixed(2)} 画布单位｜自由位置 ${自由.toFixed(2)}｜**最近 12 倍数 = ${预测}**｜不吸附应落在 ${自由.toFixed(2)} 附近`);
    const a = await 逐帧拖(ID, 落点[0], 落点[1], 屏px);
    if (a.错) { 记('   ⛔ ' + a.错); }
    else {
      记('   轨迹：' + JSON.stringify(a.轨迹.map((t) => t.画布 && t.画布[0])));
      记(`   落点 ${JSON.stringify(a.后)}｜**等于 12 的倍数 ${预测}？ ${a.后[0] === 预测}**｜到自由值 ${自由.toFixed(2)} 的差 ${(a.后[0] - 自由).toFixed(2)}`);
      R.读数[态] = { 起, 后: a.后, 自由, 预测, 轨迹: a.轨迹.map((t) => t.画布) };
    }
    const b = await 逐帧拖(ID, 落点[0], 落点[1], -屏px);
    const 止 = (await 读(ID)).画布;
    记(`   往返：${JSON.stringify(起)} → ${JSON.stringify(止)}｜净 ${(止[0] - 起[0]).toFixed(4)}`);
    if (态 === '关') {
      const g2 = await 吸附态();
      await page.mouse.move(g2.中心[0], g2.中心[1]); await page.waitForTimeout(300);
      await page.mouse.down(); await page.mouse.up(); await page.waitForTimeout(900);
      await page.mouse.move(720, 170); await page.waitForTimeout(500);
      记(`   点开关后 svg 数 = ${(await 吸附态()).svg数}`);
    }
  }
  const g3 = await 吸附态();
  if (g3.svg数 >= 2) {
    await page.mouse.move(g3.中心[0], g3.中心[1]); await page.waitForTimeout(300);
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
  console.log('\n=== 已写 tools/batchFB11.json ===');
}

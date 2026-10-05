// ⭐⭐⭐ Batch FB-10：用**避开 nodrag 的落点**在普通节点上验证「12 画布单位吸附」
//
// FB-9 的判据又漏了一项：只验了 elementFromPoint 命中本节点，**没验命中的元素有没有 nodrag 祖先**。
// 于是 t-UtVx3lZmrV / v-oZNpH99MtM 的中心落点虽然 `closest('.react-flow__node')` 对，
// 但那个点命中的是内容里的 `nodrag` 元素 ⇒ 拖拽根本不启动 ⇒ 位移 0。
// 导演台能拖是因为它的中心区域没有 nodrag。
//
// 本轮：框内 6×6 扫格，找「属本节点 且 最近 nodrag 祖先为 null」的点，在那上面做逐帧往返。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const R = { 步骤: [], 读数: {} };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFB10.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };

const 浏览器 = await launch();
const page = 浏览器.page;
const 读 = (id) => page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return null;
  const t = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
  const r = n.getBoundingClientRect();
  return { 画布: t ? [Number(t[1]), Number(t[2])] : null, 框: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] };
}, id);
const 落点信息 = (p) => page.evaluate(([x, y]) => {
  const e = document.elementFromPoint(x, y);
  if (!e) return null;
  const n = e.closest('.react-flow__node');
  const nd = e.closest('.nodrag');
  return {
    节点: n ? n.getAttribute('data-id') : null,
    有nodrag: !!nd,
    nodrag类: nd ? (nd.getAttribute('class') || '').slice(0, 70) : null,
    标签: e.tagName, class: (e.getAttribute('class') || '').slice(0, 70),
  };
}, p);
const 逐帧拖 = async (id, x, y, dx, dy) => {
  await page.mouse.move(x, y); await page.waitForTimeout(300);
  const v = await 落点信息([x, y]);
  if (!v || v.节点 !== id) return { 错: '落点不属于本节点', v };
  if (v.有nodrag) return { 错: '落点有 nodrag', v };
  const 起 = (await 读(id)).画布;
  const 轨迹 = [{ 帧: '按下', 画布: 起 }];
  await page.mouse.down(); await page.waitForTimeout(160);
  const 帧数 = Math.max(2, Math.round(Math.abs(dx) / 2));
  for (let i = 1; i <= 帧数; i++) {
    await page.mouse.move(Math.round(x + (dx * i) / 帧数), Math.round(y + (dy * i) / 帧数));
    await page.waitForTimeout(170);
    轨迹.push({ 帧: i, 画布: (await 读(id)).画布 });
  }
  await page.mouse.up(); await page.waitForTimeout(600);
  await page.mouse.move(720, 170); await page.waitForTimeout(240);
  return { 轨迹, 后: (await 读(id)).画布 };
};

const 目标 = ['t-UtVx3lZmrV', 'v-oZNpH99MtM'];
try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(9000);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(3000);

  for (const id of 目标) {
    const s = await 读(id);
    const [L, T, W, H] = s.框;
    记(`—— ${id} 基线 ${JSON.stringify(坐标[id])}｜框 ${JSON.stringify(s.框)}｜现 ${JSON.stringify(s.画布)} ——`);
    // 6×6 扫格找可拖落点
    const 可拖 = [];
    for (let r = 0; r < 6; r++) for (let c = 0; c < 6; c++) {
      const x = L + Math.round(W * (c + 0.5) / 6);
      const y = T + Math.round(H * (r + 0.5) / 6);
      if (x < 2 || x > 1438 || y < 2 || y > 808) continue;
      const v = await 落点信息([x, y]);
      if (v && v.节点 === id && !v.有nodrag) 可拖.push({ x, y, class: v.class });
    }
    记(`   6×6 扫出可拖落点 ${可拖.length} 个` + (可拖.length ? '｜样本 ' + JSON.stringify(可拖.slice(0, 5).map((p) => [p.x, p.y, p.class])) : ''));
    if (!可拖.length) { 记('   ⛔ 本节点框内没有可拖落点'); continue; }

    const 起 = (await 读(id)).画布;
    const 预测 = Math.round((起[0] + 13 * 0.458621 * 2.1804) / 12) * 12;
    记(`   ⭐ 预测：+13 屏px = +${(13 / 0.458621).toFixed(2)} 画布单位 ⇒ 自由位置 ${(起[0] + 13 / 0.458621).toFixed(2)} ⇒ 最近 12 倍数 **${预测}**`);
    const a = await 逐帧拖(id, 可拖[0].x, 可拖[0].y, 13, 0);
    if (a.错) { 记('   ⛔ ' + JSON.stringify(a)); }
    else {
      记('   轨迹：' + JSON.stringify(a.轨迹.map((t) => t.画布)));
      记(`   落点 ${JSON.stringify(a.后)}｜**命中预测 ${预测}？ ${Math.abs(a.后[0] - 预测) < 0.5}**｜位移 ${(a.后[0] - 起[0]).toFixed(4)}（自由值应为 ${(13 / 0.458621).toFixed(2)}）`);
      R.读数[id] = { 起, 后: a.后, 预测, 轨迹: a.轨迹.map((t) => t.画布) };
    }
    // 往返复原
    const 中 = (await 读(id)).画布;
    const b = await 逐帧拖(id, 可拖[0].x, 可拖[0].y, -13, 0);
    const 止 = (await 读(id)).画布;
    记(`   往返：${JSON.stringify(起)} → ${JSON.stringify(中)} → ${JSON.stringify(止)}｜净 ${(止[0] - 起[0]).toFixed(4)}, ${(止[1] - 起[1]).toFixed(4)}`);
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
  console.log('\n=== 已写 tools/batchFB10.json ===');
}

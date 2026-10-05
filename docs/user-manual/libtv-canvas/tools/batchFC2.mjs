// ⭐⭐⭐⭐⭐ Batch FC-2：网格吸附开关「开 / 关」对落点的影响（FB 留下的最大 📖）
//
// FC-1 拿到两条有用的读数，但没测到东西：
//   ⭐ **新布局两两重叠 0 对**（FB 事故后「整理画布」把节点铺成了整齐网格）⇒ 落点好找
//   ⭐ 开关的完整 outerHTML diff **第三次**独立确证：关 1 枚 svg → 开 2 枚 → 点回完全一致
//   ⛔ `t-UtVx3lZmrV` 框内 9 个候选落点**全部有 nodrag 祖先**（和 FB-9 同一个坑）
//
// 本轮改成：先自动挑「框内有干净落点」的节点，再做三档开关态的逐帧 A/B。
// ⭐ 预测用**当轮实测的 zoom**（本轮是 0.482682，1 屏px = 2.0718 画布单位，不是 46% 那套）。
// ⭐⭐ 兜底：finally 里按基线做闭环复原，每轮重找落点、按 12 格距换算像素
//   —— FB 事故的根因就是不做这个换算，这轮把它写死在 finally 里。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标, 读全部坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = HERE + '.evidence/';
const R = { 步骤: [], 读数: {} };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFC2.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };
let Z = 0.482682;

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
  return { 画布: t ? [Number(t[1]), Number(t[2])] : null, 框: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] };
}, id);
/** ⭐ 框内 6×6 扫格，返回「属主对 且 无 nodrag 祖先」的落点列表 */
const 扫落点 = async (id) => {
  const s = await 读(id);
  if (!s || !s.框) return [];
  const [L, T, W, H] = s.框;
  const 好 = [];
  for (let r = 0; r < 6; r++) for (let c = 0; c < 6; c++) {
    const x = L + Math.round(W * (c + 0.5) / 6), y = T + Math.round(H * (r + 0.5) / 6);
    if (x < 4 || x > 1436 || y < 4 || y > 806) continue;
    const ok = await page.evaluate((p) => {
      const e = document.elementFromPoint(p[0], p[1]);
      const n = e ? e.closest('.react-flow__node') : null;
      return !!(n && !e.closest('.nodrag') && n.getAttribute('data-id') === p[2]);
    }, [x, y, id]);
    if (ok) 好.push({ x, y });
  }
  return 好;
};
const 逐帧拖 = async (id, p, dx) => {
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
const 开关 = () => page.evaluate(() => {
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
const 点开关 = async () => {
  const g = await 开关();
  await page.mouse.move(g.中心[0], g.中心[1]); await page.waitForTimeout(350);
  await page.mouse.down(); await page.mouse.up(); await page.waitForTimeout(900);
  await page.mouse.move(720, 170); await page.waitForTimeout(500);
  return 开关();
};
/** ⭐ 闭环复原：按 12 格距换算像素，每轮重找落点 */
const 闭环复原 = async (id) => {
  for (let 轮 = 1; 轮 <= 14; 轮++) {
    const s = await 读(id);
    if (!s || !s.画布) return 读不到;
    const dx = 坐标[id][0] - s.画布[0], dy = 坐标[id][1] - s.画布[1];
    if (Math.hypot(dx, dy) < 0.5) return { ok: true, 轮, 终: s.画布 };
    let px = Math.round((dx - Math.sign(dx) * Math.min(4, Math.abs(dx) / 6)) / Z);
    if (dx !== 0 && Math.abs(px) < 4) px = dx > 0 ? 5 : -5;
    let py = Math.round((dy - Math.sign(dy) * Math.min(4, Math.abs(dy) / 6)) / Z);
    if (dy !== 0 && Math.abs(py) < 4) py = dy > 0 ? 5 : -5;
    if (px === 0 && py === 0) { py = 5; }
    const 落 = await 扫落点(id);
    if (!落.length) return { ok: false, 原因: '找不到落点' };
    await 逐帧拖(id, 落[0], px).then((r) => { if (!r.轨迹) throw 0; });
    if (py) { const 落2 = await 扫落点(id); if (落2.length) await 逐帧拖(id, 落2[0], 0); }
    记(`   复原轮${轮}：${JSON.stringify(s.画布)} → 拖 ${px},${py}px → ${JSON.stringify((await 读(id)).画布)}`);
  }
  return { ok: false, 原因: '轮数用完' };
};

try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(12000);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(4000);
  Z = await 读zoom();
  记(`zoom = ${Z}｜1 屏px = ${(1 / Z).toFixed(4)} 画布单位`);

  // ① 自动挑节点
  记('—— ① 挑「框内有干净落点」的节点 ——');
  const 候选 = ['v-oZNpH99MtM', 'n-56F19pXVB4', 'b-mfkcQNULC3', 'a-THmbuJXQj4'];
  const 好节点 = [];
  for (const id of 候选) {
    const 落 = await 扫落点(id);
    记(`   ${id} 干净落点 ${落.length}/36 个`);
    if (落.length >= 3) 好节点.push([id, 落]);
  }
  if (!好节点.length) throw new Error('没有可拖的节点');
  记(`   ⭐ 选中 ${好节点.map((x) => x[0]).join('、')}`);

  // ② 三档开关态逐帧 A/B
  const g0 = await 开关();
  R.读数.开关关 = g0;
  记(`—— ② 三档开关态 A/B（初始 svg 数 ${g0.svg数}）——`);
  for (const [id, 落] of 好节点.slice(0, 2)) {
    记(`—— 节点 ${id}（基线 ${JSON.stringify(坐标[id])}）——`);
    const 对照 = {};
    for (const 态 of ['关', '开', '关2']) {
      if (态 === '开') {
        const g1 = await 点开关();
        记(`   ⭐ 点开关：svg 数 ${g0.svg数} → ${g1.svg数}｜外链变了？ ${g1.外链 !== g0.外链}`);
        R.读数.开关开 = g1;
      }
      if (态 === '关2') {
        await 点开关();
        const g2 = await 开关();
        记(`   ⭐ 点回开关：svg 数 ${g2.svg数}｜与初始外链一致？ ${g2.外链 === g0.外链}`);
        R.读数.开关回 = g2;
      }
      const 当前 = await 开关();
      const 落新 = 落.length ? (await 扫落点(id)) : [];
      if (!落新.length) { 记(`   【${态}】⛔ 落点用尽`); break; }
      const 起 = (await 读(id)).画布[0];
      const 自由 = 起 + 13 / Z;
      const 预测 = (Math.abs(自由) > Math.abs(起) ? Math.ceil(自由 / 12) : Math.floor(自由 / 12)) * 12;
      const a = await 逐帧拖(id, 落新[0], 13);
      const 落点1 = (await 读(id)).画布[0];
      const 落b = (await 扫落点(id))[0];
      if (落b) await 逐帧拖(id, 落b, -13);
      const 止 = (await 读(id)).画布[0];
      记(`   【${态}】svg 数 ${当前.svg数}｜起 ${起}`);
      记(`      轨迹 ${JSON.stringify(a.轨迹)}`);
      记(`      落点 ${落点1}｜预测 ${预测}｜命中？ ${落点1 === 预测}｜是 12 倍数？ ${落点1 % 12 === 0}｜位移 ${(落点1 - 起).toFixed(2)}（自由值 ${(13 / Z).toFixed(2)}）`);
      记(`      往返净位移 ${(止 - 起).toFixed(4)}`);
      对照[态] = { 轨迹: a.轨迹, 落点: 落点1, 预测, 净: Number((止 - 起).toFixed(4)) };
    }
    R.读数['节点_' + id] = 对照;
    if (对照['关'] && 对照['开']) {
      记(`   ⭐⭐⭐⭐ ${id}：关态落点 ${对照['关'].落点}｜开态落点 ${对照['开'].落点}｜**相同？ ${对照['关'].落点 === 对照['开'].落点}**`);
      记(`      逐帧轨迹完全相同？ ${JSON.stringify(对照['关'].轨迹) === JSON.stringify(对照['开'].轨迹)}`);
    }
    const r = await 闭环复原(id);
    记(`   ${id} 复原：${JSON.stringify(r)}`);
  }
  await page.screenshot({ path: EVID + 'fc2-01-测完整屏.png' });
} catch (e) {
  R.错误 = String((e && e.stack) || e);
  记('❌ ' + e.message);
} finally {
  const g = await 开关();
  if (g && g.svg数 >= 2) {
    await page.mouse.move(g.中心[0], g.中心[1]); await page.waitForTimeout(350);
    await page.mouse.down(); await page.mouse.up(); await page.waitForTimeout(900);
    await page.mouse.move(720, 170); await page.waitForTimeout(500);
    记(`finally：开关复原 → svg 数 ${(await 开关()).svg数}`);
  }
  for (const id of Object.keys(坐标)) {
    const s = await 读(id);
    if (s && s.画布 && Math.hypot(s.画布[0] - 坐标[id][0], s.画布[1] - 坐标[id][1]) > 0.5) {
      记(`finally：${id} 偏离基线 ${JSON.stringify(s.画布)}，做闭环复原`);
      await 闭环复原(id);
    }
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
  console.log('\n=== 已写 tools/batchFC2.json ===');
}

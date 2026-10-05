// ⭐⭐⭐⭐⭐ Batch FE-1：开态到底是「完全不吸附」还是「换了一个更细的格距」？
//
// FC-2 的结论是「关 = 吸附（落点都是 12 的倍数）、开 = 不吸附（落点 −47701.2 不是）」。
// ⛔ 但那只拖了 **13 屏 px**（8 帧）。**量对一个数 ≠ 答对一个问题**：
//    「落点不是 12 的倍数」并不能排除「它在吸附到 4 格 / 1 格 / 0.5 格」。
//    FC 用的判据是「终点不是 12 的倍数」—— 终点一个点，说服力有限。
//
// ⭐⭐⭐ 这轮改用**相邻帧差值序列**来判：
//   · 关态：Δ 只能是 0 或 ±12（阶梯）。出现 12 就叫**阳性对照**——
//     没看到 12 就说明采样太粗 / 落点不干净，判据不成立，必须报出来而不是硬下结论。
//   · 开态：Δ 应恒等于「这一帧鼠标走了多少画布单位」。
//     若「完全不吸附」⇒ 每个 Δ 都贴着理论值（浮点误差量级）；
//     若「换了个更细的格距 g」⇒ Δ 会在理论值上出现**周期性尖峰**（跳格的那几帧偏得多）。
//
// ⭐ 两段采样密度不同，用来探不同量级的 g：
//   粗扫：每帧 2 屏 px（≈4.14 画布单位）拖 200 屏 px ⇒ 能探 g ≳ 4
//   细扫：每帧 0.5 屏 px（≈1.04 画布单位）拖 20 屏 px ⇒ 能探 g ≳ 1
//
// ⛔ 安全：全程**往返法**（+D 再 −D，净位移 0）；finally 里按基线闭环复原；
//   开关的初始态在 try 之前读，finally 里**无条件点回**。
// ⛔ 从来不用 git stash。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = HERE + '.evidence/';
const R = { 步骤: [], 读数: {} };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFE1.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };

const ID = 'v-oZNpH99MtM'; // 智能剪辑：FC-1 实测框内 36/36 落点无 nodrag 祖先，最干净
let Z = 0.48;
// ⛔ try 之前算好，finally 才拿得到
let 开关初始 = null;
let 已拖动 = false;

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
/** 框内 6×6 扫格，返回「属主对 且 无 nodrag 祖先」的落点 */
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
/** ⭐ 逐帧拖：每帧步长 stepPx 屏像素，帧间隔 170ms。返回逐帧画布 x */
const 逐帧拖 = async (id, p, 总dx, 帧数) => {
  const 起 = (await 读(id)).画布;
  const 轨迹 = [];
  await page.mouse.move(p.x, p.y); await page.waitForTimeout(300);
  await page.mouse.down(); await page.waitForTimeout(160);
  for (let i = 1; i <= 帧数; i++) {
    await page.mouse.move(Math.round(p.x + (总dx * i) / 帧数), p.y);
    await page.waitForTimeout(170);
    轨迹.push((await 读(id)).画布[0]);
  }
  await page.mouse.up(); await page.waitForTimeout(620);
  await page.mouse.move(720, 170); await page.waitForTimeout(240);
  已拖动 = true;
  return { 轨迹, 起, 后: (await 读(id)).画布[0], 落点: p };
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
  return { svg数: b.querySelectorAll('svg').length, 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)] };
});
const 点开关 = async () => {
  const g = await 开关();
  await page.mouse.move(g.中心[0], g.中心[1]); await page.waitForTimeout(350);
  await page.mouse.down(); await page.mouse.up(); await page.waitForTimeout(900);
  await page.mouse.move(720, 170); await page.waitForTimeout(500);
  return 开关();
};

/** ⭐ 闭环复原：按 12 格距换算像素，每轮重找落点，符号乘 Math.sign */
const 闭环复原 = async (id) => {
  for (let 轮 = 1; 轮 <= 16; 轮++) {
    const s = await 读(id);
    if (!s || !s.画布) return { ok: false, 原因: '节点读不到' };
    const dx = 坐标[id][0] - s.画布[0], dy = 坐标[id][1] - s.画布[1];
    if (Math.hypot(dx, dy) < 0.5) return { ok: true, 轮, 终: s.画布 };
    let px = Math.round((dx - Math.sign(dx) * Math.min(4, Math.abs(dx) / 6)) / Z);
    if (dx !== 0 && Math.abs(px) < 4) px = dx > 0 ? 5 : -5;
    let py = Math.round((dy - Math.sign(dy) * Math.min(4, Math.abs(dy) / 6)) / Z);
    if (dy !== 0 && Math.abs(py) < 4) py = dy > 0 ? 5 : -5;
    if (px === 0 && py === 0) py = 5;
    const 落 = await 扫落点(id);
    if (!落.length) return { ok: false, 原因: '找不到落点', 当前: s.画布 };
    await 逐帧拖(id, 落[0], px, Math.max(2, Math.round(Math.abs(px) / 2)));
    记(`   复原轮${轮}：${JSON.stringify(s.画布)} → 拖 ${px},${py}px → ${JSON.stringify((await 读(id)).画布)}`);
    if (py) { const l2 = await 扫落点(id); if (l2.length) await 逐帧拖(id, l2[0], 0, 2); }
  }
  return { ok: false, 原因: '轮数用完' };
};

/** ⭐ 一段采样：拖 总dx，记逐帧 Δ，返回统计 */
const 采样 = async (名, 总dx, 帧数) => {
  const 落 = await 扫落点(ID);
  if (!落.length) return { 名, 失败: '框内无干净落点' };
  const p = 落[Math.floor(落.length / 2)];
  const r = await 逐帧拖(ID, p, 总dx, 帧数);
  const 步长单位 = Math.abs(总dx) / 帧数 / Z;
  const d = [];
  let prev = r.起[0];
  for (const v of r.轨迹) { d.push(Number((v - prev).toFixed(4))); prev = v; }
  const 非零 = d.filter((x) => Math.abs(x) > 0.01);
  // ⭐ 逐个 Δ 跟理论值比：|Δ - 理论| 的最大值，就是「有没有跳格」的证据
  const 偏差 = 非零.map((x) => Math.abs(Math.abs(x) - 步长单位));
  return {
    名, 落点: p, 总dx, 帧数, 理论步长单位: Number(步长单位.toFixed(4)),
    起点: r.起[0], 终点: r.后, 净位移: Number((r.后 - r.起[0]).toFixed(4)),
    轨迹: r.轨迹, Δ序列: d,
    非零Δ个数: 非零.length,
    绝对值集合: [...new Set(非零.map((x) => Number(Math.abs(x).toFixed(3))))].sort((a, b) => a - b).slice(0, 24),
    最大偏差: Number(Math.max(0, ...偏差).toFixed(4)),
    中位偏差: Number(偏差.slice().sort((a, b) => a - b)[Math.floor(偏差.length / 2)]?.toFixed?.(4) || 0),
  };
};

try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(12000);
  const 关浮层 = await closePromos(page);
  记(`closePromos：${JSON.stringify(关浮层).slice(0, 300)}`);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(4000);
  Z = await 读zoom();
  记(`zoom = ${Z}｜1 屏px = ${(1 / Z).toFixed(4)} 画布单位｜节点 ${ID} 基线 ${JSON.stringify(坐标[ID])}`);

  const 开关0 = await 开关();
  开关初始 = 开关0?.svg数 ?? 1;
  记(`开关初始 svg 数 = ${开关初始}（1 = 关/吸附态，2 = 开/斜杠态）`);

  const 结果 = {};

  // ——— 关态（默认，吸附）——— 两段采样
  记('—— ① 关态：粗扫 200 屏px / 100 帧 × 2px ——');
  const c1 = await 采样('关-粗', 200, 100);
  记(`   理论步长 ${c1.理论步长单位}｜净位移 ${c1.净位移}｜绝对值集合 ${JSON.stringify(c1.绝对值集合)}｜最大偏差 ${c1.最大偏差}`);
  const l1 = await 扫落点(ID); const b1 = await 逐帧拖(ID, l1[Math.floor(l1.length / 2)], -200, 100);
  记(`   往返回程净位移 ${Number((b1.后 - c1.后).toFixed(4))}`);

  记('—— ② 关态：细扫 20 屏px / 40 帧 × 0.5px ——');
  const c2 = await 采样('关-细', 20, 40);
  记(`   理论步长 ${c2.理论步长单位}｜净位移 ${c2.净位移}｜绝对值集合 ${JSON.stringify(c2.绝对值集合)}｜最大偏差 ${c2.最大偏差}`);
  const l2 = await 扫落点(ID); const b2 = await 逐帧拖(ID, l2[Math.floor(l2.length / 2)], -20, 40);
  记(`   往返回程净位移 ${Number((b2.后 - c2.后).toFixed(4))}`);

  // ——— 开态（点一下开关）———
  const 开后 = await 点开关();
  记(`点开关后 svg 数 = ${开后?.svg数}`);
  记('—— ③ 开态：粗扫 200 屏px / 100 帧 × 2px ——');
  const c3 = await 采样('开-粗', 200, 100);
  记(`   理论步长 ${c3.理论步长单位}｜净位移 ${c3.净位移}｜绝对值集合 ${JSON.stringify(c3.绝对值集合)}｜最大偏差 ${c3.最大偏差}`);
  const l3 = await 扫落点(ID); const b3 = await 逐帧拖(ID, l3[Math.floor(l3.length / 2)], -200, 100);
  记(`   往返回程净位移 ${Number((b3.后 - c3.后).toFixed(4))}`);

  记('—— ④ 开态：细扫 20 屏px / 40 帧 × 0.5px ——');
  const c4 = await 采样('开-细', 20, 40);
  记(`   理论步长 ${c4.理论步长单位}｜净位移 ${c4.净位移}｜绝对值集合 ${JSON.stringify(c4.绝对值集合)}｜最大偏差 ${c4.最大偏差}`);
  const l4 = await 扫落点(ID); const b4 = await 逐帧拖(ID, l4[Math.floor(l4.length / 2)], -20, 40);
  记(`   往返回程净位移 ${Number((b4.后 - c4.后).toFixed(4))}`);

  结果.关 = { 粗: c1, 细: c2 };
  结果.开 = { 粗: c3, 细: c4 };
  R.读数 = { zoom: Z, 开关初始, ...结果 };

  await page.screenshot({ path: EVID + 'fe1-01-收尾.png' });
  记('⛔ 收尾截图 fe1-01');
} catch (e) {
  记('❌ 出错：' + (e && e.message ? e.message : String(e)));
} finally {
  // ⭐ 先复原，再无条件点回开关，最后关浏览器
  try {
    if (已拖动) {
      const rec = await 闭环复原(ID);
      记('finally 复原：' + JSON.stringify(rec));
    } else 记('finally：没拖过，无需复原');
    const s = await 开关();
    if (s && s.svg数 !== 开关初始) {
      const back = await 点开关();
      记(`finally 点回开关：svg ${s.svg数} → ${back?.svg数}（目标 ${开关初始}）`);
    } else 记(`finally：开关已是目标态 svg=${s?.svg数}`);
  } catch (e) { 记('finally 出错：' + (e && e.message ? e.message : String(e))); }
  try { await page.waitForTimeout(15000); } catch (e) { /* 静置 */ }
  try {
    // ⛔ 不用 canvas-baseline 的 读全部坐标：它用 querySelectorAll，
    //   **框选 / 拖动状态下会漏读**（FD-4 只读到 4/11）。这里逐个 data-id 读。
    const 核 = await page.evaluate((基线) => Object.entries(基线).map(([id, [bx, by]]) => {
      const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
      if (!n) return { id, 现: null, 偏: '节点不在 DOM 里' };
      const t = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
      if (!t) return { id, 现: null, 偏: '读不到 transform' };
      const x = parseFloat(t[1]), y = parseFloat(t[2]);
      return Math.hypot(x - bx, y - by) > 1.5 ? { id, 基线: [bx, by], 现: [x, y], 偏: Number(Math.hypot(x - bx, y - by).toFixed(2)) } : null;
    }).filter(Boolean), 坐标);
    记('⭐ 静置 15s 后核对坐标：' + JSON.stringify(核));
  } catch (e) { 记('核对失败：' + e); }
  try { await 浏览器.browser.close(); } catch (e) { /* 关 */ }
  记('done');
}

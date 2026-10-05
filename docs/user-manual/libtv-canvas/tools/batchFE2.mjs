// ⭐⭐⭐⭐⭐ Batch FE-2：「12 格」是**绝对栅格**还是**相对位移的量化**？
//
// FE-1 已经拿到两组决定性读数（见 batchFE1.json）：
//   · 关态 40 帧走完 41.4 画布单位，只出现 **4 个**坐标（−60276 / −60264 / −60250 / −60240）
//   · 开态 同样 40 帧，出现 **40 个**互不相同的坐标（−60276 / −60273.9 / −60271.9 …）
//   ⇒ 关态栅格 = 12 画布单位；开态 = **完全不吸附**（不是「换了个更细的格距」）。
//
// ⛔ 但 FE-1 还没排除一种解释：**12 也许不是「绝对坐标的栅格」，
//    而只是「相对拖拽起点的位移被量化成 12 的倍数」**。
//    这两种解释在「起点恰好是 12 的倍数」时**完全等价**，分不开。
//
// ⭐⭐⭐ 本轮用一步分掉它们：
//   ① 开态下把节点挪到**不在 12 栅格上**的位置（终点带小数）；
//   ② 切回关态，**先原地不动**读一次坐标（确认它就停在那儿，没被偷偷吸附）；
//   ③ 关态下只走**一帧**（2 屏 px ≈ 4.14 画布单位），再读一次。
//   · 若是**绝对栅格** ⇒ 落点必是 12 的倍数（−60277 → −60264，跳 13 而不是 4.14）。
//   · 若是**相对量化** ⇒ 落点 = 起点 + round(4.14/12)*12 = 起点 + 0 = 原地不动。
//   两个预测**互斥**，一次实验就能分开。
//
// ⭐ 顺带测一件手册从没写过的事：**开态能不能把节点停在带小数的坐标上**（关态行不行？）。
// ⛔ 安全：往返法 + finally 里按基线闭环复原 + 无条件点回开关。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const R = { 步骤: [], 读数: {} };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFE2.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };

const ID = 'v-oZNpH99MtM';
let Z = 0.48;
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
  return { svg数: b.querySelectorAll('svg').length, 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)] };
});
const 点开关 = async () => {
  const g = await 开关();
  await page.mouse.move(g.中心[0], g.中心[1]); await page.waitForTimeout(350);
  await page.mouse.down(); await page.mouse.up(); await page.waitForTimeout(900);
  await page.mouse.move(720, 170); await page.waitForTimeout(500);
  return 开关();
};
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
    记(`   复原轮${轮}：${JSON.stringify(s.画布)} → ${JSON.stringify((await 读(id)).画布)}`);
  }
  return { ok: false, 原因: '轮数用完' };
};
/** 只走一帧：用来测「第一帧落到哪」 */
const 走一帧 = async (id, p, dx) => {
  await page.mouse.move(p.x, p.y); await page.waitForTimeout(300);
  await page.mouse.down(); await page.waitForTimeout(160);
  await page.mouse.move(Math.round(p.x + dx), p.y);
  await page.waitForTimeout(260);
  const 中途 = (await 读(id)).画布[0];
  await page.mouse.up(); await page.waitForTimeout(620);
  await page.mouse.move(720, 170); await page.waitForTimeout(240);
  已拖动 = true;
  return { 中途, 后: (await 读(id)).画布[0] };
};

try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(12000);
  记('closePromos：' + JSON.stringify(await closePromos(page)).slice(0, 200));
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(4000);
  Z = await 读zoom();
  const s0 = await 开关(); 开关初始 = s0?.svg数 ?? 1;
  const 起 = (await 读(ID)).画布;
  记(`zoom=${Z}｜1屏px=${(1 / Z).toFixed(4)} 画布单位｜${ID} 起点 ${JSON.stringify(起)}（${起[0] % 12} mod 12）｜开关 svg=${开关初始}`);

  const 读数 = { 起点: 起 };

  // ① 开态：慢慢挪 3 帧 × 2px = 6px ≈ 12.43 单位 ⇒ 落到不在 12 栅格上的位置
  记('—— ① 点开关到开态 ——');
  const 开 = await 点开关(); 记(`   svg ${开关初始} → ${开?.svg数}`);
  let 落 = await 扫落点(ID);
  const r1 = await 逐帧拖(ID, 落[Math.floor(落.length / 2)], 6, 3);
  const 偏位 = r1.后;
  读数.开态挪后 = { 坐标: 偏位, mod12: Number((偏位[0] % 12).toFixed(3)), 理论位移: Number((6 * (1 / Z)).toFixed(3)), 实际位移: Number((偏位[0] - 起[0]).toFixed(3)) };
  记(`   开态拖 6 屏px（理论 ${(6 / Z).toFixed(3)} 单位）→ ${JSON.stringify(偏位)}，mod 12 = ${(偏位[0] % 12).toFixed(3)}`);

  // ② 切回关态，**原地不动**读一次：确认它不会自己跳到栅格上
  记('—— ② 点回关态，原地读 ——');
  const 关 = await 点开关(); 记(`   svg → ${关?.svg数}`);
  await page.waitForTimeout(1200);
  const 静置 = (await 读(ID)).画布;
  读数.切回关态后静置 = { 坐标: 静置, mod12: Number((静置[0] % 12).toFixed(3)), 与开态落点差: Number((静置[0] - 偏位[0]).toFixed(4)) };
  记(`   切回关态后静置坐标 ${JSON.stringify(静置)}，mod 12 = ${(静置[0] % 12).toFixed(3)}，与开态落点差 ${(静置[0] - 偏位[0]).toFixed(4)}`);

  // ③ 关态下只走一帧（2 屏px ≈ 4.14 单位）
  落 = await 扫落点(ID);
  const r2 = await 走一帧(ID, 落[Math.floor(落.length / 2)], 2);
  读数.关态一帧 = { 拖动中: r2.中途, 松手后: r2.后, 理论位移: Number((2 / Z).toFixed(3)), 实际位移: Number((r2.中途 - 静置[0]).toFixed(3)), mod12: Number((r2.中途 % 12).toFixed(3)) };
  记(`   关态走一帧 2 屏px（理论 ${(2 / Z).toFixed(3)} 单位）→ ${JSON.stringify(r2.中途)}，mod 12 = ${(r2.中途 % 12).toFixed(3)}`);

  // ④ 再走一帧，看它是在新栅格上还是回到旧栅格
  落 = await 扫落点(ID);
  const r3 = await 走一帧(ID, 落[Math.floor(落.length / 2)], 2);
  读数.关态二帧 = { 拖动中: r3.中途, 实际位移: Number((r3.中途 - r2.中途).toFixed(3)), mod12: Number((r3.中途 % 12).toFixed(3)) };
  记(`   关态第二帧 → ${JSON.stringify(r3.中途)}，mod 12 = ${(r3.中途 % 12).toFixed(3)}`);

  // ⑤ 判据：绝对栅格预测 vs 相对量化预测
  const 是12 = (v) => Math.abs(v % 12) < 0.02 || Math.abs((v % 12) - 12) < 0.02;
  读数.判据 = {
    开态落点是12的倍数: 是12(偏位[0]),
    切回关态静置后是12的倍数: 是12(静置[0]),
    关态一帧后是12的倍数: 是12(r2.中途),
    关态一帧的实际位移: Number((r2.中途 - 静置[0]).toFixed(3)),
    相对量化预测位移: 0,
    绝对栅格预测位移: Number((Math.round(静置[0] / 12) * 12 - 静置[0]).toFixed(3)),
  };
  记('—— 判据 ——');
  记('   ' + JSON.stringify(读数.判据));
  R.读数 = { zoom: Z, 开关初始, ...读数 };
} catch (e) {
  记('❌ 出错：' + (e && e.message ? e.message : String(e)));
} finally {
  try {
    if (已拖动) 记('finally 复原：' + JSON.stringify(await 闭环复原(ID)));
    else 记('finally：没拖过');
    const s = await 开关();
    if (s && s.svg数 !== 开关初始) {
      const b = await 点开关();
      记(`finally 点回开关 svg ${s.svg数} → ${b?.svg数}（目标 ${开关初始}）`);
    } else 记(`finally 开关已是 svg=${s?.svg数}`);
  } catch (e) { 记('finally 出错：' + (e && e.message ? e.message : String(e))); }
  try { await page.waitForTimeout(15000); } catch (e) { /* 静置 */ }
  try {
    const 核 = await page.evaluate((基线) => Object.entries(基线).map(([id, [bx, by]]) => {
      const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
      if (!n) return { id, 现: null, 偏: '不在 DOM' };
      const t = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
      if (!t) return { id, 现: null, 偏: '无 transform' };
      const x = parseFloat(t[1]), y = parseFloat(t[2]);
      return Math.hypot(x - bx, y - by) > 1.5 ? { id, 基线: [bx, by], 现: [x, y], 偏: Number(Math.hypot(x - bx, y - by).toFixed(2)) } : null;
    }).filter(Boolean), 坐标);
    记('⭐ 静置 15s 后核对坐标：' + JSON.stringify(核));
  } catch (e) { 记('核对失败：' + e); }
  try { await 浏览器.browser.close(); } catch (e) { /* 关 */ }
  记('done');
}

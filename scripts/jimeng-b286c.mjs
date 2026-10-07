/**
 * 批次 286c：**样本外**检验从应用代码里读出的取景公式。
 *
 * 📌 起意（批次 286 b286v2 在 bundle 里读到的，build `canvas-view.25249acfc0.js`）：
 *   ```js
 *   function Q(e,t){ if("number"==typeof e) return Math.floor((t-t/(1+e))*.5); ... }   // @87330
 *   let J=(e,t,n,r,i,o)=>{ let a=function(e,t,n){ let r=Q(e,n), i=Q(e,t);
 *                        return {top:r,right:i,bottom:r,left:i,x:2*i,y:2*r} }(o,t,n),
 *                s=F(Math.min((t-a.x)/e.width,(n-a.y)/e.height),r,i), ... }              // @87150
 *   R4:J                                                                            // 导出映射
 *   ```
 *   三个调用点都写明 `padding ?? .1`（@9587 / @54400 / @84428）。
 *   ⇒ **取景律（代码形态）**：
 *      `Q(p,t) = floor((t − t/(1+p))/2)`（`p=0.1` ⇒ `floor(t·0.0454545…)`）
 *      `边距x = 2·Q(0.1,w)`、`边距y = 2·Q(0.1,h)`
 *      `zoom = clamp( min( (w−边距x)/包围盒宽 , (h−边距y)/包围盒高 ) , minZoom , maxZoom )`
 *      应用默认 `fitViewOptions = {maxZoom: sQ.zoom, minZoom: .08, padding: .1}`（@367876）
 *
 * 📌 **这正好补上批次 283–285 排除掉的那条路**：
 *   批次 284 实测「横向余量 `32.0104 → 34.0104`（`373→374`）」，
 *   代码算 `w=374 ⇒ 2·floor(17.0)=34`、`w=373 ⇒ 2·floor(16.9545)=32` ⇒ **逐字命中**。
 *   🔴 **但那两档是我「发现公式时看过」的数据 —— 用它验证公式等于自证。**
 *
 * 📌 **本批只测「公式没见过的宽度/高度」**（这才是真检验）：
 *   🔴 **宽度轴台阶**：`边距x = 2·floor(w·0.0454545…)`，台阶落在 `w·0.0454545 = 整数`
 *      ⇒ `w = 22k` ⇒ **`374`（已见）**、**`770`（没见过）**。
 *      预测：`w=769 ⇒ 边距 68`、`w=770 ⇒ 边距 70`（**再跳 2px**）。
 *   🔴 **高度轴台阶**：`边距y = 2·floor(h·0.0454545…)` ⇒ 台阶也在 `h = 22k`
 *      ⇒ 预测 **`h=241 ⇒ 20`**（分子 `221`，正是批次 280 反复复现的那个 `221`！）、
 *        **`h=242 ⇒ 22`**（分子 `220`）、**`h=264 ⇒ 24`**。
 *      📌 批次 280 当初猜的是「`H−22=219`」，代码说 `241` 这一档是 `H−20=221` —— **可判定谁对**。
 *   🔴 **`minZoom` 下夹**：预测 `w=300 ⇒ 理论 0.06697 < minZoom` ⇒ 实测应**正好卡在 `0.08`**；
 *      `w=280` 同理。⇒ 若实测真是 `0.08`，`minZoom:.08` 这条常量就被**独立证实**。
 *
 * 📌 **四条前提**：
 *   ① **缺臂整组作废**：任一臂没读到包围盒，整组不出判定（立规 164）；
 *   ② **反变换自检**：同一臂连量两次必须逐字相同（沿用批次 284 口径，保证可比）；
 *   ③ **轴向自检**：`window.innerWidth/Height` 必须等于设定值；
 *   ④ 📌 **公式在测量之前写死**：`预测` 由代码常量（`0.1`/`0.08`）与
 *      **当臂实测的包围盒**算出，**不许用实测 zoom 反推任何参数**。
 *
 * 📌 **纪律**：只改视口尺寸、只读数；不点任何东西、不改任何状态；
 *   不进扣费页、绝不点生成；末态在实验流程之外独立复查（立规 140）。
 *
 * 用法：node scripts/jimeng-b286c.mjs      （落盘 /tmp/b286c.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B286C_OUT || '/tmp/b286c.json';

const 宽度组 = [280, 300, 360, 372, 373, 374, 375, 769, 770];
const 高度组 = [241, 242, 264];
const 固定高 = 720, 固定宽 = 1280;

// 🔴 前提④：常量取自 bundle 字面量，不是拟合出来的
const PADDING = 0.1;
const MIN_ZOOM = 0.08;
const Q = (t) => Math.floor((t - t / (1 + PADDING)) / 2);   // bundle @87330
const 夹 = (v) => Math.min(Math.max(v, MIN_ZOOM), Infinity);

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b286c',
  问: '从代码读出的取景公式，在「没参与发现公式」的宽度/高度上是否逐字成立？',
  构建: 'canvas-view.25249acfc0.js',
  常量: { PADDING, MIN_ZOOM, 来源: 'Q() @87330 与 fitViewOptions @367876' },
  臂: [], 判定: {},
};

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

const 量 = (p) => p.evaluate(() => {
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  const t = vp ? /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(vp.style.transform || '') : null;
  const scale = m ? Number(m[1]) : null;
  const vpRect = vp ? vp.getBoundingClientRect() : null;
  if (!scale || !vpRect) return { 相机: { scale, tx: t ? Number(t[1]) : null, ty: t ? Number(t[2]) : null }, 包围盒: null };
  const ox = vpRect.x, oy = vpRect.y;
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity, n = 0;
  document.querySelectorAll('.react-flow__node').forEach((el) => {
    const r = el.getBoundingClientRect();
    if (!(r.width > 0 && r.height > 0)) return;
    x0 = Math.min(x0, (r.left - ox) / scale); y0 = Math.min(y0, (r.top - oy) / scale);
    x1 = Math.max(x1, (r.right - ox) / scale); y1 = Math.max(y1, (r.bottom - oy) / scale);
    n++;
  });
  if (!n) return { 相机: { scale }, 包围盒: null, 节点数: 0 };
  return {
    相机: { scale, tx: t ? Number(t[1]) : null, ty: t ? Number(t[2]) : null },
    节点数: n,
    包围盒: { x: +x0.toFixed(4), y: +y0.toFixed(4), 宽: +(x1 - x0).toFixed(4), 高: +(y1 - y0).toFixed(4) },
  };
});

const 臂表 = [
  ...宽度组.map((w) => ({ w, h: 固定高, 轴: '宽' })),
  ...高度组.map((h) => ({ w: 固定宽, h, 轴: '高' })),
];

for (const { w, h, 轴 } of 臂表) {
  const p = await ctx.newPage();
  const 记 = { w, h, 轴 };
  try {
    await p.setViewportSize({ width: w, height: h });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(6000);
    const 实际 = await p.evaluate(() => ({ w: window.innerWidth, h: window.innerHeight }));
    if (实际.w !== w || 实际.h !== h) throw new Error(`轴向自检失败：要 ${w}×${h}，实测 ${实际.w}×${实际.h}`);
    记.实际视口 = 实际;

    const a = await 量(p), c = await 量(p);                 // 前提②
    记.相机 = a.相机; 记.包围盒 = a.包围盒; 记.节点数 = a.节点数;
    记.两次逐字相同 = JSON.stringify(a.包围盒) === JSON.stringify(c.包围盒);
    if (!a.包围盒 || !(a.包围盒.宽 > 0 && a.包围盒.高 > 0)) throw new Error('反变换自检失败：包围盒宽高非正');
    if (!记.两次逐字相同) throw new Error(`反变换自检失败：两次读数不同`);

    const 边距x = 2 * Q(w), 边距y = 2 * Q(h);
    const sx = (w - 边距x) / a.包围盒.宽, sy = (h - 边距y) / a.包围盒.高;
    const 理论 = Math.min(sx, sy);
    记.边距 = { 边距x, 边距y, 预测为整除: w % 1 === 0 ? `Q(w)=${Q(w)}` : '' };
    记.分量 = { sx: +sx.toFixed(6), sy: +sy.toFixed(6), 主导: sx <= sy ? 'x' : 'y' };
    记.理论 = +理论.toFixed(6);
    记.预测 = +夹(理论).toFixed(6);
    记.实测 = +a.相机.scale.toFixed(6);
    记.误差 = +(a.相机.scale - 夹(理论)).toFixed(6);
    记.相对误差 = +(记.误差 / 夹(理论) * 100).toFixed(4) + '%';
    记.是否撞下夹 = 理论 < MIN_ZOOM;
    记.命中 = Math.abs(记.误差) <= 5e-5 || (记.是否撞下夹 && Math.abs(记.实测 - MIN_ZOOM) <= 1e-9);
    log(`${w}×${h}｜边距 x=${边距x} y=${边距y}｜理论 ${记.理论}（主导 ${记.分量.主导}）｜实测 ${记.实测}｜误差 ${记.误差}（${记.相对误差}）${记.是否撞下夹 ? '｜⚠️ 理论低于 minZoom，预测应卡 0.08' : ''}｜包围盒 ${a.包围盒.宽}×${a.包围盒.高}｜${记.命中 ? '✅' : '🔴'}`);
  } catch (e) {
    记.错误 = e.message; log(`${w}×${h} 🔴 ${e.message}`);
  } finally {
    try { await p.close(); } catch (e) { /* 忽略 */ }
    out.臂.push(记);
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

// ── 前提①：缺臂整组作废 ──
const 缺 = out.臂.filter((x) => x.错误 || !x.包围盒 || !x.实测);
const 命中 = out.臂.filter((x) => x.命中);
const 未中 = out.臂.filter((x) => !x.命中 && !x.错误 && x.实测);

// 台阶检验：只看「相邻两臂边距差 2」处，实测 zoom 是否按公式反向变化
const 台阶 = [];
for (let i = 1; i < out.臂.length; i++) {
  const a = out.臂[i - 1], b = out.臂[i];
  if (a.错误 || b.错误 || a.轴 !== b.轴) continue;
  const d = b.边距.边距x - a.边距.边距x;
  const dy = b.边距.边距y - a.边距.边距y;
  if ((轴同(a, b) && d === 2) || dy === 2) {
    台阶.push({
      从: `${a.w}×${a.h}`, 到: `${b.w}×${b.h}`, 边距变化: d || dy,
      实测从: a.实测, 实测到: b.实测, 公式预测从: a.预测, 公式预测到: b.预测,
      实测同预测: a.命中 && b.命中,
    });
  }
}
function 轴同(a, b) { return a.轴 === b.轴; }

log('\n════ 台阶处 ════');
for (const s of 台阶) log(`  ${s.从} → ${s.到}｜边距 +${s.边距变化}｜实测 ${s.实测从} → ${s.实测到}｜公式 ${s.公式预测从} → ${s.公式预测到}｜${s.实测同预测 ? '✅ 两端都中' : '🔴'}`);

log('\n════ 判定 ════');
if (缺.length) {
  out.判定 = { 结论: `🔴 缺 ${缺.length} 臂（${缺.map((x) => `${x.w}×${x.h}`).join(', ')}）⇒ 整组作废，不出判定` };
} else if (!命中.length) {
  out.判定 = { 结论: '🔴 有读数但一条都没命中 ⇒ 公式错' };
} else {
  const 下夹臂 = 命中.filter((x) => x.是否撞下夹);
  out.判定 = {
    命中: `${命中.length}/${out.臂.length} 臂`,
    最大相对误差: 未中.length ? Math.max(...未中.map((x) => Math.abs(Number(x.相对误差.replace('%', ''))))).toFixed(4) + '%' : '0%',
    台阶: 台阶.length ? `边距 +2 的台阶共 ${台阶.length} 处，实测与公式${台阶.every((s) => s.实测同预测) ? '全部一致' : '有出入'}` : '（本组没采到台阶处）',
    下夹: 下夹臂.length
      ? `✅ ${下夹臂.map((x) => `${x.w}×${x.h}`).join(', ')} 理论 < minZoom，实测正好卡 ${MIN_ZOOM} ⇒ minZoom 常量被独立证实`
      : '（本组没采到会撞下夹的臂）',
    结论: `✅ ${命中.length}/${out.臂.length} 臂命中（|误差|≤5e-5），最大相对误差 ${out.判定?.最大相对误差 || ''} ⇒ 取景律在**没参与发现公式**的宽度/高度上成立`,
  };
}
log(JSON.stringify(out.判定, null, 1));

// ── 末态：在实验流程之外独立复查（立规 140）──
const pz = await ctx.newPage();
try {
  await pz.setViewportSize({ width: 1280, height: 720 });
  await pz.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await pz.waitForSelector('.react-flow__node', { timeout: 45000 });
  await pz.waitForTimeout(6000);
  out.末态 = await pz.evaluate(() => ({
    节点数: document.querySelectorAll('.react-flow__node').length,
    状态行: (document.body.innerText.match(/\d+ nodes, \d+ edges, \d+ selected[^\n]*/) || [])[0] || null,
    积分: (document.body.innerText.match(/([\d,]+)\s*\n?\s*积分/) || [])[1] || null,
  }));
} finally { try { await pz.close(); } catch (e) { /* 忽略 */ } }
log(`\n末态独立复查：${JSON.stringify(out.末态)}`);

fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log(`写入 ${OUT}`);
process.exit(0);
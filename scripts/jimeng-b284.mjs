/**
 * 批次 284：把「偏移」和「分母」这一对**分开测** —— 直接量画布的内容包围盒。
 *
 * 📌 起意（批次 283 之后必须做的一步）：
 *   批次 271 把宽度项写成 `s = (w − 偏移) / 4091.4`，批次 270 把高度项写成 `s = (H − 22) / 2520.5`。
 *   🔴 **但这一对里只有一个数是观测量。**
 *   宽度轴上，观测到的只有「`w` 每多 `1px`，`s` 多多少」——也就是**斜率**。
 *   由此拟合出的 `(偏移 = 32, 分母 = 4091.4)` 是一整条等价类：
 *   换任何 `W`，都能得到一组自洽的 `(偏移(W), W)`。
 *   📌 **所以「偏移 `32`」不是测出来的，是拟合出来的。**
 *
 * 📌 **本批把缺的第二个观测量补上：内容包围盒本身。**
 *   `s = 可用宽 / 包围盒宽` ⇒ **只要把包围盒宽独立测出来，可用宽就是一个观测量**，
 *   而 `偏移 = w − 可用宽` 于是**第一次是测出来的**。
 *   🔴 **而且这一测还能直接判一件事**：
 *   包围盒宽**在 `w = 374` 处会不会变**？
 *   - 若**不变** ⇒ `可用宽` 在那一步少 `2px`，机制在「可用宽」这一侧；
 *   - 若**变大** ⇒ `可用宽` 照常是 `w − 32`，**是包围盒本身在 `w = 374` 变宽了** ——
 *     那样的话「`2px` 台阶」的机制就变成「某个节点在该宽度下变宽」，**是一个可以继续追的具体东西**。
 *
 * 📌 **怎么量包围盒**（不读应用代码）：
 *   react-flow 的视口是**均匀缩放 + 平移**，所以
 *   `画布坐标 = (屏幕坐标 − 视口原点) / scale`。
 *   对**每个** `.react-flow__node` 的 `getBoundingClientRect()` 反变换后取并集
 *   ⇒ 得到内容包围盒（`x / y / width / height`）。
 *
 * 📌 **预测先写死**（立规 129/130）：
 *   P1 **包围盒宽跨档不变** ⇒ `可用宽 = s × 包围盒宽` 是纯观测量，
 *      偏移在 `373` 是 `32`、在 `374` 是 `34`，**机制在「可用宽」这一侧**。
 *   P2 **包围盒宽在 `373 → 374` 变大**（`≈ +24.6` 画布像素）⇒
 *      **`可用宽` 照常是 `w − 32`，是包围盒本身变宽了** ⇒ 那个 `2px` 有了一个**可继续追的落点**。
 *   🔴 **两个假设的处置完全不同**，所以必须先把包围盒量出来再写任何一句关于机制的句子。
 *
 * 📌 **三条前提**：
 *   ① **轴向自检**：`innerW/innerH` 逐字等于设定值；
 *   ② **反变换自检**：反变换后包围盒的宽高必须是**正数**，且
 *      🔴 **同一档内重复量两次要逐字相同**（否则反变换本身不稳，结论作废）；
 *   ③ 📌 **噪声底对照**：同时测 `1px` 档（`373→374`）与 `3px` 档（`372→375`）。
 *
 * 📌 **纪律**：只读（本批**一个东西都不点**）；每臂开新页；
 *   末态在实验流程之外独立复查（立规 140）。
 *
 * 用法：node scripts/jimeng-b284.mjs      （落盘 /tmp/b284.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B284_OUT || '/tmp/b284.json';
const 高 = 244;
const 宽度组 = [371, 372, 373, 374, 375, 376, 377];

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b284',
  问: '内容包围盒跨档变不变？把「偏移」从拟合值变成观测量。',
  预测: {
    P1: '包围盒宽跨档不变 ⇒ 机制在「可用宽」这一侧',
    P2: '包围盒宽在 373→374 变大 ⇒ 可用宽照常是 w−32，是包围盒本身变宽了',
  },
  高度组高: 高, 宽度组, 臂: [], 收尾: {},
};

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

/** 量相机 + 内容包围盒（反变换），可重复调用以验稳定性 */
const 量 = (p) => p.evaluate(() => {
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  const t = vp ? /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(vp.style.transform || '') : null;
  const scale = m ? Number(m[1]) : null;
  const tx = t ? Number(t[1]) : null;
  const ty = t ? Number(t[2]) : null;
  const vpRect = vp ? vp.getBoundingClientRect() : null;
  if (!scale || !vpRect) return { 相机: { scale, tx, ty }, 包围盒: null };
  // 反变换：画布坐标 = (屏幕坐标 − 视口原点) / scale
  const ox = vpRect.x, oy = vpRect.y;
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity, n = 0;
  document.querySelectorAll('.react-flow__node').forEach((el) => {
    const r = el.getBoundingClientRect();
    if (!(r.width > 0 && r.height > 0)) return;
    const a = (r.left - ox) / scale, bq = (r.top - oy) / scale;
    const c = (r.right - ox) / scale, d = (r.bottom - oy) / scale;
    x0 = Math.min(x0, a); y0 = Math.min(y0, bq);
    x1 = Math.max(x1, c); y1 = Math.max(y1, d);
    n++;
  });
  if (!n) return { 相机: { scale, tx, ty }, 包围盒: null, 节点数: 0 };
  return {
    相机: { scale, tx, ty },
    节点数: n,
    包围盒: {
      x: +x0.toFixed(4), y: +y0.toFixed(4),
      宽: +(x1 - x0).toFixed(4), 高: +(y1 - y0).toFixed(4),
      视口原点: [+ox.toFixed(3), +oy.toFixed(3)],
    },
  };
});

for (const 宽 of 宽度组) {
  const p = await ctx.newPage();
  const 记 = { 宽, 高 };
  try {
    await p.setViewportSize({ width: 宽, height: 高 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(6000);
    const 实际 = await p.evaluate(() => ({ w: window.innerWidth, h: window.innerHeight }));
    if (实际.w !== 宽 || 实际.h !== 高) throw new Error(`轴向自检失败：要 ${宽}×${高}，实测 ${实际.w}×${实际.h}`);
    记.实际视口 = 实际;

    // 前提②：反变换自检 —— 重复量两次要逐字相同
    const a = await 量(p);
    const c = await 量(p);
    记.相机 = a.相机;
    记.包围盒 = a.包围盒;
    记.节点数 = a.节点数;
    记.反变换两次逐字相同 = JSON.stringify(a.包围盒) === JSON.stringify(c.包围盒);
    if (!a.包围盒 || !(a.包围盒.宽 > 0 && a.包围盒.高 > 0)) throw new Error('反变换自检失败：包围盒宽高非正');
    if (!记.反变换两次逐字相同) throw new Error(`反变换自检失败：两次读数不同 ${JSON.stringify(a.包围盒)} vs ${JSON.stringify(c.包围盒)}`);

    // 观测量：可用宽 / 可用高（不再有拟合参数）
    记.可用宽 = +(a.相机.scale * a.包围盒.宽).toFixed(4);
    记.可用高 = +(a.相机.scale * a.包围盒.高).toFixed(4);
    记.横向余量 = +(宽 - 记.可用宽).toFixed(4);      // 每边 (宽−可用宽)/2
    记.纵向余量 = +(高 - 记.可用高).toFixed(4);
    log(`w=${宽}｜scale=${a.相机.scale}｜节点 ${a.节点数}｜包围盒 ${a.包围盒.宽} × ${a.包围盒.高} @ (${a.包围盒.x}, ${a.包围盒.y})｜可用宽 ${记.可用宽} 横向余量 ${记.横向余量}｜可用高 ${记.可用高} 纵向余量 ${记.纵向余量}｜两次逐字相同 ${记.反变换两次逐字相同 ? '✅' : '🔴'}`);
  } catch (e) { 记.错误 = e.message; log(`w=${宽} 🔴 ${e.message}`); }
  finally {
    try { await p.close(); } catch (e) { /* 忽略 */ }
    out.臂.push(记);
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

// ═══ 差分 ═══
if (!out.臂.every((x) => x.包围盒)) throw new Error(`有臂缺读数（${out.臂.filter((x) => !x.包围盒).map((x) => x.宽).join(',')}）⇒ 整组作废，不出判定`);
const 档 = (w) => out.臂.find((x) => x.宽 === w);
out.差分 = {};
for (const [a, c] of [[373, 374], [372, 375], [372, 373], [374, 375]]) {
  const A = 档(a), B = 档(c);
  const d = (k) => +(B[k] - A[k]).toFixed(4);
  out.差分[`${a}→${c}`] = {
    包围盒宽: { 从: A.包围盒.宽, 到: B.包围盒.宽, Δ: d.call ? +(B.包围盒.宽 - A.包围盒.宽).toFixed(4) : null },
    包围盒高: { 从: A.包围盒.高, 到: B.包围盒.高, Δ: +(B.包围盒.高 - A.包围盒.高).toFixed(4) },
    可用宽: { 从: A.可用宽, 到: B.可用宽, Δ: +(B.可用宽 - A.可用宽).toFixed(4) },
    可用高: { 从: A.可用高, 到: B.可用高, Δ: +(B.可用高 - A.可用高).toFixed(4) },
    横向余量: { 从: A.横向余量, 到: B.横向余量, Δ: +(B.横向余量 - A.横向余量).toFixed(4) },
    纵向余量: { 从: A.纵向余量, 到: B.纵向余量, Δ: +(B.纵向余量 - A.纵向余量).toFixed(4) },
    scale: { 从: A.相机.scale, 到: B.相机.scale, Δ: +(B.相机.scale - A.相机.scale).toFixed(7) },
  };
}
log('\n════ 差分 ════');
for (const [k, v] of Object.entries(out.差分)) {
  log(`\n--- ${k} ---`);
  for (const [名, o] of Object.entries(v)) log(`  ${名.padEnd(10)} ${String(o.从).padStart(12)} → ${String(o.到).padEnd(12)} Δ=${o.Δ}`);
}

const 盒宽Δ = out.差分['373→374'].包围盒宽.Δ;
const 可用宽Δ = out.差分['373→374'].可用宽.Δ;
out.判定 = {
  '373→374_包围盒宽Δ': 盒宽Δ,
  '373→374_可用宽Δ': 可用宽Δ,
  包围盒宽各档: Object.fromEntries(out.臂.map((x) => [x.宽, x.包围盒.宽])),
  可用宽各档: Object.fromEntries(out.臂.map((x) => [x.宽, x.可用宽])),
  横向余量各档: Object.fromEntries(out.臂.map((x) => [x.宽, x.横向余量])),
  结论: Math.abs(盒宽Δ) < 0.01
    ? `P1 ✅ 包围盒宽在 373→374 不变（Δ=${盒宽Δ}）⇒ 可用宽 Δ=${可用宽Δ}，机制在「可用宽」这一侧`
    : `P2 ✅ 包围盒宽在 373→374 变了 Δ=${盒宽Δ} ⇒ 可用宽 Δ=${可用宽Δ}；那个 2px 的落点是「包围盒在某个宽度变宽了」，可继续追`,
};
log(`\n════ 判定 ════\n${out.判定.结论}`);
log(`包围盒宽各档：${JSON.stringify(out.判定.包围盒宽各档)}`);
log(`可用宽各档  ：${JSON.stringify(out.判定.可用宽各档)}`);
log(`横向余量各档：${JSON.stringify(out.判定.横向余量各档)}`);

// 末态独立复查（立规 140）
{
  const p = await ctx.newPage();
  try {
    await p.setViewportSize({ width: 1280, height: 720 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(6000);
    out.收尾.节点数 = await p.evaluate(() => document.querySelectorAll('.react-flow__node').length);
    out.收尾.状态行 = await p.evaluate(() => (document.body.innerText.match(/\d+ nodes, \d+ edges, \d+ selected[^\n]*/) || [])[0] || null);
    out.收尾.通过 = out.收尾.节点数 === 76 && /0 selected/.test(out.收尾.状态行 || '');
    log(`\n末态独立复查：节点 ${out.收尾.节点数}｜${out.收尾.状态行} ⇒ ${out.收尾.通过 ? '✅' : '🔴'}`);
  } catch (e) { out.收尾.错误 = e.message; } finally { try { await p.close(); } catch (e) { /* 忽略 */ } }
}

fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log(`\n写入 ${OUT}`);
process.exit(0);
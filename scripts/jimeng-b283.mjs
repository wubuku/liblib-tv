/**
 * 批次 283：`w = 374` 少掉的那 `2px` 到底藏在哪 —— 去查**文档级**的宽度量。
 *
 * 📌 起意（追了 8 个批次的老问题）：
 *   批次 271 钉死：初始自适应的宽度项偏移是 `32`（`w ≤ 373`）/ `34`（`w ≥ 374`），
 *   批次 272 把台阶钉死在 `w = 374`，批次 273/274/275 换了三套量纲，
 *   批次 276 在四个相位上又量了一遍，批次 277 把 `+2` 拆成六步后确认**它不是台阶**（是 `round(w/2)` 的楼层）。
 *   ⇒ **整棵 DOM 里没有任何一个量在 `373 → 374` 变化 `2px`**
 *   （批次 276 已把 `373→374` 的完整变化谱列出来：全部 `+1`，没有 `0→1` / `1→0`）。
 *   ⇒ 📌 **那么这 `2px` 就不在元素盒模型里。**
 *
 * 📌 **还没查过的一层：文档级宽度量。**
 *   `window.innerWidth` / `documentElement.clientWidth` / `body.clientWidth` /
 *   `documentElement.scrollWidth` / **`visualViewport.width`** ——
 *   🔴 **它们和「某个元素的盒子」不是一回事**：
 *   一个**文档级滚动条**会让 `documentElement.clientWidth` 比 `innerWidth` 小，
 *   而这个差值在元素盒上**一个都看不出来**。
 *   ⇒ 这正是批次 154 点名的「换量纲」思路里，**唯一还没换过的那一维**。
 *
 * 📌 **预测先写死**（立规 129/130）：
 *   P1 **某一档文档级宽度量在 `373 → 374` 少 `2`**
 *      ⇒ 那 `2px` 就是它，**机制闭合**（例如某个滚动条在 `w = 374` 恰好出现）。
 *   P2 **所有文档级宽度量都逐字 `+1`**
 *      ⇒ 🔴 **这 `2px` 既不在元素盒模型里、也不在文档级宽度量里**
 *      ⇒ **它在应用的适配计算内部**，**这一层没有 DOM 观测量**
 *      ⇒ 只能写「**已排除两级，剩下的机制需要读应用代码才能测**」，**不编**（立规 113）。
 *
 * 📌 **三条前提**：
 *   ① **轴向自检**：`innerW/innerH` 逐字等于设定值；
 *   ② **`innerWidth` 必须等于设定值**（否则下面的 `Δ` 算的是别的东西）；
 *   ③ 📌 **噪声底对照**（立规 153）：同时扫 `1px` 档（`373→374`）与 `3px` 档（`372→375`）——
 *      **若某一维在 `1px` 档给不出差异、在 `3px` 档却给出 `2`，
 *      那它也是 `round()` 楼层式的假象，不是台阶。**
 *
 * 📌 **纪律**：只读（本批**一个东西都不点**，只开页读数）；每臂开新页；
 *   末态在实验流程之外独立复查（立规 140）。
 *
 * 用法：node scripts/jimeng-b283.mjs      （落盘 /tmp/b283.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B283_OUT || '/tmp/b283.json';
const 高 = 244;
const 宽度组 = [371, 372, 373, 374, 375, 376, 377];
const 分母 = 4091.4;

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b283',
  问: 'w=374 少掉的那 2px 在不在文档级宽度量里？',
  预测: {
    P1: '某一档文档级宽度量在 373→374 少 2 ⇒ 机制闭合',
    P2: '所有文档级宽度量都逐字 +1 ⇒ 它既不在元素盒模型、也不在文档级宽度量里，只能写「需读应用代码才能测」',
  },
  高度组高: 高, 宽度组, 分母, 臂: [], 收尾: {},
};

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

const 读文档量 = () => {
  const de = document.documentElement, bd = document.body;
  const r = (e) => (e ? e.getBoundingClientRect() : null);
  const sc = document.scrollingElement;
  const cs = (e, k) => { try { return getComputedStyle(e)[k]; } catch (_) { return null; } };
  const flow = document.querySelector('.react-flow');
  return {
    innerWidth: window.innerWidth,
    innerHeight: window.innerHeight,
    deClientWidth: de.clientWidth, deOffsetWidth: de.offsetWidth, deScrollWidth: de.scrollWidth,
    deClientHeight: de.clientHeight, deScrollHeight: de.scrollHeight,
    bdClientWidth: bd.clientWidth, bdOffsetWidth: bd.offsetWidth, bdScrollWidth: bd.scrollWidth,
    scClientWidth: sc ? sc.clientWidth : null, scScrollWidth: sc ? sc.scrollWidth : null,
    deRectW: r(de) ? +r(de).width.toFixed(3) : null,
    bdRectW: r(bd) ? +r(bd).width.toFixed(3) : null,
    flowRectW: r(flow) ? +r(flow).width.toFixed(3) : null,
    flowClientW: flow ? flow.clientWidth : null,
    vvWidth: window.visualViewport ? +window.visualViewport.width.toFixed(3) : null,
    htmlOverflowY: cs(de, 'overflowY'), bodyOverflowY: cs(bd, 'overflowY'),
    htmlOverflowX: cs(de, 'overflowX'), bodyOverflowX: cs(bd, 'overflowX'),
    文档有滚动条: de.scrollWidth > de.clientWidth,
  };
};

const 读 = (p) => p.evaluate((读量) => {
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  const t = vp ? /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(vp.style.transform || '') : null;
  return {
    相机: { scale: m ? Number(m[1]) : null, tx: t ? Number(t[1]) : null, ty: t ? Number(t[2]) : null },
    文档: eval(`(${读量})()`),
  };
}, 读文档量.toString());

for (const 宽 of 宽度组) {
  const p = await ctx.newPage();
  const 记 = { 宽, 高 };
  try {
    await p.setViewportSize({ width: 宽, height: 高 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(6000);
    const r = await 读(p);
    // 前提①②
    if (r.文档.innerWidth !== 宽 || r.文档.innerHeight !== 高) throw new Error(`轴向自检失败：要 ${宽}×${高}，实测 ${r.文档.innerWidth}×${r.文档.innerHeight}`);
    记.相机 = r.相机;
    记.文档 = r.文档;
    记.分子 = +(r.相机.scale * 分母).toFixed(4);
    记.偏移 = +(宽 - r.相机.scale * 分母).toFixed(4);
    log(`w=${宽}｜scale=${r.相机.scale} 分子=${记.分子} 偏移=${记.偏移}｜innerW=${r.文档.innerWidth} de.client=${r.文档.deClientWidth} body.client=${r.文档.bdClientWidth} de.scroll=${r.文档.deScrollWidth} vv=${r.文档.vvWidth} flow.client=${r.文档.flowClientW} flow.rect=${r.文档.flowRectW}｜html overflowY=${r.文档.htmlOverflowY}`);
  } catch (e) { 记.错误 = e.message; log(`w=${宽} 🔴 ${e.message}`); }
  finally {
    try { await p.close(); } catch (e) { /* 忽略 */ }
    out.臂.push(记);
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

// ═══ 逐维差分（含噪声底对照）═══
const 维表 = ['innerWidth', 'deClientWidth', 'deOffsetWidth', 'deScrollWidth', 'bdClientWidth', 'bdOffsetWidth', 'bdScrollWidth', 'scClientWidth', 'scScrollWidth', 'deRectW', 'bdRectW', 'flowRectW', 'flowClientW', 'vvWidth'];
out.差分 = {};
for (const [a, c] of [[373, 374], [372, 375], [372, 373], [374, 375]]) {
  const A = out.臂.find((x) => x.宽 === a)?.文档, B = out.臂.find((x) => x.宽 === c)?.文档;
  if (!A || !B) continue;
  const 行 = {};
  for (const k of 维表) {
    const x = A[k], y = B[k];
    if (typeof x !== 'number' || typeof y !== 'number') { 行[k] = { 从: x, 到: y, 差: null }; continue; }
    行[k] = { 从: x, 到: y, 差: +(y - x).toFixed(3) };
  }
  行.__分子 = { 从: out.臂.find((x) => x.宽 === a)?.分子, 到: out.臂.find((x) => x.宽 === c)?.分子, 差: +((out.臂.find((x) => x.宽 === c)?.分子 ?? 0) - (out.臂.find((x) => x.宽 === a)?.分子 ?? 0)).toFixed(4) };
  out.差分[`${a}→${c}`] = 行;
}

log('\n════ 逐维差分 ════');
for (const [k, v] of Object.entries(out.差分)) {
  log(`\n--- ${k} ---`);
  for (const [d, o] of Object.entries(v)) log(`  ${d.padEnd(16)} ${String(o.从).padStart(10)} → ${String(o.到).padEnd(10)} Δ=${o.差}`);
}

// 🔴 前提④（本批 v1 就是死在这里，值得留成硬门）：
//   v1 里七臂**全部报错**（常量名笔误），`out.差分` 是空的，
//   而脚本**照样打印了一句自信的「P2 ✅」** —— 那是**零行数据上的假通过**（立规 142/153）。
//   ⇒ 差分表为空 ⇒ 直接 throw，**不许出判定**。
if (!Object.keys(out.差分).length) throw new Error('差分表为空（各臂读数缺失）⇒ 不许出判定，整组作废');

const 有2的维 = Object.entries(out.差分['373→374'] || {}).filter(([, o]) => o.差 === 2).map(([k]) => k);
const 对照有2的维 = Object.entries(out.差分['372→375'] || {}).filter(([, o]) => o.差 === 2).map(([k]) => k);
out.判定 = {
  目标档_1px_里差2的维: 有2的维,
  对照档_3px_里差2的维: 对照有2的维,
  结论: 有2的维.length
    ? `P1 ✅ ${JSON.stringify(有2的维)} 在 373→374 少 2 ⇒ 这 2px 就是它`
    : 对照有2的维.length
      ? `⚠️ P2 变体：${JSON.stringify(对照有2的维)} 在 3px 对照档里差 2、目标档里不差 ⇒ 又是 round() 楼层式假象，不是台阶`
      : 'P2 ✅ 目标档与对照档里没有任何一维差 2 ⇒ 这 2px 既不在元素盒模型、也不在文档级宽度量里',
};
log(`\n════ 判定 ════\n${out.判定.结论}`);

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
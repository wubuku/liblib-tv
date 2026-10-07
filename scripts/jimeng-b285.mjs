/**
 * 批次 285：量 **CSS 自定义属性**（`--*`）—— 前面每一轮都漏掉了这一整类量。
 *
 * 📌 起意（批次 284 留下的唯一一条可走的路）：
 *   284 把包围盒当观测量反算出来，确认那个 `2px` 落在
 *   「**包围盒之外留给内容的那条边距**」上：每边 `16.0052px` → `17.0052px`，
 *   而 DOM 两级（元素盒模型、文档级宽度）与包围盒本身**全部排除**。
 *   ⚠️ 批次 283 明说「这一层没有 DOM 观测量」—— 🔴 **但那句话下得太早了。**
 *
 * 📌 🔴 **前面每一轮都漏了一整类量：CSS 自定义属性。**
 *   批次 276/277/283 读的样式维度是
 *   `padding / margin / border / gap / left / right` ——
 *   🔴 **这些全是「具体属性」，没有一个是 `--*` 自定义属性**。
 *   而一个 `@media` 断点里改 **`--gutter: 16px` → `17px`** 的写法
 *   （正是很多设计系统的常规做法）**对上面那套量纲是完全隐形的**：
 *   它既不改元素的 `padding`，也不改任何盒子的尺寸。
 *   ⇒ 📌 **这是一条与批次 276「padding 层未测」同型、但更深一层的盲点。**
 *
 * 📌 **怎么把自定义属性读出来**（这一步本身有个坑）：
 *   `getComputedStyle(el).paddingLeft` 读得到具体属性，
 *   但**自定义属性不在具名字段里** —— 要**枚举索引**把名字以 `--` 开头的挑出来。
 *   做法：`for (let i = 0; i < cs.length; i++) { const n = cs[i]; if (n.startsWith('--')) … }`
 *   ⚠️ 这个枚举**顺序不保证稳定** ⇒ 必须**按名字排序后再比较**，否则 diff 全是噪声。
 *
 * 📌 **预测先写死**（立规 129/130）：
 *   P1 **某个元素的某个 `--*` 在 `373 → 374` 变了**（尤其 `16px → 17px` 一类）
 *      ⇒ **机制闭合**：那条边距来自一个 CSS 变量，根因是那个断点。
 *   P2 **一个都没变** ⇒ 🔴 **那条 `32/34` 是 JS 常量或内联算出来的**，
 *      **DOM 这条路到此为止** ⇒ 只剩「读应用代码」，**本批不编**（立规 113）。
 *
 * 📌 **三条前提**：
 *   ① **轴向自检**：`innerW/innerH` 逐字等于设定值；
 *   ② **枚举自检**：每个元素读到的自定义属性**个数必须大于 0**
 *      （全为 `0` ⇒ 枚举法本身失效，**整组作废**，绝不能拿「一个都没变」当结论 ——
 *      这正是立规 164 的空数据假通过）；
 *   ③ 📌 **噪声底对照**：同时跑 `3px` 档（`372→375`）——
 *      **若某一属性只在对照档变、目标档不变，那是噪声不是信号。**
 *
 * 📌 **纪律**：只读（本批**一个东西都不点**）；每臂开新页；
 *   末态在实验流程之外独立复查（立规 140）。
 *
 * 用法：node scripts/jimeng-b285.mjs      （落盘 /tmp/b285.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B285_OUT || '/tmp/b285.json';
const 高 = 244;
const 宽度组 = [372, 373, 374, 375];

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b285',
  问: '那条边距的 16px→17px 是不是一个 CSS 自定义属性在断点处变了？',
  预测: {
    P1: '某个元素的某个 --* 在 373→374 变了 ⇒ 机制闭合',
    P2: '一个都没变 ⇒ 32/34 是 JS 常量或内联算的，DOM 这条路到此为止',
  },
  高度组高: 高, 宽度组, 臂: [], 收尾: {},
};

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

/**
 * 每元素：全部 `--*` 自定义属性（**按名字排序**，因为枚举顺序不保证稳定）。
 * 另外顺带把外框与相机一起读，方便对齐上下文。
 */
const 读一帧 = (p) => p.evaluate(() => {
  const 路径 = (el) => {
    const parts = [];
    let e = el;
    while (e && e.nodeType === 1) {
      const par = e.parentElement;
      let i2 = 1;
      if (par) i2 = Array.from(par.children).filter((c) => c.nodeType === 1 && c.tagName === e.tagName).indexOf(e) + 1;
      parts.unshift(`${e.tagName}:${i2}`);
      e = par;
    }
    return parts.join('>');
  };
  const o = { _变体: {}, _相机: null, _统计: null };
  let 元素数 = 0, 带变量的元素数 = 0, 变量总数 = 0;
  const 全部名字 = new Set();
  document.querySelectorAll('*').forEach((el) => {
    const cs = getComputedStyle(el);
    const 变量 = [];
    for (let i = 0; i < cs.length; i++) {
      const 名 = cs[i];
      if (typeof 名 === 'string' && 名.startsWith('--')) {
        变量.push([名, cs.getPropertyValue(名).trim()]);
        全部名字.add(名);
      }
    }
    if (变量.length) 带变量的元素数++;
    变量总数 += 变量.length;
    o[路径(el)] = 变量.sort((a, b2) => (a[0] < b2[0] ? -1 : a[0] > b2[0] ? 1 : 0)).map(([k, v]) => `${k}=${v}`).join(';');
    元素数++;
  });
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  o._相机 = { scale: m ? Number(m[1]) : null };
  o._统计 = { 元素数, 带变量的元素数, 变量总数, 不同的变量名数: 全部名字.size, 全部变量名: Array.from(全部名字).sort() };
  return o;
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

    const f = await 读一帧(p);
    记.相机 = f._相机;
    记.统计 = f._统计;
    const 快照 = {};
    for (const k of Object.keys(f)) if (!k.startsWith('_')) 快照[k] = f[k];
    记.快照 = 快照;
    记.有变量的元素数 = f._统计.带变量的元素数;
    记.不同的变量名数 = f._统计.不同的变量名数;

    // 前提②：枚举自检 —— 必须真的读到自定义属性，否则整组作废
    if (f._统计.带变量的元素数 === 0 || f._统计.不同的变量名数 === 0) {
      throw new Error(`前提②失败：枚举法读不到任何自定义属性（带变量元素 ${f._统计.带变量的元素数}、变量名 ${f._统计.不同的变量名数}）⇒ 整组作废，绝不能拿「一个都没变」当结论`);
    }
    log(`w=${宽}｜元素 ${f._统计.元素数}｜**带自定义属性的元素 ${f._统计.带变量的元素数}**｜变量出现总次数 ${f._统计.变量总数}｜**不同的变量名 ${f._统计.不同的变量名数}**`);
  } catch (e) { 记.错误 = e.message; log(`w=${宽} 🔴 ${e.message}`); }
  finally {
    try { await p.close(); } catch (e) { /* 忽略 */ }
    out.臂.push(记);
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

// ═══ 差分 ═══
const 有效臂 = out.臂.filter((a) => a.快照 && !a.错误);
if (有效臂.length !== 宽度组.length) throw new Error(`有效臂 ${有效臂.length}/${宽度组.length} ⇒ 整组作废，不出判定`);
const 档 = (w) => 有效臂.find((x) => x.宽 === w);

const 差 = (a, c) => {
  const A = 档(a).快照, B = 档(c).快照;
  const 变了 = [];
  for (const k of new Set([...Object.keys(A), ...Object.keys(B)])) {
    const x = A[k] || '', y = B[k] || '';
    if (x === y) continue;
    const px = new Map((x ? x.split(';').filter(Boolean) : []).map((s) => [s.slice(0, s.indexOf('=')), s.slice(s.indexOf('=') + 1)]));
    const py = new Map((y ? y.split(';').filter(Boolean) : []).map((s) => [s.slice(0, s.indexOf('=')), s.slice(s.indexOf('=') + 1)]));
    const 变 = {};
    for (const [名, 值] of py) if (px.get(名) !== undefined && px.get(名) !== 值) 变[名] = `${px.get(名)} → ${值}`;
    for (const [名, 值] of px) if (!py.has(名)) 变[名] = `${值} → （消失）`;
    if (Object.keys(变).length) 变了.push({ 路径: k, 变 });
  }
  return { 变化元素数: 变了.length, 明细: 变了.slice(0, 60) };
};

out.差分 = {};
for (const [a, c] of [[373, 374], [372, 375], [372, 373], [374, 375]]) out.差分[`${a}→${c}`] = 差(a, c);

log('\n════ 自定义属性差分 ════');
for (const [k, v] of Object.entries(out.差分)) {
  log(`\n--- ${k}：变化元素 ${v.变化元素数} 个 ---`);
  for (const m of v.明细.slice(0, 25)) log(`  ${m.路径.slice(-62)}｜${JSON.stringify(m.变)}`);
}

const 目标 = out.差分['373→374'].变化元素数;
const 对照 = out.差分['372→375'].变化元素数;
out.判定 = {
  各档枚举自检: Object.fromEntries(有效臂.map((a) => [a.宽, { 带变量的元素数: a.有变量的元素数, 不同的变量名数: a.不同的变量名数 }])),
  目标档1px_变化元素数: 目标,
  对照档3px_变化元素数: 对照,
  结论: 目标 > 0
    ? `P1 ✅ 目标档有 ${目标} 个元素的自定义属性变了 ⇒ 去明细里找 16px→17px 一类的`
    : 对照 > 0
      ? `P2 ✅ 目标档 0 个、对照档 ${对照} 个 ⇒ 变化只出现在对照档，**先当噪声**（立规 153），需逐个验`
      : 'P2 ✅ 目标档与对照档都是 0 ⇒ 自定义属性这一层也排除，32/34 只剩 JS 常量或内联计算',
};
log(`\n════ 判定 ════\n${out.判定.结论}`);
log(`各档枚举自检：${JSON.stringify(out.判定.各档枚举自检)}`);

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
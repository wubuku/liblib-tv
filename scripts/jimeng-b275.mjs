/**
 * 批次 275：去量批次 274 **点名但看不见**的那一层 —— `padding` / `margin` / `border` / `gap`。
 *
 * 📌 起意（批次 274 的结论 + 它自己写下的盲点）：
 *   274 把噪声底降到 `0`（`2384` 个元素跨 `5` 帧全稳定），
 *   换来一个**高置信负结论**：`w = 373 → 374` 之间**没有任何元素的外框变化 `2px`**。
 *   🔴 但 274 同时写明了自己的盲点：`offsetWidth` / `clientWidth`
 *   **看不见 `padding` / `margin` / `border` / `gap`** ——
 *   🔴 **一个「只改内边距、不改外框」的变化，对 274 的量纲是完全隐形的。**
 *   ⇒ 「没有 `2px`」只否掉了**盒模型外框**那一层。
 *   📌 立规 154 说「不能说的那一半要点名」—— 本批就是去把那**点名的一半**量出来。
 *
 * 📌 **量什么**（每元素，`getComputedStyle`）：
 *   `paddingLeft/Right/Top/Bottom`、`marginLeft/Right/Top/Bottom`、
 *   `borderLeftWidth/RightWidth/TopWidth/BottomWidth`、
 *   `gap` / `columnGap` / `rowGap`、
 *   以及定位量 `left` / `right`（对 `position ≠ static` 的元素）
 *   —— 🔴 最后这一项是 274 与 273 **都没量过**的：`left`/`right` 变了而外框不变的情况，
 *   在绝对定位元素上完全可能。
 *
 * 📌 **噪声底怎么控**：
 *   ① 同样叠**多帧过滤**（只留跨 `5` 帧逐字相同的元素）；
 *   ② 取值**四舍五入到 `0.01px`**（`getComputedStyle` 的 padding 常是整数，但 `calc()` 会出小数）
 *      ⇒ 小数抖动仍在，但**量级从 `0.13px` 降到 `0.01px`**，与要找的 `2px` 差 `200` 倍；
 *   ③ **对照照跑**（立规 153）：`1px`（`373→374`）与 `3px`（`372→375`）两档都跑，
 *      **若两档规模不再相同，说明量纲换对了**。
 *
 * 📌 **纯只读**：不点任何东西。轴向自检保留（批次 273 的教训）。
 *   不新建/不删除/不上传/不分享/不进扣费页/绝不点生成。末态在实验流程之外独立复查（立规 140）。
 *
 * 用法：node scripts/jimeng-b275.mjs      （落盘 /tmp/b275.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B275_OUT || '/tmp/b275.json';
const 宽度组 = [[372, 244], [373, 244], [374, 244], [375, 244]];   // [宽, 高]
const 帧数 = 5, 帧间隔 = 350;
const 属性 = [
  'paddingLeft', 'paddingRight', 'paddingTop', 'paddingBottom',
  'marginLeft', 'marginRight', 'marginTop', 'marginBottom',
  'borderLeftWidth', 'borderRightWidth', 'borderTopWidth', 'borderBottomWidth',
  'gap', 'columnGap', 'rowGap', 'left', 'right',
];

const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b275', 问: 'padding/margin/border/gap/left/right 层上，w=374 处有没有 2px 变化？', 属性, 宽度组, 快照: {}, 收尾: {} };

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

for (const [宽, 高] of 宽度组) {
  const p = await ctx.newPage();
  const 键 = `${宽}x${高}`;
  try {
    await p.setViewportSize({ width: 宽, height: 高 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(6000);
    const 帧 = [];
    for (let i = 0; i < 帧数; i++) {
      帧.push(await p.evaluate((attrs) => {
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
        const o = {};
        document.querySelectorAll('*').forEach((el) => {
          const cs = getComputedStyle(el);
          o[路径(el)] = attrs.map((a) => {
            const v = parseFloat(cs[a]);
            return Number.isFinite(v) ? +v.toFixed(2) : cs[a];
          }).join(',');
        });
        return o;
      }, 属性));
      await p.waitForTimeout(帧间隔);
    }
    const 实际 = await p.evaluate(() => ({ w: window.innerWidth, h: window.innerHeight }));
    if (实际.w !== 宽 || 实际.h !== 高) throw new Error(`轴向自检失败：要 ${宽}×${高}，实测 ${实际.w}×${实际.h}`);

    const 稳定 = {};
    const 键集 = Object.keys(帧[0]);
    let 不稳定 = 0;
    for (const k of 键集) {
      const v0 = 帧[0][k];
      if (帧.every((f) => f[k] === v0)) 稳定[k] = v0; else 不稳定++;
    }
    out.快照[键] = { 稳定, 元素总数: 键集.length, 不稳定元素数: 不稳定 };
    log(`${键}｜innerW=${实际.w} innerH=${实际.h}｜元素 ${键集.length}，跨 ${帧数} 帧稳定 ${Object.keys(稳定).length}，不稳定 ${不稳定}`);
  } catch (e) {
    out.快照[键] = { 错误: e.message };
    log(`${键} 🔴 ${e.message}`);
  } finally {
    try { await p.close(); } catch (e) { /* 忽略 */ }
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

function diff(a键, b键) {
  const A = out.快照[a键]?.稳定, B = out.快照[b键]?.稳定;
  if (!A || !B) return { 错误: '缺快照' };
  const 变了 = [];
  for (const k of new Set([...Object.keys(A), ...Object.keys(B)])) {
    const a = (A[k] || '').split(','), b = (B[k] || '').split(',');
    if (a.length !== 属性.length || b.length !== 属性.length) continue;
    const d = {};
    属性.forEach((名, i) => { if (b[i] !== a[i]) d[名] = `${a[i]}→${b[i]}`; });
    if (Object.keys(d).length) 变了.push({ 路径: k, 变化: d });
  }
  return { 总变化: 变了.length, 恰为2的: 变了.filter((e) => Object.values(e.变化).some((v) => { const m = /→(-?[\d.]+)$/.exec(v); return m && Math.abs(parseFloat(m[1])) === 2; })).length, 明细: 变了.slice(0, 40) };
}

out.diff_1px_373对374 = diff('373x244', '374x244');
out.diff_3px_372对375 = diff('372x244', '375x244');

const 报 = (名, d) => {
  log(`\n=== ${名}：总变化 ${d.总变化 ?? '—'}，其中**变化量恰为 2** 的 ${d.恰为2的 ?? '—'} 处 ===`);
  for (const m of (d.明细 || []).slice(0, 15)) log(`  ${m.路径.slice(-72)}｜${JSON.stringify(m.变化)}`);
  if (d.错误) log('  ' + d.错误);
};
报('样式 diff：373 → 374（1px，要找的就是它）', out.diff_1px_373对374);
报('样式 diff：372 → 375（3px，纯对照）', out.diff_3px_372对375);

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

out.汇总 = {
  各档稳定元素数: Object.fromEntries(Object.entries(out.快照).map(([k, v]) => [k, v.稳定 ? Object.keys(v.稳定).length : v.错误])),
  diff_1px_总变化: out.diff_1px_373对374.总变化,
  diff_1px_恰为2: out.diff_1px_373对374.恰为2的,
  diff_3px_总变化: out.diff_3px_372对375.总变化,
  diff_3px_恰为2: out.diff_3px_372对375.恰为2的,
  两档是否可分辨: out.diff_1px_373对374.总变化 !== out.diff_3px_372对375.总变化,
};
log('\n=== 汇总 ===');
log(JSON.stringify(out.汇总, null, 1));
fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log(`写入 ${OUT}`);
process.exit(0);

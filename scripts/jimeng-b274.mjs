/**
 * 批次 274：把信噪比提上去再查 `w = 374` 那个 `2px` 台阶 —— 改用**整数布局属性**。
 *
 * 📌 起意（批次 273 的结论是「方法够不着」）：
 *   273 用 `getBoundingClientRect()` 做逐元素 diff，噪声底太大 ——
 *   `1px` 的视口差与 `3px` 的对照差**输出规模完全一样**（都是 `1981` 处），
 *   `Δw` 全在 `≤ 0.13px` 的小数里抖动 ⇒ **浮点矩形量不出 `2px` 的布局变化**。
 *
 * 📌 **本批换量纲，这是立规 136「精度不够先提高信噪比」的直接做法**：
 *   🔴 `offsetWidth` / `clientWidth` / `offsetHeight` / `clientHeight` /
 *      `scrollWidth` / `scrollHeight` / `offsetLeft` / `offsetTop`
 *      **全部是整数**（CSSOM 规定取整）⇒ **亚像素抖动在原理上影响不到它们**
 *      ⇒ **噪声底 ≈ 0**，而信号是 `2px` ⇒ **信噪比从 `< 1` 变成「够用」。
 *   📌 顺带：`offsetLeft/offsetTop` 是**相对 offsetParent 的布局坐标**，
 *      **与相机 transform 无关** ⇒ 画布在动也不影响它们
 *      （这正是 273 那份 diff 被动画淹没的原因之一）。
 *
 * 📌 **对照照旧要跑**（立规 153）：`1px` 差（`373→374`）与 `3px` 差（`372→375`）都跑，
 *   🔴 **若这次两档的 diff 规模不再相同，就说明量纲换对了** ——
 *   这本身就是对「噪声底被降下来了」的一次验证。
 *
 * 📌 **纯只读**：不点任何东西（连取景都不做）—— 判据完全来自布局。
 *   不新建/不删除/不上传/不分享/不进扣费页/绝不点生成。末态在实验流程之外独立复查（立规 140）。
 *
 * 用法：node scripts/jimeng-b274.mjs      （落盘 /tmp/b274.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B274_OUT || '/tmp/b274.json';
const 宽度组 = [[372, 244], [373, 244], [374, 244], [375, 244]];   // [宽, 高]
const 帧数 = 5, 帧间隔 = 350;

const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b274', 问: '用整数布局属性重查：w=374 处到底有没有元素变了 2px？', 宽度组, 快照: {}, 收尾: {} };

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
    // 📌 连采 N 帧，**只保留每帧都逐字相同**的元素（把动画抖掉的那些直接剔掉）
    const 帧 = [];
    for (let i = 0; i < 帧数; i++) {
      帧.push(await p.evaluate(() => {
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
          o[路径(el)] = [el.offsetWidth, el.clientWidth, el.offsetHeight, el.clientHeight,
            el.scrollWidth, el.scrollHeight, el.offsetLeft, el.offsetTop].join(',');
        });
        return o;
      }));
      await p.waitForTimeout(帧间隔);
    }
    // 🔴 **轴向自检**（批次 273 第一版栽在这里，务必保留）
    const 实际 = await p.evaluate(() => ({ w: window.innerWidth, h: window.innerHeight }));
    if (实际.w !== 宽 || 实际.h !== 高) throw new Error(`轴向自检失败：要 ${宽}×${高}，实测 ${实际.w}×${实际.h}`);

    // 只保留所有帧都出现的、且每帧取值完全相同的元素
    const 稳定 = {};
    let 不稳定 = 0;
    const 键集 = Object.keys(帧[0]);
    for (const k of 键集) {
      const v0 = 帧[0][k];
      if (帧.every((f) => f[k] === v0)) 稳定[k] = v0; else 不稳定++;
    }
    out.快照[键] = { 稳定, 元素总数: 键集.length, 不稳定元素数: 不稳定 };
    log(`${键}｜innerW=${实际.w} innerH=${实际.h}｜元素 ${键集.length}，**跨 ${帧数} 帧稳定** ${Object.keys(稳定).length}，不稳定 ${不稳定}`);
  } catch (e) {
    out.快照[键] = { 错误: e.message };
    log(`${键} 🔴 ${e.message}`);
  } finally {
    try { await p.close(); } catch (e) { /* 忽略 */ }
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

const 名 = { ow: 'offsetWidth', cw: 'clientWidth', oh: 'offsetHeight', ch: 'clientHeight', sw: 'scrollWidth', sh: 'scrollHeight', ol: 'offsetLeft', ot: 'offsetTop' };
function diff(a键, b键) {
  const A = out.快照[a键]?.稳定, B = out.快照[b键]?.稳定;
  if (!A || !B) return { 错误: '缺快照' };
  const 变了 = [];
  for (const k of new Set([...Object.keys(A), ...Object.keys(B)])) {
    const a = (A[k] || '').split(','), b = (B[k] || '').split(',');
    if (!a.length || !b.length || a.length !== 8 || b.length !== 8) { 变了.push({ 路径: k, 类型: a.length ? '消失' : '出现' }); continue; }
    const d = {};
    Object.keys(名).forEach((键2, i) => { if (b[i] !== a[i]) d[名[键2]] = b[i] - a[i]; });
    if (Object.keys(d).length) 变了.push({ 路径: k, 变化: d, 后值: b.join(',') });
  }
  const 按幅度 = [...变了].sort((p, q) => {
    const m = (e) => Math.max(...Object.values(e.变化 || { x: 0 }).map(Math.abs));
    return m(q) - m(p);
  });
  return { 总变化: 变了.length, 宽度变了的: 变了.filter((e) => e.变化 && (e.变化.offsetWidth || e.变化.clientWidth || e.变化.scrollWidth)).length, 明细: 按幅度.slice(0, 30) };
}

out.diff_1px_373对374 = diff('373x244', '374x244');
out.diff_3px_372对375 = diff('372x244', '375x244');

const 报 = (名2, d) => {
  log(`\n=== ${名2}：总变化 ${d.总变化 ?? '—'}，其中宽度类变化 ${d.宽度变了的 ?? '—'} ===`);
  for (const m of (d.明细 || []).slice(0, 12)) {
    log(`  ${m.路径.slice(-70)}｜${m.类型 || JSON.stringify(m.变化)}｜后值[${m.后值 || ''}]`);
  }
  if (d.错误) log('  ' + d.错误);
};
报('宽度 diff：373 → 374（1px，要找的就是它）', out.diff_1px_373对374);
报('宽度 diff：372 → 375（3px，纯对照）', out.diff_3px_372对375);

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
  diff_1px_宽度变化: out.diff_1px_373对374.宽度变了的,
  diff_3px_总变化: out.diff_3px_372对375.总变化,
  diff_3px_宽度变化: out.diff_3px_372对375.宽度变了的,
  噪声底是否已降下来: out.diff_1px_373对374.总变化 !== out.diff_3px_372对375.总变化,
};
log('\n=== 汇总 ===');
log(JSON.stringify(out.汇总, null, 1));
fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log(`写入 ${OUT}`);
process.exit(0);

/**
 * 批次 273：去 DOM 里找 `w = 374` 那个**布局开关**，并测它与高度轴那个 `2px` 台阶是否同源。
 *
 * 📌 起意（批次 272 留下的两个未测项）：
 *   ① 宽度轴的台阶**已 1px 钉死在 `w = 374`**，且 `H = 242 / 244 / 246` **逐字相同**
 *      ⇒ 它与视口高度无关，是个**常数**。但「它到底是不是一个响应式断点」**未测**。
 *   ② 高度轴上还有一个**形状相同**的 `2px` 台阶（批次 270：`H ≤ 241` 比直线外推高 `2.00` 个台阶）
 *      ⇒ 两者**是否同源**也**未测**。
 *
 * 📌 **本批的方法：不猜，直接 diff 整棵 DOM。**
 *   对相邻尺寸各取一份「每个元素的稳定路径 → 矩形/滚动尺寸」快照，
 *   然后**逐元素相减** ⇒ 🔴 凡是 `x` 或 `w` 变了约 `2px` 的元素会自己冒出来。
 *   📌 稳定路径用 `tag:nth-of-type(n)` 逐级拼，**不依赖 class 名**
 *   （class 名带哈希、会随构建变，批次 255 已经吃过一次教训）。
 *
 * 📌 **顺带读滚动条信号**：`clientWidth !== offsetWidth` 是「这个盒子有滚动条」的判据 ——
 *   一个 `2px` 的宽度台阶最常见的来源就是**某层布局在某个宽度上多/少让出了 `2px`**。
 *
 * 📌 两组 diff：
 *   **宽度组**：固定 `H = 244`，比 `w = 373` 与 `374`（台阶两侧），再加 `372`/`375` 做邻域对照
 *   **高度组**：固定 `w = 1000`，比 `H = 242` 与 `241`（高度台阶两侧）
 *   ⇒ 📌 若两组 diff **指向同一个元素、同一种属性变化**，就是同源；
 *   **若指向不同元素，就是两回事**。判据互斥，一眼可辨。
 *
 * 📌 **只读**：只读 DOM，不点任何东西（连取景都不做）——
 *   本批的判据完全来自布局，不依赖「取景后相机怎么动」。
 *   不新建/不删除/不上传/不分享/不进扣费页/**绝不点生成**。末态在实验流程之外独立复查（立规 140）。
 *
 * 用法：node scripts/jimeng-b273.mjs      （落盘 /tmp/b273.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B273_OUT || '/tmp/b273.json';
const 宽度组 = [[372, 244], [373, 244], [374, 244], [375, 244]];   // [宽, 高]
const 高度组 = [[1000, 241], [1000, 242]];
const 全部 = [...宽度组, ...高度组];

const log = (...a) => console.log(a.join(' '));

const out = { 轮次: 'b273', 问: 'w=374 那个布局开关是什么？它与高度轴的 2px 台阶同源吗？', 快照: {}, 收尾: {} };
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

for (const [宽, 高] of 全部) {
  const p = await ctx.newPage();
  const 键 = `${宽}x${高}`;
  try {
    await p.setViewportSize({ width: 宽, height: 高 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(6000);
    // 📌 本批不点任何东西：纯布局快照
    const s = await p.evaluate(() => {
      const 路径 = (el) => {
        const parts = [];
        let e = el;
        while (e && e.nodeType === 1) {
          const p = e.parentElement;
          let i = 1;
          if (p) {
            const sibs = Array.from(p.children).filter((c) => c.nodeType === 1 && c.tagName === e.tagName);
            i = sibs.indexOf(e) + 1;
          }
          parts.unshift(`${e.tagName}:nth-of-type(${i})`);
          e = p;
        }
        return parts.join('>');
      };
      const 元素 = {};
      document.querySelectorAll('*').forEach((el) => {
        const r = el.getBoundingClientRect();
        if (r.width < 0.5 && r.height < 0.5) return;
        元素[路径(el)] = {
          tag: el.tagName,
          x: +r.x.toFixed(2), y: +r.y.toFixed(2), w: +r.width.toFixed(2), h: +r.height.toFixed(2),
          cw: el.clientWidth, ow: el.offsetWidth, sw: el.scrollWidth, sh: el.scrollHeight,
          有滚动条: el.clientWidth !== el.offsetWidth,
        };
      });
      const de = document.documentElement;
      return {
        innerW: window.innerWidth, innerH: window.innerHeight,
        html: { clientW: de.clientWidth, offsetW: de.offsetWidth, scrollW: de.scrollWidth, clientH: de.clientHeight, offsetH: de.offsetHeight, scrollH: de.scrollHeight },
        body: { clientW: document.body.clientWidth, offsetW: document.body.offsetWidth, scrollW: document.body.scrollWidth },
        元素数: Object.keys(元素).length,
        元素,
      };
    });
    // 🔴 **轴向自检（本批第一版整批作废就栽在这里，务必保留）**：
    //   第一版把 `宽度组` 写成了 `[[244, 372], …]`，而下面解构的是 `[宽, 高]`
    //   ⇒ 实际在扫**高度**（`innerW=244 / innerH=372`），不是我以为的 `372×244`
    //   ⇒ **整批测反了轴**，而脚本照样输出了「31 处变化、`0` 处 `Δw`」这种看起来很正常的结论。
    //   📌 与立规 152 同型：**「跑一下就有结果」的那一步，先验它测的是不是你要测的轴。**
    if (s.innerW !== 宽 || s.innerH !== 高) {
      throw new Error(`轴向自检失败：要 ${宽}×${高}，实测 innerW=${s.innerW} innerH=${s.innerH} ⇒ 该臂作废`);
    }
    out.快照[键] = s;
    log(`${键}｜innerW=${s.innerW} html.clientW=${s.html.clientW} offsetW=${s.html.offsetW} scrollW=${s.html.scrollW} body.clientW=${s.body.clientW}｜元素 ${s.元素数} 个｜有滚动条的盒子 ${Object.values(s.元素).filter((e) => e.有滚动条).length} 个`);
  } catch (e) {
    out.快照[键] = { 错误: e.message };
    log(`${键} 🔴 ${e.message}`);
  } finally {
    try { await p.close(); } catch (e) { /* 忽略 */ }
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

/** 逐元素 diff：只报真正动了的 */
function diff(a键, b键) {
  const A = out.快照[a键]?.元素, B = out.快照[b键]?.元素;
  if (!A || !B) return { 错误: '缺快照' };
  const 变了 = [];
  for (const k of new Set([...Object.keys(A), ...Object.keys(B)])) {
    const a = A[k], b = B[k];
    if (!a || !b) { 变了.push({ 路径: k, 类型: a ? '消失' : '出现' }); continue; }
    const dw = +(b.w - a.w).toFixed(2), dx = +(b.x - a.x).toFixed(2), dh = +(b.h - a.h).toFixed(2);
    const dcw = b.cw - a.cw;
    if (dw === 0 && dx === 0 && dh === 0 && dcw === 0 && b.有滚动条 === a.有滚动条) continue;
    变了.push({ 路径: k, tag: b.tag, Δw: dw, Δx: dx, Δh: dh, ΔclientW: dcw, 滚动条: `${a.有滚动条}→${b.有滚动条}`, w: b.w, x: b.x });
  }
  变了.sort((p, q) => Math.abs(q.Δw) - Math.abs(p.Δw));
  return { 总变化: 变了.length, 明细: 变了.slice(0, 40) };
}

out.diff_宽度_373对374 = diff('373x244', '374x244');
out.diff_宽度_372对375 = diff('372x244', '375x244');
out.diff_高度_241对242 = diff('1000x241', '1000x242');

const 报 = (名, d) => {
  log(`\n=== ${名}：共 ${d.总变化 ?? '—'} 处变化 ===`);
  for (const m of (d.明细 || []).slice(0, 14)) {
    log(`  ${m.路径}｜${m.Δw !== undefined ? `Δw=${m.Δw} Δx=${m.Δx} Δh=${m.Δh} ΔclientW=${m.ΔclientW} 滚动条=${m.滚动条}` : m.类型}`);
  }
  if (d.错误) log('  ' + d.错误);
};
报('宽度 diff：373 → 374（台阶两侧）', out.diff_宽度_373对374);
报('宽度 diff：372 → 375（邻域对照）', out.diff_宽度_372对375);
报('高度 diff：241 → 242（高度台阶两侧）', out.diff_高度_241对242);

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
  快照数: Object.keys(out.快照).length,
  宽度373对374变化数: out.diff_宽度_373对374.总变化,
  宽度372对375变化数: out.diff_宽度_372对375.总变化,
  高度241对242变化数: out.diff_高度_241对242.总变化,
  宽度侧Δw恰为2的元素: (out.diff_宽度_373对374.明细 || []).filter((m) => Math.abs(Math.abs(m.Δw) - 2) < 0.01).map((m) => m.路径),
};
log('\n=== 汇总 ===');
log(JSON.stringify(out.汇总, null, 1));
fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log(`写入 ${OUT}`);
process.exit(0);

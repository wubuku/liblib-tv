// 会话 mvs_fb62b78 · 批次 210 b 轮：**只变一个变量** —— 读 ty 时用「新开页」还是「复用页」。
//
// 为什么必须做这一轮（立规 79 的正向用法）：
//   a 轮 11 臂在「**一个页签复用 + setViewportSize**」下测出：
//     分支 A（1190/1200/1210）ty = −44.5555 → C = −407.4355   ← 与批次 200 的 −407.435 逐字吻合
//     分支 B（1230~1290）      ty = −156.555  → C = −519.435
//   但批次 200 记的分支 B 是 **C ≈ −508**（1280×720 末帧 ty = −145.169）。
//   ⇒ 两边**差了约 11**，而两边只差一个东西：**批次 200 每档新开页签 + goto，我是一页复用**。
//   在没控制这个变量之前，**任何一句「谁对」都是草率的**。
//
// 本轮：w ∈ {1200, 1280} × 条件 {复用页, 新开页} = 4 臂。
//   1200 预期两边**都**落在分支 A（若一致 ⇒ 说明条件不影响分支 A，问题只在 B）；
//   1280 才是真判据：分支 B 的常数到底跟条件走不走。
import fs from 'node:fs';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const 搜索词 = '音频';
const 目标 = 'canvas-search-result-node_tadm1nyykc';
const H = 720;
const 高度系数 = 0.504;              // 批次 200 拟合出来的 ty ≈ 系数 × 视口高 + C
const 宽度集 = [1200, 1280];
const log = (...a) => console.log(a.join(' '));
const OUT = '/tmp/b210b.json';
const out = { 轮次: 'b210b', 测的量: '取景之后的 vp ty', 唯一自变量: '复用页 vs 新开页', 高度系数, 臂: {} };

/** 完整取景流程：开搜索 → 输入 → 断言目标行在 → 点 → 连采 6 帧。 */
async function 取景(p, 记初值) {
  if (记初值) {
    记初值.初始vp = await p.evaluate(() => {
      const vp = document.querySelector('.react-flow__viewport');
      const m = vp ? /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
      return m ? [Number(m[1]), Number(m[2]), Number(m[3])] : null;
    });
  }
  // 🔴🔴 第一个版本把 Esc 放在**开完搜索面板之后** ⇒ Esc 把面板关掉 ⇒ 4 臂全部「目标行不在」。
  //   这正是批次 200 a 轮 18 臂全废的**同一个错**，而我自己在 a 轮注释里刚写下它。
  //   ⇒ 立规 83：**知道一条教训 ≠ 执行时记得它。纪律必须贴在取点的那一行**，
  //     只写在文件头/方法论页的教训，会在写代码时被"顺手"绕过去。
  await p.keyboard.press('Escape');           // ✅ 清场必须在开面板**之前**
  await p.waitForTimeout(400);
  const 搜索钮 = await p.evaluate(() => {
    const e = document.querySelector('[data-testid="canvas-panel-launcher"][aria-label="搜索"]')
      || Array.from(document.querySelectorAll('button')).find((x) => (x.getAttribute('aria-label') || '') === '搜索');
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
  });
  if (!搜索钮) return { 无效: '找不到搜索钮' };
  await p.mouse.click(搜索钮[0], 搜索钮[1]);
  await p.waitForTimeout(1200);
  await p.evaluate(() => {
    const e = document.querySelector('input[aria-label*="搜索"],input[type="text"]');
    if (e) {
      Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(e, '');
      e.dispatchEvent(new Event('input', { bubbles: true }));
    }
  });
  await p.keyboard.type(搜索词, { delay: 90 });   // 点完结果行之后一个键都不按
  await p.waitForTimeout(2000);

  const 前置 = await p.evaluate((tid) => {
    const e = document.querySelector(`[data-testid="${tid}"]`);
    if (!e) return { 存在: false, 现存前5: Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-node_"]')).slice(0, 5).map((x) => x.getAttribute('data-testid')) };
    const id = tid.replace('canvas-search-result-node_', 'node_');
    const r = e.getBoundingClientRect();
    return { 存在: true, 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
      aria: e.getAttribute('aria-label'),
      总条数: document.querySelectorAll('[data-testid^="canvas-search-result-node_"]').length,
      节点在: !!document.querySelector(`.react-flow__node[data-id="${id}"]`) };
  }, 目标);
  if (!前置.存在) return { 无效: '目标行不在', 前置 };
  if (!前置.节点在) return { 无效: '画布上找不到目标节点', 前置 };

  await p.mouse.click(前置.点[0], 前置.点[1]);
  const 帧 = [];
  for (let k = 0; k < 6; k++) {
    帧.push(await p.evaluate(() => {
      const vp = document.querySelector('.react-flow__viewport');
      const m = vp ? /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
      const z = document.querySelector('[data-testid="canvas-zoom-percent"]');
      return { vp: m ? [Number(m[1]), Number(m[2]), Number(m[3])] : null, zoom: z ? z.getAttribute('aria-label') : null };
    }));
    await p.waitForTimeout(600);
  }
  const 有效帧 = 帧.filter((f) => f.vp && f.vp.length === 3 && Number.isFinite(f.vp[1]));  // 立规 82
  if (有效帧.length === 0) return { 无效: '6 帧全空', 前置, 帧 };
  const ty集合 = [...new Set(帧.map((f) => f.vp && f.vp[1]))];
  return { 前置, 帧, 有效帧数: 有效帧.length, ty取值: ty集合,
    C取值: ty集合.filter((t) => t != null).map((t) => Math.round((t - 高度系数 * H) * 1000) / 1000) };
}

const { chromium } = await import('playwright');
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

// —— 条件 ①：复用页 ——
const 复用 = await ctx.newPage();
try {
  await 复用.setViewportSize({ width: 1280, height: H });
  await 复用.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await 复用.waitForSelector('.react-flow__node', { timeout: 45000 });
  await 复用.waitForTimeout(4500);
  for (const w of 宽度集) {
    const 键 = `复用页@${w}`;
    try {
      await 复用.setViewportSize({ width: w, height: H });
      await 复用.waitForTimeout(1800);
      const 记初值 = {};
      out.臂[键] = await 取景(复用, 记初值);
      out.臂[键].条件 = '复用页'; out.臂[键].宽 = w; out.臂[键]._初 = 记初值.初始vp;
      log(键, '|', JSON.stringify(out.臂[键].ty取值), '| C', JSON.stringify(out.臂[键].C取值), '| 初始', JSON.stringify(记初值.初始vp));
    } catch (e) { out.臂[键] = { 出错: e.message }; log(键, '🔴', e.message); }
    finally { fs.writeFileSync(OUT, JSON.stringify(out, null, 1)); }
  }
} finally { try { await 复用.close(); } catch {} }

// —— 条件 ②：新开页（批次 200 的做法：每档 newPage + goto）——
for (const w of 宽度集) {
  const 键 = `新开页@${w}`;
  const p = await ctx.newPage();
  try {
    await p.setViewportSize({ width: w, height: H });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(4500);
    const 记初值 = {};
    out.臂[键] = await 取景(p, 记初值);
    out.臂[键].条件 = '新开页'; out.臂[键].宽 = w; out.臂[键]._初 = 记初值.初始vp;
    log(键, '|', JSON.stringify(out.臂[键].ty取值), '| C', JSON.stringify(out.臂[键].C取值), '| 初始', JSON.stringify(记初值.初始vp));
  } catch (e) { out.臂[键] = { 出错: e.message }; log(键, '🔴', e.message); }
  finally { try { await p.close(); } catch {} fs.writeFileSync(OUT, JSON.stringify(out, null, 1)); }
}

// —— 汇总：唯一自变量的判据 ——
const 汇总 = {};
for (const [k, v] of Object.entries(out.臂)) {
  汇总[k] = v.无效 || v.出错 ? { 无效: v.无效 || v.出错 } : { ty: v.ty取值, C: v.C取值, 有效帧数: v.有效帧数 };
}
out.汇总 = 汇总;
log('\n=== 汇总 ===');
log(JSON.stringify(汇总, null, 1));
const A = (k) => (汇总[k] && 汇总[k].C ? 汇总[k].C : null);
log('\n1200 复用', JSON.stringify(A('复用页@1200')), 'vs 新开', JSON.stringify(A('新开页@1200')));
log('1280 复用', JSON.stringify(A('复用页@1280')), 'vs 新开', JSON.stringify(A('新开页@1280')));
fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
await b.close();

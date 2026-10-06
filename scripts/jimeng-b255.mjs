/**
 * 批次 255：**全 DOM 普查** —— 穷举每一个元素、每一条 CSS 规则，
 *   看有没有任何东西能**直接给出 `412` 或 `532`**。
 *
 * 📌 背景（批次 254）：三路几何读法全部排除
 *   ① 不是画布容器净宽（`7/7` 开关 `Δ=0`）
 *   ② 不是任何一块浮层的宽度/位置（都随 `w` 变）
 *   ③ 不是视口被 UI 遮住的总宽度（`291/284/284/284/284/284/204/364`，`0/8` 命中）
 *   ⇒ 「**`412` 到底是什么**」只剩一条路：**它是某个还没被看见的东西。**
 *
 * 📌 本批用**穷举**代替猜（立规 131 的正用）：
 *   不列候选、不挑「最像的」，而是把**全部元素**都量一遍，全部可能的读法都记下来：
 *     · 元素宽度（未裁剪 / 裁剪到视口）
 *     · 元素的 `left` / `right` / `x+width`
 *     · **祖先链**上的 `padding-left/right`、`margin`、`gap`（累加）
 *     · `getBoundingClientRect` 之外的**布局量**（`offsetWidth` / `clientWidth` / `scrollWidth`）
 *   再把**所有可读样式表**的规则文本扫一遍，找字面量 `412` / `532`。
 *   ⇒ 两种可能，分歧点明确：
 *     · 命中 ⇒ 那就是（或就是线索）；
 *     · 零命中 ⇒ **`412`/`532` 不在这张页面的任何可见几何与 CSS 里**，
 *       下一步就不必再在 DOM 里找了。
 *
 * 📌 诚实要求：**跨域样式表读不到**（`cssRules` 抛错）必须**计数并报出来**，
 *   不能默认「读到了全部」⇒ 这是立规 126 的应用。
 *
 * 🔴 纪律：一个控件都不点；只开新页、只读 DOM；不建不删不上传不生成不扣费不分享。
 *
 * 用法：node scripts/jimeng-b255.mjs      （读数落盘 /tmp/b255.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B255_OUT || '/tmp/b255.json';
const 高 = 720;
// 🔴 `412` 起约束的是 `w∈[438,512]`、`532` 起约束的是宽侧 ⇒ 两档各测一次
const 宽表 = [500, 1100];

const log = (...a) => console.log(a.join(' '));
const 目标 = [412, 532];

const 普查 = (目标数) => {
  const 视口W = window.innerWidth;
  const 命中 = [];
  const 近似 = [];
  const 全量 = { 元素数: 0, 候选数: 0 };
  const 全 = document.querySelectorAll('*');
  全量.元素数 = 全.length;

  const 记一次 = (键, 值, e) => {
    全量.候选数++;
    if (typeof 值 !== 'number' || !Number.isFinite(值)) return;
    const v = Math.round(值 * 1000) / 1000;
    const 近 = 目标数.some((t) => Math.abs(v - t) < 1);
    const 条 = {
      键, 值: v, testid: e.getAttribute ? (e.getAttribute('data-testid') || null) : null,
      tag: e.tagName ? e.tagName.toLowerCase() : null,
      cls: (typeof e.className === 'string' ? e.className : '').slice(0, 70),
    };
    if (目标数.includes(v)) 命中.push(条);
    else if (近) 近似.push(条);
  };

  for (const e of 全) {
    const b = e.getBoundingClientRect();
    const cs = getComputedStyle(e);
    // 📌 全部可能给出常数的读法，**逐个记**（不挑）
    记一次('rect.w', b.width, e);
    记一次('rect.left', b.left, e);
    记一次('rect.right', b.right, e);
    记一次('rect.x+w', b.x + b.width, e);
    记一次('视口内宽', Math.max(0, Math.min(视口W, b.right) - Math.max(0, b.left)), e);
    记一次('offsetWidth', e.offsetWidth, e);
    记一次('clientWidth', e.clientWidth, e);
    记一次('scrollWidth', e.scrollWidth, e);
    记一次('offsetLeft', e.offsetLeft, e);
    for (const k of ['paddingLeft', 'paddingRight', 'marginLeft', 'marginRight', 'left', 'right', 'width', 'gap', 'columnGap', 'rowGap', 'insetInlineStart', 'insetInlineEnd']) {
      const 原始 = cs[k];
      if (!原始 || !原始.endsWith('px')) continue;
      const n = parseFloat(原始);
      if (n) 记一次(`css.${k}`, n, e);
    }
    // 📌 祖先链上的左右留白累加（"距左 / 距右 的总让位"是最自然的 412 候选）
    let 累计左 = 0, 累计右 = 0, 层数 = 0;
    for (let p = e.parentElement; p && 层数 < 12; p = p.parentElement, 层数++) {
      const pc = getComputedStyle(p);
      累计左 += parseFloat(pc.paddingLeft) || 0;
      累计右 += parseFloat(pc.paddingRight) || 0;
    }
    if (累计左) 记一次('祖先链左留白', 累计左, e);
    if (累计右) 记一次('祖先链右留白', 累计右, e);
    if (累计左 + 累计右) 记一次('祖先链左右留白和', 累计左 + 累计右, e);
  }

  // 📌 样式表字面量扫描 —— 读不到的必须计数
  const 表统计 = { 总数: 0, 可读: 0, 读不到: 0, 命中规则: [] };
  for (const sh of Array.from(document.styleSheets)) {
    表统计.总数++;
    let 规则 = null;
    try { 规则 = sh.cssRules; } catch (e) { 表统计.读不到++; continue; }
    if (!规则) { 表统计.读不到++; continue; }
    表统计.可读++;
    for (const r of Array.from(规则)) {
      const t = r.cssText || '';
      for (const 目标值 of 目标数) {
        // 只认"作为完整数值出现"，避免 1412 / 0.532 这类误报
        const 正则 = new RegExp(`(^|[^0-9.])${目标值}([^0-9.]|$)`);
        if (正则.test(t)) {
          表统计.命中规则.push({ 表: (sh.href || '内联').slice(-60), 值: 目标值, 片段: t.slice(0, 220) });
        }
      }
    }
  }

  return { 视口W, 全量, 命中, 近似, 表统计 };
};

const out = { 轮次: 'b255', 高, 宽表, 目标, 行: [] };
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

for (const 宽 of 宽表) {
  const p = await ctx.newPage();
  const 记 = { 宽 };
  try {
    await p.setViewportSize({ width: 宽, height: 高 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(5500);
    Object.assign(记, await p.evaluate(普查, 目标));
    记.逐字命中数 = 记.命中.length;
    记.近似命中数 = 记.近似.length;
    log(`【w=${宽}】元素 ${记.全量.元素数} 个 · 生成读量 ${记.全量.候选数} 条`);
    log(`   逐字等于 ${JSON.stringify(目标)} 的读量：**${记.逐字命中数} 条**`);
    log(`   ±1 内近似：**${记.近似命中数} 条**`);
    log(`   样式表 ${记.表统计.总数} 张：可读 ${记.表统计.可读} / **读不到 ${记.表统计.读不到}**`
      + `；命中规则 **${记.表统计.命中规则.length} 条**`);
    for (const h of 记.命中.slice(0, 40)) {
      log(`   🎯 ${h.键}=${h.值} <${h.tag}> testid=${JSON.stringify(h.testid)} cls=${JSON.stringify(h.cls)}`);
    }
    for (const h of 记.近似.slice(0, 12)) {
      log(`   ≈ ${h.键}=${h.值} <${h.tag}> testid=${JSON.stringify(h.testid)}`);
    }
    for (const h of 记.表统计.命中规则.slice(0, 20)) log(`   📄 CSS 命中 ${h.值}: ${h.片段}`);
  } catch (e) {
    记.错误 = e.message;
    log(`🔴 w=${宽} ${e.message}`);
  } finally {
    try { await p.close(); } catch (e) { /* 忽略 */ }
    out.行.push(记);
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

const 好 = out.行.filter((r) => !r.错误);
out.总逐字命中 = 好.reduce((a, r) => a + r.逐字命中数, 0);
out.总近似命中 = 好.reduce((a, r) => a + r.近似命中数, 0);
out.总CSS命中 = 好.reduce((a, r) => a + r.表统计.命中规则.length, 0);
out.总读量 = 好.reduce((a, r) => a + r.全量.候选数, 0);
out.总读不到的表 = 好.reduce((a, r) => a + r.表统计.读不到, 0);
out.总表数 = 好.reduce((a, r) => a + r.表统计.总数, 0);
log('=== 总计 ===');
log(`逐字命中 ${out.总逐字命中} / ${out.总读量} 条读量；近似命中 ${out.总近似命中}；CSS 规则命中 ${out.总CSS命中}`);
log(`样式表 ${out.总表数} 张中 **${out.总读不到的表} 张读不到**（跨域）⇒ 未覆盖面已如实记出`);
fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log('写入 ' + OUT);
// 🔴 不要 `b.close()`：那会把无头浏览器一起关掉（批次 249 踩过）
process.exit(0);
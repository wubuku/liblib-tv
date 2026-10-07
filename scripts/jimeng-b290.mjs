/**
 * 批次 290：夹 `w = 1212` 那个翻转点 —— 但先用**不点任何东西**的办法。
 *
 * 📌 起意（批次 289）：
 *   `视频 1`（`320 × 569`）、`H = 720`：
 *     `w = 900 / 1000 / 1100` ⇒ `vs = 0.984183`，**逐字等于闭式**
 *     `w = 1212`（两遍）      ⇒ `vs ≈ 0.62`，**与闭式差 `37%`**
 *   ⇒ 🔴 **翻转点夹在 `(1100, 1212]`。**
 *
 * 📌 **为什么不直接用点击法去夹**：
 *   点击法每臂要「重载页面 + 按 13 次放大键 + 搜 + 点 + 等落定」，约 `90s`，
 *   而且 🔴 **它读出来的 `vs` 自身带 `±0.005` 的跨遍方差**（批次 289）。
 *   ⇒ 📌 **先用一条便宜得多的读量去夹，夹到 `25px` 窗口之后再用点击法确认。**
 *
 * 📌 **本批的便宜读量（纯 DOM，一个东西都不点）**：
 *   ① `.react-flow` **表面尺寸** —— 若某个面板在断点处出现/消失，表面尺寸会**断崖式**变；
 *   ② `视频 1` 的 **`offsetWidth / offsetHeight`** ——
 *      🔴 **这是最关键的一条**：`vs = min(safeW/Wc, safeH/Hc)` 的分母就是它。
 *      批次 287 在 `w=1212` 上读到 `offsetHeight = 569`，而批次 289 反解出的
 *      `targetH ≈ 899–906`（**多 `≈330`–`337`**）⇒
 *      📌 **若节点的 DOM 盒在断点处真的变高，那 `vs` 的跳变当场就被解释**；
 *   ③ 全部 `[data-testid]` 元素的盒 —— 用来找**是哪一个元素**在断点处改了尺寸。
 *
 * 📌 **三条前提**：
 *   ① **轴向自检**：`innerW/innerH` 逐字等于设定值；
 *   ② 🔴 **比较集固定（立规 166）**：相邻两档的 `[data-testid]` 差分**只在该对的交集上做**，
 *      且「判变化」指「值变了」而不是「元素出现了」；
 *   ③ 📌 **相邻档连测**：顺序升序扫，差分只在**相邻两档**之间做（不跨档，避免累加）。
 *
 * 📌 **纪律**：**纯只读，一个东西都不点**；不新建/不删除/不上传/不分享/不进扣费页/绝不点生成；
 *   末态在实验流程之外独立复查（立规 140）。
 *
 * 用法：node scripts/jimeng-b290.mjs      （落盘 /tmp/b290.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B290_OUT || '/tmp/b290.json';
const 高 = 720;
const 目标 = 'node_236ctpehgg';                 // 视频 1
const 宽度组 = [1100, 1120, 1150, 1175, 1200, 1202, 1210, 1212, 1300];

const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b290', 问: 'w=1212 的翻转点在 (1100,1212] 的哪一档？纯 DOM 读，不点任何东西', 宽度组, 臂: [], 差分: [], 判定: {} };

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

const 读 = (p, nid) => p.evaluate((id) => {
  const rf = document.querySelector('.react-flow');
  const 盒 = (el) => { if (!el) return null; const r = el.getBoundingClientRect(); return { w: +r.width.toFixed(2), h: +r.height.toFixed(2) }; };
  const 节点 = document.querySelector(`.react-flow__node[data-id="${id}"]`);
  const testid = {};
  document.querySelectorAll('[data-testid]').forEach((el) => {
    const k = el.getAttribute('data-testid');
    if (!k || testid[k]) return;
    const r = el.getBoundingClientRect();
    if (!(r.width > 0 && r.height > 0)) return;
    testid[k] = [+r.width.toFixed(2), +r.height.toFixed(2)];
  });
  return {
    表面: 盒(rf),
    节点数: document.querySelectorAll('.react-flow__node').length,
    节点盒: 节点 ? { W: 节点.offsetWidth, Hc: 节点.offsetHeight } : null,
    节点rect: 盒(节点),
    testid,
  };
}, nid);

for (const w of 宽度组) {
  const p = await ctx.newPage();
  const 记 = { w, h: 高 };
  try {
    await p.setViewportSize({ width: w, height: 高 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(7000);
    const 实际 = await p.evaluate(() => ({ w: innerWidth, h: innerHeight }));
    if (实际.w !== w || 实际.h !== 高) throw new Error(`轴向自检失败：要 ${w}×${高}，实测 ${实际.w}×${实际.h}`);
    const r = await 读(p, 目标);
    记.表面 = r.表面; 记.节点数 = r.节点数; 记.节点盒 = r.节点盒; 记.testid = r.testid;
    log(`${String(w).padStart(4)}×${高}｜表面 ${r.表面 ? r.表面.w + '×' + r.表面.h : 'null'}｜视频节点 ${r.节点盒 ? r.节点盒.W + '×' + r.节点盒.Hc : 'null'}｜节点数 ${r.节点数}｜testid ${Object.keys(r.testid).length}`);
  } catch (e) {
    记.错误 = e.message; log(`${String(w).padStart(4)} 🔴 ${e.message}`);
  } finally {
    try { await p.close(); } catch (e) { /* 忽略 */ }
    out.臂.push(记);
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

// ── 前提②：相邻档差分，且只在该对的 testid 交集上做 ──
const 好 = out.臂.filter((x) => !x.错误 && x.表面);
log('\n════ 表面与节点盒随宽度 ════');
for (const x of 好) log(`  w=${String(x.w).padEnd(5)} 表面 ${String(x.表面.w).padEnd(8)}×${String(x.表面.h).padEnd(7)} 视频节点 ${x.节点盒 ? x.节点盒.W + '×' + x.节点盒.Hc : 'null'}`);

const 节点跳 = [];
const 表面跳 = [];
for (let i = 1; i < 好.length; i++) {
  const a = 好[i - 1], c = 好[i];
  const dW = +(c.表面.w - a.表面.w).toFixed(2);
  const dH = +(c.表面.h - a.表面.h).toFixed(2);
  const 盒子变 = (a.节点盒 && c.节点盒 && (a.节点盒.W !== c.节点盒.W || a.节点盒.Hc !== c.节点盒.Hc))
    ? `${a.节点盒.W}×${a.节点盒.Hc} -> ${c.节点盒.W}×${c.节点盒.Hc}` : null;
  const 交 = Object.keys(a.testid).filter((k) => k in c.testid);
  const 变testid = 交.filter((k) => a.testid[k][0] !== c.testid[k][0] || a.testid[k][1] !== c.testid[k][1])
    .map((k) => `${k}: ${a.testid[k]} -> ${c.testid[k]}`);
  const 增 = Object.keys(c.testid).filter((k) => !(k in a.testid));
  const 减 = Object.keys(a.testid).filter((k) => !(k in c.testid));
  out.差分.push({ 从: a.w, 到: c.w, 表面Δ: [dW, dH], 交集数: 交.length, 变testid, 新增: 增, 消失: 减, 节点盒变化: 盒子变 });
  if (盒子变) 节点跳.push({ 从: a.w, 到: c.w, 变化: 盒子变 });
  if (Math.abs(dW) > 1 || Math.abs(dH) > 1) 表面跳.push({ 从: a.w, 到: c.w, Δ: [dW, dH] });
}

log('\n════ 相邻档差分（只在该对的 testid 交集上做）════');
for (const d of out.差分) {
  log(`  ${d.从} → ${d.到}｜表面Δ ${d.表面Δ}｜交集 ${d.交集数} 个｜变了的 testid ${d.变testid.length}｜新增 ${d.新增.length} 消失 ${d.消失.length}` +
      (d.节点盒变化 ? `｜🔴 视频节点盒 ${d.节点盒变化}` : ''));
  for (const t of d.变testid.slice(0, 8)) log(`      ${t}`);
}

if (!好.length) {
  out.判定 = { 结论: '🔴 一条有效臂都没有 ⇒ 整组作废' };
} else {
  const 首 = 好[0], 末 = 好[好.length - 1];
  out.判定 = {
    有效臂: `${好.length}/${out.臂.length}`,
    表面宽度随w: 好.map((x) => `${x.w}→${x.表面.w}`).join('  '),
    表面断崖: 表面跳.length ? `⚠️ 有 ${表面跳.length} 处相邻档表面尺寸变化超过 1px：${表面跳.map((s) => `${s.从}→${s.到} Δ${s.Δ}`).join('; ')}` : '✅ 相邻档表面尺寸变化都 ≤1px（纯线性）',
    视频节点盒: 好.map((x) => `${x.w}→${x.节点盒 ? x.节点盒.W + '×' + x.节点盒.Hc : 'null'}`).join('  '),
    节点盒跳变: 节点跳.length ? `🔴 ${节点跳.length} 处跳变：${节点跳.map((s) => `${s.从}→${s.到} ${s.变化}`).join('; ')}` : '✅ 全程没跳变 ⇒ 🔴 **`vs` 的跳变不是节点 DOM 盒造成的**',
    结论: 节点跳.length
      ? `🔴 **视频节点的 DOM 盒在某个宽度上跳变** ⇒ 那就是 vs 跳变的直接来源；跳变被夹在相邻两档之间`
      : `⚠️ **视频节点的 DOM 盒全程不变（` + 首.节点盒.W + '×' + 首.节点盒.Hc + `）** ⇒ 🔴 **vs 在 w=1212 的跳变不由节点 DOM 盒造成**，成因仍未测，不编（立规 113）。下一批要么查 testid 层（见上面变了的 testid），要么回到点击法在夹窄的窗口里确认`,
  };
}
log('\n════ 判定 ════\n' + JSON.stringify(out.判定, null, 1));

const pz = await ctx.newPage();
try {
  await pz.setViewportSize({ width: 1280, height: 720 });
  await pz.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await pz.waitForSelector('.react-flow__node', { timeout: 45000 });
  await pz.waitForTimeout(6000);
  out.末态 = await pz.evaluate(() => ({
    节点数: document.querySelectorAll('.react-flow__node').length,
    状态行: (document.body.innerText.match(/\d+ nodes, \d+ edges, \d+ selected[^\n]*/) || [])[0] || null,
  }));
} finally { try { await pz.close(); } catch (e) { /* 忽略 */ } }
log(`\n末态独立复查：${JSON.stringify(out.末态)}`);

fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log(`写入 ${OUT}`);
process.exit(0);
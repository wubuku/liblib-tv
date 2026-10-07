/**
 * 批次 307 · `z0=1.93` 那条臂的终点为什么不是 `vs`？—— 两条正交对照把它定死。
 *
 * 🔴 起意：批次 306 的闭式 `vs = min((w−532)/320, (h−160)/320)` 对 `9/9` 臂逐字吻合，
 *    🔴 但批次 303/304/305 的低起点臂（`z0 = 1.93` / `1.608`）落 `1.55214`–`1.56009`，
 *    距 `vs = 1.75` 差 `≈0.19`。批次 306 如实记账为「成因未测」。
 *    📌 本批把它做成**两条正交对照**，因为「确定性第二分支」与「定点迭代未收敛」
 *       这两个解释会给出**相反的预测**。
 *
 * 📌 **对照 A（同 `z0` 连跑 `3` 遍）** —— 判「是不是确定性」：
 *   **A1** 三个终点极差**极小**（相对 < `0.1%`）⇒ 🔴 不是噪声，是**一条稳定的第二分支**；
 *   **A2** 三个终点**明显飘** ⇒ 是噪声或未收敛态，⚠️ 立规 113 只报区间。
 *   📌 关键：**这不是「连读两次逐字相同」那种弱检查**（立规 171 已推翻过它的强度），
 *      而是**三遍独立浏览器**的跨遍比较。
 *
 * 📌 **对照 B（等更久 vs 常规等待）** —— 判「是不是定点迭代没跑完」：
 *   批次 298 已定位「最多 `24` 轮、`|Δzoom| ≤ 1e-7`、**不收敛返回最后一轮**」。
 *   📌 若终点在更长等待后**往 `vs = 1.75` 方向移动** ⇒ 🔴 **是未收敛**（时间不够，动画没跑完）；
 *   📌 若**逐字不动** ⇒ 🔴 **不是时间问题**，是另一条机制。
 *   📌 **等待时间是本批唯一变量**，其余全同。
 *
 * 📌 **对照 C（高起点臂，阳性对照）** —— 确保尺子没漂：
 *   📌 同一条测量路径在 `z0` 高的臂上必须仍然落 `vs = 1.75`；
 *   🔴 否则 A/B 两组的读数都不能用（同族：批次 306 P4 准入、批次 304 立规 182）。
 *
 * 📌 判据（**测量前写死**）：
 *   **P1/A1** A 组三遍极差 `< 0.1%` ⇒ 第二分支；否则只报区间
 *   **P2/B**  B 组（等 `12s`）终点若 ≠ A 组常规终点 ⇒ 未收敛；若逐字相同 ⇒ 非时间问题
 *   **P3/C**  C 组必须落 `vs = 1.75`，否则本批读数全部作废
 *
 * 前提检查：轴向自检 / 落定自检 / 点击生效自检 / `aria` 精确匹配现找现量 /
 *   参数写死（按键次数与等待时间是唯一变量）/ 每臂独立浏览器。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const STATE = `${process.env.HOME}/.jimeng-automation/state.json`;
const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b307.json';
const 放大键 = 'Meta+Equal';
const w = 1212; const h = 720;
const kind = '文本'; const 名 = '文本 1';

/** 📌 批次 306 闭式给出的 vs（写死当基准，不是本批算的） */
const 基准vs = 1.75;

/** 📌 A 组：同 z0=11 次键 连跑 3 遍（常规等待）；C 组：高起点臂（阳性对照） */
const 臂表 = [
  { 键: 'A1遍', 组: 'A', 按: 11, 等后ms: 2600, 遍: 1 },
  { 键: 'A2遍', 组: 'A', 按: 11, 等后ms: 2600, 遍: 2 },
  { 键: 'A3遍', 组: 'A', 按: 11, 等后ms: 2600, 遍: 3 },
  { 键: 'B等12s', 组: 'B', 按: 11, 等后ms: 12000, 遍: 1 },
  { 键: 'C高起点', 组: 'C', 按: 13, 等后ms: 2600, 遍: 1 },
];

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b307',
  问: 'z0=1.93 那条臂的终点为什么不是 vs？确定性第二分支，还是定点迭代未收敛？',
  判据: {
    P1_A: 'A组三遍极差<0.1% ⇒ 第二分支（确定性）；否则只报区间',
    P2_B: 'B组(等12s)终点若≠A组 ⇒ 未收敛；若逐字同 ⇒ 非时间问题',
    P3_C: 'C组(高起点)必须落 vs=1.75，否则本批全部作废',
  },
  基准vs, w, h, 臂表, 臂: [], 判定: {},
};

for (const A of 臂表) {
  let br = null; let p = null; let nid = null;
  const 记 = { 键: A.键, 组: A.组, 按: A.按, 等后ms: A.等后ms, 遍: A.遍 };
  try {
    br = await chromium.launch({ headless: true });
    const ctx = await br.newContext({ storageState: STATE, viewport: { width: w, height: h } });
    p = await ctx.newPage();
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 60000 });
    await p.waitForTimeout(6000);
    const 实际 = await p.evaluate(() => ({ w: innerWidth, h: innerHeight }));
    if (实际.w !== w || 实际.h !== h) throw new Error(`轴向自检失败：实测 ${实际.w}×${实际.h}`);

    const ariaWant = `${kind} node: ${名}`;
    const 目标 = await p.evaluate((aria) => {
      const e = Array.from(document.querySelectorAll('.react-flow__node[data-id]'))
        .find((x) => x.getAttribute('aria-label') === aria);
      return e ? { id: e.dataset.id, W: e.offsetWidth, H: e.offsetHeight } : null;
    }, ariaWant);
    if (!目标) throw new Error(`找不到 aria 为「${ariaWant}」的节点`);
    nid = 目标.id;
    记.盒 = { W: 目标.W, H: 目标.H };

    for (let i = 0; i < A.按; i++) { await p.keyboard.press(放大键); await p.waitForTimeout(380); }
    await p.waitForTimeout(1400);
    const 读缩放 = () => p.evaluate(() => {
      const vp = document.querySelector('.react-flow__viewport');
      const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
      return m ? Number(m[1]) : null;
    });
    const z0 = await 读缩放();
    记.z0 = z0;
    if (z0 === null) throw new Error('读不到缩放');

    const 钮 = await p.evaluate(() => {
      const b = document.querySelector('button[aria-label="搜索"]');
      if (!b) return null;
      const r = b.getBoundingClientRect();
      return { 中心: [r.x + r.width / 2, r.y + r.height / 2], 可见: r.width > 0 && r.height > 0 && r.y >= 0 && r.bottom <= innerHeight };
    });
    if (!钮 || !钮.可见) throw new Error('找不到可见的搜索钮');
    await p.mouse.click(钮.中心[0], 钮.中心[1]);
    await p.waitForTimeout(1600);

    let 行 = null;
    for (const 词 of [名, ariaWant, kind]) {
      await p.evaluate(() => { const i = document.querySelector('[data-testid="canvas-search-panel"] input'); if (i) { i.focus(); i.select(); } });
      await p.keyboard.type(词, { delay: 80 });
      await p.waitForTimeout(2000);
      const sel = `[data-testid="canvas-search-result-node_${nid.replace(/^node_/, '')}"]`;
      let r = await p.evaluate((s) => {
        const e = document.querySelector(s);
        if (!e) return null;
        e.scrollIntoView({ block: 'center' });
        const b = e.getBoundingClientRect();
        return { 中心: [Math.round(b.x + b.width / 2), Math.round(b.y + b.height / 2)], 可见: b.width > 0 && b.height > 0 && b.y >= 0 && b.bottom <= innerHeight && b.x >= 0 && b.right <= innerWidth };
      }, sel);
      if (r && !r.可见) {
        await p.waitForTimeout(600);
        r = await p.evaluate((s) => { const e = document.querySelector(s); const b = e.getBoundingClientRect(); return { 中心: [Math.round(b.x + b.width / 2), Math.round(b.y + b.height / 2)], 可见: b.width > 0 && b.height > 0 && b.y >= 0 && b.bottom <= innerHeight && b.x >= 0 && b.right <= innerWidth }; }, sel);
      }
      if (r && r.可见) { 行 = r; break; }
    }
    if (!行) throw new Error(`搜不到「${名}」的可见结果行`);
    await p.mouse.click(行.中心[0], 行.中心[1]);
    await p.waitForTimeout(3200);

    // 📌 第一次读（落定自检的第一次）
    const 读1 = await 读缩放();
    记.读1 = 读1;
    // 📌 B 组在这里多等，📌 等待时间是本批唯一变量
    await p.waitForTimeout(A.等后ms);
    const 读2 = await 读缩放();
    记.读2 = 读2;
    // 📌 再等一小段做第二次落定自检
    await p.waitForTimeout(2000);
    const 读3 = await 读缩放();
    记.读3 = 读3;

    记.落定 = (读1 === 读2 && 读2 === 读3);
    记.终点 = 读3;
    const 选 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((x) => x.dataset.id));
    记.点击生效 = 选.includes(nid);
    if (!记.点击生效) throw new Error(`点击未生效（选中=${JSON.stringify(选)}）`);
    记.落vs = Math.abs(读3 - 基准vs) < 1e-6;
    记.距vs = +(基准vs - 读3).toFixed(5);
    log(`${A.键.padEnd(8)}｜z0=${String(z0).padEnd(8)}｜读1=${String(读1).padEnd(10)}读2=${String(读2).padEnd(10)}读3=${String(读3).padEnd(10)}｜落定=${记.落定}｜距vs=${记.距vs}`);
  } catch (e) {
    记.错误 = e.message;
    log(`${A.键.padEnd(8)}🔴 ${e.message}`);
  } finally {
    try { if (p) await p.close(); } catch (e) { /* 忽略 */ }
    try { if (br) await br.close(); } catch (e) { /* 忽略 */ }
    out.臂.push(记);
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

// ───────── 判定 ─────────
const 好 = out.臂.filter((x) => !x.错误 && x.点击生效 && x.终点 !== undefined && x.落定);
const A组 = 好.filter((x) => x.组 === 'A');
const B臂 = 好.find((x) => x.组 === 'B');
const C臂 = 好.find((x) => x.组 === 'C');
const 极差 = (arr) => (arr.length > 1 ? Math.max(...arr) - Math.min(...arr) : null);

const A终点 = A组.map((x) => x.终点);
const A极差 = 极差(A终点);
const A相对极差 = (A极差 !== null && A极差 > 0) ? A极差 / Math.min(...A终点) : 0;
const P3ok = C臂 ? C臂.落vs : false;

let P1; let P2;
if (A组.length >= 3 && A相对极差 < 0.001) {
  P1 = `✅ P1/A1：A 组三遍终点 ${JSON.stringify(A终点)} 相对极差 ${(A相对极差 * 100).toFixed(4)}%（<0.1%）⇒ 🔴 **不是噪声，是一条稳定的第二分支**（确定性）`;
} else if (A组.length >= 3) {
  P1 = `⚠️ P1/A2：A 组三遍终点 ${JSON.stringify(A终点)} 相对极差 ${(A相对极差 * 100).toFixed(4)}%（≥0.1%）⇒ 是噪声/未收敛态，📌 按立规 113 **只报区间 [${Math.min(...A终点)}, ${Math.max(...A终点)}]**，不报单值`;
} else {
  P1 = `（A 组有效臂 ${A组.length}/3，不足）`;
}
if (B臂 && A组.length >= 1) {
  const A典型 = A组[0].终点;
  const 相同 = Math.abs(B臂.终点 - A典型) < 1e-6;
  P2 = 相同
    ? `✅ P2/B：B 组（等 ${B臂.等后ms}ms）终点 ${B臂.终点} 与 A 组常规等待 ${A典型} **逐字相同** ⇒ 🔴 **不是「等不够久」**（时间不是原因），另一条机制仍待查`
    : `🔴 P2/B：B 组（等 ${B臂.等后ms}ms）终点 ${B臂.终点} ≠ A 组 ${A典型}，且朝 vs=${基准vs} 移动了 ${(A典型 - B臂.终点).toFixed(5)} ⇒ 疑为**定点迭代未跑完**`;
} else {
  P2 = '（B 臂无效）';
}
const P3 = P3ok
  ? `✅ P3/C：C 组（高起点 z0=${C臂 ? C臂.z0 : '—'}）落 vs=${基准vs}（终点 ${C臂 ? C臂.终点 : '—'}）⇒ 尺子没漂，A/B 读数可用`
  : `🔴 P3/C：C 组未落 vs=${基准vs}（终点 ${C臂 ? C臂.终点 : '—'}）⇒ 本批读数作废`;

out.判定 = {
  有效臂: `${好.length}/${臂表.length}`,
  A组终点: A终点, A组极差: A极差, A组相对极差: A相对极差,
  B组终点: B臂 ? B臂.终点 : null, C组终点: C臂 ? C臂.终点 : null,
  P1_A: P1, P2_B: P2, P3_C: P3,
};
log('\n════ 判定 ════\n' + JSON.stringify(out.判定, null, 1));

const brz = await chromium.launch({ headless: true });
const ctxz = await brz.newContext({ storageState: STATE, viewport: { width: 1280, height: 720 } });
const pz = await ctxz.newPage();
try {
  await pz.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await pz.waitForSelector('.react-flow__node', { timeout: 60000 });
  await pz.waitForTimeout(6000);
  out.末态 = await pz.evaluate(() => ({
    节点数: document.querySelectorAll('.react-flow__node').length,
    状态行: (document.body.innerText.match(/\d+ nodes, \d+ edges, \d+ selected[^\n]*/) || [])[0] || null,
    积分: (document.querySelector('[data-testid="canvas-commerce-entry"]') || {}).textContent || null,
  }));
  log('末态独立复查：', JSON.stringify(out.末态));
} finally { try { await pz.close(); await brz.close(); } catch (e) { /* 忽略 */ } }

fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log('写入', OUT);
process.exit(0);
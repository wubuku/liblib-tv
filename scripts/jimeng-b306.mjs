/**
 * 批次 306 · 判别 `compound` 宽高比 `1.214286` 是**恒等式回声**还是**真机制**。
 *
 * 🔴 起意：批次 305 差点把「`compound` 宽高比 = `safeW/safeH` = `1.214286`」写成机制发现，
 *    最后发现那是反推定义（`compoundW := safeW/z`、`compoundH := safeH/z`）造出来的**代数恒等式**。
 *    🔴 立规 184：**要让结论可证伪，就得找一个能让它不成立的条件。**
 *
 * 📌 **本批找的那个条件：换视口宽高比。** 而且本批**刻意不假设 `safeW`/`safeH` 的公式** ——
 *    🔴 批次 305 的教训是「自己定义出来的量不能再当证据」。
 *
 * 📌 **判别逻辑（只依赖「哪一项绑定」，不依赖任何偏移常数）：**
 *   在**高度固定、只变宽度**的一组里，高度项的分母 `safeH` 与盒高都是常数
 *   ⇒ 📌 若高度项绑定，则 `z = safeH/cH` 与宽度无关 ⇒ **`z` 在这一组里应当恒定**；
 *   ⇒ 📌 若宽度项绑定，则 `z` 必随 `w` 递增。
 *   🔴 **「`z` 动不动」这件事不需要知道 `safeW` 是 `w−532` 还是 `w−412`** ——
 *      偏移量留给拟合去反证，而不是先假设。
 *
 * 📌 判据（**测量前写死**）：
 *   **P1** 宽度组：若 `z` 随 `w` **显著递增** ⇒ 宽度项绑定；**若 `z` 逐字恒定** ⇒ 高度项绑定；
 *   **P2** 高度组：若 `z` 随 `h` **显著递减** ⇒ 高度项绑定；**若 `z` 逐字恒定** ⇒ 宽度项绑定；
 *   **P3** 拟合：宽度绑定的那一组，`z` 对 `w` 做线性拟合，
 *          📌 **截距应落在已知侧栏宽（`532` 或 `412`）附近** ⇒ 用拟合反证常数，不靠假设；
 *   **P4** 🔴 **准入条件**：只有 `z_end < z0` 且 `z_end !== z0` 的臂才进统计
 *          —— 不跳臂的终点没被 `vs` 决定（批次 305 结果六），其 `safeW/z` 是伪缺口。
 *
 * 前提检查：轴向自检 / 落定自检 / 点击生效自检 / `aria` 精确匹配现找现量 /
 *   参数写死 / 每臂独立浏览器。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const STATE = `${process.env.HOME}/.jimeng-automation/state.json`;
const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b306.json';
const 放大键 = 'Meta+Equal';
const kind = '文本';
const 名 = '文本 1';
const 按 = 13;

/** 📌 宽度组（h 固定 720，只变 w）｜高度组（w 固定 1212，只变 h） */
const 臂表 = [
  { 键: '宽900', 组: '宽度组', vw: 900, vh: 720 },
  { 键: '宽1000', 组: '宽度组', vw: 1000, vh: 720 },
  { 键: '宽1100', 组: '宽度组', vw: 1100, vh: 720 },
  { 键: '宽1212', 组: '宽度组', vw: 1212, vh: 720 },
  { 键: '宽1400', 组: '宽度组', vw: 1400, vh: 720 },
  { 键: '高600', 组: '高度组', vw: 1212, vh: 600 },
  { 键: '高720', 组: '高度组', vw: 1212, vh: 720 },
  { 键: '高840', 组: '高度组', vw: 1212, vh: 840 },
  { 键: '高900', 组: '高度组', vw: 1212, vh: 900 },
];

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b306',
  问: 'compound 宽高比 1.214286 是反推定义造出来的恒等式回声，还是真实机制？',
  判据: {
    P1: '宽度组(h固定)：z 随 w 递增⇒宽度项绑定；z 逐字恒定⇒高度项绑定',
    P2: '高度组(w固定)：z 随 h 递减⇒高度项绑定；z 逐字恒定⇒宽度项绑定',
    P3: '对绑定项那一组做线性拟合，截距应落在已知侧栏宽附近(532/412)⇒ 用拟合反证常数',
    P4: '准入：只有 z_end < z0 且 z_end !== z0 的臂进统计（批次305：不跳臂是伪缺口）',
  },
  按, 臂表, 臂: [], 判定: {},
};

for (const A of 臂表) {
  let br = null; let p = null; let nid = null;
  const 记 = { 键: A.键, 组: A.组, vw: A.vw, vh: A.vh, kind, 名, 按 };
  try {
    br = await chromium.launch({ headless: true });
    const ctx = await br.newContext({ storageState: STATE, viewport: { width: A.vw, height: A.vh } });
    p = await ctx.newPage();
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 60000 });
    await p.waitForTimeout(6000);
    const 实际 = await p.evaluate(() => ({ w: innerWidth, h: innerHeight }));
    记.实测视口 = 实际;
    if (实际.w !== A.vw || 实际.h !== A.vh) throw new Error(`轴向自检失败：期望 ${A.vw}×${A.vh} 实测 ${实际.w}×${实际.h}`);
    // 📌 点击搜索结果行需要 H ≥ 249（批次已验证），本批最低 600，安全
    if (实际.h < 249) throw new Error(`视口高 ${实际.h} 不足 249，点不到搜索结果行`);

    const ariaWant = `${kind} node: ${名}`;
    const 目标 = await p.evaluate((aria) => {
      const e = Array.from(document.querySelectorAll('.react-flow__node[data-id]'))
        .find((x) => x.getAttribute('aria-label') === aria);
      return e ? { id: e.dataset.id, W: e.offsetWidth, H: e.offsetHeight } : null;
    }, ariaWant);
    if (!目标) throw new Error(`找不到 aria 为「${ariaWant}」的节点`);
    nid = 目标.id;
    记.画布盒 = { W: 目标.W, H: 目标.H };

    for (let i = 0; i < 按; i++) { await p.keyboard.press(放大键); await p.waitForTimeout(380); }
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

    let 行 = null; let 用名 = null;
    // 📌 依次尝试三个搜索词：🔴 用不同变量名，📴 循环变量会遮蔽外层 `名` 并让右侧数组撞 TDZ
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
      if (r && r.可见) { 行 = r; 用名 = 词; break; }
    }
    if (!行) throw new Error(`搜不到「${名}」的可见结果行`);
    记.用名 = 用名;
    await p.mouse.click(行.中心[0], 行.中心[1]);
    await p.waitForTimeout(3200);
    const a1 = await 读缩放();
    await p.waitForTimeout(2600);
    const 后 = await p.evaluate(() => {
      const vp = document.querySelector('.react-flow__viewport');
      const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
      return { scale: m ? Number(m[1]) : null, 选中: Array.from(document.querySelectorAll('.react-flow__node.selected')).map((x) => x.dataset.id) };
    });
    记.终点 = 后.scale;
    记.落定 = a1 === 后.scale;
    记.点击生效 = (后.选中 || []).includes(nid);
    if (!记.点击生效) throw new Error(`点击未生效（选中=${JSON.stringify(后.选中)}）`);
    // 📌 P4 准入：只有终点被 vs 压住（终点 < 起点且不等）才进统计
    记.绑定 = (后.scale !== null && z0 !== null && 后.scale < z0 && 后.scale !== z0);
    记.是否恒定候选 = 后.scale !== null && z0 !== null && 后.scale === z0;
    log(`${A.键.padEnd(8)}｜视口 ${String(A.vw).padEnd(5)}×${String(A.vh).padEnd(4)}｜z0=${String(z0).padEnd(9)}｜终点=${String(后.scale).padEnd(10)}｜${记.绑定 ? '跳(可用)' : '未跳(不入统计)'}`);
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
const 宽组 = 好.filter((x) => x.组 === '宽度组' && x.绑定).sort((a, b) => a.vw - b.vw);
const 高组 = 好.filter((x) => x.组 === '高度组' && x.绑定).sort((a, b) => a.vh - b.vh);
const 极差 = (arr) => (arr.length > 1 ? Math.max(...arr) - Math.min(...arr) : null);

const 宽终点 = 宽组.map((x) => x.终点);
const 高终点 = 高组.map((x) => x.终点);
const 宽极差 = 极差(宽终点); const 高极差 = 极差(高终点);
/** 📌 阈值：以「相对极差 > 1% 视为显著变化」写死，避免用眼睛判断 */
const 显 = (v) => v !== null && v > 0.01;

let P1; let P2;
P1 = (宽极差 !== null && 显(宽极差))
  ? `✅ P1：宽度组终点随宽度变化，极差 ${宽极差.toFixed(5)}（>1%）⇒ **宽度项绑定**，高度项不绑定`
  : (宽极差 !== null ? `✅ P1：宽度组终点逐字恒定（极差 ${宽极差}）⇒ **高度项绑定**（终点与宽度无关）` : '（宽度组可用臂不足）');
P2 = (高极差 !== null && 显(高极差))
  ? `✅ P2：高度组终点随高度变化，极差 ${高极差.toFixed(5)}（>1%）⇒ **高度项参与**`
  : (高极差 !== null ? `✅ P2：高度组终点逐字恒定（极差 ${高极差}）⇒ **宽度项绑定**（终点与高度无关）` : '（高度组可用臂不足）');

/** 📌 线性拟合 z = m*x + c，返回斜率截距与 R² */
const 拟合 = (pts) => {
  const n = pts.length; if (n < 2) return null;
  const mx = pts.reduce((s, p) => s + p[0], 0) / n;
  const my = pts.reduce((s, p) => s + p[1], 0) / n;
  let sxy = 0, sxx = 0, syy = 0;
  for (const [x, y] of pts) { sxy += (x - mx) * (y - my); sxx += (x - mx) ** 2; syy += (y - my) ** 2; }
  const m = sxy / sxx; const c = my - m * mx;
  const r2 = syy === 0 ? 1 : (sxy * sxy) / (sxx * syy);
  return { 斜率: +m.toFixed(8), 截距: +c.toFixed(4), R2: +r2.toFixed(6), n };
};
const 宽拟合 = 拟合(宽组.map((x) => [x.vw, x.终点]));
const 高拟合 = 拟合(高组.map((x) => [x.vh, x.终点]));

let P3 = '（样本不足，未拟合）';
if (宽拟合 && 高拟合) {
  P3 = '📌 P3 拟合：宽度组 z = ' + 宽拟合.斜率 + '·w ' + (宽拟合.截距 >= 0 ? '+ ' : '− ') + Math.abs(宽拟合.截距)
    + '（R²=' + 宽拟合.R2 + '，n=' + 宽拟合.n + '）｜高度组 z = ' + 高拟合.斜率 + '·h ' + (高拟合.截距 >= 0 ? '+ ' : '− ') + Math.abs(高拟合.截距)
    + '（R²=' + 高拟合.R2 + '，n=' + 高拟合.n + '）。'
    + '\n　📌 **截距反证**：宽度项 z=(w−k)/cW 的 x 轴截距 = −截距/斜率 = **' + (-宽拟合.截距 / 宽拟合.斜率).toFixed(1) + '**'
    + ' ⇒ 与已知侧栏宽 532/412 比较；📌 **斜率的倒数就是 cW** = **' + (1 / 宽拟合.斜率).toFixed(3) + '** 画布单位。'
    + '\n　📌 同理高度项 x 轴截距 = **' + (-高拟合.截距 / 高拟合.斜率).toFixed(1) + '**，1/斜率 = **' + (1 / 高拟合.斜率).toFixed(3) + '**。';
}

const P4 = `📌 P4 准入：${好.filter((x) => x.绑定).length}/${好.length} 条臂终点被 vs 压住（终点<起点且不等）进统计；`
  + `${好.filter((x) => x.是否恒定候选).length} 条未跳臂**不入统计**（批次 305 结果六：终点未被 vs 决定时 safeW/z 是伪缺口）`;

out.判定 = {
  有效臂: `${好.length}/${臂表.length}`,
  宽度组绑定臂: 宽组.map((x) => `w=${x.vw} → z=${x.终点}`),
  高度组绑定臂: 高组.map((x) => `h=${x.vh} → z=${x.终点}`),
  宽度组终点极差: 宽极差, 高度组终点极差: 高极差,
  P1, P2, P3, P4,
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
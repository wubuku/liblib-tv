/**
 * 批次 314 · 音频/视频/时间线的落点**到底绑在哪个轴上**？—— 顺带回答「批次 191 那张表是不是 vs 的切片」。
 *
 * 🔴 起意：批次 313 把「文本落 1.75」的来源定死为撞 vs 上限，但它自己留下一句没定的话：
 *    「若它其实是 vs 在某个固定视口下的值，那批次 191 的表就是一个视口下的切片；
 *      若它是独立的类型常量，本批两个不等点只在 vs 更紧的那一侧覆盖了它。两条路都还开着，不编。」
 *
 * 📌 批次 311 的落点表里，**音频 1.10512 / 视频 0.598681 都不等于 vs**，
 *    🔴 但它**从没测过非 1212×720 的视口** ⇒ 「vs 切片」这条路对这两个 kind **一次都没被否过**。
 *
 * 📌 **本批的判别器（来自批次 311 反解代码的一个方法学事实）**：
 *    批次 311 的 `反推compoundW = safeW/终点`、`反推compoundH = safeH/终点`
 *    是**轴无关**的：它同时给出两个候选，**没有判定哪条轴真绑定**。
 *    🔴 所以它表里的「多出宽」列在宽度项不绑定时是**伪值**（文本的 `68.571` 就是）。
 *
 * 📌 于是有了这个设计 —— 同一个节点、同一批读数，两个模型给出**完全相反**的预测：
 *      **M宽**：绑定在宽度项 ⇒ `L(w,h) = (w − 532) / W_c`，`W_c = 680 / L₀`
 *      **M高**：绑定在高度项 ⇒ `L(w,h) = (h − 160) / H_c`，`H_c = 560 / L₀`
 *    📌 `L₀` 取**同一批次 311 在 `1212×720` 的实测**，🔴 **不是本批现拟合**。
 *
 *    两个视口各自只动一个轴：
 *      `1212×900`（只变高）⇒ M宽 **不动**、M高 **变**
 *      `1000×720`（只变宽）⇒ M宽 **变**、M高 **不动**
 *    ⇒ 🔴 **判别力极强**：方向相反，一眼能分开。
 *
 * 📌 **文本是阳性对照**：批次 306 已独立证实文本的闭式是 `min((w−532)/320,(h−160)/320)`，
 *    📌 批次 313 又实测 `1212×900→2.125`、`1000×720→1.4625` 逐字吻合
 *    ⇒ 📌 文本臂落 `1.75` ⇒ **尺子没漂**，本批读数可用（立规 189）。
 *
 * 📌 **判据（测量前写死）**：
 *   **P0（阳性对照）** 文本臂必须落 `1.75`，否则本批全部读数作废。
 *   **P1（轴绑定）** 每臂必须**逐字**（`<1e-4`）命中 M宽 / M高 / 两者 / 都不命中；
 *          🔴 两者同时命中 = 该视口下两轴恰好相等（分不出），记 `M宽M高` 并**不算通过**。
 *   **P2（vs 切片）** 若音频/视频在**两个视口下都能逐字命中同一个模型**，
 *          ⇒ 它们也遵守 `(视口 − inset)/compound`，📌 **批次 191 的表是 vs 的切片**（各 kind 一个 compound）。
 *   **P3（无切片）** 若它们两视口都不命中任何模型 ⇒ 🔴 **「191 那张表 = vs 切片」这条路被否**。
 *
 * 前提检查：轴向自检 / 落定自检（三连读）/ 点击生效自检 /
 *   `aria` 精确匹配现找现量 / 参数写死 / 每臂独立浏览器。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const STATE = `${process.env.HOME}/.jimeng-automation/state.json`;
const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b314.json';
const 放大键 = 'Meta+Equal';

/** 📌 批次 306 证实：inset 与视口无关（`1212×900`/`1000×720` 两档逐字命中） */
const SAFE_W = (w) => w - 532;
const SAFE_H = (h) => h - 160;

/** 📌 批次 311 在 `1212×720`、`z0=2.779` 的实测落点（本批的 L₀，不是现拟合） */
const 基线 = {
  音频: 1.10512,
  视频: 0.598681,
  时间线: 0.566667,
  文本: 1.75,
};

const 臂表 = [
  // 实验 A：只变高（宽度项若绑定则不动）
  { 键: 'A1音频-高变', 组: 'A', kind: '音频', 名: '音频 1', vw: 1212, vh: 900 },
  { 键: 'A2音频-宽变', 组: 'A', kind: '音频', 名: '音频 1', vw: 1000, vh: 720 },
  { 键: 'A3视频-高变', 组: 'A', kind: '视频', 名: '视频 1', vw: 1212, vh: 900 },
  { 键: 'A4视频-宽变', 组: 'A', kind: '视频', 名: '视频 1', vw: 1000, vh: 720 },
  // 实验 B：时间线的宽度项到底生不生效（批次 311 那里两轴恰好相等，分不出）
  { 键: 'B1时间线-宽变', 组: 'B', kind: '时间线', 名: '时间线 1', vw: 1000, vh: 720 },
  // 基线复测：确认批次 311 的读数今天还成立（阳性对照之二）
  { 键: 'C1音频-基线', 组: 'C', kind: '音频', 名: '音频 1', vw: 1212, vh: 720 },
  { 键: 'C2视频-基线', 组: 'C', kind: '视频', 名: '视频 1', vw: 1212, vh: 720 },
  // 尺子没漂
  { 键: 'D1文本-对照', 组: 'D', kind: '文本', 名: '文本 1', vw: 1212, vh: 720 },
];

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b314',
  问: '音频/视频/时间线的落点绑在宽度项还是高度项？批次 191 那张表是不是 vs 在某个视口下的切片？',
  判据: {
    P0: '阳性对照：文本臂必须落 1.75（= 批次 306/311/312/313 反复测到的基线），否则整批作废',
    P1: '逐臂判定命中 M宽 / M高 / M宽M高 / 无；M宽M高 不算通过',
    P2: '音频、视频在两个视口下都逐字命中同一模型 ⇒ 遵守 (视口−inset)/compound ⇒ 191 的表是 vs 切片',
    P3: '两者两视口都不命中 ⇒ 否掉「191 那张表 = vs 切片」',
  },
  模型: {
    M宽: 'L(w,h) = (w−532)/W_c，W_c = 680/L0（L0 取批次 311 在 1212×720 的实测）',
    M高: 'L(w,h) = (h−160)/H_c，H_c = 560/L0',
    备注: '两个模型对同一节点在同一新视口下的预测方向相反，这是本批的判别力来源',
  },
  臂表, 臂: [], 判定: {},
};

for (const 臂 of 臂表) {
  let br = null; let p = null; let nid = null;
  const 记 = { 键: 臂.键, 组: 臂.组, kind: 臂.kind, 名: 臂.名, vw: 臂.vw, vh: 臂.vh };
  try {
    // 🔴 预测一律在测量前算好，写进读数，不许事后拟合
    const L0 = 基线[臂.kind];
    记.L0 = L0;
    记.预测M宽 = +(SAFE_W(臂.vw) / (SAFE_W(1212) / L0)).toFixed(6);
    记.预测M高 = +(SAFE_H(臂.vh) / (SAFE_H(720) / L0)).toFixed(6);
    记.预测盒尺寸M宽 = +(SAFE_W(1212) / L0).toFixed(3);
    记.预测盒尺寸M高 = +(SAFE_H(720) / L0).toFixed(3);

    br = await chromium.launch({ headless: true });
    const ctx = await br.newContext({ storageState: STATE, viewport: { width: 臂.vw, height: 臂.vh } });
    p = await ctx.newPage();
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 60000 });
    await p.waitForTimeout(6000);

    // 前提：轴向自检
    const 实际 = await p.evaluate(() => ({ w: innerWidth, h: innerHeight }));
    if (实际.w !== 臂.vw || 实际.h !== 臂.vh) throw new Error('轴向自检失败：' + 实际.w + 'x' + 实际.h);
    if (实际.h < 249) throw new Error('视口高不足 249');

    // 前提：aria 精确匹配，现找现量，不硬编码 id
    const ariaWant = 臂.kind + ' node: ' + 臂.名;
    const 目标 = await p.evaluate((aria) => {
      const e = Array.from(document.querySelectorAll('.react-flow__node[data-id]'))
        .find((x) => x.getAttribute('aria-label') === aria);
      return e ? { id: e.dataset.id, W: e.offsetWidth, H: e.offsetHeight } : null;
    }, ariaWant);
    if (!目标) throw new Error('找不到 aria 为「' + ariaWant + '」的节点');
    nid = 目标.id;
    记.画布盒 = { W: 目标.W, H: 目标.H };

    for (let i = 0; i < 13; i++) { await p.keyboard.press(放大键); await p.waitForTimeout(380); }
    await p.waitForTimeout(1600);
    const 读缩放 = () => p.evaluate(() => {
      const vp = document.querySelector('.react-flow__viewport');
      const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
      return m ? Number(m[1]) : null;
    });
    记.点之前 = await 读缩放();
    if (记.点之前 === null) throw new Error('点之前读不到 scale');
    if (记.点之前 < 2.7) throw new Error('点之前缩放偏低（' + 记.点之前 + '），放大键可能没生效');

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
    for (const 词 of [臂.名, ariaWant, 臂.kind]) {
      await p.evaluate(() => { const i = document.querySelector('[data-testid="canvas-search-panel"] input'); if (i) { i.focus(); i.select(); } });
      await p.keyboard.type(词, { delay: 80 });
      await p.waitForTimeout(2000);
      const sel = '[data-testid="canvas-search-result-node_' + nid.replace(/^node_/, '') + '"]';
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
    if (!行) throw new Error('搜不到「' + 臂.名 + '」的可见结果行');
    await p.mouse.click(行.中心[0], 行.中心[1]);
    await p.waitForTimeout(3200);

    // 前提：落定自检（三连读）
    const 读1 = await 读缩放();
    await p.waitForTimeout(2600);
    const 读2 = await 读缩放();
    await p.waitForTimeout(2000);
    const 读3 = await 读缩放();
    记.读1 = 读1; 记.读2 = 读2; 记.读3 = 读3;
    记.落定 = (读1 === 读2 && 读2 === 读3);
    记.终点 = 读3;

    // 前提：点击生效自检
    const 选 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((x) => x.dataset.id));
    记.点击生效 = 选.includes(nid);
    if (!记.点击生效) throw new Error('点击未生效（选中=' + JSON.stringify(选) + '）');

    // 判据 P1：逐字判定
    记.差M宽 = +(记.终点 - 记.预测M宽).toFixed(6);
    记.差M高 = +(记.终点 - 记.预测M高).toFixed(6);
    const 中宽 = Math.abs(记.差M宽) < 1e-4;
    const 中高 = Math.abs(记.差M高) < 1e-4;
    记.命中 = (中宽 && 中高) ? 'M宽M高' : (中宽 ? 'M宽' : (中高 ? 'M高' : '无'));
    记.较基线动 = +(记.终点 - L0).toFixed(6);

    log(臂.键.padEnd(16) + '｜视口' + String(臂.vw + 'x' + 臂.vh).padEnd(10)
      + '｜z0=' + String(记.点之前).padEnd(7)
      + '｜落点=' + String(记.终点).padEnd(10)
      + '｜M宽=' + String(记.预测M宽).padEnd(10)
      + '｜M高=' + String(记.预测M高).padEnd(10)
      + '｜命中=' + 记.命中);
  } catch (e) {
    记.错误 = e.message;
    log(臂.键.padEnd(16) + '🔴 ' + e.message);
  } finally {
    try { if (p) await p.close(); } catch (e) { /* 忽略 */ }
    try { if (br) await br.close(); } catch (e) { /* 忽略 */ }
    out.臂.push(记);
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

// ───────── 判定 ─────────
const 好 = out.臂.filter((x) => !x.错误 && x.点击生效 && x.落定 && x.终点 !== undefined);
const 取 = (k) => 好.find((x) => x.键 === k);
const 判定P0 = 取('D1文本-对照')
  ? (Math.abs(取('D1文本-对照').终点 - 1.75) < 1e-6
    ? '✅ P0：文本臂落 ' + 取('D1文本-对照').终点 + ' ⇒ 尺子没漂，本批读数可用'
    : '🔴 P0：文本臂落 ' + 取('D1文本-对照').终点 + ' ≠ 1.75 ⇒ 本批读数作废')
  : '🔴 P0：文本臂无效';

const 基线ok = ['C1音频-基线', 'C2视频-基线'].map((k) => {
  const x = 取(k);
  if (!x) return { 键: k, ok: false, 说明: '无效' };
  const d = Math.abs(x.终点 - x.L0);
  return { 键: k, ok: d < 5e-5, 说明: '落 ' + x.终点 + '，批次 311 基线 ' + x.L0 + '，差 ' + d.toFixed(6) };
});

function 轴结论(kind, 高键, 宽键) {
  const g = 取(高键); const c = 取(宽键);
  if (!g || !c) return { kind, 结论: '🔴 臂不全，无法判定轴' };
  const 高的动 = Math.abs(g.较基线动) > 5e-5;
  const 宽的动 = Math.abs(c.较基线动) > 5e-5;
  if (高的动 && !宽的动) return { kind, 结论: '✅ 绑定**高度项**：只变高就动、只变宽不动（M高两臂逐字=' + g.命中 + '/' + c.命中 + '）', g, c };
  if (!高的动 && 宽的动) return { kind, 结论: '✅ 绑定**宽度项**：只变宽就动、只变高不动（M宽两臂逐字=' + g.命中 + '/' + c.命中 + '）', g, c };
  if (高的动 && 宽的动) return { kind, 结论: '⚠️ 两个方向都动 ⇒ 不是单一绑定轴；逐字命中 ' + g.命中 + '/' + c.命中 + '，需按 min 两项合看', g, c };
  return { kind, 结论: '🔴 两个视口下落点都不动 ⇒ **与视口无关**，是类型常量', g, c };
}

const 轴音频 = 轴结论('音频', 'A1音频-高变', 'A2音频-宽变');
const 轴视频 = 轴结论('视频', 'A3视频-高变', 'A4视频-宽变');
const 时间线臂 = 取('B1时间线-宽变');

const 都逐字 = [轴音频, 轴视频].map((x) => (x.g && x.c && (x.g.命中 === 'M宽' || x.g.命中 === 'M高')
  && (x.c.命中 === 'M宽' || x.c.命中 === 'M高')
  && x.g.命中 === x.c.命中 ? { kind: x.kind, ok: true, 命中: x.g.命中 } : { kind: x.kind, ok: false, 命中: (x.g && x.g.命中) + '/' + (x.c && x.c.命中) }));
const 切片 = 都逐字.filter((x) => x.ok).length;
const 判定P23 = 切片 === 2
  ? '✅ P2：音频、视频在两个视口下都**逐字命中同一模型**（音频 ' + 都逐字[0].命中 + '、视频 ' + 都逐字[1].命中 + '）⇒ 🔴 **批次 191 那张表是「(视口 − inset)/compound」在某个固定视口下的切片**，各 kind 一个 compound，不是独立类型常量'
  : (切片 === 0
    ? '🔴 P3：音频/视频两视口下都**不命中**同一模型（音频 ' + 都逐字[0].命中 + '、视频 ' + 都逐字[1].命中 + '）⇒ 🔴 **「191 那张表 = vs 切片」这条路被否**，落点另有机制'
    : '⚠️ P2/P3：只有 ' + 切片 + '/2 个 kind 两视口都逐字命中同一模型 ⇒ 不足以断言切片，也不足以否');

out.判定 = {
  有效臂: 好.length + '/' + 臂表.length,
  判定P0_阳性对照: 判定P0,
  基线复测: 基线ok,
  判定P1_逐臂: 好.map((x) => ({ 键: x.键, 视口: x.vw + 'x' + x.vh, 盒: x.画布盒, z0: x.点之前, 落点: x.终点, 预测M宽: x.预测M宽, 预测M高: x.预测M高, 命中: x.命中, 较基线动: x.较基线动 })),
  音频轴: 轴音频.结论,
  视频轴: 轴视频.结论,
  时间线窄视口: 时间线臂
    ? ('落 ' + 时间线臂.终点 + '｜M宽预测 ' + 时间线臂.预测M宽 + '｜M高预测 ' + 时间线臂.预测M高 + '｜命中 ' + 时间线臂.命中
      + '｜较基线动 ' + 时间线臂.较基线动
      + (时间线臂.命中 === 'M高' ? ' ⇒ 🔴 宽度项对时间线**不生效**，基线处两轴相等纯属巧合' : ''))
    : '（B1 臂无效）',
  判定P2P3_是否vs切片: 判定P23,
};
log('\n════ 判定 ════\n' + JSON.stringify(out.判定, null, 1));

// ───────── 末态独立复查（另一个浏览器实例） ─────────
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
  log('末态独立复查：' + JSON.stringify(out.末态));
} finally { try { await pz.close(); await brz.close(); } catch (e) { /* 忽略 */ } }

fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log('写入 ' + OUT);
process.exit(0);
/**
 * 批次 320 · 一刀分开「常数 inset」与「屏固定工具条」两个模型 —— 靠**判别式的符号**。
 *
 * 🔴 接批次 319：落点写成 `s · H₀ + a = safeH`，📌 音频的 `a`（画布像素）`204.27` / `215.52` / `202.74`（mean `≈207`），
 *    🔴 而**屏固定工具条**的画布尺寸**应该**是 `204 / s`（`s=1.07651` 时 `189.5`），📌 **差 `13.6%`** ⇒ 立规 198 的量级比对**没过**。
 *
 * 📌 **两个候选模型**（测量前写死）：
 *   **M常（常数 inset）**：`a = A_kind` 是**画布像素常数** ⇒ `s = (safeH − A) / H₀` ⇒ 📌 **总是有解**。
 *   **M屏（屏固定工具条）**：`a = T / s`（`T = 204` 屏像素）⇒ `H₀·s² − safeH·s + T = 0`
 *        ⇒ 📌 **判别式 `Δ = safeH² − 4·H₀·T`**
 *        🔴 **`safeH` 小于 `2√(H₀·T)` 时 `Δ < 0` ⇒ 这个模型在该视口下根本没有解**。
 *        📌 音频 `H₀ = 320`、`T = 204` ⇒ 临界 `safeH = 2√65280 = 511.0` ⇒ **`h < 671` 时 M屏无解**。
 *
 * 📌 **这就是本批的判别器**：📌 在 **`h ≤ 660`** 的几档上，
 *    ✅ **M常 有解且能预测；M屏 无解（`Δ < 0`）**
 *    ⇒ 📌 **只要音频在这些档上仍然落点，屏固定模型即被排除** —— 🔴 不需要比对值，**「有解/无解」就是判据**。
 *
 * 📌 **另一个独立的判别器（值层面）**：📌 M常 说 `a` 是**常数**；M屏 说 `a = 204/s`，📌 **落点越小 `a` 越大**。
 *    📌 批次 319 已有三个点，`a` 的极差只有 `6%` 而 `204/s` 的极差是 **`3.6×`**（`121.5` → `277`）
 *    ⇒ 📌 **值层面 M常 已占优**；📌 本批再加几档，把它压到能下判决的宽度。
 *
 * 📌 **判据（测量前写死）**：
 *   **P0** 阳性对照 `文本 @1212×680` 必须逐字落闭式 `1.625`；🔴 不中 ⇒ 本批作废。
 *   **P1（主判据）** 音频在 **`h ≤ 660`** 的档上**有落点** ⇒ 🔴 **M屏 被排除**（那个区间 `Δ < 0`）；
 *        🔴 若某档**落空**（`h` 够大、`Δ ≥ 0` 却不落）⇒ 📌 另找原因。
 *   **P2** 音频各档的 `a`（画布像素）**跨比 `< 1.15`** ⇒ ✅ M常 成立；📌 同时报 `204/s` 的跨比作对照。
 *   **P3** 视频各档的 `a` 同样报跨比 ⇒ 📌 若视频的 `A` 与音频的 `A` **逐字不同**，📌 那 `A` 就是 kind 专属的
 *        （📌 与批次 315 立规 194①「一个节点上的读数不能升格成 kind 的性质」区分开：📌 本批每档都用**同一节点**）。
 *
 * 前提检查：轴向自检 / 落定自检（三连读）/ 点击生效自检 /
 *   `aria` 精确匹配现找现量 / 参数写死 / 每臂独立浏览器 / 盒尺寸逐臂现量。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const STATE = `${process.env.HOME}/.jimeng-automation/state.json`;
const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b320.json';
const 放大键 = 'Meta+Equal';
const 闭式 = (w, h, W, H, z0) => Math.min((w - 532) / W, (h - 160) / H, z0);

/** 📌 屏固定工具条的屏高（批次 319 实测 `204`，与批次 304 的屏固定清单逐字吻合） */
const T = 204;

/** 📌 两个模型（测量前写死） */
const M常 = (safeH, H0, A) => (safeH - A) / H0;                       // 常数 inset（画布像素）
const M屏判别式 = (safeH, H0, t) => safeH * safeH - 4 * H0 * t;        // < 0 ⇒ 无实根
const M屏 = (safeH, H0, t) => {                                        // 取较小正根（落点应较小）
  const d = M屏判别式(safeH, H0, t);
  if (d < 0) return null;
  return (safeH - Math.sqrt(d)) / (2 * H0);
};

const 臂表 = [
  // 音频：h ≤ 660 的三档 ⇒ M屏 的 Δ < 0，主判据区间
  { 键: '音_h560', 组: '音', kind: '音频', 名: '音频 1', vw: 1212, vh: 560 },
  { 键: '音_h640', 组: '音', kind: '音频', 名: '音频 1', vw: 1212, vh: 640 },
  { 键: '音_h660', 组: '音', kind: '音频', 名: '音频 1', vw: 1212, vh: 660 },
  // 音频：h 更大的两档，扩 P2 的值域
  { 键: '音_h800', 组: '音', kind: '音频', 名: '音频 1', vw: 1212, vh: 800 },
  { 键: '音_h1000', 组: '音', kind: '音频', 名: '音频 1', vw: 1212, vh: 1000 },
  // 视频：同 kind 同一节点，扩 A 的 kind 对照
  { 键: '视_h640', 组: '视', kind: '视频', 名: '视频 1', vw: 1212, vh: 640 },
  { 键: '视_h800', 组: '视', kind: '视频', 名: '视频 1', vw: 1212, vh: 800 },
  { 键: '视_h1000', 组: '视', kind: '视频', 名: '视频 1', vw: 1212, vh: 1000 },
  // 阳性对照
  { 键: '文_h680', 组: '文', kind: '文本', 名: '文本 1', vw: 1212, vh: 680, 期望: 1.625 },
];

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b320',
  问: '落点里的那份额是「常数画布 inset」还是「屏固定工具条的 204/s」？用判别式的符号一刀分开',
  接批次319: {
    音频a画布: { h600: 204.27, h720: 215.52, h900: 202.74 },
    M屏应给的: { h600: '204/0.736662 = 276.9', h720: '204/1.076510 = 189.6', h900: '204/1.678950 = 121.6' },
    差: 'M屏 应给值跨 3.6×，实测 a 跨 1.06× ⇒ 值层面 M常 已占优，但批次 319 没下判决（立规 198 要求量级闭合）',
  },
  模型: {
    M常: 'a = A_kind（画布像素常数）⇒ s = (safeH − A)/H0，总有解',
    M屏: 'a = T/s（T=204 屏像素）⇒ H0·s² − safeH·s + T = 0；Δ = safeH² − 4·H0·T；Δ<0 ⇒ 无实根',
    临界: '音频 H0=320、T=204 ⇒ 临界 safeH = 2√65280 = 511.0 ⇒ h < 671 时 M屏 无解',
  },
  判据: {
    P0: '阳性对照 文本 @1212×680 必须逐字落闭式 1.625，不中即本批作废',
    P1: '主判据：音频在 h ≤ 660 的档上（Δ<0，M屏 无解）仍有落点 ⇒ M屏 被排除',
    P2: '音频各档 a（画布像素）跨比 < 1.15 ⇒ M常 成立；同时报 204/s 的跨比作对照',
    P3: '视频各档 a 的跨比；并与音频的 A 对撞，判 A 是否 kind 专属',
  },
  臂表, 臂: [], 判定: {},
};

for (const 臂 of 臂表) {
  let br = null; let p = null; let nid = null;
  const 记 = { 键: 臂.键, 组: 臂.组, kind: 臂.kind, 名: 臂.名, vw: 臂.vw, vh: 臂.vh };
  try {
    br = await chromium.launch({ headless: true });
    const ctx = await br.newContext({ storageState: STATE, viewport: { width: 臂.vw, height: 臂.vh } });
    p = await ctx.newPage();
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 60000 });
    await p.waitForTimeout(6000);

    const 实际 = await p.evaluate(() => ({ w: innerWidth, h: innerHeight }));
    if (实际.w !== 臂.vw || 实际.h !== 臂.vh) throw new Error('轴向自检失败：' + 实际.w + 'x' + 实际.h);
    if (实际.h < 249) throw new Error('视口高不足 249');

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
    // 🔴 门槛按「本臂预期」写：这一批预期落点最高 1.98 ⇒ 只查它高于预期，且预期低的臂不能被它误杀
    记.safeH = 臂.vh - 160;
    记.闭式预测 = +闭式(臂.vw, 臂.vh, 目标.W, 目标.H, 记.点之前).toFixed(6);
    if (记.闭式预测 >= 记.点之前) 记.可能被第三项截顶 = true;

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

    const 读1 = await 读缩放();
    await p.waitForTimeout(2600);
    const 读2 = await 读缩放();
    await p.waitForTimeout(2000);
    const 读3 = await 读缩放();
    记.读1 = 读1; 记.读2 = 读2; 记.读3 = 读3;
    记.落定 = (读1 === 读2 && 读2 === 读3);
    记.终点 = 读3;

    const 选 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((x) => x.dataset.id));
    记.点击生效 = 选.includes(nid);
    if (!记.点击生效) throw new Error('点击未生效（选中=' + JSON.stringify(选) + '）');

    if (臂.期望 !== undefined) 记.命中期望 = Math.abs(记.终点 - 臂.期望) < 5e-6;

    // 📌 两个模型的预测（测量前算好，不许事后拟合）
    记.M屏判别式 = +M屏判别式(记.safeH, 目标.H, T).toFixed(2);
    记.M屏有无解 = 记.M屏判别式 < 0;
    记.M屏预测 = M屏(记.safeH, 目标.H, T);
    // 📌 反解出的常数 inset（若落点就是 M常，则这个值应当跨档几乎不变）
    记.a实测 = +((记.safeH - 目标.H * 记.终点)).toFixed(3);
    记.M屏应给的a = +(T / 记.终点).toFixed(3);

    log(臂.键.padEnd(9) + '｜视口' + String(臂.vw + 'x' + 臂.vh).padEnd(10)
      + '｜z0=' + String(记.点之前).padEnd(8)
      + '｜落点=' + String(记.终点).padEnd(10)
      + '｜a实测=' + String(记.a实测).padStart(8)
      + '｜M屏应给a=' + String(记.M屏应给的a).padStart(8)
      + '｜M屏Δ=' + String(记.M屏判别式).padStart(10)
      + (记.M屏有无解 ? '｜🔴无解' : '｜有解'));
  } catch (e) {
    记.错误 = e.message;
    log(臂.键.padEnd(9) + '🔴 ' + e.message);
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
const 音 = 好.filter((x) => x.组 === '音').sort((a, b) => a.vh - b.vh);
const 视 = 好.filter((x) => x.组 === '视').sort((a, b) => a.vh - b.vh);
const 文 = 取('文_h680');

const 判定P0 = 文 && 文.命中期望
  ? '✅ P0：阳性对照 `文本 @1212×680` 落 ' + 文.终点 + '（期望 1.625）逐字 ⇒ 尺子没漂'
  : '🔴 P0：阳性对照=' + (文 ? 文.终点 : '—') + '（期望 1.625）⇒ 本批作废';

const 无解档 = 音.filter((x) => x.M屏有无解);
const 有解档 = 音.filter((x) => !x.M屏有无解);
const 判定P1 = 无解档.length === 0 ? '（没有 Δ<0 的音频臂）'
  : ('✅ P1（主判据）：音频在 **' + 无解档.length + ' 档 `Δ<0` 的视口**（M屏 判别式为负 ⇒ 屏固定模型**根本没有实根**）上'
    + '**仍然有落点** —— ' + 无解档.map((x) => x.键 + '(h=' + x.vh + ', Δ=' + x.M屏判别式 + ')→' + x.终点).join('、')
    + ' ⇒ 🔴 **M屏（屏固定工具条直接构成 compound）被排除**；📌 M屏 在 `' + 有解档.map((x) => 'h=' + x.vh).join('/') + '` 上**有解**，'
    + '📌 但那几档的实测 `a` 与它的预测也对不上（见 P2）');

function 跨比(组, 键名) {
  const v = 组.map((x) => x[键名]).filter((z) => typeof z === 'number');
  if (v.length < 2) return null;
  return +(Math.max.apply(null, v) / Math.min.apply(null, v)).toFixed(4);
}
const a跨 = 跨比(音, 'a实测');
const M跨 = 跨比(音, 'M屏应给的a');
const 判定P2 = a跨 === null ? '（音频臂不足）'
  : ('📌 P2：音频各档 `a`（画布像素）= ' + 音.map((x) => x.键 + '=' + x.a实测).join('、')
    + '｜**跨比 `' + a跨 + '`**'
    + '｜对照「M屏 应给的 `204/s`」跨比 `' + M跨 + '`'
    + '（' + 音.map((x) => x.M屏应给的a).join('/') + '）'
    + ' ⇒ ' + (a跨 < 1.15
      ? '✅ **M常 成立：`a` 是画布像素常数**；🔴 **M屏 的跨比大 ' + (M跨 / a跨).toFixed(1) + ' 倍**'
        + ' ⇒ 📌 那份额是**画布空间的常数 inset**，🔴 **不是屏固定装饰的 `屏尺寸/落点`**'
      : '⚠️ `a` 的跨比 `' + a跨 + '` 不小 ⇒ 常数 inset 模型也存疑'));

const v跨 = 跨比(视, 'a实测');
const 音A = 音.length ? 音.reduce((s, x) => s + x.a实测, 0) / 音.length : null;
const 视A = 视.length ? 视.reduce((s, x) => s + x.a实测, 0) / 视.length : null;
const 判定P3 = !视.length || !音.length ? '（臂不全）'
  : ('📌 P3：视频各档 `a` = ' + 视.map((x) => x.键 + '=' + x.a实测).join('、') + '｜跨比 `' + v跨 + '`'
    + '｜均值：音频 `' + (音A !== null ? 音A.toFixed(2) : '—') + '`、视频 `' + (视A !== null ? 视A.toFixed(2) : '—') + '`'
    + ' ⇒ ' + (Math.abs(视A - 音A) / 音A < 0.05
      ? '✅ **两个 kind 的 `A` 逐字接近** ⇒ 📌 `A` 是**画布级**的量，不是 kind 专属'
      : '⚠️ 两个 kind 的 `A` 差 ' + (Math.abs(视A - 音A) / 音A * 100).toFixed(1) + '% ⇒ 📌 `A` **kind 专属**；'
        + '📌 注意 📌 **每档都用同一节点**（`音频 1` / `视频 1`），📌 所以这不是立规 194① 那个「单节点升格成 kind 性质」的坑'));

out.判定 = {
  有效臂: 好.length + '/' + 臂表.length,
  判定P0_尺子: 判定P0,
  判定P1_主判据_判别式: 判定P1,
  判定P2_值层面: 判定P2,
  判定P3_kind对照: 判定P3,
  跨比: { 音频a实测: a跨, 音频M屏应给: M跨, 视频a实测: v跨 },
  逐臂: 好.map((x) => ({ 键: x.键, 名: x.名, 视口: x.vw + 'x' + x.vh, safeH: x.safeH, 盒: x.画布盒, z0: x.点之前, 落点: x.终点, a实测: x.a实测, M屏应给的a: x.M屏应给的a, M屏判别式: x.M屏判别式, M屏有无解: x.M屏有无解 })),
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
  log('末态独立复查：' + JSON.stringify(out.末态));
} finally { try { await pz.close(); await brz.close(); } catch (e) { /* 忽略 */ } }

fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log('写入 ' + OUT);
process.exit(0);
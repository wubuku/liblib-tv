/**
 * 批次 322 · 「`A ≈ 209`」这个说法本身可能就是错的 —— 检验 `A` 到底是常数、还是被 `204` 从下方截断的分布。
 *
 * 🔴 接批次 321：321 合并 `n = 16` 报出 `A` 均值 `210.298`、标准误 `0.974`，
 *    并据此判「`A = 204` 可排除（`z = −6.47`）」⇒ 📌 **321 的 P1 判决是范畴错误，本批要推翻它。**
 *
 * 📌 **先算出来的事实（零浏览器成本，纯复算 b321 的 16 条读数）**：
 *    把 `A = 560 − 320·s` 对全部 `16` 条排序后：
 *      `204.013 / 204.042 / 204.269 / 206.362 / 209.258 / 209.603 / 210.390 / 211.069 /`
 *      `211.133 / 211.475 / 211.475 / 211.898 / 213.610 / 215.050 / 215.517 / 215.610`
 *    ⇒ ✅ **`A < 204` 的条数是 `0`；`A` 的最小值 `204.013`；`A < 204.5` 的只有 `3` 条且挤在最下面。**
 *    ⇒ 🔴 **`204` 不是分布内部的一个竞争点，而是分布的**下边界** ⇒ 分布是**左截断**的，均值被右尾拉高。**
 *    ⇒ 🔴 **拿均值对一个边界值做 z 检验没有意义**（321 P1 的错就在这里）。
 *    ⇒ 📌 而且最贴边的两条对得上闭式：`(560 − 204)/320 = 1.112500`，
 *        实测 `1.11246`（差 `−4.0e−05`）、`1.11237`（差 `−1.3e−04`）⇒ ✅ **这不像巧合。**
 *
 * 📌 **由此得到的完整闭式（本批要验它）**：
 *    **落点 `= (safeH − 204)/320`，即 `A ≡ 204 = 音频工具条的屏高`（批次 319 测得 `node-toolbar` 是 `680×204` 屏固定）。**
 *    推论：**竖向堆叠 `320·s + 204` 恰好填满可用高度 `safeH`；节点与工具条一起瓜分这条带。**
 *
 * 📌 **顺带解释了批次 314 的开关**：`safeW = w − 532`，`w ≤ 1210 ⇒ safeW ≤ 678 < 680`（工具条屏宽装不下）
 *    ⇒ 落点退回朴素闭式 `1.75`（工具条溢出不管）；`w ≥ 1212 ⇒ safeW ≥ 680`（工具条装得下）
 *    ⇒ 开始给它留 `204` 的竖向份额。📌 **那开关的阈值应当正好是 `safeW = 680 = 工具条屏宽`** ⇒ 🔴 **本批必须补测 `w = 1211`**
 *    （`safeW = 679 < 680`）——它若落 `1.75` 而 `w = 1212` 落 `1.1125`，开关就被钉死在 `680` 上。
 *
 * 🔴 **三个竞争模型，判据在测量前写死**（`safeH = h − 160`，`H0 = 320`）：
 *   **M1「竖向堆叠」** `A ≡ 204`（与 `safeH`、`safeW` 都无关）⇒ 各 `h` 上 `A` 的极差 `≤ 1.0` 且 `|A − 204| ≤ 1.0`。
 *   **M2「固定内容高 `T`」** `A = safeH · T/(H0+T) = 0.375532·safeH`（`A` 与 `safeH` 成正比）⇒
 *        `h=640→180.26`、`h=680→195.28`、`h=760→225.32`、`h=800→240.34`。
 *   **M3「横竖混合」** `A` 随 `safeW` 变 ⇒ `w` 扫上 `A` 的极差 `> 1.0`。
 *   🔴 M1 与 M2 在 `h = 720` 上就差 `6.3`（`204` vs `210.30`），超过两条判据各自的容差 ⇒ ✅ **可判别**。
 *
 * 📌 **判据（测量前写死）**：
 *   **P0** 阳性对照 `文本 @1212×720` 必须逐字落 `1.75`；🔴 不中 ⇒ 本批作废。
 *   **P1** `h` 扫上 `A` 的极差 `≤ 1.0` **且** `|A − 204| ≤ 1.0` ⇒ ✅ **M1 成立，真值 `= 204 = 工具条屏高`**。
 *   **P2** `h` 扫上 `A` 与 `0.375532·safeH` 的偏差全部 `≤ 5` ⇒ ✅ **M2 成立，`A` 是随 `safeH` 线性长的**。
 *   **P3** 逐臂报 `A`、工具条屏高 `R`、`gap = A − R`；`gap` 的极差 `≤ 2` ⇒ ✅ **`A ≡ R`（逐臂恒等式）**。
 *   **P4** `w` 扫上 `A` 的极差 `≤ 1.0` ⇒ ✅ **`A` 与 `safeW` 无关**（排掉 M3）。
 *   **P5** 逐臂报「竖向堆叠 `节点屏高 + R`」与 `safeH` 的差；差 `≤ 2` ⇒ ✅ **堆叠恰好填满可用高度**。
 *   **P6** `w ≤ 1211` 的臂必须逐字命中闭式 `1.75`（`A` 恒为 `0`）；🔴 不中 ⇒ 尺子漂。
 *
 * 前提检查：轴向自检 / 落定自检（三连读）/ 点击生效自检 /
 *   `aria` 精确匹配现找现量 / 参数写死 / 每臂独立浏览器 / 盒尺寸逐臂现量。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const STATE = `${process.env.HOME}/.jimeng-automation/state.json`;
const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b322.json';
const 放大键 = 'Meta+Equal';
const 闭式 = (w, h, W, H, z0) => Math.min((w - 532) / W, (h - 160) / H, z0);
const H0 = 320;
const M1常数 = 204;
const M2斜率 = 0.375532;

/** 📌 采集：只取本臂要用的三个屏盒 + 选中态，逐臂现量。 */
const 采集 = () => {
  const 矩形 = (e) => {
    if (!e) return null;
    const b = e.getBoundingClientRect();
    return {
      x: Math.round(b.x * 10) / 10, y: Math.round(b.y * 10) / 10,
      w: Math.round(b.width * 10) / 10, h: Math.round(b.height * 10) / 10,
    };
  };
  const 节点 = Array.from(document.querySelectorAll('.react-flow__node[data-id]'))
    .find((x) => x.getAttribute('aria-label') === window.__找的aria);
  const 全体 = Array.from(document.querySelectorAll('[data-testid]'));
  const 取最大 = (tid) => {
    const c = 全体.filter((x) => x.getAttribute('data-testid') === tid)
      .map(矩形)
      .filter(Boolean)
      .filter((r) => r.w > 0 && r.h > 0);
    if (!c.length) return null;
    return c.reduce((p, q) => (q.w * q.h > p.w * p.h ? q : p));
  };
  return {
    节点屏盒: 矩形(节点),
    工具条: 取最大('node-toolbar'),
    生成表单: 取最大('audio-generation-form'),
    工具条宿主: 取最大('node-toolbar-feature-host'),
    选中: Array.from(document.querySelectorAll('.react-flow__node.selected')).map((x) => x.dataset.id),
  };
};

const 臂表 = [
  // P1/P2：h 扫（w 固定 1212）
  { 键: 'h640', 组: 'hsweep', kind: '音频', 名: '音频 1', vw: 1212, vh: 640 },
  { 键: 'h680', 组: 'hsweep', kind: '音频', 名: '音频 1', vw: 1212, vh: 680 },
  { 键: 'h720', 组: 'hsweep|wsweep', kind: '音频', 名: '音频 1', vw: 1212, vh: 720 },
  { 键: 'h760', 组: 'hsweep', kind: '音频', 名: '音频 1', vw: 1212, vh: 760 },
  { 键: 'h800', 组: 'hsweep', kind: '音频', 名: '音频 1', vw: 1212, vh: 800 },
  // P4/P6：w 扫（h 固定 720）—— 🔴 必须含 1211，把开关钉在 safeW=680 上
  { 键: 'w1206', 组: 'wsweep', kind: '音频', 名: '音频 1', vw: 1206, vh: 720 },
  { 键: 'w1210', 组: 'wsweep', kind: '音频', 名: '音频 1', vw: 1210, vh: 720 },
  { 键: 'w1211', 组: 'wsweep', kind: '音频', 名: '音频 1', vw: 1211, vh: 720 },
  { 键: 'w1216', 组: 'wsweep', kind: '音频', 名: '音频 1', vw: 1216, vh: 720 },
  { 键: 'w1220', 组: 'wsweep', kind: '音频', 名: '音频 1', vw: 1220, vh: 720 },
  { 键: 'w1230', 组: 'wsweep', kind: '音频', 名: '音频 1', vw: 1230, vh: 720 },
  { 键: 'w1250', 组: 'wsweep', kind: '音频', 名: '音频 1', vw: 1250, vh: 720 },
  // 阳性对照
  { 键: 'W_1', 组: '对照', kind: '文本', 名: '文本 1', vw: 1212, vh: 720, 期望: 1.75 },
];

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b322',
  问: 'A 是常数，还是被 204 从下方截断的分布？批次 321 的「A=204 可排除」是不是范畴错误？',
  复算_零浏览器成本: {
    来源: 'b321 落盘的 16 条读数（历史 10 + 本批 6），全部 音频 1 @1212×720',
    A升序: '204.013 / 204.042 / 204.269 / 206.362 / 209.258 / 209.603 / 210.390 / 211.069 / 211.133 / 211.475 / 211.475 / 211.898 / 213.610 / 215.050 / 215.517 / 215.610',
    小于204的条数: 0,
    最小值: 204.013,
    闭式上盖: '(560 − 204)/320 = 1.112500',
    最贴边的两条: 's=1.11246（差 −4.0e−05）、s=1.11237（差 −1.3e−04）',
    结论: '🔴 A 的分布是**左截断**的，204 是边界不是竞争点 ⇒ 321 P1 的 z 检验是范畴错误',
  },
  假说: {
    M1: 'A ≡ 204（竖向堆叠：320·s + 204 填满 safeH），与 safeH、safeW 都无关',
    M2: 'A = 0.375532·safeH（固定内容高 T，A 与 safeH 成正比）：h=640→180.26、h=680→195.28、h=720→210.30、h=760→225.32、h=800→240.34',
    M3: 'A 随 safeW 变',
    开关说: 'safeW ≥ 680（= 工具条屏宽）才开始给工具条留 204；故 w=1211 应落闭式 1.75、w=1212 应落 1.1125',
  },
  判据: {
    P0: '阳性对照 文本 @1212×720 必须逐字落 1.75，不中即本批作废',
    P1: 'h 扫上 A 的极差 ≤ 1.0 且 |A−204| ≤ 1.0 ⇒ M1 成立、真值 = 204 = 工具条屏高',
    P2: 'h 扫上 A 与 0.375532·safeH 的偏差全部 ≤ 5 ⇒ M2 成立',
    P3: '逐臂报 A、工具条屏高 R、gap=A−R；gap 极差 ≤ 2 ⇒ A ≡ R',
    P4: 'w 扫上 A 的极差 ≤ 1.0 ⇒ A 与 safeW 无关（排掉 M3）',
    P5: '逐臂报「节点屏高 + R」与 safeH 的差；差 ≤ 2 ⇒ 堆叠恰好填满可用高度',
    P6: 'w ≤ 1211 的臂必须逐字命中闭式 1.75（A 恒为 0）',
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
    if (臂.vh < 249) throw new Error('视口高不足 249');

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

    记.闭式预测 = +闭式(臂.vw, 臂.vh, 目标.W, 目标.H, 记.点之前).toFixed(6);
    记.命中闭式 = Math.abs(记.终点 - 记.闭式预测) < 5e-5;
    if (臂.期望 !== undefined) 记.命中期望 = Math.abs(记.终点 - 臂.期望) < 5e-6;

    await p.evaluate((aria) => { window.__找的aria = aria; }, ariaWant);
    const 清 = await p.evaluate(采集);
    记.屏盒 = 清;
    记.选中含目标 = 清.选中.includes(nid);
    if (!记.选中含目标) throw new Error('点击未生效（选中=' + JSON.stringify(清.选中) + '）');

    const safeH = 臂.vh - 160;
    const safeW = 臂.vw - 532;
    记.safeH = safeH; 记.safeW = safeW;
    记.A = +(safeH - H0 * 记.终点).toFixed(3);
    记.M1预测 = M1常数;
    记.M2预测 = +(M2斜率 * safeH).toFixed(2);
    记.上盖预测 = +((safeH - M1常数) / H0).toFixed(5);
    const 工具条屏高 = 清.工具条 ? 清.工具条.h : null;
    记.工具条屏高 = 工具条屏高;
    记.gap = 工具条屏高 === null ? null : +(记.A - 工具条屏高).toFixed(2);
    记.节点屏高 = 清.节点屏盒 ? 清.节点屏盒.h : null;
    记.节点屏高与320倍落点之差 = 清.节点屏盒 ? +Math.abs(清.节点屏盒.h - H0 * 记.终点).toFixed(2) : null;
    记.堆叠 = 工具条屏高 === null || !清.节点屏盒 ? null : +(清.节点屏盒.h + 工具条屏高).toFixed(2);
    记.堆叠减safeH = 记.堆叠 === null ? null : +(记.堆叠 - safeH).toFixed(2);

    log(臂.键.padEnd(7) + '｜视口' + String(臂.vw + 'x' + 臂.vh).padEnd(10)
      + '｜z0=' + String(记.点之前).padEnd(8)
      + '｜落点=' + String(记.终点).padEnd(10)
      + (记.命中闭式 ? '｜✅闭式' : '｜🔴不中')
      + '｜A=' + String(记.A).padEnd(9)
      + '｜工具条屏高=' + String(工具条屏高).padEnd(8)
      + '｜gap=' + String(记.gap).padEnd(8)
      + '｜堆叠−safeH=' + String(记.堆叠减safeH));
  } catch (e) {
    记.错误 = e.message;
    log(臂.键.padEnd(7) + '🔴 ' + e.message);
  } finally {
    try { if (p) await p.close(); } catch (e) { /* 忽略 */ }
    try { if (br) await br.close(); } catch (e) { /* 忽略 */ }
    out.臂.push(记);
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

// ───────── 判定 ─────────
const 好 = out.臂.filter((x) => !x.错误 && x.选中含目标 && x.落定 && x.终点 !== undefined);
const 取 = (k) => 好.find((x) => x.键 === k);
const 极差 = (arr) => (arr.length ? +(Math.max.apply(null, arr) - Math.min.apply(null, arr)).toFixed(3) : null);
const 在组 = (g) => 好.filter((x) => x.组.split('|').indexOf(g) >= 0);

const 对照 = 取('W_1');
const 判定P0 = 对照 && 对照.命中期望
  ? '✅ P0：阳性对照 `文本 @1212×720` 落 `' + 对照.终点 + '` 逐字等于闭式 `1.75` ⇒ 尺子没漂'
  : '🔴 P0：阳性对照=' + (对照 ? 对照.终点 : '—') + '（期望 1.75）⇒ 本批作废';

const 音 = 好.filter((x) => x.kind === '音频');
const h组 = 在组('hsweep').filter((x) => x.kind === '音频');
const w组 = 在组('wsweep').filter((x) => x.kind === '音频');
const 好区 = w组.filter((x) => x.vw <= 1211);
const 坏区 = w组.filter((x) => x.vw >= 1212);

const hA = h组.map((x) => x.A).filter((x) => typeof x === 'number');
const 判定P1 = (hA.length >= 4 && 极差(hA) !== null && 极差(hA) <= 1.0 && hA.every((a) => Math.abs(a - M1常数) <= 1.0))
  ? '✅ P1：`h` 扫 `n = ' + hA.length + '` 的 `A` 极差 `' + 极差(hA) + '`（≤ 1.0）且逐条 `|A − 204| ≤ 1.0`'
    + ' ⇒ ✅ **M1 成立：`A ≡ 204 = 工具条屏高`，与 `safeH` 无关** ⇒ 📌 **`A ≈ 209` 这个说法作废，真值就是 `204`**'
  : '📌 P1：`h` 扫 `n = ' + hA.length + '` 的 `A` 极差 `' + 极差(hA) + '`，逐条 A = [' + hA.join(', ') + ']'
    + ' ⇒ ' + (极差(hA) !== null && 极差(hA) <= 1.0
      ? '⚠️ 极差达标但不是 204 ⇒ A 是别的常数'
      : '🔴 极差 > 1.0 ⇒ `A` 随 `safeH` 变，**M1 被否**');

const M2偏差 = h组.map((x) => ({ 键: x.键, h: x.vh, A: x.A, 预测: x.M2预测, 差: +Math.abs(x.A - x.M2预测).toFixed(2) }));
const 判定P2 = (M2偏差.length >= 4 && M2偏差.every((x) => x.差 <= 5))
  ? '✅ P2：`h` 扫上 `A` 与 `0.375532·safeH` 的偏差逐条 ≤ 5（最大 `' + Math.max.apply(null, M2偏差.map((x) => x.差)) + '`）⇒ ✅ **M2 成立，`A` 随 `safeH` 线性长**'
  : '📌 P2：M2 偏差逐条 = ' + M2偏差.map((x) => x.键 + ':' + x.差).join('、') + ' ⇒ 🔴 **M2 被否**';

const 有工具条的 = 音.filter((x) => typeof x.gap === 'number');
const g集 = 有工具条的.map((x) => x.gap);
const 判定P3 = !g集.length
  ? '（没量到工具条屏盒）'
  : ('📌 P3：逐臂 `A` / 工具条屏高 `R` / `gap = A − R` ⇒ gap 极差 `' + 极差(g集) + '`'
    + ' ⇒ ' + (极差(g集) <= 2
      ? '✅ **`A ≡ R` 逐臂恒等** ⇒ 「那份额就是工具条的屏高」得到逐臂确认'
      : '🔴 **`A ≠ R`** ⇒ 工具条之外还有别的份额，gap 逐条 = ' + 有工具条的.map((x) => x.键 + ':' + x.gap).join('、')));

const wA = 坏区.map((x) => x.A).filter((x) => typeof x === 'number');
const 判定P4 = (!wA.length) ? '（坏区臂不全）'
  : ('📌 P4：`w ≥ 1212` 的 `n = ' + wA.length + '` 条，`A` 极差 `' + 极差(wA) + '` ⇒ '
    + (极差(wA) <= 1.0 ? '✅ **`A` 与 `safeW` 无关** ⇒ M3 被否' : '🔴 **`A` 随 `safeW` 变** ⇒ M3 存活'));

const 堆差 = 音.filter((x) => typeof x.堆叠减safeH === 'number').map((x) => x.堆叠减safeH);
const 判定P5 = !堆差.length
  ? '（没量到堆叠）'
  : ('📌 P5：「节点屏高 `320·s` + 工具条屏高 `R`」与 `safeH` 的差逐条 = [' + 堆差.join(', ') + ']'
    + ' ⇒ ' + (Math.max.apply(null, 堆差.map(Math.abs)) <= 2
      ? '✅ **竖向堆叠恰好填满可用高度** ⇒ 闭式 `s = (safeH − 204)/320` 得到几何确认'
      : '🔴 **堆叠没填满 `safeH`** ⇒ 闭式的几何解释被否'));

const 判定P6 = !好区.length ? '（好区臂不全）'
  : ('📌 P6：`w ≤ 1211` 的臂 = ' + 好区.map((x) => x.键 + '(w=' + x.vw + ',safeW=' + x.safeW + ')→' + x.终点 + (x.命中闭式 ? '✅' : '🔴')).join('、')
    + ' ⇒ ' + (好区.every((x) => x.命中闭式) ? '✅ **全部逐字命中闭式 `1.75`（`A ≡ 0`）** ⇒ 开关在 `safeW` 跨过 `680` 的那一侧' : '🔴 有臂不中闭式 ⇒ 尺子漂或开关位置与本批假设不同'));

const 开关 = 取('w1211') && 取('w1212')
  ? '📌 开关定位：`w = 1211`（`safeW = 679`）落 `' + 取('w1211').终点 + '`；`w = 1212`（`safeW = 680`）落 `' + 取('w1212').终点 + '` ⇒ '
    + (取('w1211').命中闭式 && !取('w1212').命中闭式
      ? '✅ **开关正好卡在 `safeW = 680 = 工具条屏宽`** ⇒ 「工具条装得下才开始给它留份额」成立'
      : '📌 开关不在 `safeW = 680` 处 ⇒ 与本批假设不符')
  : '（1211/1212 臂不全，开关未定位）';

out.判定 = {
  有效臂: 好.length + '/' + 臂表.length,
  判定P0_尺子: 判定P0,
  判定P1_A是不是204: 判定P1,
  判定P2_是否随safeH线性: 判定P2,
  判定P3_是否就是工具条: 判定P3,
  判定P4_是否随safeW变: 判定P4,
  判定P5_堆叠是否填满: 判定P5,
  判定P6_好区是否命中闭式: 判定P6,
  开关定位: 开关,
  逐臂: 好.map((x) => ({
    键: x.键, 名: x.名, 视口: x.vw + 'x' + x.vh, safeW: x.safeW, safeH: x.safeH,
    z0: x.点之前, 落点: x.终点, 闭式预测: x.闭式预测, 命中闭式: x.命中闭式,
    A: x.A, M1预测: x.M1预测, M2预测: x.M2预测, 上盖预测: x.上盖预测,
    工具条屏高: x.工具条屏高, gap: x.gap, 节点屏高: x.节点屏高,
    节点屏高与320倍落点之差: x.节点屏高与320倍落点之差, 堆叠减safeH: x.堆叠减safeH,
  })),
  失效臂: out.臂.filter((x) => x.错误).map((x) => ({ 键: x.键, 错: x.错误 })),
};
log('\n════ 判定 ════\n' + JSON.stringify({
  有效臂: out.判定.有效臂, P0: 判定P0, P1: 判定P1, P2: 判定P2,
  P3: 判定P3, P4: 判定P4, P5: 判定P5, P6: 判定P6, 开关: 开关,
}, null, 1));

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

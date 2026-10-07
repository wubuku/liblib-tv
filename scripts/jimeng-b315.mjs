/**
 * 批次 315 · 那个 `w ∈ (1210, 1212]` 的开关，是**视口的**还是**这个节点的**？
 *
 * 🔴 接批次 314（`31` 条读数，四轮）：`音频 1` 与 `视频 1` 在 `w ≤ 1210` 逐字命中批次 306 闭式、
 *    在 `w = 1212` 全部不中；`文本`/`时间线` 在 `w = 1212` 仍逐字命中。
 *    ⇒ ⚠️ **本批要回答三个批次 314 自己列下、但没测的缺口**：
 *
 * 📌 **Q1 开关跟着谁走？**
 *    🔴 批次 314 用的**音频只有一个节点（`音频 1`）** ⇒ 📌 **「音频这个 kind 有开关」**
 *       与「**这一个节点**恰好有开关」**在本批之前分不开**（同批次 311 踩过的同款：样本量 1 不要外推）。
 *       ⇒ 本批换**同 kind 的另外两个节点**（`音频 2`、`音频 68`，本画布共有 `68` 个音频节点）：
 *         **若另两个节点也在 `w=1212` 掉下去** ⇒ ✅ **开关是视口的，不是节点的**；
 *         **若它们照常命中** ⇒ 🔴 **是节点属性**，批次 314 的结论要收窄到「`音频 1`/`视频 1` 这两个节点」。
 *
 * 📌 **Q2 开关和视口高有关吗？**
 *    📌 批次 314 的阈值是在 `h = 720` 这一行上夹出来的 ⇒ 🔴 **`h ≠ 720` 时它还在不在 `1210/1212` 之间，没测过**。
 *    ⇒ `音频 1 @ 1200×600`（闭式 `1.375`）：**命中 ⇒ 开关只认 `w`**；**不中 ⇒ 它是 `(w,h)` 的交互**。
 *
 * 📌 **Q3 散布是节点自己的，还是这一行的？**
 *    📌 批次 314 测出坏区散布 `音频 2.07%` / `视频 0.94%` ⇒ 📌 **`音频 2` 自己的散布是多少，没人知道**
 *       （**不同节点的散布不可互相代入**，立规 193⑤）。
 *    ⇒ `音频 2 @ 1212×720` **测两遍**，与 `音频 1` 的 `2.07%` 并排比。
 *
 * 📌 **Q4 尺子（阳性对照）**：`文本 1 @ 1210×720` 必须落 `1.75`、
 *    `时间线 1 @ 1210×720` 必须落 `0.566667` ⇒ 📌 这两条**还没在 `w=1210` 上测过**，
 *    📌 它们是本批判定「好区判定标准没有漂」的锚（立规 189）。
 *
 * 📌 **判据（测量前写死）**：
 *   **P0** Q4 两条逐字命中，否则整批作废。
 *   **P1** `音频 2` 与 `音频 68` 在 `w=1210` **命中** 且在 `w=1212` **不中**
 *        ⇒ ✅ **开关属于视口**（Q1）；任一节点在 `1212` 仍命中 ⇒ 🔴 **开关属于节点**（Q1 反面）。
 *   **P2** `音频 1 @ 1200×600` 命中闭式 `1.375` ⇒ ✅ **开关只认 `w`**；不中 ⇒ 🔴 **是 `(w,h)` 交互**。
 *   **P3** `音频 2` 自身两遍的差，与 `音频 1` 的 `2.07%` 并排，📌 **只报数、不合并**（立规 193⑤）。
 *
 * 前提检查：轴向自检 / 落定自检（三连读）/ 点击生效自检 /
 *   `aria` 精确匹配现找现量 / 参数写死 / 每臂独立浏览器 / 盒尺寸逐臂现量。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const STATE = `${process.env.HOME}/.jimeng-automation/state.json`;
const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b315.json';
const 放大键 = 'Meta+Equal';
/** 📌 批次 306 闭式：分母取**布局盒**，inset 写死在减数上。本批用它【预测】，不反推。 */
const 闭式 = (w, h, W, H, z0) => Math.min((w - 532) / W, (h - 160) / H, z0);

const 臂表 = [
  // Q1 换同 kind 的另外两个节点，各测阈值两侧
  { 键: 'X2_1210', 组: 'Q1', kind: '音频', 名: '音频 2', vw: 1210, vh: 720, 按: 13 },
  { 键: 'X2_1212甲', 组: 'Q1', kind: '音频', 名: '音频 2', vw: 1212, vh: 720, 按: 13 },
  { 键: 'X68_1210', 组: 'Q1', kind: '音频', 名: '音频 68', vw: 1210, vh: 720, 按: 13 },
  { 键: 'X68_1212', 组: 'Q1', kind: '音频', 名: '音频 68', vw: 1212, vh: 720, 按: 13 },
  // Q2 换视口高，看开关还在不在
  { 键: 'Y1_1200x600', 组: 'Q2', kind: '音频', 名: '音频 1', vw: 1200, vh: 600, 按: 13 },
  // Q3 散布是节点自己的吗
  { 键: 'X2_1212乙', 组: 'Q3', kind: '音频', 名: '音频 2', vw: 1212, vh: 720, 按: 13 },
  // Q4 尺子：w=1210 这条线上的两个锚
  { 键: 'Q4_文本_1210', 组: 'Q4', kind: '文本', 名: '文本 1', vw: 1210, vh: 720, 按: 13, 期望: 1.75 },
  { 键: 'Q4_时间线_1210', 组: 'Q4', kind: '时间线', 名: '时间线 1', vw: 1210, vh: 720, 按: 13, 期望: 0.566667 },
];

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b315',
  问: '那个 w ∈ (1210, 1212] 的开关，是视口的还是节点的？和视口高有关吗？散布是不是节点自己的？',
  接批次314: {
    已知: '音频 1 / 视频 1 在 w ≤ 1210 逐字命中闭式、w = 1212 全部不中；文本/时间线在 w=1212 仍命中',
    缺口一: '音频只用过一个节点 ⇒ 「kind 有开关」与「这一个节点有开关」分不开（样本量 1，与批次 311 同款）',
    缺口二: '阈值是在 h=720 那一行夹出来的，h ≠ 720 时还在不在 1210/1212 之间没测过',
    缺口三: '坏区散布是 音频1 的 2.07%，音频 2 自己的散布没人知道',
  },
  判据: {
    P0: '文本 1210×720 落 1.75 且时间线 1210×720 落 0.566667，逐字，否则整批作废',
    P1: '音频2 与 音频68 在 1210 命中且在 1212 不中 ⇒ 开关属于视口；任一在 1212 仍命中 ⇒ 开关属于节点',
    P2: '音频1 @1200×600 命中闭式 1.375 ⇒ 开关只认 w；不中 ⇒ 是 (w,h) 交互',
    P3: '音频2 自身两遍的差与 音频1 的 2.07% 并排，只报数不合并',
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

    // 前提：轴向自检
    const 实际 = await p.evaluate(() => ({ w: innerWidth, h: innerHeight }));
    if (实际.w !== 臂.vw || 实际.h !== 臂.vh) throw new Error('轴向自检失败：' + 实际.w + 'x' + 实际.h);
    if (实际.h < 249) throw new Error('视口高不足 249');

    // 前提：aria 精确匹配，现找现量；盒尺寸逐臂现量
    const ariaWant = 臂.kind + ' node: ' + 臂.名;
    const 目标 = await p.evaluate((aria) => {
      const e = Array.from(document.querySelectorAll('.react-flow__node[data-id]'))
        .find((x) => x.getAttribute('aria-label') === aria);
      return e ? { id: e.dataset.id, W: e.offsetWidth, H: e.offsetHeight } : null;
    }, ariaWant);
    if (!目标) throw new Error('找不到 aria 为「' + ariaWant + '」的节点');
    nid = 目标.id;
    记.画布盒 = { W: 目标.W, H: 目标.H };

    for (let i = 0; i < 臂.按; i++) { await p.keyboard.press(放大键); await p.waitForTimeout(380); }
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

    记.闭式预测 = +闭式(臂.vw, 臂.vh, 目标.W, 目标.H, 记.点之前).toFixed(6);
    记.命中闭式 = Math.abs(记.终点 - 记.闭式预测) < 5e-5;
    记.隐含a = +((臂.vh - 160) - 目标.H * 记.终点).toFixed(4);
    if (臂.期望 !== undefined) 记.命中期望 = Math.abs(记.终点 - 臂.期望) < 5e-6;

    log(臂.键.padEnd(15) + '｜视口' + String(臂.vw + 'x' + 臂.vh).padEnd(10)
      + '｜盒' + String(目标.W + 'x' + 目标.H).padEnd(9)
      + '｜z0=' + String(记.点之前).padEnd(8)
      + '｜落点=' + String(记.终点).padEnd(11)
      + '｜闭式=' + String(记.闭式预测).padEnd(11)
      + (记.命中闭式 ? '｜✅命中' : '｜🔴不中')
      + '｜隐含a=' + 记.隐含a);
  } catch (e) {
    记.错误 = e.message;
    log(臂.键.padEnd(15) + '🔴 ' + e.message);
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
const 述 = (k) => {
  const x = 取(k);
  return x ? x.名 + ' @' + x.vw + '×' + x.vh + ' 落 ' + x.终点 + '（闭式 ' + x.闭式预测 + '）' + (x.命中闭式 ? '✅命中' : '🔴不中') : k + ' 无效';
};

// P0
const qa = 取('Q4_文本_1210'); const qb = 取('Q4_时间线_1210');
const 判定P0 = (qa && qa.命中期望 && qb && qb.命中期望)
  ? '✅ P0：' + 述('Q4_文本_1210') + '、' + 述('Q4_时间线_1210') + '，两条逐字 ⇒ 尺子没漂'
  : '🔴 P0：文本=' + (qa ? qa.终点 : '—') + '、时间线=' + (qb ? qb.终点 : '—') + ' ⇒ 本批作废';

// P1 开关属于视口还是节点
const x2a = 取('X2_1210'); const x2b = 取('X2_1212甲');
const x68a = 取('X68_1210'); const x68b = 取('X68_1212');
const 判定P1 = (!x2a || !x2b || !x68a || !x68b) ? '（Q1 臂不全）'
  : (x2a.命中闭式 && x68a.命中闭式 && !x2b.命中闭式 && !x68b.命中闭式
    ? '✅ P1：' + 述('X2_1210') + '；' + 述('X2_1212甲') + '；' + 述('X68_1210') + '；' + 述('X68_1212')
      + ' ⇒ ✅ **三个音频节点在 `w=1210` 全部命中、在 `w=1212` 全部不中 ⇒ 开关属于视口，不属于节点**'
    : '🔴 P1：' + 述('X2_1210') + '；' + 述('X2_1212甲') + '；' + 述('X68_1210') + '；' + 述('X68_1212')
      + ' ⇒ 🔴 **未出现「两档都命中 / 都不中」的整齐形态 ⇒ 开关可能是节点属性**，批次 314 的结论要收窄到具体节点');

// P2 开关与视口高有关吗
const y = 取('Y1_1200x600');
const 判定P2 = !y ? '（Q2 臂无效）'
  : (y.命中闭式
    ? '✅ P2：' + 述('Y1_1200x600') + ' ⇒ ✅ **开关只认 `w`，与视口高无关**（`h=600` 这一行的好区判定标准没有漂）'
    : '🔴 P2：' + 述('Y1_1200x600') + ' ⇒ 🔴 **`h=600` 这一行连 `w=1200` 都不命中 ⇒ 开关是 `(w,h)` 的交互，不是纯 `w`**');

// P3 散布是节点自己的吗（只报数、不合并）
const 集 = [取('X2_1212甲'), 取('X2_1212乙')].filter(Boolean).map((x) => x.终点);
const 差 = 集.length >= 2 ? Math.abs(集[0] - 集[1]) : null;
const 判定P3 = 集.length < 2 ? '（Q3 臂不全）'
  : '📌 P3：`音频 2` 自身两遍 ' + 集.map((v) => v.toFixed(6)).join(' / ') + '，**自身差 ' + 差.toFixed(6)
    + '（相对 ' + (差 / ((集[0] + 集[1]) / 2) * 100).toFixed(2) + '%）**'
    + '｜`音频 1` 的 `2.07%`（批次 314）**并排对照，不合并**'
    + (差 / ((集[0] + 集[1]) / 2) < 0.04
      ? ' ⇒ 📌 **量级相近，但仍需更多节点才能说「散布是这一行的共性」**'
      : ' ⇒ 🔴 **量级差一个数量级 ⇒ 散布更像是节点各自的**，不可跨节点代入');

out.判定 = {
  有效臂: 好.length + '/' + 臂表.length,
  判定P0_尺子: 判定P0,
  判定P1_开关归属: 判定P1,
  判定P2_与视口高: 判定P2,
  判定P3_散布归属: 判定P3,
  逐臂: 好.map((x) => ({ 键: x.键, 名: x.名, 视口: x.vw + 'x' + x.vh, 盒: x.画布盒, z0: x.点之前, 落点: x.终点, 闭式预测: x.闭式预测, 命中闭式: x.命中闭式, 隐含a: x.隐含a })),
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
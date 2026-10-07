/**
 * 批次 314c · 把「闭式失效」的那一个自变量找出来：`w` 还是 `z0`？
 *
 * 🔴 接批次 314b 的 12/12 读数。批次 306 闭式 `vs = min((w−532)/W, (h−160)/H, z0)` 的命中情况：
 *    **7/12**。🔴 6 条不命中的**全部**落在「高度项绑定」的臂里：
 *      音频 `1212×720 → 1.09021`（闭式 1.75）、音频 `1212×600 → 0.697712`（闭式 1.375）、
 *      视频 `1212×720 → 0.593848`（闭式 0.984183）、视频 `1212×600 → 0.397249`（闭式 0.773286）、
 *      视频 `1212×1080 → 1.23309`（闭式 1.616872）
 *    📌 而「宽度项绑定」的臂 **4/4 逐字命中**（时间线 `1212×720`/`1000×720`、音频 `1212×1080`/`1000×720`）。
 *
 * 📌 **本批要解决的那一对是全批最干净的反例**：
 *      视频 `1000×720` → **`0.984183`** = 闭式的 `560/569` **逐字**
 *      视频 `1212×720` → **`0.593848`** ≠ 闭式的 `560/569`（**同一个数**）
 *    📌 这两臂的高度项**完全相同**（`h=720` ⇒ `560/569`），盒也相同（`320×569`），
 *      🔴 **唯一变的是 `w`（1000↔1212）和 `z0`（2.377↔2.779）**。
 *    ⇒ 📌 **「高度项绑定时不命中」这句话还不成立** —— 得先分清是 `w` 还是 `z0`。
 *
 * 📌 **两把刀，一次分清**：
 *   **刀 W（扫 w，h 固定 720，按键固定 13）**：若落点在某个 `w` 上**跳变** ⇒ `w` 驱动，
 *        📌 顺带把批次历史里「音频凹口 `1212–1230`」「窄侧 `safeW=w−412`」那两个未测的开关点定位。
 *   **刀 Z（固定 `w=1212`、`h=720`，只改按键次数 10/11/12/13）**：
 *        若落点**随 `z0` 连续变化** ⇒ `z0` 驱动，🔴 **批次 306 的第三项 `z0` 就不是纯 `min` 上界**；
 *        若落点**几乎不变** ⇒ `z0` 无关，🔴 就是 `w` 的事。
 *
 * 📌 **判据（测量前写死）**：
 *   **P0** 视频 `1000×720`（刀 W 首臂）必须落 `0.984183`、文本 `1212×720` 必须落 `1.75`，两条都逐字。
 *   **P1（刀 W）** 报出 `w`→落点的序列，📌 **不拟合**，只报「是否跳变」与「跳变点落在哪两档之间」。
 *   **P2（刀 Z）** 报 `z0`→落点序列，📌 判据是**同组自身跨遍极差**：
 *        🔴 **若极差 < `1e-4` 即判「`z0` 不驱动」** —— 不拿绝对阈值判，拿自己的极差判。
 *   **P3** 两把刀结论必须**指向同一个自变量**；不一致就如实记「两个都在起作用」，🔴 不硬收敛。
 *
 * 前提检查：轴向自检 / 落定自检（三连读）/ 点击生效自检 /
 *   `aria` 精确匹配现找现量 / 参数写死 / 每臂独立浏览器 / 盒尺寸逐臂现量。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const STATE = `${process.env.HOME}/.jimeng-automation/state.json`;
const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b314c.json';
const 放大键 = 'Meta+Equal';
const 闭式 = (w, h, W, H, z0) => Math.min((w - 532) / W, (h - 160) / H, z0);

const 臂表 = [
  // 刀 W：h 固定 720、按键固定 13，只扫 w
  { 键: 'W1000', 组: 'W', kind: '视频', 名: '视频 1', vw: 1000, vh: 720, 按: 13, 期望: 0.984183 },
  { 键: 'W1100', 组: 'W', kind: '视频', 名: '视频 1', vw: 1100, vh: 720, 按: 13 },
  { 键: 'W1150', 组: 'W', kind: '视频', 名: '视频 1', vw: 1150, vh: 720, 按: 13 },
  { 键: 'W1200', 组: 'W', kind: '视频', 名: '视频 1', vw: 1200, vh: 720, 按: 13 },
  { 键: 'W1212', 组: 'W', kind: '视频', 名: '视频 1', vw: 1212, vh: 720, 按: 13 },
  // 刀 Z：w、h 全固定，只改按键次数 ⇒ z0 变，其余一切不变
  { 键: 'Z按10', 组: 'Z', kind: '视频', 名: '视频 1', vw: 1212, vh: 720, 按: 10 },
  { 键: 'Z按11', 组: 'Z', kind: '视频', 名: '视频 1', vw: 1212, vh: 720, 按: 11 },
  { 键: 'Z按12', 组: 'Z', kind: '视频', 名: '视频 1', vw: 1212, vh: 720, 按: 12 },
  { 键: 'Z按13', 组: 'Z', kind: '视频', 名: '视频 1', vw: 1212, vh: 720, 按: 13 },
  // 阳性对照：尺子没漂
  { 键: 'D文本-1212x720', 组: 'D', kind: '文本', 名: '文本 1', vw: 1212, vh: 720, 按: 13, 期望: 1.75 },
];

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b314c',
  问: '高度项绑定时闭式失效，是 w 驱动还是 z0 驱动？',
  接批次314b: {
    闭式命中: '7/12；6 条不命中全在「高度项绑定」的臂里；「宽度项绑定」4/4 逐字',
    最干净的反例: '视频 1000×720 → 0.984183（= 闭式 560/569 逐字）vs 1212×720 → 0.593848（闭式同一个数）；两臂盒相同、h 相同，只差 w 与 z0',
    另一条并存事实: '同条件下音频 1212×720 跨批复现极差 1.35%（1.10512/1.09021）、视频 0.81%（0.598681/0.593848），而时间线与文本极差 0',
  },
  判据: {
    P0: '视频 1000×720 落 0.984183 且文本 1212×720 落 1.75，逐字，否则整批作废',
    P1: '刀W 只报「是否跳变」与跳变点区间，不拟合',
    P2: '刀Z 用同组自身跨遍极差判 z0 是否驱动，极差 < 1e-4 即判不驱动',
    P3: '两刀须指向同一自变量；不一致如实记「两个都在起作用」',
  },
  臂表, 臂: [], 判定: {},
};

for (const 臂 of 臂表) {
  let br = null; let p = null; let nid = null;
  const 记 = { 键: 臂.键, 组: 臂.组, kind: 臂.kind, 名: 臂.名, vw: 臂.vw, vh: 臂.vh, 按: 臂.按 };
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

    记.闭式预测 = +闭式(臂.vw, 臂.vh, 目标.W, 目标.H, 记.点之前).toFixed(6);
    记.命中闭式 = Math.abs(记.终点 - 记.闭式预测) < 5e-5;
    记.隐含a = +((臂.vh - 160) - 目标.H * 记.终点).toFixed(4);
    if (臂.期望 !== undefined) 记.命中期望 = Math.abs(记.终点 - 臂.期望) < 5e-5;

    log(臂.键.padEnd(14) + '｜视口' + String(臂.vw + 'x' + 臂.vh).padEnd(10)
      + '｜盒' + String(目标.W + 'x' + 目标.H).padEnd(9)
      + '｜按' + String(臂.按).padEnd(3)
      + '｜z0=' + String(记.点之前).padEnd(8)
      + '｜落点=' + String(记.终点).padEnd(11)
      + '｜闭式=' + String(记.闭式预测).padEnd(11)
      + (记.命中闭式 ? '｜✅命中' : '｜🔴不中')
      + '｜隐含a=' + 记.隐含a);
  } catch (e) {
    记.错误 = e.message;
    log(臂.键.padEnd(14) + '🔴 ' + e.message);
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
const 刀W = 好.filter((x) => x.组 === 'W').sort((a, b) => a.vw - b.vw);
const 刀Z = 好.filter((x) => x.组 === 'Z').sort((a, b) => a.按 - b.按);
const 对照 = 取('D文本-1212x720');
const 首臂 = 刀W[0];

const 判定P0 = (首臂 && 首臂.命中闭式 && 对照 && 对照.命中期望)
  ? '✅ P0：视频 ' + 首臂.vw + '×' + 首臂.vh + ' 落 ' + 首臂.终点 + '（= 闭式 ' + 首臂.闭式预测 + ' 逐字）、文本对照落 ' + 对照.终点 + ' ⇒ 尺子没漂，本批读数可用'
  : '🔴 P0：视频首臂命中=' + (首臂 ? 首臂.命中闭式 : '—') + '、文本对照=' + (对照 ? 对照.终点 : '—') + ' ⇒ 本批读数作废';

// P1 刀W：只判「是否跳变」，不拟合
let 判定P1 = '（刀 W 无有效臂）';
if (刀W.length >= 2) {
  const 命中集 = 刀W.filter((x) => x.命中闭式);
  const 不中集 = 刀W.filter((x) => !x.命中闭式);
  const a集 = 刀W.map((x) => x.隐含a);
  const a极差 = +(Math.max.apply(null, a集) - Math.min.apply(null, a集)).toFixed(4);
  const 跳变点 = 命中集.length && 不中集.length
    ? '命中段 w≤' + Math.max.apply(null, 命中集.map((x) => x.vw)) + '、不中段 w≥' + Math.min.apply(null, 不中集.map((x) => x.vw))
    : (命中集.length === 刀W.length ? '全部命中' : '全部不中');
  判定P1 = 'w→落点：' + 刀W.map((x) => x.vw + '→' + x.终点 + (x.命中闭式 ? '✅' : '🔴')).join('；')
    + '｜隐含a：' + a集.join('、') + '（极差 ' + a极差 + '）'
    + '｜' + (a极差 < 1e-3
      ? '📌 **隐含 a 跨 w 几乎不变 ⇒ 落点不随 w 变**，🔴 那对反例的差别不在 w'
      : '✅ **隐含 a 跨 w 变（极差 ' + a极差 + '）⇒ `w` 驱动**；命中段：' + 跳变点);
}

// P2 刀Z：用同组自身极差判
let 判定P2 = '（刀 Z 无有效臂）';
if (刀Z.length >= 2) {
  const 集 = 刀Z.map((x) => x.终点);
  const 极差 = +(Math.max.apply(null, 集) - Math.min.apply(null, 集)).toFixed(6);
  判定P2 = '按次数→(z0,落点)：' + 刀Z.map((x) => x.按 + '→(' + x.点之前 + ',' + x.终点 + ')').join('；')
    + '｜落点跨遍极差 **' + 极差 + '**'
    + (极差 < 1e-4
      ? ' ⇒ 📌 **`z0` 不驱动落点**（同组自身极差 < 1e-4）'
      : ' ⇒ ✅ **`z0` 驱动落点**，🔴 批次 306 的第三项**不是纯 min 上界**')
    + '｜命中闭式：' + 刀Z.filter((x) => x.命中闭式).length + '/' + 刀Z.length;
}

// P3 两刀是否指向同一个自变量
const w驱动 = /`w` 驱动/.test(判定P1);
const z驱动 = /`z0` 驱动/.test(判定P2);
const 判定P3 = (w驱动 && z驱动) ? '⚠️ P3：**`w` 与 `z0` 都驱动** ⇒ 两个自变量都在起作用'
  : (w驱动 ? '✅ P3：刀 W 说 `w` 驱动、刀 Z 说 `z0` 不驱动 ⇒ 🔴 **失效的自变量是 `w`**，且它与批次 306 第三项无关'
    : (z驱动 ? '✅ P3：刀 Z 说 `z0` 驱动、刀 W 说落点不随 `w` 变 ⇒ 🔴 **失效的自变量是 `z0`**'
      : '⚠️ P3：两刀都没给出驱动因素 ⇒ 🔴 **本批不能定自变量**，如实记两把刀各自的结果'));

out.判定 = {
  有效臂: 好.length + '/' + 臂表.length,
  判定P0_尺子: 判定P0,
  判定P1_刀W: 判定P1,
  判定P2_刀Z: 判定P2,
  判定P3_两刀一致性: 判定P3,
  逐臂: 好.map((x) => ({ 键: x.键, 视口: x.vw + 'x' + x.vh, 按: x.按, 盒: x.画布盒, z0: x.点之前, 落点: x.终点, 闭式预测: x.闭式预测, 命中闭式: x.命中闭式, 隐含a: x.隐含a })),
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
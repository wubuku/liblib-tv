/**
 * 批次 314d · 把批次 314c 的开关**夹到一个更窄的区间**，并查它是不是 kind 专属。
 *
 * 🔴 接批次 314c（10/10）：`w` 扫描 `1000/1100/1150/1200` **四档全部逐字命中**闭式、全部落 `0.984183`；
 *    `w=1212` 落 `0.598854` 不中。📌 **`w=1200` 与 `w=1212` 的 `z0` 同为 `2.779`** ⇒ 开关不是 `z0`。
 * 🔴 顺带发现批次 314c 判据 P3 写宽了：`z0` 在 `w ≤ 1200` 四档（`2.377/2.611/2.736/2.779`）上
 *    **全部落同一个数** ⇒ **`z0` 在健康区不驱动落点**；它只在 `w=1212` 的坏区出现相关性，且**非单调**
 *    （`0.609283 → 0.58348 → 0.616556 → 0.599459`）⇒ 📌 那不是公式的形状，是散布的形状。
 *
 * 📌 本批四问，每问都配了对照：
 *   **Q1 阈值**：`w ∈ {1206, 1210}` ⇒ 开关落在 `(1200, 1210]` 还是更靠右。
 *   **Q2 kind 专属吗**：`文本`/`时间线` 在 `w=1212` **命中**闭式（批次 314b/314c 已测），
 *        🔴 而 `音频`/`视频` 在 `w=1212` 不命中 ⇒ 📌 要看 `音频` 在 `w=1200` 是不是**命中** ——
 *        **若音频在 1200 命中、在 1212 不中，事件就是「跨过阈值」，不是「音频这个 kind 不行」。**
 *   **Q3 散布有多大**：`音频 1212×720` 再测两遍 + `视频 1212×720` 已有三读，
 *        ⇒ 报**跨遍极差与相对极差**，🔴 用**同组自身极差**判「稳不稳」，不用绝对阈值。
 *   **Q4 尺子**：`文本 1200×720` 必须落 `1.75`、`时间线 1212×720` 必须落 `0.566667`。
 *
 * 📌 **判据（测量前写死）**：
 *   **P0** Q4 两条逐字命中，否则整批作废。
 *   **P1** 报「命中段 / 不中段」的 `w` 分界，📌 只报区间不拟合。
 *   **P2** `音频 1200` 命中 **且** `音频 1212` 不中 ⇒ ✅ 确认是**跨阈值事件**；
 *        两者都命中 ⇒ 🔴 是 kind 属性；两者都不中 ⇒ ⚠️ 是 kind × w 的交互。
 *   **P3** 报散布的**相对极差**，📌 与同组内「`w ≤ 1200` 侧」的极差（应为 `0`）并排对照。
 */
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
const OUT = '/tmp/b314d.json';
const 放大键 = 'Meta+Equal';
const 闭式 = (w, h, W, H, z0) => Math.min((w - 532) / W, (h - 160) / H, z0);

const 臂表 = [
  // Q1 阈值
  { 键: 'V1206', 组: 'V', kind: '视频', 名: '视频 1', vw: 1206, vh: 720, 按: 13 },
  { 键: 'V1210', 组: 'V', kind: '视频', 名: '视频 1', vw: 1210, vh: 720, 按: 13 },
  // Q2 kind 专属：音频在阈值两侧
  { 键: 'A1200', 组: 'A', kind: '音频', 名: '音频 1', vw: 1200, vh: 720, 按: 13 },
  { 键: 'A1212甲', 组: 'A', kind: '音频', 名: '音频 1', vw: 1212, vh: 720, 按: 13 },
  { 键: 'A1212乙', 组: 'A', kind: '音频', 名: '音频 1', vw: 1212, vh: 720, 按: 13 },
  // Q4 尺子
  { 键: 'Q文本-1200', 组: 'Q', kind: '文本', 名: '文本 1', vw: 1200, vh: 720, 按: 13, 期望: 1.75 },
  { 键: 'Q时间线-1212', 组: 'Q', kind: '时间线', 名: '时间线 1', vw: 1212, vh: 720, 按: 13, 期望: 0.566667 },
];

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b314d',
  问: '开关夹到哪个 w？它是不是 kind 专属？坏区的散布有多大？',
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

// P0 尺子
const q1 = 取('Q文本-1200'); const q2 = 取('Q时间线-1212');
const 判定P0 = (q1 && Math.abs(q1.终点 - 1.75) < 1e-6 && q2 && Math.abs(q2.终点 - 0.566667) < 1e-6)
  ? '✅ P0：文本 ' + q1.vw + '×720 落 ' + q1.终点 + '、时间线 1212×720 落 ' + q2.终点 + '，两条逐字 ⇒ 尺子没漂'
  : '🔴 P0：文本=' + (q1 ? q1.终点 : '—') + '、时间线=' + (q2 ? q2.终点 : '—') + ' ⇒ 本批作废';

// P1 阈值：把批次 314c 的五档与本批两档并排，只报分界区间
const 视频序列 = [
  { w: 1000, 落: 0.984183, 中: true, 源: '314c' },
  { w: 1100, 落: 0.984183, 中: true, 源: '314c' },
  { w: 1150, 落: 0.984183, 中: true, 源: '314c' },
  { w: 1200, 落: 0.984183, 中: true, 源: '314c' },
];
for (const k of ['V1206', 'V1210']) {
  const x = 取(k);
  if (x) 视频序列.push({ w: x.vw, 落: x.终点, 中: x.命中闭式, 源: '314d' });
}
视频序列.push({ w: 1212, 落: 0.598854, 中: false, 源: '314c' });
视频序列.sort((a, b) => a.w - b.w);
const 中段 = 视频序列.filter((x) => x.中).map((x) => x.w);
const 不中段 = 视频序列.filter((x) => !x.中).map((x) => x.w);
const 判定P1 = '视频 h=720 的 w→命中：' + 视频序列.map((x) => x.w + (x.中 ? '✅' : '🔴')).join(' ')
  + '｜' + (中段.length && 不中段.length
    ? '✅ **开关落在 (' + Math.max.apply(null, 中段) + ', ' + Math.min.apply(null, 不中段) + ']**，📌 落点从「逐字等于闭式」一步跳到「明显更小」，**不是渐变**'
    : (中段.length === 视频序列.length ? '全部命中' : '全部不中'));

// P2 kind 专属
const a1200 = 取('A1200'); const a1212 = 好.filter((x) => x.键 === 'A1212甲' || x.键 === 'A1212乙');
const 判定P2 = !a1200 || !a1212.length
  ? '（音频臂不全）'
  : (a1200.命中闭式 && a1212.every((x) => !x.命中闭式)
    ? '✅ P2：音频 `w=1200` 落 ' + a1200.终点 + '（= 闭式 ' + a1200.闭式预测 + ' 逐字）、`w=1212` 两臂落 ' + a1212.map((x) => x.终点).join(' 与 ') + ' 均不中 ⇒ 🔴 **这是「跨过 `w` 阈值」的事件，不是「音频这个 kind 不行」**'
    : (a1200.命中闭式 && a1212.every((x) => x.命中闭式)
      ? '🔴 P2：音频在 `1200` 与 `1212` **都命中**闭式 ⇒ 与 `w` 无关，📌 视频那一侧要另找原因'
      : '⚠️ P2：音频 `1200` 命中=' + a1200.命中闭式 + '、`1212` 命中=' + a1212.map((x) => x.命中闭式).join('/') + ' ⇒ 是 kind × w 的交互'));

// P3 散布：并排对照「好区极差」与「坏区极差」
const 坏区 = a1212.map((x) => x.终点).concat([0.598854, 0.599459]);
const 坏极差 = +(Math.max.apply(null, 坏区) - Math.min.apply(null, 坏区)).toFixed(6);
const 好区 = [0.984183];
const 判定P3 = '坏区（音频/视频 @ `w=1212`）' + a1212.length + '+3 读数：' + 坏区.join('、')
  + '｜**极差 ' + 坏极差 + '（相对 ' + (坏极差 / (坏区.reduce((a, b) => a + b, 0) / 坏区.length) * 100).toFixed(2) + '%）**'
  + '｜好区（视频 @ `w ≤ 1200`，4 读数）极差 **0**'
  + '⇒ 🔴 **跨过 `w` 阈值之后，落点既不再是闭式，也不再逐字可复现**';

out.判定 = {
  有效臂: 好.length + '/' + 臂表.length,
  判定P0_尺子: 判定P0,
  判定P1_阈值: 判定P1,
  判定P2_kind专属: 判定P2,
  判定P3_散布: 判定P3,
  逐臂: 好.map((x) => ({ 键: x.键, 视口: x.vw + 'x' + x.vh, 盒: x.画布盒, z0: x.点之前, 落点: x.终点, 闭式预测: x.闭式预测, 命中闭式: x.命中闭式, 隐含a: x.隐含a })),
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
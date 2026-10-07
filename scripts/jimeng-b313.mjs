/**
 * 批次 313 · 判别「文本落 `1.75`」的来源：`vs` 上限，还是类型预设？—— 外加填 `按12` 的缺口。
 *
 * 🔴 起意：批次 312 留下一个**盲区** ——
 *    在视口 `1212×720` 下，批次 306 的闭式 `vs = min((w−532)/320,(h−160)/320)` 算出 **`1.75`**，
 *    而正文批次 191 的「导演台取景预设」**也是 `1.75`**。
 *    🔴 **两个来源数值相同 ⇒ 单看这个数分不出是谁决定的** ⇒ 必须换一个让两者不等的视口。
 *
 * 📌 **实验 A（换视口分开两个来源）** —— 本批的主判据：
 *   📌 选视口 `1212×900`：批次 306 的闭式给出 `vs = min(2.12500, 2.31250) = 2.125`，
 *   📌 🔴 **它不等于 `1.75`** ⇒ 在这个视口下：
 *     **A1** 文本落点 **`=== 2.125`** ⇒ 🔴 **撞的是 `vs`**，「一律到预设」需收窄；
 *     **A2** 文本落点仍 **`=== 1.75`** ⇒ ✅ **它是类型预设，与视口无关**，正文成立。
 *   📌 另配 `1000×720`（闭式 `vs = 1.4625`）作**第二个不等点**，
 *   📌 🔴 **两个不等点方向相反**（一个 >1.75、一个 <1.75）⇒ 判别力比单点强得多。
 *
 * 📌 **实验 B（填批次 312 的缺口档）**：
 *   📌 `按12` 键的 `z0 = 2.316`，📌 **恰好落在正文射程（`z0 ≤ 2.0`）与批次 312 观测（`2.779`）之间**。
 *     **B1** 落点 `≈ 1.56` ⇒ 「预设是硬上界」，正文成立；
 *     **B2** 落点 `> 1.56` ⇒ 🔴 正文「一律到预设」**需要收窄**。
 *
 * 📌 **判据（测量前写死）**：
 *   **P0（阳性对照）** 必须有一臂落 `1.75`（批次 306/311/312 已反复测到的基线），
 *          🔴 否则本批全部读数作废（立规 189：不拿不可信的尺子量东西）。
 *
 * 前提检查：轴向自检 / 落定自检（连读两次）/ 点击生效自检 /
 *   `aria` 精确匹配现找现量 / 参数写死 / 每臂独立浏览器。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const STATE = `${process.env.HOME}/.jimeng-automation/state.json`;
const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b313.json';
const 放大键 = 'Meta+Equal';
const kind = '文本'; const 名 = '文本 1';

/** 📌 批次 306 的闭式，本批用它【预测】落点（不是用来反推） */
const 闭式 = (w, h) => Math.min((w - 532) / 320, (h - 160) / 320);

const 臂表 = [
  // 实验 A：换视口，让 vs 与「预设 1.75」不等
  { 键: 'A视1212x900', 组: 'A', vw: 1212, vh: 900, 按: 13 },
  { 键: 'A视1000x720', 组: 'A', vw: 1000, vh: 720, 按: 13 },
  // 对照：vs 恰等于 1.75 的视口（批次 306/311 已 9/9 证）
  { 键: 'A对照1212x720', 组: 'A对照', vw: 1212, vh: 720, 按: 13 },
  // 实验 B：填缺口档
  { 键: 'B按12', 组: 'B', vw: 1212, vh: 720, 按: 12 },
  { 键: 'B按13对照', 组: 'B', vw: 1212, vh: 720, 按: 13 },
];

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b313',
  问: '文本落 1.75 是撞 vs 上限还是类型预设？按12(z0=2.316) 落在哪一边？',
  判据: {
    P0: '阳性对照：必须有一臂落 1.75，否则整批作废',
    A1: '视口 vs≠1.75 时落 vs ⇒ 撞的是 vs，正文「一律到预设」需收窄',
    A2: '视口 vs≠1.75 时仍落 1.75 ⇒ 是类型预设，正文成立',
    B1: '按12(z0=2.316) 落 ≈1.56 ⇒ 预设是硬上界',
    B2: '按12 落 >1.56 ⇒ 正文需收窄',
  },
  闭式来源: '批次306 vs=min((w-532)/320,(h-160)/320)，9/9 逐字',
  臂表, 臂: [], 判定: {},
};

for (const A of 臂表) {
  let br = null; let p = null; let nid = null;
  const 记 = { 键: A.键, 组: A.组, vw: A.vw, vh: A.vh, 按: A.按 };
  try {
    记.预测vs = +闭式(A.vw, A.vh).toFixed(5);
    br = await chromium.launch({ headless: true });
    const ctx = await br.newContext({ storageState: STATE, viewport: { width: A.vw, height: A.vh } });
    p = await ctx.newPage();
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 60000 });
    await p.waitForTimeout(6000);
    const 实际 = await p.evaluate(() => ({ w: innerWidth, h: innerHeight }));
    if (实际.w !== A.vw || 实际.h !== A.vh) throw new Error(`轴向自检失败：${实际.w}×${实际.h}`);
    if (实际.h < 249) throw new Error('视口高不足 249');

    const ariaWant = `${kind} node: ${名}`;
    const 目标 = await p.evaluate((aria) => {
      const e = Array.from(document.querySelectorAll('.react-flow__node[data-id]'))
        .find((x) => x.getAttribute('aria-label') === aria);
      return e ? { id: e.dataset.id, W: e.offsetWidth, H: e.offsetHeight } : null;
    }, ariaWant);
    if (!目标) throw new Error(`找不到 aria 为「${ariaWant}」的节点`);
    nid = 目标.id;

    for (let i = 0; i < A.按; i++) { await p.keyboard.press(放大键); await p.waitForTimeout(380); }
    await p.waitForTimeout(1600);
    const 读缩放 = () => p.evaluate(() => {
      const vp = document.querySelector('.react-flow__viewport');
      const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
      return m ? Number(m[1]) : null;
    });
    记.点之前 = await 读缩放();

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
    const r1 = await 读缩放();
    await p.waitForTimeout(2600);
    const r2 = await 读缩放();
    记.读1 = r1; 记.读2 = r2;
    记.落定 = (r1 === r2);
    记.终点 = r2;
    const 选 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((x) => x.dataset.id));
    记.点击生效 = 选.includes(nid);
    if (!记.点击生效) throw new Error('点击未生效');
    记.落175 = Math.abs(r2 - 1.75) < 1e-6;
    记.落预测vs = Math.abs(r2 - 记.预测vs) < 1e-4;
    log(`${A.键.padEnd(14)}｜视口${String(A.vw + 'x' + A.vh).padEnd(10)}｜点之前=${String(记.点之前).padEnd(9)}｜终点=${String(r2).padEnd(10)}｜预测vs=${记.预测vs}${记.落175 ? '｜落1.75' : ''}${记.落预测vs ? '｜落vs✅' : ''}`);
  } catch (e) {
    记.错误 = e.message;
    log(`${A.键.padEnd(14)}🔴 ${e.message}`);
  } finally {
    try { if (p) await p.close(); } catch (e) { /* 忽略 */ }
    try { if (br) await br.close(); } catch (e) { /* 忽略 */ }
    out.臂.push(记);
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

// ───────── 判定 ─────────
const 好 = out.臂.filter((x) => !x.错误 && x.点击生效 && x.落定 && x.终点 !== undefined);
const A臂 = 好.filter((x) => x.组 === 'A');
const 对照臂 = 好.find((x) => x.组 === 'A对照');
const B12 = 好.find((x) => x.键 === 'B按12');
const B13 = 好.find((x) => x.键 === 'B按13对照');

const 判定P0 = (对照臂 && 对照臂.落175)
  ? '✅ P0：阳性对照落 1.75（对照臂 z0=' + 对照臂.点之前 + '）⇒ 尺子没漂，本批读数可用'
  : '🔴 P0：对照臂未落 1.75（' + (对照臂 ? 对照臂.终点 : '—') + '）⇒ 本批读数作废';

// 🔴 实验 A 的判别：两个不等点方向相反
const 不等点 = A臂.filter((x) => Math.abs(x.预测vs - 1.75) > 1e-6);
const 跟vs = 不等点.filter((x) => x.落预测vs);
const 跟175 = 不等点.filter((x) => x.落175);
const 判定A = 不等点.length === 0 ? '（无 vs≠1.75 的不等点）'
  : (跟vs.length === 不等点.length
    ? '✅ A1：' + 不等点.length + ' 个 vs≠1.75 的视口下，落点**全部等于闭式算出的 vs**（'
      + 不等点.map((x) => `${x.vw}x${x.vh}: vs=${x.预测vs} 落=${x.终点}`).join('；')
      + '）⇒ 🔴 **文本的落点是撞 `vs` 上限，不是类型预设** ⇒ 📌 正文「一律到该类型预设」**需要收窄**'
    : (跟175.length === 不等点.length
      ? '✅ A2：' + 不等点.length + ' 个 vs≠1.75 的视口下，落点**全部仍是 1.75** ⇒ ✅ **它是类型预设，与视口无关**，正文成立'
      : '⚠️ A3：' + 不等点.length + ' 个不等点里，' + 跟vs.length + ' 个跟 vs、' + 跟175.length + ' 个跟 1.75 ⇒ 🔴 **两个来源都在起作用**，需按视口再细查'));

const 判定B = B12
  ? (Math.abs(B12.终点 - 1.5625) < 0.01
    ? '✅ B1：按12（z0=' + B12.点之前 + '）落 ' + B12.终点 + '，≈ 预设 1.5625（差 ' + Math.abs(B12.终点 - 1.5625).toFixed(5) + '）⇒ 📌 **预设是硬上界，正文成立**'
    : (B12.终点 > 1.5625 + 0.01
      ? '🔴 B2：按12（z0=' + B12.点之前 + '）落 ' + B12.终点 + '，**高于**预设 1.5625（高 ' + (B12.终点 - 1.5625).toFixed(5) + '）⇒ 📌 **预设不是硬上界**，正文「一律到预设」需收窄'
      : '⚠️ B4：按12 落 ' + B12.终点 + '，落在预设下方 ⇒ 需另找原因'))
  : '（B12 臂无效）';

out.判定 = {
  有效臂: `${好.length}/${臂表.length}`,
  逐臂: 好.map((x) => ({ 键: x.键, 视口: `${x.vw}x${x.vh}`, 点之前: x.点之前, 终点: x.终点, 预测vs: x.预测vs, 落175: x.落175, 落vs: x.落预测vs })),
  判定P0: 判定P0,
  判定A_换视口分来源: 判定A,
  判定B_填缺口档: 判定B,
  B13对照终点: B13 ? B13.终点 : null,
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
/**
 * 批次 314b · 把音频/视频落点随视口高的**形状**测出来，并补上被自伤门槛误杀的三个宽度臂。
 *
 * 🔴 接批次 314 第一轮的三条有效读数（`/tmp/b314.json`）：
 *    音频 `1212×900` 落 **`1.66349`**，视频 `1212×900` 落 **`0.926991`**
 *    🔴 两个模型都**逐字不中**：宽度项预测 `1.10512`/`0.598681`（= 基线值，即「不变」）、
 *       「高度项 = 常数 compound」预测 `1.460337`/`0.791114`。
 *    ⇒ 📌 **落点确实随视口高变**（这两个 kind 的「与视口无关的类型常量」被排除），
 *      🔴 **但「常数 inset」也不成立**：反解出的隐含 inset 在漂，且**两个 kind 方向相反** ——
 *        音频 `206.3616 → 207.6832`（**+0.64%**）、视频 `219.4253 → 212.6580`（**−3.10%**）。
 *
 * 📌 **本批的三个问题，各配一个方向相反的判别点**：
 *   **Q1 轴**：只变宽（`1000×720`）时落点动不动？
 *        音频 M宽 `0.760539` vs M高 `1.105120`（不动）｜视频 `0.412034` vs `0.598681`｜时间线 `0.390000` vs `0.566666`
 *        ⇒ 🔴 三个都是「宽度项变 / 高度项不变」，📌 **宽度项若绑定，音频/视频的 `W_c` 必须 ≈ `615.318`/`1135.83`**
 *   **Q2 形状**：高度取 `{600, 720, 900, 1080}` 四点。
 *        「常数 inset」模型预测：音频 `0.730120 / 1.105120 / 1.667620 / 2.230120`；
 *          视频 `0.387728 / 0.598681 / 0.915095 / 1.231472`
 *        ⇒ 📌 **四个点里任意一个不落在这条直线上，「常数 inset」即被否**，🔴 且能看出往哪边弯。
 *   **Q3 前提**：文本在 `1212×720` 必须落 `1.75`、在 `1212×600` 必须落 `1.375`（立规 189：不拿不可信的尺子量东西）。
 *
 * 🔴 **本批修掉的第一轮自伤 bug**：`点之前缩放 >= 2.7` 这条门槛是按 `1212` 宽标定的，
 *    🔴 而**按 `13` 次得到的 `z0` 本身就随视口宽变**（`1212×720→2.779`、`1212×900→2.885`、`1000×720→2.377`）
 *    ⇒ 三个 `1000×720` 臂被我自己的守卫杀掉。📌 **门槛必须按「本臂预期值」写，不能按单点观察写死。**
 *
 * 📌 **判据（测量前写死）**：
 *   **P0** 文本 `1212×720 → 1.75` 且 `1212×600 → 1.375`，两条都逐字，否则整批作废。
 *   **P1** 每臂对「常数 inset」模型的相对偏差记 `δ`，🔴 **`|δ| > 1%` 即判该点不落在线上**。
 *   **P2** 音频/视频的 `δ` 若**在四个高度上系统性同号**，📌 说明存在一个可外推的形状；
 *        若**变号**，🔴 说明不是单一仿射关系，**不许拟合**，只如实记四点。
 *
 * 前提检查：轴向自检 / 落定自检（三连读）/ 点击生效自检 /
 *   `aria` 精确匹配现找现量 / 参数写死 / 每臂独立浏览器 / 盒尺寸逐臂现量。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const STATE = `${process.env.HOME}/.jimeng-automation/state.json`;
const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b314b.json';
const 放大键 = 'Meta+Equal';

/** 📌 批次 306 证实：inset 与视口无关（`1212×900`/`1000×720` 两档逐字命中） */
const SAFE_W = (w) => w - 532;
const SAFE_H = (h) => h - 160;

/** 📌 批次 311 在 `1212×720`、`z0=2.779` 的实测落点，以及批次 314b 首批复测的盒尺寸 */
const 基线落点 = { 音频: 1.10512, 视频: 0.598681, 时间线: 0.566667, 文本: 1.75 };

const 臂表 = [
  // Q1 轴：只变宽（高度项若绑定则落点不变）
  { 键: 'W1音频-宽变', 组: 'W', kind: '音频', 名: '音频 1', vw: 1000, vh: 720 },
  { 键: 'W2视频-宽变', 组: 'W', kind: '视频', 名: '视频 1', vw: 1000, vh: 720 },
  { 键: 'W3时间线-宽变', 组: 'W', kind: '时间线', 名: '时间线 1', vw: 1000, vh: 720 },
  // Q2 形状：高度四点里的两端
  { 键: 'H1音频-h1080', 组: 'H', kind: '音频', 名: '音频 1', vw: 1212, vh: 1080 },
  { 键: 'H2音频-h600', 组: 'H', kind: '音频', 名: '音频 1', vw: 1212, vh: 600 },
  { 键: 'H3视频-h1080', group2: 'H', 组: 'H', kind: '视频', 名: '视频 1', vw: 1212, vh: 1080 },
  { 键: 'H4视频-h600', 组: 'H', kind: '视频', 名: '视频 1', vw: 1212, vh: 600 },
  // 基线复测（算隐含 inset 要用本批现量的盒，不跨批硬编码）
  { 键: 'C1音频-基线', 组: 'C', kind: '音频', 名: '音频 1', vw: 1212, vh: 720 },
  { 键: 'C2视频-基线', 组: 'C', kind: '视频', 名: '视频 1', vw: 1212, vh: 720 },
  { 键: 'C3时间线-基线', 组: 'C', kind: '时间线', 名: '时间线 1', vw: 1212, vh: 720 },
  // Q3 前提：尺子
  { 键: 'D1文本-720', 组: 'D', kind: '文本', 名: '文本 1', vw: 1212, vh: 720, 期望: 1.75 },
  { 键: 'D2文本-h600', 组: 'D', kind: '文本', 名: '文本 1', vw: 1212, vh: 600, 期望: 1.375 },
];

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b314b',
  问: '音频/视频落点绑在哪个轴？随视口高的形状是不是「常数 inset」这条直线？',
  接批次314第一轮: {
    音频_1212x900: 1.66349, 音频_模型M宽: 1.10512, 音频_模型M高: 1.460337, 音频_隐含a: { h720: 206.3616, h900: 207.6832 },
    视频_1212x900: 0.926991, 视频_模型M宽: 0.598681, 视频_模型M高: 0.791114, 视频_隐含a: { h720: 219.4253, h900: 212.6580 },
    第一轮自伤bug: 'z0 门槛按 1212 宽写成 >=2.7，但 13 次放大的 z0 随视口宽变（1000 宽只到 2.377）⇒ 三个宽度臂被自己的守卫杀掉',
  },
  判据: {
    P0: '文本 1212×720 落 1.75 且 1212×600 落 1.375，逐字，否则整批作废',
    P1: '每臂记相对偏差 δ=(实测−常数inset模型)/模型；|δ|>1% 即判该点不落在线上',
    P2: 'δ 在四个高度上系统同号 ⇒ 有可外推形状；变号 ⇒ 不是单一仿射关系，不许拟合',
  },
  臂表, 臂: [], 判定: {},
};

/** 📌 「常数 inset」模型：由基线臂的落点与**本批现量的盒高**反解 a，再对任意 h 预测 */
function 建模型(L0, H0) {
  const a = (SAFE_H(720)) - H0 * L0;
  return {
    a: +a.toFixed(4),
    H0,
    预测: (h) => (SAFE_H(h) - a) / H0,
  };
}

for (const 臂 of 臂表) {
  let br = null; let p = null; let nid = null;
  const 记 = { 键: 臂.键, 组: 臂.组, kind: 臂.kind, 名: 臂.名, vw: 臂.vw, vh: 臂.vh };
  try {
    记.L0基线 = 基线落点[臂.kind];

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

    // 前提：aria 精确匹配，现找现量；盒尺寸逐臂现量（不跨批硬编码）
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
    // 🔴 修掉第一轮的自伤：只查「读得到」与「不小于会截顶的 1.2」，不按某个视口标定的绝对值
    if (记.点之前 === null) throw new Error('点之前读不到 scale');
    if (记.点之前 < 1.2) throw new Error('点之前缩放过低（' + 记.点之前 + '），放大键可能没生效');

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

    // 📌 本臂盒高对应的隐含 inset（用**本臂现量**的盒，不跨批硬编码）
    记.隐含a = +(SAFE_H(臂.vh) - 目标.H * 记.终点).toFixed(4);
    记.较基线动 = +(记.终点 - 记.L0基线).toFixed(6);
    if (臂.期望 !== undefined) {
      记.期望 = 臂.期望;
      记.命中期望 = Math.abs(记.终点 - 臂.期望) < 1e-6;
    }

    log(臂.键.padEnd(14) + '｜视口' + String(臂.vw + 'x' + 臂.vh).padEnd(10)
      + '｜盒' + String(目标.W + 'x' + 目标.H).padEnd(11)
      + '｜z0=' + String(记.点之前).padEnd(7)
      + '｜落点=' + String(记.终点).padEnd(10)
      + '｜隐含a=' + String(记.隐含a).padEnd(10)
      + '｜较基线动=' + 记.较基线动);
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

// P0
const d1 = 取('D1文本-720'); const d2 = 取('D2文本-h600');
const 判定P0 = (d1 && Math.abs(d1.终点 - 1.75) < 1e-6 && d2 && Math.abs(d2.终点 - 1.375) < 1e-6)
  ? '✅ P0：文本臂 ' + (d1 ? d1.终点 : '—') + '（1212×720，期望 1.75）、' + (d2 ? d2.终点 : '—') + '（1212×600，期望 1.375）逐字命中 ⇒ 尺子没漂，本批读数可用'
  : '🔴 P0：文本臂 720→' + (d1 ? d1.终点 : '—') + '、600→' + (d2 ? d2.终点 : '—') + ' ≠ 期望 ⇒ 本批读数作废';

// P1/P2：常数 inset 直线的相对偏差
function 形状(kind) {
  const 基 = 取('C1音频-基线') && kind === '音频' ? 取('C1音频-基线')
    : (kind === '视频' ? 取('C2视频-基线') : 取('C3时间线-基线'));
  const 键集 = kind === '音频' ? ['C1音频-基线', 'H2音频-h600', 'H1音频-h1080']
    : (kind === '视频' ? ['C2视频-基线', 'H4视频-h600', 'H3视频-h1080'] : []);
  if (!基 || !基.画布盒) return { kind, 结论: '🔴 基线臂无效' };
  const 模型 = 建模型(基.终点, 基.画布盒.H);
  const 点 = [{ h: 720, 实测: 基.终点, 来源: 基.键, 盒H: 基.画布盒.H }];
  for (const k of 键集) {
    const x = 取(k);
    if (x) 点.push({ h: 臂表.find((y) => y.键 === k).vh, 实测: x.终点, 来源: k, 盒H: x.画布盒.H });
  }
  // 批次 314 第一轮的两点也并进来（当时盒尺寸同族，未逐臂复量，标注来源）
  if (kind === '音频') {
    点.push({ h: 900, 实测: 1.66349, 来源: 'b314第一轮 A1', 盒H: 基.画布盒.H });
  } else {
    点.push({ h: 900, 实测: 0.926991, 来源: 'b314第一轮 A3', 盒H: 基.画布盒.H });
  }
  点.sort((x, y) => x.h - y.h);
  const 表 = 点.map((x) => {
    const 预测 = 模型.预测(x.h);
    const δ = (x.实测 - 预测) / 预测;
    return { h: x.h, 来源: x.来源, 盒H: x.盒H, 实测: x.实测, 预测: +预测.toFixed(6), δ: +(δ * 100).toFixed(3) + '%', 隐含a: +(SAFE_H(x.h) - x.盒H * x.实测).toFixed(4), 落在线上: Math.abs(δ) <= 0.01 };
  });
  const 符号 = 表.map((x) => (x.δ.startsWith('-') ? -1 : 1));
  const 同号 = 符号.every((s) => s === 符号[0]);
  return {
    kind, 模型常数a: 模型.a, 基线盒H: 基.画布盒.H, 表,
    结论: 同号
      ? '⚠️ ' + 表.length + ' 点 δ 同号（' + 符号[0] > 0 ? '全正' : '全负' + '），最大 |δ|=' + Math.max.apply(null, 表.map((x) => Math.abs(parseFloat(x.δ)))).toFixed(3) + '% ⇒ 📌 偏一条直线但不在线上 ⇒ 🔴 **「常数 inset」不是精确关系**'
      : '⚠️ ' + 表.length + ' 点 δ **变号** ⇒ 🔴 **不是单一仿射关系，不许拟合**；如实记这四点',
  };
}

const 形状音频 = 形状('音频');
const 形状视频 = 形状('视频');

// P1 轴：只变宽动不动
function 轴(kind, 键) {
  const x = 取(键); const 基 = kind === '音频' ? 取('C1音频-基线') : (kind === '视频' ? 取('C2视频-基线') : 取('C3时间线-基线'));
  if (!x || !基) return kind + '：臂不全';
  const 动 = Math.abs(x.终点 - 基.终点) > 5e-5;
  const 模型M宽 = +(SAFE_W(x.vw) / (SAFE_W(1212) / 基.终点)).toFixed(6);
  return kind + '：落 ' + 基.终点 + ' → ' + x.终点 + '（动 ' + 动 + '）｜M宽预测 ' + 模型M宽 + '｜M高预测 ' + 基.终点
    + '｜' + (动 ? '✅ 变宽会动 ⇒ 宽度项对 ' + kind + ' 生效' : '📌 变宽不动 ⇒ ' + kind + ' 只受视口高影响');
}

out.判定 = {
  有效臂: 好.length + '/' + 臂表.length,
  判定P0_尺子: 判定P0,
  判定P1_轴: [轴('音频', 'W1音频-宽变'), 轴('视频', 'W2视频-宽变'), 轴('时间线', 'W3时间线-宽变')],
  判定P1P2_形状: { 音频: 形状音频, 视频: 形状视频 },
  逐臂: 好.map((x) => ({ 键: x.键, 视口: x.vw + 'x' + x.vh, 盒: x.画布盒, z0: x.点之前, 落点: x.终点, 隐含a: x.隐含a, 较基线动: x.较基线动 })),
};
log('\n════ 判定 ════\n' + JSON.stringify(out.判定, null, 1));

// ───────── 末态独立复查 ─────────
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
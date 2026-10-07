/**
 * 批次 308 · 低起点分支：终点从哪一点开始脱离 `vs`？—— 沿 `z0` 密集扫。
 *
 * 🔴 起意：批次 307 把「`z0=1.93` 那条臂」收窄到三个已知 ——
 *    **稳定**（七次、跨四批、相对极差 `1.49%`）、**`≠ vs`**（差 `12%`）、**与等待时长无关**（否掉「定点迭代未收敛」）。
 *    🔴 **真因仍未测。**
 *
 * 📌 本批换个入口：**不追某一个 `z0`，而是沿 `z0` 扫一串，找「脱离点」。**
 *    📌 依据是已知读数里那条最干净的线索：
 *    🔴 **`z0 = 1.34` 时终点逐字等于 `z0`（不跳）**，
 *      而 `z0 = 1.608 / 1.93` 都跳到了 `≈1.55–1.56`。
 *      ⇒ 📌 **说明存在一个门：低到某个 `z0` 就不动，越过就跳到另一处。**
 *
 * 📌 **判据（**测量前写死**）：
 *   **P1** 存在**不跳区**（终点 `=== z0`）与**跳区**（终点 `≠ z0`），
 *          两者之间有一个**转折 `z0`** ⇒ 📌 记下转折点落在哪两档之间；
 *   **P2** 跳区的终点是否**逐字等于同一个值** ——
 *          🔴 若逐字相同 ⇒ 第二分支是**定值**；
 *          🔴 若不相同 ⇒ 第二分支**本身是带噪的**，📌 按立规 113 只报区间；
 *   **P3** 🔴 **必须有一个 `z0 > vs` 的阳性对照臂落 `vs = 1.75`**，
 *          否则跳区读数不可用（尺子漂了就一切免谈，批次 307 P3 的教训）。
 *
 * 🔴 **前置自查（本批的教训来自批次 307）**：
 *    批次 307 判定段崩在 `P1_A is not defined`，且该错**犯了两次**。
 *    📌 本批把判定变量名与输出键**分开写**，🔴 **不再出现 `键: 值` 简写里值是裸标识符**。
 *
 * 前提检查：轴向自检 / 落定自检（连读三次）/ 点击生效自检 /
 *   `aria` 精确匹配现找现量 / 参数写死（按键次数是唯一变量）/ 每臂独立浏览器。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const STATE = `${process.env.HOME}/.jimeng-automation/state.json`;
const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b308.json';
const 放大键 = 'Meta+Equal';
const w = 1212; const h = 720;
const kind = '文本'; const 名 = '文本 1';
/** 📌 批次 306/307 反复测到的 vs（写死当基准） */
const 基准vs = 1.75;

/**
 * 📌 按键次数表：密集扫 `z0`。
 * 📌 已知（历史）：`按8→1.34`、`按9→?`、`按10→1.608`、`按11→1.93`、`按13→2.779`。
 * 📌 🔴 **转折点若落在 9–11 之间，这里就是最密的**；📌 `按12` 是历史 `2.316` 那档。
 */
const 臂表 = [
  { 键: '按8', 按: 8 }, { 键: '按9', 按: 9 }, { 键: '按10', 按: 10 },
  { 键: '按11', 按: 11 }, { 键: '按12', 按: 12 },
  { 键: '按13对照', 按: 13, 对照: true },
];

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b308',
  问: '低起点分支：终点从哪一点开始脱离 vs=1.75？跳区终点是定值还是带噪的？',
  判据: {
    P1: '存在不跳区(终点===z0)与跳区(终点≠z0)，记下转折点落在哪两档之间',
    P2: '跳区终点逐字相同⇒定值；否则带噪，只报区间（立规113）',
    P3: '须有一个 z0>vs 的对照臂落 vs=1.75，否则跳区读数不可用',
  },
  基准vs, w, h, 臂表, 臂: [], 判定: {},
};

for (const A of 臂表) {
  let br = null; let p = null; let nid = null;
  const 记 = { 键: A.键, 按: A.按, 对照: !!A.对照 };
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
    if (!记.点击生效) throw new Error(`点击未生效（选中=${JSON.stringify(选)}）`);
    记.跳 = (读3 !== z0 && 读3 < z0);
    记.落vs = Math.abs(读3 - 基准vs) < 1e-6;
    记.距vs = +(基准vs - 读3).toFixed(5);
    log(`${A.键.padEnd(9)}｜z0=${String(z0).padEnd(9)}｜终点=${String(读3).padEnd(10)}｜${记.跳 ? '跳  ' : '不跳'}｜落vs=${记.落vs}｜距vs=${记.距vs}`);
  } catch (e) {
    记.错误 = e.message;
    log(`${A.键.padEnd(9)}🔴 ${e.message}`);
  } finally {
    try { if (p) await p.close(); } catch (e) { /* 忽略 */ }
    try { if (br) await br.close(); } catch (e) { /* 忽略 */ }
    out.臂.push(记);
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

// ───────── 判定 ─────────
// 🔴 变量名与输出键**分开写**，避免批次 307 那类 `键: 裸标识符` 的 ReferenceError
const 好 = out.臂.filter((x) => !x.错误 && x.点击生效 && x.终点 !== undefined && x.落定).sort((a, b) => a.按 - b.按);
const 对照臂 = 好.find((x) => x.对照);
const 实验臂 = 好.filter((x) => !x.对照);
const 不跳 = 实验臂.filter((x) => !x.跳);
const 跳区 = 实验臂.filter((x) => x.跳);

const 判定P1 = (不跳.length > 0 && 跳区.length > 0)
  ? `✅ P1：存在不跳区（${不跳.map((x) => `${x.键}/z0=${x.z0}`).join('、')}）与跳区（${跳区.map((x) => `${x.键}/z0=${x.z0}→${x.终点}`).join('、')}）⇒ 📌 **转折点落在 ${不跳[不跳.length - 1].键}(z0=${不跳[不跳.length - 1].z0}) 与 ${跳区[0].键}(z0=${跳区[0].z0}) 之间**`
  : `⚠️ P1：本次未同时取到不跳区与跳区（不跳 ${不跳.length} / 跳 ${跳区.length}）`;

const 跳终点 = 跳区.map((x) => x.终点);
const 跳极差 = 跳终点.length > 1 ? Math.max(...跳终点) - Math.min(...跳终点) : null;
const 判定P2 = (跳终点.length >= 2 && 跳极差 < 1e-9)
  ? `✅ P2：跳区终点 ${JSON.stringify(跳终点)} **逐字相同** ⇒ 第二分支是**定值**`
  : (跳终点.length >= 2
    ? `⚠️ P2：跳区终点 ${JSON.stringify(跳终点)} 极差 ${跳极差.toFixed(5)}（非 0）⇒ 🔴 第二分支**带噪**，📌 按立规 113 只报区间 [${Math.min(...跳终点)}, ${Math.max(...跳终点)}]`
    : `（跳区样本不足，${跳终点.length} 条）`);

const 判定P3 = 对照臂 && 对照臂.落vs
  ? `✅ P3：对照臂（${对照臂.键}/z0=${对照臂.z0}）终点 ${对照臂.终点} 逐字落 vs=${基准vs} ⇒ 尺子没漂，跳区读数可用`
  : `🔴 P3：对照臂未落 vs=${基准vs}（终点 ${对照臂 ? 对照臂.终点 : '—'}）⇒ 本批跳区读数作废`;

out.判定 = {
  有效臂: `${好.length}/${臂表.length}`,
  逐档读数: 好.map((x) => ({ 按: x.按, z0: x.z0, 终点: x.终点, 跳: x.跳, 距vs: x.距vs })),
  不跳区: 不跳.map((x) => `${x.键}(z0=${x.z0})`),
  跳区: 跳区.map((x) => `${x.键}(z0=${x.z0}→${x.终点})`),
  跳区终点极差: 跳极差,
  判定P1: 判定P1,
  判定P2: 判定P2,
  判定P3: 判定P3,
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
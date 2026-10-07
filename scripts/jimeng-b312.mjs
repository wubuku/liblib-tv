/**
 * 批次 312 · 落点是否依赖「点之前的缩放」？—— 面向用户的那一维。
 *
 * 🔴 起意：批次 311 产出落点表（视口 1212×720、按 13 次键 z0=2.779），但 📌 **那一列不是
 *    用户会遇到的场景** —— 手册正文测的是「从默认缩放直接点搜索结果」。
 *    🔴 且批次 309 在 bundle 里发现 `vs` 的第三项 `i` 默认 `Infinity`，
 *    📌 **但有一个调用点显式传了 `n = viewport.zoom`**（即「点之前的缩放」）
 *    ⇒ 🔴 **落点很可能依赖点之前的缩放**，而批次 311 把这一维固定住了。
 *
 * 📌 **判据（测量前写死）**：
 *   **P1** 同一节点、同一视口，扫一串「点之前的缩放」，
 *          📌 看落点是否随之变化 ⇒ 变化则「点之前的缩放」是落点的一个因子；
 *   **P2** 🔴 **正交对照**：把视口也扫一串，若「点之前的缩放」与「视口宽」对落点的
 *          影响形状不同 ⇒ 📌 两个独立因子；若形状相同 ⇒ 🔴 **其实是一个因子，别当成两个**；
 *   **P3** 🔴 **阳性对照**：必须有一档落 `1.75`（批次 311 已证的 `文本` 高分支），
 *          🔴 否则本批读数不可用。
 *
 * 📌 **口径对齐（先做，否则整批读数无法与正文对话）**：
 *   📌 正文 UI 百分比 === `.react-flow__viewport` 的 `scale()`，
 *   📌 验算：正文「窗口 1215 → 音频 68 落 29%、节点屏上 93×93」，而画布盒是 `320×320`
 *   ⇒ 📌 `93/320 = 0.29063 = 29.06%`，与正文逐字吻合 ⇒ **同一口径**。
 *
 * 前提检查：轴向自检 / 落定自检（连读两次）/ 点击生效自检 /
 *   `aria` 精确匹配现找现量 / 参数写死 / 每臂独立浏览器。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const STATE = `${process.env.HOME}/.jimeng-automation/state.json`;
const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b312.json';
const 放大键 = 'Meta+Equal';
const h = 720;
const kind = '文本'; const 名 = '文本 1';

/**
 * 📌 臂表：两个正交维度。
 * 📌 组 A（固定视口 1212，扫「点之前的缩放」）：用不同按键次数造不同的 z0。
 * 📌 组 B（固定按键 0 次 = 默认缩放，扫视口宽）：📌 对照「视口宽」的影响形状。
 */
const 臂表 = [
  { 键: 'A按0', 组: 'A', vw: 1212, 按: 0 },
  { 键: 'A按6', 组: 'A', vw: 1212, 按: 6 },
  { 键: 'A按9', 组: 'A', vw: 1212, 按: 9 },
  { 键: 'A按11', 组: 'A', vw: 1212, 按: 11 },
  { 键: 'A按13', 组: 'A', vw: 1212, 按: 13 },
  { 键: 'B宽900', 组: 'B', vw: 900, 按: 0 },
  { 键: 'B宽1212', 组: 'B', vw: 1212, 按: 0 },
  { 键: 'B宽1400', 组: 'B', vw: 1400, 按: 0 },
];

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b312',
  问: '取景落点依赖「点之前的缩放」吗？它与「视口宽」是两个独立因子还是同一个？',
  判据: {
    P1: '同一节点同一视口，扫点之前的缩放，看落点是否变',
    P2: '正交对照：与扫视口宽的影响形状不同⇒两个独立因子；相同⇒其实是一个',
    P3: '阳性对照：须有一档落 1.75，否则读数不可用',
  },
  口径: 'UI 百分比 === viewport scale()（正文 93/320=29.06% 与 scale 逐字吻合）',
  h, 臂表, 臂: [], 判定: {},
};

for (const A of 臂表) {
  let br = null; let p = null; let nid = null;
  const 记 = { 键: A.键, 组: A.组, vw: A.vw, 按: A.按 };
  try {
    br = await chromium.launch({ headless: true });
    const ctx = await br.newContext({ storageState: STATE, viewport: { width: A.vw, height: h } });
    p = await ctx.newPage();
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 60000 });
    await p.waitForTimeout(6000);
    const 实际 = await p.evaluate(() => ({ w: innerWidth, h: innerHeight }));
    if (实际.w !== A.vw || 实际.h !== h) throw new Error(`轴向自检失败：${实际.w}×${实际.h}`);
    if (实际.h < 249) throw new Error('视口高不足 249');

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
    await p.waitForTimeout(1600);
    const 读缩放 = () => p.evaluate(() => {
      const vp = document.querySelector('.react-flow__viewport');
      const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
      return m ? Number(m[1]) : null;
    });
    const z0 = await 读缩放();      // 📌 这就是「点之前的缩放」
    记.点之前缩放 = z0;
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
    const r1 = await 读缩放();
    await p.waitForTimeout(2600);
    const r2 = await 读缩放();
    记.读1 = r1; 记.读2 = r2;
    记.落定 = (r1 === r2);
    记.终点 = r2;
    const 选 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((x) => x.dataset.id));
    记.点击生效 = 选.includes(nid);
    if (!记.点击生效) throw new Error(`点击未生效`);
    记.是否变化 = Math.abs(r2 - z0) > 1e-9;
    记.落175 = Math.abs(r2 - 1.75) < 1e-6;
    log(`${A.键.padEnd(9)}｜视口${String(A.vw).padEnd(6)}｜点之前=${String(z0).padEnd(9)}｜终点=${String(r2).padEnd(10)}｜${记.是否变化 ? '跳' : '不跳'}${记.落175 ? '｜落1.75' : ''}`);
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
const 好 = out.臂.filter((x) => !x.错误 && x.点击生效 && x.落定 && x.终点 !== undefined);
const A组 = 好.filter((x) => x.组 === 'A').sort((a, b) => a.点之前缩放 - b.点之前缩放);
const B组 = 好.filter((x) => x.组 === 'B').sort((a, b) => a.vw - b.vw);

const A终点 = A组.map((x) => x.终点);
const A极差 = A终点.length > 1 ? Math.max(...A终点) - Math.min(...A终点) : null;
const B终点 = B组.map((x) => x.终点);
const B极差 = B终点.length > 1 ? Math.max(...B终点) - Math.min(...B终点) : null;

const 有175 = 好.some((x) => x.落175);
const 判定P3 = 有175
  ? '✅ P3：有一档落 1.75（' + 好.filter((x) => x.落175).map((x) => `${x.键}=${x.终点}`).join('、') + '）⇒ 尺子没漂'
  : '🔴 P3：无任何一档落 1.75 ⇒ 本批读数不可用';

const 判定P1 = A极差 !== null && A极差 > 1e-6
  ? '✅ P1：固定视口 `1212`，只改「点之前的缩放」，落点极差 **' + A极差.toFixed(5)
    + '** ⇒ 🔴 **落点依赖「点之前的缩放」**，📌 它是落点的一个独立因子'
  : (A极差 !== null ? '✅ P1：固定视口下落点极差 ' + A极差 + '（=0）⇒ 落点**不依赖**点之前的缩放' : '（A 组不足）');

const 判定P2 = (A极差 !== null && B极差 !== null)
  ? '📌 P2：A 组（变「点之前的缩放」）落点极差 **' + A极差.toFixed(5)
    + '**；B 组（变「视口宽」）落点极差 **' + B极差.toFixed(5)
    + '**。'
    + (Math.abs(A极差 - B极差) > 0.01
      ? '📌 两者量级不同 ⇒ **是两个因子**，但 📌 **极差大小不能证明它们独立** —— 🔴 需下一批做「双因子交叉扫」才敢说独立'
      : '📌 两者量级相近 ⇒ 🔴 **不能就此说是两个因子**，需看逐点对照')
  : '（样本不足）';

out.判定 = {
  有效臂: `${好.length}/${臂表.length}`,
  A组_固定视口变点前缩放: A组.map((x) => ({ 点之前: x.点之前缩放, 终点: x.终点 })),
  B组_固定缩放变视口宽: B组.map((x) => ({ 视口宽: x.vw, 点之前: x.点之前缩放, 终点: x.终点 })),
  A极差: A极差, B极差: B极差,
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
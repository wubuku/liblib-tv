/**
 * 批次 304 · 「`文本` 在低起点下的 `≈1.53` 平台」是什么外框造成的？—— 直接量。
 *
 * 🔴 起意：批次 303 查出 `文本 1` 在 `z0 = 1.93` 时落 `1.53807`、`z0 = 1.608` 时落 `1.53221`，
 *    🔴 而批次 301 已证明 `音频` 的外框是屏幕固定的（屏宽 `6/6` 恒为 `680`）。
 *    ⇒ 📌 本批把同一把尺子量到 `文本` 的**每一个起点**上：
 *        **`node-toolbar` 的屏宽到底是不是也恒为 `680`？**
 *
 * 📌 判据（**测量前写死**）：
 *   **P1** `文本` 的工具条屏宽在**所有起点**都等于 `680` ⇒ 它与音频是同一块屏幕固定外框
 *   **P2** 屏宽随起点变 ⇒ 🔴 `文本` 的外框**不是**屏幕固定的 ⇒ 批次 301 的机制不适用
 *   **P3** 对账：由终点反推的 `compoundW = safeW / 终点`，应与实测的
 *          `工具条屏宽 / 终点`（即画布宽）**一致** ⇒ 证实 `vs` 由宽度项决定
 *
 * 📌 同时对账音频侧两档，确认尺子本身没漂。
 *
 * 前提检查：轴向自检 / 落定自检 / 点击生效自检 / `aria` 精确匹配现找现量 /
 *   参数写死（放大键次数是唯一变量）/ 每臂独立浏览器。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const STATE = `${process.env.HOME}/.jimeng-automation/state.json`;
const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b304.json';
const 放大键 = 'Meta+Equal';
const w = 1212;

const 臂表 = [
  { 键: '文本1/13', kind: '文本', 名: '文本 1', 按: 13 },
  { 键: '文本1/12', kind: '文本', 名: '文本 1', 按: 12 },
  { 键: '文本1/11', kind: '文本', 名: '文本 1', 按: 11 },
  { 键: '文本1/10', kind: '文本', 名: '文本 1', 按: 10 },
  { 键: '文本1/9',  kind: '文本', 名: '文本 1', 按: 9 },
  { 键: '音频1/11', kind: '音频', 名: '音频 1', 按: 11 },
  { 键: '音频1/10', kind: '音频', 名: '音频 1', 按: 10 },
];

const vf = (z) => Math.min(8, Math.max(0.08, z));
const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b304',
  问: '文本在低起点下的那个 ≈1.53 平台，是哪个外框造成的？它的屏宽恒定吗？',
  判据: { P1: '文本工具条屏宽在所有起点都等于 680 ⇒ 与音频同一块屏幕固定外框', P2: '屏宽随起点变 ⇒ 不是屏幕固定的' },
  w, 臂表, 臂: [], 判定: {},
};

for (const A of 臂表) {
  let br = null; let p = null; let nid = null;
  const 记 = { 键: A.键, w, 按: A.按, kind: A.kind, 名: A.名 };
  try {
    br = await chromium.launch({ headless: true });
    const ctx = await br.newContext({ storageState: STATE, viewport: { width: w, height: 720 } });
    p = await ctx.newPage();
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 60000 });
    await p.waitForTimeout(6000);
    const 实际 = await p.evaluate(() => ({ w: innerWidth, h: innerHeight }));
    if (实际.w !== w || 实际.h !== 720) throw new Error(`轴向自检失败：实测 ${实际.w}×${实际.h}`);

    const ariaWant = `${A.kind} node: ${A.名}`;
    const 目标 = await p.evaluate((aria) => {
      const e = Array.from(document.querySelectorAll('.react-flow__node[data-id]'))
        .find((x) => x.getAttribute('aria-label') === aria);
      return e ? { id: e.dataset.id, W: e.offsetWidth, H: e.offsetHeight } : null;
    }, ariaWant);
    if (!目标) throw new Error(`找不到 aria 为「${ariaWant}」的节点`);
    nid = 目标.id;
    记.画布盒 = { W: 目标.W, H: 目标.H };

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
    if (!(z0 > 0.5)) throw new Error(`z0(${z0}) 低于 .5，无法观察`);

    const 钮 = await p.evaluate(() => {
      const b = document.querySelector('button[aria-label="搜索"]');
      if (!b) return null;
      const r = b.getBoundingClientRect();
      return { 中心: [r.x + r.width / 2, r.y + r.height / 2], 可见: r.width > 0 && r.height > 0 && r.y >= 0 && r.bottom <= innerHeight };
    });
    if (!钮 || !钮.可见) throw new Error('找不到可见的搜索钮');
    await p.mouse.click(钮.中心[0], 钮.中心[1]);
    await p.waitForTimeout(1600);

    let 行 = null; let 用名 = null;
    for (const 名 of [A.名, ariaWant, A.kind]) {
      await p.evaluate(() => { const i = document.querySelector('[data-testid="canvas-search-panel"] input'); if (i) { i.focus(); i.select(); } });
      await p.keyboard.type(名, { delay: 80 });
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
      if (r && r.可见) { 行 = r; 用名 = 名; break; }
    }
    if (!行) throw new Error(`搜不到「${A.名}」的可见结果行`);
    记.用名 = 用名;
    await p.mouse.click(行.中心[0], 行.中心[1]);
    await p.waitForTimeout(3200);
    const a1 = await 读缩放();
    await p.waitForTimeout(2600);
    const 后 = await p.evaluate(() => {
      const vp = document.querySelector('.react-flow__viewport');
      const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
      const 选 = Array.from(document.querySelectorAll('.react-flow__node.selected')).map((x) => x.dataset.id);
      const grab = (sel) => { const e = document.querySelector(sel); if (!e) return null; const r = e.getBoundingClientRect(); return { x: +r.x.toFixed(1), y: +r.y.toFixed(1), w: +r.width.toFixed(1), h: +r.height.toFixed(1) }; };
      return {
        scale: m ? Number(m[1]) : null,
        选中: 选,
        工具条: grab('[data-testid="node-toolbar"]'),
        生成表单: grab('[data-testid="audio-generation-form"]') || grab('[data-testid="text-generation-form"]') || grab('[data-testid="video-generation-form"]'),
        全部带toolbar: Array.from(document.querySelectorAll('[data-testid*="toolbar"],[data-testid*="generation-form"]')).map((e) => {
          const r = e.getBoundingClientRect();
          return { testid: e.getAttribute('data-testid'), w: +r.width.toFixed(1), h: +r.height.toFixed(1) };
        }),
      };
    });
    记.z后1 = a1;
    记.落定 = a1 === 后.scale;
    记.点击生效 = 后.选中.includes(nid);
    if (!记.点击生效) throw new Error(`点击未生效（选中=${JSON.stringify(后.选中)}）`);
    记.终点 = 后.scale;
    记.工具条 = 后.工具条;
    记.生成表单 = 后.生成表单;
    记.全部带toolbar = 后.全部带toolbar;
    记.与起点逐字相同 = 后.scale === z0;
    // 对账：宽度项反推的 compoundW  vs  实测工具条画布宽
    const safeW = Math.max(100, w - 532);
    记.反推compoundW = +(safeW / 后.scale).toFixed(3);
    记.实测工具条画布宽 = 后.工具条 ? +(后.工具条.w / 后.scale).toFixed(3) : null;
    记.差 = (后.工具条 && Math.abs(记.反推compoundW - 记.实测工具条画布宽) <= 2) ? '✅ 一致' : (后.工具条 ? '🔴 不一致' : '（无工具条）');
    log(`${A.键.padEnd(10)}｜z0=${String(z0).padEnd(8)}｜终点=${String(后.scale).padEnd(10)}｜工具条屏 ${后.工具条 ? 后.工具条.w + '×' + 后.工具条.h : '—'}｜反推 compoundW=${记.反推compoundW}｜实测画布宽=${记.实测工具条画布宽}｜${记.差}`);
  } catch (e) {
    记.错误 = e.message;
    log(`${A.键.padEnd(10)}🔴 ${e.message}`);
  } finally {
    try { if (p) await p.close(); } catch (e) { /* 忽略 */ }
    try { if (br) await br.close(); } catch (e) { /* 忽略 */ }
    out.臂.push(记);
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

const 好 = out.臂.filter((x) => !x.错误 && x.点击生效 && x.终点 !== undefined && x.落定);
const 文本 = 好.filter((x) => x.kind === '文本');
const 音频 = 好.filter((x) => x.kind === '音频');
const 屏宽集 = (arr) => arr.map((x) => (x.工具条 ? x.工具条.w : null));

log('\n════ 判定表 ════');
for (const x of 好) {
  log(`  ${x.键.padEnd(10)} z0=${String(x.z0).padEnd(8)} 终点=${String(x.终点).padEnd(10)} 工具条屏宽=${x.工具条 ? x.工具条.w : '—'} 屏高=${x.工具条 ? x.工具条.h : '—'} 全toolbar=${JSON.stringify(x.全部带toolbar)}`);
}

const 文本屏宽 = 屏宽集(文本).filter((v) => v !== null);
const 文本恒680 = 文本屏宽.length > 0 && 文本屏宽.every((v) => Math.abs(v - 680) < 1);
const 音频屏宽 = 屏宽集(音频).filter((v) => v !== null);
const 对账过 = 好.filter((x) => x.差 === '✅ 一致').length;

out.判定 = {
  有效臂: `${好.length}/${臂表.length}`,
  文本工具条屏宽: 文本屏宽,
  音频工具条屏宽: 音频屏宽,
  P1_P2: 文本恒680
    ? `✅ P1：文本的工具条屏宽在全部 ${文本屏宽.length} 个起点上都等于 680 ⇒ 与音频是同一块屏幕固定外框`
    : `🔴 P2：文本的工具条屏宽 ${JSON.stringify(文本屏宽)} 不是恒 680 ⇒ 不是屏幕固定的`,
  P3_宽度项对账: `${对账过}/${好.filter((x) => x.工具条).length} 条臂「反推 compoundW」与「实测工具条画布宽」一致`,
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
/**
 * 批次 297 · 抖动的因子是什么？—— 沿用批次 296 的已验证设计，**只加读数不加变量**。
 *
 * 🔴 起意：批次 296 测出「不跳侧跨三遍极差 0、跳变侧极差 ≈0.02」，
 *    证明**抖动不是测量噪声**，但**没说是谁在抖**。
 *    📌 本批不去改实验设计（那会引入新变量），而是**在同一条路径上多读几个量**，
 *    然后看 `vs` 到底跟着哪一个走。
 *
 * 📌 两条**测量前写死**的假设（不成立就不成立，不事后编故事）：
 *   H1 **`vs` 与落点无关** —— 批次 248/231 记过纵向落点中心 Y 从 `360` 变 `≈257~260`，
 *      若落点与 `vs` 无关，则落点**不是**因子。
 *   H2 **`vs` 与落点强相关** —— 若两者同涨同落，则落点**就是**因子（立规 169：找能区分假设的自由度）。
 *
 * 🔴 一条必须先说的测量纪律：`vs` 的跨遍噪声就有 `≈0.02`，
 *    🔴 **所以单条读数之间比大小是无效的** —— 任何「相关」都必须先看**多遍**，
 *    并且报的是「同组内是否同向」，不是「两个数相减」；本批每组 `3` 遍。
 *
 * 记录项（每臂全记）：`vs`、节点屏上中心 X/Y、屏上盒尺寸、是否完整落在视口内、
 *   画布空间盒、页面上是否开着任何遮罩面板。
 * 三道前提照旧：P0 确定性对照（不跳侧三遍逐字相同）/ P1 阈值对照（`1211` 不跳）/ P2 落定自检。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const STATE = `${process.env.HOME}/.jimeng-automation/state.json`;
const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b297.json';
const 放大键 = 'Meta+Equal';
const 按够 = 13;

const 臂表 = [];
for (const 遍 of [1, 2, 3]) {
  臂表.push({ w: 1212, 遍, kind: '文本', 名: '文本 1', 角色: 'P0 确定性对照' });
  臂表.push({ w: 1212, 遍, kind: '音频', 名: '音频 1', 角色: '主体（跳）' });
  臂表.push({ w: 1212, 遍, kind: '视频', 名: '视频 1', 角色: '主体（跳）' });
}
臂表.push({ w: 1211, 遍: 1, kind: '音频', 名: '音频 1', 角色: 'P1 阈值对照' });
臂表.push({ w: 1211, 遍: 1, kind: '文本', 名: '文本 1', 角色: 'P1 阈值对照' });

const 屏上律 = (ww) => Math.max(100, ww - 532);
const vf = (z) => Math.min(8, Math.max(0.08, z));
const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b297', 问: 'vs 的跨遍抖动跟着哪一个量走？', 假设: { H1: 'vs 与落点无关', H2: 'vs 与落点强相关' }, 臂表, 臂: [], 判定: {} };

const 读 = (p, nid) => p.evaluate((nid) => {
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  const e = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  let 屏 = null;
  if (e) {
    const r = e.getBoundingClientRect();
    屏 = {
      中心X: +(r.x + r.width / 2).toFixed(2),
      中心Y: +(r.y + r.height / 2).toFixed(2),
      屏宽: +r.width.toFixed(2),
      屏高: +r.height.toFixed(2),
      完整可见: r.x >= 0 && r.y >= 0 && r.right <= innerWidth && r.bottom <= innerHeight,
    };
  }
  // 页面上是否开着任何遮罩层（role=dialog / aria-modal / 高 z-index 的浮层）
  const 遮罩 = Array.from(document.querySelectorAll('[role="dialog"],[aria-modal="true"]'))
    .filter((d) => { const r = d.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
    .map((d) => d.getAttribute('aria-label') || d.getAttribute('data-testid') || d.className.toString().slice(0, 40));
  return {
    scale: m ? Number(m[1]) : null,
    选中: Array.from(document.querySelectorAll('.react-flow__node.selected')).map((x) => x.dataset.id),
    屏, 遮罩,
    元素数: document.querySelectorAll('.react-flow *').length,
  };
}, nid);

for (const A of 臂表) {
  let br = null; let p = null; let nid = null;
  const 记 = { w: A.w, 遍: A.遍, kind: A.kind, 名: A.名, 角色: A.角色 };
  try {
    br = await chromium.launch({ headless: true });
    const ctx = await br.newContext({ storageState: STATE, viewport: { width: A.w, height: 720 } });
    p = await ctx.newPage();
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 60000 });
    await p.waitForTimeout(6000);

    const 实际 = await p.evaluate(() => ({ w: innerWidth, h: innerHeight }));
    if (实际.w !== A.w || 实际.h !== 720) throw new Error(`轴向自检失败：实测 ${实际.w}×${实际.h}`);

    const ariaWant = `${A.kind} node: ${A.名}`;
    const 目标 = await p.evaluate((aria) => {
      const e = Array.from(document.querySelectorAll('.react-flow__node[data-id]'))
        .find((x) => x.getAttribute('aria-label') === aria);
      if (!e) return null;
      return { id: e.dataset.id, aria: e.getAttribute('aria-label'), W: e.offsetWidth, H: e.offsetHeight };
    }, ariaWant);
    if (!目标) throw new Error(`找不到 aria 为「${ariaWant}」的节点`);
    nid = 目标.id;
    记.节点id = nid;
    记.画布盒 = { W: 目标.W, H: 目标.H };
    const 闭式 = +vf(Math.min(屏上律(A.w) / 目标.W, (720 - 160) / 目标.H)).toFixed(6);
    记.闭式 = 闭式;

    for (let i = 0; i < 按够; i++) { await p.keyboard.press(放大键); await p.waitForTimeout(380); }
    await p.waitForTimeout(1200);
    const z0 = await 读(p, nid);
    记.z0 = z0.scale;
    if (z0.scale === null) throw new Error('读不到缩放');
    if (!(z0.scale > 闭式)) throw new Error(`z0(${z0.scale}) 不高于闭式(${闭式}) ⇒ 读不到平台`);

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
    await p.waitForTimeout(3000);
    const a1 = await 读(p, nid);
    await p.waitForTimeout(2500);
    const a2 = await 读(p, nid);
    记.z后1 = a1.scale;
    记.z后2 = a2.scale;
    记.落定 = a1.scale === a2.scale;
    记.选中 = a2.选中;
    记.点击生效 = a2.选中.includes(nid);
    if (!记.点击生效) throw new Error(`点击未生效（选中=${JSON.stringify(a2.选中)}）`);
    记.vs = a2.scale;
    记.跳了 = Math.abs(a2.scale - 闭式) > 2e-3;
    记.落点 = a2.屏;
    记.遮罩 = a2.遮罩;
    记.元素数 = a2.元素数;
    log(`w=${A.w}｜${A.kind} ${A.名}｜第${A.遍}遍｜vs=${a2.scale}｜中心 ${a2.屏 ? a2.屏.中心X + ',' + a2.屏.中心Y : '—'}｜屏盒 ${a2.屏 ? a2.屏.屏宽 + '×' + a2.屏.屏高 : '—'}｜完整 ${a2.屏 && a2.屏.完整可见}｜遮罩 ${a2.遮罩.length}｜元素 ${a2.元素数}`);
  } catch (e) {
    记.错误 = e.message;
    log(`w=${A.w}｜${A.kind} ${A.名}｜第${A.遍}遍 🔴 ${e.message}`);
  } finally {
    try { if (p) await p.close(); } catch (e) { /* 忽略 */ }
    try { if (br) await br.close(); } catch (e) { /* 忽略 */ }
    out.臂.push(记);
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

// ── 相关性：只看「同一节点的多遍之间」是否同向 ─────────────
const 好 = out.臂.filter((x) => !x.错误 && x.点击生效 && x.vs !== undefined && x.落定 && x.落点);
const 组 = {};
for (const x of 好.filter((y) => y.w === 1212)) {
  const k = `${x.kind} ${x.名}`;
  (组[k] ||= []).push(x);
}
const 表 = {};
for (const [k, 臂] of Object.entries(组)) {
  const vs = 臂.map((a) => a.vs);
  const cy = 臂.map((a) => a.落点.中心Y);
  const cx = 臂.map((a) => a.落点.中心X);
  const 屏高 = 臂.map((a) => a.落点.屏高);
  const spread = (v) => +(Math.max(...v) - Math.min(...v)).toFixed(4);
  // 同向判定：两个序列各自排序后，配对排名是否单调（正相关/负相关/无）
  const 同向 = (a, b) => {
    const idx = a.map((_, i) => i).sort((i, j) => a[i] - a[j]);
    const bs = idx.map((i) => b[i]);
    let up = true; let dn = true;
    for (let i = 1; i < bs.length; i++) { if (bs[i] <= bs[i - 1]) up = false; if (bs[i] >= bs[i - 1]) dn = false; }
    if (up) return '正相关';
    if (dn) return '负相关';
    return '无单调关系';
  };
  表[k] = {
    vs, 中心Y: cy, 中心X: cx, 屏高,
    vs极差: spread(vs), 中心Y极差: spread(cy), 中心X极差: spread(cx), 屏高极差: spread(屏高),
    vs对中心Y: 同向(vs, cy),
    vs对中心X: 同向(vs, cx),
    遮罩数: 臂.map((a) => (a.遮罩 || []).length),
    完整可见: 臂.map((a) => a.落点.完整可见),
  };
}

const p0过 = 表['文本 文本 1'] && 表['文本 文本 1'].vs极差 === 0;
const P1 = 臂表.filter((a) => a.w === 1211);
const p1过 = P1.every((a) => { const r = 好.find((x) => x.w === 1211 && x.kind === a.kind && x.名 === a.名); return r && !r.跳了; });

log('\n════ 相关性表（w=1212）════');
for (const [k, v] of Object.entries(表)) {
  log(`  ${k}`);
  log(`     vs   ${v.vs.join(' / ')}   极差 ${v.vs极差}`);
  log(`     中心Y ${v.中心Y.join(' / ')}   极差 ${v.中心Y极差}`);
  log(`     中心X ${v.中心X.join(' / ')}   极差 ${v.中心X极差}`);
  log(`     屏高  ${v.屏高.join(' / ')}   极差 ${v.屏高极差}`);
  log(`     vs 对中心Y = ${v.vs对中心Y}｜vs 对中心X = ${v.vs对中心X}｜遮罩数 ${JSON.stringify(v.遮罩数)}｜完整可见 ${JSON.stringify(v.完整可见)}`);
}

const 跳组 = Object.entries(表).filter(([k]) => k !== '文本 文本 1');
out.判定 = {
  有效臂: `${好.length}/${臂表.length}`,
  P0_确定性对照: p0过 ? '✅ 文本 1 三遍 vs 极差 0' : '🔴 文本 1 自己就不复现 ⇒ 整组作废',
  P1_阈值对照: p1过 ? '✅ 1211 上两条都不跳' : '🔴 1211 上出现跳变 ⇒ 整组作废',
  相关性: 表,
  结论: (p0过 && p1过)
    ? '（见逐条：H1/H2 哪一个成立以「相关性」字段为准，不在此处下结论）'
    : '🔴 前提没过 ⇒ 整组作废',
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

/**
 * 批次 300 · 「节点外框」是屏幕固定装饰还是画布空间元素？—— 用两点判据钉死。
 *
 * 🔴 起意：批次 298 从代码读出 `inset = attached + nodeChromeInsets × 1/max(zoom,.5)`，
 *    批次 299 在 DOM 里找到实体 `flow-node-title`（`32` 屏幕像素，贴在节点正上方），
 *    🔴 **但两者对不上** —— 那个乘子只有在元素**屏幕固定**时才有意义，
 *    而批次 299 的模型没能闭合。
 *
 * 📌 判据（**测量前写死**，用缩放差做杠杆）：
 *   本批在两个**缩放差 1.6 倍**的配置下量同一个元素的屏高 ——
 *     `w=1211` ⇒ `vs = 1.75`；`w=1212` ⇒ `vs ≈ 1.09`（比值 `≈1.60`）。
 *   **H1（屏幕固定）**：两处屏高**都等于 `32`**（比值 `1`）
 *   **H2（画布空间）**：屏高**按缩放同比缩放**（比值 `≈1.60`，即 `56` vs `35`）
 *   🔴 这两条互斥，**不需要统计、不需要多遍**，两点就能分开。
 *
 * 📌 顺带记：`compound` 的反推值（由 `vd` 居中推出）、`flow-node-selected-tag` 的尺寸、
 *   `flow-node-title` 的逐字文本（若标题长度不同是否影响尺寸）。
 *
 * 前提检查：轴向自检 / `z0 > 闭式` 硬门 / 落定自检 / 点击生效自检 / 参数写死 /
 *   `aria` 精确匹配现找现量 / 每臂独立浏览器。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const STATE = `${process.env.HOME}/.jimeng-automation/state.json`;
const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b300.json';
const 放大键 = 'Meta+Equal';
const 按够 = 13;

const 臂表 = [
  { w: 1211, kind: '音频', 名: '音频 1', 角色: '🔴 高缩放侧（vs=1.75），与 1212 侧配对' },
  { w: 1212, kind: '音频', 名: '音频 1', 角色: '🔴 低缩放侧（vs≈1.09）' },
  { w: 1211, kind: '文本', 名: '文本 1', 角色: '对照：外框为 0 的一侧' },
  { w: 1212, kind: '文本', 名: '文本 1', 角色: '对照：外框为 0 的一侧' },
  { w: 1211, kind: '视频', 名: '视频 1', 角色: '配对侧' },
  { w: 1212, kind: '视频', 名: '视频 1', 角色: '配对侧' },
];

const 屏上律 = (ww) => Math.max(100, ww - 532);
const vf = (z) => Math.min(8, Math.max(0.08, z));
const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b300',
  问: 'flow-node-title 是屏幕固定装饰，还是画布空间元素？',
  判据: { H1: '屏高在 1.75 与 1.09 两个缩放下都等于 32（比值 1）⇒ 屏幕固定', H2: '屏高按缩放同比（比值 ≈1.60）⇒ 画布空间' },
  臂表, 臂: [], 判定: {},
};

for (const A of 臂表) {
  let br = null; let p = null; let nid = null;
  const 记 = { w: A.w, kind: A.kind, 名: A.名, 角色: A.角色 };
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
      return { id: e.dataset.id, W: e.offsetWidth, H: e.offsetHeight };
    }, ariaWant);
    if (!目标) throw new Error(`找不到 aria 为「${ariaWant}」的节点`);
    nid = 目标.id;
    记.画布盒 = { W: 目标.W, H: 目标.H };
    const 闭式 = +vf(Math.min(屏上律(A.w) / 目标.W, (720 - 160) / 目标.H)).toFixed(6);
    记.闭式 = 闭式;

    for (let i = 0; i < 按够; i++) { await p.keyboard.press(放大键); await p.waitForTimeout(380); }
    await p.waitForTimeout(1200);
    const z0 = await p.evaluate(() => {
      const vp = document.querySelector('.react-flow__viewport');
      const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
      return m ? Number(m[1]) : null;
    });
    记.z0 = z0;
    if (z0 === null) throw new Error('读不到缩放');
    if (!(z0 > 闭式)) throw new Error(`z0(${z0}) 不高于闭式(${闭式}) ⇒ 读不到平台`);

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
    const a1 = await p.evaluate(() => { const vp = document.querySelector('.react-flow__viewport'); const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null; return m ? Number(m[1]) : null; });
    await p.waitForTimeout(2500);
    const 读 = await p.evaluate((nid) => {
      const vp = document.querySelector('.react-flow__viewport');
      const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
      const node = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
      const out = {
        scale: m ? Number(m[1]) : null,
        选中: Array.from(document.querySelectorAll('.react-flow__node.selected')).map((x) => x.dataset.id),
        节点: null, 标题: null, 标签: null,
      };
      if (node) {
        const r = node.getBoundingClientRect();
        out.节点 = { top: +r.top.toFixed(2), bottom: +r.bottom.toFixed(2), w: +r.width.toFixed(2), h: +r.height.toFixed(2), centerY: +(r.top + r.height / 2).toFixed(2) };
        const t = node.querySelector('[data-testid="flow-node-title"]');
        if (t) { const q = t.getBoundingClientRect(); out.标题 = { top: +q.top.toFixed(2), h: +q.height.toFixed(2), w: +q.width.toFixed(2), 文本: (t.textContent || '').trim().slice(0, 20) }; }
        const g = node.querySelector('[data-testid="flow-node-selected-tag"]');
        if (g) { const q = g.getBoundingClientRect(); out.标签 = { top: +q.top.toFixed(2), h: +q.height.toFixed(2), w: +q.width.toFixed(2) }; }
      }
      return out;
    }, nid);
    记.z后1 = a1;
    记.落定 = a1 === 读.scale;
    记.点击生效 = 读.选中.includes(nid);
    if (!记.点击生效) throw new Error(`点击未生效（选中=${JSON.stringify(读.选中)}）`);
    记.vs = 读.scale;
    记.节点 = 读.节点;
    记.标题 = 读.标题;
    记.标签 = 读.标签;
    记.跳了 = Math.abs(读.scale - 闭式) > 2e-3;
    记.标题屏高除以vs = 读.标题 ? +(读.标题.h / 读.scale).toFixed(2) : null;
    记.标签屏高除以vs = 读.标签 ? +(读.标签.h / 读.scale).toFixed(2) : null;
    log(`w=${A.w}｜${A.kind} ${A.名}｜vs=${读.scale}｜节点顶 ${读.节点.top} 屏高 ${读.节点.h}｜标题 ${读.标题 ? '顶' + 读.标题.top + ' 屏高' + 读.标题.h : '—'}｜标签 ${读.标签 ? '顶' + 读.标签.top + ' ' + 读.标签.w + '×' + 读.标签.h : '—'}｜标题/vs ${记.标题屏高除以vs}`);
  } catch (e) {
    记.错误 = e.message;
    log(`w=${A.w}｜${A.kind} ${A.名} 🔴 ${e.message}`);
  } finally {
    try { if (p) await p.close(); } catch (e) { /* 忽略 */ }
    try { if (br) await br.close(); } catch (e) { /* 忽略 */ }
    out.臂.push(记);
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

// ── 两点判据 ──────────────────────────────────────────
const 好 = out.臂.filter((x) => !x.错误 && x.点击生效 && x.vs !== undefined && x.落定);
const 配对 = {};
for (const x of 好) {
  const k = `${x.kind} ${x.名}`;
  (配对[k] ||= {})[x.w] = x;
}
const 表 = {};
for (const [k, v] of Object.entries(配对)) {
  const a = v[1211]; const b = v[1212];
  if (!a || !b || !a.标题 || !b.标题) continue;
  表[k] = {
    vs1211: a.vs, vs1212: b.vs,
    缩放比: +(a.vs / b.vs).toFixed(4),
    标题屏高1211: a.标题.h, 标题屏高1212: b.标题.h,
    标题屏高比: +(a.标题.h / b.标题.h).toFixed(4),
    标题画布高1211: a.标题屏高除以vs, 标题画布高1212: b.标题屏高除以vs,
    标签屏高1211: a.标签 ? a.标签.h : null, 标签屏高1212: b.标签 ? b.标签.h : null,
    标题文本: a.标题.文本,
  };
}

log('\n════ 两点判据 ════');
for (const [k, v] of Object.entries(表)) {
  const 屏固定 = Math.abs(v.标题屏高比 - 1) < 0.02;
  const 画布空间 = Math.abs(v.标题屏高比 - v.缩放比) < 0.05;
  表[k].判决 = 屏固定 ? 'H1 屏幕固定' : (画布空间 ? 'H2 画布空间' : '两条都不像 🔴');
  log(`  ${k.padEnd(9)}｜vs ${v.vs1211} / ${v.vs1212}（比 ${v.缩放比}）｜标题屏高 ${v.标题屏高1211} / ${v.标题屏高1212}（比 ${v.标题屏高比}）｜标签屏高 ${v.标签屏高1211} / ${v.标签屏高1212}｜标题「${v.标题文本}」⇒ **${表[k].判决}**`);
}

const 结论集 = new Set(Object.values(表).map((v) => v.判决));
out.判定 = {
  有效臂: `${好.length}/${臂表.length}`,
  配对结果: 表,
  结论: 结论集.size === 1
    ? `**两个配对都给出同一个判决：${[...结论集][0]}**`
    : `🔴 **配对之间判决不一致**（${[...结论集].join(' / ')}）⇒ 不下结论，如实记`,
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
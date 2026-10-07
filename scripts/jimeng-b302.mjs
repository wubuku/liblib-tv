/**
 * 批次 302 · 定点迭代是「路径依赖」的吗？—— 改**起点** `z0`，看终点 `vs` 动不动。
 *
 * 🔴 起意：批次 301 找到 `node-toolbar`（屏幕 `680 × 204`，横跨安全区），
 *    并算出一条值得注意的推论：若它是**屏宽恒定**的，则
 *    `compoundW = safeW/zoom` ⇒ `vs = safeW/(safeW/zoom) = zoom`
 *    ⇒ 🔴 **那个定点方程退化成恒等式、什么也不约束**，
 *    而退化方程的终点取决于**路径与终止条件** —— 正好对应批次 296 的「跨遍不落定」。
 *
 * 📌 但那是**推论**。本批直接测「路径依赖」本身，**杠杆是起点 `z0`**：
 *   同一个 `w`、同一个节点，唯一变量是**按放大键的次数** ⇒ `z0` 逐档变化。
 *   📌 按 `Meta+Equal` 是 `×1.2`，`13` 次得 `z0=2.779`，每少一次 `÷1.2`。
 *
 * 📌 判据（**测量前写死**）：
 *   **P1** 若 `vs` **与 `z0` 无关** ⇒ 🔴 定点是唯一确定的（退化推论错）
 *        ⇒ **跨遍抖动另有来源**，得回去找别的因子。
 *   **P2** 若 `vs` **随 `z0` 变** ⇒ 🔴 **路径依赖被证实** ⇒ 跨遍抖动的机制找到。
 *
 * 📌 顺带（免费的一枪）：每次都记 `node-toolbar` 的屏矩形 ——
 *   `w=1211` 与 `w=1212` 两侧终点缩放差 `≈1.6×`，
 *   **屏尺寸恒定 ⇒ 屏幕固定装饰；随 zoom 同比 ⇒ 画布空间元素**。
 *
 * 前提检查：`z0 > 闭式` 硬门（每档都验，`z0` 低于平台就作废那条臂）／落定自检／
 *   点击生效自检 / 轴向自检 / `aria` 精确匹配现找现量 / 每臂独立浏览器。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const STATE = `${process.env.HOME}/.jimeng-automation/state.json`;
const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b302.json';
const 放大键 = 'Meta+Equal';

// 每一档都保证 z0 明显高于平台（≈1.08）；13→10 对应 2.779 → 2.316 → 1.930 → 1.608
const 次数档 = [13, 12, 11, 10];
const 宽度档 = [1211, 1212];
const 节点 = { kind: '音频', 名: '音频 1' };

const 臂表 = [];
for (const w of 宽度档) for (const n of 次数档) 臂表.push({ w, 按: n, kind: 节点.kind, 名: 节点.名 });

const 屏上律 = (ww) => Math.max(100, ww - 532);
const vf = (z) => Math.min(8, Math.max(0.08, z));
const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b302',
  问: '定点迭代是路径依赖的吗？—— 只改起点 z0，终点 vs 动不动',
  判据: { P1: 'vs 与 z0 无关 ⇒ 定点唯一确定，退化推论错', P2: 'vs 随 z0 变 ⇒ 路径依赖成立' },
  次数档, 宽度档, 节点, 臂表, 臂: [], 判定: {},
};

for (const A of 臂表) {
  let br = null; let p = null; let nid = null;
  const 记 = { w: A.w, 按: A.按, kind: A.kind, 名: A.名 };
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

    for (let i = 0; i < A.按; i++) { await p.keyboard.press(放大键); await p.waitForTimeout(380); }
    await p.waitForTimeout(1200);
    const 读缩放 = () => p.evaluate(() => {
      const vp = document.querySelector('.react-flow__viewport');
      const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
      return m ? Number(m[1]) : null;
    });
    const z0 = await 读缩放();
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
    const a1 = await 读缩放();
    await p.waitForTimeout(2500);
    const 后 = await p.evaluate((nid2) => {
      const vp = document.querySelector('.react-flow__viewport');
      const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
      const node = document.querySelector(`.react-flow__node[data-id="${nid2}"]`);
      const out = {
        scale: m ? Number(m[1]) : null,
        选中: Array.from(document.querySelectorAll('.react-flow__node.selected')).map((x) => x.dataset.id),
        工具条: null, 节点屏: null,
      };
      const tb = document.querySelector('[data-testid="node-toolbar"]');
      if (tb) { const r = tb.getBoundingClientRect(); out.工具条 = { x: +r.x.toFixed(1), y: +r.y.toFixed(1), w: +r.width.toFixed(1), h: +r.height.toFixed(1) }; }
      if (node) { const r = node.getBoundingClientRect(); out.节点屏 = { top: +r.top.toFixed(2), h: +r.height.toFixed(2) }; }
      return out;
    }, nid);
    记.z后1 = a1;
    记.落定 = a1 === 后.scale;
    记.点击生效 = 后.选中.includes(nid);
    if (!记.点击生效) throw new Error(`点击未生效（选中=${JSON.stringify(后.选中)}）`);
    记.vs = 后.scale;
    记.工具条 = 后.工具条;
    记.节点屏 = 后.节点屏;
    记.跳了 = Math.abs(后.scale - 闭式) > 2e-3;
    记.工具条画布宽 = 后.工具条 ? +(后.工具条.w / 后.scale).toFixed(2) : null;
    log(`w=${A.w}｜按${String(A.按).padStart(2)}次｜z0=${String(z0).padEnd(8)}｜vs=${String(后.scale).padEnd(10)}｜工具条 ${后.工具条 ? 后.工具条.w + '×' + 后.工具条.h + ' @x' + 后.工具条.x : '—'}｜工具条画布宽 ${记.工具条画布宽}`);
  } catch (e) {
    记.错误 = e.message;
    log(`w=${A.w}｜按${A.按}次 🔴 ${e.message}`);
  } finally {
    try { if (p) await p.close(); } catch (e) { /* 忽略 */ }
    try { if (br) await br.close(); } catch (e) { /* 忽略 */ }
    out.臂.push(记);
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

const 好 = out.臂.filter((x) => !x.错误 && x.点击生效 && x.vs !== undefined && x.落定);
const 分组 = {};
for (const x of 好.filter((y) => y.w === 1212)) (分组['1212'] ||= []).push(x);
for (const x of 好.filter((y) => y.w === 1211)) (分组['1211'] ||= []).push(x);

const 路径表 = {};
for (const [w, 臂] of Object.entries(分组)) {
  臂.sort((a, b) => b.按 - a.按);
  const vs = 臂.map((a) => a.vs);
  路径表[w] = {
    z0档: 臂.map((a) => a.z0),
    vs档: vs,
    极差: vs.length > 1 ? +(Math.max(...vs) - Math.min(...vs)).toFixed(6) : null,
    逐字全同: new Set(vs).size === 1,
    工具条屏宽: 臂.map((a) => (a.工具条 ? a.工具条.w : null)),
    工具条画布宽: 臂.map((a) => a.工具条画布宽),
  };
}

log('\n════ 路径依赖表 ════');
for (const [w, v] of Object.entries(路径表)) {
  log(`  w=${w}｜z0 ${JSON.stringify(v.z0档)}`);
  log(`       vs ${JSON.stringify(v.vs档)}｜极差 ${v.极差}｜${v.逐字全同 ? '✅ 逐字全同' : '🔴 随起点变'}`);
  log(`       工具条屏宽 ${JSON.stringify(v.工具条屏宽)}｜画布宽 ${JSON.stringify(v.工具条画布宽)}`);
}

const 任一路径依赖 = Object.values(路径表).some((v) => !v.逐字全同);
// 屏固定判据：跨两个宽度，工具条屏宽是否恒定
const 两宽屏宽 = [1211, 1212].map((w) => 路径表[w] && 路径表[w].工具条屏宽.find((x) => x !== null));
const 屏固定 = 两宽屏宽.length === 2 && 两宽屏宽[0] !== null && 两宽屏宽[0] === 两宽屏宽[1];

out.判定 = {
  有效臂: `${好.length}/${臂表.length}`,
  路径表,
  P1_P2: 任一路径依赖 ? 'P2：vs 随起点 z0 变 ⇒ 路径依赖成立' : 'P1：每个宽度内 vs 与 z0 无关 ⇒ 定点唯一确定，退化推论不成立',
  工具条屏固定: 屏固定 ? `✅ 两个宽度下工具条屏宽都是 ${两宽屏宽[0]} ⇒ 屏幕固定装饰` : `🔴 屏宽 ${JSON.stringify(两宽屏宽)} 两者不等或缺样本`,
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
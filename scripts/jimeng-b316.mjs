/**
 * 批次 316 · 为什么偏偏是 `音频`/`视频` 会掉、`文本`/`时间线` 不会掉？—— 用 **DOM 清单对拍**去找那个多出来的东西。
 *
 * 🔴 接批次 315：开关属于视口、只认 `w`，阈值在 `w ∈ (1210, 1212]`；
 *    `音频 1`/`音频 2`/`音频 68` 三个节点整齐地在 `1212` 掉下去，`文本`/`时间线` 不掉。
 *    🔴 **批次 315 只证明了「与节点无关、与视口高无关」，没有说原因。**
 *
 * 📌 **本批的思路：不再只量落点，直接量「屏上到底有什么」。**
 *    📌 批次 310 已经从 bundle 里读通整条链：`resolveTargetBounds → getNodesBounds →
 *    vO(bounds, attachedInsets, nodeChromeInsets, r)`，且 `visibilityGuard === i.compound`。
 *    🔴 **`attachedInsets`/`nodeChromeInsets` 的运行时实值三路探针（window / CSS / React）全空**（批次 309/310 未测项），
 *    📌 **但它们的**结果**会体现在屏上多出来的元素上** ⇒ 📌 **量屏，比量变量便宜。**
 *
 * 📌 **判别设计（对拍，不是各测一遍）**：
 *    📌 对**同一个节点**，在 `w=1210`（好区）与 `w=1212`（坏区）各点一次搜索结果行，
 *    📌 各自导出**一份归一化的 DOM 清单**，⇒ 🔴 **两份清单求差**：
 *    📌 **差集里多出来的元素，就是那个把落点顶下去的东西的候选。**
 *    📌 `文本 1` 走同样两臂作**阴性对照**（它不切换 ⇒ 🔴 **它的差集必须为空或与音频同形但不影响落点**）。
 *
 * 📌 **清单里记什么（挑「能解释落点」的，不是「什么都记」）**：
 *    ① 节点**自身元素**的 `getBoundingClientRect`（屏像素）—— 落点变了它会跟着变；
 *    ② **节点内部的后代元素**（按 `data-testid` / `class` 标识）—— 装饰挂在这里；
 *    ③ 文档里**所有** `[data-testid]` 元素的 `rect` + `position`/`transform`，
 *       🔴 **重点标出 `position: fixed` 的**（批次 304/305 已证屏固定装饰是屏幕尺寸）；
 *    ④ 画布视口的 `transform`（落点本身）。
 *
 * 📌 **判据（测量前写死）**：
 *   **P0** 阳性对照：`文本 1 @1210` 必须落 `1.75`、`文本 1 @1212` 必须落 `1.75`，两条逐字。
 *   **P1（对拍）** `音频 1` 的 `1212` 清单相对 `1210` 清单的**差集非空**
 *        ⇒ ✅ **有一个屏上元素随阈值出现**（本批主结论候选）；**差集为空**
 *        ⇒ 🔴 **屏上没有多出东西 ⇒ 那 `≈200px` 的差额不是「多了个元素」，是同一批元素的尺寸/位置变了**。
 *   **P2（阴性对照）** `文本 1` 的差集**必须为空** —— 🔴 若它也非空，
 *        📌 说明「差集非空」不足以解释切换，🔴 **P1 判据作废**。
 *   **P3** 差集里的元素要带**逐字 `data-testid`/`class` + 屏像素尺寸**，📌 不许只报「有个 div」。
 *
 * 前提检查：轴向自检 / 落定自检（三连读）/ 点击生效自检 /
 *   `aria` 精确匹配现找现量 / 参数写死 / 每臂独立浏览器 / 盒尺寸逐臂现量。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const STATE = `${process.env.HOME}/.jimeng-automation/state.json`;
const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b316.json';
const 放大键 = 'Meta+Equal';
const 闭式 = (w, h, W, H, z0) => Math.min((w - 532) / W, (h - 160) / H, z0);

const 臂表 = [
  { 键: 'A音频_1210', 组: 'A', kind: '音频', 名: '音频 1', vw: 1210, vh: 720, 按: 13 },
  { 键: 'A音频_1212', 组: 'A', kind: '音频', 名: '音频 1', vw: 1212, vh: 720, 按: 13 },
  { 键: 'C文本_1210', 组: 'C', kind: '文本', 名: '文本 1', vw: 1210, vh: 720, 按: 13, 期望: 1.75 },
  { 键: 'C文本_1212', 组: 'C', kind: '文本', 名: '文本 1', vw: 1212, vh: 720, 按: 13, 期望: 1.75 },
  { 键: 'B视频_1212', 组: 'B', kind: '视频', 名: '视频 1', vw: 1212, vh: 720, 按: 13 },
];

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b316',
  问: '音频/视频 在 w=1212 多出来的落点份额，屏上是不是真的多了一个元素？',
  接批次315: {
    已知: '开关属于视口、只认 w，阈值 w ∈ (1210, 1212]；音频 1/2/68 整齐掉落，文本/时间线不掉',
    未答: '为什么偏偏是这两个 kind —— attachedInsets/nodeChromeInsets 运行时实值三路探针全空（批次 309/310）',
    本批思路: '不再只量落点，直接量「屏上到底有什么」：同一个节点两个视口各点一次，导出归一化 DOM 清单求差集',
  },
  判据: {
    P0: '文本 1210 与 1212 都必须落 1.75，逐字，否则整批作废',
    P1: '音频的 1212 清单相对 1210 的差集非空 ⇒ 屏上多出元素；为空 ⇒ 同一批元素尺寸/位置变了',
    P2: '文本的差集必须为空，否则 P1 判据作废',
    P3: '差集元素必须带逐字 data-testid/class + 屏像素尺寸，不许只报「有个 div」',
  },
  臂表, 臂: [], 判定: {},
};

/** 📌 在页面里跑的清单采集器（纯读，不点任何东西） */
const 采集 = () => {
  const 号 = (e) => {
    const tid = e.getAttribute('data-testid');
    const cls = (e.getAttribute('class') || '').trim().split(/\s+/).slice(0, 3).join('.');
    return (tid ? '[testid=' + tid + ']' : '') + (cls ? '.' + cls : '') || e.tagName.toLowerCase();
  };
  const 矩形 = (e) => {
    const b = e.getBoundingClientRect();
    return [Math.round(b.x * 10) / 10, Math.round(b.y * 10) / 10, Math.round(b.width * 10) / 10, Math.round(b.height * 10) / 10];
  };
  const 节点 = Array.from(document.querySelectorAll('.react-flow__node[data-id]'))
    .find((x) => x.getAttribute('aria-label') === window.__想找的aria);
  const 目标 = 节点 ? { id: 节点.dataset.id, rect: 矩形(节点), W: 节点.offsetWidth, H: 节点.offsetHeight } : null;
  const 后代 = 节点
    ? Array.from(节点.querySelectorAll('*')).map((e) => ({
      号: 号(e), rect: 矩形(e),
      position: getComputedStyle(e).position,
      inNode: true,
    }))
    : [];
  const 全域 = Array.from(document.querySelectorAll('[data-testid]')).map((e) => ({
    号: 号(e), rect: 矩形(e),
    position: getComputedStyle(e).position,
    transform: (getComputedStyle(e).transform || '').slice(0, 60),
    inNode: !!(节点 && 节点.contains(e)),
  }));
  const 固定 = 全域.filter((x) => x.position === 'fixed');
  const vp = document.querySelector('.react-flow__viewport');
  return {
    目标,
    落点: vp ? (/scale\(([\d.]+)\)/.exec(vp.style.transform || '') || [])[1] || null : null,
    选中: Array.from(document.querySelectorAll('.react-flow__node.selected')).map((x) => x.dataset.id),
    后代数: 后代.length,
    全域数: 全域.length,
    固定数: 固定.length,
    后代, 固定,
  };
};

for (const 臂 of 臂表) {
  let br = null; let p = null; let nid = null;
  const 记 = { 键: 臂.键, 组: 臂.组, kind: 臂.kind, 名: 臂.名, vw: 臂.vw, vh: 臂.vh };
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
    if (臂.期望 !== undefined) 记.命中期望 = Math.abs(记.终点 - 臂.期望) < 5e-6;

    // 📌 采集 DOM 清单（点完之后，屏固定装饰已经挂上）
    await p.evaluate((aria) => { window.__想找的aria = aria; }, ariaWant);
    记.清单 = await p.evaluate(采集);
    记.清单.选中与目标一致 = 记.清单.选中.join(',') === nid;

    log(臂.键.padEnd(12) + '｜视口' + String(臂.vw + 'x' + 臂.vh).padEnd(10)
      + '｜落点=' + String(记.终点).padEnd(10)
      + '｜闭式=' + String(记.闭式预测).padEnd(10)
      + (记.命中闭式 ? '｜✅命中' : '｜🔴不中')
      + '｜后代=' + 记.清单.后代数 + '｜全域testid=' + 记.清单.全域数 + '｜fixed=' + 记.清单.固定数
      + '｜节点屏盒=' + JSON.stringify(记.清单.目标.rect));
  } catch (e) {
    记.错误 = e.message;
    log(臂.键.padEnd(12) + '🔴 ' + e.message);
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

/** 📌 对拍两份清单：返回「只在 1212 出现」与「只在 1210 出现」的标识集合 */
function 对拍(甲键, 乙键, 字段) {
  const a = 取(甲键); const b = 取(乙键);
  if (!a || !b) return null;
  const sa = new Set(a.清单[字段].map((x) => x.号));
  const sb = new Set(b.清单[字段].map((x) => x.号));
  const 只在乙 = [...sb].filter((x) => !sa.has(x));
  const 只在甲 = [...sa].filter((x) => !sb.has(x));
  return {
    甲: 甲键, 乙: 乙键, 字段,
    甲数: sa.size, 乙数: sb.size,
    只在乙, 只在甲,
    乙里的细节: 只在乙.map((号x) => {
      const e = b.清单[字段].find((y) => y.号 === 号x);
      return { 号: 号x, rect: e.rect, position: e.position, inNode: e.inNode, transform: e.transform || null };
    }),
  };
}

const P0a = 取('C文本_1210'); const P0b = 取('C文本_1212');
const 判定P0 = (P0a && P0b && P0a.命中期望 && P0b.命中期望)
  ? '✅ P0：文本 @1210 落 ' + P0a.终点 + '、@1212 落 ' + P0b.终点 + '，两条逐字 ⇒ 尺子没漂'
  : '🔴 P0：文本 @1210=' + (P0a ? P0a.终点 : '—') + '、@1212=' + (P0b ? P0b.终点 : '—') + ' ⇒ 本批作废';

const 拍音频后代 = 对拍('A音频_1210', 'A音频_1212', '后代');
const 拍音频全域 = 对拍('A音频_1210', 'A音频_1212', '固定');
const 拍文本后代 = 对拍('C文本_1210', 'C文本_1212', '后代');

const 差集非空 = (p) => !!(p && (p.只在乙.length || p.只在甲.length));
const 判定P1 = !拍音频后代 ? '（A 组臂不全）'
  : (差集非空(拍音频后代)
    ? '✅ P1：`音频 1` 的后代清单在 `1212` 相对 `1210` **有差集** ⇒ ✅ **屏上确实随阈值多出东西**；🔴 只在 `1212` 出现：'
      + JSON.stringify(拍音频后代.只在乙) + '；只在 `1210` 出现：' + JSON.stringify(拍音频后代.只在甲)
      + '｜尺寸细节：' + JSON.stringify(拍音频后代.乙里的细节)
    : '🔴 P1：`音频 1` 的后代清单在 `1212` 与 `1210` **完全相同** ⇒ 🔴 **屏上没有多出元素 ⇒ 那份额来自同一批元素的尺寸/位置变化，不是「多了个东西」**');

const 判定P2 = !拍文本后代 ? '（C 组臂不全）'
  : (拍文本后代.只在乙.length === 0 && 拍文本后代.只在甲.length === 0
    ? '✅ P2：阴性对照 `文本 1` 的差集**为空** ⇒ ✅ 「差集非空」在本批是有判别力的（文本不切换，它的差集就该空）'
    : '⚠️ P2：阴性对照 `文本 1` 的差集**非空**（只在 `1212`：' + JSON.stringify(拍文本后代.只在乙)
      + '）⇒ 🔴 **P1 的判别力被削弱**：「差集非空」不足以解释切换');

out.判定 = {
  有效臂: 好.length + '/' + 臂表.length,
  判定P0_尺子: 判定P0,
  判定P1_音频后代对拍: 判定P1,
  判定P2_阴性对照: 判定P2,
  对拍明细: { 音频后代: 拍音频后代, 音频固定元素: 拍音频全域, 文本后代: 拍文本后代 },
  节点屏盒对照: 好.map((x) => ({ 键: x.键, 视口: x.vw + 'x' + x.vh, 落点: x.终点, 屏盒: x.清单.目标.rect, 盒: x.画布盒, 闭式预测: x.闭式预测, 命中闭式: x.命中闭式 })),
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
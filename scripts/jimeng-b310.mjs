/**
 * 批次 310 · 低分支 `≈1.55918` 的成因 —— 从**运行时**读 `inset`，不再从 bundle 猜。
 *
 * 🔴 起意：批次 309 在 bundle 里读通了完整链条 ——
 *    `resolveTargetBounds(e,t,i)` → `getNodesBounds(nodeIds, roles, r)` →
 *    `vO(bounds, attachedInsets, nodeChromeInsets, r)`，
 *    其中 `vO` 四边分别独立算：`inset = attached + chrome * (1/max(r,.5))`。
 *    🔴 **但 `attachedInsets` 的实际值在 bundle 里读不到**，📌 它在运行时注入 ⇒ 只能实测。
 *
 * 📌 **本批要拿的三个数**（静态推演给不出）：
 *   ① **`attachedInsets`** 的实际值 —— 低分支反推需要「多出宽 ≈ 116.13、高 ≈ 39.16」；
 *   ② **`nodeChromeInsets`** —— bundle 里只找到 `{top:24}`（`@1089897`，**「编辑目标」场景**），
 *      🔴 **那不一定是搜索点击这条路用的值**；
 *   ③ **`hasScreenFixedDecoration`** 的真假 —— 批次 309 找到
 *      `resolveNonScreenFixedDecorationRoles` 会把它的 role **剔除**，
 *      📌 这就是 `retry:"withoutScreenFixed"` 的实体。
 *
 * 📌 **判据（测量前写死）**：
 *   **P1** 若能从运行时拿到 `attachedInsets` / `nodeChromeInsets` 的**字面值**
 *          ⇒ ✅ 代入 `vO` 重算 `compound`，📌 **与「反解出的 `436.13 × 359.16`」逐字对账**；
 *   **P2** 🔴 **若拿不到（运行时不可达）** ⇒ 📌 **如实记「静态与运行时之间有一层未打通」**，
 *          🔴 **不拿 bundle 里的字面值冒充实测值**（立规 113）；
 *   **P3** 顺带验 `hasScreenFixedDecoration` 与 `retry:"withoutScreenFixed"` 是否真的联动 ——
 *          📌 判据：文本节点挂了屏幕固定装饰（批次 301/304 已证 `selection-context-toolbar` `160×40`）
 *          ⇒ 若该标记为真，📌 **「零 inset」就不该成立**，🔴 而批次 306 说它成立。
 *
 * 前提检查：轴向自检 / 落定自检 / 点击生效自检 / `aria` 精确匹配现找现量 / 每臂独立浏览器。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const STATE = `${process.env.HOME}/.jimeng-automation/state.json`;
const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b310.json';
const 放大键 = 'Meta+Equal';
const w = 1212; const h = 720;
const kind = '文本'; const 名 = '文本 1';

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b310',
  问: 'attachedInsets / nodeChromeInsets / hasScreenFixedDecoration 的运行时实值是什么？低分支 ≈1.55918 能否闭合？',
  判据: {
    P1: '能读到 insets 字面值 ⇒ 代入 vO 重算 compound，与反解的 436.13x359.16 逐字对账',
    P2: '读不到 ⇒ 如实记「静态与运行时之间有一层未打通」，不拿 bundle 字面值冒充实测',
    P3: '验 hasScreenFixedDecoration 与零 inset 是否矛盾（文本挂了 160x40 屏幕固定装饰）',
  },
  w, h, 臂: [], 判定: {},
};

/**
 * 📌 在页面上下文里找 runtime 的 inset 来源。
 * 🔴 立规 182 的教训：不靠猜 testid，📌 **列出所有可能的全局挂载点**并逐个量。
 */
const 探测 = () => {
  const out = { 全局键: [], dom量: {}, reactProps: null };
  // ① 扫 window 上带 inset / chrome / bounds 字样的键
  const 键集 = new Set();
  for (const k of Object.keys(window)) {
    const lk = k.toLowerCase();
    if (lk.includes('inset') || lk.includes('chrome') || lk.includes('safe') || lk.includes('guard')) 键集.add(k);
  }
  for (const k of 键集) {
    try {
      const v = window[k];
      out.全局键.push({ 键: k, 类型: typeof v, 摘要: (() => { try { return JSON.stringify(v).slice(0, 300); } catch (e) { return '[不可序列化]'; } })() });
    } catch (e) { out.全局键.push({ 键: k, 错: e.message }); }
  }
  // ② DOM 上有没有直接写着 inset 的样式变量
  const 根 = document.documentElement;
  const cs = getComputedStyle(根);
  const 变量 = [];
  for (let i = 0; i < cs.length; i++) {
    const nm = cs[i];
    if (nm.startsWith('--') && /inset|chrome|safe|guard|pad/i.test(nm)) 变量.push({ 名: nm, 值: cs.getPropertyValue(nm).trim() });
  }
  out.dom量.CSS变量 = 变量;
  // ③ 节点自身上的 CSS 自定义属性（inset 类）
  const 节点 = document.querySelector('.react-flow__node');
  if (节点) {
    const cs2 = getComputedStyle(节点);
    const v2 = [];
    for (let i = 0; i < cs2.length; i++) {
      const nm = cs2[i];
      if (/inset|chrome|safe|guard/i.test(nm)) v2.push({ 名: nm, 值: cs2.getPropertyValue(nm).trim() });
    }
    out.dom量.节点变量 = v2;
  }
  // ④ react fiber 上有没有 props 挂着这些
  const 候选 = Array.from(document.querySelectorAll('.react-flow__node')).slice(0, 3);
  for (const el of 候选) {
    const keys = Object.keys(el).filter((k) => k.startsWith('__react'));
    for (const k of keys) {
      let f = el[k];
      try {
        // 往上走 fiber 链，收集 memoizedProps / state 里的 inset 线索
        for (let d = 0; d < 8 && f; d++, f = f.return) {
          const 探 = [f.memoizedProps, f.pendingProps];
          for (const p of 探) {
            if (!p || typeof p !== 'object') continue;
            for (const pk of Object.keys(p)) {
              if (/inset|chrome|safeArea|guard|compound/i.test(pk)) {
                out.reactProps = out.reactProps || [];
                try { out.reactProps.push({ 深度: d, 键: pk, 值: JSON.stringify(p[pk]).slice(0, 300) }); } catch (e) { /* 忽略 */ }
              }
            }
          }
        }
      } catch (e) { /* 忽略 */ }
    }
  }
  return out;
};

for (let 臂次 = 1; 臂次 <= 2; 臂次++) {
  let br = null; let p = null; let nid = null;
  const 记 = { 臂次, 按: 臂次 === 1 ? 11 : 13 };
  try {
    br = await chromium.launch({ headless: true });
    const ctx = await br.newContext({ storageState: STATE, viewport: { width: w, height: h } });
    p = await ctx.newPage();
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 60000 });
    await p.waitForTimeout(6000);
    const 实际 = await p.evaluate(() => ({ w: innerWidth, h: innerHeight }));
    if (实际.w !== w || 实际.h !== h) throw new Error(`轴向自检失败：${实际.w}×${实际.h}`);

    const ariaWant = `${kind} node: ${名}`;
    const 目标 = await p.evaluate((aria) => {
      const e = Array.from(document.querySelectorAll('.react-flow__node[data-id]'))
        .find((x) => x.getAttribute('aria-label') === aria);
      return e ? { id: e.dataset.id, W: e.offsetWidth, H: e.offsetHeight } : null;
    }, ariaWant);
    if (!目标) throw new Error(`找不到 aria 为「${ariaWant}」的节点`);
    nid = 目标.id;
    记.盒 = { W: 目标.W, H: 目标.H };

    // 📌 未选中前先探一次（零 inset 应当发生在这个状态）
    记.选中前探测 = await p.evaluate(探测);

    for (let i = 0; i < 记.按; i++) { await p.keyboard.press(放大键); await p.waitForTimeout(380); }
    await p.waitForTimeout(1400);
    const 读缩放 = () => p.evaluate(() => {
      const vp = document.querySelector('.react-flow__viewport');
      const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
      return m ? Number(m[1]) : null;
    });
    记.z0 = await 读缩放();

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

    // 📌 选中后再探一次（低分支就发生在选中后）
    记.选中后探测 = await p.evaluate(探测);
    log(`臂${臂次}｜z0=${记.z0}｜终点=${记.终点}｜全局键=${(记.选中后探测.全局键 || []).length}｜CSS变量=${(记.选中后探测.dom量?.CSS变量 || []).length}｜react命中=${(记.选中后探测.reactProps || []).length}`);
  } catch (e) {
    记.错误 = e.message;
    log(`臂${臂次}🔴 ${e.message}`);
  } finally {
    try { if (p) await p.close(); } catch (e) { /* 忽略 */ }
    try { if (br) await br.close(); } catch (e) { /* 忽略 */ }
    out.臂.push(记);
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

// ───────── 判定 ─────────
const 好 = out.臂.filter((x) => !x.错误 && x.点击生效 && x.落定);
const 末 = 好.length ? 好[好.length - 1] : null;
const 收集 = (源, 键) => ((源 || {})[键] || []);

const 全局命中 = 好.flatMap((x) => 收集(x.选中后探测, '全局键').filter((k) => /inset|chrome/i.test(k.键)));
const CSS命中 = 好.flatMap((x) => 收集(x.选中后探测.dom量, 'CSS变量'));
const React命中 = 好.flatMap((x) => 收集(x.选中后探测, 'reactProps'));

/**
 * 🔴 判据必须用【画布专属】的白名单，不能只靠「名字里有没有 inset」。
 * 📌 第一版只查 /inset|chrome/i，🔴 结果把 22 条 CSS 变量（全是 `padding-inline`、
 *    `badge-inset`、`workbench-chrome=#292929` 之类）全算成命中，还报「✅ P1 抓到 44 条」。
 * 📌 **过滤器太宽等于没过滤**（立规 183 的又一次现形）。
 */
const 画布白名单 = /(nodeChromeInsets|attachedInsets|visibilityGuard|safeAreaInsets|originSafeCanvasRect|canvas-safe|node-inset)/i;
const 全局真 = 全局命中.filter((k) => 画布白名单.test(k.键));
const CSS真 = CSS命中.filter((k) => 画布白名单.test(k.名));
const React真 = React命中.filter((k) => 画规(k.键));
function 画规(k) { return 画布白名单.test(k); }

const 判定P1 = (全局真.length + CSS真.length + React真.length > 0)
  ? '✅ P1：运行时抓到 ' + (全局真.length + CSS真.length + React真.length) + ' 条**画布专属** inset 线索 ⇒ 见清单'
  : '🔴 P2：运行时**没有任何画布专属 inset 挂载点**'
    + '（全局 ' + 全局真.length + ' / CSS 变量 ' + CSS真.length + ' / react props ' + React真.length
    + '；🔴 原始命中 ' + (全局命中.length + CSS命中.length + React命中.length)
    + ' 条**全部是 padding/badge-inset/workbench-chrome 之类，已剔除**）'
    + ' ⇒ 📌 **静态与运行时之间有一层未打通**，🔴 **不拿 bundle 里的 {top:24} 冒充实测值**（立规 113）';

const 判定P3 = (React命中.length > 0)
  ? `⚠️ P3：react props 上有 inset 类字段，需人工判读（见清单）`
  : '📌 P3：读不到 `hasScreenFixedDecoration` 的运行时值 ⇒ 🔴 **「文本零 inset」这个结论本批既不能证实也不能证伪**';

out.判定 = {
  有效臂: `${好.length}/${out.臂.length}`,
  终点读数: 好.map((x) => ({ 按: x.按, z0: x.z0, 终点: x.终点 })),
  全局键清单: 全局命中,
  CSS变量清单: CSS命中,
  reactProps清单: React命中.slice(0, 20),
  判定P1_或P2: 判定P1,
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
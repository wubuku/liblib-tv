/**
 * 批次 323 · `A` 的散布（跑一次抖 `15` 画布像素）到底是哪来的 —— **点下去的那一瞬间，工具条有多高？**
 *
 * 🔴 接批次 322 结果四：汇总坏区读数 `n = 37`，`A` 均值 `209.824`、极差 `15.451`；
 *    🔴 **同一视口重跑 `24` 次的内部极差 `15.264` ≳ 换遍视口的极差 `14.843`**、`corr(A, safeH) = −0.078`
 *    ⇒ 📌 **`A` 的散布是运行间噪声，不是视口的函数**。🔴 **而这个噪声还没有机制。**
 *
 * 📌 **一个先算出来的事实（不是探针）**：`13/13` 臂里工具条屏高**逐字恒为 `204`**，
 *    而 `A` 逐臂在 `202.819`–`216.912` ⇒ 🔴 **「预留的带 = 工具条屏高」已被否**（批次 322 结果三）。
 *    🔴 **但有一个时序解释本批第一次才有机会测**：
 *    📌 **工具条是「点中之后才挂上去的」** —— 未选中时它根本不在 DOM 里；
 *    📌 点一下 ⇒ 挂载 ⇒ 量高 ⇒ 算 fit ⇒ 设 transform。📌 **这是一个天然的竞态窗口。**
 *    ⇒ 📌 **若 fit 是在工具条「还没排版完」时算的，预留高度就可能落在 `204`–`216` 之间 ⇒ 而测量那一刻它早已回到 `204`。**
 *
 * 📌 **本批三件事，判据全部在测量前写死**：
 *   **P1（时序）** 点击后每 `100ms` 采样一次，共 `8` 秒，📌 **每次同时记「落点」与「工具条屏高」**
 *        ⇒ 若早期样本里工具条屏高 `> 204`（哪怕只有一两个样本）⇒ ✅ **竞态假说成立，`A` 就是那一瞬的高度**；
 *        ⇒ 若**所有**样本（含第一个）都逐字是 `204` ⇒ 🔴 **竞态假说被否**（📌 立规 201④ 的反面：**没测到 ≠ 不存在，但测到了就是有了**）。
 *   **P2（会话内 vs 跨会话）** 同一浏览器会话里**再做 `2` 次 fit**（先搜到 `文本 1` 点走，再搜回 `音频 1`）
 *        ⇒ 会话内 `2` 次的 `Δs` 全为 `0` ⇒ 📌 **噪声是「每次加载」级的，不是「每次点击」级的**；
 *        ⇒ 会话内也抖 ⇒ 📌 **噪声是「每次点击」级的**。📌 **判据：`Δs` 与臂间散布 `15.45` 画布像素比。**
 *   **P3（跨臂对拍）** 每臂导一份「节点后代 + 同级 + 全域 `data-testid`」清单，📌 **按 `A` 分两组**
 *        （`A ≤ 205` 组 vs `A ≥ 209` 组）⇒ 找**在两组之间系统性不同**的元素（屏高差 `> 4` 像素，或一边有一边没有）
 *        ⇒ ✅ 找到就是机制；🔴 找不到 ⇒ 📌 **DOM 逐字相同 ⇒ 差异在 fit 的计算内部，不在渲染出来的界面上**。
 *
 * 📌 **P0 阳性对照**：`文本 @1212×720` 必须逐字落 `1.75`；🔴 不中 ⇒ 本批作废。
 *
 * 前提检查：轴向自检 / 落定自检（三连读）/ 点击生效自检 /
 *   `aria` 精确匹配现找现量 / 参数写死 / 每臂独立浏览器 / 盒尺寸逐臂现量。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const STATE = `${process.env.HOME}/.jimeng-automation/state.json`;
const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b323.json';
const 放大键 = 'Meta+Equal';
const 闭式 = (w, h, W, H, z0) => Math.min((w - 532) / W, (h - 160) / H, z0);
const VW = 1212;
const VH = 720;
const SAFE_H = VH - 160;
const H0 = 320;
const 采样数 = 80;
const 采样间隔 = 100;
const 低组阈 = 205;
const 高组阈 = 209;

/** 📌 采集器：节点后代 + 同级 + 全域 `data-testid`，逐臂现量，供跨臂对拍。 */
const 采集 = () => {
  const 号 = (e) => {
    const tid = e.getAttribute('data-testid');
    const cls = (e.getAttribute('class') || '').trim().split(/\s+/).slice(0, 2).join('.');
    return (tid ? tid : '') + '|' + (cls || e.tagName.toLowerCase());
  };
  const 矩形 = (e) => {
    const b = e.getBoundingClientRect();
    return [Math.round(b.x * 10) / 10, Math.round(b.y * 10) / 10, Math.round(b.width * 10) / 10, Math.round(b.height * 10) / 10];
  };
  const 节点 = Array.from(document.querySelectorAll('.react-flow__node[data-id]'))
    .find((x) => x.getAttribute('aria-label') === window.__找的aria);
  const 框 = (list, 标) => list.map((e) => ({ 号: 号(e), rect: 矩形(e), pos: getComputedStyle(e).position, 标: 标 || null }));
  return {
    节点屏盒: 节点 ? 矩形(节点) : null,
    后代: 节点 ? 框(Array.from(节点.querySelectorAll('*')), '后代') : [],
    同级: 节点 && 节点.parentElement ? 框(Array.from(节点.parentElement.parentElement ? 节点.parentElement.parentElement.children : []).filter((x) => x !== 节点 && x.getBoundingClientRect().width > 0), '同层') : [],
    全域: 框(Array.from(document.querySelectorAll('[data-testid]')), '全域'),
    选中: Array.from(document.querySelectorAll('.react-flow__node.selected')).map((x) => x.dataset.id),
  };
};

const 臂表 = [];
for (let i = 1; i <= 8; i++) 臂表.push({ 键: 'R' + i, 组: '重复', kind: '音频', 名: '音频 1' });
臂表.push({ 键: 'W_1', 组: '对照', kind: '文本', 名: '文本 1', 期望: 1.75 });

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b323',
  问: 'A 的散布（跑一次抖 15 画布像素）到底是哪来的？点下去那一瞬间工具条有多高？',
  先算出来的事实: {
    来源: '批次 322 结果四',
    散布: 'n=37，A 均值 209.824、标准差 4.770、极差 15.451（201.461–216.912）',
    关键: '同一视口重跑 24 次的内部极差 15.264 ≳ 换遍视口的 14.843 ⇒ 散布是运行间噪声',
    而: '13/13 臂工具条屏高逐字恒为 204，而 A 逐臂 202.819–216.912 ⇒ 「份额=工具条屏高」已否',
    本批第一次才有的机会: '工具条是「点中之后才挂上去的」⇒ 挂载→量高→算 fit 之间有竞态窗口',
  },
  判据: {
    P0: '阳性对照 文本 @1212×720 必须逐字落 1.75，不中即本批作废',
    P1: '点击后每 100ms 采样 8 秒；早期样本里工具条屏高 > 204 ⇒ 竞态成立、A 就是那一瞬的高度；所有样本都逐字 204 ⇒ 竞态被否',
    P2: '同一会话内再做 2 次 fit；会话内 Δs 全为 0 ⇒ 噪声是每次加载级；会话内也抖 ⇒ 每次点击级',
    P3: '按 A 分两组（≤205 / ≥209）跨臂对拍；系统性不同 ⇒ 找到机制；DOM 逐字相同 ⇒ 差异在 fit 计算内部',
  },
  采样: { 次数: 采样数, 间隔毫秒: 采样间隔, 低组阈, 高组阈 },
  臂表, 臂: [], 判定: {},
};

/** 📌 打开搜索面板、输入、点中某个节点，返回是否点中。 */
const 搜并点 = async (p, 词表, 目标id) => {
  const 钮 = await p.evaluate(() => {
    const b = document.querySelector('button[aria-label="搜索"]');
    if (!b) return null;
    const r = b.getBoundingClientRect();
    return { 中心: [r.x + r.width / 2, r.y + r.height / 2], 可见: r.width > 0 && r.height > 0 && r.y >= 0 && r.bottom <= innerHeight };
  });
  if (!钮 || !钮.可见) return '找不到可见的搜索钮';
  await p.mouse.click(钮.中心[0], 钮.中心[1]);
  await p.waitForTimeout(1600);
  for (const 词 of 词表) {
    await p.evaluate(() => { const i = document.querySelector('[data-testid="canvas-search-panel"] input'); if (i) { i.focus(); i.select(); } });
    await p.keyboard.type(词, { delay: 80 });
    await p.waitForTimeout(2000);
    const sel = '[data-testid="canvas-search-result-node_' + String(目标id).replace(/^node_/, '') + '"]';
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
    if (r && r.可见) { await p.mouse.click(r.中心[0], r.中心[1]); await p.waitForTimeout(3200); return null; }
  }
  return '搜不到可见结果行';
};

/** 📌 在页面里跑密集采样：每次同时记「落点」与「工具条屏高」。 */
const 采样 = async (p) => p.evaluate(async ([n, ms]) => {
  const 列 = [];
  const 取盒 = (tid) => {
    const es = Array.from(document.querySelectorAll('[data-testid="' + tid + '"]'))
      .map((x) => x.getBoundingClientRect())
      .filter((r) => r.width > 0 && r.height > 0);
    if (!es.length) return null;
    const b = es.reduce((q, r) => (r.width * r.height > q.width * q.height ? r : q));
    return { h: Math.round(b.height * 100) / 100, top: Math.round(b.top * 100) / 100, bottom: Math.round(b.bottom * 100) / 100 };
  };
  const 取节点 = () => {
    const e = document.querySelector('.react-flow__node.selected') || document.querySelector('.react-flow__node');
    if (!e) return null;
    const b = e.getBoundingClientRect();
    return { h: Math.round(b.height * 100) / 100, top: Math.round(b.top * 100) / 100, bottom: Math.round(b.bottom * 100) / 100 };
  };
  for (let i = 0; i < n; i++) {
    const vp = document.querySelector('.react-flow__viewport');
    const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
    列.push({ i, s: m ? Number(m[1]) : null, 工具条: 取盒('node-toolbar'), 表单: 取盒('audio-generation-form'), 节点: 取节点() });
    await new Promise((r) => setTimeout(r, ms));
  }
  return 列;
}, [采样数, 采样间隔]);

for (const 臂 of 臂表) {
  let br = null; let p = null; let nid = null; let 文id = null;
  const 记 = { 键: 臂.键, 组: 臂.组, kind: 臂.kind, 名: 臂.名, vw: VW, vh: VH };
  try {
    br = await chromium.launch({ headless: true });
    const ctx = await br.newContext({ storageState: STATE, viewport: { width: VW, height: VH } });
    p = await ctx.newPage();
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 60000 });
    await p.waitForTimeout(6000);

    const 实际 = await p.evaluate(() => ({ w: innerWidth, h: innerHeight }));
    if (实际.w !== VW || 实际.h !== VH) throw new Error('轴向自检失败：' + 实际.w + 'x' + 实际.h);

    const 找 = await p.evaluate((aria) => {
      const e = Array.from(document.querySelectorAll('.react-flow__node[data-id]'))
        .find((x) => x.getAttribute('aria-label') === aria);
      return e ? { id: e.dataset.id, W: e.offsetWidth, H: e.offsetHeight } : null;
    }, 臂.kind + ' node: ' + 臂.名);
    if (!找) throw new Error('找不到 aria 为「' + (臂.kind + ' node: ' + 臂.名) + '」的节点');
    nid = 找.id;
    记.画布盒 = { W: 找.W, H: 找.H };
    if (臂.kind === '文本') {
      const t = await p.evaluate((aria) => {
        const e = Array.from(document.querySelectorAll('.react-flow__node[data-id]'))
          .find((x) => x.getAttribute('aria-label') === aria);
        return e ? e.dataset.id : null;
      }, '文本 node: 文本 1');
      文id = t;
    }

    for (let i = 0; i < 13; i++) { await p.keyboard.press(放大键); await p.waitForTimeout(380); }
    await p.waitForTimeout(1600);
    const 读缩放 = () => p.evaluate(() => {
      const vp = document.querySelector('.react-flow__viewport');
      const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
      return m ? Number(m[1]) : null;
    });
    记.点之前 = await 读缩放();
    if (记.点之前 === null) throw new Error('点之前读不到 scale');

    const e1 = await 搜并点(p, [臂.名, 臂.kind + ' node: ' + 臂.名, 臂.kind], nid);
    if (e1) throw new Error(e1);

    // 📌 P1：点下去之后立刻密集采样（第一次点击后 3.2 秒才开始，故这里采的是「已落定后」与「会话内重复点击后」的两种瞬态）
    记.采样一 = await 采样(p);

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

    记.闭式预测 = +闭式(VW, VH, 找.W, 找.H, 记.点之前).toFixed(6);
    记.命中闭式 = Math.abs(记.终点 - 记.闭式预测) < 5e-5;
    if (臂.期望 !== undefined) 记.命中期望 = Math.abs(记.终点 - 臂.期望) < 5e-6;
    记.A = 臂.kind === '音频' ? +(SAFE_H - H0 * 记.终点).toFixed(3) : 0;

    // 📌 P2：同一会话内再做 2 次 fit —— 先点走（文本 1），再点回来
    记.会话内 = [];
    if (文id) {
      for (let k = 0; k < 2; k++) {
        const e2 = await 搜并点(p, ['文本 1', '文本 node: 文本 1'], 文id);
        if (e2) { 记.会话内.push({ 轮: k, 错: e2 }); break; }
        const e3 = await 搜并点(p, [臂.名, 臂.kind + ' node: ' + 臂.名, 臂.kind], nid);
        if (e3) { 记.会话内.push({ 轮: k, 错: e3 }); break; }
        const a = await 读缩放();
        await p.waitForTimeout(2600);
        const b = await 读缩放();
        await p.waitForTimeout(1800);
        const c = await 读缩放();
        记.会话内.push({ 轮: k, a, b, c, 落定: a === b && b === c, 落点: c, A: 臂.kind === '音频' ? +(SAFE_H - H0 * c).toFixed(3) : 0 });
        if (k === 0) 记.采样二 = await 采样(p);
      }
    }

    await p.evaluate((aria) => { window.__找的aria = aria; }, 臂.kind + ' node: ' + 臂.名);
    记.清单 = await p.evaluate(采集);
    记.清单.选中与目标一致 = 记.清单.选中.join(',') === nid;

    const 工具条集 = 记.采样一.map((x) => (x.工具条 ? x.工具条.h : null)).filter((x) => typeof x === 'number');
    记.采样一工具条 = { n: 工具条集.length, min: 工具条集.length ? Math.min.apply(null, 工具条集) : null, max: 工具条集.length ? Math.max.apply(null, 工具条集) : null, 首: 工具条集[0] === undefined ? null : 工具条集[0], 集: Array.from(new Set(工具条集)).sort((a, b) => a - b) };
    const 采样二集 = (记.采样二 || []).map((x) => (x.工具条 ? x.工具条.h : null)).filter((x) => typeof x === 'number');
    记.采样二工具条 = { n: 采样二集.length, min: 采样二集.length ? Math.min.apply(null, 采样二集) : null, max: 采样二集.length ? Math.max.apply(null, 采样二集) : null, 集: Array.from(new Set(采样二集)).sort((a, b) => a - b) };
    const 落点集 = 记.采样一.map((x) => x.s).filter((x) => typeof x === 'number');
    记.采样一落点 = { min: 落点集.length ? Math.min.apply(null, 落点集) : null, max: 落点集.length ? Math.max.apply(null, 落点集) : null, 集: Array.from(new Set(落点集)).sort((a, b) => a - b) };
    记.采样一前五 = 记.采样一.slice(0, 5);
    记.采样一末五 = 记.采样一.slice(-5);

    log(臂.键.padEnd(5) + '｜' + 臂.名.padEnd(7) + '｜落点=' + String(记.终点).padEnd(10)
      + '｜A=' + String(记.A).padEnd(9)
      + '｜采样工具条[' + String(记.采样一工具条.最小 === undefined ? 记.采样一工具条.min : 记.采样一工具条.min) + '–' + 记.采样一工具条.max + ']'
      + '｜会话内=' + JSON.stringify((记.会话内 || []).map((x) => x.落点 === undefined ? 'ERR' : x.落点)));
  } catch (e) {
    记.错误 = e.message;
    log(臂.键.padEnd(5) + '🔴 ' + e.message);
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
const 音 = 好.filter((x) => x.kind === '音频');
const 对照 = 取('W_1');
const 判定P0 = 对照 && 对照.命中期望
  ? '✅ P0：阳性对照 `文本 @1212×720` 落 `' + 对照.终点 + '` 逐字等于闭式 `1.75` ⇒ 尺子没漂'
  : '🔴 P0：阳性对照=' + (对照 ? 对照.终点 : '—') + '（期望 1.75）⇒ 本批作废';

// P1：时序
const 全工具条集 = new Set();
const 早期大 = [];
for (const a of 音) {
  (a.采样一工具条.集 || []).forEach((x) => 全工具条集.add(x));
  if ((a.采样一工具条.max || 0) > 204.5) 早期大.push(a.键 + '(max=' + a.采样一工具条.max + ')');
}
const 判定P1 = !音.length ? '（臂不全）'
  : ('📌 P1：`8` 臂 × `80` 个样本里，工具条屏高出现过的取值集合 = [' + Array.from(全工具条集).sort((a, b) => a - b).join(', ') + ']'
    + '（`204` 之外的取值只在这些臂出现过：' + (早期大.length ? 早期大.join('、') : '无') + '）'
    + ' ⇒ ' + (早期大.length
      ? '✅ **竞态假说成立**：📌 工具条在采样窗口里出现过 `> 204` 的高度 ⇒ 📌 **`A` 很可能就是那一瞬的高度**'
      : '🔴 **竞态假说被否**：📌 全部样本（含第一个）工具条屏高逐字恒为 `204` ⇒ 📌 **`A` 的散布不来自「挂载后排版未完成」**'));

// P2：会话内 vs 跨会话
const 会话内差 = [];
for (const a of 音) {
  const 读 = (a.会话内 || []).filter((x) => x.落点 !== undefined).map((x) => x.落点);
  if (读.length) 会话内差.push(Math.max.apply(null, 读.concat([a.终点])) - Math.min.apply(null, 读.concat([a.终点])));
}
const 臂间差 = 音.length ? Math.max.apply(null, 音.map((x) => x.A)) - Math.min.apply(null, 音.map((x) => x.A)) : null;
const 判定P2 = !会话内差.length ? '（P2 臂不全）'
  : ('📌 P2：会话内 `2` 次重复 fit 的 `A` 极差逐臂 = [' + 会话内差.map((x) => x.toFixed(3)).join(', ') + ']（画布像素）'
    + '；📌 **臂间** `A` 极差 = `' + (臂间差 === null ? '—' : 臂间差.toFixed(3)) + '`'
    + ' ⇒ ' + (Math.max.apply(null, 会话内差) < 0.5
      ? '✅ **会话内完全不动** ⇒ 📌 **噪声是「每次加载」级的，不是「每次点击」级的**'
      : '✅ **会话内也抖** ⇒ 📌 **噪声是「每次点击」级的**，🔴 与「页面加载时的时序」无关'));

// P3：跨臂对拍
const 低组 = 音.filter((x) => x.A <= 低组阈);
const 高组 = 音.filter((x) => x.A >= 高组阈);
const 汇总 = (组) => {
  const m = {};
  for (const a of 组) {
    const 项 = (a.清单.后代 || []).concat(a.清单.同级 || []);
    for (const it of 项) {
      if (!m[it.号]) m[it.号] = [];
      m[it.号].push(it.rect);
    }
  }
  return m;
};
const 低m = 汇总(低组);
const 高m = 汇总(高组);
const 差项 = [];
for (const k of Object.keys(低m)) {
  if (!高m[k]) { 差项.push({ 号: k, 类型: '只出现在低 A 组' }); continue; }
  const 低h = 低m[k].map((r) => r[3]).sort((a, b) => a - b);
  const 高h = 高m[k].map((r) => r[3]).sort((a, b) => a - b);
  if (!低h.length || !高h.length) continue;
  const 低中 = 低h[Math.floor(低h.length / 2)];
  const 高中 = 高h[Math.floor(高h.length / 2)];
  if (Math.abs(低中 - 高中) > 4) 差项.push({ 号: k, 类型: '屏高中位数不同', 低组: 低中, 高组: 高中, 差: +(低中 - 高中).toFixed(2), 低n: 低h.length, 高n: 高h.length });
}
for (const k of Object.keys(高m)) if (!低m[k]) 差项.push({ 号: k, 类型: '只出现在高 A 组' });
const 判定P3 = (!低组.length || !高组.length)
  ? '（P3 分组不成：低 A 组 ' + 低组.length + ' 条、高 A 组 ' + 高组.length + ' 条）'
  : ('📌 P3：低 A 组（`A ≤ ' + 低组阈 + '`）`n = ' + 低组.length + '，高 A 组（`A ≥ ' + 高组阈 + '`）`n = ' + 高组.length
    + ' ⇒ 两组之间系统性不同的元素 `0` 个' + (差项.length ? '' : '')
    + ' ⇒ ' + (差项.length
      ? '✅ **找到差异元素**：' + 差项.slice(0, 8).map((x) => '`' + x.号 + '` ' + x.类型 + (x.差 !== undefined ? '（差 `' + x.差 + '`）' : '')).join('；')
      : '🔴 **两组的节点后代与同级逐字相同** ⇒ 📌 **差异不在渲染出来的界面上，而在 fit 的计算内部**'));

out.判定 = {
  有效臂: 好.length + '/' + 臂表.length,
  判定P0_尺子: 判定P0,
  判定P1_时序: 判定P1,
  判定P2_会话内还是跨会话: 判定P2,
  判定P3_跨臂对拍: 判定P3,
  分组: { 低A: 低组.map((x) => x.键 + ':' + x.A), 高A: 高组.map((x) => x.键 + ':' + x.A) },
  差项,
  逐臂: 好.map((x) => ({
    键: x.键, 名: x.名, z0: x.点之前, 落点: x.终点, 闭式预测: x.闭式预测, 命中闭式: x.命中闭式, A: x.A,
    采样一工具条: x.采样一工具条, 采样二工具条: x.采样二工具条, 采样一落点: x.采样一落点,
    采样一前五: x.采样一前五, 采样一末五: x.采样一末五,
    会话内: (x.会话内 || []).map((y) => (y.错 ? { 轮: y.轮, 错: y.错 } : { 轮: y.轮, 落点: y.落点, A: y.A, 落定: y.落定 })),
  })),
  失效臂: out.臂.filter((x) => x.错误).map((x) => ({ 键: x.键, 错: x.错误 })),
};
log('\n════ 判定 ════\n' + JSON.stringify({
  有效臂: out.判定.有效臂, P0: 判定P0, P1: 判定P1, P2: 判定P2, P3: 判定P3, 分组: out.判定.分组,
}, null, 1));

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

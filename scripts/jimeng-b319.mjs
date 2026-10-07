/**
 * 批次 319 · 「为什么偏偏 `音频`/`视频` 掉、`文本`/`时间线` 不掉」—— 嫌疑锁定在 `node-toolbar` 的屏尺寸行为上。
 *
 * 🔴 接批次 314–318（`31`+`5`+`6`+复算）：开关在 `w ∈ (1210, 1212]`、只认 `w`、与节点无关；
 *    🔴 连续三批只排除、没定因。批次 318 立规 198：**「机制存在」≠「它是原因」，两者之间要过一次量级比对。**
 *
 * 📌 **本批的证据起点（批次 317 落盘读数的复算，零浏览器成本）**：
 *    📌 `node-toolbar` 在 **`音频` 臂**里是 **`680×204`**，📌 在 `文本` 臂**里是 `560×40`** —— 🔴 **同一个 `data-testid`，两个 kind 两种行为**。
 *    📌 `560 = 320 × 1.75`，📌 **恰好等于「节点宽 × 落点」** ⇒ 📌 **文本的工具条像是画布尺寸**；
 *    📌 而 `音频` 的 `680×204` 在五臂里（落点 `1.75 → 1.07622`）**屏宽逐字恒定** ⇒ 📌 **屏固定**。
 *    📌 `audio-generation-form` 与 `node-toolbar-feature-host` 与 `node-toolbar` **是同一个盒子** `[…, 680, 204]`。
 *
 * 📌 **假设 H**：📌 **「落点掉不下去」的原因是工具条是否屏固定** ——
 *    📌 **屏固定** ⇒ 它的画布尺寸 `= 屏尺寸 / 落点`，📌 **落点越小画布尺寸越大** ⇒ compound 变大 ⇒ 落点被压低；
 *    📌 **画布尺寸** ⇒ 画布尺寸是常数 ⇒ 不进 compound 的分母 ⇒ 🔴 **批次 306 的闭式成立**。
 *
 * 📌 **判别设计（这是本批的关键）**：📌 批次 317 的 `文本` 臂**只在一个落点上测过**，
 *    🔴 「`560 = 320 × 1.75`」在**单一缩放下**完全可能只是巧合 ⇒ 📌 **必须给 `文本` 三个不同的落点**。
 *    📌 `文本` 的落点靠**改视口高**拿（批次 314 已证实：`h=600→1.375`、`h=900→2.125`、`h=720→1.75`），
 *    📌 **视口宽固定在 `1212`**（🔴 免得把 `w` 的开关混进来）。
 *
 * 📌 **判据（测量前写死）**：
 *   **P0** `文本` 三臂必须逐字命中闭式 `1.375` / `2.125` / `1.75`；🔴 任一不中 ⇒ 本批作废。
 *   **P1（主判据）** `文本` 的 `node-toolbar` **屏宽之比 ≈ 1**（三个落点 `1.375/1.75/2.125`，跨 `1.55×`）
 *        ⇒ 🔴 **文本的工具条也是屏固定 ⇒ H 被否**；
 *        **屏宽随落点变**（屏宽之比 `≈ 落点之比`）
 *        ⇒ ✅ **文本的工具条是画布尺寸 ⇒ 这就是「文本不掉」的原因**。
 *   **P2** `音频` 的 `node-toolbar` 在落点 `≈0.70 → 1.75`（跨 `2.5×`）下**屏宽逐字恒为 `680`**
 *        ⇒ ✅ **屏固定确认**，📌 与批次 304 的屏固定清单 `680×204` 逐字吻合。
 *   **P3** `音频` 三臂的落点**不命中**闭式，而 `文本` 三臂**全部命中** ⇒ ✅ **两者行为不同，这是本批的落点侧对照**。
 *
 * 前提检查：轴向自检 / 落定自检（三连读）/ 点击生效自检 /
 *   `aria` 精确匹配现找现量 / 参数写死 / 每臂独立浏览器 / 盒尺寸逐臂现量 /
 *   🔴 **采集的三段全部落盘**（批次 316 的教训）。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const STATE = `${process.env.HOME}/.jimeng-automation/state.json`;
const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b319.json';
const 放大键 = 'Meta+Equal';
const 闭式 = (w, h, W, H, z0) => Math.min((w - 532) / W, (h - 160) / H, z0);
const 盯 = [
  'node-toolbar|react-flow__node-toolbar',
  'node-toolbar-feature-host|nodrag.nopan',
  'audio-generation-form|generation-input-group.generation-input-panel',
  'audio-node-status-icon|shrink-0.text-dreamina-on-media-text-placeholder',
  'canvas-search-hover-preview|pointer-events-auto.overflow-hidden',
];

const 臂表 = [
  // P1 主判据：文本的三个落点（视口宽固定 1212，只改高）
  { 键: '文_h600', 组: '文', kind: '文本', 名: '文本 1', vw: 1212, vh: 600, 按: 13, 期望: 1.375 },
  { 键: '文_h720', 组: '文', kind: '文本', 名: '文本 1', vw: 1212, vh: 720, 按: 13, 期望: 1.75 },
  { 键: '文_h900', 组: '文', kind: '文本', 名: '文本 1', vw: 1212, vh: 900, 按: 13, 期望: 2.125 },
  // P2：音频的三个落点
  { 键: '音_h600', 组: '音', kind: '音频', 名: '音频 1', vw: 1212, vh: 600, 按: 13 },
  { 键: '音_h720', 组: '音', kind: '音频', 名: '音频 1', vw: 1212, vh: 720, 按: 13 },
  { 键: '音_h900', 组: '音', kind: '音频', 名: '音频 1', vw: 1212, vh: 900, 按: 13 },
  // 好区对照（w=1210）
  { 键: '文_1210', 组: '好', kind: '文本', 名: '文本 1', vw: 1210, vh: 720, 按: 13, 期望: 1.75 },
  { 键: '音_1210', 组: '好', kind: '音频', 名: '音频 1', vw: 1210, vh: 720, 按: 13, 期望: 1.75 },
];

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b319',
  问: 'node-toolbar 是不是屏固定？是的话，为什么文本不掉而音频/视频掉？',
  证据起点: {
    来源: '批次 317 落盘读数的复算，零浏览器成本',
    音频臂: 'node-toolbar / node-toolbar-feature-host / audio-generation-form 三者同一个盒子 680×204，五臂屏宽逐字恒定 680（落点 1.75→1.07622）',
    文本臂: 'node-toolbar 560×40，而 560 = 320 × 1.75 —— 但文本臂只测过一个落点，单缩放下的吻合可能是巧合',
  },
  假设H: '落点掉不下去的原因是工具条是否屏固定：屏固定 ⇒ 画布尺寸 = 屏尺寸/落点 ⇒ 落点越小画布尺寸越大 ⇒ compound 变大 ⇒ 落点被压低；画布尺寸 ⇒ 不进 compound 分母 ⇒ 批次 306 闭式成立',
  判据: {
    P0: '文本三臂逐字命中闭式 1.375/1.75/2.125，任一不中即本批作废',
    P1: '文本 node-toolbar 屏宽之比≈1 ⇒ 文本工具条也是屏固定 ⇒ H 被否；屏宽随落点变 ⇒ 是画布尺寸 ⇒ 这就是「文本不掉」的原因',
    P2: '音频 node-toolbar 在落点 0.70→1.75（跨 2.5×）下屏宽逐字恒为 680 ⇒ 屏固定确认',
    P3: '音频三臂落点不命中闭式、文本三臂全部命中 ⇒ 两者行为不同的落点侧对照',
  },
  臂表, 臂: [], 判定: {},
};

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
  const 框 = (list, 标) => list.map((e) => ({
    号: 号(e), rect: 矩形(e), pos: getComputedStyle(e).position,
    inNode: !!(节点 && 节点.contains(e)), 标: 标 || null,
  }));
  const 后代 = 节点 ? 框(Array.from(节点.querySelectorAll('*')), '后代') : [];
  const 同级 = 节点 && 节点.parentElement
    ? 框(Array.from(节点.parentElement.children).filter((x) => x !== 节点 && x.getBoundingClientRect().width > 0), '同级') : [];
  const 全域 = 框(Array.from(document.querySelectorAll('[data-testid]')));
  // 📌 盯着的几个盒子，各取面积最大的一个（同名可能有多个，取主体）
  const 盯住 = {};
  for (const 名 of window.__盯) {
    const c = 全域.filter((x) => x.号 === 名);
    盯住[名] = c.length
      ? c.reduce((p, q) => (q.rect[2] * q.rect[3] > p.rect[2] * p.rect[3] ? q : p)).rect
      : null;
  }
  return {
    节点屏盒: 节点 ? 矩形(节点) : null,
    节点盒: 节点 ? { W: 节点.offsetWidth, H: 节点.offsetHeight } : null,
    选中: Array.from(document.querySelectorAll('.react-flow__node.selected')).map((x) => x.dataset.id),
    盯住, 全域, 后代, 同级,
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
    // 📌 隐含的额外画布高度，以及它折回屏像素后的值（立规 198 要的量级）
    记.隐含a画布 = +((臂.vh - 160) - 目标.H * 记.终点).toFixed(4);
    记.隐含a屏 = +(记.隐含a画布 * 记.终点).toFixed(2);
    记.抽屉K = +(记.隐含a画布 * 记.终点).toFixed(2);

    await p.evaluate(([aria, 盯名]) => { window.__找的aria = aria; window.__盯 = 盯名; }, [ariaWant, 盯]);
    记.清单 = await p.evaluate(采集);
    记.清单.选中与目标一致 = 记.清单.选中.join(',') === nid;

    const tb = 记.清单.盯住['node-toolbar|react-flow__node-toolbar'];
    log(臂.键.padEnd(8) + '｜视口' + String(臂.vw + 'x' + 臂.vh).padEnd(10)
      + '｜落点=' + String(记.终点).padEnd(10)
      + (记.命中闭式 ? '｜✅闭式' : '｜🔴不中')
      + '｜K=' + String(记.抽屉K).padStart(7)
      + '｜工具条屏盒=' + JSON.stringify(tb));
  } catch (e) {
    记.错误 = e.message;
    log(臂.键.padEnd(8) + '🔴 ' + e.message);
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
const TB = 'node-toolbar|react-flow__node-toolbar';

const 文 = ['文_h600', '文_h720', '文_h900'].map(取).filter(Boolean);
const 音 = ['音_h600', '音_h720', '音_h900'].map(取).filter(Boolean);
const 好区 = ['文_1210', '音_1210'].map(取).filter(Boolean);

const 判定P0 = 文.length === 3 && 文.every((x) => x.命中期望)
  ? '✅ P0：文本三臂落 ' + 文.map((x) => x.终点).join(' / ') + '，逐字命中闭式 ' + 文.map((x) => x.闭式预测).join(' / ') + ' ⇒ 尺子没漂'
  : '🔴 P0：文本三臂落 ' + 文.map((x) => x.终点).join(' / ') + '，期望 1.375 / 1.75 / 2.125 ⇒ 本批作废';

function 屏盒序列(组) {
  return 组.map((x) => ({
    键: x.键, 落点: x.终点, 视口: x.vw + 'x' + x.vh,
    工具条: x.清单.盯住[TB], 表单: x.清单.盯住['audio-generation-form|generation-input-group.generation-input-panel'],
    悬停预览: x.清单.盯住['canvas-search-hover-preview|pointer-events-auto.overflow-hidden'],
    节点屏盒: x.清单.节点屏盒, K: x.抽屉K,
  }));
}
const 序文 = 屏盒序列(文); const 序音 = 屏盒序列(音);

function 判屏固定(序, 名) {
  const 有 = 序.filter((x) => x.工具条);
  if (有.length < 2) return { 名, 结论: '🔴 工具条读数不足（' + 有.length + ' 臂）' };
  const 宽 = 有.map((x) => x.工具条[2]);
  const 落 = 有.map((x) => x.落点);
  const 落跨 = Math.max.apply(null, 落) / Math.min.apply(null, 落);
  const 宽比 = Math.max.apply(null, 宽) / Math.min.apply(null, 宽);
  const 屏固定 = new Set(宽.map((x) => x.toFixed(1))).size === 1;
  return {
    名, 屏宽集合: Array.from(new Set(宽.map((x) => x.toFixed(1)))),
    落点跨比: +落跨.toFixed(4), 屏宽跨比: +宽比.toFixed(4),
    跟落点: Math.abs(宽比 / 落跨 - 1) < 0.02,
    是屏固定: 屏固定,
    结论: 屏固定
      ? '✅ **屏固定**：落点跨 `' + 落跨.toFixed(3) + '×`，屏宽跨比只有 `' + 宽比.toFixed(4) + '`（屏宽逐字恒 `' + 宽[0] + '`）'
      : (Math.abs(宽比 / 落跨 - 1) < 0.02
        ? '✅ **画布尺寸**：落点跨 `' + 落跨.toFixed(3) + '×`，屏宽跨比 `' + 宽比.toFixed(4) + '` **与之同步** ⇒ 屏宽 = 画布宽 × 落点'
        : '⚠️ 两者都不像：落点跨 `' + 落跨.toFixed(3) + '×`、屏宽跨比 `' + 宽比.toFixed(4) + '`'),
  };
}

const 判文 = 判屏固定(序文, '文本 1');
const 判音 = 判屏固定(序音, '音频 1');

const 判定P1 = 文.length < 3 ? '（文本臂不全）'
  : (判文.是屏固定
    ? '🔴 P1：`文本 1` 的 `node-toolbar` **三个落点下屏宽逐字恒定** ⇒ 🔴 **文本的工具条也是屏固定 ⇒ 假设 H 被否**'
    : (判文.跟落点
      ? '✅ P1：`文本 1` 的 `node-toolbar` 屏宽**跟着落点走**（落点跨 `' + 判文.落点跨比 + '×`，屏宽跨比 `' + 判文.屏宽跨比 + '`）'
        + ' ⇒ ✅ **文本的工具条是画布尺寸，不进 compound 的分母 ⇒ 这就是「文本不掉、音频/视频掉」的原因**'
      : '⚠️ P1：`文本 1` 的工具条屏宽既不恒定也不跟落点 ⇒ 🔴 **H 不成立**，另找原因'));

const 判定P2 = 音.length < 2 ? '（音频臂不全）'
  : (判音.是屏固定
    ? '✅ P2：`音频 1` 的 `node-toolbar` 在落点跨 `' + 判音.落点跨比 + '×`（`' + 判音.屏宽集合.join('/') + '` 屏宽）下**逐字恒定**'
      + ' ⇒ ✅ **屏固定确认**，📌 与批次 304 的屏固定清单 `680×204` 逐字吻合'
    : '🔴 P2：`音频 1` 的工具条屏宽不是恒定（' + 判音.屏宽集合.join('/') + '）⇒ 屏固定被否');

const 判定P3 = (文.length === 3 && 音.length === 3)
  ? '📌 P3（落点侧对照）：文本三臂' + (文.every((x) => x.命中闭式) ? '**全部命中**闭式' : '有 ' + 文.filter((x) => !x.命中闭式).length + ' 臂不中')
    + '；音频三臂' + (音.filter((x) => x.命中闭式).length === 0 ? '**全部不中**闭式' : '中 ' + 音.filter((x) => x.命中闭式).length + ' 臂')
    + '｜📌 音频的隐含 K（额外画布高度折回屏像素）：' + 音.map((x) => x.键 + '=' + x.抽屉K).join('、')
    + ' ⇒ ' + (function () {
      const ks = 音.map((x) => x.抽屉K);
      const 跨 = Math.max.apply(null, ks) / Math.min.apply(null, ks);
      return '跨比 `' + 跨.toFixed(4) + '` ⇒ ' + (跨 < 1.03 ? '✅ **K 在音频内几乎恒定**（立规 198 的量级比对通过）' : '⚠️ K 不恒定');
    })()
  : '（P3 臂不全）';

out.判定 = {
  有效臂: 好.length + '/' + 臂表.length,
  判定P0_尺子: 判定P0,
  判定P1_文本工具条: 判文.结论,
  判定P1_总: 判定P1,
  判定P2_音频工具条: 判音.结论,
  判定P2_总: 判定P2,
  判定P3_落点侧对照: 判定P3,
  序列_文本: 序文,
  序列_音频: 序音,
  序列_好区: 好区.map((x) => ({ 键: x.键, 视口: x.vw + 'x' + x.vh, 落点: x.终点, 工具条: x.清单.盯住[TB], 表单: x.清单.盯住['audio-generation-form|generation-input-group.generation-input-panel'] })),
  逐臂: 好.map((x) => ({ 键: x.键, 名: x.名, 视口: x.vw + 'x' + x.vh, z0: x.点之前, 落点: x.终点, 闭式预测: x.闭式预测, 命中闭式: x.命中闭式, K: x.抽屉K, 隐含a画布: x.隐含a画布 })),
};
log('\n════ 判定 ════\n' + JSON.stringify({ 有效臂: out.判定.有效臂, P0: 判定P0, P1: 判定P1, P2: 判定P2, P3: 判定P3 }, null, 1));
log('\n序列：'); for (const s of 序文) log('  文 ' + JSON.stringify(s));
for (const s of 序音) log('  音 ' + JSON.stringify(s));

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
  log('\n末态独立复查：' + JSON.stringify(out.末态));
} finally { try { await pz.close(); await brz.close(); } catch (e) { /* 忽略 */ } }

fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log('写入 ' + OUT);
process.exit(0);
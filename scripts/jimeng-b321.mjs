/**
 * 批次 321 · `A ≈ 209`（画布常数）到底是多少？—— 用同一份脚本取新读数，再与历史读数合并做判决。
 *
 * 🔴 接批次 320：那份额是**画布空间的常数 inset `A ≈ 209`**（音频跨比 `1.0687`、视频 `1.0211`），
 *    🔴 但 `A ≈ 209` 与工具条屏高 `204` 数值接近、**单位不同**，批次 320 明确「不认领」。
 *    ⚠️ 批次 320 每档只有 `1` 个读数，而**单读数的散布是 `±2%`（批次 314/315）** ⇒ 📌 **分不清 `204` 与 `211`**。
 *
 * 📌 **一个先算出来的事实（不是探针，是汇总）**：把此前**同一节点、同一视口 `1212×720`、同一按键 `13` 次**
 *    的**全部 `10` 条**历史读数汇总：
 *    📌 `s` 均值 `1.09091`、标准差 `0.01137`（相对 `1.04%`）；
 *    📌 `A = 560 − 320·s` ⇒ **均值 `210.91`、标准差 `3.64`、均值标准误 `1.15`**；
 *    ⇒ ✅ **`A = 204` 的 z 值是 `−6.01`（可排除）；`209` 是 `−1.66`、`211` 是 `+0.08`（都不能排除）。**
 *    🔴 **但这是跨 6 个批次、6 份脚本的汇总** ⇒ 📌 **同源但不同码**，📌 必须用**一份脚本**重取新读数复核。
 *
 * 🔴 **本批自己刚犯的一个错，如实记**：第一次汇总时 🔴 **把 `h=640` 那条（`safeH = 480`）混进了 `1212×720` 组**，
 *    算出 `A` 均值 `218.58`、把 `204` 的 z 稀释到 `−1.88`。⇒ 📌 **混条件会把「可排除」降级成「不能排除」**
 *    （立规 195⑤「复现性极差必须固定 `(kind, 视口, z0)`」的同款，本批第 N 次现形）。
 *
 * 📌 **本批三件事**：
 *   **P1（判决）** 同一脚本取 `6` 条新读数，与历史 `10` 条合并 ⇒ `n ≥ 16`；
 *        判据写死为 **`|假设 − 均值| > 3 × 均值标准误` 即判该假设可排除**（🔴 不许用 1σ 或 2σ 说「排除」）。
 *   **P2（节点依赖）** `音频 2` 与 `音频 68` 各 `2` 条 ⇒ 与 `音频 1` 的 `A` 比；
 *        🔴 批次 320 明说「**每档都用同一节点，排掉的是随 kind 变，没排随节点变**」⇒ 📌 本批补这一格。
 *   **P3（报全）** 📌 **必须报全部读数与来源批次**，📌 **不许只报均值**（否则读者看不出散布）。
 *
 * 📌 **判据（测量前写死）**：
 *   **P0** 阳性对照 `文本 @1212×720` 必须逐字落闭式 `1.75`（它的 `A` 恒为 `0`）；🔴 不中 ⇒ 本批作废。
 *   **P1** 合并后 `|204 − A均值| > 3 × 标准误` ⇒ ✅ **`A = 204` 可排除**；否则 🔴 不能排除。
 *   **P2** 任一节点的 `A` 与 `音频 1` 相差 `> 3 × 标准误` ⇒ 🔴 **`A` 随节点变**；否则 📌 在这三个节点上 `A` 一致。
 *
 * 前提检查：轴向自检 / 落定自检（三连读）/ 点击生效自检 /
 *   `aria` 精确匹配现找现量 / 参数写死 / 每臂独立浏览器 / 盒尺寸逐臂现量。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const STATE = `${process.env.HOME}/.jimeng-automation/state.json`;
const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b321.json';
const 放大键 = 'Meta+Equal';
const 闭式 = (w, h, W, H, z0) => Math.min((w - 532) / W, (h - 160) / H, z0);

/** 📌 视口固定 `1212×720` ⇒ `safeH = 560`、`H0 = 320`、`A = 560 − 320·s` */
const VW = 1212; const VH = 720; const SAFE_H = VH - 160; const H0 = 320;

/**
 * 📌 历史读数：**同一个节点（`音频 1`）、同一个视口（`1212×720`）、同一按键次数（`13`）、同一套流程**。
 * 📌 每条都记来源批次 —— 🔴 **混来源等于混条件**，所以这里逐条标出，不合并成一句「历史数据」。
 */
const 历史 = [
  ['b311', 1.10512], ['b314', 1.08914], ['b314b', 1.09021],
  ['b314d甲', 1.08247], ['b314d乙', 1.09607], ['b316', 1.08914],
  ['b317A1', 1.07622], ['b317A2', 1.11166], ['b317A3', 1.09253], ['b319', 1.07651],
];

const 臂表 = [
  // 音频 1：同一脚本取 6 条新读数
  { 键: 'X1_1', 组: '音1', kind: '音频', 名: '音频 1' },
  { 键: 'X1_2', 组: '音1', kind: '音频', 名: '音频 1' },
  { 键: 'X1_3', 组: '音1', kind: '音频', 名: '音频 1' },
  { 键: 'X1_4', 组: '音1', kind: '音频', 名: '音频 1' },
  { 键: 'X1_5', 组: '音1', kind: '音频', 名: '音频 1' },
  { 键: 'X1_6', 组: '音1', kind: '音频', 名: '音频 1' },
  // P2 节点依赖
  { 键: 'X2_1', 组: '音2', kind: '音频', 名: '音频 2' },
  { 键: 'X2_2', 组: '音2', kind: '音频', 名: '音频 2' },
  { 键: 'X68_1', 组: '音68', kind: '音频', 名: '音频 68' },
  { 键: 'X68_2', 组: '音68', kind: '音频', 名: '音频 68' },
  // 阳性对照
  { 键: 'W_1', 组: '对照', kind: '文本', 名: '文本 1', 期望: 1.75 },
];

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b321',
  问: 'A（画布常数 inset）到底是 204 还是别的数？它随节点变吗？',
  先算出来的事实: {
    口径: '音频 1 @1212×720，按13次，同一套流程',
    n: 历史.length,
    s均值: +(历史.reduce((a, b) => a + b[1], 0) / 历史.length).toFixed(5),
    A均值: +(SAFE_H - H0 * (历史.reduce((a, b) => a + b[1], 0) / 历史.length)).toFixed(2),
    结论: 'A=204 的 z≈−6.01 可排除；A=209 z≈−1.66、A=211 z≈+0.08 不能排除',
    但: '🔴 这是跨 6 个批次、6 份脚本的汇总 ⇒ 本批用同一份脚本复核',
    本批自己犯的错: '🔴 第一次汇总时把 h=640 那条（safeH=480）混进了本组，把 A 均值算成 218.58、把 204 的 z 稀释到 −1.88 ⇒ 混条件会把「可排除」降级成「不能排除」',
  },
  判据: {
    P0: '阳性对照 文本 @1212×720 必须逐字落闭式 1.75，不中即本批作废',
    P1: '合并后 |204 − A均值| > 3 × 均值标准误 ⇒ A=204 可排除；不许用 1σ 或 2σ 说「排除」',
    P2: '音频2/音频68 的 A 与 音频1 相差 > 3 × 标准误 ⇒ A 随节点变；否则在这三个节点上一致',
    P3: '必须报全部读数与来源批次，不许只报均值',
  },
  视口: VW + 'x' + VH, safeH: SAFE_H, H0: H0, 历史读数: 历史,
  臂表, 臂: [], 判定: {},
};

for (const 臂 of 臂表) {
  let br = null; let p = null; let nid = null;
  const 记 = { 键: 臂.键, 组: 臂.组, kind: 臂.kind, 名: 臂.名 };
  try {
    br = await chromium.launch({ headless: true });
    const ctx = await br.newContext({ storageState: STATE, viewport: { width: VW, height: VH } });
    p = await ctx.newPage();
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 60000 });
    await p.waitForTimeout(6000);

    const 实际 = await p.evaluate(() => ({ w: innerWidth, h: innerHeight }));
    if (实际.w !== VW || 实际.h !== VH) throw new Error('轴向自检失败：' + 实际.w + 'x' + 实际.h);

    const ariaWant = 臂.kind + ' node: ' + 臂.名;
    const 目标 = await p.evaluate((aria) => {
      const e = Array.from(document.querySelectorAll('.react-flow__node[data-id]'))
        .find((x) => x.getAttribute('aria-label') === aria);
      return e ? { id: e.dataset.id, W: e.offsetWidth, H: e.offsetHeight } : null;
    }, ariaWant);
    if (!目标) throw new Error('找不到 aria 为「' + ariaWant + '」的节点');
    nid = 目标.id;
    记.画布盒 = { W: 目标.W, H: 目标.H };
    if (目标.H !== H0 && 臂.kind === '音频') 记.盒高与预期不符 = true;

    for (let i = 0; i < 13; i++) { await p.keyboard.press(放大键); await p.waitForTimeout(380); }
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

    记.闭式预测 = +闭式(VW, VH, 目标.W, 目标.H, 记.点之前).toFixed(6);
    记.命中闭式 = Math.abs(记.终点 - 记.闭式预测) < 5e-5;
    if (臂.期望 !== undefined) 记.命中期望 = Math.abs(记.终点 - 臂.期望) < 5e-6;
    // 📌 只有音频才谈 A；文本的 A 按定义是 0（命中闭式）
    记.A = 臂.kind === '音频' ? +(SAFE_H - 目标.H * 记.终点).toFixed(3) : 0;

    log(臂.键.padEnd(7) + '｜' + 臂.名.padEnd(7) + '｜z0=' + String(记.点之前).padEnd(8)
      + '｜落点=' + String(记.终点).padEnd(10)
      + (记.命中闭式 ? '｜✅闭式' : '｜🔴不中')
      + '｜A=' + 记.A);
  } catch (e) {
    记.错误 = e.message;
    log(臂.键.padEnd(7) + '🔴 ' + e.message);
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
const 组 = (g) => 好.filter((x) => x.组 === g);
const 统计 = (arr) => {
  const n = arr.length;
  if (!n) return null;
  const m = arr.reduce((a, b) => a + b, 0) / n;
  const sd = n > 1 ? Math.sqrt(arr.reduce((a, b) => a + (b - m) * (b - m), 0) / (n - 1)) : null;
  return { n, 均值: +m.toFixed(3), 标准差: sd === null ? null : +sd.toFixed(3), 标准误: sd === null ? null : +(sd / Math.sqrt(n)).toFixed(3) };
};

const 对照 = 取('W_1');
const 判定P0 = 对照 && 对照.命中期望
  ? '✅ P0：阳性对照 `文本 @1212×720` 落 `' + 对照.终点 + '` 逐字等于闭式 `1.75` ⇒ 尺子没漂'
  : '🔴 P0：阳性对照=' + (对照 ? 对照.终点 : '—') + '（期望 1.75）⇒ 本批作废';

// P1：历史 10 + 本批音1 的 6 条，合并
const 新音1 = 组('音1').map((x) => x.A).filter((x) => typeof x === 'number');
const 合并A = 历史.map((x) => +(SAFE_H - H0 * x[1]).toFixed(3)).concat(新音1);
const 统计1 = 统计(合并A);
const 假设列表 = [204, 209, 211, 215];
const z表 = 假设列表.map((h) => ({ 假设: h, z: 统计1 && 统计1.标准误 ? +(((h - 统计1.均值) / 统计1.标准误)).toFixed(2) : null }));
const 可排除 = z表.filter((x) => x.z !== null && Math.abs(x.z) > 3);
const 判定P1 = !统计1 || !统计1.标准误 ? '（臂不全）'
  : ('📌 P1：合并 `n = ' + 统计1.n + '`（历史 `10` + 本批音1 `6`）⇒ `A` 均值 **`' + 统计1.均值 + '`**、标准差 `' + 统计1.标准差 + '`、均值标准误 `' + 统计1.标准误 + '`'
    + '｜各假设的 z：' + z表.map((x) => x.假设 + '→' + x.z).join('、')
    + ' ⇒ ' + (可排除.length
      ? '✅ **可排除（`|z|>3`）：' + 可排除.map((x) => '`A=' + x.假设 + '`').join('、') + '**'
      : '⚠️ 没有一个假设能被 `3σ` 排除 ⇒ 📌 `A` 落在这些候选之间，🔴 不许硬挑一个')
    + '｜📌 `A = 204` 的 z 是 `' + (z表.find((x) => x.假设 === 204) || {}).z + '` ⇒ '
    + ((z表.find((x) => x.假设 === 204) || {}).z !== null && Math.abs((z表.find((x) => x.假设 === 204) || {}).z) > 3
      ? '✅ **批次 320「不认领 `204`」这一处理由升级为「已排除」**'
      : '🔴 **`A = 204` 仍不能排除** ⇒ 批次 320 的「不认领」维持原状'));

// P2：节点依赖
const s2 = 统计(组('音2').map((x) => x.A).filter((x) => typeof x === 'number'));
const s68 = 统计(组('音68').map((x) => x.A).filter((x) => typeof x === 'number'));
const 差2 = s2 && 统计1 && 统计1.标准差 ? Math.abs(s2.均值 - 统计1.均值) : null;
const 差68 = s68 && 统计1 && 统计1.标准差 ? Math.abs(s68.均值 - 统计1.均值) : null;
const 判定P2 = (!s2 || !s68) ? '（P2 臂不全）'
  : ('📌 P2：`音频 1`（n=' + 统计1.n + '）`A` 均值 `' + 统计1.均值 + '`'
    + '；`音频 2`（n=' + s2.n + '）`' + s2.均值 + '`；`音频 68`（n=' + s68.n + '）`' + s68.均值 + '`'
    + '｜差：`音频2` `' + (差2 !== null ? 差2.toFixed(2) : '—') + '`、`音频68` `' + (差68 !== null ? 差68.toFixed(2) : '—') + '`，'
    + '📌 同组自身标准差 `' + 统计1.标准差 + '`'
    + ' ⇒ ' + (差2 !== null && 差2 > 3 * 统计1.标准差
      ? '🔴 **`A` 随节点变**'
      : (差68 !== null && 差68 > 3 * 统计1.标准差
        ? '🔴 **`A` 随节点变**'
        : '✅ **三个节点上 `A` 在 `3σ` 内一致** ⇒ 📌 在这三个节点上 `A` 是画布级的常量')));

out.判定 = {
  有效臂: 好.length + '/' + 臂表.length,
  判定P0_尺子: 判定P0,
  判定P1_A是多少: 判定P1,
  判定P2_节点依赖: 判定P2,
  统计_合并: 统计1,
  P3_全部读数: {
    历史: 历史.map((x) => ({ 来源: x[0], s: x[1], A: +(SAFE_H - H0 * x[1]).toFixed(3) })),
    本批音1: 组('音1').map((x) => ({ 键: x.键, s: x.终点, A: x.A })),
    本批音2: 组('音2').map((x) => ({ 键: x.键, s: x.终点, A: x.A })),
    本批音68: 组('音68').map((x) => ({ 键: x.键, s: x.终点, A: x.A })),
  },
  逐臂: 好.map((x) => ({ 键: x.键, 名: x.名, z0: x.点之前, 落点: x.终点, 闭式预测: x.闭式预测, 命中闭式: x.命中闭式, A: x.A })),
};
log('\n════ 判定 ════\n' + JSON.stringify({ 有效臂: out.判定.有效臂, P0: 判定P0, P1: 判定P1, P2: 判定P2 }, null, 1));

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
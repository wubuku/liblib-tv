/**
 * 批次 323b · **修两处自己的错**：① 采样窗口根本没盖住点击那一刻；② P2 那一格是死代码。
 *
 * 🔴 **错一（本批自己犯的，如实记）**：`jimeng-b323.mjs` 的 `搜并点` 在点中结果行之后 `await 3200ms` 才返回，
 *    📌 采样是**在它返回之后**才开始的 ⇒ 📌 **第一个样本落在点击后 `≈3.2` 秒**，
 *    🔴 **而「挂载 → 量高 → 算 fit → 设 transform」这个竞态窗口早就过去了**
 *    ⇒ 🔴 **b323 的 P1 根本没有测到它声称要测的东西**（立规 201④ 的反面：**没测到 ≠ 不存在，但没覆盖窗口就是没测**）。
 *    ⇒ 📌 **修法：先起采样器，再点击。** 采样器在点击前就开始记，于是「点击前 / 点击瞬间 / 点击后」三段都在数据里。
 *
 * 🔴 **错二**：`jimeng-b323.mjs` 里查找 `文本 1` 的 id 被写在 `if (臂.kind === '文本')` 里面
 *    ⇒ 🔴 **音频臂（唯一需要 P2 的那些）永远拿不到 `文id`** ⇒ 📌 `会话内` 数组恒为 `[]`，**P2 一次都没跑**。
 *
 * 📌 **本批要判的（判据测量前写死）**：
 *   **P0** 阳性对照 `文本 @1212×720` 必须逐字落 `1.75`；🔴 不中 ⇒ 本批作废。
 *   **P1（时序，本次真覆盖到窗口）** 点击前 `≈0.4` 秒起、每 `60ms` 采一次、共 `120` 个样本
 *        ⇒ 📌 报出「工具条**第一次出现**的那个样本」的高度（挂载瞬间有多高）、
 *        📌 以及「落点**第一次变化**的那个样本」；
 *        ⇒ 若挂载瞬间的工具条高度 `> 204` ⇒ ✅ **竞态假说成立，`A` 就是那一瞬的高度**；
 *        ⇒ 若挂载瞬间逐字是 `204`、而落点却在别的时刻才定 ⇒ 🔴 **竞态假说被否，`A` 的来源另有其人**。
 *   **P2（会话内 vs 跨会话）** 同一会话内**再做 `2` 次 fit**（先搜到 `文本 1` 点走，再搜回 `音频 1`）
 *        ⇒ 会话内 `2` 次的 `A` 极差逐臂 `< 0.5` 画布像素 ⇒ 📌 **噪声是「每次加载」级的**；否则 📌 **是「每次点击」级的**。
 *
 * 前提检查：轴向自检 / 落定自检（三连读）/ 点击生效自检 /
 *   `aria` 精确匹配现找现量 / 参数写死 / 每臂独立浏览器 / 盒尺寸逐臂现量。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const STATE = `${process.env.HOME}/.jimeng-automation/state.json`;
const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b323b.json';
const 放大键 = 'Meta+Equal';
const 闭式 = (w, h, W, H, z0) => Math.min((w - 532) / W, (h - 160) / H, z0);
const VW = 1212;
const VH = 720;
const SAFE_H = VH - 160;
const H0 = 320;
const 样本数 = 120;
const 间隔 = 60;

/** 📌 页面内采样器：每个样本同时记「落点」「工具条屏高」「表单屏高」「节点屏高与顶边」。 */
const 采样器 = async ([n, ms]) => {
  const 列 = [];
  const 取盒 = (tid) => {
    const es = Array.from(document.querySelectorAll('[data-testid="' + tid + '"]'))
      .map((x) => x.getBoundingClientRect())
      .filter((r) => r.width > 0 && r.height > 0);
    if (!es.length) return null;
    const b = es.reduce((q, r) => (r.width * r.height > q.width * q.height ? r : q));
    return { h: Math.round(b.height * 100) / 100, top: Math.round(b.top * 100) / 100, bottom: Math.round(b.bottom * 100) / 100 };
  };
  const 取节点 = (aria) => {
    const e = Array.from(document.querySelectorAll('.react-flow__node[data-id]'))
      .find((x) => x.getAttribute('aria-label') === aria);
    if (!e) return null;
    const b = e.getBoundingClientRect();
    return { h: Math.round(b.height * 100) / 100, top: Math.round(b.top * 100) / 100, bottom: Math.round(b.bottom * 100) / 100 };
  };
  for (let i = 0; i < n; i++) {
    const vp = document.querySelector('.react-flow__viewport');
    const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
    列.push({ i, s: m ? Number(m[1]) : null, 工具条: 取盒('node-toolbar'), 表单: 取盒('audio-generation-form'), 节点: 取节点(window.__目标aria) });
    await new Promise((r) => setTimeout(r, ms));
  }
  return 列;
};

const 臂表 = [];
for (let i = 1; i <= 4; i++) 臂表.push({ 键: 'S' + i, 组: '重复', kind: '音频', 名: '音频 1' });
臂表.push({ 键: 'W_1', 组: '对照', kind: '文本', 名: '文本 1', 期望: 1.75 });

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b323b',
  问: '点下去那一瞬间工具条有多高？A 的散布是「每次加载」级还是「每次点击」级？',
  本批修的两处自己的错: {
    错一: 'b323 的采样在「点中后 3.2 秒」才开始 ⇒ 没盖住竞态窗口 ⇒ P1 测的不是它声称要测的。修法：先起采样器，再点击。',
    错二: 'b323 里查「文本 1」id 的那句写在 if (臂.kind === 文本) 里面 ⇒ 音频臂永远拿不到 ⇒ P2 一次没跑。修法：改成无条件查。',
  },
  判据: {
    P0: '阳性对照 文本 @1212×720 必须逐字落 1.75，不中即本批作废',
    P1: '点击前 0.4 秒起采样；报「工具条第一次出现」的高度与「落点第一次变化」的样本；挂载瞬间 >204 ⇒ 竞态成立；挂载瞬间逐字 204 ⇒ 竞态被否',
    P2: '同一会话内再做 2 次 fit；会话内 A 极差逐臂 < 0.5 画布像素 ⇒ 噪声是每次加载级；否则是每次点击级',
  },
  采样: { 样本数, 间隔毫秒: 间隔 },
  臂表, 臂: [], 判定: {},
};

/** 📌 打开搜索面板、输入词、**只把结果行准备好并返回坐标**（不点，留给调用方在采样窗口里点）。 */
const 备好结果行 = async (p, 词表, 目标id) => {
  const 钮 = await p.evaluate(() => {
    const b = document.querySelector('button[aria-label="搜索"]');
    if (!b) return null;
    const r = b.getBoundingClientRect();
    return { 中心: [r.x + r.width / 2, r.y + r.height / 2], 可见: r.width > 0 && r.height > 0 && r.y >= 0 && r.bottom <= innerHeight };
  });
  if (!钮 || !钮.可见) return { 错: '找不到可见的搜索钮' };
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
    if (r && r.可见) return { 中心: r.中心 };
  }
  return { 错: '搜不到可见结果行' };
};

/** 📌 完整走一遍「点中某个节点」，返回落点。 */
const 搜并点 = async (p, 词表, 目标id) => {
  const r = await 备好结果行(p, 词表, 目标id);
  if (r.错) return r.错;
  await p.mouse.click(r.中心[0], r.中心[1]);
  await p.waitForTimeout(3200);
  return null;
};

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
    // 📌 错二的修法：**无条件**查「文本 1」的 id（音频臂也要它，才能做「点走再点回来」）
    const t = await p.evaluate((aria) => {
      const e = Array.from(document.querySelectorAll('.react-flow__node[data-id]'))
        .find((x) => x.getAttribute('aria-label') === aria);
      return e ? e.dataset.id : null;
    }, '文本 node: 文本 1');
    文id = t;
    if (!文id) throw new Error('找不到「文本 1」，P2 做不了');

    for (let i = 0; i < 13; i++) { await p.keyboard.press(放大键); await p.waitForTimeout(380); }
    await p.waitForTimeout(1600);
    const 读缩放 = () => p.evaluate(() => {
      const vp = document.querySelector('.react-flow__viewport');
      const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
      return m ? Number(m[1]) : null;
    });
    记.点之前 = await 读缩放();
    if (记.点之前 === null) throw new Error('点之前读不到 scale');

    const ariaWant = 臂.kind + ' node: ' + 臂.名;
    await p.evaluate((aria) => { window.__目标aria = aria; }, ariaWant);
    const 行 = await 备好结果行(p, [臂.名, ariaWant, 臂.kind], nid);
    if (行.错) throw new Error(行.错);

    // 📌 错一的修法：**先起采样器**（不 await），让它先记下点击前的样子，再点
    const 采样中 = p.evaluate(采样器, [样本数, 间隔]);
    await p.waitForTimeout(420);
    await p.mouse.click(行.中心[0], 行.中心[1]);
    记.列 = await 采样中;

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

    // 📌 错二的修法：现在音频臂也拿得到 文id ⇒ P2 真跑
    记.会话内 = [];
    for (let k = 0; k < 2; k++) {
      const e2 = await 搜并点(p, ['文本 1', '文本 node: 文本 1'], 文id);
      if (e2) { 记.会话内.push({ 轮: k, 错: e2 }); break; }
      const e3 = await 搜并点(p, [臂.名, ariaWant, 臂.kind], nid);
      if (e3) { 记.会话内.push({ 轮: k, 错: e3 }); break; }
      const a = await 读缩放();
      await p.waitForTimeout(2600);
      const b = await 读缩放();
      await p.waitForTimeout(1800);
      const c = await 读缩放();
      记.会话内.push({ 轮: k, a, b, c, 落定: a === b && b === c, 落点: c, A: 臂.kind === '音频' ? +(SAFE_H - H0 * c).toFixed(3) : 0 });
    }

    // 📌 P1 的时序摘要：工具条第一次出现、落点第一次变化
    const 首个工具条 = 记.列.findIndex((x) => x.工具条 !== null);
    记.首个工具条样本 = 首个工具条;
    记.首个工具条高 = 首个工具条 >= 0 ? 记.列[首个工具条].工具条.h : null;
    记.工具条高序列 = Array.from(new Set(记.列.filter((x) => x.工具条).map((x) => x.工具条.h))).sort((a, b) => a - b);
    const s集 = 记.列.map((x) => x.s);
    const 首个变 = s集.findIndex((v, i) => i > 0 && v !== s集[i - 1]);
    记.落点序列 = Array.from(new Set(s集.filter((v) => v !== null)));
    记.首个变化样本 = 首个变;
    记.点击前落点 = 首个变 >= 0 ? s集[0] : s集[s集.length - 1];
    记.点击后落点 = 首个变 >= 0 ? s集[首个变] : null;
    记.落点稳定样本 = s集.findIndex((v, i) => i > 0 && v === 记.终点 && s集[i - 1] === 记.终点);
    记.采样窗口内落点极差 = 记.点击前落点 !== null && 记.点击后落点 !== null ? +Math.abs(记.点击后落点 - 记.点击前落点).toFixed(6) : null;
    记.关键窗口 = 记.列.slice(Math.max(0, 首个变 - 2), Math.max(0, 首个变) + 6);

    log(臂.键.padEnd(5) + '｜' + 臂.名.padEnd(7) + '｜落点=' + String(记.终点).padEnd(10)
      + '｜A=' + String(记.A).padEnd(9)
      + '｜首个工具条样本=' + String(首个工具条).padEnd(4) + '高=' + String(记.首个工具条高).padEnd(8)
      + '｜工具条高集=' + JSON.stringify(记.工具条高序列)
      + '｜落点 ' + String(记.点击前落点) + '→' + String(记.点击后落点)
      + '｜会话内=' + JSON.stringify(记.会话内.map((x) => (x.错 ? 'ERR' : x.落点))));
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

const 全工具条高 = new Set();
音.forEach((a) => (a.工具条高序列 || []).forEach((x) => 全工具条高.add(x)));
const 挂载高 = 音.map((x) => x.首个工具条高);
const 判定P1 = !音.length ? '（臂不全）'
  : ('📌 P1：采样器在**点击前 `0.42` 秒**就起了，`4` 臂 × `' + 样本数 + '` 个样本'
    + '｜工具条**第一次出现**的样本序号逐臂 = [' + 音.map((x) => x.首个工具条样本).join(', ') + ']'
    + '，**挂载那一刻**的屏高逐臂 = [' + 挂载高.join(', ') + ']'
    + '｜整个采样窗口里工具条屏高出现过的取值 = [' + Array.from(全工具条高).sort((a, b) => a - b).join(', ') + ']'
    + '｜落点 `点击前 → 点击后` 逐臂 = [' + 音.map((x) => String(x.点击前落点) + '→' + String(x.点击后落点)).join('、') + ']'
    + ' ⇒ ' + (挂载高.some((h) => h > 204.5)
      ? '✅ **竞态假说成立**：📌 工具条挂载瞬间就比 `204` 高 ⇒ 📌 **`A` 很可能就是那一瞬的高度**'
      : (挂载高.every((h) => h === 204)
        ? '🔴 **竞态假说被否**：📌 工具条**挂载的第一帧就逐字是 `204`**，且整个窗口里没出现过别的值 ⇒ 📌 **`A` 的散布不来自「挂载后排版未完成」**'
        : '📌 挂载瞬间的屏高既不全是 `204` 也不都大于 `204.5` ⇒ ⚠️ 需要逐条看关键窗口')));

const 会话内差 = [];
for (const a of 音) {
  const 读 = (a.会话内 || []).filter((x) => x.落点 !== undefined).map((x) => x.A);
  if (读.length) 会话内差.push(+Math.max.apply(null, 读.concat([a.A])).toFixed(0) - Math.min.apply(null, 读.concat([a.A])).toFixed(0));
}
const 会话内极差 = 会话内差.map((x) => Math.abs(Number(x)));
const 臂间极差 = 音.length ? +(Math.max.apply(null, 音.map((x) => x.A)) - Math.min.apply(null, 音.map((x) => x.A))).toFixed(3) : null;
const 判定P2 = !会话内极差.length ? '（P2 臂不全）'
  : ('📌 P2：会话内 `2` 次重复 fit 的 `A` 极差逐臂 = [' + 会话内极差.join(', ') + ']（画布像素）'
    + '；📌 **臂间** `A` 极差 = `' + (臂间极差 === null ? '—' : 臂间极差) + '`'
    + ' ⇒ ' + (Math.max.apply(null, 会话内极差) < 0.5
      ? '✅ **会话内完全不动** ⇒ 📌 **噪声是「每次加载」级的，不是「每次点击」级的** ⇒ 📌 **竞态/时序类解释整体出局**'
      : '✅ **会话内也抖** ⇒ 📌 **噪声是「每次点击」级的**'));

out.判定 = {
  有效臂: 好.length + '/' + 臂表.length,
  判定P0_尺子: 判定P0,
  判定P1_时序: 判定P1,
  判定P2_会话内还是跨会话: 判定P2,
  逐臂: 好.map((x) => ({
    键: x.键, 名: x.名, z0: x.点之前, 落点: x.终点, 闭式预测: x.闭式预测, 命中闭式: x.命中闭式, A: x.A,
    首个工具条样本: x.首个工具条样本, 首个工具条高: x.首个工具条高, 工具条高序列: x.工具条高序列,
    落点序列: x.落点序列, 点击前落点: x.点击前落点, 点击后落点: x.点击后落点,
    落点稳定样本: x.落点稳定样本, 采样窗口内落点极差: x.采样窗口内落点极差,
    会话内: (x.会话内 || []).map((y) => (y.错 ? { 轮: y.轮, 错: y.错 } : { 轮: y.轮, 落点: y.落点, A: y.A, 落定: y.落定 })),
    关键窗口: x.关键窗口,
  })),
  失效臂: out.臂.filter((x) => x.错误).map((x) => ({ 键: x.键, 错: x.错误 })),
};
log('\n════ 判定 ════\n' + JSON.stringify({
  有效臂: out.判定.有效臂, P0: 判定P0, P1: 判定P1, P2: 判定P2,
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

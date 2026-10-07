/**
 * 批次 311 · 跨 `kind` 实测落点表 —— 把 16 批机制结论回写成**面向用户可用的判据**。
 *
 * 📌 起意：Goal 的完成判据是「画布相关功能的操作说明全部编写完毕」，
 *    本批自查发现手册正文 `navigate-canvas.md` 只有**窗口宽度**一个自测判据
 *    （「看缩放读数」「把窗口拖宽就恢复」），
 *    🔴 **但它没说「同一个窗口下，不同类型节点会卡在不同的倍数」**。
 *    🔴 而批次 306 的闭式 `min((w−532)/320,(h−160)/320)` 只对 `文本` 逐字命中，
 *    📌 `音频` 实测 `1.07643` ≠ `1.75` ⇒ 🔴 **「零 inset」不可跨 kind 外推**
 *    （批次 306 已标注，本批要把差异量出来）。
 *
 * 📌 **本批要产出的，是一张面向用户的表**：
 *    「同一个窗口下，我点不同类型的节点，会各自放大到多少」——
 *    📌 这是**用户能自己照着核对**的，而不是「看读数」这种事后确认。
 *
 * 📌 **判据（测量前写死）**：
 *   **P1** 每个 `kind` 各测一个节点，落点读 `viewport scale()`，
 *          📌 **同一视口、同一按键次数**，📌 唯一变量是节点类型；
 *   **P2** 🔴 **必须先量各节点的 `compound`**（用 `w/落点` 反算），
 *          📌 用来验证「音频/视频含外框、文本零 inset」这条**跨 kind 推论**；
 *   **P3** 🔴 **必须有 `文本` 作阳性对照**：它必须落 `1.75`（批次 306 的 `9/9` 已证），
 *          🔴 否则本批整表作废（立规 189：不拿不可信的尺子量东西）。
 *
 * 前提检查：轴向自检 / 落定自检 / 点击生效自检 / `aria` 精确匹配现找现量 /
 *   参数写死（按键次数固定）/ 每臂独立浏览器。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const STATE = `${process.env.HOME}/.jimeng-automation/state.json`;
const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b311.json';
const 放大键 = 'Meta+Equal';
const w = 1212; const h = 720;
const 按 = 13;

/** 📌 各 kind 各取一个节点（按 aria 精确匹配，现找现量，不硬编码 id） */
const 臂表 = [
  { 键: '文本1', kind: '文本', 名: '文本 1' },
  { 键: '音频1', kind: '音频', 名: '音频 1' },
  { 键: '视频1', kind: '视频', 名: '视频 1' },
  { 键: '时间线1', kind: '时间线', 名: '时间线 1' },
  { 键: '导演台', kind: '外部', 名: '导演台' },
  { 键: '文本2', kind: '文本', 名: '文本 2' },
];

const safeW = w - 532; const safeH = h - 160;
const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b311',
  问: '同一视口下不同 kind 的节点，取景落点各是多少？「零 inset」能不能跨 kind 外推？',
  判据: {
    P1: '同视口同按键次数，唯一变量=节点类型',
    P2: '用 w/落点 反算 compound，验证音频/视频含外框、文本零 inset',
    P3: '文本臂必须落 1.75 作阳性对照，否则整表作废',
  },
  w, h, 按, safeW, safeH, 臂表, 臂: [], 判定: {},
};

for (const A of 臂表) {
  let br = null; let p = null; let nid = null;
  const 记 = { 键: A.键, kind: A.kind, 名: A.名 };
  try {
    br = await chromium.launch({ headless: true });
    const ctx = await br.newContext({ storageState: STATE, viewport: { width: w, height: h } });
    p = await ctx.newPage();
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 60000 });
    await p.waitForTimeout(6000);
    const 实际 = await p.evaluate(() => ({ w: innerWidth, h: innerHeight }));
    if (实际.w !== w || 实际.h !== h) throw new Error(`轴向自检失败：${实际.w}×${实际.h}`);

    const ariaWant = `${A.kind} node: ${A.名}`;
    const 目标 = await p.evaluate((aria) => {
      const e = Array.from(document.querySelectorAll('.react-flow__node[data-id]'))
        .find((x) => x.getAttribute('aria-label') === aria);
      return e ? { id: e.dataset.id, W: e.offsetWidth, H: e.offsetHeight } : null;
    }, ariaWant);
    if (!目标) throw new Error(`找不到 aria 为「${ariaWant}」的节点`);
    nid = 目标.id;
    记.画布盒 = { W: 目标.W, H: 目标.H };

    for (let i = 0; i < 按; i++) { await p.keyboard.press(放大键); await p.waitForTimeout(380); }
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
    for (const 词 of [A.名, ariaWant, A.kind]) {
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
    if (!行) throw new Error(`搜不到「${A.名}」的可见结果行`);
    await p.mouse.click(行.中心[0], 行.中心[1]);
    await p.waitForTimeout(3200);
    const r1 = await 读缩放();
    await p.waitForTimeout(2600);
    const r2 = await 读缩放();
    await p.waitForTimeout(2000);
    const r3 = await 读缩放();

    记.读1 = r1; 记.读2 = r2; 记.读3 = r3;
    记.落定 = (r1 === r2 && r2 === r3);
    记.终点 = r3;
    const 选 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((x) => x.dataset.id));
    记.点击生效 = 选.includes(nid);
    if (!记.点击生效) throw new Error(`点击未生效（选中=${JSON.stringify(选)}）`);

    // 📌 P2：由落点反算 compound（宽度项与高度项各一）
    记.反推compoundW = +(safeW / r3).toFixed(3);
    记.反推compoundH = +(safeH / r3).toFixed(3);
    记.多出宽 = +(记.反推compoundW - 目标.W).toFixed(3);
    记.多出高 = +(记.反推compoundH - 目标.H).toFixed(3);
    log(`${A.键.padEnd(9)}｜z0=${String(记.z0).padEnd(8)}｜终点=${String(r3).padEnd(10)}｜compound=${记.反推compoundW}×${记.反推compoundH}｜多出 ${记.多出宽}×${记.多出高}`);
  } catch (e) {
    记.错误 = e.message;
    log(`${A.键.padEnd(9)}🔴 ${e.message}`);
  } finally {
    try { if (p) await p.close(); } catch (e) { /* 忽略 */ }
    try { if (br) await br.close(); } catch (e) { /* 忽略 */ }
    out.臂.push(记);
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

// ───────── 判定 ─────────
const 好 = out.臂.filter((x) => !x.错误 && x.点击生效 && x.落定 && x.终点 !== undefined);
const 文本臂 = 好.filter((x) => x.kind === '文本');
const 对照ok = 文本臂.length > 0 && 文本臂.every((x) => Math.abs(x.终点 - 1.75) < 1e-6);

const 判定P3 = 对照ok
  ? '✅ P3：文本臂 ' + 文本臂.map((x) => `${x.键}=${x.终点}`).join('、') + ' 逐字落 1.75 ⇒ 尺子没漂，本表可用'
  : '🔴 P3：文本臂未逐字落 1.75（实测 ' + 文本臂.map((x) => `${x.键}=${x.终点}`).join('、') + '）⇒ 本表作废';

const 判定P2 = 对照ok
  ? '📌 P2：各 kind 的 compound 反算值见下表 ⇒ '
    + (好.some((x) => Math.abs(x.多出宽) > 1)
      ? '🔴 **不是所有 kind 都零 inset**：多出量非零的 kind = '
        + 好.filter((x) => Math.abs(x.多出宽) > 1).map((x) => `${x.键}(+${x.多出宽}宽/+${x.多出高}高)`).join('、')
        + ' ⇒ 📌 **批次 306 的「零 inset」只对 `文本` 成立，不可跨 kind 外推**'
      : '📌 所有 kind 的多出量都 ≈0')
  : '（P2 未判：阳性对照不过）';

const 判定P1 = `📌 P1：同视口 ${w}×${h}、同按键 ${按} 次，唯一变量是节点类型 ⇒ ${好.length} 臂有效`;

out.判定 = {
  有效臂: `${好.length}/${臂表.length}`,
  落点表: 好.map((x) => ({ 名: x.名, kind: x.kind, 盒: x.画布盒, 终点: x.终点, compound: `${x.反推compoundW}×${x.反推compoundH}`, 多出: `${x.多出宽}×${x.多出高}` })),
  落点极差: 好.length > 1 ? +(Math.max(...好.map((x) => x.终点)) - Math.min(...好.map((x) => x.终点))).toFixed(5) : null,
  判定P1: 判定P1,
  判定P2: 判定P2,
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
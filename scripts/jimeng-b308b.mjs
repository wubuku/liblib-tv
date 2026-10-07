/**
 * 批次 308b · 补测 `z0 ∈ (1.93, 2.316)` 这一段 —— 找**第二个**转折点。
 *
 * 🔴 起意：批次 308 的 6 档显示图景是「**两个分支**」，不是一个：
 *    `z0 ≤ 1.34` 不跳（终点 `=== z0`）｜`z0 ∈ {1.608, 1.93}` 跳到**低分支 `≈1.55`**｜
 *    `z0 ≥ 2.316` 跳到**高分支 `= vs = 1.75`**。
 *    🔴 **而 `z0 ∈ (1.93, 2.316)` 这一段没测** ⇒ **第二个转折点藏在里面**。
 *
 * 📌 **难点（先说清，免得下一个人重踩）**：
 *    🔴 放大键是 **`1.2` 倍递进**，整数档给不出 `1.93` 与 `2.316` 之间的 `z0`。
 *    📌 历史映射：`按8=1.117 / 按9=1.34 / 按10=1.608 / 按11=1.93 / 按12=2.316 / 按13=2.779`。
 *    📌 **解法：`11` 键打底 + 画布滚轮微调**，🔴 **滚轮是独立于键盘的第二个变量**，
 *    📌 所以本批要把**滚轮方向与次数写死**，并在判据里**只按实际读到的 `z0` 分组**。
 *
 * 📌 **判据（测量前写死）**：
 *   **P1** 滚轮档的 `z0` 必须**逐字落在 `(1.93, 2.316)` 开区间内**
 *          ⇒ 📌 落进来本批的读数才有效；🔴 落不进来就**如实记无效**，不硬凑。
 *   **P2** 若区间内某档终点 **`=== 1.75`** ⇒ ✅ **高分支的起点 ≤ 该 `z0`**，
 *          📌 与低分支的分界点被夹在 `(1.93, 该档]` 内；
 *          🔴 若某档终点仍 `≈1.55` ⇒ ✅ **低分支一直延伸到该 `z0`**。
 *   **P3** 🔴 **必须有 `z0 > vs` 的对照臂落 `1.75`**（批次 307 P3 / 308 P3 的同款门槛），
 *          🔴 否则「高分支 `=1.75`」这个前提本身没被验证。
 *   **P4** 🔴 **量级门槛（立规 186）**：与低分支历史区间的中心 `≈1.5564` 比较，
 *          📌 **偏差必须显著超过该区间自身极差 `0.02291`**，才算「跳到高分支」。
 *
 * 前提检查：轴向自检 / 落定自检（连读三次）/ 点击生效自检 /
 *   `aria` 精确匹配现找现量 / 参数写死 / 每臂独立浏览器。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const STATE = `${process.env.HOME}/.jimeng-automation/state.json`;
const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b308b.json';
const 放大键 = 'Meta+Equal';
const w = 1212; const h = 720;
const kind = '文本'; const 名 = '文本 1';
const 基准vs = 1.75;
/** 📌 低分支历史区间（批次 303–308 合并的 11 个读数） */
const 低分支中心 = 1.5564;
const 低分支极差 = 0.02291;
/** 📌 要填的 z0 缺口区间（开区间） */
const 缺口下 = 1.93; const 缺口上 = 2.316;

/**
 * 📌 臂表：`11` 键打底（`z0=1.93`）+ 滚轮微调。
 * 📌 🔴 滚轮方向与次数是本批唯一变量；📌 `无滚轮` 那一档是**基线复现**（批次 308 的 `按11`）。
 */
const 臂表 = [
  { 键: '基线11键', 按: 11, 滚轮: 0 },
  { 键: '滚上1', 按: 11, 滚轮: +1 },
  { 键: '滚上2', 按: 11, 滚轮: +2 },
  { 键: '滚上3', 按: 11, 滚轮: +3 },
  { 键: '滚下1', 按: 11, 滚轮: -1 },
  { 键: '对照13键', 按: 13, 滚轮: 0, 对照: true },
];

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b308b',
  问: 'z0 落在 (1.93, 2.316) 之间时，终点还在低分支 ≈1.55 还是已经跳到高分支 1.75？',
  判据: {
    P1: '滚轮档 z0 必须逐字落在 (1.93,2.316) 开区间内，否则该臂无效',
    P2: '终点===1.75 ⇒ 高分支起点≤该z0；仍≈1.55 ⇒ 低分支延伸到此',
    P3: '须有 z0>vs 的对照臂落 1.75',
    P4: '量级门槛（立规186）：与低分支中心1.5564的偏差须显著超过 0.02291',
  },
  基准vs, 低分支中心, 低分支极差, 缺口下, 缺口上, w, h, 臂表, 臂: [], 判定: {},
};

for (const A of 臂表) {
  let br = null; let p = null; let nid = null;
  const 记 = { 键: A.键, 按: A.按, 滚轮: A.滚轮, 对照: !!A.对照 };
  try {
    br = await chromium.launch({ headless: true });
    const ctx = await br.newContext({ storageState: STATE, viewport: { width: w, height: h } });
    p = await ctx.newPage();
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 60000 });
    await p.waitForTimeout(6000);
    const 实际 = await p.evaluate(() => ({ w: innerWidth, h: innerHeight }));
    if (实际.w !== w || 实际.h !== h) throw new Error(`轴向自检失败：实测 ${实际.w}×${实际.h}`);

    const ariaWant = `${kind} node: ${名}`;
    const 目标 = await p.evaluate((aria) => {
      const e = Array.from(document.querySelectorAll('.react-flow__node[data-id]'))
        .find((x) => x.getAttribute('aria-label') === aria);
      return e ? { id: e.dataset.id, W: e.offsetWidth, H: e.offsetHeight } : null;
    }, ariaWant);
    if (!目标) throw new Error(`找不到 aria 为「${ariaWant}」的节点`);
    nid = 目标.id;
    记.盒 = { W: 目标.W, H: 目标.H };

    for (let i = 0; i < A.按; i++) { await p.keyboard.press(放大键); await p.waitForTimeout(380); }
    await p.waitForTimeout(1400);
    const 读缩放 = () => p.evaluate(() => {
      const vp = document.querySelector('.react-flow__viewport');
      const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
      return m ? Number(m[1]) : null;
    });

    // 📌 滚轮在**画布区域**上滚，🔴 先把鼠标移到画布中心，避免滚到侧栏
    if (A.滚轮 !== 0) {
      const 画布点 = await p.evaluate(() => {
        const el = document.querySelector('.react-flow__pane') || document.querySelector('.rf__wrapper');
        if (!el) return null;
        const r = el.getBoundingClientRect();
        return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2), 可见: r.width > 0 && r.height > 0 && r.y >= 0 && r.bottom <= innerHeight };
      });
      if (!画布点 || !画布点.可见) throw new Error('找不到可见的画布区域来滚轮');
      await p.mouse.move(画布点.x, 画布点.y);
      await p.waitForTimeout(300);
      for (let i = 0; i < Math.abs(A.滚轮); i++) {
        await p.mouse.wheel(0, A.滚轮 > 0 ? -120 : 120);
        await p.waitForTimeout(450);
      }
      await p.waitForTimeout(900);
    }

    const z0 = await 读缩放();
    记.z0 = z0;
    if (z0 === null) throw new Error('读不到缩放');

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
    if (!记.点击生效) throw new Error(`点击未生效（选中=${JSON.stringify(选)}）`);
    记.落vs = Math.abs(读3 - 基准vs) < 1e-6;
    记.在缺口内 = (z0 > 缺口下 && z0 < 缺口上);
    // 📌 P4 量级门槛：与低分支中心的偏差 vs 低分支自身极差
    记.偏差低分支 = +(读3 - 低分支中心).toFixed(5);
    记.超噪声带 = Math.abs(读3 - 低分支中心) > 低分支极差;
    log(`${A.键.padEnd(10)}｜z0=${String(z0).padEnd(9)}｜终点=${String(读3).padEnd(10)}｜落vs=${String(记.落vs).padEnd(5)}｜在缺口内=${String(记.在缺口内).padEnd(5)}｜偏低分支=${记.偏差低分支}`);
  } catch (e) {
    记.错误 = e.message;
    log(`${A.键.padEnd(10)}🔴 ${e.message}`);
  } finally {
    try { if (p) await p.close(); } catch (e) { /* 忽略 */ }
    try { if (br) await br.close(); } catch (e) { /* 忽略 */ }
    out.臂.push(记);
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

// ───────── 判定 ─────────
const 好 = out.臂.filter((x) => !x.错误 && x.点击生效 && x.终点 !== undefined && x.落定);
const 对照臂 = 好.find((x) => x.对照);
const 基线 = 好.find((x) => x.键 === '基线11键');
const 缺口臂 = 好.filter((x) => !x.对照 && x.滚轮 !== 0 && x.在缺口内);
const 未进缺口 = 好.filter((x) => !x.对照 && x.滚轮 !== 0 && !x.在缺口内);

const 判定P1 = 缺口臂.length > 0
  ? `✅ P1：${缺口臂.length} 条臂的 z0 逐字落在 (${缺口下}, ${缺口上}) 开区间内：${缺口臂.map((x) => `${x.键}(z0=${x.z0})`).join('、')}`
  : `🔴 P1：没有滚轮档落进 (${缺口下}, ${缺口上})；实际读到的 z0 = ${好.filter((x) => x.滚轮 !== 0 && !x.对照).map((x) => `${x.键}:${x.z0}`).join('、') || '—'} ⇒ 📌 滚轮步长太大/方向相反，本段未取到有效读数`;

const 判定P2 = (缺口臂.length > 0)
  ? (缺口臂.every((x) => x.落vs)
    ? `✅ P2：缺口内 ${缺口臂.length} 条臂终点**逐字落 vs=${基准vs}** ⇒ 高分支的起点 ≤ ${Math.min(...缺口臂.map((x) => x.z0))} ⇒ 📌 **第二个转折点被夹在 (${缺口下}, ${Math.min(...缺口臂.map((x) => x.z0))}] 内**`
    : (缺口臂.every((x) => x.超噪声带 && !x.落vs)
      ? `⚠️ P2：缺口内终点 ${缺口臂.map((x) => x.终点).join('、')} 既不落 vs、偏差又超噪声带 ⇒ 既不是高分支也不是已知低分支，🔴 可能有第三条分支`
      : `✅ P2：缺口内仍有臂停在低分支（${缺口臂.filter((x) => !x.超噪声带).map((x) => `${x.键}→${x.终点}`).join('、')}）⇒ 低分支至少延伸到该 z0`))
  : '（无有效缺口臂，P2 未判）';

const 判定P3 = 对照臂 && 对照臂.落vs
  ? `✅ P3：对照臂（${对照臂.键}/z0=${对照臂.z0}）终点 ${对照臂.终点} 逐字落 vs=${基准vs} ⇒ 尺子没漂`
  : `🔴 P3：对照臂未落 vs=${基准vs}（终点 ${对照臂 ? 对照臂.终点 : '—'}）⇒ 本批判据作废`;

const 判定P4 = `📌 P4：低分支中心 ${低分支中心}、自身极差 ${低分支极差}（批次303–308 合并 11 读数）`
  + `；各臂偏差：${缺口臂.map((x) => `${x.键}=${x.偏差低分支}`).join('、') || '—'}`
  + ` ⇒ 偏差需 > ${低分支极差} 才算「跳出低分支」`;

out.判定 = {
  有效臂: `${好.length}/${臂表.length}`,
  缺口内臂: 缺口臂.map((x) => ({ 键: x.键, z0: x.z0, 终点: x.终点, 落vs: x.落vs })),
  未进缺口臂: 未进缺口.map((x) => `${x.键}(z0=${x.z0})`),
  基线11键终点: 基线 ? 基线.终点 : null,
  判定P1: 判定P1,
  判定P2: 判定P2,
  判定P3: 判定P3,
  判定P4: 判定P4,
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
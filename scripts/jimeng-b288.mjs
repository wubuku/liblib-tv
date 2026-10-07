/**
 * 批次 288：`vs` 随视口宽怎么变 —— 验「`safeW = w − 532`」的线性段与它的饱和点。
 *
 * 📌 起意（批次 287 的结果）：
 *   读到的代码给出 **`zoom_after = min( max(z0, 0.5) , vs )`**，
 *   `vs = vf(min(safeW/W, safeH/targetH))`，**`vs` 与当前缩放无关**
 *   ⇒ 📌 **「按足够多次放大键再点」，读到的平台值就是 `vs` 本身**（批次 287 已用 `12` 臂验过这个读法）。
 *   批次 287 只在 **`w = 1212` 一个宽度**上读到：
 *     `图片 b22-upload`（`569 × 320`）→ `vs = 1.19531`（两个臂逐字相同）
 *     `视频 1`（`320 × 569`）        → `vs ≈ 0.623`（`± 0.0040`，疑动画未落定）
 *   ⇒ 🔴 **`safeW` 的宽度依赖性完全没测**：`w=1212` 那一个点既不能证也不能否「`safeW = w − 532`」。
 *
 * 📌 **两条预测（测量前写死，前提④）**：
 *   🔴 **P1（线性段，从来没测过）**：按批次 244–253 的「宽侧屏上律」`screen = max(100, w − 532)`，
 *     代入 `图片` 的 `(569 × 320)` 与 `H = 720`：
 *       `vs(w) = min( (w − 532)/569 , (720 − 160)/320 ) = min( (w − 532)/569 , 1.75 )`
 *     ⇒ `700→0.29526`、`900→0.64675`、`1100→0.99824`、`1500→1.69771`
 *   🔴 **P2（饱和点，🔴 全新的一段）**：两条臂一旦相等就**被高度项接住** ——
 *     `(w − 532)/569 = 1.75` ⇒ `w = 1527.75`
 *     ⇒ 🔴 **`w = 1600` 上 `vs` 应恰好等于 `1.75`，而且这是第一次测到这个高度**。
 *     📌 **这个宽度以前从未被测过** ⇒ 它是本批真正的样本外点。
 *   📌 P3 **`视频 1` 的 `vs` 应与宽度无关**（它是**高项**在管）：
 *     `vs = safeH/targetH`，与 `w` 无关 ⇒ `w=700/900` 两档应读到**同一个数**。
 *     🔴 **而旧经验律给的是 `min((w−532)/320, 560/569)`** ⇒ `700` 给 `0.525`、`900` 给 `0.98419`
 *     ⇒ 📌 **两档不同 ⇒ 旧律错；两档相同 ⇒ 旧律错且「`targetH ≠ Hc`」成立。**
 *
 * 📌 **五条前提**：
 *   ① **轴向自检**：`innerW/innerH` 逐字等于设定值；
 *   ② 🔴 **`z0 > vs` 硬门**：本批读的是**平台**，若 `z0 ≤ vs` 读到的就是 `z0` 而不是 `vs`
 *      ⇒ **该臂作废**（这一条治的就是「把起点当成落点」这种自欺）；
 *   ③ 🔴 **落定自检（补批次 287 的缺陷②）**：点完**连读两次**，必须逐字相同，
 *      否则标「未落定」并把两次读数都记下来（不丢数据、不硬判）；
 *   ④ 🔴 **点击生效自检**：`selectedNodeIds` 必须含目标节点（沿用批次 287，前提③）；
 *   ⑤ 🔴 **参数写死**：`0.5 / 0.08 / 8 / 412 / 532 / 160` 全部取自代码或已发布结论，
 *      **不许用实测值反推**；预测里只有 `safeW`、`safeH` 是**待检验量**，不是可调参数。
 *
 * 📌 **纪律**：只按放大键、只点搜索结果行；不新建/不删除/不上传/不分享/不进扣费页/**绝不点生成**；
 *   末态在实验流程之外独立复查（立规 140）。
 *
 * 用法：node scripts/jimeng-b288.mjs      （落盘 /tmp/b288.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B288_OUT || '/tmp/b288.json';
const 高 = 720;
const 放大键 = 'Meta+Equal';
const 按够 = 13;                        // 0.26 × 1.2^13 ≈ 4.1 ≫ 任何一档的 vs

// 🔴 前提⑤：常数写死
const 屏上律 = (w) => Math.max(100, w - 532);       // 批次 244–253「宽侧」那条（待检验）
const 安全高 = 720 - 160;                            // 批次 266 的 (H − 160)（待检验）
const 地板 = 0.5, 上限 = 8, 下限 = 0.08;
const vf = (z) => Math.min(上限, Math.max(下限, z));
const 预测vs = (w, W, Hc) => +vf(Math.min(屏上律(w) / W, 安全高 / Hc)).toFixed(6);

const 臂表 = [
  ...[700, 900, 1100, 1500, 1600].map((w) => ({ w, h: 高, 键: '图片', id: 'node_gref4sw056', 备用名: ['图片 b22-upload', 'b22-upload', '图片'] })),
  ...[700, 900].map((w) => ({ w, h: 高, 键: '视频', id: 'node_236ctpehgg', 备用名: ['视频 1', '视频'] })),
];

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b288',
  问: 'vs 随视口宽怎么变？「safeW = w − 532」的线性段与它在 w≈1528 的饱和点，测得到吗？',
  常量: { 屏上律: 'max(100, w−532)', 安全高: 'H−160', 地板, 上限, 下限 },
  臂: [], 判定: {},
};

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

const 读 = (p) => p.evaluate(() => {
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  const z = document.querySelector('[data-testid="canvas-zoom-percent"]');
  return {
    scale: m ? Number(m[1]) : null,
    百分比: z ? z.textContent.trim() : null,
    选中: Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.dataset.id),
  };
});

for (const { w, h, 键, id, 备用名 } of 臂表) {
  const p = await ctx.newPage();
  const 记 = { w, h, 键, 节点: id, 按了几次: 按够 };
  try {
    await p.setViewportSize({ width: w, height: h });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(6000);
    const 实际 = await p.evaluate(() => ({ w: innerWidth, h: innerHeight }));
    if (实际.w !== w || 实际.h !== h) throw new Error(`轴向自检失败：要 ${w}×${h}，实测 ${实际.w}×${实际.h}`);

    const 节 = await p.evaluate((nid) => {
      const e = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
      return e ? { W: e.offsetWidth, Hc: e.offsetHeight } : null;
    }, id);
    if (!节) throw new Error('目标节点不在画布上');
    记.节点尺寸 = 节;
    记.预测vs = 预测vs(w, 节.W, 节.Hc);

    for (let i = 0; i < 按够; i++) { await p.keyboard.press(放大键); await p.waitForTimeout(380); }
    await p.waitForTimeout(1200);
    const z0 = await 读(p);
    记.z0 = z0.scale; 记.z0_百分比 = z0.百分比;
    if (z0.scale === null || !(z0.scale > 0)) throw new Error('读不到缩放');
    // 前提②：z0 必须高于预测 vs，否则读到的不是平台
    if (!(z0.scale > 记.预测vs)) throw new Error(`z0(${z0.scale}) 不高于预测 vs(${记.预测vs}) ⇒ 读不到平台，本臂作废`);

    const 钮 = await p.evaluate(() => {
      const b = document.querySelector('button[aria-label="搜索"]');
      if (!b) return null;
      const r = b.getBoundingClientRect();
      return { 中心: [r.x + r.width / 2, r.y + r.height / 2], 可见: r.width > 0 && r.height > 0 && r.y >= 0 && r.bottom <= innerHeight };
    });
    if (!钮 || !钮.可见) throw new Error('找不到可见的搜索钮');
    await p.mouse.click(钮.中心[0], 钮.中心[1]);
    await p.waitForTimeout(1600);

    let 行 = null, 用名 = null;
    for (const 名 of 备用名) {
      await p.evaluate(() => { const i = document.querySelector('[data-testid="canvas-search-panel"] input'); if (i) { i.focus(); i.select(); } });
      await p.keyboard.type(名, { delay: 80 });
      await p.waitForTimeout(2000);
      const r = await p.evaluate((nid) => {
        const e = document.querySelector(`[data-testid="canvas-search-result-node_${nid.replace(/^node_/, '')}"]`);
        if (!e) return null;
        const b = e.getBoundingClientRect();
        return { 中心: [Math.round(b.x + b.width / 2), Math.round(b.y + b.height / 2)], 可见: b.width > 0 && b.height > 0 && b.y >= 0 && b.bottom <= innerHeight && b.x >= 0 && b.right <= innerWidth };
      }, id);
      if (r && r.可见) { 行 = r; 用名 = 名; break; }
    }
    if (!行) throw new Error('搜不到可见的结果行');
    记.用名 = 用名;
    await p.mouse.click(行.中心[0], 行.中心[1]);
    await p.waitForTimeout(3000);
    const a1 = await 读(p);
    await p.waitForTimeout(2500);
    const a2 = await 读(p);                       // 前提③：落定自检
    记.z后1 = a1.scale; 记.z后2 = a2.scale;
    记.落定 = a1.scale === a2.scale;
    记.选中 = a2.选中;
    记.点击生效 = a2.选中.includes(id);
    if (!记.点击生效) throw new Error(`点击未生效（选中=${JSON.stringify(a2.选中)}）`);
    记.vs实测 = a2.scale;
    记.误差 = +(a2.scale - 记.预测vs).toFixed(6);
    log(`${String(w).padStart(4)}×${h}｜${键} ${节.W}×${节.Hc}｜z0=${z0.scale}｜vs实测=${a2.scale}｜预测=${记.预测vs}｜误差 ${记.误差}｜落定 ${记.落定 ? '✅' : '🔴 ' + a1.scale + ' vs ' + a2.scale}`);
  } catch (e) {
    记.错误 = e.message; log(`${String(w).padStart(4)}×${h}｜${键} 🔴 ${e.message}`);
  } finally {
    try { await p.close(); } catch (e) { /* 忽略 */ }
    out.臂.push(记);
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

const 好 = out.臂.filter((x) => !x.错误 && x.点击生效 && x.vs实测 !== undefined);
const 未落定 = 好.filter((x) => !x.落定);
log('\n════ 汇总 ════');
log(`有效臂 ${好.length} / 作废 ${out.臂.length - 好.length}｜其中未落定 ${未落定.length}`);
const 图 = 好.filter((x) => x.键 === '图片').sort((a, c) => a.w - c.w);
log('\n  w      节点        vs实测        预测 min((w−532)/W, 1.75)   误差');
for (const x of 图) log(`  ${String(x.w).padEnd(6)} ${String(x.节点尺寸.W + '×' + x.节点尺寸.Hc).padEnd(11)} ${String(x.vs实测).padEnd(13)} ${String(x.预测vs).padEnd(26)} ${x.误差}`);
const 视 = 好.filter((x) => x.键 === '视频').sort((a, c) => a.w - c.w);
if (视.length) {
  log(`\n  视频（高项在管，应与 w 无关）：${视.map((x) => `w=${x.w} → ${x.vs实测}`).join('；')}`);
  log(`  旧经验律预测：${视.map((x) => `w=${x.w} → ${(Math.min(屏上律(x.w) / x.节点尺寸.W, 安全高 / x.节点尺寸.Hc)).toFixed(6)}`).join('；')}`);
}

if (!好.length) {
  out.判定 = { 结论: '🔴 一条有效臂都没有 ⇒ 整组作废，不出判定' };
} else if (未落定.length === 好.length) {
  out.判定 = { 结论: `🔴 ${好.length} 臂全部未落定 ⇒ 平台读数不可信，整组作废（需更长等待或落定轮询）` };
} else {
  const 命中 = 好.filter((x) => Math.abs(x.误差) <= 1e-3);
  const 饱和 = 图.find((x) => x.w === 1600);
  out.判定 = {
    有效臂: `${好.length}/${out.臂.length}`,
    P1_线性段: 图.filter((x) => x.w < 1528).map((x) => `w=${x.w}: ${x.vs实测} vs ${x.预测vs}`).join('；'),
    P2_饱和点: 饱和 ? `w=1600 实测 ${饱和.vs实测}，预测 ${饱和.预测vs}（= 高度项 ${安全高}/${图[0]?.节点尺寸.Hc}）` : '（1600 那臂没数据）',
    P3_视频: 视.length >= 2 ? `${视[0].w} 与 ${视[1].w} 两档实测 ${视[0].vs实测} / ${视[1].vs实测} → ${视[0].vs实测 === 视[1].vs实测 ? '✅ 与 w 无关（高项在管）' : '🔴 随 w 变'}` : '（视频不足两档，不判）',
    命中容差1e_3: `${命中.length}/${好.length}`,
    结论: 命中.length === 好.length
      ? `✅ **P1+P2+P3 全部成立**：vs 随 w 线性增长后在 w=1600 恰好被高度项 ${安全高}/${图[0]?.节点尺寸.Hc} 接住 ⇒ 「safeW = w − 532」「safeH = H − 160」两条都在 ${好.length} 臂上逐字成立`
      : `⚠️ **部分命中 ${命中.length}/${好.length}** ⇒ 只在命中的那些档上成立；未命中的档逐条看上面的表，**不外推**（立规 113）`,
  };
}
log('\n════ 判定 ════\n' + JSON.stringify(out.判定, null, 1));

const pz = await ctx.newPage();
try {
  await pz.setViewportSize({ width: 1280, height: 720 });
  await pz.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await pz.waitForSelector('.react-flow__node', { timeout: 45000 });
  await pz.waitForTimeout(6000);
  out.末态 = await pz.evaluate(() => ({
    节点数: document.querySelectorAll('.react-flow__node').length,
    状态行: (document.body.innerText.match(/\d+ nodes, \d+ edges, \d+ selected[^\n]*/) || [])[0] || null,
  }));
} finally { try { await pz.close(); } catch (e) { /* 忽略 */ } }
log(`\n末态独立复查：${JSON.stringify(out.末态)}`);

fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log(`写入 ${OUT}`);
process.exit(0);
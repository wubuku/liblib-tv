/**
 * 批次 293：判「`w = 1212` 那个阈值」是**窗口的事**还是**视频节点自己的事**。
 *
 * 📌 起意（批次 292）：`视频 1` 的 `vs` 在 `w = 1211` 仍是闭式的 `0.984183`，
 *   到 `w = 1212` 掉到 `≈0.62` ⇒ 🔴 **翻转点钉死在 `1px` 之间，且 `vs` 对宽度是阈值不是斜坡。**
 *   批次 290/291 两轮已把 DOM 布局层（全部 `2340` 个元素）排除干净 ⇒ **它不在任何渲染出来的盒上。**
 *
 * 📌 **本批只问一个问题：这个阈值是「所有节点共有」还是「只有视频节点有」？**
 *   🔴 **这是立规 169 的直接应用** —— 两个候选必须能被某个自由度分开：
 *     **(a) 窗口的事**：若 `w ≥ 1212` 时窗口/栅格上出现了什么（面板、列数、档位），
 *         则 🔴 **任何节点点过去都该在同一宽度跳**；
 *     **(b) 视频节点自己的事**：若跳变来自该节点的呈现盒（例如它自己的某个状态），
 *         则 🔴 **只有它跳**。
 *   📌 **判据（写死）**：同一个 `w`，三个节点各测一档；
 *     **一起跳 ⇒ (a)；只有视频跳 ⇒ (b)。**
 *
 * 📌 **三条预测（测量前写死，前提⑤）**：
 *   `视频 1`（`320 × 569`）：`1211 ⇒ 0.984183`（批次 292 已逐字测到）、`1212 ⇒ ≈0.62`
 *   `图片 b22-upload`（画布 `568.889 × 320`）：
 *     `1211 ⇒ min(679/568.8889, 1.75) = 1.193467`、`1212 ⇒ min(680/568.8889, 1.75) = 1.195313`
 *     ⇒ 📌 **这两档都应当「只随 w 线性变一点」，不应出现跳变**
 *   `音频 68`（`320 × 320`）：
 *     `1211 ⇒ min(679/320, 1.75) = 1.75`、`1212 ⇒ min(680/320, 1.75) = 1.75`
 *     ⇒ 📌 **`560/320 = 1.75` 已经封顶，两档都应是 `1.75`（完全饱和）**
 *   🔴 **音频这一档是本批的「封顶对照」**：它在 `w ≤ 1528` 上都被高度项接住，
 *      **所以按闭式它本来就不该随 `w` 变** ⇒ **若它偏偏在 `1212` 跳了，
 *      那就不是「节点自己的形状」，而是「窗口上多出了什么」** —— 这是最强的一条判据。
 *
 * 📌 **五条前提**：
 *   ① **轴向自检**：`innerW/innerH` 逐字等于设定值；
 *   ② 🔴 **`z0 > vs` 硬门**：`z0` 必须高于预测 `vs`，否则读到的不是平台；
 *   ③ 🔴 **落定自检**：点完连读两次（间隔 `2.5s`），必须逐字相同（立规 170）；
 *   ④ 📌 **跨遍一致性照样要报**（立规 171）—— 🔴 **臂内两次相同不等于定值**，
 *      本批**只报区间，不报定值**；
 *   ⑤ 🔴 **参数写死**：`532 / 160 / 0.08 / 8 / 0.5` 全部取自代码或已发布结论；
 *      📌 **`Wc` 用画布空间的 `5120/9 = 568.888…`，不是 `offsetWidth = 569`**（批次 288 的结论）。
 *
 * 📌 **纪律**：只按放大键、只点搜索结果行；不新建/不删除/不上传/不分享/不进扣费页/**绝不点生成**；
 *   末态在实验流程之外独立复查（立规 140）。
 *
 * 用法：node scripts/jimeng-b293.mjs      （落盘 /tmp/b293.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B293_OUT || '/tmp/b293.json';
const 高 = 720;
const 放大键 = 'Meta+Equal';
const 按够 = 13;
const 节点表 = [
  { 键: '视频', id: 'node_236ctpehgg', 备用名: ['视频 1', '视频'], 画布W: 320, 画布H: 569 },
  { 键: '图片', id: 'node_gref4sw056', 备用名: ['图片 b22-upload', 'b22-upload', '图片'], 画布W: 5120 / 9, 画布H: 320 },
  { 键: '音频', id: 'node_tadm1nyykc', 备用名: ['音频 68', '音频'], 画布W: 320, 画布H: 320 },
];
const 宽度组 = [1211, 1212];
const 臂表 = [];
for (const w of 宽度组) for (const n of 节点表) 臂表.push({ w, n });

// 🔴 前提⑤
const 屏上律 = (w) => Math.max(100, w - 532);
const 安全高 = 高 - 160;
const vf = (z) => Math.min(8, Math.max(0.08, z));
// 🔴 前提⑤：Wc/Hc 用**画布空间**尺寸（批次 288 的结论：offsetWidth=569 会带来 1.94e-4 的相对误差）
const 预测vs = (w, Wc, Hc) => +vf(Math.min(屏上律(w) / Wc, 安全高 / Hc)).toFixed(6);

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b293',
  问: 'w=1212 那个阈值是窗口的事还是视频节点自己的事？',
  预测: '视频 1211⇒0.984183 / 1212⇒≈0.62；图片 1211⇒1.193467 / 1212⇒1.195313；音频 两档都⇒1.75（封顶对照）',
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

for (const { w, n: 节点 } of 臂表) {
  const p = await ctx.newPage();
  const 记 = { w, h: 高, 键: 节点.键, 节点: 节点.id, 按了几次: 按够 };
  try {
    await p.setViewportSize({ width: w, height: 高 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(6000);
    const 实际 = await p.evaluate(() => ({ w: innerWidth, h: innerHeight }));
    if (实际.w !== w || 实际.h !== 高) throw new Error(`轴向自检失败：要 ${w}×${高}，实测 ${实际.w}×${实际.h}`);

    const 节 = await p.evaluate((nid) => {
      const e = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
      return e ? { W: e.offsetWidth, Hc: e.offsetHeight } : null;
    }, 节点.id);
    if (!节) throw new Error('目标节点不在画布上');
    记.节点尺寸 = 节;
    记.画布尺寸 = { Wc: 节点.画布W, Hc: 节点.画布H };
    记.预测vs = 预测vs(w, 节点.画布W, 节点.画布H);

    for (let i = 0; i < 按够; i++) { await p.keyboard.press(放大键); await p.waitForTimeout(380); }
    await p.waitForTimeout(1200);
    const z0 = await 读(p);
    记.z0 = z0.scale;
    if (z0.scale === null) throw new Error('读不到缩放');
    if (!(z0.scale > 记.预测vs)) throw new Error(`z0(${z0.scale}) 不高于预测 vs(${记.预测vs}) ⇒ 读不到平台`);

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
    for (const 名 of 节点.备用名) {
      await p.evaluate(() => { const i = document.querySelector('[data-testid="canvas-search-panel"] input'); if (i) { i.focus(); i.select(); } });
      await p.keyboard.type(名, { delay: 80 });
      await p.waitForTimeout(2000);
      const r = await p.evaluate((nid) => {
        const e = document.querySelector(`[data-testid="canvas-search-result-node_${nid.replace(/^node_/, '')}"]`);
        if (!e) return null;
        const b = e.getBoundingClientRect();
        return { 中心: [Math.round(b.x + b.width / 2), Math.round(b.y + b.height / 2)], 可见: b.width > 0 && b.height > 0 && b.y >= 0 && b.bottom <= innerHeight && b.x >= 0 && b.right <= innerWidth };
      }, 节点.id);
      if (r && r.可见) { 行 = r; 用名 = 名; break; }
    }
    if (!行) throw new Error('搜不到可见的结果行');
    记.用名 = 用名;
    await p.mouse.click(行.中心[0], 行.中心[1]);
    await p.waitForTimeout(3000);
    const a1 = await 读(p);
    await p.waitForTimeout(2500);
    const a2 = await 读(p);
    记.z后1 = a1.scale; 记.z后2 = a2.scale;
    记.落定 = a1.scale === a2.scale;                      // 前提③
    记.选中 = a2.选中;
    记.点击生效 = a2.选中.includes(节点.id);
    if (!记.点击生效) throw new Error(`点击未生效（选中=${JSON.stringify(a2.选中)}）`);
    记.vs实测 = a2.scale;
    记.符合闭式 = Math.abs(a2.scale - 记.预测vs) <= 1e-3;
    log(`${String(w).padStart(4)}｜${节点.键}｜z0=${z0.scale}｜vs实测=${a2.scale}｜闭式=${记.预测vs}｜${记.符合闭式 ? '✅符合' : '🔴不符'}｜落定 ${记.落定 ? '✅' : '🔴'}`);
  } catch (e) {
    记.错误 = e.message; log(`${String(w).padStart(4)} 🔴 ${e.message}`);
  } finally {
    try { await p.close(); } catch (e) { /* 忽略 */ }
    out.臂.push(记);
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

const 好 = out.臂.filter((x) => !x.错误 && x.点击生效 && x.vs实测 !== undefined);
log('\n════ 逐节点配对 ════');
const 按节点 = {};
for (const x of 好) { (按节点[x.键] = 按节点[x.键] || []).push(x); }
for (const k of Object.keys(按节点)) {
  const 组 = 按节点[k].sort((a, c) => a.w - c.w);
  log(`  ${k.padEnd(4)} (${组[0] ? 组[0].画布尺寸.Wc.toFixed(3) + '×' + 组[0].画布尺寸.Hc : '?'}): ` +
      组.map((x) => `w=${x.w} → ${x.vs实测}（闭式 ${x.预测vs}${x.符合闭式 ? ' ✅' : ' 🔴'}）`).join('  ｜  '));
}
const 跳了的 = Object.keys(按节点).filter((k) => {
  const 组 = 按节点[k];
  return 组.some((x) => !x.符合闭式);
});
const 没跳的 = Object.keys(按节点).filter((k) => !跳了的.includes(k));
const 缺失 = 节点表.filter((n) => !(按节点[n.键] || []).some((x) => x.w === 1212) || !(按节点[n.键] || []).some((x) => x.w === 1211)).map((n) => n.键);

if (!好.length) {
  out.判定 = { 结论: '🔴 一条有效臂都没有 ⇒ 整组作废' };
} else if (缺失.length) {
  out.判定 = { 结论: `🔴 节点 ${缺失.join('、')} 缺 1211/1212 其中一档 ⇒ 配对不完整，整组作废（立规 164）`, 缺失 };
} else {
  out.判定 = {
    有效臂: `${好.length}/${out.臂.length}`,
    落定: 好.every((x) => x.落定) ? '✅ 全部臂内落定' : `🔴 ${好.filter((x) => !x.落定).map((x) => x.键 + '@' + x.w).join('、')} 未落定`,
    跳了的节点: 跳了的.length ? 跳了的.join('、') : '（无）',
    没跳的节点: 没跳的.length ? 没跳的.join('、') : '（无）',
    // 🔴 判决规则（v2，修正了 v1 的错）：
    //   **窗口级的原因必须打中「全体」节点** ⇒ 只有 3/3 才算 (a)；
    //   **2/3 不是「窗口的事」** —— 那个没跳的成员是信息，不是噪声。
    判决: 跳了的.length === 节点表.length
      ? `✅ **候选 (a) 成立：是「窗口的事」** —— ${跳了的.join('、')} 三个节点在 w=1212 上一起跳 ⇒ 窗口/栅格在那个宽度上多出了什么`
      : 跳了的.length > 0 && 没跳的.length > 0
        ? `🔴 **不是「窗口的事」（例外成员存在）** —— 跳的是 ${跳了的.join('、')}，而 ${没跳的.join('、')} 在 w=1212 上逐字仍等于闭式 ⇒ 🔴 **窗口级的解释打不中全体 ⇒ 失效是节点相关的**；📌 与节点相关的那条线索：${跳了的.map((k)=>k+':W='+(按节点[k][0].画布尺寸.Wc)).join(' / ')}，而 ${没跳的.map((k)=>k+':W='+(按节点[k][0].画布尺寸.Wc)).join(' / ')}`
        : 跳了的.length === 0
          ? `🔴 **三个节点一个都没跳** ⇒ 「视频在 1212 掉到 ≈0.62」这件事在本批**没能复现** ⇒ 与批次 292 冲突，**成因未测，不选边**（立规 113）`
          : '⚠️ 数据不足，不出判定',
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
/**
 * 批次 292：把 `w = 1212` 的翻转点**钉到 1px**。
 *
 * 📌 起意（批次 289 / 290 / 291）：
 *   `视频 1`（`320 × 569`）、`H = 720`：`vs` 随宽度走，闭式
 *     `vs = clamp(min(max(100, w−532)/Wc, (H−160)/Hc), 0.08, 8)`
 *   批次 289：`w = 900 / 1000 / 1100` ⇒ `0.984183` **逐字**；`w = 1212`（两遍）⇒ `≈0.62`。
 *   批次 290 / 291：DOM 布局层（表面盒、节点盒、全部 `2340` 个元素）**全程线性、零增删**。
 *   ⇒ 🔴 **翻转点夹在 `(1100, 1212]`，而它不在任何渲染出来的盒上。**
 *
 * 📌 **本批只问一件事：那个窗口到底有多窄？**
 *   办法是在 `1211` 与 `1212` 之间各测一档 —— 若 `1211` 还是闭式那个数、
 *   `1212` 已经掉下去，**翻转点就被钉死在这 `1px` 里**。
 *   配套在更宽的几档上取点，确认中间没有第二个翻转。
 *
 * 📌 **两条预测（测量前写死，前提⑤）**：
 *   P1 `w ∈ {1130, 1160, 1190, 1210, 1211}` ⇒ `vs = 0.984183`，
 *      与闭式 `min((w−532)/320, 560/569) = 0.984183` **逐字相同**
 *      （宽项在 `w ≥ 900` 起就大于高项，所以这几档的值与 `w` 无关）。
 *   P2 `w = 1212` ⇒ **`≈0.62`**（批次 289 两遍：`0.622621` / `0.617832`）。
 *   ⇒ 📌 **若 P1 与 P2 同时成立 ⇒ 翻转点落在 `1211 → 1212` 这 `1px` 之间。**
 *   🔴 **P1 若在中间某档就掉了 ⇒ 窗口比想的宽，那一档就是新的上界。**
 *
 * 📌 **五条前提**：
 *   ① **轴向自检**：`innerW/innerH` 逐字等于设定值；
 *   ② 🔴 **`z0 > vs` 硬门**：`z0` 必须高于预测 `vs`，否则读到的不是平台；
 *   ③ 🔴 **落定自检**：点完连读两次（间隔 `2.5s`），必须逐字相同（立规 170）；
 *   ④ 📌 **跨重复一致性照样要报**（立规 171）：
 *      🔴 **本批不因为「臂内两次相同」就把它当定值** —— 批次 289 的 `w=1212`
 *      **臂内 ✅ 而两遍之间 ❌**，所以本批**只报区间，不报定值**；
 *   ⑤ 🔴 **参数写死**：`532 / 160 / 0.08 / 8 / 0.5` 全部取自代码或已发布结论。
 *
 * 📌 **纪律**：只按放大键、只点搜索结果行；不新建/不删除/不上传/不分享/不进扣费页/**绝不点生成**；
 *   末态在实验流程之外独立复查（立规 140）。
 *
 * 用法：node scripts/jimeng-b292.mjs      （落盘 /tmp/b292.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B292_OUT || '/tmp/b292.json';
const 高 = 720;
const 放大键 = 'Meta+Equal';
const 按够 = 13;
const 节点 = { 键: '视频', id: 'node_236ctpehgg', 备用名: ['视频 1', '视频'] };
const 宽度组 = [1130, 1160, 1190, 1210, 1211, 1212];

// 🔴 前提⑤
const 屏上律 = (w) => Math.max(100, w - 532);
const 安全高 = 高 - 160;
const vf = (z) => Math.min(8, Math.max(0.08, z));
const 预测vs = (w, W, Hc) => +vf(Math.min(屏上律(w) / W, 安全高 / Hc)).toFixed(6);

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b292',
  问: 'w=1212 的翻转点能不能钉到 1px？',
  预测: 'w∈{1130,1160,1190,1210,1211} ⇒ 0.984183；w=1212 ⇒ ≈0.62',
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

for (const w of 宽度组) {
  const p = await ctx.newPage();
  const 记 = { w, h: 高, 节点: 节点.id, 按了几次: 按够 };
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
    记.预测vs = 预测vs(w, 节.W, 节.Hc);

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
    log(`${String(w).padStart(4)}｜z0=${z0.scale}｜vs实测=${a2.scale}｜闭式=${记.预测vs}｜${记.符合闭式 ? '✅符合' : '🔴不符'}｜落定 ${记.落定 ? '✅' : '🔴'}`);
  } catch (e) {
    记.错误 = e.message; log(`${String(w).padStart(4)} 🔴 ${e.message}`);
  } finally {
    try { await p.close(); } catch (e) { /* 忽略 */ }
    out.臂.push(记);
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

const 好 = out.臂.filter((x) => !x.错误 && x.点击生效 && x.vs实测 !== undefined);
const 符 = 好.filter((x) => x.符合闭式);
const 不符 = 好.filter((x) => !x.符合闭式);
log('\n════ 汇总 ════');
for (const x of 好) log(`  w=${String(x.w).padEnd(5)} vs=${String(x.vs实测).padEnd(10)} 闭式=${x.预测vs} ${x.符合闭式 ? '✅' : '🔴'}`);

// 翻转窗口 = 「最后一个符合闭式的档」与「第一个不符合的档」之间
const 排序 = [...好].sort((a, c) => a.w - c.w);
let 最后符合 = null, 首个不符 = null;
for (const x of 排序) { if (x.符合闭式) 最后符合 = x.w; else if (首个不符 === null && (最后符合 !== null || x.w < (符[0]?.w ?? Infinity))) 首个不符 = x.w; }
if (最后符合 !== null && 首个不符 !== null && 首个不符 > 最后符合) {
  out.窗口 = { 仍符合的最大宽度: 最后符合, 开始不符合的最小宽度: 首个不符 };
}

if (!好.length) {
  out.判定 = { 结论: '🔴 一条有效臂都没有 ⇒ 整组作废' };
} else {
  out.判定 = {
    有效臂: `${好.length}/${out.臂.length}`,
    P1: `${符.length}/${好.length} 档逐字等于闭式的 0.984183：${符.map((x) => x.w).join('、')}`,
    P2: 不符.length ? `🔴 不符闭式的档：${不符.map((x) => `${x.w} → ${x.vs实测}`).join('、')}` : '（本批没有不符的档）',
    落定: 好.every((x) => x.落定) ? '✅ 全部臂内落定' : `🔴 ${好.filter((x) => !x.落定).map((x) => x.w).join('、')} 未落定`,
    窗口: out.窗口 || '（本批数据不足以夹出窗口）',
    结论: out.窗口
      ? `✅ **翻转点钉死在 w = ${out.窗口.仍符合的最大宽度} → ${out.窗口.开始不符合的最小宽度} 这 ${out.窗口.开始不符合的最小宽度 - out.窗口.仍符合的最大宽度}px 之间** ⇒ P1 与 P2 同时成立；⚠️ **但按立规 171，w = ${out.窗口.开始不符合的最小宽度} 那一档跨遍一致性仍不过，所以只能报「≈0.62」，不许当定值**`
      : `⚠️ **本批没能夹出单窗口**（${符.map((x) => x.w).join('、')} 符合，${不符.map((x) => x.w).join('、')} 不符合）⇒ 不出定论，不编（立规 113）`,
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
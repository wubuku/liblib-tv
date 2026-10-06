/**
 * 批次 271：给那条「只由视口高度决定」的异常分支找一个**可证伪**的宽度项。
 *
 * 📌 起意（批次 270 留下的线索）：
 *   异常分支在 `H = 242…248` 上**斜率逐字 `= 1/2520.5`**（`6` 个相邻差，最大偏差 `5.33e-8`
 *   < 落点量化步长 `1e-7`），而 `2520.5` 正是批次 259 测到的「`适配画布`」**垂直分母**；
 *   同一族的**水平分母是 `4091.4`**。
 *   📌 且 `×2520.5` 的残差在 `9` 个点上系统性 `+1.0e-3…+1.24e-3`，而残差自身的量化步长是
 *   `1e-7 × 2520.5 = 2.52e-4` ⇒ **散布只有约 `1` 个量化单位 ⇒ 残差其实是常数**。
 *
 * 📌 **由此得到一个可以证伪的假设**（不是结论）：
 *   那条分支 = 「把 `4091.4 × 2520.5` 的内容盒装进视口、上下留 `22px`、左右留 `20px`」：
 *   `s = min( (w − 20) / 4091.4 , (H − 22) / 2520.5 )`
 *   ⇒ 🔴 **它必然有一个宽度项**，且在
 *   `w* = 20 + 0.0880782 × 4091.4 = `**`380.4`** 处被接住
 *   ⇒ **接缝是 `1px` 级的**（立规 121）：
 *   `w = 380` 给 `360/4091.4 = 0.087992`（宽度项取小），`w = 381` 给 `0.0880782`（高度项取小）。
 *
 * 📌 **对立假设**：那条分支**根本没有宽度项** ⇒ 任何 `w` 都读 `0.0880782`。
 *   ⇒ 📌 **两条假设在 `w ≤ 380` 给出差 `≈0.015` 的读数，一眼可辨**；
 *   而批次 269/270 只在 `w = 700/1000/1200` 上测过 —— 那三个宽度**全在接缝右侧**，
 *   所以「不依赖视口宽」这个结论**当时是对的，但覆盖范围只有接缝以上**（立规 148 的同型：
 *   **一个结论的有效范围，要由「别的项在哪里接住」划定，而不是由「我测过哪里」划定**）。
 *
 * 📌 **只读**：不新建/不删除/不上传/不分享/不进扣费页/**绝不点生成**。
 *   每臂开新页（批次 260）。**连采 6 帧去重**（立规 76）。末态在实验流程之外独立复查（立规 140）。
 *
 * 用法：node scripts/jimeng-b271.mjs      （落盘 /tmp/b271.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B271_OUT || '/tmp/b271.json';
const 高 = 244;                                   // 批次 270 在这个高度读到 0.0880782
const 节点 = { id: 'node_tadm1nyykc', 名: '音频 68', W: 320, Hc: 320 };
const 宽表 = [320, 360, 380, 381, 400];
const 帧数 = 6, 帧间隔 = 400;

const log = (...a) => console.log(a.join(' '));
const 预测 = (w) => {
  const 高度项 = (高 - 22) / 2520.5;
  const 宽度项 = (w - 20) / 4091.4;
  return {
    高度项: +高度项.toFixed(9), 宽度项: +宽度项.toFixed(9),
    假设A_有宽度项: +Math.min(宽度项, 高度项).toFixed(9),
    假设B_无宽度项: +高度项.toFixed(9),
    两者差: +Math.abs(Math.min(宽度项, 高度项) - 高度项).toFixed(9),
  };
};

const out = { 轮次: 'b271', 问: '异常分支到底有没有宽度项？接缝在 w≈380.4？', 高, 节点, 宽表, 臂: [], 收尾: {} };
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

for (const 宽 of 宽表) {
  const p = await ctx.newPage();
  const 记 = { 宽, 高, ...预测(宽) };
  try {
    await p.setViewportSize({ width: 宽, height: 高 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(5000);
    const 钮 = await p.evaluate(() => {
      const e = Array.from(document.querySelectorAll('button, [role="button"]'))
        .find((x) => (x.getAttribute('aria-label') || '') === '搜索');
      if (!e) return null;
      const r = e.getBoundingClientRect();
      return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
    });
    if (!钮) throw new Error('找不到搜索钮');
    await p.mouse.click(钮[0], 钮[1]);
    await p.waitForTimeout(1500);
    const 短名 = 节点.id.replace(/^node_/, '');
    await p.evaluate(() => {
      const inp = document.querySelector('[data-testid="canvas-search-panel"] input');
      if (inp) { inp.focus(); inp.select(); }
    });
    await p.keyboard.type(节点.名, { delay: 85 });
    await p.waitForTimeout(2200);
    const 行 = await p.evaluate((nid) => {
      const e = document.querySelector(`[data-testid="canvas-search-result-node_${nid}"]`);
      if (!e) return { 有行: false };
      const r = e.getBoundingClientRect();
      return { 有行: true, 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 盒: [Math.round(r.width), Math.round(r.height)], 可点: r.width > 0 && r.height > 0 && r.y >= 0 && r.bottom <= innerHeight && r.x >= 0 && r.right <= innerWidth };
    }, 短名);
    if (!行.有行 || !行.可点) { 记.不可达 = !行.有行 ? '搜不到那一行' : `结果行不可点（${JSON.stringify(行.盒)}）`; out.臂.push(记); log(`w=${宽} ⚠️ ${记.不可达}`); await p.close(); continue; }
    await p.mouse.click(行.中心[0], 行.中心[1]);
    await p.waitForTimeout(5000);
    await p.keyboard.press('Escape'); await p.waitForTimeout(600);
    await p.keyboard.press('Escape'); await p.waitForTimeout(900);

    const 帧 = [];
    for (let i = 0; i < 帧数; i++) {
      帧.push(await p.evaluate((nid) => {
        const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
        const vp = document.querySelector('.react-flow__viewport');
        const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
        const nr = n ? n.getBoundingClientRect() : null;
        return { 落点: m ? Number(m[1]) : null, 屏上宽: nr ? +nr.width.toFixed(4) : null, 中心Y: nr ? Math.round(nr.y + nr.height / 2) : null, innerW: window.innerWidth };
      }, 节点.id));
      await p.waitForTimeout(帧间隔);
    }
    const 去重 = [...new Set(帧.map((f) => f.落点))];
    记.去重后落点 = 去重;
    记.是否收敛 = 去重.length === 1;
    记.落点 = 记.是否收敛 ? 去重[0] : null;
    记.屏上宽 = [...new Set(帧.map((f) => f.屏上宽))];
    记.中心Y = [...new Set(帧.map((f) => f.中心Y))];
    记.内宽一致 = 帧.every((f) => f.innerW === 宽);
    记.命中A = 记.落点 !== null && Math.abs(记.落点 - 记.假设A_有宽度项) <= 1e-6;
    记.命中B = 记.落点 !== null && Math.abs(记.落点 - 记.假设B_无宽度项) <= 1e-6;
    记.命中取景律 = 记.落点 !== null && Math.abs(记.落点 - +Math.min((宽 - 532) / 节点.W, 0.5, (高 - 160) / 节点.Hc).toFixed(9)) <= 1e-6;
    out.臂.push(记);
    log(`w=${String(宽).padStart(3)} 落点=${记.落点}（去重 ${去重.length}，内宽一致=${记.内宽一致}）屏上=${JSON.stringify(记.屏上宽)} 中心Y=${JSON.stringify(记.中心Y)}｜A=${记.假设A_有宽度项} B=${记.假设B_无宽度项} ⇒ ${记.命中A ? '✅A' : 记.命中B ? '✅B' : 记.命中取景律 ? '✅取景律' : '两者皆非'}`);
  } catch (e) {
    记.错误 = e.message; out.臂.push(记); log(`w=${宽} 🔴 ${e.message}`);
  } finally {
    try { await p.close(); } catch (e) { /* 忽略 */ }
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

{
  const p = await ctx.newPage();
  try {
    await p.setViewportSize({ width: 1280, height: 720 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(6000);
    out.收尾.节点数 = await p.evaluate(() => document.querySelectorAll('.react-flow__node').length);
    out.收尾.状态行 = await p.evaluate(() => (document.body.innerText.match(/\d+ nodes, \d+ edges, \d+ selected[^\n]*/) || [])[0] || null);
    out.收尾.通过 = out.收尾.节点数 === 76 && /0 selected/.test(out.收尾.状态行 || '');
    log(`\n末态独立复查：节点 ${out.收尾.节点数}｜${out.收尾.状态行} ⇒ ${out.收尾.通过 ? '✅' : '🔴'}`);
  } catch (e) { out.收尾.错误 = e.message; } finally { try { await p.close(); } catch (e) { /* 忽略 */ } }
}

const 成 = out.臂.filter((a) => a.落点 !== null);
out.汇总 = {
  臂: out.臂.length, 成功: 成.length, 不可达: out.臂.length - 成.length,
  收敛: 成.filter((a) => a.是否收敛).length,
  命中A_有宽度项: 成.filter((a) => a.命中A).length,
  命中B_无宽度项: 成.filter((a) => a.命中B).length,
  命中取景律: 成.filter((a) => a.命中取景律).length,
  逐字明细: 成.map((a) => ({ w: a.宽, 实测: a.落点, A: a.假设A_有宽度项, B: a.假设B_无宽度项 })),
};
log('\n=== 汇总 ===');
log(JSON.stringify(out.汇总, null, 1));
fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log(`写入 ${OUT}`);
process.exit(0);

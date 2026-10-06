/**
 * 批次 266c：把 **`0.5` 那个盖子**在 `W = 1200` 上单独验一遍，并把它的接缝钉到 `1px`。
 *
 * 📌 为什么必须补这一环（立规 138：同一句话两个方向要分别闭合）：
 *   266b 测出时间线（`W=1200`）在 `w=1000` 恒读 `0.39`（屏上 `468 = 1000−532`），
 *   而 `0.5 × 1200 = 600 > 468` ⇒ 🔴 **`0.5` 那个盖子在 `W=1200` 上一次都没生效过**。
 *   ⇒ 「封顶是 `0.5`（与 `W` 无关的比例）」这句话，目前**只有 `W=320` 支撑**。
 *
 * 📌 预测先算好（`H=720`，高度律不生效，`(720−160)/Hc ≫`）：
 *   `屏上 = min(w − 532, 0.5×W)`，接缝在 `w = 532 + 0.5W = 532 + 600 = `**`1132`**。
 *   🔴 接缝**不是整数也不是粗估**，必须用 `1px` 步长去撞（立规 121）：
 *   `1130 → 598/1200 = 0.498333`、`1131 → 599/1200 = 0.499167`、
 *   `1132 → 600/1200 = `**`0.5`**、`1133 → 601/1200 = 0.500833`（**封顶后应恒 `0.5`**）。
 *
 * 📌 只读：不新建/不删除/不上传/不分享/不进扣费页/**绝不点生成**。
 *   每臂开新页（批次 260）。多帧去重（立规 76）。末态在实验流程之外独立复查（立规 140）。
 *
 * 用法：node scripts/jimeng-b266c.mjs      （落盘 /tmp/b266c.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B266C_OUT || '/tmp/b266c.json';
const 高 = 720;
const 宽表 = [1130, 1131, 1132, 1133, 1200];
const 节点 = { id: 'node_d4tjtpnatq', 名: '时间线 2', W: 1200, Hc: 207 };
const 帧数 = 6, 帧间隔 = 400;

const log = (...a) => console.log(a.join(' '));
const 预测 = (w) => {
  const 屏上 = Math.min(w - 532, 0.5 * 节点.W, (高 - 160) * 节点.W / 节点.Hc);
  return { 预测屏上: +屏上.toFixed(6), 预测落点: +(屏上 / 节点.W).toFixed(9), 预测封顶: w - 532 >= 0.5 * 节点.W };
};

const out = { 轮次: 'b266c', 高, 宽表, 节点, 臂: [], 收尾: {} };
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
      return { 有行: true, 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 可点: r.width > 0 && r.height > 0 && r.y >= 0 && r.bottom <= innerHeight && r.x >= 0 && r.right <= innerWidth };
    }, 短名);
    if (!行.有行 || !行.可点) { 记.不可达 = !行.有行 ? '搜不到那一行' : '结果行不可点'; out.臂.push(记); log(`w=${宽} ⚠️ ${记.不可达}`); await p.close(); continue; }
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
        return { 落点: m ? Number(m[1]) : null, 屏上宽: nr ? +nr.width.toFixed(4) : null, 中心Y: nr ? Math.round(nr.y + nr.height / 2) : null };
      }, 节点.id));
      await p.waitForTimeout(帧间隔);
    }
    记.六帧 = 帧;
    const 去重 = [...new Set(帧.map((f) => f.落点))];
    记.去重后落点 = 去重;
    记.是否收敛 = 去重.length === 1;
    记.落点 = 记.是否收敛 ? 去重[0] : null;
    记.屏上宽 = [...new Set(帧.map((f) => f.屏上宽))];
    记.中心Y = [...new Set(帧.map((f) => f.中心Y))];
    记.命中 = 记.落点 !== null && Math.abs(记.落点 - 记.预测落点) <= 1e-6;
    记.误差 = 记.落点 !== null ? +(记.落点 - 记.预测落点).toExponential(2) : null;
    out.臂.push(记);
    log(`w=${String(宽).padStart(4)} 落点=${记.落点}（去重 ${去重.length}）屏上=${JSON.stringify(记.屏上宽)} 中心Y=${JSON.stringify(记.中心Y)}｜预测 ${记.预测落点} ⇒ ${记.命中 ? '✅ 逐字命中' : '❌ 偏差 ' + 记.误差}`);
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
  臂: out.臂.length, 成功: 成.length, 收敛: 成.filter((a) => a.是否收敛).length,
  命中: 成.filter((a) => a.命中).length,
  封顶档读到0_5: 成.filter((a) => Math.abs(a.落点 - 0.5) <= 1e-9).length,
  逐字明细: 成.map((a) => ({ w: a.宽, 实测: a.落点, 预测: a.预测落点, 命中: a.命中 })),
};
log('\n=== 汇总 ===');
log(JSON.stringify(out.汇总, null, 1));
fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log(`写入 ${OUT}`);
process.exit(0);

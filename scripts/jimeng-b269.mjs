/**
 * 批次 269：钉死 `H = 240` 那条**与 `W` 无关**的 `0.0872847` 到底在哪儿换的机制。
 *
 * 📌 起意（批次 266 登记的未解释异常）：
 *   `H=240` 时 `音频 68`（`W=320 Hc=320`）与 `时间线 2`（`W=1200 Hc=207`）
 *   **读到同一个落点 `0.0872847`** ⇒ 与节点无关；且两条中心 `Y`（`61`/`86`）**都不等于 `H/2`**。
 *   批次 268 又把取景律的第三项钉成 `(H−160)/Hc`，`H ≥ 260` 全部逐字。
 *   ⇒ 🔴 **`H ≤ 259` 这一段至今只有 `H=240` 一个读数，而它明显不是同一条律。**
 *
 * 📌 **一条算术线索**（先写下、再验，不当结论）：
 *   批次 259 测到 `适配画布 = min( (w−200)/4091.4 , (H−160)/2520.5 )`，
 *   而 📌 **`0.0872847 × 2520.5 = 219.998 ≈ 220`**，
 *   📌 **`0.0872847 × 4091.4 = 357.1`**（不整）。
 *   ⇒ 提示：那个数**像是「某个盒子高度 ÷ 2520.5」**，即**可能掉进了 `适配画布`（适配整张画布）那条分支** ——
 *   而 `适配画布` **本来就不依赖被选中的那个节点** ⇒ 正好解释「与 `W` 无关」。
 *   ⚠️ 但 `H=240` 代进 `适配画布` 原式给 `(240−160)/2520.5 = 0.0317`，**不是** `0.0873`
 *   ⇒ 分子是 `220 = H − 20` 而不是 `H − 160` ⇒ **公式不一样**，只能算线索。
 *
 * 📌 **本批两问，各有唯一预测**：
 *   ① **切换点在哪儿？** 用 `1px` 步长从 `H=259` 一路扫到 `H=240`（立规 121）
 *      ⇒ 若存在高度 `H*`，`H ≥ H*` 逐字读 `(H−160)/320`，`H < H*` 读**另一个值**。
 *   ② **那个值依赖视口宽吗？** 在 `H=240` 上把 `w` 从 `1000` 改成 `700` 与 `1200`
 *      ⇒ 若**逐字不变**，则它**既不依赖节点、也不依赖视口宽**（只跟 `H` 有关或干脆是常数）。
 *
 * 📌 **可达性先记在前面**（立规 142）：批次 266 已测出 `H ≤ 230` 时搜索结果行落到视口外
 *   或搜不到 ⇒ **可测的异常段只有 `H = 231…240`**，本批就在这个窗口里做。
 *
 * 📌 **只读**：不新建/不删除/不上传/不分享/不进扣费页/**绝不点生成**。
 *   每臂开新页（批次 260）。**连采 6 帧去重**（立规 76）。末态在实验流程之外独立复查（立规 140）。
 *
 * 用法：node scripts/jimeng-b269.mjs      （落盘 /tmp/b269.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B269_OUT || '/tmp/b269.json';
const 节点 = { id: 'node_tadm1nyykc', 名: '音频 68', W: 320, Hc: 320 };
// ① 高度扫描：从上往下 1px/2px 步长，直到越界
const 高度臂 = [[1000, 259], [1000, 257], [1000, 255], [1000, 253], [1000, 251],
[1000, 249], [1000, 247], [1000, 245], [1000, 243], [1000, 241], [1000, 240]];
// ② 宽度依赖：固定 H=240，换视口宽
const 宽度臂 = [[700, 240], [1200, 240]];
const 异常值 = 0.0872847;      // 批次 266/268 观测到的那个数
const 帧数 = 6, 帧间隔 = 400;

const log = (...a) => console.log(a.join(' '));
// 📌 预测先算好并落盘
const 预测 = (w, h) => ({
  预测落点_取景律: +Math.min((w - 532) / 节点.W, 0.5, (h - 160) / 节点.Hc).toFixed(9),
  预测落点_适配画布原式: +Math.min((w - 200) / 4091.4, (h - 160) / 2520.5).toFixed(9),
  预测_异常值除2520_5反推分子: +(异常值 * 2520.5).toFixed(3),
});

const out = { 轮次: 'b269', 问: 'H=240 的 0.0872847 在哪儿换机制？它依赖视口宽吗？', 节点, 异常值, 高度臂, 宽度臂, 臂: [], 收尾: {} };
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

for (const [宽, 高] of [...高度臂, ...宽度臂]) {
  const p = await ctx.newPage();
  const 记 = { 宽, 高, 组: 高度臂.some(([w, h]) => w === 宽 && h === 高) ? '高度扫描' : '宽度依赖', ...预测(宽, 高) };
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
    if (!行.有行 || !行.可点) { 记.不可达 = !行.有行 ? '搜不到那一行' : '结果行不可点'; out.臂.push(记); log(`${宽}×${高} ⚠️ ${记.不可达}`); await p.close(); continue; }
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
        return {
          落点: m ? Number(m[1]) : null,
          屏上宽: nr ? +nr.width.toFixed(4) : null,
          中心Y: nr ? Math.round(nr.y + nr.height / 2) : null,
          视口translate: vp ? (vp.style.transform || '') : null,
        };
      }, 节点.id));
      await p.waitForTimeout(帧间隔);
    }
    const 去重 = [...new Set(帧.map((f) => f.落点))];
    记.去重后落点 = 去重;
    记.是否收敛 = 去重.length === 1;
    记.落点 = 记.是否收敛 ? 去重[0] : null;
    记.屏上宽 = [...new Set(帧.map((f) => f.屏上宽))];
    记.中心Y = [...new Set(帧.map((f) => f.中心Y))];
    记.视口translate = 帧[0].视口translate;
    记.等于异常值 = 记.落点 !== null && Math.abs(记.落点 - 异常值) <= 5e-8;
    记.命中取景律 = 记.落点 !== null && Math.abs(记.落点 - 记.预测落点_取景律) <= 1e-6;
    记.中心Y是H一半 = 记.中心Y.length === 1 && 记.中心Y[0] === 高 / 2;
    out.臂.push(记);
    log(`${宽}×${高} [${记.组}] 落点=${记.落点}（去重 ${去重.length}）中心Y=${JSON.stringify(记.中心Y)}（H/2=${高 / 2}）｜取景律 ${记.预测落点_取景律} 适配原式 ${记.预测落点_适配画布原式} ⇒ ${记.等于异常值 ? '🔴 异常值' : 记.命中取景律 ? '✅ 取景律' : '两者皆非'}`);
  } catch (e) {
    记.错误 = e.message; out.臂.push(记); log(`${宽}×${高} 🔴 ${e.message}`);
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
const 异常臂 = 成.filter((a) => a.等于异常值);
const 取景臂 = 成.filter((a) => a.命中取景律);
out.汇总 = {
  臂: out.臂.length, 成功: 成.length, 不可达: out.臂.length - 成.length,
  收敛: 成.filter((a) => a.是否收敛).length,
  读异常值: 异常臂.length, 读取景律: 取景臂.length, 两者皆非: 成.length - 异常臂.length - 取景臂.length,
  异常值逐字恒定: new Set(异常臂.map((a) => a.落点)).size <= 1,
  异常值依赖视口宽: 异常臂.length >= 2 && new Set(异常臂.map((a) => a.落点)).size > 1,
  异常段最高H: 异常臂.length ? Math.max(...异常臂.map((a) => a.高)) : null,
  取景段最低H: 取景臂.length ? Math.min(...取景臂.map((a) => a.高)) : null,
  中心Y是H一半的臂: 成.filter((a) => a.中心Y是H一半).length,
};
log('\n=== 汇总 ===');
log(JSON.stringify(out.汇总, null, 1));
fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log(`写入 ${OUT}`);
process.exit(0);

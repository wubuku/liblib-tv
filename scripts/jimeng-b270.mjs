/**
 * 批次 270：把 `H=248` 那几个点补上 —— 批次 269 的「切换点在 `(247,249]`」是**站在一个采样漏洞上**的。
 *
 * 🔴 **起意（本批先认自己的错）**：
 *   批次 269 的高度臂是 `[259, 257, 255, 253, 251, 249, 247, 245, 243, 241]` ＋ 一个 `240`
 *   —— 步长 `2` 且**起点 `259` 是奇数** ⇒ **`259…241` 全是奇数，偶数只测了 `240` 这一个**。
 *   而它给出的结论是「切换点落在 `H ∈ (247, 249]`」⇒ 🔴 **那个区间里一个点都没测过。**
 *   📌 这正是立规 121 的原样复发（「两端都这样」不等于「中间也这样」），
 *   而本批更糟：**中间连一个采样都没有**，却被写成了「定位到区间」。
 *
 * 📌 **本批就是把那 `5` 个偶数补齐**：`250 / 248 / 246 / 244 / 242`
 *   ⇒ 加上已有读数，`H = 250…240` 变成 **`1px` 粒度的连续序列**（`11` 个点），
 *   届时「奇偶」「切换高度」「台阶在哪」三件事**同时**能被读数回答。
 *
 * 📌 **预测先算好并落盘**（`w=1000`，`音频 68` `W=320 Hc=320`）：
 *   取景律 `s = min(468/320, 0.5, (H−160)/320)`
 *   | `H` | 取景律预测 | 批次 269 实测 |
 *   |---|---|---|
 *   | `250` | `0.28125` | — |
 *   | `248` | `0.275` | — |
 *   | `246` | `0.26875` | — |
 *   | `244` | `0.2625` | — |
 *   | `242` | `0.25625` | — |
 *   🔴 **本批不预设这些偶数读什么** —— 上一批正是因为「没测就下了区间结论」才要返工。
 *
 * 📌 顺带一臂**换族复核**：批次 266 只在 `H=240` 一个点上验过「新分支与节点无关」，
 *   本批在 `H=244` 上用 `图片 b22-upload`（`W=568.889, Hc=320`）再验一次
 *   ⇒ 若逐字相同，则「与节点无关」从**单点**升级为**两点**。
 *
 * 📌 **只读**：不新建/不删除/不上传/不分享/不进扣费页/**绝不点生成**。
 *   每臂开新页（批次 260）。**连采 6 帧去重**（立规 76）。末态在实验流程之外独立复查（立规 140）。
 *
 * 用法：node scripts/jimeng-b270.mjs      （落盘 /tmp/b270.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B270_OUT || '/tmp/b270.json';
const 宽 = 1000;
const 节点表 = {
  音频: { id: 'node_tadm1nyykc', 名: '音频 68', W: 320, Hc: 320 },
  图片: { id: 'node_gref4sw056', 名: '图片 b22-upload', W: 5120 / 9, Hc: 320 },
};
// 补齐偶数：250 248 246 244 242；外加换族复核 244
const 臂表 = [
  ['音频', 250], ['音频', 248], ['音频', 246], ['音频', 244], ['音频', 242],
  ['图片', 244],
];
const 帧数 = 6, 帧间隔 = 400;

const log = (...a) => console.log(a.join(' '));
const 预测 = (h, W, Hc) => ({ 预测落点_取景律: +Math.min((宽 - 532) / W, 0.5, (h - 160) / Hc).toFixed(9) });

const out = { 轮次: 'b270', 问: '补齐偶数高度：切换点到底在哪？', 宽, 臂表, 臂: [], 收尾: {} };
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

for (const [键, 高] of 臂表) {
  const 节点 = 节点表[键];
  const p = await ctx.newPage();
  const 记 = { 族: 键, 高, 宽, ...预测(高, 节点.W, 节点.Hc) };
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
    if (!行.有行 || !行.可点) { 记.不可达 = !行.有行 ? '搜不到那一行' : '结果行不可点'; out.臂.push(记); log(`${键} H=${高} ⚠️ ${记.不可达}`); await p.close(); continue; }
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
    const 去重 = [...new Set(帧.map((f) => f.落点))];
    记.去重后落点 = 去重;
    记.是否收敛 = 去重.length === 1;
    记.落点 = 记.是否收敛 ? 去重[0] : null;
    记.屏上宽 = [...new Set(帧.map((f) => f.屏上宽))];
    记.中心Y = [...new Set(帧.map((f) => f.中心Y))];
    记.命中取景律 = 记.落点 !== null && Math.abs(记.落点 - 记.预测落点_取景律) <= 1e-6;
    记.是奇数高度 = 高 % 2 === 1;
    out.臂.push(记);
    log(`${键} H=${String(高).padStart(3)}${高 % 2 ? '(奇)' : '(偶)'} 落点=${记.落点}（去重 ${去重.length}）屏上=${JSON.stringify(记.屏上宽)} 中心Y=${JSON.stringify(记.中心Y)}｜取景律 ${记.预测落点_取景律} ⇒ ${记.命中取景律 ? '✅ 取景律' : '🔴 非取景律'}`);
  } catch (e) {
    记.错误 = e.message; out.臂.push(记); log(`${键} H=${高} 🔴 ${e.message}`);
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

// ============ 与批次 269 合并成 1px 连续序列 ============
const b269 = JSON.parse(fs.existsSync('/tmp/b269.json') ? fs.readFileSync('/tmp/b269.json', 'utf8') : 'null');
const 旧 = b269 ? b269.臂.filter((a) => a.宽 === 宽 && a.族 === undefined && a.落点 !== null && a.高 <= 259).map((a) => ({ 族: '音频', 高: a.高, 落点: a.落点, 命中取景律: a.命中取景律, 来源: 'b269' })) : [];
const 新 = out.臂.filter((a) => a.落点 !== null).map((a) => ({ 族: a.族, 高: a.高, 落点: a.落点, 命中取景律: a.命中取景律, 来源: 'b270' }));
const 序列 = [...旧, ...新].sort((a, b) => b.高 - a.高);
out.合并序列 = 序列;
out.汇总 = {
  本批臂: out.臂.length, 本批成功: 新.length, 本批收敛: out.臂.filter((a) => a.是否收敛).length,
  偶数命中取景律: 新.filter((a) => a.高 % 2 === 0 && a.命中取景律).length,
  偶数非取景律: 新.filter((a) => a.高 % 2 === 0 && !a.命中取景律).length,
  序列点数: 序列.length,
  序列中非取景律的H: 序列.filter((a) => !a.命中取景律).map((a) => a.高),
};
log('\n=== 合并后的 1px 序列（w=1000，音频 68）===');
for (const s of 序列) log(`  H=${String(s.高).padStart(3)}${s.高 % 2 ? '奇' : '偶'}  ${s.落点}  ${s.命中取景律 ? '✅取景律' : '🔴非取景律'}  (${s.来源})`);
log('\n=== 汇总 ===');
log(JSON.stringify(out.汇总, null, 1));
fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log(`写入 ${OUT}`);
process.exit(0);

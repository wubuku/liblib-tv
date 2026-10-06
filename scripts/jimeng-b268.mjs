/**
 * 批次 268：**补上批次 266 自己留下的洞** —— 高度项的分母到底是 `Hc` 还是 `W`？
 *
 * 🔴 **批次 266 的结论有个自己没发现的漏洞**（回头查出来的）：
 *   266 报的是 `s = min( 屏上律(w)/W , 0.5 , (H − 160)/Hc )`，`23/23` 逐字。
 *   但逐臂回看：
 *     · **时间线（`W=1200`、`Hc=207`）那 `9` 个臂，高度项一次都没真正生效** ——
 *       `w=1000` 时宽度律给 `468`，而高度项即使取最大也只有 `(720−160)×1200/207 = 3246`
 *       …… 真正让它不生效的是：**它要生效需要 `H < 240.7`，而批次 266 已测出 `H < 240` 取景不可达**
 *       ⇒ 🔴 **那 9 个臂只验了 `min()` 里另外两项。**
 *     · **音频（`W=320`、`Hc=320`）—— `Hc` 恰好等于 `W`** ⇒
 *       `(H−160)/Hc` 与 `(H−160)/W` **在已测数据上逐字相同，无法分辨**。
 *   ⇒ 📌 **这正是批次 252 的教训原样复发**：「两族 `W` 相同 ⇒ 一致并不能证明与 `W` 无关」。
 *
 * 📌 **本批的族选得准**（立规 141：动手前先查手册/前情）——
 *   `图片 b22-upload`：**`W = 5120/9 ≈ 568.889`（算法宽）而画布高 `Hc = 320`**，
 *   🔴 **`Hc ≠ W`，且 `Hc/W ≈ 0.5625`** ⇒ 两种公式给出的落点差约 `1.8` 倍，**一眼可辨**。
 *
 * 📌 **预测先算好并落盘**（`w = 1000`，宽度律给 `468`）：
 *   落点(`Hc` 律) `= min(468/W, 0.5, (H−160)/320)`
 *   落点(`W` 律)  `= min(468/W, 0.5, (H−160)/W)`
 *   | `H` | `Hc` 律 | `W` 律 | 能否分辨 |
 *   |---|---|---|---|
 *   | `400` | `0.5` | `0.421875` | ✅ |
 *   | `320` | `0.5` | `0.28125` | ✅ |
 *   | `300` | `0.4375` | `0.246094` | ✅ |
 *   | `280` | `0.375` | `0.210938` | ✅ |
 *   | `260` | `0.3125` | `0.175781` | ✅ |
 *
 * 📌 **只读**：不新建/不删除/不上传/不分享/不进扣费页/**绝不点生成**。
 *   每臂开新页（批次 260）。**连采 6 帧去重**（立规 76）。末态在实验流程之外独立复查（立规 140）。
 *
 * 用法：node scripts/jimeng-b268.mjs      （落盘 /tmp/b268.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B268_OUT || '/tmp/b268.json';
const 宽 = 1000;
const 高表 = [400, 320, 300, 280, 260];
const 节点 = { id: 'node_gref4sw056', 名: '图片 b22-upload', W: 5120 / 9, Hc: 320 };
const 帧数 = 6, 帧间隔 = 400;

const log = (...a) => console.log(a.join(' '));
const 预测 = (h) => {
  const 宽项 = (宽 - 532) / 节点.W;
  const c = Math.min(宽项, 0.5, (h - 160) / 节点.Hc);
  const w = Math.min(宽项, 0.5, (h - 160) / 节点.W);
  return { 宽项: +宽项.toFixed(6), Hc律: +c.toFixed(9), W律: +w.toFixed(9), 可分辨: Math.abs(c - w) > 1e-6 };
};

const out = { 轮次: 'b268', 问: '高度项的分母是 Hc 还是 W？', 宽, 节点, 高表, 臂: [], 收尾: {} };
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

for (const 高 of 高表) {
  const p = await ctx.newPage();
  const 记 = { 高, 宽, ...预测(高) };
  try {
    await p.setViewportSize({ width: 宽, height: 高 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(5000);

    // 顺带把该节点的画布尺寸逐字读出来，验 Hc=320 这个前提本身
    记.节点尺寸 = await p.evaluate((nid) => {
      const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
      return n ? { offsetW: n.offsetWidth, offsetH: n.offsetHeight } : null;
    }, 节点.id);

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
    if (!行.有行 || !行.可点) { 记.不可达 = !行.有行 ? '搜不到那一行' : '结果行不可点'; out.臂.push(记); log(`H=${高} ⚠️ ${记.不可达}`); await p.close(); continue; }
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
          屏上高: nr ? +nr.height.toFixed(4) : null,
          中心Y: nr ? Math.round(nr.y + nr.height / 2) : null,
        };
      }, 节点.id));
      await p.waitForTimeout(帧间隔);
    }
    记.六帧 = 帧;
    const 去重 = [...new Set(帧.map((f) => f.落点))];
    记.去重后落点 = 去重;
    记.是否收敛 = 去重.length === 1;
    记.落点 = 记.是否收敛 ? 去重[0] : null;
    记.屏上宽 = [...new Set(帧.map((f) => f.屏上宽))];
    记.屏上高 = [...new Set(帧.map((f) => f.屏上高))];
    记.中心Y = [...new Set(帧.map((f) => f.中心Y))];
    记.屏上高除Hc = 记.落点 !== null ? +(记.落点 * 节点.Hc).toFixed(4) : null;  // 应逐字等于屏上高
    记.命中 = 记.落点 === null ? null
      : (Math.abs(记.落点 - 记.Hc律) <= 1e-6 ? 'Hc律' : Math.abs(记.落点 - 记.W律) <= 1e-6 ? 'W律' : '两者皆非');
    out.臂.push(记);
    log(`H=${String(高).padStart(3)} 落点=${记.落点}（去重 ${去重.length}）屏上=${JSON.stringify(记.屏上宽)}×${JSON.stringify(记.屏上高)} 中心Y=${JSON.stringify(记.中心Y)}｜Hc律 ${记.Hc律} W律 ${记.W律} ⇒ ${记.命中}`);
  } catch (e) {
    记.错误 = e.message; out.臂.push(记); log(`H=${高} 🔴 ${e.message}`);
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
  可分辨臂: 成.filter((a) => a.可分辨).length,
  命中Hc律: 成.filter((a) => a.命中 === 'Hc律').length,
  命中W律: 成.filter((a) => a.命中 === 'W律').length,
  两者皆非: 成.filter((a) => a.命中 === '两者皆非').length,
  逐字明细: 成.map((a) => ({ H: a.高, 实测: a.落点, Hc律: a.Hc律, W律: a.W律, 命中: a.命中 })),
};
log('\n=== 汇总 ===');
log(JSON.stringify(out.汇总, null, 1));
fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log(`写入 ${OUT}`);
process.exit(0);

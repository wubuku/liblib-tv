/**
 * 批次 251：**文本族**的窄侧 —— 判「`412` 这个常数里的 `120` 偏移」是音频特有还是取景通性。
 *
 * 📌 批次 249 把音频窄侧测闭合了，四段折线的第二段是 **`screen = w − 412`**，
 *   而三族通用的那条是 **`screen = w − 532`** ⇒ **两者正好差 `120`**。
 *   `120` 从哪来没测过（立规 113 不编），本批去撞**它到底跟不跟族走**。
 *
 * 🔴 **为什么选 `文本 1`（`node_3bfb9r79qe`）当对照**：
 *   **文本族的算法宽 `W` 也是 `320`**（批次 244）⇒ **若那条 `412` 律是「取景通性」，
 *   文本在同一批 `w` 上的落点应当与音频 `8/8` 逐字相同**（屏上宽一样 ⇒ 落点也一样）；
 *   **若 `120` 是音频特有**，文本在窄侧会走**别的**律 ⇒ 两族读数分岔。
 *   📌 这就是立规 123 第 1 问要的「**分歧区**」：两边给出不同答案的位置。
 *
 * 📌 顺带**把批次 249 那个 `437.6` 的精确预测在第二个节点上复测**：
 *   批次 249 预测（`w = 412 + 25.6`）`w=437` 仍落在应用下限 `0.08`、`w=438` 跳到 `(438−412)/320 = 0.08125`。
 *   ⚠️ **那一批步长 `20`，压根没测过那个区间**（立规 121）⇒ **现在只是预测**，
 *   本批用 `1px` 档位把它撞出来。
 *
 * 📌 落点一律与音频同一批读数**逐字比对**，不比「差不多」。
 *
 * 🔴 纪律：
 *   · **正交读量**：读完缩放再点搜索结果行；**不点结果行之外的任何东西**；
 *   · **不新建、不删除、不上传、不触发生成、不进扣费页、不点「保存到主体库」、不分享**；
 *   · 缩放不跨页持久化 ⇒ 每臂开新页即可；**一格键都不用按**；
 *   · 每臂都定位**同一个节点 `文本 1`**（空文本节点，**按节点名匹配**，不是占位文字 —— 批次 240 的教训）。
 *
 * 用法：node scripts/jimeng-b251.mjs            （读数落盘 /tmp/b251.json）
 *      B251_W=400,420 node scripts/jimeng-b251.mjs   （临时换档位表）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B251_OUT || '/tmp/b251.json';
const 节点ID = 'node_3bfb9r79qe';   // 文本 1（画布 [480.055, 240]、z-index 0、布局 320×320）
// ⚠️ 空文本节点**按节点名匹配**（批次 240：拿占位文字当搜索词，5 臂全失败）
const 节点词 = ['文本 1', '文本'];
const 放大键 = 'Meta+Equal';      // 批次 246 试点 + 批次 247 两处证据验证

// 🔴 窄侧 8 档（与批次 249 音频批**同档位**，便于逐字比对）＋ `437`/`438` 两档撞接缝
const 默认档位 = [300, 360, 420, 460, 480, 500, 560, 600, 632, 437, 438];
const 档位 = (process.env.B251_W || 默认档位.join(',')).split(',').map((x) => Number(x.trim())).filter((n) => Number.isFinite(n) && n > 0);
const 臂表 = 档位.map((w) => ({
  名: `w=${w}`, 宽: w, 按键: [],
  说明: (w === 437 || w === 438)
    ? '**1px 档位**：批次 249 预测 `w = 412 + 25.6 = 437.6` ⇒ `437` 应仍在应用下限 `0.08`、`438` 应跳到 `(438−412)/320 = 0.08125`。⚠️ 那一批步长 `20` 没测过这里 ⇒ **现在才第一次测**'
    : '与批次 249 音频批**同档位**，用来判「`412` 里的 `120` 偏移」跟不跟族走（文本 `W` 也是 `320`）',
}));

const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b251', 节点: '文本 1', 档位, 臂: [] };

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

const 读缩放 = (p) => p.evaluate(() => {
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  const z = document.querySelector('[data-testid="canvas-zoom-percent"]');
  return { scale: m ? Number(m[1]) : null, 原始: vp ? (vp.style.transform || '') : null, aria: z ? z.getAttribute('aria-label') : null };
});

for (const 臂 of 臂表) {
  const p = await ctx.newPage();
  const 记 = { 臂: 臂.名, 宽: 臂.宽, 说明: 臂.说明 };
  try {
    await p.setViewportSize({ width: 臂.宽, height: 720 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(5000);

    记.定位前缩放 = await 读缩放(p);

    for (const k of 臂.按键) {
      await p.keyboard.press(k);
      await p.waitForTimeout(1500);
      const 现 = await 读缩放(p);
      if (现.scale === 记.定位前缩放.scale) {
        throw new Error(`按 ${k} 没改到缩放（仍是 ${记.定位前缩放.scale}），本臂作废（不改机制、不猜）`);
      }
      记.定位前缩放 = 现;
    }
    记.定位时缩放 = await 读缩放(p);
    log(`【${臂.名}】定位时缩放 ${记.定位时缩放.scale}（${记.定位时缩放.aria}）`);

    // ---- 搜索 → 点结果行定位 ----
    const 钮 = await p.evaluate(() => {
      const e = Array.from(document.querySelectorAll('button, [role="button"]'))
        .find((x) => (x.getAttribute('aria-label') || '') === '搜索');
      if (!e) return null;
      const r = e.getBoundingClientRect();
      return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
    });
    if (!钮) throw new Error('找不到搜索钮');
    await p.mouse.click(钮[0] + Math.round(钮[2] / 2), 钮[1] + Math.round(钮[3] / 2));
    await p.waitForTimeout(1500);
    await p.evaluate(() => {
      const inp = document.querySelector('[data-testid="canvas-search-panel"] input');
      if (inp) { inp.focus(); inp.select(); }
    });

    const 短名 = 节点ID.replace(/^node_/, '');
    let 点 = null;
    for (const 词 of 节点词) {
      await p.evaluate(() => {
        const inp = document.querySelector('[data-testid="canvas-search-panel"] input');
        if (inp) { inp.focus(); inp.select(); }
      });
      await p.keyboard.type(词, { delay: 85 });
      await p.waitForTimeout(2200);
      const 读行 = await p.evaluate((nid) => {
        const inp = document.querySelector('[data-testid="canvas-search-panel"] input');
        const e = document.querySelector(`[data-testid="canvas-search-result-node_${nid}"]`);
        return { 回读: inp ? inp.value : null, 有行: !!e };
      }, 短名);
      if (读行.有行 && 读行.回读 === 词) {
        点 = await p.evaluate((nid) => {
          const e = document.querySelector(`[data-testid="canvas-search-result-node_${nid}"]`);
          if (!e) return null;
          const r = e.getBoundingClientRect();
          return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
        }, 短名);
        if (点) { await p.mouse.click(点[0], 点[1]); await p.waitForTimeout(5000); 记.用的词 = 词; break; }
      }
    }
    if (!点) throw new Error('候选词都没命中那一行');
    await p.keyboard.press('Escape');
    await p.waitForTimeout(600);
    await p.keyboard.press('Escape');
    await p.waitForTimeout(900);

    记.定位后 = await p.evaluate((nid) => {
      const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
      const vp = document.querySelector('.react-flow__viewport');
      const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
      const z = document.querySelector('[data-testid="canvas-zoom-percent"]');
      const nr = n ? n.getBoundingClientRect() : null;
      return {
        落点: m ? Number(m[1]) : null,
        aria: z ? z.getAttribute('aria-label') : null,
        布局宽: n ? n.offsetWidth : null,
        屏上原始: nr ? [nr.width, nr.height] : null,
        中心Y: nr ? Math.round(nr.y + nr.height / 2) : null,
        状态行: (document.body.innerText.match(/\d+ nodes, \d+ edges, \d+ selected[^\n]*/) || [])[0] || null,
      };
    }, 节点ID);

    if (记.定位后.屏上原始 && 记.定位后.落点) {
      记.反推W = +(记.定位后.屏上原始[0] / 记.定位后.落点).toFixed(4);
    }
    log(`【${臂.名}】落点 ${记.定位后.落点}（${记.定位后.aria}）｜ 屏上原始 ${JSON.stringify(记.定位后.屏上原始)} ｜ 中心Y ${记.定位后.中心Y} ｜ 反推W ${记.反推W}`);
  } catch (e) {
    记.错误 = e.message;
    log(`🔴 ${臂.名} ${e.message}`);
  } finally {
    try { await p.close(); } catch (e) { /* 忽略 */ }
  }
  out.臂.push(记);
  fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
}

log('写入 ' + OUT);
// 🔴 **不要 `b.close()`**：`connectOverCDP` 拿到的 browser 上调 `close()`
//   会**把那个无头浏览器一起关掉**，后面的探针与收尾门第 9 项就会连不上 9444
//   （批次 248 之后真的发生过一次，门 9/11 报 `ECONNREFUSED`，靠重启
//   `scripts/jimeng-headless.mjs` 才恢复）。⇒ 只断开本进程的连接，让浏览器活着。
process.exit(0);
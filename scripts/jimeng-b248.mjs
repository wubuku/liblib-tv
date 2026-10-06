/**
 * 批次 248：音频在 `w < 1212` 到底会不会离开 `0.5`？`0.5` 这一段依不依赖当前缩放？
 *
 * 📌 **本批起因是一句可能写错的话**：批次 247 的收尾写的是
 *   「**音频的地板区（`w ≤ 632`）从来没在非默认缩放下测过**」——
 *   但这句话**把三族的「地板区」框架套到了音频身上**。
 *   查批次 231 的曲线：音频的 `z₀ = 0.260267` 是**指数斜坡在凹口左端（`w = 1212`）的截距**，
 *   **不是**「`w` 变小就压住的���板」。已知读数（`w = 1195`、`1203` → `0.5`；
 *   `692`/`695`/`699` → `0.5`）**全部在 `1212` 以下且全是 `0.5`**，
 *   ⇒ 「`w ≤ 1211` 恒 `0.5`、音频根本没有地板区」是一个**说得通但没测过**的候选机制。
 *
 * 🔴 两种候选，**分歧点明确**，本批各出几臂去撞：
 *     (A) `w ≤ 1211` 恒封顶 `0.5`，**全族最小值就是凹口底的 `0.260267`**
 *         ⇒ 音频**没有**地板区，批次 247 那句话**作废**
 *     (B) 更低处还有一个地板区（`w` 继续变小会掉出斜坡）
 *         ⇒ 那里的地板**依不依赖当前缩放**就还得再问一次
 *
 * 📌 顺带测「封顶支依不依赖当前缩放」：批次 246 的 B 臂在**文本**上答过「不依赖」，
 *   但**音频的 `0.5` 段从没在非默认缩放下测过** ⇒ 配一对同 `w`、只差缩放的臂。
 *
 * 📌 **一条免费的路**：新开页的初始缩放随视口宽变（批次 246 实测
 *   `w=1212` ⇒ `0.260267`，`w=600` ⇒ `0.133452`）⇒ 大多数臂**不需要按任何键**。
 *   「扰动缩放」的那两臂才用 `⌘+`（`Meta+=`，批次 246 试点 + 批次 247 双向验证）。
 *
 * 🔴 纪律：
 *   · **正交读量**：改完缩放必须先读 `canvas-zoom-percent` 确认生效，**再**点搜索结果行；
 *   · **逐次断言**每次按键都真的改了缩放，没改**立刻弃臂**（批次 247 立规）；
 *   · **不点结果行之外的任何东西**，不新建、不删除、不上传、不触发生成；
 *   · 缩放不跨页持久化 ⇒ 每臂开新页即可；
 *   · 每臂都定位**同一个节点 `音频 68`**，唯一变量是「视口宽」与「按了几次键」。
 *
 * 用法：node scripts/jimeng-b248.mjs   （读数落盘 /tmp/b248.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b248.json';
const 音频ID = 'node_tadm1nyykc';
const 音频词 = ['音频 68', '音频'];
const 放大键 = 'Meta+Equal';      // 批次 246 试点 + 批次 247 两处证据验证

// 🔴 先密后疏：`1211` 是凹口左邻，必须打；`1212` 是已知值，当锚点复现一次
const 臂表 = [
  { 名: 'w=300',  宽: 300,  按键: [], 说明: '最窄的一档。若音频真有地板区，这里最该露馅' },
  { 名: 'w=400',  宽: 400,  按键: [], 说明: '同上' },
  { 名: 'w=500',  宽: 500,  按键: [], 说明: '同上' },
  { 名: 'w=632',  宽: 632,  按键: [], 说明: '三族地板区的上界；音频在这里若不是 0.5，说明它根本不是三族那种地板' },
  { 名: 'w=800',  宽: 800,  按键: [], 说明: '中段' },
  { 名: 'w=900·对照（不按键）', 宽: 900, 按键: [], 说明: '与下一臂配对：只差缩放，用来判「音频的 0.5 段依不依赖当前缩放」' },
  { 名: 'w=900·⌘+ 两次',  宽: 900, 按键: ['Meta+Equal', 'Meta+Equal'], 说明: '若落点仍 0.5 ⇒ 封顶支与当前缩放无关' },
  { 名: 'w=1000', 宽: 1000, 按键: [], 说明: '靠近 `w*=1212` 的那一侧' },
  { 名: 'w=1150', 宽: 1150, 按键: [], 说明: '同上' },
  { 名: 'w=1211', 宽: 1211, 按键: [], 说明: '**凹口左邻**。若它是 0.5 而 1212 是 0.260267，那凹口是硬跳变' },
  { 名: 'w=1212·锚点复现', 宽: 1212, 按键: [], 说明: '已知 0.260267；这一臂验「已知值今天还在不在」（立规 120）' },
];

const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b248', 节点: '音频 68', 臂: [] };

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

    const 短名 = 音频ID.replace(/^node_/, '');
    let 点 = null;
    for (const 词 of 音频词) {
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
    }, 音频ID);

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
await b.close();